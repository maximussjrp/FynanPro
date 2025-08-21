from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from email_validator import validate_email, EmailNotValidError
import bcrypt
import stripe
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-muito-segura-aqui-123456789'
app.config['WTF_CSRF_ENABLED'] = True

# Configurações do Stripe
stripe.api_key = 'sk_test_...'  # Sua chave secreta do Stripe (TROCAR!)
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'  # Sua chave pública do Stripe (TROCAR!)

# Preços dos planos (em centavos)
PLAN_PRICES = {
    'monthly': 1900,    # R$ 19,00
    'semester': 8900,   # R$ 89,00  
    'annual': 14900     # R$ 149,00
}

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configuração do banco de dados
engine = create_engine('sqlite:///finance_planner_saas.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Modelo para usuários
class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')  # 'admin' ou 'user' ou 'master'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Campos para planos
    plan_type = Column(String(20), default='trial')  # 'trial', 'free', 'monthly', 'semester', 'annual', 'enterprise'
    plan_start_date = Column(DateTime, default=datetime.utcnow)
    plan_end_date = Column(DateTime)
    trial_used = Column(Boolean, default=False)
    
    # Campos para pagamentos
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))
    payment_method = Column(String(50))  # 'stripe', 'pix', 'boleto'
    last_payment_date = Column(DateTime)
    total_paid = Column(Float, default=0.0)
    
    # Relacionamentos
    transactions = relationship('Transaction', backref='user', lazy=True)
    categories = relationship('Category', backref='user', lazy=True)
    
    def set_password(self, password):
        """Criptografa e define a senha do usuário"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_trial_active(self):
        """Verifica se o período de teste ainda está ativo"""
        if self.plan_type != 'trial':
            return False
        if not self.plan_end_date:
            return False
        return datetime.utcnow() <= self.plan_end_date
    
    def is_plan_active(self):
        """Verifica se o plano do usuário está ativo"""
        if self.plan_type == 'free':
            return True
        if self.plan_type == 'trial':
            return self.is_trial_active()
        if not self.plan_end_date:
            return False
        return datetime.utcnow() <= self.plan_end_date
    
    def get_plan_name(self):
        """Retorna o nome do plano em português"""
        plans = {
            'trial': 'Período de Teste',
            'free': 'Gratuito',
            'monthly': 'Mensal',
            'semester': 'Semestral', 
            'annual': 'Anual',
            'enterprise': 'Enterprise'
        }
        return plans.get(self.plan_type, 'Desconhecido')
    
    def days_remaining(self):
        """Retorna quantos dias restam do plano"""
        if self.plan_type == 'free':
            return 999999  # Ilimitado
        if not self.plan_end_date:
            return 0
        delta = self.plan_end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    try:
        return session.query(User).get(int(user_id))
    finally:
        session.close()

# Modelo para categorias
class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'income' ou 'expense'
    expense_type = Column(String(20), default='variable')  # 'fixed' ou 'variable' (apenas para expenses)
    color = Column(String(7), default='#007bff')  # Cor em hexadecimal
    parent_id = Column(Integer, default=None)  # ID da categoria pai
    level = Column(Integer, default=0)  # Nível da hierarquia (0=raiz, 1=subcategoria, etc)
    is_active = Column(Integer, default=1)  # 1=ativa, 0=inativa
    sort_order = Column(Integer, default=0)  # Ordem de exibição
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_full_name(self):
        """Retorna o nome completo da categoria com hierarquia"""
        if self.parent_id:
            session = Session()
            try:
                parent = session.query(Category).get(self.parent_id)
                if parent:
                    return f"{parent.get_full_name()} > {self.name}"
            finally:
                session.close()
        return self.name
    
    def get_children(self):
        """Retorna as subcategorias desta categoria"""
        session = Session()
        try:
            return session.query(Category).filter_by(parent_id=self.id, is_active=1).order_by(Category.sort_order, Category.name).all()
        finally:
            session.close()
    
    def has_children(self):
        """Verifica se a categoria tem subcategorias"""
        session = Session()
        try:
            return session.query(Category).filter_by(parent_id=self.id, is_active=1).count() > 0
        finally:
            session.close()

# Modelo para contas bancárias/carteiras
class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)
    initial_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relacionamento
    user = relationship("User", backref="accounts")

# Modelo para transações financeiras
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(String(200))
    amount = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)  # 'income' ou 'expense'
    category = Column(String(100))
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    account_id = Column(Integer)
    transfer_to_account_id = Column(Integer)
    transfer_from_account_id = Column(Integer)
    is_transfer = Column(Boolean, default=False)
    is_adjustment = Column(Boolean, default=False)
    adjustment_reason = Column(String(200))
    recurrence_type = Column(String(20))
    recurrence_interval = Column(Integer)
    recurrence_count = Column(Integer)
    current_occurrence = Column(Integer)
    parent_transaction_id = Column(Integer)
    
    # Relacionamento
    user = relationship("User", backref="transactions")

# Modelo para mensagens de chat
class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False)  # 'user', 'admin', 'agent'
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    replied_by_agent_id = Column(Integer, ForeignKey('support_agents.id'), nullable=True)
    
    # Relacionamento com usuário
    user = relationship("User", backref="chat_messages")

# Modelo para respostas rápidas do chat
class QuickReply(Base):
    __tablename__ = 'quick_replies'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), nullable=False, unique=True)
    response = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo para colaboradores de suporte
class SupportAgent(Base):
    __tablename__ = 'support_agents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(60), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relacionamento com mensagens respondidas
    replied_messages = relationship("ChatMessage", foreign_keys="ChatMessage.replied_by_agent_id", backref="replied_by_agent")
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        if not self.is_active:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

# Criar tabelas
Base.metadata.create_all(engine)

# Formulários
class LoginForm(FlaskForm):
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6, max=50)])
    password_confirm = PasswordField('Confirmar senha', validators=[
        DataRequired(), EqualTo('password', message='As senhas devem coincidir')
    ])
    submit = SubmitField('Cadastrar')

class ProfileForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Atualizar Perfil')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha atual', validators=[DataRequired()])
    new_password = PasswordField('Nova senha', validators=[DataRequired(), Length(min=6, max=50)])
    confirm_password = PasswordField('Confirmar nova senha', validators=[
        DataRequired(), EqualTo('new_password', message='As senhas devem coincidir')
    ])
    submit = SubmitField('Alterar Senha')

class SupportLoginForm(FlaskForm):
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar no Suporte')

# Inicializar categorias padrão para um usuário
def init_default_categories_for_user(user_id):
    session = Session()
    try:
        # Verificar se já existem categorias para este usuário
        existing_categories = session.query(Category).filter_by(user_id=user_id).count()
        if existing_categories == 0:
            # Categorias principais de receita
            salary_cat = Category(name='Salário', type='income', color='#28a745', level=0, sort_order=1, user_id=user_id)
            session.add(salary_cat)
            session.flush()  # Para obter o ID
            
            freelance_cat = Category(name='Freelance', type='income', color='#17a2b8', level=0, sort_order=2, user_id=user_id)
            session.add(freelance_cat)
            session.flush()
            
            investments_cat = Category(name='Investimentos', type='income', color='#6f42c1', level=0, sort_order=3, user_id=user_id)
            session.add(investments_cat)
            session.flush()
            
            others_income_cat = Category(name='Outros Rendimentos', type='income', color='#20c997', level=0, sort_order=4, user_id=user_id)
            session.add(others_income_cat)
            session.flush()
            
            # Subcategorias de receita
            session.add(Category(name='Salário Base', type='income', color='#28a745', parent_id=salary_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Horas Extras', type='income', color='#28a745', parent_id=salary_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Bônus', type='income', color='#28a745', parent_id=salary_cat.id, level=1, sort_order=3, user_id=user_id))
            
            # DESPESAS FIXAS
            housing_cat = Category(name='Moradia', type='expense', expense_type='fixed', color='#6c757d', level=0, sort_order=1, user_id=user_id)
            session.add(housing_cat)
            session.flush()
            
            utilities_cat = Category(name='Contas Essenciais', type='expense', expense_type='fixed', color='#dc3545', level=0, sort_order=2, user_id=user_id)
            session.add(utilities_cat)
            session.flush()
            
            insurance_cat = Category(name='Seguros e Planos', type='expense', expense_type='fixed', color='#e83e8c', level=0, sort_order=3, user_id=user_id)
            session.add(insurance_cat)
            session.flush()
            
            loan_cat = Category(name='Empréstimos e Financiamentos', type='expense', expense_type='fixed', color='#6f42c1', level=0, sort_order=4, user_id=user_id)
            session.add(loan_cat)
            session.flush()
            
            # Subcategorias de despesas fixas
            session.add(Category(name='Aluguel', type='expense', expense_type='fixed', color='#6c757d', parent_id=housing_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Condomínio', type='expense', expense_type='fixed', color='#6c757d', parent_id=housing_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='IPTU', type='expense', expense_type='fixed', color='#6c757d', parent_id=housing_cat.id, level=1, sort_order=3, user_id=user_id))
            
            session.add(Category(name='Luz', type='expense', expense_type='fixed', color='#dc3545', parent_id=utilities_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Água', type='expense', expense_type='fixed', color='#dc3545', parent_id=utilities_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Internet', type='expense', expense_type='fixed', color='#dc3545', parent_id=utilities_cat.id, level=1, sort_order=3, user_id=user_id))
            session.add(Category(name='Telefone', type='expense', expense_type='fixed', color='#dc3545', parent_id=utilities_cat.id, level=1, sort_order=4, user_id=user_id))
            
            session.add(Category(name='Plano de Saúde', type='expense', expense_type='fixed', color='#e83e8c', parent_id=insurance_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Seguro Auto', type='expense', expense_type='fixed', color='#e83e8c', parent_id=insurance_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Seguro Vida', type='expense', expense_type='fixed', color='#e83e8c', parent_id=insurance_cat.id, level=1, sort_order=3, user_id=user_id))
            
            # OUTRAS DESPESAS (todas tratadas como fixas)
            food_cat = Category(name='Alimentação', type='expense', expense_type='fixed', color='#fd7e14', level=0, sort_order=5, user_id=user_id)
            session.add(food_cat)
            session.flush()
            
            transport_cat = Category(name='Transporte', type='expense', expense_type='fixed', color='#dc3545', level=0, sort_order=6, user_id=user_id)
            session.add(transport_cat)
            session.flush()
            
            health_cat = Category(name='Saúde', type='expense', expense_type='fixed', color='#e83e8c', level=0, sort_order=7, user_id=user_id)
            session.add(health_cat)
            session.flush()
            
            education_cat = Category(name='Educação', type='expense', expense_type='fixed', color='#6f42c1', level=0, sort_order=8, user_id=user_id)
            session.add(education_cat)
            session.flush()
            
            leisure_cat = Category(name='Lazer', type='expense', expense_type='fixed', color='#20c997', level=0, sort_order=9, user_id=user_id)
            session.add(leisure_cat)
            session.flush()
            
            shopping_cat = Category(name='Compras', type='expense', expense_type='fixed', color='#ffc107', level=0, sort_order=10, user_id=user_id)
            session.add(shopping_cat)
            session.flush()
            
            # Subcategorias de outras despesas (todas fixas)
            session.add(Category(name='Supermercado', type='expense', expense_type='fixed', color='#fd7e14', parent_id=food_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Restaurantes', type='expense', expense_type='fixed', color='#fd7e14', parent_id=food_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Delivery', type='expense', expense_type='fixed', color='#fd7e14', parent_id=food_cat.id, level=1, sort_order=3, user_id=user_id))
            session.add(Category(name='Lanchonetes', type='expense', expense_type='fixed', color='#fd7e14', parent_id=food_cat.id, level=1, sort_order=4, user_id=user_id))
            
            session.add(Category(name='Combustível', type='expense', expense_type='fixed', color='#dc3545', parent_id=transport_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Transporte Público', type='expense', expense_type='fixed', color='#dc3545', parent_id=transport_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Uber/Taxi', type='expense', expense_type='fixed', color='#dc3545', parent_id=transport_cat.id, level=1, sort_order=3, user_id=user_id))
            session.add(Category(name='Manutenção Veículo', type='expense', expense_type='fixed', color='#dc3545', parent_id=transport_cat.id, level=1, sort_order=4, user_id=user_id))
            
            session.add(Category(name='Consultas Médicas', type='expense', expense_type='fixed', color='#e83e8c', parent_id=health_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Medicamentos', type='expense', expense_type='fixed', color='#e83e8c', parent_id=health_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Exames', type='expense', expense_type='fixed', color='#e83e8c', parent_id=health_cat.id, level=1, sort_order=3, user_id=user_id))
            
            session.add(Category(name='Cursos', type='expense', expense_type='fixed', color='#6f42c1', parent_id=education_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Livros', type='expense', expense_type='fixed', color='#6f42c1', parent_id=education_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Material Escolar', type='expense', expense_type='fixed', color='#6f42c1', parent_id=education_cat.id, level=1, sort_order=3, user_id=user_id))
            
            session.add(Category(name='Cinema', type='expense', expense_type='fixed', color='#20c997', parent_id=leisure_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Viagens', type='expense', expense_type='fixed', color='#20c997', parent_id=leisure_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Esportes', type='expense', expense_type='fixed', color='#20c997', parent_id=leisure_cat.id, level=1, sort_order=3, user_id=user_id))
            session.add(Category(name='Hobbies', type='expense', expense_type='fixed', color='#20c997', parent_id=leisure_cat.id, level=1, sort_order=4, user_id=user_id))
            
            session.add(Category(name='Roupas', type='expense', expense_type='fixed', color='#ffc107', parent_id=shopping_cat.id, level=1, sort_order=1, user_id=user_id))
            session.add(Category(name='Eletrônicos', type='expense', expense_type='fixed', color='#ffc107', parent_id=shopping_cat.id, level=1, sort_order=2, user_id=user_id))
            session.add(Category(name='Casa e Decoração', type='expense', expense_type='fixed', color='#ffc107', parent_id=shopping_cat.id, level=1, sort_order=3, user_id=user_id))
            
            session.commit()
    finally:
        session.close()

# As categorias padrão serão criadas quando o usuário se registrar
# init_default_categories_for_user será chamada no registro

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        session = Session()
        try:
            user = session.query(User).filter_by(email=form.email.data.lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                session.commit()
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('index')
                
                flash(f'Bem-vindo(a), {user.name}!', 'success')
                return redirect(next_page)
            else:
                flash('E-mail ou senha incorretos.', 'danger')
        finally:
            session.close()
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        session = Session()
        try:
            # Verificar se o e-mail já existe
            existing_user = session.query(User).filter_by(email=form.email.data.lower()).first()
            if existing_user:
                flash('Este e-mail já está cadastrado.', 'danger')
                return render_template('auth/register.html', form=form)
            
            # Criar novo usuário
            user = User(
                name=form.name.data,
                email=form.email.data.lower(),
                plan_type='trial',
                plan_start_date=datetime.utcnow(),
                plan_end_date=datetime.utcnow() + timedelta(days=7),  # 7 dias grátis
                trial_used=True
            )
            user.set_password(form.password.data)
            
            session.add(user)
            session.commit()
            
            # Criar categorias padrão para o novo usuário
            init_default_categories_for_user(user.id)
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')
        finally:
            session.close()
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# Rotas para planos
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/select_plan/<plan>')
@login_required
def select_plan(plan):
    if plan == 'free':
        # Plano gratuito - ativar imediatamente
        session = Session()
        try:
            user = session.query(User).get(current_user.id)
            user.plan_type = 'free'
            user.plan_start_date = datetime.utcnow()
            user.plan_end_date = None
            session.commit()
            
            current_user.plan_type = 'free'
            current_user.plan_start_date = datetime.utcnow()
            current_user.plan_end_date = None
            
            flash('Plano Gratuito ativado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            session.rollback()
            flash('Erro ao ativar plano. Tente novamente.', 'danger')
            return redirect(url_for('pricing'))
        finally:
            session.close()
    else:
        # Planos pagos - redirecionar para pagamento
        return redirect(url_for('payment', plan=plan))

@app.route('/payment/<plan>')
@login_required  
def payment(plan):
    if plan not in PLAN_PRICES:
        flash('Plano inválido.', 'danger')
        return redirect(url_for('pricing'))
    
    plan_info = {
        'monthly': {'name': 'Plano Mensal', 'price': 19.00, 'period': '/mês'},
        'semester': {'name': 'Plano Semestral', 'price': 89.00, 'period': '/6 meses'},
        'annual': {'name': 'Plano Anual', 'price': 149.00, 'period': '/ano'}
    }
    
    return render_template('payment.html', 
                         plan=plan,
                         plan_info=plan_info[plan],
                         stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    session = Session()
    try:
        plan = request.json.get('plan')
        payment_method = request.json.get('payment_method', 'stripe')
        
        if plan not in PLAN_PRICES:
            return jsonify({'error': 'Plano inválido'}), 400
        
        if payment_method == 'stripe':
            # Processar com Stripe
            try:
                # Criar cliente no Stripe se não existir
                if not current_user.stripe_customer_id:
                    customer = stripe.Customer.create(
                        email=current_user.email,
                        name=current_user.name
                    )
                    user = session.query(User).get(current_user.id)
                    user.stripe_customer_id = customer.id
                    session.commit()
                
                # Criar sessão de pagamento
                checkout_session = stripe.checkout.Session.create(
                    customer=current_user.stripe_customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'brl',
                            'product_data': {
                                'name': f'Finance SaaS - {plan.title()}',
                            },
                            'unit_amount': PLAN_PRICES[plan],
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=url_for('payment_success', plan=plan, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=url_for('payment_cancel', _external=True),
                )
                
                return jsonify({'checkout_url': checkout_session.url})
                
            except stripe.error.StripeError as e:
                return jsonify({'error': f'Erro no pagamento: {str(e)}'}), 400
        
        elif payment_method == 'pix':
            # Simular PIX (você pode integrar com PagSeguro, MercadoPago, etc.)
            pix_code = f"PIX-{current_user.id}-{plan}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return jsonify({
                'pix_code': pix_code,
                'amount': PLAN_PRICES[plan] / 100,
                'instructions': 'Use o código PIX acima para realizar o pagamento. O plano será ativado automaticamente após confirmação.'
            })
        
        else:
            return jsonify({'error': 'Método de pagamento não suportado'}), 400
            
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    finally:
        session.close()

@app.route('/payment/success/<plan>')
@login_required
def payment_success(plan):
    session_id = request.args.get('session_id')
    session = Session()
    
    try:
        if session_id:
            # Verificar pagamento no Stripe
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if checkout_session.payment_status == 'paid':
                # Ativar plano
                user = session.query(User).get(current_user.id)
                user.plan_type = plan
                user.plan_start_date = datetime.utcnow()
                user.last_payment_date = datetime.utcnow()
                user.payment_method = 'stripe'
                user.total_paid += PLAN_PRICES[plan] / 100
                
                # Definir data de expiração
                if plan == 'monthly':
                    user.plan_end_date = datetime.utcnow() + timedelta(days=30)
                elif plan == 'semester':
                    user.plan_end_date = datetime.utcnow() + timedelta(days=180)
                elif plan == 'annual':
                    user.plan_end_date = datetime.utcnow() + timedelta(days=365)
                
                session.commit()
                
                # Atualizar sessão
                current_user.plan_type = plan
                current_user.plan_end_date = user.plan_end_date
                
                flash(f'Pagamento confirmado! Plano {user.get_plan_name()} ativado com sucesso!', 'success')
                return redirect(url_for('index'))
        
        flash('Erro na confirmação do pagamento.', 'danger')
        return redirect(url_for('pricing'))
        
    except Exception as e:
        session.rollback()
        flash('Erro ao processar pagamento. Entre em contato com o suporte.', 'danger')
        return redirect(url_for('pricing'))
    finally:
        session.close()

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    flash('Pagamento cancelado.', 'info')
    return redirect(url_for('pricing'))

# Rotas para perfil
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/support')
@login_required
def support_chat():
    return render_template('support_chat.html')

# Rotas para chat e mensagens
@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    session = Session()
    try:
        # Salvar mensagem do usuário
        chat_message = ChatMessage(
            user_id=current_user.id,
            message=message,
            sender='user'
        )
        session.add(chat_message)
        session.commit()
        
        # Buscar resposta automática
        auto_response = get_auto_response_from_db(message, session)
        
        if auto_response:
            # Salvar resposta automática
            bot_message = ChatMessage(
                user_id=current_user.id,
                message=auto_response,
                sender='admin'
            )
            session.add(bot_message)
            session.commit()
            
            return jsonify({
                'success': True,
                'auto_response': auto_response
            })
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chat/messages')
@login_required
def get_chat_messages():
    session = Session()
    try:
        messages = session.query(ChatMessage).filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.created_at).all()
        
        return jsonify({
            'messages': [{
                'message': msg.message,
                'sender': msg.sender,
                'created_at': msg.created_at.strftime('%H:%M')
            } for msg in messages]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# Painel administrativo para gerenciar chat
@app.route('/admin/chat')
@login_required
def admin_chat():
    # Verificar se é usuário master/admin
    if not current_user.is_master:
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    session = Session()
    try:
        # Buscar mensagens não lidas
        unread_messages = session.query(ChatMessage).filter_by(
            is_read=False, sender='user'
        ).order_by(ChatMessage.created_at.desc()).all()
        
        # Buscar todas as conversas recentes
        recent_conversations = session.query(ChatMessage).join(User).filter(
            ChatMessage.sender == 'user'
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()
        
        # Buscar respostas rápidas
        quick_replies = session.query(QuickReply).filter_by(is_active=True).all()
        
        return render_template('admin_chat.html', 
                             unread_messages=unread_messages,
                             recent_conversations=recent_conversations,
                             quick_replies=quick_replies)
        
    except Exception as e:
        flash(f'Erro ao carregar painel: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        session.close()

@app.route('/admin/chat/reply', methods=['POST'])
@login_required
def admin_reply():
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    
    if not message or not user_id:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    session = Session()
    try:
        # Salvar resposta do admin
        admin_message = ChatMessage(
            user_id=user_id,
            message=message,
            sender='admin'
        )
        session.add(admin_message)
        
        # Marcar mensagens do usuário como lidas
        session.query(ChatMessage).filter_by(
            user_id=user_id, sender='user', is_read=False
        ).update({'is_read': True})
        
        session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/admin/quick-replies')
@login_required
def manage_quick_replies():
    if not current_user.is_master:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    session = Session()
    try:
        quick_replies = session.query(QuickReply).order_by(QuickReply.created_at.desc()).all()
        return render_template('manage_quick_replies.html', quick_replies=quick_replies)
    finally:
        session.close()

@app.route('/admin')
@login_required
def admin_dashboard():
    """Dashboard principal do administrador"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    session = Session()
    try:
        # Estatísticas básicas
        total_users = session.query(User).count()
        total_agents = session.query(SupportAgent).count()
        active_agents = session.query(SupportAgent).filter_by(is_active=True).count()
        
        # Mensagens recentes
        recent_messages = session.query(ChatMessage).order_by(
            ChatMessage.created_at.desc()
        ).limit(10).all()
        
        return render_template('admin_dashboard.html',
                             total_users=total_users,
                             total_agents=total_agents,
                             active_agents=active_agents,
                             recent_messages=recent_messages)
    
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        session.close()

