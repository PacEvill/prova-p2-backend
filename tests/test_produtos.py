import pytest
from main import Produto

# 1. Listar produtos quando o banco está vazio
def test_listar_produtos_vazio(client):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []

# 2. Criar produto e verificar persistência no banco
def test_criar_produto_sucesso(client, db_session):
    payload = {
        "nome": "Mouse Gamer",
        "preco": 150.00,
        "estoque": 10,
        "ativo": True
    }
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["nome"] == payload["nome"]
    assert data["preco"] == payload["preco"]
    assert data["estoque"] == payload["estoque"]
    assert data["ativo"] == payload["ativo"]

    # Verifica persistência direta no banco de dados usando a db_session
    produto_db = db_session.query(Produto).filter(Produto.id == data["id"]).first()
    assert produto_db is not None
    assert produto_db.nome == payload["nome"]
    assert produto_db.preco == payload["preco"]

# 3. Criar produto e verificar que aparece na listagem
def test_criar_produto_e_listar(client):
    payload = {
        "nome": "Teclado Mecânico",
        "preco": 350.00,
        "estoque": 5,
        "ativo": True
    }
    # Cria
    response_create = client.post("/produtos", json=payload)
    assert response_create.status_code == 201
    created_id = response_create.json()["id"]

    # Lista
    response_list = client.get("/produtos")
    assert response_list.status_code == 200
    produtos = response_list.json()
    
    assert len(produtos) == 1
    assert produtos[0]["id"] == created_id
    assert produtos[0]["nome"] == payload["nome"]

# 4. Buscar produto por id — caso de sucesso
def test_buscar_produto_por_id_sucesso(client, produto_existente):
    response = client.get(f"/produtos/{produto_existente.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == produto_existente.id
    assert data["nome"] == produto_existente.nome
    assert data["preco"] == produto_existente.preco

# 5. Buscar produto com id inexistente — deve retornar 404
def test_buscar_produto_inexistente(client):
    response = client.get("/produtos/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"

# 6. Deletar produto — deve retornar 204
def test_deletar_produto_sucesso(client, produto_existente):
    response = client.delete(f"/produtos/{produto_existente.id}")
    assert response.status_code == 204
    assert response.content == b""  # 204 No Content não possui corpo

# 7. Deletar produto e confirmar remoção com GET subsequente
def test_deletar_produto_confirmar_remocao(client, produto_existente):
    # Deleta
    response_delete = client.delete(f"/produtos/{produto_existente.id}")
    assert response_delete.status_code == 204

    # GET subsequente deve retornar 404
    response_get = client.get(f"/produtos/{produto_existente.id}")
    assert response_get.status_code == 404

# 8. Deletar produto inexistente — deve retornar 404
def test_deletar_produto_inexistente(client):
    response = client.delete("/produtos/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"

# 9. Pelo menos 1 teste parametrizado com @pytest.mark.parametrize cobrindo payloads inválidos (status 422)
@pytest.mark.parametrize(
    "payload, campo_erro",
    [
        # Nome vazio
        ({"nome": "", "preco": 10.0, "estoque": 5}, "nome"),
        # Nome contendo apenas espaços
        ({"nome": "   ", "preco": 10.0, "estoque": 5}, "nome"),
        # Nome nulo/ausente
        ({"preco": 10.0, "estoque": 5}, "nome"),
        # Preço igual a zero
        ({"nome": "Produto Invalido", "preco": 0.0, "estoque": 5}, "preco"),
        # Preço negativo
        ({"nome": "Produto Invalido", "preco": -15.5, "estoque": 5}, "preco"),
        # Preço ausente
        ({"nome": "Produto Invalido", "estoque": 5}, "preco"),
        # Preço com tipo inválido
        ({"nome": "Produto Invalido", "preco": "gratis", "estoque": 5}, "preco"),
        # Estoque negativo
        ({"nome": "Produto Invalido", "preco": 100.0, "estoque": -1}, "estoque"),
        # Estoque com tipo inválido
        ({"nome": "Produto Invalido", "preco": 100.0, "estoque": "muitos"}, "estoque"),
    ]
)
def test_criar_produto_payload_invalido(client, payload, campo_erro):
    response = client.post("/produtos", json=payload)
    assert response.status_code == 422
    # Pydantic retorna detalhes dos erros de validação no corpo da resposta
    detalhes = response.json().get("detail", [])
    assert len(detalhes) > 0
    # Opcional: valida que o erro reportado aponta para o campo problemático esperado
    locs = [d.get("loc", []) for d in detalhes]
    assert any(campo_erro in loc for loc in locs)

# 10. Pelo menos 1 teste que valide que o banco está isolado entre execuções
def test_validar_isolamento_banco(client):
    """
    Este teste valida que o banco de dados é limpo e isolado entre execuções.
    Mesmo que testes anteriores tenham inserido produtos (como em test_criar_produto_sucesso
    ou através da fixture produto_existente), este teste inicia com o banco totalmente
    vazio (0 registros), comprovando o isolamento proporcionado pelas fixtures de conftest.py.
    """
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []
