"""
Configuração do Pagar.me para o FynanPro
"""
import os
import requests

# Configurações do Pagar.me
PAGARME_API_KEY = os.environ.get('PAGARME_API_KEY', 'ak_test_sua_chave_aqui')
PAGARME_ENCRYPTION_KEY = os.environ.get('PAGARME_ENCRYPTION_KEY', 'ek_test_sua_chave_aqui')
PAGARME_API_URL = 'https://api.pagar.me/1'

# Importar pagarme se disponível, senão usar requests
try:
    import pagarme
    pagarme.authentication_key(PAGARME_API_KEY)
    PAGARME_AVAILABLE = True
except ImportError:
    print("⚠️ Módulo pagarme não encontrado, usando requests diretamente")
    pagarme = None
    PAGARME_AVAILABLE = False

# Planos de assinatura em centavos (R$)
PLAN_PRICES_BRL = {
    'mensal': 1900,      # R$ 19,00/mês
    'semestral': 8900,   # R$ 89,00/semestre (economia de ~22%)  
    'anual': 14900       # R$ 149,00/ano (economia de ~35%)
}

def create_pagarme_customer(user_data):
    """
    Cria um cliente no Pagar.me
    """
    try:
        customer = pagarme.customer.create({
            'name': user_data['name'],
            'email': user_data['email'],
            'document_number': user_data.get('cpf', ''),
            'address': {
                'street': user_data.get('address', 'Rua Exemplo'),
                'street_number': user_data.get('street_number', '123'),
                'neighborhood': user_data.get('neighborhood', 'Centro'),
                'zipcode': user_data.get('zipcode', '01234567'),
                'city': user_data.get('city', 'São Paulo'),
                'state': user_data.get('state', 'SP'),
                'country': 'br'
            },
            'phone': {
                'ddd': user_data.get('phone_ddd', '11'),
                'number': user_data.get('phone', '999999999')
            }
        })
        return customer
    except Exception as e:
        print(f"Erro ao criar cliente Pagar.me: {e}")
        return None

def create_subscription(customer_id, plan_type):
    """
    Cria uma assinatura no Pagar.me
    """
    try:
        amount = PLAN_PRICES_BRL.get(plan_type, 1900)
        
        subscription = pagarme.subscription.create({
            'plan': {
                'amount': amount,
                'days': 30 if plan_type == 'mensal' else (180 if plan_type == 'semestral' else 365),
                'name': f'FynanPro - Plano {plan_type.title()}'
            },
            'customer': {
                'id': customer_id
            },
            'payment_method': 'credit_card',
            'postback_url': 'https://seu-dominio.com/webhook/pagarme'
        })
        
        return subscription
    except Exception as e:
        print(f"Erro ao criar assinatura: {e}")
        return None

def process_credit_card_payment(payment_data):
    """
    Processa pagamento com cartão de crédito
    """
    try:
        transaction = pagarme.transaction.create({
            'amount': payment_data['amount'],
            'payment_method': 'credit_card',
            'card_number': payment_data['card_number'],
            'card_holder_name': payment_data['card_holder_name'],
            'card_expiration_date': payment_data['card_expiration_date'],
            'card_cvv': payment_data['card_cvv'],
            'customer': {
                'name': payment_data['customer_name'],
                'email': payment_data['customer_email'],
                'document_number': payment_data.get('cpf', ''),
                'address': {
                    'street': payment_data.get('address', 'Rua Exemplo'),
                    'street_number': payment_data.get('street_number', '123'),
                    'neighborhood': payment_data.get('neighborhood', 'Centro'),
                    'zipcode': payment_data.get('zipcode', '01234567'),
                    'city': payment_data.get('city', 'São Paulo'),
                    'state': payment_data.get('state', 'SP'),
                    'country': 'br'
                },
                'phone': {
                    'ddd': payment_data.get('phone_ddd', '11'),
                    'number': payment_data.get('phone', '999999999')
                }
            }
        })
        
        return transaction
    except Exception as e:
        print(f"Erro ao processar pagamento: {e}")
        return None

def process_boleto_payment(payment_data):
    """
    Processa pagamento com boleto bancário
    """
    try:
        transaction = pagarme.transaction.create({
            'amount': payment_data['amount'],
            'payment_method': 'boleto',
            'customer': {
                'name': payment_data['customer_name'],
                'email': payment_data['customer_email'],
                'document_number': payment_data.get('cpf', ''),
                'address': {
                    'street': payment_data.get('address', 'Rua Exemplo'),
                    'street_number': payment_data.get('street_number', '123'),
                    'neighborhood': payment_data.get('neighborhood', 'Centro'),
                    'zipcode': payment_data.get('zipcode', '01234567'),
                    'city': payment_data.get('city', 'São Paulo'),
                    'state': payment_data.get('state', 'SP'),
                    'country': 'br'
                },
                'phone': {
                    'ddd': payment_data.get('phone_ddd', '11'),
                    'number': payment_data.get('phone', '999999999')
                }
            }
        })
        
        return transaction
    except Exception as e:
        print(f"Erro ao processar boleto: {e}")
        return None

def process_pix_payment(payment_data):
    """
    Processa pagamento via PIX
    """
    try:
        transaction = pagarme.transaction.create({
            'amount': payment_data['amount'],
            'payment_method': 'pix',
            'customer': {
                'name': payment_data['customer_name'],
                'email': payment_data['customer_email'],
                'document_number': payment_data.get('cpf', ''),
                'address': {
                    'street': payment_data.get('address', 'Rua Exemplo'),
                    'street_number': payment_data.get('street_number', '123'),
                    'neighborhood': payment_data.get('neighborhood', 'Centro'),
                    'zipcode': payment_data.get('zipcode', '01234567'),
                    'city': payment_data.get('city', 'São Paulo'),
                    'state': payment_data.get('state', 'SP'),
                    'country': 'br'
                }
            }
        })
        
        return transaction
    except Exception as e:
        print(f"Erro ao processar PIX: {e}")
        return None

def verify_transaction_status(transaction_id):
    """
    Verifica o status de uma transação
    """
    try:
        transaction = pagarme.transaction.find_by_id(transaction_id)
        return transaction
    except Exception as e:
        print(f"Erro ao verificar transação: {e}")
        return None