@app.route('/admin/users')
@login_required
def admin_users():
    """Gerenciar usuários (apenas master)"""
    if not current_user.is_master:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    session = Session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        return render_template('admin_users.html', users=users)
    finally:
        session.close()

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Analytics do sistema (apenas master)"""
    if not current_user.is_master:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin_analytics.html')

@app.route('/admin/support-agents')
@login_required
def manage_support_agents():
    """Gerenciar colaboradores de suporte (apenas master)"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('index'))
    
    session = Session()
    try:
        # Buscar todos os agentes de suporte
        agents = session.query(SupportAgent).order_by(SupportAgent.created_at.desc()).all()
        
        # Estatísticas dos agentes
        agent_stats = {}
        for agent in agents:
            today = datetime.utcnow().date()
            responses_today = session.query(ChatMessage).filter(
                ChatMessage.replied_by_agent_id == agent.id,
                ChatMessage.created_at >= today
            ).count()
            
            total_responses = session.query(ChatMessage).filter(
                ChatMessage.replied_by_agent_id == agent.id
            ).count()
            
            agent_stats[agent.id] = {
                'responses_today': responses_today,
                'total_responses': total_responses
            }
        
        return render_template('manage_support_agents.html', 
                             agents=agents, 
                             agent_stats=agent_stats)
    
    except Exception as e:
        flash(f'Erro ao carregar agentes: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        session.close()

@app.route('/admin/support-agents/add', methods=['POST'])
@login_required
def add_support_agent():
    """Adicionar novo colaborador de suporte"""
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not name or not email or not password:
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
    
    session = Session()
    try:
        # Verificar se email já existe
        existing_agent = session.query(SupportAgent).filter_by(email=email).first()
        if existing_agent:
            return jsonify({'error': 'Este email já está em uso'}), 400
        
        # Criar novo agente
        new_agent = SupportAgent(name=name, email=email)
        new_agent.set_password(password)
        
        session.add(new_agent)
        session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Colaborador {name} criado com sucesso!'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'Erro ao criar colaborador: {str(e)}'}), 500
    finally:
        session.close()

@app.route('/admin/support-agents/<int:agent_id>/toggle', methods=['POST'])
@login_required
def toggle_support_agent(agent_id):
    """Ativar/desativar colaborador de suporte"""
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    session = Session()
    try:
        agent = session.query(SupportAgent).get(agent_id)
        if not agent:
            return jsonify({'error': 'Colaborador não encontrado'}), 404
        
        agent.is_active = not agent.is_active
        session.commit()
        
        status = 'ativado' if agent.is_active else 'desativado'
        return jsonify({
            'success': True,
            'message': f'Colaborador {status} com sucesso!',
            'is_active': agent.is_active
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/admin/support-agents/<int:agent_id>/reset-password', methods=['POST'])
@login_required
def reset_agent_password(agent_id):
    """Resetar senha do colaborador"""
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    new_password = data.get('password', '').strip()
    
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
    
    session = Session()
    try:
        agent = session.query(SupportAgent).get(agent_id)
        if not agent:
            return jsonify({'error': 'Colaborador não encontrado'}), 404
        
        agent.set_password(new_password)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Senha do colaborador {agent.name} alterada com sucesso!'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/admin/support-agents/<int:agent_id>', methods=['DELETE'])
@login_required
def delete_support_agent(agent_id):
    """Excluir colaborador de suporte"""
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    session = Session()
    try:
        agent = session.query(SupportAgent).get(agent_id)
        if not agent:
            return jsonify({'error': 'Colaborador não encontrado'}), 404
        
        # Verificar se tem mensagens associadas
        has_messages = session.query(ChatMessage).filter_by(replied_by_agent_id=agent_id).first()
        
        if has_messages:
            # Não deletar, apenas desativar se tem histórico
            agent.is_active = False
            session.commit()
            return jsonify({
                'success': True,
                'message': f'Colaborador {agent.name} foi desativado (tem histórico de mensagens)'
            })
        else:
            # Pode deletar se não tem histórico
            agent_name = agent.name
            session.delete(agent)
            session.commit()
            return jsonify({
                'success': True,
                'message': f'Colaborador {agent_name} foi excluído com sucesso!'
            })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/admin/quick-replies/add', methods=['POST'])
@login_required
def add_quick_reply():
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    response = data.get('response', '').strip()
    
    if not keyword or not response:
        return jsonify({'error': 'Campos obrigatórios'}), 400
    
    session = Session()
    try:
        # Verificar se keyword já existe
        existing = session.query(QuickReply).filter_by(keyword=keyword).first()
        if existing:
            return jsonify({'error': 'Palavra-chave já existe'}), 400
        
        quick_reply = QuickReply(keyword=keyword, response=response)
        session.add(quick_reply)
        session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/admin/quick-replies/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_quick_reply(reply_id):
    if not current_user.is_master:
        return jsonify({'error': 'Acesso negado'}), 403
    
    session = Session()
    try:
        quick_reply = session.query(QuickReply).get(reply_id)
        if quick_reply:
            session.delete(quick_reply)
            session.commit()
            return jsonify({'success': True})
        
        return jsonify({'error': 'Resposta não encontrada'}), 404
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

def get_auto_response_from_db(message, session):
    """Busca resposta automática no banco de dados"""
    lowercaseMessage = message.lower()
    
    quick_replies = session.query(QuickReply).filter_by(is_active=True).all()
    
    for reply in quick_replies:
        if reply.keyword.lower() in lowercaseMessage:
            return reply.response
    
    # Resposta padrão se não encontrar
    return "Obrigada pela mensagem! Nossa equipe irá responder em breve. Para dúvidas urgentes, envie um email para suporte@financesaas.com"

# ============ SISTEMA DE SUPORTE PARA COLABORADORES ============

@app.route('/suporte')
def support_home():
    """Página inicial do sistema de suporte"""
    return render_template('support_home.html')

@app.route('/suporte/login', methods=['GET', 'POST'])
def support_login():
    """Login para colaboradores de suporte"""
    form = SupportLoginForm()
    
    if form.validate_on_submit():
        session = Session()
        try:
            agent = session.query(SupportAgent).filter_by(
                email=form.email.data.lower(),
                is_active=True
            ).first()
            
            if agent and agent.check_password(form.password.data):
                # Simular login do agente (usando session do Flask)
                flask_session['support_agent_id'] = agent.id
                flask_session['support_agent_name'] = agent.name
                
                # Atualizar último login
                agent.last_login = datetime.utcnow()
                session.commit()
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('support_dashboard'))
            else:
                flash('Email ou senha incorretos.', 'danger')
                
        except Exception as e:
            flash('Erro no sistema. Tente novamente.', 'danger')
        finally:
            session.close()
    
    return render_template('support_login.html', form=form)

@app.route('/suporte/logout')
def support_logout():
    """Logout do sistema de suporte"""
    flask_session.pop('support_agent_id', None)
    flask_session.pop('support_agent_name', None)
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('support_home'))

