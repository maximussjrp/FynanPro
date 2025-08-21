"""
FynanPro - Sistema de Gestão Financeira
Versão FINAL FUNCIONAL para Render.com
"""

from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import logging
from contextlib import contextmanager

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fynanpro-secret-key-2024')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return User(user[0], user[1], user[2]) if user else None

# Database
def get_db_path():
    db_url = app.config['DATABASE_URL']
    if db_url.startswith('sqlite:///'):
        return db_url.replace('sqlite:///', '')
    return db_url

@contextmanager
def get_db():
    conn = None
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_database():
    """Initialize database with correct schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions table - FIXED SCHEMA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT,
                date DATETIME NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        logger.info("Database initialized")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return "<h1>🏦 FynanPro - Sistema Financeiro</h1><p><a href='/login'>🔐 Login</a> | <a href='/register'>📝 Register</a></p>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not all([username, email, password]):
                return "<h2>❌ Erro</h2><p>Todos os campos são obrigatórios</p><a href='/register'>Voltar</a>", 400
            
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
                if cursor.fetchone():
                    return "<h2>❌ Erro</h2><p>Usuário já existe</p><a href='/register'>Voltar</a>", 400
                
                # Create user
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
                
                return redirect(url_for('login'))
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return "<h2>❌ Erro</h2><p>Falha no registro</p><a href='/register'>Voltar</a>", 500
    
    return '''
    <h1>📝 Registrar no FynanPro</h1>
    <form method="post">
        <p>👤 Username: <input name="username" required></p>
        <p>📧 Email: <input name="email" type="email" required></p>
        <p>🔒 Password: <input name="password" type="password" required></p>
        <p><input type="submit" value="✅ Registrar"></p>
    </form>
    <p><a href="/login">🔐 Já tenho conta</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not all([username, password]):
                return "<h2>❌ Erro</h2><p>Usuário e senha obrigatórios</p><a href='/login'>Voltar</a>", 400
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?",
                    (username, username)
                )
                user_data = cursor.fetchone()
                
                if user_data and check_password_hash(user_data[3], password):
                    user = User(user_data[0], user_data[1], user_data[2])
                    login_user(user, remember=True)
                    return redirect(url_for('dashboard'))
                else:
                    return "<h2>❌ Erro</h2><p>Credenciais inválidas</p><a href='/login'>Voltar</a>", 401
                    
        except Exception as e:
            logger.error(f"Login error: {e}")
            return "<h2>❌ Erro</h2><p>Falha no login</p><a href='/login'>Voltar</a>", 500
    
    return '''
    <h1>🔐 Login FynanPro</h1>
    <form method="post">
        <p>👤 Username/Email: <input name="username" required></p>
        <p>🔒 Password: <input name="password" type="password" required></p>
        <p><input type="submit" value="🚀 Entrar"></p>
    </form>
    <p><a href="/register">📝 Criar conta</a></p>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get stats
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                    COUNT(*) as total_transactions
                FROM transactions 
                WHERE user_id = ?
            """, (current_user.id,))
            
            stats = cursor.fetchone()
            total_income = stats[0] or 0
            total_expense = stats[1] or 0
            balance = total_income - total_expense
            
            # Get recent transactions
            cursor.execute("""
                SELECT description, amount, type, date
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT 10
            """, (current_user.id,))
            
            transactions = cursor.fetchall()
            
            balance_color = "green" if balance >= 0 else "red"
            
            html = f"""
            <h1>📊 Dashboard - {current_user.username}</h1>
            <div style="background: #f5f5f5; padding: 20px; margin: 10px 0;">
                <h2>💰 Resumo Financeiro</h2>
                <p>💚 Receitas: <strong>R$ {total_income:.2f}</strong></p>
                <p>❌ Despesas: <strong>R$ {total_expense:.2f}</strong></p>
                <p>💎 Saldo: <strong style="color: {balance_color}">R$ {balance:.2f}</strong></p>
            </div>
            
            <h2>📋 Transações Recentes</h2>
            <ul>
            """
            
            if not transactions:
                html += "<li>Nenhuma transação encontrada</li>"
            else:
                for tx in transactions:
                    emoji = "💚" if tx[2] == 'income' else "❌"
                    html += f"<li>{emoji} {tx[0]} - R$ {tx[1]:.2f} ({tx[2]}) - {tx[3]}</li>"
            
            html += f"""
            </ul>
            
            <div style="margin: 20px 0;">
                <p><a href="/add_transaction" style="background: green; color: white; padding: 10px; text-decoration: none;">➕ Adicionar Transação</a></p>
                <p><a href="/logout">🚪 Sair</a></p>
            </div>
            
            <div style="margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                <p>✅ <strong>Sistema funcionando perfeitamente!</strong></p>
                <p>🎯 Total de transações: {stats[2]}</p>
            </div>
            """
            
            return html
            
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"<h2>❌ Erro no Dashboard</h2><p>{str(e)}</p><a href='/'>Voltar</a>", 500

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            description = request.form.get('description', '').strip()
            amount = float(request.form.get('amount', 0))
            trans_type = request.form.get('type', 'expense')
            
            if not description or amount <= 0:
                return "<h2>❌ Erro</h2><p>Descrição e valor positivo obrigatórios</p><a href='/add_transaction'>Voltar</a>", 400
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (user_id, description, amount, type, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (current_user.id, description, amount, trans_type, datetime.now().isoformat()))
                
                conn.commit()
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            logger.error(f"Add transaction error: {e}")
            return f"<h2>❌ Erro</h2><p>Falha ao adicionar: {str(e)}</p><a href='/add_transaction'>Voltar</a>", 500
    
    return '''
    <h1>➕ Adicionar Transação</h1>
    <form method="post">
        <p>📝 Descrição: <input name="description" required style="width: 300px;"></p>
        <p>💰 Valor: <input name="amount" type="number" step="0.01" required style="width: 100px;"></p>
        <p>📊 Tipo: 
           <select name="type">
             <option value="expense">❌ Despesa</option>
             <option value="income">💚 Receita</option>
           </select>
        </p>
        <p><input type="submit" value="✅ Adicionar"></p>
    </form>
    <p><a href="/dashboard">⬅️ Voltar ao Dashboard</a></p>
    '''

# Health checks
@app.route('/health')
def health():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'app_name': 'FynanPro',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health')
def api_health():
    return health()

# Initialize app
try:
    init_database()
    logger.info("✅ FynanPro initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize: {e}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
