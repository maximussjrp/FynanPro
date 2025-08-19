from app import create_master_user, Base, engine

if __name__ == '__main__':
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar usuário master
    create_master_user()
