# FinanProAdvanced - Sistema Principal
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import uuid
from decimal import Decimal

# Importações locais
from config_advanced import config
from models_advanced import (db, User, FamilyProfile, ChartOfAccounts, Account, 
                           Transaction, Budget, BudgetItem, TransactionType, 
                           AccountType, RecurrenceType)
from forms_advanced import (LoginForm, RegistrationForm, ProfileForm, AccountForm,
                          TransactionForm, ChartOfAccountsForm, BudgetForm,
                          BudgetItemForm, FamilyProfileForm, SearchForm, FilterForm,
                          ImportCSVForm)

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensões
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Filtros Jinja2 personalizados
    @app.template_filter('currency')
    def currency_filter(value):
        """Formata valor monetário"""
        if value is None:
            return "R$ 0,00"
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @app.template_filter('date_format')
    def date_format_filter(value, format='%d/%m/%Y'):
        """Formata data"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return value.strftime(format)
    
    @app.template_filter('percentage')
    def percentage_filter(value):
        """Formata porcentagem"""
        if value is None:
            return "0%"
        return f"{float(value):.1f}%"
    
    # Context processors
    @app.context_processor
    def inject_user_data():
        """Injeta dados do usuário em todos os templates"""
        if current_user.is_authenticated:
            return dict(
                user_accounts=current_user.accounts.filter_by(is_active=True).all(),
                total_balance=current_user.get_total_balance()
            )
        return dict()
    
    # Rotas de Autenticação
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Login realizado com sucesso!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos.', 'danger')
        
        return render_template('auth/login_advanced.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            # Verificar se email já existe
            if User.query.filter_by(email=form.email.data).first():
                flash('Este email já está em uso.', 'danger')
                return render_template('auth/register_advanced.html', form=form)
            
            # Criar novo usuário
            user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register_advanced.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Você foi desconectado.', 'info')
        return redirect(url_for('login'))
    
    # Rota Principal - Dashboard
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Estatísticas do período atual (mês atual)
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        
        # Receitas e despesas do mês
        monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_([acc.id for acc in current_user.accounts]),
            Transaction.transaction_type == TransactionType.RECEITA,
            Transaction.date >= start_of_month,
            Transaction.date <= today
        ).scalar() or 0
        
        monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_([acc.id for acc in current_user.accounts]),
            Transaction.transaction_type == TransactionType.DESPESA,
            Transaction.date >= start_of_month,
            Transaction.date <= today
        ).scalar() or 0
        
        # Saldo total de todas as contas
        total_balance = current_user.get_total_balance()
        
        # Transações recentes (últimas 10)
        recent_transactions = Transaction.query.join(Account).filter(
            Account.user_id == current_user.id
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        # Contas do usuário
        user_accounts = current_user.accounts.filter_by(is_active=True).all()
        
        # Dados para gráficos (últimos 6 meses)
        chart_data = get_chart_data_for_dashboard()
        
        return render_template('dashboard/index.html',
                             monthly_income=float(monthly_income),
                             monthly_expenses=float(monthly_expenses),
                             total_balance=total_balance,
                             recent_transactions=recent_transactions,
                             user_accounts=user_accounts,
                             chart_data=chart_data)
    
    # Rotas de Contas
    @app.route('/accounts')
    @login_required
    def accounts():
        user_accounts = current_user.accounts.order_by(Account.name).all()
        return render_template('accounts/index.html', accounts=user_accounts)
    
    @app.route('/accounts/new', methods=['GET', 'POST'])
    @login_required
    def new_account():
        form = AccountForm()
        if form.validate_on_submit():
            account = Account(
                name=form.name.data,
                account_type=AccountType(form.account_type.data),
                bank_name=form.bank_name.data,
                bank_code=form.bank_code.data,
                agency=form.agency.data,
                account_number=form.account_number.data,
                initial_balance=form.initial_balance.data,
                current_balance=form.initial_balance.data,
                credit_limit=form.credit_limit.data,
                color=form.color.data,
                is_active=form.is_active.data,
                include_in_total=form.include_in_total.data,
                user_id=current_user.id
            )
            
            db.session.add(account)
            db.session.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('accounts'))
        
        return render_template('accounts/form.html', form=form, title='Nova Conta')
    
    @app.route('/accounts/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_account(id):
        account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        form = AccountForm(obj=account)
        
        if form.validate_on_submit():
            form.populate_obj(account)
            account.account_type = AccountType(form.account_type.data)
            db.session.commit()
            flash('Conta atualizada com sucesso!', 'success')
            return redirect(url_for('accounts'))
        
        return render_template('accounts/form.html', form=form, title='Editar Conta', account=account)
    
    # Rotas de Transações
    @app.route('/transactions')
    @login_required
    def transactions():
        page = request.args.get('page', 1, type=int)
        filter_form = FilterForm()
        
        # Construir query base
        query = Transaction.query.join(Account).filter(Account.user_id == current_user.id)
        
        # Aplicar filtros se fornecidos
        if request.args.get('start_date'):
            filter_form.start_date.data = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= filter_form.start_date.data)
        
        if request.args.get('end_date'):
            filter_form.end_date.data = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= filter_form.end_date.data)
        
        if request.args.get('account_id'):
            filter_form.account_id.data = int(request.args.get('account_id'))
            query = query.filter(Transaction.account_id == filter_form.account_id.data)
        
        if request.args.get('transaction_type'):
            filter_form.transaction_type.data = request.args.get('transaction_type')
            query = query.filter(Transaction.transaction_type == TransactionType(filter_form.transaction_type.data))
        
        # Popular choices dos SelectField
        filter_form.account_id.choices = [(0, 'Todas as Contas')] + [(acc.id, acc.name) for acc in current_user.accounts.filter_by(is_active=True).all()]
        filter_form.chart_account_id.choices = [(0, 'Todas as Categorias')] + [(cat.id, cat.full_name) for cat in ChartOfAccounts.query.filter_by(is_active=True).all()]
        
        # Ordenar e paginar
        transactions_paginated = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).paginate(
            page=page, per_page=app.config['TRANSACTIONS_PER_PAGE'], error_out=False
        )
        
        return render_template('transactions/index.html', 
                             transactions=transactions_paginated,
                             filter_form=filter_form)
    
    @app.route('/transactions/new', methods=['GET', 'POST'])
    @login_required
    def new_transaction():
        form = TransactionForm()
        
        # Popular choices dos SelectField
        form.account_id.choices = [(acc.id, acc.name) for acc in current_user.accounts.filter_by(is_active=True).all()]
        form.transfer_account_id.choices = [(0, 'Selecione...')] + [(acc.id, acc.name) for acc in current_user.accounts.filter_by(is_active=True).all()]
        form.chart_account_id.choices = [(cat.id, cat.full_name) for cat in ChartOfAccounts.query.filter_by(is_active=True, is_summary=False).all()]
        
        if form.validate_on_submit():
            transaction = Transaction(
                description=form.description.data,
                amount=form.amount.data,
                date=form.date.data,
                transaction_type=TransactionType(form.transaction_type.data),
                chart_account_id=form.chart_account_id.data,
                account_id=form.account_id.data,
                notes=form.notes.data,
                reference=form.reference.data,
                tags=form.tags.data,
                recurrence_type=RecurrenceType(form.recurrence_type.data),
                recurrence_end_date=form.recurrence_end_date.data,
                is_confirmed=form.is_confirmed.data
            )
            
            if form.transfer_account_id.data and form.transfer_account_id.data != 0:
                transaction.transfer_account_id = form.transfer_account_id.data
            
            db.session.add(transaction)
            db.session.commit()
            flash('Transação criada com sucesso!', 'success')
            return redirect(url_for('transactions'))
        
        return render_template('transactions/form.html', form=form, title='Nova Transação')
    
    # Funções auxiliares
    def get_chart_data_for_dashboard():
        """Gera dados para os gráficos do dashboard"""
        # Implementar lógica para gerar dados dos últimos 6 meses
        return {
            'income_expenses': {
                'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                'income': [5000, 5200, 4800, 5100, 5300, 5000],
                'expenses': [3500, 3800, 3200, 3600, 4000, 3700]
            },
            'categories': {
                'labels': ['Alimentação', 'Transporte', 'Moradia', 'Saúde', 'Lazer'],
                'values': [1200, 800, 2000, 400, 600]
            }
        }
    
    # Criar tabelas e dados iniciais
    with app.app_context():
        db.create_all()
        
        # Criar plano de contas padrão se não existir
        if not ChartOfAccounts.query.first():
            create_default_chart_of_accounts()
    
    def create_default_chart_of_accounts():
        """Cria plano de contas padrão"""
        accounts = [
            # Receitas
            {'code': '3.1', 'name': 'RECEITAS', 'type': TransactionType.RECEITA, 'is_summary': True, 'parent': None},
            {'code': '3.1.01', 'name': 'Salários', 'type': TransactionType.RECEITA, 'is_summary': False, 'parent': '3.1'},
            {'code': '3.1.02', 'name': 'Freelances', 'type': TransactionType.RECEITA, 'is_summary': False, 'parent': '3.1'},
            {'code': '3.1.03', 'name': 'Investimentos', 'type': TransactionType.RECEITA, 'is_summary': False, 'parent': '3.1'},
            {'code': '3.1.04', 'name': 'Outras Receitas', 'type': TransactionType.RECEITA, 'is_summary': False, 'parent': '3.1'},
            
            # Despesas
            {'code': '4.1', 'name': 'DESPESAS', 'type': TransactionType.DESPESA, 'is_summary': True, 'parent': None},
            {'code': '4.1.01', 'name': 'Moradia', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.02', 'name': 'Alimentação', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.03', 'name': 'Transporte', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.04', 'name': 'Saúde', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.05', 'name': 'Educação', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.06', 'name': 'Lazer', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
            {'code': '4.1.07', 'name': 'Outras Despesas', 'type': TransactionType.DESPESA, 'is_summary': False, 'parent': '4.1'},
        ]
        
        parent_accounts = {}
        
        for acc_data in accounts:
            account = ChartOfAccounts(
                code=acc_data['code'],
                name=acc_data['name'],
                account_type=acc_data['type'],
                is_summary=acc_data['is_summary'],
                level=acc_data['code'].count('.') - 1
            )
            
            if acc_data['parent']:
                account.parent_id = parent_accounts[acc_data['parent']]
            
            db.session.add(account)
            db.session.flush()  # Para obter o ID
            parent_accounts[acc_data['code']] = account.id
        
        db.session.commit()
    
    return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
