# FinanProAdvanced - Modelos de Dados
from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
import enum

db = SQLAlchemy()

# Enums para categorização
class TransactionType(enum.Enum):
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"

class AccountType(enum.Enum):
    CORRENTE = "corrente"
    POUPANCA = "poupanca"
    CARTAO_CREDITO = "cartao_credito"
    INVESTIMENTO = "investimento"
    DINHEIRO = "dinheiro"

class RecurrenceType(enum.Enum):
    UNICA = "unica"
    DIARIA = "diaria"
    SEMANAL = "semanal"
    QUINZENAL = "quinzenal"
    MENSAL = "mensal"
    BIMESTRAL = "bimestral"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"

# Modelo de Usuário
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Configurações de Perfil
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    profile_image = db.Column(db.String(100))
    
    # Configurações do Sistema
    preferred_currency = db.Column(db.String(3), default='BRL')
    date_format = db.Column(db.String(10), default='DD/MM/YYYY')
    decimal_places = db.Column(db.Integer, default=2)
    
    # Controle de Sessão
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    family_profiles = db.relationship('FamilyProfile', backref='owner', lazy='dynamic', 
                                    cascade='all, delete-orphan')
    accounts = db.relationship('Account', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_total_balance(self):
        """Calcula o saldo total de todas as contas"""
        return sum(account.balance for account in self.accounts)

# Modelo de Perfil Familiar
class FamilyProfile(db.Model):
    __tablename__ = 'family_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50))  # cônjuge, filho, etc.
    birth_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamento com usuário
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FamilyProfile {self.name}>'

# Modelo de Plano de Contas Hierárquico
class ChartOfAccounts(db.Model):
    __tablename__ = 'chart_of_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Hierarquia
    parent_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'))
    level = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Tipo e natureza
    account_type = db.Column(db.Enum(TransactionType), nullable=False)
    is_summary = db.Column(db.Boolean, default=False)  # Conta sintética (não aceita lançamentos)
    
    # Auto-relacionamento para hierarquia
    children = db.relationship('ChartOfAccounts', backref=db.backref('parent', remote_side=[id]))
    
    # Relacionamento com transações
    transactions = db.relationship('Transaction', backref='chart_account', lazy='dynamic')
    
    def __repr__(self):
        return f'<ChartOfAccounts {self.code} - {self.name}>'
    
    @property
    def full_name(self):
        return f"{self.code} - {self.name}"
    
    def get_balance(self, start_date=None, end_date=None):
        """Calcula saldo da conta em um período"""
        query = self.transactions
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        total = query.with_entities(db.func.sum(Transaction.amount)).scalar() or 0
        return Decimal(str(total))

# Modelo de Contas Bancárias
class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.Enum(AccountType), nullable=False)
    
    # Dados bancários
    bank_name = db.Column(db.String(100))
    bank_code = db.Column(db.String(10))
    agency = db.Column(db.String(20))
    account_number = db.Column(db.String(50))
    
    # Saldos e limites
    initial_balance = db.Column(db.Numeric(15, 2), default=0)
    current_balance = db.Column(db.Numeric(15, 2), default=0)
    credit_limit = db.Column(db.Numeric(15, 2), default=0)
    
    # Configurações
    is_active = db.Column(db.Boolean, default=True)
    include_in_total = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(7), default='#007bff')  # Cor em hexadecimal
    
    # Relacionamento
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Account {self.name}>'
    
    @property
    def balance(self):
        return float(self.current_balance or 0)
    
    def update_balance(self):
        """Recalcula o saldo baseado nas transações"""
        total_transactions = db.session.query(db.func.sum(Transaction.amount)).filter_by(account_id=self.id).scalar() or 0
        self.current_balance = float(self.initial_balance) + float(total_transactions)
        db.session.commit()

# Modelo de Transações
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    
    # Classificação
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    chart_account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Dados complementares
    notes = db.Column(db.Text)
    reference = db.Column(db.String(100))  # Número do documento, referência externa
    tags = db.Column(db.String(500))  # Tags separadas por vírgula
    
    # Recorrência
    recurrence_type = db.Column(db.Enum(RecurrenceType), default=RecurrenceType.UNICA)
    recurrence_end_date = db.Column(db.Date)
    parent_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    
    # Transferências
    transfer_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))  # Conta destino para transferências
    
    # Anexos
    attachment_path = db.Column(db.String(200))
    
    # Status e controle
    is_confirmed = db.Column(db.Boolean, default=True)
    is_reconciled = db.Column(db.Boolean, default=False)
    created_by_import = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Auto-relacionamento para recorrências
    child_transactions = db.relationship('Transaction', backref=db.backref('parent_transaction', remote_side=[id]))
    
    def __repr__(self):
        return f'<Transaction {self.description}: {self.amount}>'
    
    @property
    def formatted_amount(self):
        return f"R$ {self.amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def tag_list(self):
        return [tag.strip() for tag in (self.tags or '').split(',') if tag.strip()]

# Modelo de Orçamento
class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Período
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Valores
    planned_income = db.Column(db.Numeric(15, 2), default=0)
    planned_expenses = db.Column(db.Numeric(15, 2), default=0)
    
    # Configurações
    is_active = db.Column(db.Boolean, default=True)
    auto_create_next = db.Column(db.Boolean, default=False)
    
    # Relacionamento
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    budget_items = db.relationship('BudgetItem', backref='budget', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Budget {self.name}>'

# Modelo de Itens do Orçamento
class BudgetItem(db.Model):
    __tablename__ = 'budget_items'
    
    id = db.Column(db.Integer, primary_key=True)
    chart_account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    
    # Valores
    planned_amount = db.Column(db.Numeric(15, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(15, 2), default=0)
    
    # Configurações
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    chart_account = db.relationship('ChartOfAccounts', backref='budget_items')
    
    def __repr__(self):
        return f'<BudgetItem {self.chart_account.name}: {self.planned_amount}>'
    
    @property
    def variance(self):
        return float(self.actual_amount or 0) - float(self.planned_amount or 0)
    
    @property
    def variance_percentage(self):
        if not self.planned_amount:
            return 0
        return (self.variance / float(self.planned_amount)) * 100

# Eventos para atualização automática de saldos
@event.listens_for(Transaction, 'after_insert')
def update_account_balance_insert(mapper, connection, target):
    # Atualiza saldo da conta após inserir transação
    account = db.session.get(Account, target.account_id)
    if account:
        account.update_balance()

@event.listens_for(Transaction, 'after_update')
def update_account_balance_update(mapper, connection, target):
    # Atualiza saldo da conta após atualizar transação
    account = db.session.get(Account, target.account_id)
    if account:
        account.update_balance()

@event.listens_for(Transaction, 'after_delete')
def update_account_balance_delete(mapper, connection, target):
    # Atualiza saldo da conta após deletar transação
    account = db.session.get(Account, target.account_id)
    if account:
        account.update_balance()
