"""
VERSÃO DEBUG DO ROUTE TRANSACTIONS - Para identificar erro 500 em produção
"""

# Adicione este route temporário no app_simple_advanced.py para debug
@app.route('/transactions_debug')
@login_required
def transactions_debug():
    """Versão debug simplificada do route transactions"""
    try:
        app.logger.info("🐛 DEBUG: Iniciando transactions_debug")
        
        # Teste 1: Verificar usuário
        current_user = get_current_user()
        if not current_user:
            return f"❌ DEBUG: Usuário não encontrado na sessão"
        
        app.logger.info(f"✅ DEBUG: Usuário encontrado - ID: {current_user['id']}")
        
        # Teste 2: Conexão com banco
        try:
            conn = get_db()
            app.logger.info("✅ DEBUG: Conexão com banco estabelecida")
        except Exception as e:
            return f"❌ DEBUG: Erro na conexão com banco: {str(e)}"
        
        # Teste 3: Query simples
        try:
            simple_query = "SELECT COUNT(*) as count FROM transactions"
            result = conn.execute(simple_query).fetchone()
            total_transactions = result[0] if result else 0
            app.logger.info(f"✅ DEBUG: Total transações no banco: {total_transactions}")
        except Exception as e:
            conn.close()
            return f"❌ DEBUG: Erro na query simples: {str(e)}"
        
        # Teste 4: Query com JOIN
        try:
            join_query = '''
            SELECT COUNT(*) as count 
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
            WHERE (a.user_id = ? OR t.user_id = ?)
            '''
            result = conn.execute(join_query, (current_user['id'], current_user['id'])).fetchone()
            user_transactions = result[0] if result else 0
            app.logger.info(f"✅ DEBUG: Transações do usuário: {user_transactions}")
        except Exception as e:
            conn.close()
            return f"❌ DEBUG: Erro na query com JOIN: {str(e)}"
        
        # Teste 5: Query completa (limitada)
        try:
            full_query = '''
            SELECT 
                t.id, t.description, t.amount, t.type, t.date,
                a.name as account_name
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
            WHERE (a.user_id = ? OR t.user_id = ?)
            ORDER BY t.date DESC
            LIMIT 10
            '''
            transactions = conn.execute(full_query, (current_user['id'], current_user['id'])).fetchall()
            app.logger.info(f"✅ DEBUG: Query completa executada - {len(transactions)} resultados")
        except Exception as e:
            conn.close()
            return f"❌ DEBUG: Erro na query completa: {str(e)}"
        
        conn.close()
        
        # Retornar resultado de debug
        debug_info = f"""
        <h2>🐛 DEBUG TRANSACTIONS - PRODUÇÃO</h2>
        <ul>
            <li>✅ Usuário: {current_user['email']} (ID: {current_user['id']})</li>
            <li>✅ Total transações no sistema: {total_transactions}</li>
            <li>✅ Transações do usuário: {user_transactions}</li>
            <li>✅ Query completa executada: {len(transactions)} resultados</li>
        </ul>
        <h3>Primeiras transações:</h3>
        <ul>
        """
        
        for t in transactions:
            debug_info += f"<li>{t['date']} - {t['description']} - R$ {t['amount']:.2f}</li>"
        
        debug_info += "</ul><p><a href='/'>← Voltar</a></p>"
        
        return debug_info
        
    except Exception as e:
        app.logger.error(f"❌ DEBUG: Erro geral: {str(e)}")
        return f"❌ DEBUG: Erro geral no route: {str(e)}"
