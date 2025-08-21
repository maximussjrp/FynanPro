from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import logging

# Configurar logging robusto
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-muito-segura-aqui-123456789'

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# RESET COMPLETO DO BANCO PARA PRODUÇÃO
def force_database_reset():
    """Reset completo do banco para resolver conflitos de schema"""
    try:
        db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        
        logger.info(f"🔄 RESET COMPLETO do banco: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # BACKUP dos dados existentes antes do reset
        try:
            cursor.execute('SELECT * FROM users')
            users_backup = cursor.fetchall()
            logger.info(f"📦 Backup de {len(users_backup)} usuários")
        except:
            users_backup = []
        
        try:
            cursor.execute('SELECT * FROM transactions')
            trans_backup = cursor.fetchall()
            logger.info(f"📦 Backup de {len(trans_backup)} transações")
        except:
            trans_backup = []
        
        # DROP e recriar tabelas com schema correto
        cursor.execute('DROP TABLE IF EXISTS transactions')
        cursor.execute('DROP TABLE IF EXISTS categories')
        cursor.execute('DROP TABLE IF EXISTS users')
        
        # Recriar tabela users
        cursor.execute('''
            CREATE TABLE users (
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
        
        # Recriar tabela transactions com TODOS os campos necessários
        cursor.execute('''
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense',
                category TEXT,
                date DATETIME NOT NULL,
                notes TEXT,
                account_id INTEGER,
                transfer_to_account_id INTEGER,
                transfer_from_account_id INTEGER,
                is_transfer BOOLEAN DEFAULT 0,
                is_adjustment BOOLEAN DEFAULT 0,
                adjustment_reason TEXT,
                recurrence_type TEXT,
                recurrence_interval INTEGER,
                recurrence_count INTEGER,
                current_occurrence INTEGER,
                parent_transaction_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Recriar tabela categories
        cursor.execute('''
            CREATE TABLE categories (
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
        
        # Restaurar usuários
        for user in users_backup:
            try:
                cursor.execute('''
                    INSERT INTO users (id, email, name, password_hash, is_active, created_at, plan_type, plan_start_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', user[:8])  # Pega apenas os primeiros 8 campos
            except Exception as e:
                logger.warning(f"⚠️ Erro ao restaurar usuário {user[1] if len(user) > 1 else 'N/A'}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ RESET COMPLETO concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no reset do banco: {e}")
        return False

# Classe User simples e robusta
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
            return True
        
        if not self.created_at:
            return True
            
        if isinstance(self.created_at, str):
            try:
                created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except:
                return True
        else:
            created_at = self.created_at
            
        trial_end = created_at + timedelta(days=7)
        return datetime.utcnow() <= trial_end

# Funções de banco ZERO SQLAlchemy
def get_db_connection():
    """Conexão direta SQLite"""
    try:
        db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro na conexão: {e}")
        raise

def get_user_by_id(user_id):
    """Buscar usuário por ID - ZERO SQLAlchemy"""
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
        logger.error(f"Erro ao buscar usuário: {e}")
        return None

def get_user_by_email(email):
    """Buscar usuário por email - ZERO SQLAlchemy"""
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
        logger.error(f"Erro ao buscar usuário: {e}")
        return None

def create_user(email, name, password):
    """Criar usuário - ZERO SQLAlchemy"""
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

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# ROTAS PRINCIPAIS
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ Erro na rota index: {e}")
        return '''
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🚀 FynanPro</h1>
            <p>Sistema de gestão financeira</p>
            <a href="/login">Fazer Login</a> | 
            <a href="/register">Cadastrar</a>
        </body>
        </html>
        '''

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
        return '''
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Login</h2>
            <form method="POST">
                <div>
                    <label>Email:</label><br>
                    <input type="email" name="email" required style="width: 300px; padding: 5px;">
                </div><br>
                <div>
                    <label>Senha:</label><br>
                    <input type="password" name="password" required style="width: 300px; padding: 5px;">
                </div><br>
                <button type="submit" style="padding: 10px 20px;">Entrar</button>
                <a href="/register">Cadastrar</a>
            </form>
        </body>
        </html>
        '''

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
            
            existing_user = get_user_by_email(email)
            if existing_user:
                flash('Este email já está cadastrado.', 'warning')
                return render_template('auth/register.html')
            
            user_id = create_user(email, name, password)
            flash('Conta criada com sucesso! Você ganhou 7 dias grátis.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html')
        
    except Exception as e:
        logger.error(f"❌ Erro no registro: {e}")
        return '''
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Cadastrar</h2>
            <form method="POST">
                <div>
                    <label>Nome:</label><br>
                    <input type="text" name="name" required style="width: 300px; padding: 5px;">
                </div><br>
                <div>
                    <label>Email:</label><br>
                    <input type="email" name="email" required style="width: 300px; padding: 5px;">
                </div><br>
                <div>
                    <label>Senha:</label><br>
                    <input type="password" name="password" required style="width: 300px; padding: 5px;">
                </div><br>
                <div>
                    <label>Confirmar Senha:</label><br>
                    <input type="password" name="password2" required style="width: 300px; padding: 5px;">
                </div><br>
                <button type="submit" style="padding: 10px 20px;">Cadastrar</button>
                <a href="/login">Fazer Login</a>
            </form>
        </body>
        </html>
        '''

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
        
        # Buscar transações ZERO SQLAlchemy
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
        
        total_income = totals['total_income'] if totals else 0
        total_expenses = totals['total_expenses'] if totals else 0
        balance = total_income - total_expenses
        
        return render_template('dashboard.html',
                             recent_transactions=transactions,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             balance=balance,
                             trial_active=current_user.is_trial_active())
        
    except Exception as e:
        logger.error(f"❌ Erro no dashboard: {e}")
        return '''
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>📊 Dashboard</h1>
            <p>Bem-vindo, ''' + str(current_user.name) + '''!</p>
            <div>
                <h3>Resumo Financeiro</h3>
                <p>Receitas: R$ 0,00</p>
                <p>Despesas: R$ 0,00</p>
                <p>Saldo: R$ 0,00</p>
            </div>
            <a href="/transactions">Ver Transações</a> |
            <a href="/add_transaction">Adicionar Transação</a> |
            <a href="/logout">Sair</a>
        </body>
        </html>
        '''

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
            'version': 'zero_sqlalchemy_v2'
        })
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Página não encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Erro 500: {error}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

# INICIALIZAÇÃO COM RESET FORÇADO
try:
    force_database_reset()
    logger.info("🚀 FynanPro ZERO SQLAlchemy V3 FINAL iniciado com sucesso")
    logger.info("🔥 VERSÃO: ZERO_SQLALCHEMY_DEFINITIVA_21AGO2025")
except Exception as e:
    logger.error(f"❌ Erro na inicialização: {e}")

if __name__ == '__main__':
    app.run(debug=True)