def support_login_required(f):
    """Decorator para verificar se agente está logado"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'support_agent_id' not in flask_session:
            flash('Acesso negado. Faça login como agente de suporte.', 'danger')
            return redirect(url_for('support_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/suporte/dashboard')
@support_login_required
def support_dashboard():
    """Dashboard exclusivo para agentes de suporte"""
    session = Session()
    try:
        # Buscar mensagens não respondidas
        unread_messages = session.query(ChatMessage).filter_by(
            sender='user',
            is_read=False
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()
        
        # Buscar mensagens recentes do dia
        today = datetime.utcnow().date()
        recent_messages = session.query(ChatMessage).filter(
            ChatMessage.created_at >= today,
            ChatMessage.sender == 'user'
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        # Estatísticas do agente atual
        agent_id = flask_session.get('support_agent_id')
        today_responses = session.query(ChatMessage).filter(
            ChatMessage.replied_by_agent_id == agent_id,
            ChatMessage.created_at >= today
        ).count()
        
        return render_template('support_dashboard.html',
                             unread_messages=unread_messages,
                             recent_messages=recent_messages,
                             today_responses=today_responses,
                             agent_name=flask_session.get('support_agent_name'))
    
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {e}', 'danger')
        return redirect(url_for('support_login'))
    finally:
        session.close()

@app.route('/suporte/reply', methods=['POST'])
@support_login_required
def support_reply():
    """Responder mensagem de usuário (apenas para agentes)"""
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    
    if not message or not user_id:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    session = Session()
    try:
        agent_id = flask_session.get('support_agent_id')
        
        # Salvar resposta do agente
        agent_message = ChatMessage(
            user_id=user_id,
            message=message,
            sender='agent',
            replied_by_agent_id=agent_id
        )
        session.add(agent_message)
        
        # Marcar mensagens do usuário como lidas
        session.query(ChatMessage).filter_by(
            user_id=user_id, 
            sender='user', 
            is_read=False
        ).update({'is_read': True})
        
        session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/suporte/conversation/<int:user_id>')
@support_login_required
def support_conversation(user_id):
    """Ver conversa completa com um usuário"""
    session = Session()
    try:
        # Buscar usuário (apenas nome e email para privacidade)
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('support_dashboard'))
        
        # Buscar todas as mensagens da conversa
        messages = session.query(ChatMessage).filter_by(
            user_id=user_id
        ).order_by(ChatMessage.created_at).all()
        
        # Marcar mensagens como lidas
        session.query(ChatMessage).filter_by(
            user_id=user_id,
            sender='user',
            is_read=False
        ).update({'is_read': True})
        session.commit()
        
        return render_template('support_conversation.html',
                             user=user,
                             messages=messages,
                             agent_name=flask_session.get('support_agent_name'))
    
    except Exception as e:
        flash(f'Erro ao carregar conversa: {e}', 'danger')
        return redirect(url_for('support_dashboard'))
    finally:
        session.close()

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    session = Session()
    
    try:
        if form.validate_on_submit():
            # Verificar se o e-mail já existe (exceto o atual)
            existing_user = session.query(User).filter(
                User.email == form.email.data.lower(),
                User.id != current_user.id
            ).first()
            
            if existing_user:
                flash('Este e-mail já está em uso por outro usuário.', 'danger')
                return render_template('edit_profile.html', form=form)
            
            # Atualizar usuário
            user = session.query(User).get(current_user.id)
            user.name = form.name.data
            user.email = form.email.data.lower()
            
            session.commit()
            
            # Atualizar sessão atual
            current_user.name = form.name.data
            current_user.email = form.email.data.lower()
            
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile'))
        
        # Preencher formulário com dados atuais
        form.name.data = current_user.name
        form.email.data = current_user.email
        
        return render_template('edit_profile.html', form=form)
        
    except Exception as e:
        session.rollback()
        flash('Erro ao atualizar perfil. Tente novamente.', 'danger')
        return render_template('edit_profile.html', form=form)
    finally:
        session.close()

@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    session = Session()
    
    try:
        if form.validate_on_submit():
            user = session.query(User).get(current_user.id)
            
            # Verificar senha atual
            if not user.check_password(form.current_password.data):
                flash('Senha atual incorreta.', 'danger')
                return render_template('change_password.html', form=form)
            
            # Atualizar senha
            user.set_password(form.new_password.data)
            session.commit()
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('profile'))
        
        return render_template('change_password.html', form=form)
        
    except Exception as e:
        session.rollback()
        flash('Erro ao alterar senha. Tente novamente.', 'danger')
        return render_template('change_password.html', form=form)
    finally:
        session.close()

@app.route('/profile/delete_account', methods=['POST'])
@login_required
def delete_account():
    session = Session()
    try:
        user_id = current_user.id
        
        # Excluir todas as transações do usuário
        session.query(Transaction).filter_by(user_id=user_id).delete()
        
        # Excluir todas as categorias do usuário
        session.query(Category).filter_by(user_id=user_id).delete()
        
        # Excluir o usuário
        session.query(User).filter_by(id=user_id).delete()
        
        session.commit()
        
        # Fazer logout
        logout_user()
        
        flash('Sua conta foi excluída permanentemente.', 'info')
        return redirect(url_for('login'))
        
    except Exception as e:
        session.rollback()
        flash('Erro ao excluir conta. Tente novamente.', 'danger')
        return redirect(url_for('profile'))
    finally:
        session.close()

# Função para criar usuário master
def create_master_user():
    session = Session()
    try:
        # Verificar se já existe um usuário master
        master_user = session.query(User).filter_by(role='master').first()
        if not master_user:
            master = User(
                name='Administrador Master',
                email='admin@financesaas.com',
                role='master',
                plan_type='enterprise',
                plan_start_date=datetime.utcnow(),
                plan_end_date=None,  # Sem expiração
                is_active=True
            )
            master.set_password('MasterPass123!')  # Mude esta senha!
            
            session.add(master)
            session.commit()
            
            print("Usuário master criado com sucesso!")
            print("Email: admin@financesaas.com")
            print("Senha: MasterPass123!")
            print("IMPORTANTE: Altere a senha após o primeiro login!")
            
        else:
            print("Usuário master já existe.")
            
    except Exception as e:
        session.rollback()
        print(f"Erro ao criar usuário master: {str(e)}")
    finally:
        session.close()

@app.route('/')
@login_required
def index():
    session = Session()
    try:
        # Transações recentes do usuário logado
        transactions = session.query(Transaction).filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(10).all()
        
        # Calcular totais gerais do usuário
        total_income = session.query(func.sum(Transaction.amount)).filter_by(type='income', user_id=current_user.id).scalar() or 0
        total_expense = session.query(func.sum(Transaction.amount)).filter_by(type='expense', user_id=current_user.id).scalar() or 0
        balance = total_income - total_expense
        
        # Calcular totais do mês atual do usuário
        now = datetime.now()
        first_day_month = datetime(now.year, now.month, 1)
        last_day_month = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59)
        
        monthly_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_month,
            Transaction.date <= last_day_month
        ).scalar() or 0
        
        monthly_expense = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_month,
            Transaction.date <= last_day_month
        ).scalar() or 0
        
        monthly_balance = monthly_income - monthly_expense
        
        # Calcular totais da semana atual do usuário
        week_start = now - timedelta(days=now.weekday())
        week_start = datetime(week_start.year, week_start.month, week_start.day)
        
        weekly_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.user_id == current_user.id,
            Transaction.date >= week_start
        ).scalar() or 0
        
        weekly_expense = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= week_start
        ).scalar() or 0
        
        weekly_balance = weekly_income - weekly_expense
        
        # Gastos por categoria (mês atual)
        category_expenses = session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_month,
            Transaction.date <= last_day_month
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()
        
        # Receitas por categoria (mês atual)
        category_income = session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'income',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_month,
            Transaction.date <= last_day_month
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()
        
        # Média diária de gastos (últimos 30 dias)
        thirty_days_ago = now - timedelta(days=30)
        last_30_days_expense = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= thirty_days_ago
        ).scalar() or 0
        
        daily_average = last_30_days_expense / 30
        
        # Crescimento mensal (comparar com mês anterior)
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        
        first_day_prev_month = datetime(prev_year, prev_month, 1)
        last_day_prev_month = datetime(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1], 23, 59, 59)
        
        prev_monthly_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_prev_month,
            Transaction.date <= last_day_prev_month
        ).scalar() or 0
        
        prev_monthly_expense = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_prev_month,
            Transaction.date <= last_day_prev_month
        ).scalar() or 0
        
        income_growth = ((monthly_income - prev_monthly_income) / prev_monthly_income * 100) if prev_monthly_income > 0 else 0
        expense_growth = ((monthly_expense - prev_monthly_expense) / prev_monthly_expense * 100) if prev_monthly_expense > 0 else 0
        
        return render_template('index.html', 
                             transactions=transactions,
                             # Totais gerais
                             income=total_income,
                             expenses=total_expense,
                             balance=balance,
                             # Totais mensais
                             monthly_income=monthly_income,
                             monthly_expenses=monthly_expense,
                             monthly_balance=monthly_balance,
                             # Totais semanais
                             weekly_income=weekly_income,
                             weekly_expenses=weekly_expense,
                             weekly_balance=weekly_balance,
                             # Indicadores
                             category_expenses=category_expenses,
                             category_income=category_income,
                             daily_average=daily_average,
                             income_growth=income_growth,
                             expense_growth=expense_growth)
    finally:
        session.close()

@app.route('/financial_health')
@login_required
def financial_health():
    """Página de indicadores avançados de saúde financeira"""
    session = Session()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        today = datetime.now()
        
        # Últimos 3, 6 e 12 meses
        three_months_ago = today - timedelta(days=90)
        six_months_ago = today - timedelta(days=180)
        twelve_months_ago = today - timedelta(days=365)
        
        # Função para calcular médias por período
        def get_period_averages(start_date):
            income_avg = session.query(func.avg(Transaction.amount)).filter(
                Transaction.type == 'income',
                Transaction.user_id == current_user.id,
                Transaction.date >= start_date
            ).scalar() or 0
            
            expense_avg = session.query(func.avg(Transaction.amount)).filter(
                Transaction.type == 'expense',
                Transaction.user_id == current_user.id,
                Transaction.date >= start_date
            ).scalar() or 0
            
            return income_avg, expense_avg
        
        # Médias dos últimos períodos
        income_3m, expense_3m = get_period_averages(three_months_ago)
        income_6m, expense_6m = get_period_averages(six_months_ago)
        income_12m, expense_12m = get_period_averages(twelve_months_ago)
        
        # Receita e despesa total do mês atual
        current_month_income = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.user_id == current_user.id,
            extract('month', Transaction.date) == today.month,
            extract('year', Transaction.date) == today.year
        ).scalar() or 0
        
        current_month_expenses = session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            extract('month', Transaction.date) == today.month,
            extract('year', Transaction.date) == today.year
        ).scalar() or 0
        
        # % da receita comprometida
        commitment_percentage = (current_month_expenses / current_month_income * 100) if current_month_income > 0 else 0
        
        # Score financeiro (0-100)
        # Base: 50 pontos
        score = 50
        
        # +20 pontos se receita > despesas
        if current_month_income > current_month_expenses:
            score += 20
        
        # +15 pontos se comprometimento < 70%
        if commitment_percentage < 70:
            score += 15
        elif commitment_percentage < 80:
            score += 10
        elif commitment_percentage < 90:
            score += 5
        
        # +15 pontos por crescimento consistente (comparar últimos 3 vs 6 meses)
        if income_3m > income_6m:
            score += 10
        if expense_3m < expense_6m:  # Diminuição de gastos é boa
            score += 5
        
        # Garantir que o score fique entre 0 e 100
        score = max(0, min(100, score))
        
        # Determinar nível do score
        if score >= 80:
            score_level = "Excelente"
            score_color = "success"
        elif score >= 60:
            score_level = "Bom"
            score_color = "primary"
        elif score >= 40:
            score_level = "Regular"
            score_color = "warning"
        else:
            score_level = "Atenção"
            score_color = "danger"
        
        # Comparativo mensal (últimos 6 meses)
        monthly_comparison = []
        for i in range(6):
            date = today - timedelta(days=30*i)
            month_income = session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'income',
                Transaction.user_id == current_user.id,
                extract('month', Transaction.date) == date.month,
                extract('year', Transaction.date) == date.year
            ).scalar() or 0
            
            month_expense = session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'expense',
                Transaction.user_id == current_user.id,
                extract('month', Transaction.date) == date.month,
                extract('year', Transaction.date) == date.year
            ).scalar() or 0
            
            monthly_comparison.append({
                'month': date.strftime('%B'),
                'income': month_income,
                'expense': month_expense,
                'balance': month_income - month_expense
            })
        
        monthly_comparison.reverse()  # Ordem cronológica
        
        return render_template('financial_health.html',
                             # Médias por período
                             income_3m=income_3m,
                             expense_3m=expense_3m,
                             income_6m=income_6m,
                             expense_6m=expense_6m,
                             income_12m=income_12m,
                             expense_12m=expense_12m,
                             # Indicadores do mês atual
                             current_income=current_month_income,
                             current_expenses=current_month_expenses,
                             commitment_percentage=commitment_percentage,
                             # Score financeiro
                             financial_score=score,
                             score_level=score_level,
                             score_color=score_color,
                             # Comparativo mensal
                             monthly_comparison=monthly_comparison)
    finally:
        session.close()

@app.route('/search')
@login_required
def search():
    """Busca inteligente por transações"""
    session = Session()
    try:
        query = request.args.get('q', '').strip()
        results = []
        total_results = 0
        
        if query:
            from sqlalchemy import or_, cast, String
            
            # Busca por descrição, categoria, notas, valor
            search_filter = or_(
                Transaction.description.ilike(f'%{query}%'),
                Transaction.category.ilike(f'%{query}%'),
                Transaction.notes.ilike(f'%{query}%'),
                cast(Transaction.amount, String).ilike(f'%{query}%')
            )
            
            results = session.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                search_filter
            ).order_by(Transaction.date.desc()).limit(50).all()
            
            total_results = session.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                search_filter
            ).count()
        
        return render_template('search.html', 
                             query=query,
                             results=results, 
                             total_results=total_results)
    finally:
        session.close()

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    session = Session()
    try:
        if request.method == 'POST':
            # Buscar a categoria selecionada para obter o nome completo
            category_id = request.form['category']
            category = session.query(Category).filter_by(id=category_id, user_id=current_user.id).first()
            category_name = category.get_full_name() if category else request.form['category']
            
            transaction = Transaction(
                description=request.form['description'],
                amount=float(request.form['amount']),
                type=request.form['type'],
                category=category_name,
                notes=request.form.get('notes', ''),
                user_id=current_user.id
            )
            session.add(transaction)
            session.commit()
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('index'))
        
        # Buscar categorias hierárquicas do usuário
        income_categories = session.query(Category).filter_by(type='income', level=0, is_active=1, user_id=current_user.id).order_by(Category.sort_order, Category.name).all()
        fixed_expense_categories = session.query(Category).filter_by(type='expense', expense_type='fixed', level=0, is_active=1, user_id=current_user.id).order_by(Category.sort_order, Category.name).all()
        variable_expense_categories = session.query(Category).filter_by(type='expense', expense_type='variable', level=0, is_active=1, user_id=current_user.id).order_by(Category.sort_order, Category.name).all()
        
        # Adicionar subcategorias a cada categoria
        for category in income_categories + fixed_expense_categories + variable_expense_categories:
            category.children = category.get_children()
        
        return render_template('add_transaction.html', 
                             income_categories=income_categories,
                             fixed_expense_categories=fixed_expense_categories,
                             variable_expense_categories=variable_expense_categories)
    except ValueError:
        flash('Valor inválido. Por favor, insira um número válido.', 'error')
        return render_template('add_transaction.html')
    except Exception as e:
        flash(f'Erro ao adicionar transação: {str(e)}', 'error')
        return render_template('add_transaction.html')
    finally:
        session.close()

@app.route('/transactions')
@login_required
def transactions():
    session = Session()
    try:
        all_transactions = session.query(Transaction).filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
        return render_template('transactions.html', transactions=all_transactions)
    finally:
        session.close()

@app.route('/delete_transaction/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    session = Session()
    try:
        transaction = session.query(Transaction).filter_by(id=transaction_id, user_id=current_user.id).first()
        if transaction:
            session.delete(transaction)
            session.commit()
            flash('Transação excluída com sucesso!', 'success')
        else:
            flash('Transação não encontrada.', 'error')
    except Exception as e:
        flash(f'Erro ao excluir transação: {str(e)}', 'error')
    finally:
        session.close()
    
    return redirect(url_for('transactions'))

@app.route('/categories')
@login_required
def categories():
    session = Session()
    try:
        # Buscar apenas categorias raiz (level=0) do usuário - todas as despesas são fixas agora
        income_categories = session.query(Category).filter_by(type='income', level=0, is_active=1, user_id=current_user.id).order_by(Category.sort_order, Category.name).all()
        fixed_expense_categories = session.query(Category).filter_by(type='expense', expense_type='fixed', level=0, is_active=1, user_id=current_user.id).order_by(Category.sort_order, Category.name).all()
        
        # Para cada categoria raiz, buscar suas subcategorias
        for category in income_categories + fixed_expense_categories:
            category.children = category.get_children()
        
        return render_template('categories.html', 
                             income_categories=income_categories,
                             fixed_expense_categories=fixed_expense_categories)
    finally:
        session.close()

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    session = Session()
    try:
        if request.method == 'POST':
            parent_id = request.form.get('parent_id')
            level = 1 if parent_id else 0
            
            # Determinar expense_type baseado no pai ou formulário
            expense_type = 'variable'  # padrão
            if request.form['type'] == 'expense':
                if parent_id:
                    # Se tem pai, herda o expense_type do pai
                    parent = session.query(Category).filter_by(id=int(parent_id), user_id=current_user.id).first()
                    if parent:
                        expense_type = parent.expense_type
                else:
                    # Se é categoria raiz, usa o valor do formulário
                    expense_type = request.form.get('expense_type', 'variable')
            
            category = Category(
                name=request.form['name'],
                type=request.form['type'],
                expense_type=expense_type,
                color=request.form.get('color', '#007bff'),
                parent_id=int(parent_id) if parent_id else None,
                level=level,
                sort_order=int(request.form.get('sort_order', 0)),
                user_id=current_user.id
            )
            session.add(category)
            session.commit()
            flash('Categoria adicionada com sucesso!', 'success')
            return redirect(url_for('categories'))
        
        # Buscar categorias raiz do usuário para seleção como pai
        income_root_categories = session.query(Category).filter_by(type='income', level=0, is_active=1, user_id=current_user.id).order_by(Category.name).all()
        fixed_expense_root_categories = session.query(Category).filter_by(type='expense', expense_type='fixed', level=0, is_active=1, user_id=current_user.id).order_by(Category.name).all()
        
        return render_template('add_category.html', 
                             income_root_categories=income_root_categories,
                             fixed_expense_root_categories=fixed_expense_root_categories)
    except Exception as e:
        flash(f'Erro ao adicionar categoria: {str(e)}', 'error')
        return redirect(url_for('categories'))
    finally:
        session.close()

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    session = Session()
    try:
        category = session.query(Category).filter_by(id=category_id, user_id=current_user.id).first()
        if not category:
            flash('Categoria não encontrada.', 'error')
            return redirect(url_for('categories'))
        
        if request.method == 'POST':
            old_name = category.get_full_name()
            
            parent_id = request.form.get('parent_id')
            level = 1 if parent_id else 0
            
            # Determinar expense_type
            expense_type = 'variable'  # padrão
            if request.form['type'] == 'expense':
                if parent_id:
                    # Se tem pai, herda o expense_type do pai
                    parent = session.query(Category).get(int(parent_id))
                    if parent:
                        expense_type = parent.expense_type
                else:
                    # Se é categoria raiz, usa o valor do formulário
                    expense_type = request.form.get('expense_type', 'variable')
            
            category.name = request.form['name']
            category.type = request.form['type']
            category.expense_type = expense_type
            category.color = request.form.get('color', '#007bff')
            category.parent_id = int(parent_id) if parent_id else None
            category.level = level
            category.sort_order = int(request.form.get('sort_order', 0))
            
            # Atualizar transações que usam esta categoria
            new_name = category.get_full_name()
            if old_name != new_name:
                transactions = session.query(Transaction).filter_by(category=old_name, user_id=current_user.id).all()
                for transaction in transactions:
                    transaction.category = new_name
            
            session.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('categories'))
        
        # Buscar categorias raiz para seleção como pai
        income_root_categories = session.query(Category).filter_by(
            type='income', level=0, is_active=1
        ).filter(Category.id != category_id).order_by(Category.name).all()
        
        fixed_expense_root_categories = session.query(Category).filter_by(
            type='expense', expense_type='fixed', level=0, is_active=1
        ).filter(Category.id != category_id).order_by(Category.name).all()
        
        return render_template('edit_category.html', 
                             category=category,
                             income_root_categories=income_root_categories,
                             fixed_expense_root_categories=fixed_expense_root_categories)
    except Exception as e:
        flash(f'Erro ao editar categoria: {str(e)}', 'error')
        return redirect(url_for('categories'))
    finally:
        session.close()

@app.route('/delete_category/<int:category_id>')
@login_required
def delete_category(category_id):
    session = Session()
    try:
        category = session.query(Category).filter_by(id=category_id, user_id=current_user.id).first()
        if not category:
            flash('Categoria não encontrada.', 'error')
            return redirect(url_for('categories'))
        
        category_full_name = category.get_full_name()
        
        # Verificar se há transações do usuário usando esta categoria
        transactions_count = session.query(Transaction).filter_by(category=category_full_name, user_id=current_user.id).count()
        if transactions_count > 0:
            flash(f'Não é possível excluir a categoria "{category_full_name}" pois há {transactions_count} transação(ões) associada(s).', 'error')
            return redirect(url_for('categories'))
        
        # Verificar se há subcategorias
        subcategories_count = session.query(Category).filter_by(parent_id=category_id, is_active=1, user_id=current_user.id).count()
        if subcategories_count > 0:
            flash(f'Não é possível excluir a categoria "{category_full_name}" pois há {subcategories_count} subcategoria(s) associada(s).', 'error')
            return redirect(url_for('categories'))
        
        # Marcar como inativa ao invés de excluir
        category.is_active = 0
        session.commit()
        flash('Categoria excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir categoria: {str(e)}', 'error')
    finally:
        session.close()
    
    return redirect(url_for('categories'))

@app.route('/indicators')
@login_required
def indicators():
    session = Session()
    try:
        now = datetime.now()
        
        # Dados para gráfico mensal (últimos 12 meses)
        monthly_data = []
        for i in range(12):
            month_date = now - timedelta(days=30*i)
            first_day = datetime(month_date.year, month_date.month, 1)
            last_day = datetime(month_date.year, month_date.month, 
                              calendar.monthrange(month_date.year, month_date.month)[1], 23, 59, 59)
            
            monthly_income = session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'income',
                Transaction.user_id == current_user.id,
                Transaction.date >= first_day,
                Transaction.date <= last_day
            ).scalar() or 0
            
            monthly_expense = session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'expense',
                Transaction.user_id == current_user.id,
                Transaction.date >= first_day,
                Transaction.date <= last_day
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_date.strftime('%b %Y'),
                'income': monthly_income,
                'expense': monthly_expense,
                'balance': monthly_income - monthly_expense
            })
        
        monthly_data.reverse()
        
        # Top 5 categorias de gastos (mês atual)
        first_day_month = datetime(now.year, now.month, 1)
        last_day_month = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59)
        
        top_expense_categories = session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            Transaction.date >= first_day_month,
            Transaction.date <= last_day_month
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).limit(5).all()
        
        # Média móvel de 7 dias
        daily_expenses = []
        for i in range(30):
            day = now - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day)
            day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
            
            daily_expense = session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'expense',
                Transaction.user_id == current_user.id,
                Transaction.date >= day_start,
                Transaction.date <= day_end
            ).scalar() or 0
            
            daily_expenses.append({
                'date': day.strftime('%d/%m'),
                'amount': daily_expense
            })
        
        daily_expenses.reverse()
        
        # Calcular algumas métricas
        total_transactions = session.query(Transaction).count()
        avg_transaction = session.query(func.avg(Transaction.amount)).scalar() or 0
        biggest_expense = session.query(func.max(Transaction.amount)).filter_by(type='expense').scalar() or 0
        biggest_income = session.query(func.max(Transaction.amount)).filter_by(type='income').scalar() or 0
        
        return render_template('indicators.html',
                             monthly_data=monthly_data,
                             top_expense_categories=top_expense_categories,
                             daily_expenses=daily_expenses,
                             total_transactions=total_transactions,
                             avg_transaction=avg_transaction,
                             biggest_expense=biggest_expense,
                             biggest_income=biggest_income)
    finally:
        session.close()

if __name__ == '__main__':
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar usuário master
    create_master_user()
    
    app.run(debug=True)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
