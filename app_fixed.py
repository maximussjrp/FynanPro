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

# MODELO CORRIGIDO - SEM CAMPOS PROBLEMÁTICOS
class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Campos básicos para planos - SEM os campos que causam erro  
    plan_type = Column(String(20), default='trial')
    plan_start_date = Column(DateTime, default=datetime.utcnow)
    
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
        # Simplificado: sempre ativo por 7 dias após criação
        if not self.created_at:
            return True
        trial_end = self.created_at + timedelta(days=7)
        return datetime.utcnow() <= trial_end

# Modelo para transações
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    type = Column(String(20), nullable=False)  # 'income' ou 'expense'
    account = Column(String(100), default='Conta Principal')
    is_recurrence = Column(Boolean, default=False)
    recurrence_type = Column(String(20))  # 'monthly', 'weekly', etc.
    recurrence_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# Modelo para categorias
class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'income' ou 'expense'
    color = Column(String(7), default='#007bff')  # Cor hex
    icon = Column(String(50), default='fa-money-bill')
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento para subcategorias
    children = relationship('Category', backref='parent', remote_side=[id])

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    try:
        return session.query(User).get(int(user_id))
    except:
        return None
    finally:
        session.close()

# Formulários
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

# ROTAS PRINCIPAIS
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        session = Session()
        try:
            user = session.query(User).filter_by(email=form.email.data.lower()).first()
            
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash('Login realizado com sucesso!', 'success')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos', 'danger')
        except Exception as e:
            flash(f'Erro no login: {str(e)}', 'danger')
        finally:
            session.close()
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        session = Session()
        try:
            # Verificar se o email já existe
            existing_user = session.query(User).filter_by(email=form.email.data.lower()).first()
            if existing_user:
                flash('Este email já está cadastrado', 'warning')
                return render_template('auth/register.html', form=form)
            
            # Criar novo usuário
            user = User(
                email=form.email.data.lower(),
                name=form.name.data,
                plan_type='trial',
                plan_start_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            user.set_password(form.password.data)
            
            session.add(user)
            session.commit()
            
            flash('Conta criada com sucesso! Você ganhou 7 dias grátis para testar.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
        finally:
            session.close()
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    session = Session()
    try:
        # Buscar transações recentes
        recent_transactions = session.query(Transaction).filter_by(
            user_id=current_user.id
        ).order_by(Transaction.date.desc()).limit(10).all()
        
        # Calcular saldos
        total_income = session.query(func.sum(Transaction.amount)).filter_by(
            user_id=current_user.id, type='income'
        ).scalar() or 0
        
        total_expenses = session.query(func.sum(Transaction.amount)).filter_by(
            user_id=current_user.id, type='expense'
        ).scalar() or 0
        
        balance = total_income - total_expenses
        
        # Verificar status do plano
        trial_active = current_user.is_trial_active()
        
        return render_template('dashboard.html', 
                             recent_transactions=recent_transactions,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             balance=balance,
                             trial_active=trial_active)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                             recent_transactions=[],
                             total_income=0,
                             total_expenses=0,
                             balance=0,
                             trial_active=True)
    finally:
        session.close()

@app.route('/transactions')
@login_required
def transactions():
    session = Session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        transactions = session.query(Transaction).filter_by(
            user_id=current_user.id
        ).order_by(Transaction.date.desc()).limit(per_page).offset((page-1)*per_page).all()
        
        return render_template('transactions.html', transactions=transactions)
        
    except Exception as e:
        flash(f'Erro ao carregar transações: {str(e)}', 'danger')
        return render_template('transactions.html', transactions=[])
    finally:
        session.close()

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        session = Session()
        try:
            transaction = Transaction(
                user_id=current_user.id,
                amount=float(request.form['amount']),
                description=request.form['description'],
                type=request.form['type'],
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                account=request.form.get('account', 'Conta Principal')
            )
            
            session.add(transaction)
            session.commit()
            
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            session.rollback()
            flash(f'Erro ao adicionar transação: {str(e)}', 'danger')
        finally:
            session.close()
    
    return render_template('add_transaction.html')

# ROTA DE PLANOS E PAGAMENTOS
@app.route('/plans')
@login_required
def plans():
    return render_template('plans.html', 
                         stripe_public_key=STRIPE_PUBLISHABLE_KEY,
                         plan_prices=PLAN_PRICES)

@app.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    try:
        data = request.get_json()
        plan_type = data['plan_type']
        
        if plan_type not in PLAN_PRICES:
            return jsonify({'error': 'Plano inválido'}), 400
        
        # Criar intent de pagamento no Stripe
        intent = stripe.PaymentIntent.create(
            amount=PLAN_PRICES[plan_type],
            currency='brl',
            metadata={
                'user_id': current_user.id,
                'plan_type': plan_type
            }
        )
        
        return jsonify({'client_secret': intent.client_secret})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    # Webhook do Stripe para confirmar pagamentos
    # Implementar conforme necessário
    return '', 200

# INICIALIZAÇÃO DO BANCO
@app.before_first_request
def create_tables():
    try:
        Base.metadata.create_all(engine)
        
        # Criar categorias padrão se necessário
        session = Session()
        try:
            if session.query(Category).count() == 0:
                default_categories = [
                    {'name': 'Alimentação', 'type': 'expense', 'icon': 'fa-utensils'},
                    {'name': 'Transporte', 'type': 'expense', 'icon': 'fa-car'},
                    {'name': 'Moradia', 'type': 'expense', 'icon': 'fa-home'},
                    {'name': 'Saúde', 'type': 'expense', 'icon': 'fa-heartbeat'},
                    {'name': 'Salário', 'type': 'income', 'icon': 'fa-money-bill'},
                    {'name': 'Freelance', 'type': 'income', 'icon': 'fa-laptop'},
                ]
                
                for cat_data in default_categories:
                    category = Category(
                        user_id=1,  # Usuário master
                        **cat_data
                    )
                    session.add(category)
                
                session.commit()
        except:
            pass
        finally:
            session.close()
            
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")

# HEALTH CHECK
@app.route('/health')
def health():
    try:
        session = Session()
        session.execute('SELECT 1')
        session.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# TRATAMENTO DE ERROS
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
