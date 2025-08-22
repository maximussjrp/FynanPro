"""
Script para adicionar tabelas de Orçamentos e Metas (Etapa 4)
Execute este arquivo para criar as tabelas necessárias para a Etapa 4
"""
import sqlite3
import os
from datetime import datetime

def create_budget_goals_tables():
    """Cria as tabelas para orçamentos e metas"""
    
    db_path = 'finance_planner_saas.db'
    print(f"🗄️ Conectando ao banco: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tabela de orçamentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                period_type VARCHAR(20) DEFAULT 'monthly',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                alert_percentage INTEGER DEFAULT 80,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        print("✅ Tabela 'budgets' criada")
        
        # Tabela de metas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                target_amount REAL NOT NULL,
                target_date DATE NOT NULL,
                category VARCHAR(50) DEFAULT 'other',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Tabela 'goals' criada")
        
        # Tabela de contribuições para metas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals (id)
            )
        ''')
        print("✅ Tabela 'goal_contributions' criada")
        
        # Adicionar algumas categorias padrão se não existirem
        cursor.execute("SELECT COUNT(*) FROM categories WHERE user_id = 1")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                (1, 'Alimentação', 'despesa', 'Gastos com comida e restaurantes', '🍽️'),
                (1, 'Transporte', 'despesa', 'Combustível, transporte público, manutenção', '🚗'),
                (1, 'Moradia', 'despesa', 'Aluguel, financiamento, condomínio', '🏠'),
                (1, 'Saúde', 'despesa', 'Consultas, medicamentos, plano de saúde', '🏥'),
                (1, 'Educação', 'despesa', 'Cursos, livros, material escolar', '📚'),
                (1, 'Lazer', 'despesa', 'Cinema, viagens, hobbies', '🎵'),
                (1, 'Compras', 'despesa', 'Roupas, eletrônicos, utensílios', '🛍️'),
                (1, 'Contas', 'despesa', 'Luz, água, internet, telefone', '📄'),
                (1, 'Salário', 'receita', 'Salário principal', '💰'),
                (1, 'Freelance', 'receita', 'Trabalhos extras', '💼'),
                (1, 'Investimentos', 'receita', 'Dividendos, juros', '📈'),
                (1, 'Outras Receitas', 'receita', 'Outras fontes de renda', '💵'),
            ]
            
            for user_id, name, cat_type, desc, icon in default_categories:
                cursor.execute('''
                    INSERT INTO categories (user_id, name, category_type, description, icon)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, cat_type, desc, icon))
            
            print("✅ Categorias padrão adicionadas")
        
        # Commit das alterações
        conn.commit()
        print("\n🎉 Tabelas de Orçamentos e Metas criadas com sucesso!")
        print("📊 Sistema de planejamento financeiro pronto para uso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Criando tabelas de Orçamentos e Metas (Etapa 4)...")
    create_budget_goals_tables()
