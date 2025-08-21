-- migration_add_type_column.sql
-- Migração SQL direta para SQLite

-- 1. Verificar estrutura atual da tabela
.schema transactions

-- 2. Adicionar a coluna type se não existir
-- CUIDADO: SQLite não suporta ADD COLUMN com NOT NULL diretamente
-- Então fazemos em etapas:

-- Etapa 1: Adicionar coluna como nullable
ALTER TABLE transactions ADD COLUMN type TEXT;

-- Etapa 2: Atualizar registros existentes com valor padrão
UPDATE transactions SET type = 'expense' WHERE type IS NULL;

-- Etapa 3: Se necessário, criar uma nova tabela com constraint NOT NULL
-- e migrar os dados (mais seguro para produção)

-- Verificação final
SELECT COUNT(*) as total_records, 
       COUNT(type) as records_with_type 
FROM transactions;

-- Schema final esperado:
/*
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL DEFAULT 'expense',
    category TEXT,
    date DATETIME NOT NULL,
    notes TEXT,
    account_id INTEGER,
    transfer_to_account_id INTEGER,
    transfer_from_account_id INTEGER,
    is_transfer BOOLEAN DEFAULT 0,
    is_adjustment BOOLEAN DEFAULT 0,
    adjustment_reason TEXT,
    recurrence_type TEXT,
    recurrence_interval INTEGER,
    recurrence_count INTEGER,
    current_occurrence INTEGER,
    parent_transaction_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
*/
