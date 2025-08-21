# models.py - Modelo Transaction corrigido

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    # Campos básicos
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    
    # CAMPO CORRIGIDO - agora com valores padrão apropriados
    type = Column(String(20), nullable=False, default='expense')  # 'income', 'expense', 'transfer'
    
    category = Column(String(100))
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    
    # Campos para contas
    account_id = Column(Integer, ForeignKey('accounts.id'))
    transfer_to_account_id = Column(Integer, ForeignKey('accounts.id'))
    transfer_from_account_id = Column(Integer, ForeignKey('accounts.id'))
    
    # Campos para controle
    is_transfer = Column(Boolean, default=False)
    is_adjustment = Column(Boolean, default=False)
    adjustment_reason = Column(Text)
    
    # Campos para recorrência
    recurrence_type = Column(String(20))  # 'monthly', 'weekly', 'yearly'
    recurrence_interval = Column(Integer)
    recurrence_count = Column(Integer)
    current_occurrence = Column(Integer)
    parent_transaction_id = Column(Integer, ForeignKey('transactions.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", backref="transactions")
    account = relationship("Account", foreign_keys=[account_id])
    transfer_to_account = relationship("Account", foreign_keys=[transfer_to_account_id])
    transfer_from_account = relationship("Account", foreign_keys=[transfer_from_account_id])
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount}, description='{self.description}')>"
    
    @property
    def formatted_amount(self):
        """Retorna valor formatado como moeda"""
        return f"R$ {self.amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def is_income(self):
        """Verifica se é receita"""
        return self.type == 'income'
    
    @property
    def is_expense(self):
        """Verifica se é despesa"""
        return self.type == 'expense'
    
    def to_dict(self):
        """Converte para dicionário (útil para APIs)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'date': self.date.isoformat() if self.date else None,
            'notes': self.notes,
            'is_transfer': self.is_transfer,
            'is_adjustment': self.is_adjustment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Validação de tipos permitidos
TRANSACTION_TYPES = ['income', 'expense', 'transfer', 'adjustment']

def validate_transaction_type(type_value):
    """Valida se o tipo da transação é válido"""
    return type_value in TRANSACTION_TYPES
