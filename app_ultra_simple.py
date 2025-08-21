"""
FynanPro - Versão Ultra Simples e Robusta
"""
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-muito-segura-2024'

# Template HTML inline para evitar problemas de arquivo
HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>FynanPro</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary">
        <div class="container">
            <span class="navbar-brand">💰 FynanPro</span>
            {% if session.get('user_id') %}
            <span class="navbar-text text-white">Olá, {{ session.get('user_name') }}!</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Sair</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {{ content | safe }}
    </div>
</body>
</html>
"""

def init_database():
    """Inicializa o banco de dados"""
    try:
        conn = sqlite3.connect('fynanpro.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

@app.route('/')
def index():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    content = f"""
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">Dashboard</h1>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Bem-vindo, {session.get('user_name')}! 🎉</h5>
                    <p>Sistema FynanPro funcionando perfeitamente!</p>
                    <div class="row mt-4">
                        <div class="col-md-4">
                            <div class="card bg-success text-white">
                                <div class="card-body text-center">
                                    <h3>R$ 0,00</h3>
                                    <p>Receitas</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-danger text-white">
                                <div class="card-body text-center">
                                    <h3>R$ 0,00</h3>
                                    <p>Despesas</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-info text-white">
                                <div class="card-body text-center">
                                    <h3>R$ 0,00</h3>
                                    <p>Saldo</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(HTML_BASE, content=content)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email e senha são obrigatórios.', 'danger')
            else:
                conn = sqlite3.connect('fynanpro.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, email, name, password_hash FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
                conn.close()
                
                if user and check_password_hash(user[3], password):
                    session['user_id'] = user[0]
                    session['user_email'] = user[1]
                    session['user_name'] = user[2]
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Email ou senha incorretos.', 'danger')
        except Exception as e:
            flash(f'Erro no login: {str(e)}', 'danger')
    
    content = """
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
            <div class="card">
                <div class="card-body">
                    <h2 class="card-title text-center mb-4">Entrar</h2>
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">E-mail</label>
                            <input type="email" name="email" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Senha</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary">Entrar</button>
                        </div>
                    </form>
                    <div class="text-center mt-3">
                        <p>Não tem conta? <a href="/register">Cadastre-se aqui</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(HTML_BASE, content=content)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            if not name or not email or not password:
                flash('Todos os campos são obrigatórios.', 'danger')
            elif len(password) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            else:
                conn = sqlite3.connect('fynanpro.db')
                cursor = conn.cursor()
                
                # Verificar se email já existe
                cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    flash('Este email já está cadastrado.', 'danger')
                else:
                    # Criar usuário
                    password_hash = generate_password_hash(password)
                    cursor.execute('''
                        INSERT INTO users (email, name, password_hash, created_at) 
                        VALUES (?, ?, ?, ?)
                    ''', (email, name, password_hash, datetime.utcnow().isoformat()))
                    
                    conn.commit()
                    flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
                    conn.close()
                    return redirect(url_for('login'))
                
                conn.close()
        except Exception as e:
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
    
    content = """
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
            <div class="card">
                <div class="card-body">
                    <h2 class="card-title text-center mb-4">Cadastrar</h2>
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Nome completo</label>
                            <input type="text" name="name" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">E-mail</label>
                            <input type="email" name="email" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Senha</label>
                            <input type="password" name="password" class="form-control" required minlength="6">
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary">Cadastrar</button>
                        </div>
                    </form>
                    <div class="text-center mt-3">
                        <p>Já tem conta? <a href="/login">Entre aqui</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(HTML_BASE, content=content)

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/health')
def health():
    try:
        conn = sqlite3.connect('fynanpro.db')
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

# Inicializar banco na startup
if init_database():
    print("✅ Banco de dados inicializado com sucesso")
else:
    print("❌ Falha ao inicializar banco de dados")

if __name__ == '__main__':
    app.run(debug=True)
