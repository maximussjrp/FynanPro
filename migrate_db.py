import sqlite3
from datetime import datetime, timedelta

def migrate_database():
    conn = sqlite3.connect('finance_planner_saas.db')
    cursor = conn.cursor()
    
    try:
        # Adicionar novas colunas se não existirem
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN plan_type TEXT DEFAULT 'trial'")
            print("Coluna plan_type adicionada")
        except sqlite3.OperationalError:
            print("Coluna plan_type já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN plan_start_date DATETIME")
            print("Coluna plan_start_date adicionada")
        except sqlite3.OperationalError:
            print("Coluna plan_start_date já existe")
        
        # Adicionar colunas de pagamento
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
            print("Coluna stripe_customer_id adicionada")
        except sqlite3.OperationalError:
            print("Coluna stripe_customer_id já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT")
            print("Coluna stripe_subscription_id adicionada")
        except sqlite3.OperationalError:
            print("Coluna stripe_subscription_id já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN payment_method TEXT DEFAULT 'free'")
            print("Coluna payment_method adicionada")
        except sqlite3.OperationalError:
            print("Coluna payment_method já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_payment_date DATETIME")
            print("Coluna last_payment_date adicionada")
        except sqlite3.OperationalError:
            print("Coluna last_payment_date já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN total_paid REAL DEFAULT 0.0")
            print("Coluna total_paid adicionada")
        except sqlite3.OperationalError:
            print("Coluna total_paid já existe")
        
        # Criar tabela de mensagens de chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("Tabela chat_messages criada ou já existe")
        
        # Criar tabela de respostas rápidas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                response TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Tabela quick_replies criada ou já existe")
        
        # Criar tabela de agentes de suporte
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        print("Tabela support_agents criada ou já existe")
        
        # Adicionar coluna replied_by_agent_id na tabela chat_messages se não existir
        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN replied_by_agent_id INTEGER")
            print("Coluna replied_by_agent_id adicionada à tabela chat_messages")
        except sqlite3.OperationalError:
            print("Coluna replied_by_agent_id já existe na tabela chat_messages")
        
        # Inserir respostas rápidas padrão
        default_replies = [
            # Respostas sobre planos e pagamentos
            ('plano', 'Temos planos a partir de R$ 9,90/mês! Acesse "Planos" no menu para ver todas as opções. 😊'),
            ('pagamento', 'Aceitamos cartão de crédito via Stripe e PIX. Todos os pagamentos são seguros. Precisa de ajuda com algum pagamento?'),
            ('teste', 'Você tem 7 dias grátis para testar todas as funcionalidades premium! Quer começar seu teste agora?'),
            ('cancelar', 'Para cancelar sua assinatura, acesse seu perfil e clique em "Gerenciar Plano". Você pode cancelar a qualquer momento sem multas.'),
            ('suporte', 'Conectando você com um atendente humano... Por favor, aguarde ou envie um email para suporte@financesaas.com'),
            
            # Respostas sobre funcionalidades do sistema
            ('lançamento', 'Para adicionar uma transação: 1) Clique em "Nova Transação" no menu, 2) Preencha descrição, valor e categoria, 3) Escolha se é receita ou despesa. É bem simples! 💰'),
            ('transação', 'Para gerenciar suas transações: Acesse "Transações" no menu para ver histórico, editar ou excluir lançamentos. Você pode filtrar por período e categoria! 📊'),
            ('categoria', 'As categorias organizam seus gastos! Acesse "Categorias" no menu para criar novas ou editar existentes. Temos categorias pré-definidas como Alimentação, Transporte, etc. 🏷️'),
            ('relatório', 'Seus relatórios estão em "Indicadores" e "Saúde Financeira". Veja gráficos de gastos por categoria, evolução mensal e dicas personalizadas! 📈'),
            ('dashboard', 'O Dashboard mostra seu resumo financeiro: saldo atual, receitas e despesas do mês, e principais categorias de gastos. É sua visão geral das finanças! 📋'),
            
            # Respostas sobre uso específico
            ('como usar', 'Acesse o Dashboard para ver seu resumo financeiro. Use "Nova Transação" para adicionar receitas/despesas e "Categorias" para organizar seus gastos.'),
            ('receita', 'Para lançar uma receita: 1) Nova Transação → 2) Escolha "Receita" → 3) Digite valor e descrição → 4) Selecione categoria (Salário, Freelance, etc.) → 5) Salvar! 💚'),
            ('despesa', 'Para lançar uma despesa: 1) Nova Transação → 2) Escolha "Despesa" → 3) Digite valor e descrição → 4) Selecione categoria (Alimentação, Transporte, etc.) → 5) Salvar! ❌'),
            ('saldo', 'Seu saldo é calculado automaticamente: Receitas - Despesas = Saldo atual. Veja no Dashboard ou em Indicadores para análise detalhada! 💰'),
            
            # Respostas sobre problemas técnicos
            ('erro', 'Se está com problemas técnicos: 1) Atualize a página (F5), 2) Limpe cache do navegador, 3) Tente outro navegador. Se persistir, nos contate! 🔧'),
            ('login', 'Problemas de login? Verifique email/senha, tente recuperar senha ou limpe cookies do navegador. Precisa de ajuda específica? 🔐'),
            ('lento', 'Se o sistema está lento: Verifique sua conexão, feche outras abas e limpe cache. Nossos servidores estão sempre otimizados! ⚡'),
            
            # Respostas sobre recursos premium
            ('gratuito', 'No plano gratuito você tem: até 50 transações/mês, categorias básicas e relatórios simples. Planos pagos têm recursos ilimitados! 🆓'),
            ('premium', 'Recursos premium incluem: transações ilimitadas, categorias personalizadas, relatórios avançados, metas financeiras e backup automático! ⭐'),
            ('limite', 'No plano gratuito há limite de 50 transações/mês. Para uso ilimitado, considere nossos planos a partir de R$ 9,90/mês! 📊'),
            
            # Respostas sobre segurança
            ('segurança', 'Seus dados estão seguros! Usamos criptografia SSL, senhas hasheadas e servidores protegidos. Nunca compartilhamos informações pessoais! 🔒'),
            ('dados', 'Respeitamos sua privacidade: dados criptografados, sem venda para terceiros, backup seguro e conformidade com LGPD! 🛡️'),
            ('backup', 'Fazemos backup automático dos seus dados. Planos premium incluem backup diário e recuperação fácil! 💾')
        ]
        
        for keyword, response in default_replies:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO quick_replies (keyword, response) 
                    VALUES (?, ?)
                ''', (keyword, response))
                print(f"Resposta rápida '{keyword}' adicionada")
            except sqlite3.Error as e:
                print(f"Erro ao adicionar resposta '{keyword}': {e}")
        
        # Criar agente de suporte padrão se não existir
        import bcrypt
        
        # Verificar se já existe algum agente
        cursor.execute("SELECT COUNT(*) FROM support_agents")
        agent_count = cursor.fetchone()[0]
        
        if agent_count == 0:
            # Criar agente padrão
            default_password = "suporte123"
            password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            try:
                cursor.execute('''
                    INSERT INTO support_agents (name, email, password_hash) 
                    VALUES (?, ?, ?)
                ''', ("Agente Suporte", "suporte@financesaas.com", password_hash))
                print("✅ Agente de suporte padrão criado:")
                print("   Email: suporte@financesaas.com")
                print("   Senha: suporte123")
                print("   ⚠️  ALTERE ESTA SENHA APÓS O PRIMEIRO LOGIN!")
            except sqlite3.Error as e:
                print(f"Erro ao criar agente padrão: {e}")
        else:
            print(f"Já existem {agent_count} agentes de suporte cadastrados")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN plan_end_date DATETIME")
            print("Coluna plan_end_date adicionada")
        except sqlite3.OperationalError:
            print("Coluna plan_end_date já existe")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT 0")
            print("Coluna trial_used adicionada")
        except sqlite3.OperationalError:
            print("Coluna trial_used já existe")
        
        # Atualizar usuários existentes para ter período de teste
        now = datetime.now()
        trial_end = now + timedelta(days=7)
        
        cursor.execute("""
            UPDATE users 
            SET plan_type = 'trial',
                plan_start_date = ?,
                plan_end_date = ?,
                trial_used = 1
            WHERE plan_type IS NULL OR plan_type = ''
        """, (now.isoformat(), trial_end.isoformat()))
        
        print(f"Atualizados {cursor.rowcount} usuários para período de teste")
        
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
