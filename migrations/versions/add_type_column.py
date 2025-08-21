# migration_fix_transaction_type.py
"""
Migração para adicionar coluna type na tabela transactions
Comando: flask db revision --message="Add type column to transactions"
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

def upgrade():
    # Verificar se a coluna já existe antes de tentar adicionar
    conn = op.get_bind()
    
    # Para SQLite, verificamos o schema
    result = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
    columns = [row[1] for row in result]
    
    if 'type' not in columns:
        # Adicionar a coluna type com valor padrão
        op.add_column('transactions', sa.Column('type', sa.String(20), nullable=False, default='expense'))
        
        # Atualizar registros existentes (opcional)
        conn.execute(text("""
            UPDATE transactions 
            SET type = 'expense' 
            WHERE type IS NULL OR type = ''
        """))
        
        print("✅ Coluna 'type' adicionada com sucesso!")
    else:
        print("⚠️ Coluna 'type' já existe!")

def downgrade():
    # Para SQLite, precisamos recriar a tabela sem a coluna
    # Isso é mais complexo, então vamos apenas avisar
    print("⚠️ Downgrade para SQLite requer recriação da tabela")
    # op.drop_column('transactions', 'type')
