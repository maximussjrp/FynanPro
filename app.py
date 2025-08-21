#!/usr/bin/env python3
"""
FynanPro - Sistema Financeiro Simplificado
Versão Ultra Limpa para Render.com
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
import secrets
import logging

# ===================== CONFIGURAÇÃO =====================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fynanpro-secret-key-2025')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== CSRF & SECURITY =====================
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    return token and session.get('csrf_token') == token

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# ===================== USER MODEL =====================
class User(UserMixin):
    def __init__(self, id, name, email, password_hash):
        self.id = id
        self.name = name  
        self.email = email
        self.password_hash = password_hash
        
@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

# ===================== DATABASE =====================
@contextmanager
def get_db():
    conn = None
    try:
        db_path = app.config['DATABASE_URL']
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
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
    """Inicializa banco com tabelas essenciais"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de transações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT,
                date DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()

# ===================== ROTAS =====================

@app.route('/')
def index():
    """Homepage moderna"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de usuários"""
    if request.method == 'POST':
        # Validação CSRF
        csrf_token = request.form.get('csrf_token', '')
        if not validate_csrf_token(csrf_token):
            flash('Token de segurança inválido', 'error')
            return redirect(url_for('register'))
            
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validações básicas
        if not name or len(name) < 2:
            flash('Nome deve ter pelo menos 2 caracteres', 'error')
            return redirect(url_for('register'))
            
        if not email or '@' not in email:
            flash('Email inválido', 'error')
            return redirect(url_for('register'))
            
        if not password or len(password) < 8:
            flash('Senha deve ter pelo menos 8 caracteres', 'error')
            return redirect(url_for('register'))
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Verificar se usuário existe
                cursor.execute("SELECT id FROM users WHERE name = ? OR email = ?", (name, email))
                if cursor.fetchone():
                    flash('Usuário ou email já existe', 'error')
                    return redirect(url_for('register'))
                
                # Criar usuário
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )
                conn.commit()
                
                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))
                
        except Exception as e:
            logger.error(f"Erro no registro: {e}")
            flash('Erro interno. Tente novamente.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuários"""
    if request.method == 'POST':
        # Validação CSRF
        csrf_token = request.form.get('csrf_token', '')
        if not validate_csrf_token(csrf_token):
            flash('Token de segurança inválido', 'error')
            return redirect(url_for('login'))
            
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        
        if not name or not password:
            flash('Nome e senha são obrigatórios', 'error')
            return redirect(url_for('login'))
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
                user_data = cursor.fetchone()
                
                if user_data and check_password_hash(user_data[3], password):
                    user = User(user_data[0], user_data[1], user_data[2], user_data[3])
                    login_user(user)
                    flash(f'Bem-vindo, {user.name}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Nome ou senha incorretos', 'error')
                    
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            flash('Erro interno. Tente novamente.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expenses,
                    COUNT(*) as total_transactions
                FROM transactions 
                WHERE user_id = ?
            """, (current_user.id,))
            
            stats = cursor.fetchone()
            income = float(stats[0]) if stats[0] else 0.0
            expenses = float(stats[1]) if stats[1] else 0.0
            balance = income - expenses
            total_transactions = stats[2] if stats[2] else 0
            
            # Transações recentes
            cursor.execute("""
                SELECT description, amount, type, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT 10
            """, (current_user.id,))
            
            recent_transactions = cursor.fetchall()
            
        return render_template('dashboard.html', 
                             income=income,
                             expenses=expenses, 
                             balance=balance,
                             total_transactions=total_transactions,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        flash('Erro ao carregar dashboard', 'error')
        return render_template('dashboard.html',
                             income=0, expenses=0, balance=0, 
                             total_transactions=0, recent_transactions=[])

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    """Gerenciamento de transações"""
    if request.method == 'POST':
        # Validação CSRF
        csrf_token = request.form.get('csrf_token', '')
        if not validate_csrf_token(csrf_token):
            flash('Token de segurança inválido', 'error')
            return redirect(url_for('transactions'))
            
        description = request.form.get('description', '').strip()
        amount = request.form.get('amount', '').strip()
        type_transaction = request.form.get('type', '').strip()
        category = request.form.get('category', '').strip()
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validações
        if not description:
            flash('Descrição é obrigatória', 'error')
            return redirect(url_for('transactions'))
            
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Valor deve ser positivo")
        except:
            flash('Valor inválido', 'error')
            return redirect(url_for('transactions'))
            
        if type_transaction not in ['income', 'expense']:
            flash('Tipo de transação inválido', 'error')
            return redirect(url_for('transactions'))
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (user_id, description, amount, type, category, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_user.id, description, amount, type_transaction, category, date))
                conn.commit()
                
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            logger.error(f"Erro ao adicionar transação: {e}")
            flash('Erro ao adicionar transação', 'error')
    
    # Listar transações
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT description, amount, type, category, date
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC
            """, (current_user.id,))
            
            user_transactions = cursor.fetchall()
            
        return render_template('transactions.html', transactions=user_transactions)
        
    except Exception as e:
        logger.error(f"Erro ao listar transações: {e}")
        flash('Erro ao carregar transações', 'error')
        return render_template('transactions.html', transactions=[])

@app.route('/health')
def health():
    """Health check para Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# ===================== INICIALIZAÇÃO =====================
def create_master_user():
    """Cria usuário master se não existir"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE name = 'admin'")
            if not cursor.fetchone():
                master_hash = generate_password_hash('admin@financesaas')
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    ('admin', 'admin@financesaas.com', master_hash)
                )
                conn.commit()
                logger.info("✅ Usuário master criado: admin / admin@financesaas")
    except Exception as e:
        logger.error(f"Erro ao criar usuário master: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando FynanPro...")
    
    try:
        init_database()
        create_master_user()
        
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
