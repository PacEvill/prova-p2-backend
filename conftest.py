import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from main import app, Base, engine, get_db, Produto

# Criamos um sessionmaker específico para os testes, associado à mesma engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    """Fixture que cria/destrói o schema e injeta a sessão de banco de dados no TestClient."""
    # (a) Cria todas as tabelas
    Base.metadata.create_all(bind=engine)

    # Cria uma sessão exclusiva para as chamadas feitas pelo TestClient da API
    session = TestingSessionLocal()

    # (b) Sobrescreve a dependência get_db da API
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # (c) Faz o yield do TestClient
    with TestClient(app) as test_client:
        yield test_client

    # Teardown:
    # Limpa os overrides
    app.dependency_overrides.clear()
    
    # Fecha a sessão utilizada pelo client para liberar conexões e locks no banco
    session.close()

    # (d) Destrói todas as tabelas no teardown
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(client):
    """Fixture que fornece uma sessão de banco de dados para asserções diretas no teste."""
    # Depende de `client` para garantir que as tabelas já foram criadas e
    # que esta sessão seja fechada antes de o `client` dropar as tabelas no teardown.
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def produto_existente(client, db_session):
    """Fixture auxiliar que cria um produto padrão no banco de dados para os testes."""
    produto = Produto(
        nome="Produto Teste Fixture",
        preco=29.90,
        estoque=15,
        ativo=True
    )
    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)
    return produto
