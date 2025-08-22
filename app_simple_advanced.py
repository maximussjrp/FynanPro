# FinanProAdvanced - Sistema Principal (Versão Simplificada)
import os
import sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from decimal import Decimal

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-super-secreta-para-desenvolvimento-2024'
app.config['DATABASE'] = 'finance_planner_saas.db'

# Criar banco de dados
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            birth_date DATE,
            preferred_currency TEXT DEFAULT 'BRL',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Tabela de contas
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            bank_name TEXT,
            bank_code TEXT,
            agency TEXT,
            account_number TEXT,
            initial_balance REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            credit_limit REAL DEFAULT 0,
            color TEXT DEFAULT '#007bff',
            is_active BOOLEAN DEFAULT 1,
            include_in_total BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de plano de contas
    c.execute('''
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            parent_id INTEGER,
            level INTEGER DEFAULT 0,
            account_type TEXT NOT NULL,
            is_summary BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES chart_of_accounts (id)
        )
    ''')
    
    # Tabela de transações
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date DATE NOT NULL,
            transaction_type TEXT NOT NULL,
            chart_account_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            notes TEXT,
            reference TEXT,
            tags TEXT,
            recurrence_type TEXT DEFAULT 'unica',
            recurrence_end_date DATE,
            parent_transaction_id INTEGER,
            transfer_account_id INTEGER,
            is_confirmed BOOLEAN DEFAULT 1,
            is_reconciled BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chart_account_id) REFERENCES chart_of_accounts (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (parent_transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (transfer_account_id) REFERENCES accounts (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Filtros personalizados
@app.template_filter('currency')
def currency_filter(value):
    if value is None:
        return "R$ 0,00"
    return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

@app.template_filter('date_format')
def date_format_filter(value, format='%d/%m/%Y'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            # Tentar converter string em date
            if 'T' in value:
                value = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            else:
                value = datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return value
    return value.strftime(format) if hasattr(value, 'strftime') else str(value)

# Funções auxiliares
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user():
    if 'user_id' not in session:
        return None
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return dict(user) if user else None

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Filtros customizados para templates
@app.template_filter('strftime')
def strftime_filter(date_str, format='%d/%m/%Y'):
    """Formatação de data para templates"""
    if not date_str:
        return ''
    try:
        from datetime import datetime
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        return date_obj.strftime(format)
    except (ValueError, TypeError):
        return date_str

# Context processor
@app.context_processor
def inject_user_data():
    current_user = get_current_user()
    if current_user:
        conn = get_db()
        accounts = conn.execute('''
            SELECT * FROM accounts 
            WHERE user_id = ? AND is_active = 1 
            ORDER BY name
        ''', (current_user['id'],)).fetchall()
        
        total_balance = sum(acc['current_balance'] for acc in accounts if acc['include_in_total'])
        conn.close()
        
        return dict(
            current_user=current_user,
            user_accounts=[dict(acc) for acc in accounts],
            total_balance=total_balance
        )
    return dict(current_user=None, user_accounts=[], total_balance=0)

# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember_me' in request.form
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session.permanent = remember
            
            # Atualizar último login
            conn = get_db()
            conn.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                        (datetime.now(), user['id']))
            conn.commit()
            conn.close()
            
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login_simple.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']
        password2 = request.form['password2']
        
        # Validações básicas
        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/register_simple.html')
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/register_simple.html')
        
        # Verificar se email já existe
        conn = get_db()
        if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            flash('Este email já está em uso.', 'danger')
            conn.close()
            return render_template('auth/register_simple.html')
        
        # Criar usuário
        password_hash = generate_password_hash(password)
        conn.execute('''
            INSERT INTO users (first_name, last_name, email, phone, password_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, password_hash))
        conn.commit()
        conn.close()
        
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register_simple.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# Rota Principal - Dashboard
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    current_user = get_current_user()
    conn = get_db()
    
    # Estatísticas do mês atual
    from datetime import datetime, date
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Receitas e despesas do mês  
    monthly_income = conn.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.type = 'receita'
        AND t.date >= ? AND t.date <= ?
    ''', (current_user['id'], start_of_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()[0]
    
    monthly_expenses = conn.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.type = 'despesa'
        AND t.date >= ? AND t.date <= ?
    ''', (current_user['id'], start_of_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()[0]
    
    # Transações recentes
    recent_transactions = conn.execute('''
        SELECT t.*, a.name as account_name, t.category as category_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ?
        ORDER BY t.date DESC
        LIMIT 10
    ''', (current_user['id'],)).fetchall()
    
    # Contas do usuário
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard/index_simple.html',
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         recent_transactions=[dict(t) for t in recent_transactions],
                         user_accounts=[dict(acc) for acc in user_accounts])

# Rotas de Transações
@app.route('/transactions')
@login_required
def transactions():
    current_user = get_current_user()
    page = int(request.args.get('page', 1))
    per_page = 25
    
    # Filtros
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    account_id = request.args.get('account_id')
    transaction_type = request.args.get('transaction_type')
    search = request.args.get('search', '').strip()
    
    conn = get_db()
    
    # Construir query base
    query = '''
        SELECT t.*, a.name as account_name, t.category as category_name,
               ta.name as transfer_account_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN accounts ta ON t.transfer_account_id = ta.id
        WHERE a.user_id = ?
    '''
    params = [current_user['id']]
    
    # Aplicar filtros
    if start_date:
        query += ' AND t.date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND t.date <= ?'
        params.append(end_date)
    
    if account_id:
        query += ' AND t.account_id = ?'
        params.append(account_id)
    
    if transaction_type:
        query += ' AND t.type = ?'
        params.append(transaction_type)
    
    if search:
        query += ' AND (t.description LIKE ? OR t.notes LIKE ? OR t.reference LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    # Contar total
    count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
    total = conn.execute(count_query, params).fetchone()[0]
    
    # Adicionar ordenação e paginação
    query += ' ORDER BY t.date DESC, t.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    transactions_list = conn.execute(query, params).fetchall()
    
    # Buscar contas para filtros
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    
    conn.close()
    
    # Calcular paginação
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('transactions/index_simple.html',
                         transactions=[dict(t) for t in transactions_list],
                         user_accounts=[dict(acc) for acc in user_accounts],
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'has_prev': has_prev,
                             'has_next': has_next,
                             'prev_num': page - 1 if has_prev else None,
                             'next_num': page + 1 if has_next else None
                         },
                         filters={
                             'start_date': start_date,
                             'end_date': end_date,
                             'account_id': account_id,
                             'transaction_type': transaction_type,
                             'search': search
                         },
                         total=total)

@app.route('/transactions/new', methods=['GET', 'POST'])
@login_required
def new_transaction():
    current_user = get_current_user()
    
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date_str = request.form['date']
        transaction_type = request.form['transaction_type']
        account_id = int(request.form['account_id'])
        chart_account_id = request.form.get('category', '')
        transfer_account_id = int(request.form['transfer_account_id']) if request.form.get('transfer_account_id') and request.form['transfer_account_id'] != '0' else None
        notes = request.form.get('notes', '')
        reference = request.form.get('reference', '')
        tags = request.form.get('tags', '')
        recurrence_type = request.form.get('recurrence_type', 'unica')
        recurrence_end_date = request.form.get('recurrence_end_date') if request.form.get('recurrence_end_date') else None
        is_confirmed = 'is_confirmed' in request.form
        
        conn = get_db()
        
        # Validações
        if not chart_account_id and transaction_type != 'transferencia':
            flash('Categoria é obrigatória para receitas e despesas.', 'danger')
            return redirect(url_for('new_transaction'))
        
        # Inserir transação principal
        transaction_id = conn.execute('''
            INSERT INTO transactions (description, amount, date, type,
                                    category, account_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (description, amount, date_str, transaction_type, chart_account_id, account_id,
              notes)).lastrowid
        
        # Para transferências, criar transação contrária
        if transaction_type == 'transferencia' and transfer_account_id:
            conn.execute('''
                INSERT INTO transactions (description, amount, date, type,
                                        account_id, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (f'Transferência de {description}', -amount, date_str, 'transferencia',
                  transfer_account_id, notes))
        
        # Atualizar saldos das contas
        update_account_balance(conn, account_id)
        if transfer_account_id:
            update_account_balance(conn, transfer_account_id)
        
        conn.commit()
        conn.close()
        
        # Processar recorrência se necessário
        if recurrence_type != 'unica' and recurrence_end_date:
            create_recurring_transactions(transaction_id, recurrence_type, recurrence_end_date)
        
        flash('Transação criada com sucesso!', 'success')
        return redirect(url_for('transactions'))
    
    # GET - Mostrar formulário
    conn = get_db()
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    
    categories = conn.execute('''
        SELECT * FROM chart_of_accounts 
        WHERE is_active = 1 AND is_summary = 0
        ORDER BY account_type, code
    ''').fetchall()
    
    conn.close()
    
    return render_template('transactions/form_simple.html',
                         title='Nova Transação',
                         user_accounts=[dict(acc) for acc in user_accounts],
                         categories=[dict(cat) for cat in categories])

@app.route('/transactions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    current_user = get_current_user()
    conn = get_db()
    
    # Verificar se a transação pertence ao usuário
    transaction = conn.execute('''
        SELECT t.* FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.id = ? AND a.user_id = ?
    ''', (id, current_user['id'])).fetchone()
    
    if not transaction:
        flash('Transação não encontrada.', 'danger')
        return redirect(url_for('transactions'))
    
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        date_str = request.form['date']
        transaction_type = request.form['transaction_type']
        account_id = int(request.form['account_id'])
        chart_account_id = request.form.get('category', '')
        transfer_account_id = int(request.form['transfer_account_id']) if request.form.get('transfer_account_id') and request.form['transfer_account_id'] != '0' else None
        notes = request.form.get('notes', '')
        reference = request.form.get('reference', '')
        tags = request.form.get('tags', '')
        is_confirmed = 'is_confirmed' in request.form
        
        # Atualizar transação
        conn.execute('''
            UPDATE transactions SET
                description = ?, amount = ?, date = ?, type = ?,
                category = ?, account_id = ?, notes = ?
            WHERE id = ?
        ''', (description, amount, date_str, transaction_type, chart_account_id,
              account_id, notes, id))
        
        # Atualizar saldos das contas
        update_account_balance(conn, transaction['account_id'])  # Conta antiga
        update_account_balance(conn, account_id)  # Conta nova
        if transfer_account_id:
            update_account_balance(conn, transfer_account_id)
        if transaction['transfer_account_id']:
            update_account_balance(conn, transaction['transfer_account_id'])
        
        conn.commit()
        conn.close()
        
        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('transactions'))
    
    # GET - Mostrar formulário
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    
    categories = conn.execute('''
        SELECT * FROM chart_of_accounts 
        WHERE is_active = 1 AND is_summary = 0
        ORDER BY account_type, code
    ''').fetchall()
    
    conn.close()
    
    return render_template('transactions/form_simple.html',
                         title='Editar Transação',
                         transaction=dict(transaction),
                         user_accounts=[dict(acc) for acc in user_accounts],
                         categories=[dict(cat) for cat in categories])

@app.route('/transactions/<int:id>/delete', methods=['POST'])
@login_required
def delete_transaction(id):
    current_user = get_current_user()
    conn = get_db()
    
    # Verificar se a transação pertence ao usuário
    transaction = conn.execute('''
        SELECT t.* FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.id = ? AND a.user_id = ?
    ''', (id, current_user['id'])).fetchone()
    
    if not transaction:
        flash('Transação não encontrada.', 'danger')
        return redirect(url_for('transactions'))
    
    # Deletar transação e filhas (recorrentes)
    conn.execute('DELETE FROM transactions WHERE id = ? OR parent_transaction_id = ?', (id, id))
    
    # Atualizar saldos das contas
    update_account_balance(conn, transaction['account_id'])
    if transaction['transfer_account_id']:
        update_account_balance(conn, transaction['transfer_account_id'])
    
    conn.commit()
    conn.close()
    
    flash('Transação excluída com sucesso!', 'success')
    return redirect(url_for('transactions'))

def update_account_balance(conn, account_id):
    """Atualiza o saldo da conta baseado nas transações"""
    if not account_id:
        return
    
    # Buscar saldo inicial
    account = conn.execute('SELECT initial_balance FROM accounts WHERE id = ?', (account_id,)).fetchone()
    if not account:
        return
    
    initial_balance = account['initial_balance'] or 0
    
    # Calcular total das transações
    total_transactions = conn.execute('''
        SELECT COALESCE(SUM(
            CASE 
                WHEN type = 'receita' THEN amount
                WHEN type = 'despesa' THEN -amount
                WHEN type = 'transferencia' THEN amount
                ELSE 0
            END
        ), 0) FROM transactions
        WHERE account_id = ? AND is_confirmed = 1
    ''', (account_id,)).fetchone()[0]
    
    new_balance = initial_balance + total_transactions
    
    # Atualizar saldo da conta
    conn.execute('UPDATE accounts SET current_balance = ? WHERE id = ?', (new_balance, account_id))

def create_recurring_transactions(parent_id, recurrence_type, end_date_str):
    """Cria transações recorrentes"""
    conn = get_db()
    
    # Buscar transação pai
    parent = conn.execute('SELECT * FROM transactions WHERE id = ?', (parent_id,)).fetchone()
    if not parent:
        return
    
    # Calcular datas das recorrências
    from datetime import datetime, timedelta
    import calendar
    
    start_date = datetime.strptime(parent['date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    current_date = start_date
    recurrence_map = {
        'diaria': timedelta(days=1),
        'semanal': timedelta(weeks=1),
        'quinzenal': timedelta(weeks=2),
        'bimestral': timedelta(days=60),
        'trimestral': timedelta(days=90),
        'semestral': timedelta(days=180),
        'anual': timedelta(days=365)
    }
    
    if recurrence_type == 'mensal':
        while current_date <= end_date:
            current_date = add_months(current_date, 1)
            if current_date <= end_date:
                create_child_transaction(conn, parent, current_date, parent_id)
    else:
        delta = recurrence_map.get(recurrence_type, timedelta(days=30))
        while current_date <= end_date:
            current_date += delta
            if current_date <= end_date:
                create_child_transaction(conn, parent, current_date, parent_id)
    
    conn.commit()
    conn.close()

def add_months(date, months):
    """Adiciona meses a uma data"""
    import calendar
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return date.replace(year=year, month=month, day=day)

def create_child_transaction(conn, parent, date, parent_id):
    """Cria uma transação filha (recorrente)"""
    conn.execute('''
        INSERT INTO transactions (description, amount, date, transaction_type,
                                chart_account_id, account_id, notes, reference, tags,
                                parent_transaction_id, transfer_account_id, is_confirmed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (parent['description'], parent['amount'], date.strftime('%Y-%m-%d'),
          parent['transaction_type'], parent['chart_account_id'], parent['account_id'],
          parent['notes'], parent['reference'], parent['tags'], parent_id,
          parent['transfer_account_id'], parent['is_confirmed']))

# Rotas de Relatórios - ETAPA 3
@app.route('/reports')
@login_required
def reports():
    """Dashboard principal de relatórios"""
    return render_template('reports/index_simple.html')

@app.route('/reports/cash_flow')
@login_required
def cash_flow_report():
    """Relatório de Fluxo de Caixa"""
    current_user = get_current_user()
    
    # Parâmetros de filtro
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    account_id = request.args.get('account_id')
    
    # Definir período padrão (últimos 6 meses)
    if not start_date or not end_date:
        from datetime import datetime, date, timedelta
        today = date.today()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
    
    conn = get_db()
    
    # Query base para fluxo de caixa mensal
    query = '''
        SELECT 
            strftime('%Y-%m', t.date) as mes,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'receita' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as receitas,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'despesa' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as despesas
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.date >= ? AND t.date <= ?
    '''
    params = [current_user['id'], start_date, end_date]
    
    if account_id:
        query += ' AND t.account_id = ?'
        params.append(account_id)
    
    query += ' GROUP BY strftime("%Y-%m", t.date) ORDER BY mes'
    
    cash_flow_data = conn.execute(query, params).fetchall()
    
    # Contas para filtro
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    
    # Dados para gráfico
    labels = []
    receitas_values = []
    despesas_values = []
    saldo_values = []
    saldo_acumulado = 0
    
    for row in cash_flow_data:
        from datetime import datetime
        mes_obj = datetime.strptime(row['mes'], '%Y-%m')
        labels.append(mes_obj.strftime('%b/%Y'))
        receitas_values.append(float(row['receitas']))
        despesas_values.append(float(row['despesas']))
        saldo_mensal = float(row['receitas']) - float(row['despesas'])
        saldo_acumulado += saldo_mensal
        saldo_values.append(saldo_acumulado)
    
    conn.close()
    
    chart_data = {
        'labels': labels,
        'receitas': receitas_values,
        'despesas': despesas_values,
        'saldo': saldo_values
    }
    
    return render_template('reports/cash_flow_simple.html',
                         chart_data=chart_data,
                         cash_flow_data=[dict(row) for row in cash_flow_data],
                         user_accounts=[dict(acc) for acc in user_accounts],
                         start_date=start_date,
                         end_date=end_date,
                         account_id=account_id)

@app.route('/reports/categories')
@login_required
def categories_report():
    """Relatório por Categorias"""
    current_user = get_current_user()
    
    # Parâmetros de filtro
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('transaction_type', 'despesa')
    
    # Definir período padrão (mês atual)
    if not start_date or not end_date:
        from datetime import date
        today = date.today()
        end_date = today.strftime('%Y-%m-%d')
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
    
    conn = get_db()
    
    # Query para categorias
    categories_data = conn.execute('''
        SELECT 
            c.name as categoria,
            c.code as codigo,
            COALESCE(SUM(t.amount), 0) as total,
            COUNT(t.id) as qtd_transacoes,
            ROUND(AVG(t.amount), 2) as valor_medio
        FROM chart_of_accounts c
        LEFT JOIN transactions t ON c.id = t.chart_account_id 
            AND t.transaction_type = ? 
            AND t.is_confirmed = 1
            AND t.date >= ? AND t.date <= ?
        JOIN accounts a ON t.account_id = a.id
        WHERE c.account_type = ? AND c.is_active = 1 AND c.is_summary = 0
            AND a.user_id = ?
        GROUP BY c.id, c.name, c.code
        HAVING total > 0
        ORDER BY total DESC
        LIMIT 20
    ''', (transaction_type, start_date, end_date, transaction_type, current_user['id'])).fetchall()
    
    # Dados para gráfico
    labels = [row['categoria'] for row in categories_data]
    values = [float(row['total']) for row in categories_data]
    
    conn.close()
    
    chart_data = {
        'labels': labels,
        'values': values
    }
    
    return render_template('reports/categories_simple.html',
                         chart_data=chart_data,
                         categories_data=[dict(row) for row in categories_data],
                         start_date=start_date,
                         end_date=end_date,
                         transaction_type=transaction_type)

@app.route('/reports/accounts')
@login_required
def accounts_report():
    """Relatório por Contas"""
    current_user = get_current_user()
    
    conn = get_db()
    
    # Relatório detalhado por conta
    accounts_data = conn.execute('''
        SELECT 
            a.*,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'receita' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as total_receitas,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'despesa' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as total_despesas,
            COUNT(t.id) as qtd_transacoes,
            MAX(t.date) as ultima_transacao
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.account_id
        WHERE a.user_id = ? AND a.is_active = 1
        GROUP BY a.id
        ORDER BY a.current_balance DESC
    ''', (current_user['id'],)).fetchall()
    
    # Evolução dos saldos (últimos 30 dias)
    from datetime import date, timedelta
    today = date.today()
    start_date_evolution = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    
    evolution_data = conn.execute('''
        SELECT 
            a.name,
            t.date,
            SUM(CASE WHEN t.transaction_type = 'receita' THEN t.amount 
                     WHEN t.transaction_type = 'despesa' THEN -t.amount 
                     ELSE 0 END) as movimento_diario
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.account_id
        WHERE a.user_id = ? AND t.date >= ? AND t.is_confirmed = 1
        GROUP BY a.name, t.date
        ORDER BY a.name, t.date
    ''', (current_user['id'], start_date_evolution)).fetchall()
    
    conn.close()
    
    return render_template('reports/accounts_simple.html',
                         accounts_data=[dict(row) for row in accounts_data],
                         evolution_data=[dict(row) for row in evolution_data])

@app.route('/reports/trends')
@login_required  
def trends_report():
    """Relatório de Tendências"""
    current_user = get_current_user()
    
    conn = get_db()
    
    # Tendências mensais dos últimos 12 meses
    from datetime import date, timedelta
    today = date.today()
    start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
    
    trends_data = conn.execute('''
        SELECT 
            strftime('%Y-%m', t.date) as mes,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'receita' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as receitas,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'despesa' AND t.is_confirmed = 1 THEN t.amount ELSE 0 END), 0) as despesas,
            COUNT(CASE WHEN t.transaction_type = 'receita' THEN 1 END) as qtd_receitas,
            COUNT(CASE WHEN t.transaction_type = 'despesa' THEN 1 END) as qtd_despesas
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.date >= ?
        GROUP BY strftime('%Y-%m', t.date)
        ORDER BY mes
    ''', (current_user['id'], start_date)).fetchall()
    
    # Top 5 categorias por período
    top_categories = conn.execute('''
        SELECT 
            c.name as categoria,
            COALESCE(SUM(t.amount), 0) as total
        FROM chart_of_accounts c
        JOIN transactions t ON c.id = t.chart_account_id
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.date >= ? AND t.is_confirmed = 1
        GROUP BY c.id, c.name
        ORDER BY total DESC
        LIMIT 5
    ''', (current_user['id'], start_date)).fetchall()
    
    # Análise de sazonalidade (por mês do ano)
    seasonality_data = conn.execute('''
        SELECT 
            CAST(strftime('%m', t.date) as INTEGER) as mes_numero,
            CASE strftime('%m', t.date)
                WHEN '01' THEN 'Janeiro' WHEN '02' THEN 'Fevereiro' WHEN '03' THEN 'Março'
                WHEN '04' THEN 'Abril' WHEN '05' THEN 'Maio' WHEN '06' THEN 'Junho'
                WHEN '07' THEN 'Julho' WHEN '08' THEN 'Agosto' WHEN '09' THEN 'Setembro'
                WHEN '10' THEN 'Outubro' WHEN '11' THEN 'Novembro' WHEN '12' THEN 'Dezembro'
            END as mes_nome,
            COALESCE(AVG(CASE WHEN t.transaction_type = 'receita' THEN t.amount END), 0) as receita_media,
            COALESCE(AVG(CASE WHEN t.transaction_type = 'despesa' THEN t.amount END), 0) as despesa_media
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE a.user_id = ? AND t.is_confirmed = 1
        GROUP BY strftime('%m', t.date)
        ORDER BY mes_numero
    ''', (current_user['id'],)).fetchall()
    
    conn.close()
    
    # Preparar dados para gráficos
    trends_chart = {
        'labels': [row['mes'] for row in trends_data],
        'receitas': [float(row['receitas']) for row in trends_data],
        'despesas': [float(row['despesas']) for row in trends_data]
    }
    
    categories_chart = {
        'labels': [row['categoria'] for row in top_categories],
        'values': [float(row['total']) for row in top_categories]
    }
    
    seasonality_chart = {
        'labels': [row['mes_nome'] for row in seasonality_data],
        'receitas': [float(row['receita_media']) for row in seasonality_data],
        'despesas': [float(row['despesa_media']) for row in seasonality_data]
    }
    
    return render_template('reports/trends_simple.html',
                         trends_chart=trends_chart,
                         categories_chart=categories_chart,
                         seasonality_chart=seasonality_chart,
                         trends_data=[dict(row) for row in trends_data],
                         top_categories=[dict(row) for row in top_categories])

@app.route('/reports/export/<report_type>')
@login_required
def export_report(report_type):
    """Exportar relatórios para CSV"""
    current_user = get_current_user()
    
    from io import StringIO
    import csv
    from flask import Response
    
    conn = get_db()
    output = StringIO()
    
    if report_type == 'transactions':
        # Exportar todas as transações
        data = conn.execute('''
            SELECT 
                t.date as Data,
                t.description as Descrição,
                a.name as Conta,
                c.name as Categoria,
                t.transaction_type as Tipo,
                t.amount as Valor,
                t.notes as Observações,
                t.reference as Referência,
                CASE WHEN t.is_confirmed = 1 THEN 'Confirmada' ELSE 'Pendente' END as Status
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            LEFT JOIN chart_of_accounts c ON t.chart_account_id = c.id
            WHERE a.user_id = ?
            ORDER BY t.date DESC
        ''', (current_user['id'],)).fetchall()
        
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(dict(row))
    
    elif report_type == 'accounts':
        # Exportar resumo de contas
        data = conn.execute('''
            SELECT 
                a.name as Conta,
                a.account_type as Tipo,
                a.initial_balance as 'Saldo Inicial',
                a.current_balance as 'Saldo Atual',
                COUNT(t.id) as 'Qtd Transações'
            FROM accounts a
            LEFT JOIN transactions t ON a.id = t.account_id
            WHERE a.user_id = ? AND a.is_active = 1
            GROUP BY a.id
            ORDER BY a.name
        ''', (current_user['id'],)).fetchall()
        
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(dict(row))
    
    conn.close()
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={report_type}_export.csv'}
    )

# Rotas de Contas
@app.route('/accounts')
@login_required
def accounts():
    current_user = get_current_user()
    conn = get_db()
    user_accounts = conn.execute('''
        SELECT * FROM accounts 
        WHERE user_id = ? 
        ORDER BY name
    ''', (current_user['id'],)).fetchall()
    conn.close()
    
    return render_template('accounts/index_simple.html', 
                         accounts=[dict(acc) for acc in user_accounts])

@app.route('/accounts/new', methods=['GET', 'POST'])
@login_required
def new_account():
    if request.method == 'POST':
        current_user = get_current_user()
        
        name = request.form['name']
        account_type = request.form['account_type']
        bank_name = request.form.get('bank_name', '')
        bank_code = request.form.get('bank_code', '')
        agency = request.form.get('agency', '')
        account_number = request.form.get('account_number', '')
        initial_balance = float(request.form.get('initial_balance', 0))
        credit_limit = float(request.form.get('credit_limit', 0))
        color = request.form.get('color', '#007bff')
        is_active = 'is_active' in request.form
        include_in_total = 'include_in_total' in request.form
        
        conn = get_db()
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type, bank_name, bank_code,
                                agency, account_number, initial_balance, current_balance,
                                credit_limit, color, is_active, include_in_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user['id'], name, account_type, bank_name, bank_code,
              agency, account_number, initial_balance, initial_balance,
              credit_limit, color, is_active, include_in_total))
        conn.commit()
        conn.close()
        
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('accounts'))
    
    return render_template('accounts/form_simple.html', title='Nova Conta')

# ===== ETAPA 4 - ORÇAMENTOS E METAS =====

# Orçamentos - Página Principal
@app.route('/budgets')
@login_required
def budgets():
    current_user = get_current_user()
    user_id = current_user['id']
    
    conn = get_db()
    
    # Buscar orçamentos ativos
    active_budgets = conn.execute('''
        SELECT 
            b.*,
            c.name as category_name,
            c.icon,
            (SELECT COALESCE(SUM(ABS(amount)), 0) 
             FROM transactions 
             WHERE user_id = ? AND category_id = b.category_id 
             AND date >= b.start_date AND date <= b.end_date
             AND amount < 0) as spent_amount
        FROM budgets b
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = ? AND b.is_active = 1
        ORDER BY b.created_at DESC
    ''', (user_id, user_id)).fetchall()
    
    # Calcular estatísticas
    total_budgets = len(active_budgets)
    over_budget_count = sum(1 for b in active_budgets if b['spent_amount'] > b['amount'])
    total_budget_amount = sum(b['amount'] for b in active_budgets)
    total_spent = sum(b['spent_amount'] for b in active_budgets)
    
    # Buscar categorias para novo orçamento
    categories = conn.execute('''
        SELECT id, name, icon FROM categories 
        WHERE user_id = ? OR user_id = 1
        ORDER BY name
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('budgets/index_simple.html',
                         active_budgets=active_budgets,
                         categories=categories,
                         total_budgets=total_budgets,
                         over_budget_count=over_budget_count,
                         total_budget_amount=total_budget_amount,
                         total_spent=total_spent)

# Criar Orçamento
@app.route('/budgets/create', methods=['POST'])
@login_required
def create_budget():
    current_user = get_current_user()
    user_id = current_user['id']
    
    category_id = request.form.get('category_id')
    amount = request.form.get('amount')
    period_type = request.form.get('period_type', 'monthly')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    alert_percentage = request.form.get('alert_percentage', 80)
    
    if not all([category_id, amount, start_date, end_date]):
        flash('Todos os campos são obrigatórios!', 'error')
        return redirect(url_for('budgets'))
    
    try:
        conn = get_db()
        
        # Verificar se já existe orçamento ativo para esta categoria
        existing = conn.execute('''
            SELECT id FROM budgets 
            WHERE user_id = ? AND category_id = ? AND is_active = 1
        ''', (user_id, category_id)).fetchone()
        
        if existing:
            flash('Já existe um orçamento ativo para esta categoria!', 'error')
            conn.close()
            return redirect(url_for('budgets'))
        
        # Criar novo orçamento
        conn.execute('''
            INSERT INTO budgets (user_id, category_id, amount, period_type, 
                               start_date, end_date, alert_percentage, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (user_id, category_id, float(amount), period_type, 
              start_date, end_date, int(alert_percentage), datetime.now()))
        
        conn.commit()
        conn.close()
        flash('Orçamento criado com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao criar orçamento: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

# Editar Orçamento
@app.route('/budgets/edit/<int:budget_id>', methods=['POST'])
@login_required
def edit_budget(budget_id):
    current_user = get_current_user()
    user_id = current_user['id']
    
    amount = request.form.get('amount')
    alert_percentage = request.form.get('alert_percentage')
    is_active = 1 if request.form.get('is_active') else 0
    
    try:
        conn = get_db()
        
        conn.execute('''
            UPDATE budgets 
            SET amount = ?, alert_percentage = ?, is_active = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        ''', (float(amount), int(alert_percentage), is_active, datetime.now(), budget_id, user_id))
        
        conn.commit()
        conn.close()
        flash('Orçamento atualizado com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao atualizar orçamento: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

# Excluir Orçamento
@app.route('/budgets/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    current_user = get_current_user()
    user_id = current_user['id']
    
    try:
        conn = get_db()
        conn.execute('DELETE FROM budgets WHERE id = ? AND user_id = ?', (budget_id, user_id))
        conn.commit()
        conn.close()
        flash('Orçamento excluído com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir orçamento: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

# Metas - Página Principal
@app.route('/goals')
@login_required
def goals():
    current_user = get_current_user()
    user_id = current_user['id']
    
    conn = get_db()
    
    # Buscar metas ativas
    active_goals = conn.execute('''
        SELECT 
            g.*,
            (SELECT COALESCE(SUM(amount), 0) 
             FROM goal_contributions 
             WHERE goal_id = g.id) as saved_amount
        FROM goals g
        WHERE g.user_id = ? AND g.is_active = 1
        ORDER BY g.target_date ASC
    ''', (user_id,)).fetchall()
    
    # Calcular estatísticas
    total_goals = len(active_goals)
    completed_goals = sum(1 for g in active_goals if g['saved_amount'] >= g['target_amount'])
    total_target = sum(g['target_amount'] for g in active_goals)
    total_saved = sum(g['saved_amount'] for g in active_goals)
    
    conn.close()
    
    return render_template('goals/index_simple.html',
                         active_goals=active_goals,
                         total_goals=total_goals,
                         completed_goals=completed_goals,
                         total_target=total_target,
                         total_saved=total_saved)

# Criar Meta
@app.route('/goals/create', methods=['POST'])
@login_required
def create_goal():
    current_user = get_current_user()
    user_id = current_user['id']
    
    name = request.form.get('name')
    description = request.form.get('description')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date')
    category = request.form.get('category', 'other')
    
    if not all([name, target_amount, target_date]):
        flash('Nome, valor e data são obrigatórios!', 'error')
        return redirect(url_for('goals'))
    
    try:
        conn = get_db()
        
        conn.execute('''
            INSERT INTO goals (user_id, name, description, target_amount, 
                             target_date, category, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (user_id, name, description, float(target_amount), 
              target_date, category, datetime.now()))
        
        conn.commit()
        conn.close()
        flash('Meta criada com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao criar meta: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

# Contribuir para Meta
@app.route('/goals/contribute/<int:goal_id>', methods=['POST'])
@login_required
def contribute_goal(goal_id):
    current_user = get_current_user()
    user_id = current_user['id']
    
    amount = request.form.get('amount')
    description = request.form.get('description', '')
    
    if not amount:
        flash('Valor da contribuição é obrigatório!', 'error')
        return redirect(url_for('goals'))
    
    try:
        conn = get_db()
        
        # Verificar se a meta pertence ao usuário
        goal = conn.execute('''
            SELECT id FROM goals WHERE id = ? AND user_id = ?
        ''', (goal_id, user_id)).fetchone()
        
        if not goal:
            flash('Meta não encontrada!', 'error')
            conn.close()
            return redirect(url_for('goals'))
        
        # Adicionar contribuição
        conn.execute('''
            INSERT INTO goal_contributions (goal_id, amount, description, created_at)
            VALUES (?, ?, ?, ?)
        ''', (goal_id, float(amount), description, datetime.now()))
        
        conn.commit()
        conn.close()
        flash('Contribuição adicionada com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao adicionar contribuição: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

# Excluir Meta
@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    current_user = get_current_user()
    user_id = current_user['id']
    
    try:
        conn = get_db()
        # Primeiro, excluir contribuições
        conn.execute('DELETE FROM goal_contributions WHERE goal_id = ?', (goal_id,))
        # Depois, excluir a meta
        conn.execute('DELETE FROM goals WHERE id = ? AND user_id = ?', (goal_id, user_id))
        conn.commit()
        conn.close()
        flash('Meta excluída com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir meta: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

# Planejamento Financeiro
@app.route('/planning')
@login_required
def planning():
    current_user = get_current_user()
    user_id = current_user['id']
    
    conn = get_db()
    
    # Resumo de orçamentos
    budget_summary = conn.execute('''
        SELECT 
            COUNT(*) as total_budgets,
            COALESCE(SUM(amount), 0) as total_budget,
            COALESCE(SUM(CASE 
                WHEN (SELECT SUM(ABS(amount)) FROM transactions 
                      WHERE user_id = ? AND category_id = b.category_id 
                      AND date >= b.start_date AND date <= b.end_date
                      AND amount < 0) > b.amount 
                THEN 1 ELSE 0 END), 0) as over_budget_count
        FROM budgets b
        WHERE b.user_id = ? AND b.is_active = 1
    ''', (user_id, user_id)).fetchone()
    
    # Resumo de metas
    goal_summary = conn.execute('''
        SELECT 
            COUNT(*) as total_goals,
            COALESCE(SUM(target_amount), 0) as total_target,
            (SELECT COALESCE(SUM(amount), 0) FROM goal_contributions gc 
             JOIN goals g ON gc.goal_id = g.id WHERE g.user_id = ?) as total_saved
        FROM goals
        WHERE user_id = ? AND is_active = 1
    ''', (user_id, user_id)).fetchone()
    
    # Próximas metas a vencer
    upcoming_goals = conn.execute('''
        SELECT name, target_amount, target_date,
               (SELECT COALESCE(SUM(amount), 0) FROM goal_contributions WHERE goal_id = g.id) as saved_amount
        FROM goals g
        WHERE user_id = ? AND is_active = 1 AND target_date >= date('now')
        ORDER BY target_date ASC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Análise de gastos por categoria (últimos 3 meses)
    spending_analysis = conn.execute('''
        SELECT 
            c.name as category,
            c.icon,
            SUM(ABS(t.amount)) as spent,
            COUNT(*) as transaction_count,
            AVG(ABS(t.amount)) as avg_transaction
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ? AND t.amount < 0 
        AND t.date >= date('now', '-3 months')
        GROUP BY t.category_id, c.name, c.icon
        ORDER BY spent DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('planning/index_simple.html',
                         budget_summary=budget_summary,
                         goal_summary=goal_summary,
                         upcoming_goals=upcoming_goals,
                         spending_analysis=spending_analysis)

# Inicializar dados padrão
def create_default_data():
    conn = get_db()
    
    # Verificar se já existem dados
    if conn.execute('SELECT COUNT(*) FROM chart_of_accounts').fetchone()[0] > 0:
        conn.close()
        return
    
    # Criar plano de contas padrão
    accounts_data = [
        ('3.1', 'RECEITAS', None, 'receita', True),
        ('3.1.01', 'Salários', '3.1', 'receita', False),
        ('3.1.02', 'Freelances', '3.1', 'receita', False),
        ('3.1.03', 'Investimentos', '3.1', 'receita', False),
        ('3.1.04', 'Outras Receitas', '3.1', 'receita', False),
        
        ('4.1', 'DESPESAS', None, 'despesa', True),
        ('4.1.01', 'Moradia', '4.1', 'despesa', False),
        ('4.1.02', 'Alimentação', '4.1', 'despesa', False),
        ('4.1.03', 'Transporte', '4.1', 'despesa', False),
        ('4.1.04', 'Saúde', '4.1', 'despesa', False),
        ('4.1.05', 'Educação', '4.1', 'despesa', False),
        ('4.1.06', 'Lazer', '4.1', 'despesa', False),
        ('4.1.07', 'Outras Despesas', '4.1', 'despesa', False),
    ]
    
    account_ids = {}
    for code, name, parent_code, acc_type, is_summary in accounts_data:
        parent_id = account_ids.get(parent_code) if parent_code else None
        level = code.count('.') - 1
        
        cursor = conn.execute('''
            INSERT INTO chart_of_accounts (code, name, parent_id, level, account_type, is_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code, name, parent_id, level, acc_type, is_summary))
        
        account_ids[code] = cursor.lastrowid
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    with app.app_context():
        init_db()
        create_default_data()
    
    app.run(debug=True, host='127.0.0.1', port=5000)
