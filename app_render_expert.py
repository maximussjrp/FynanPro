from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import logging

# Configurar logging para debug em produção
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-muito-segura-aqui-123456789'

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# INICIALIZAÇÃO ROBUSTA DO BANCO - APPROACH ESPECIALISTA RENDER
def init_database():
    """Inicialização robusta compatível com Render.com"""
    try:
        db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        
        logger.info(f"Inicializando banco de dados: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar tabelas com schema compatível
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(150) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                plan_type TEXT DEFAULT 'trial',
                plan_start_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL,
                date DATETIME NOT NULL,
                account TEXT DEFAULT 'Conta Principal',
                is_recurrence BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                type TEXT NOT NULL,
                color VARCHAR(7) DEFAULT '#007bff',
                icon VARCHAR(50) DEFAULT 'fa-money-bill',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Banco de dados inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
        return False

# Classe User compatível com Flask-Login e SQLite direto
class User(UserMixin):
    def __init__(self, id, email, name, password_hash, is_active=True, created_at=None, plan_type='trial', plan_start_date=None):
        self.id = id
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.plan_type = plan_type
        self.plan_start_date = plan_start_date or datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_trial_active(self):
        if self.plan_type != 'trial':
            return True  # Planos pagos são sempre ativos
        
        if not self.created_at:
            return True
            
        # Parse da data se for string
        if isinstance(self.created_at, str):
            try:
                created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except:
                return True
        else:
            created_at = self.created_at
            
        trial_end = created_at + timedelta(days=7)
        return datetime.utcnow() <= trial_end

# Funções de banco robustas
def get_db_connection():
    """Conexão robusta com o banco"""
    try:
        db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro na conexão com banco: {e}")
        raise

def create_user(email, name, password):
    """Criar usuário de forma robusta"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (email, name, password_hash, is_active, created_at, plan_type, plan_start_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, name, password_hash, True, datetime.utcnow().isoformat(), 'trial', datetime.utcnow().isoformat()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Usuário criado: {email}")
        return user_id
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário: {e}")
        raise

def get_user_by_email(email):
    """Buscar usuário por email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                email=row['email'],
                name=row['name'],
                password_hash=row['password_hash'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                plan_type=row['plan_type'],
                plan_start_date=row['plan_start_date']
            )
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar usuário: {e}")
        return None

def get_user_by_id(user_id):
    """Buscar usuário por ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                email=row['email'],
                name=row['name'],
                password_hash=row['password_hash'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                plan_type=row['plan_type'],
                plan_start_date=row['plan_start_date']
            )
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar usuário por ID: {e}")
        return None

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# ROTAS
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ Erro na rota index: {e}")
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email e senha são obrigatórios.', 'danger')
                return render_template('auth/login.html')
            
            user = get_user_by_email(email)
            
            if user and user.check_password(password):
                login_user(user, remember=request.form.get('remember_me'))
                flash('Login realizado com sucesso!', 'success')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos.', 'danger')
        
        return render_template('auth/login.html')
        
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        flash('Erro interno. Tente novamente.', 'danger')
        return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            password2 = request.form.get('password2', '')
            
            if not name or not email or not password:
                flash('Todos os campos são obrigatórios.', 'danger')
                return render_template('auth/register.html')
            
            if password != password2:
                flash('As senhas não coincidem.', 'danger')
                return render_template('auth/register.html')
            
            if len(password) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
                return render_template('auth/register.html')
            
            # Verificar se usuário já existe
            existing_user = get_user_by_email(email)
            if existing_user:
                flash('Este email já está cadastrado.', 'warning')
                return render_template('auth/register.html')
            
            # Criar usuário
            user_id = create_user(email, name, password)
            flash('Conta criada com sucesso! Você ganhou 7 dias grátis.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html')
        
    except Exception as e:
        logger.error(f"❌ Erro no registro: {e}")
        flash(f'Erro ao criar conta. Tente novamente.', 'danger')
        return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar transações recentes
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 10
        ''', (current_user.id,))
        transactions = cursor.fetchall()
        
        # Calcular saldos
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expenses
            FROM transactions 
            WHERE user_id = ?
        ''', (current_user.id,))
        
        totals = cursor.fetchone()
        conn.close()
        
        total_income = totals['total_income']
        total_expenses = totals['total_expenses']
        balance = total_income - total_expenses
        
        return render_template('dashboard.html',
                             recent_transactions=transactions,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             balance=balance,
                             trial_active=current_user.is_trial_active())
        
    except Exception as e:
        logger.error(f"❌ Erro no dashboard: {e}")
        flash('Erro ao carregar dashboard.', 'danger')
        return render_template('dashboard.html',
                             recent_transactions=[],
                             total_income=0,
                             total_expenses=0,
                             balance=0,
                             trial_active=True)

@app.route('/transactions')
@login_required
def transactions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 50
        ''', (current_user.id,))
        
        transactions = cursor.fetchall()
        conn.close()
        
        return render_template('transactions.html', transactions=transactions)
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar transações: {e}")
        flash('Erro ao carregar transações.', 'danger')
        return render_template('transactions.html', transactions=[])

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, description, type, date, account)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                current_user.id,
                float(request.form['amount']),
                request.form['description'],
                request.form['type'],
                request.form['date'],
                request.form.get('account', 'Conta Principal')
            ))
            
            conn.commit()
            conn.close()
            
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar transação: {e}")
            flash('Erro ao adicionar transação.', 'danger')
    
    return render_template('add_transaction.html')

@app.route('/plans')
@login_required
def plans():
    return render_template('plans.html')

# Health check robusto
@app.route('/health')
def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users')
        user_count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'users': user_count,
            'timestamp': datetime.utcnow().isoformat(),
            'render_ready': True
        })
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Tratamento de erros robusto
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Erro 500: {error}")
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# Inicializar banco na startup
try:
    init_database()
    logger.info("🚀 FynanPro iniciado com sucesso")
except Exception as e:
    logger.error(f"❌ Erro na inicialização: {e}")

if __name__ == '__main__':
    app.run(debug=True)
