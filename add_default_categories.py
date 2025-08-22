"""
Script para adicionar categorias padrão se não existirem
"""
import sqlite3

def add_default_categories():
    """Adiciona categorias padrão ao banco de dados"""
    
    db_path = 'finance_planner_saas.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se já existem categorias padrão
        cursor.execute("SELECT COUNT(*) FROM categories WHERE user_id = 1")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print("✅ Categorias padrão já existem")
            return
        
        # Adicionar categorias padrão
        default_categories = [
            (1, 'Alimentação', 'expense', 'Gastos com comida e restaurantes', '🍽️'),
            (1, 'Transporte', 'expense', 'Combustível, transporte público, manutenção', '🚗'),
            (1, 'Moradia', 'expense', 'Aluguel, financiamento, condomínio', '🏠'),
            (1, 'Saúde', 'expense', 'Consultas, medicamentos, plano de saúde', '🏥'),
            (1, 'Educação', 'expense', 'Cursos, livros, material escolar', '📚'),
            (1, 'Lazer', 'expense', 'Cinema, viagens, hobbies', '🎵'),
            (1, 'Compras', 'expense', 'Roupas, eletrônicos, utensílios', '🛍️'),
            (1, 'Contas', 'expense', 'Luz, água, internet, telefone', '📄'),
            (1, 'Outros Gastos', 'expense', 'Outras despesas não categorizadas', '📋'),
            (1, 'Salário', 'income', 'Salário principal', '💰'),
            (1, 'Freelance', 'income', 'Trabalhos extras', '💼'),
            (1, 'Investimentos', 'income', 'Dividendos, juros', '📈'),
            (1, 'Outras Receitas', 'income', 'Outras fontes de renda', '💵'),
        ]
        
        for user_id, name, cat_type, desc, icon in default_categories:
            cursor.execute('''
                INSERT INTO categories (user_id, name, category_type, description, icon, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (user_id, name, cat_type, desc, icon))
        
        conn.commit()
        print(f"✅ {len(default_categories)} categorias padrão adicionadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar categorias: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏷️ Adicionando categorias padrão...")
    add_default_categories()
