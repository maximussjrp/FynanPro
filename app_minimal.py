"""
Versão mínima do FynanPro para testar funcionalidades básicas
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-muito-segura-2024'

# Configuração Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página.'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id, email, name, password_hash, is_active=True, created_at=None):
        self.id = id
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('finance_planner_saas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, name, password_hash, is_active, created_at FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(*user_data)
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email e senha são obrigatórios.', 'danger')
            return render_template('auth/login.html')
            
        conn = sqlite3.connect('finance_planner_saas.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, name, password_hash, is_active, created_at FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[3], password):
            user = User(*user_data)
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        if not name or not email or not password:
            flash('Todos os campos são obrigatórios.', 'danger')
            return render_template('auth/register.html')
            
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/register.html')
            
        try:
            conn = sqlite3.connect('finance_planner_saas.db')
            cursor = conn.cursor()
            
            # Verificar se email já existe
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Este email já está cadastrado.', 'danger')
                conn.close()
                return render_template('auth/register.html')
            
            # Criar usuário
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (email, name, password_hash, is_active, created_at, plan_type, plan_start_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email, name, password_hash, True, datetime.utcnow(), 'trial', datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
            
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/health')
def health():
    try:
        conn = sqlite3.connect('finance_planner_saas.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            'status': 'ok',
            'database': 'connected',
            'users': user_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
