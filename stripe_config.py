# CONFIGURAÇÃO STRIPE - SUBSTITUA PELAS SUAS CHAVES REAIS

# Chaves de teste do Stripe (substitua pelas suas chaves reais)
STRIPE_PUBLISHABLE_KEY = "pk_test_51234567890abcdef..."  # Sua chave pública do Stripe
STRIPE_SECRET_KEY = "sk_test_51234567890abcdef..."       # Sua chave secreta do Stripe

# URLs para webhooks (configure no dashboard do Stripe)
STRIPE_WEBHOOK_SECRET = "whsec_1234567890abcdef..."     # Endpoint secret do webhook

# Configurações de preços (IDs dos produtos no Stripe)
STRIPE_PRICE_IDS = {
    'monthly': 'price_1234567890abcdef...',      # ID do preço mensal no Stripe
    'semester': 'price_1234567890abcdef...',     # ID do preço semestral no Stripe
    'annual': 'price_1234567890abcdef...',       # ID do preço anual no Stripe
}

# INSTRUÇÕES PARA CONFIGURAÇÃO:
# 
# 1. Acesse https://dashboard.stripe.com
# 2. Crie uma conta ou faça login
# 3. Vá em "Developers" > "API keys"
# 4. Copie sua "Publishable key" e "Secret key"
# 5. Substitua os valores acima
# 6. Em "Products", crie produtos para cada plano
# 7. Copie os IDs dos preços e atualize STRIPE_PRICE_IDS
# 8. Configure webhooks em "Developers" > "Webhooks"

# IMPORTANTE: NUNCA COMMITE SUAS CHAVES REAIS NO GIT!
# Adicione este arquivo ao .gitignore em produção
