"""
Rotas de pagamento com Pagar.me para o FynanPro
Adicione este código ao seu app.py principal
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from pagarme_config import (
    process_credit_card_payment, 
    process_boleto_payment, 
    process_pix_payment,
    create_pagarme_customer,
    create_subscription,
    verify_transaction_status
)
import json
from datetime import datetime, timedelta

# Rota para exibir página de pagamento
@app.route('/payment/pagarme')
@login_required
def payment_pagarme():
    """Página de pagamento com Pagar.me"""
    return render_template('payment_pagarme.html')

# Rota para processar pagamento
@app.route('/process_pagarme_payment', methods=['POST'])
@login_required
def process_pagarme_payment():
    """Processa pagamento via Pagar.me"""
    try:
        data = request.get_json()
        
        # Dados do pagamento
        payment_method = data.get('payment_method')
        amount = data.get('amount')  # Valor em centavos
        plan = data.get('plan')
        
        # Dados do cliente
        payment_data = {
            'amount': amount,
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email'),
            'cpf': data.get('customer_cpf', '').replace('.', '').replace('-', ''),
            'phone': data.get('customer_phone', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', ''),
            'phone_ddd': data.get('customer_phone', '')[:2] if data.get('customer_phone') else '11'
        }
        
        # Processar conforme método de pagamento
        transaction = None
        
        if payment_method == 'credit_card':
            # Adicionar dados do cartão
            payment_data.update({
                'card_number': data.get('card_number', '').replace(' ', ''),
                'card_holder_name': data.get('card_holder_name'),
                'card_expiration_date': data.get('card_expiry', '').replace('/', ''),
                'card_cvv': data.get('card_cvv')
            })
            transaction = process_credit_card_payment(payment_data)
            
        elif payment_method == 'boleto':
            transaction = process_boleto_payment(payment_data)
            
        elif payment_method == 'pix':
            transaction = process_pix_payment(payment_data)
        
        if transaction and transaction.get('status') in ['paid', 'authorized', 'waiting_payment']:
            # Atualizar usuário no banco
            session_db = Session()
            user = session_db.query(User).filter_by(id=current_user.id).first()
            
            if user:
                # Calcular data de expiração
                if plan == 'mensal':
                    expiry_date = datetime.now() + timedelta(days=30)
                elif plan == 'semestral':
                    expiry_date = datetime.now() + timedelta(days=180)
                else:  # anual
                    expiry_date = datetime.now() + timedelta(days=365)
                
                # Atualizar usuário
                user.plan_type = plan
                user.plan_start_date = datetime.now()
                user.plan_expiry_date = expiry_date
                user.payment_method = 'pagarme'
                user.pagarme_customer_id = transaction.get('customer', {}).get('id')
                user.pagarme_transaction_id = transaction.get('id')
                
                if transaction.get('status') == 'paid':
                    user.last_payment_date = datetime.now()
                    user.total_paid += amount / 100  # Converter centavos para reais
                
                session_db.commit()
                session_db.close()
                
                # Resposta baseada no status
                if transaction.get('status') == 'paid':
                    return jsonify({
                        'success': True,
                        'message': 'Pagamento aprovado!',
                        'redirect_url': '/dashboard'
                    })
                elif transaction.get('status') == 'waiting_payment':
                    return jsonify({
                        'success': True,
                        'message': 'Aguardando pagamento',
                        'boleto_url': transaction.get('boleto_url'),
                        'qr_code': transaction.get('qr_code'),
                        'redirect_url': '/payment/success'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Pagamento autorizado',
                        'redirect_url': '/dashboard'
                    })
            
        else:
            error_message = 'Erro no pagamento'
            if transaction and transaction.get('refuse_reason'):
                error_message = transaction.get('refuse_reason')
            
            return jsonify({
                'success': False,
                'message': error_message
            })
            
    except Exception as e:
        print(f"Erro no pagamento: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno no servidor'
        })

# Rota para sucesso do pagamento
@app.route('/payment/success')
@login_required
def payment_success():
    """Página de sucesso do pagamento"""
    return render_template('payment_success.html')

# Webhook do Pagar.me
@app.route('/webhook/pagarme', methods=['POST'])
def pagarme_webhook():
    """Webhook para receber notificações do Pagar.me"""
    try:
        data = request.get_json()
        
        if data.get('object') == 'transaction':
            transaction_id = data.get('id')
            status = data.get('status')
            
            # Buscar usuário pela transaction_id
            session_db = Session()
            user = session_db.query(User).filter_by(pagarme_transaction_id=transaction_id).first()
            
            if user:
                if status == 'paid':
                    # Pagamento confirmado
                    user.last_payment_date = datetime.now()
                    amount = data.get('amount', 0) / 100  # Converter para reais
                    user.total_paid += amount
                    
                    # Ativar plano se necessário
                    if user.plan_type in ['trial', 'free']:
                        user.plan_type = 'premium'
                        user.plan_start_date = datetime.now()
                        user.plan_expiry_date = datetime.now() + timedelta(days=30)
                    
                elif status == 'refused':
                    # Pagamento recusado
                    user.plan_type = 'trial' if user.plan_type == 'premium' else user.plan_type
                
                session_db.commit()
                session_db.close()
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({'status': 'error'})

# Função para verificar status de assinatura
def check_subscription_status(user):
    """Verifica se a assinatura do usuário está ativa"""
    if not user.plan_expiry_date:
        return False
    
    return datetime.now() < user.plan_expiry_date

# Função para atualizar banco com campos do Pagar.me
def update_database_for_pagarme():
    """Adiciona campos necessários para o Pagar.me"""
    import sqlite3
    
    conn = sqlite3.connect('finance_planner_saas.db')
    cursor = conn.cursor()
    
    try:
        # Adicionar campos do Pagar.me
        cursor.execute("ALTER TABLE users ADD COLUMN pagarme_customer_id TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN pagarme_transaction_id TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN plan_expiry_date DATETIME")
        
        conn.commit()
        print("✅ Campos do Pagar.me adicionados ao banco")
        
    except Exception as e:
        print(f"Campos já existem ou erro: {e}")
    
    finally:
        conn.close()

# Executar atualização do banco (chame uma vez)
if __name__ == "__main__":
    update_database_for_pagarme()
