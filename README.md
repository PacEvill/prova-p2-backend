# API de Catálogo de E-commerce & Testes de Integração

Esta é uma API REST desenvolvida com **FastAPI**, **SQLAlchemy** e **PostgreSQL** para o gerenciamento de produtos de um e-commerce. A suíte de testes automatizados é executada contra um banco de dados PostgreSQL real rodando via Docker, garantindo o comportamento fidedigno das constraints e tipos de dados do banco de produção.

---

## 1. Como Executar a Infraestrutura (Docker)

Antes de executar a API localmente ou rodar a suíte de testes, inicie os bancos de dados PostgreSQL (de desenvolvimento e de testes) configurados no Docker:

```bash
# Sobe os containers de desenvolvimento e teste em segundo plano (detached mode)
docker compose up -d
```

* **Banco de Desenvolvimento**: Disponível na porta local `5432` com volume persistente.
* **Banco de Testes**: Disponível na porta local `5433` sem volume persistente (dados descartáveis).

---

## 2. Instalação e Execução dos Testes

### 2.1 Preparar Ambiente Local

Crie o ambiente virtual e instale todas as dependências do projeto:

```bash
# 1. Cria o ambiente virtual
python3 -m venv .venv

# 2. Ativa o ambiente virtual
source .venv/bin/activate

# 3. Atualiza o pip e instala as dependências
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Executar os Testes Automatizados

Com o container `ecom_db_test` em execução, use o seguinte comando para rodar os testes com o relatório de cobertura de código:

```bash
pytest --cov=main -v
```

---

## 3. Saída Esperada dos Testes (Pytest Output)

```text
============================= test session starts ==============================
platform linux -- Python 3.14.5, pytest-9.1.0, pluggy-1.6.0 -- .venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/diego_silva/Documentos/cofre/20 - Áreas/FACULDADE/5° Periodo/03. Laboratório de Programação Back-end/p2
configfile: pytest.ini
plugins: cov-7.1.0, env-1.6.0, anyio-4.13.0
collecting ... collected 18 items                                                             

tests/test_produtos.py::test_listar_produtos_vazio PASSED                [  5%]
tests/test_produtos.py::test_criar_produto_sucesso PASSED                [ 11%]
tests/test_produtos.py::test_criar_produto_e_listar PASSED               [ 16%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 22%]
tests/test_produtos.py::test_buscar_produto_inexistente PASSED           [ 27%]
tests/test_produtos.py::test_deletar_produto_sucesso PASSED              [ 33%]
tests/test_produtos.py::test_deletar_produto_confirmar_remocao PASSED    [ 38%]
tests/test_produtos.py::test_deletar_produto_inexistente PASSED          [ 44%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload0-nome] PASSED [ 50%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload1-nome] PASSED [ 55%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload2-nome] PASSED [ 61%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload3-preco] PASSED [ 66%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload4-preco] PASSED [ 72%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload5-preco] PASSED [ 77%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload6-preco] PASSED [ 83%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload7-estoque] PASSED [ 88%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload8-estoque] PASSED [ 94%]
tests/test_produtos.py::test_validar_isolamento_banco PASSED             [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.5-final-0 ________________

Name      Stmts   Miss  Cover
-----------------------------
main.py      73      4    95%
-----------------------------
TOTAL        73      4    95%
======================== 18 passed, 1 warning in 0.58s =========================
```

---

## 4. Como o Isolamento Entre Testes Funciona

O isolamento é alcançado no arquivo `conftest.py` por meio do ciclo de vida das fixtures do `pytest` com escopo de função (`scope="function"`):

1. **Setup de cada teste (`client`)**: Antes de cada função de teste individual ser executada, a fixture `client` cria todas as tabelas no banco de dados de testes utilizando `Base.metadata.create_all(bind=engine)`.
2. **Substituição de Dependência**: A fixture então inicia uma sessão de banco com a base recém-criada e substitui a dependência `get_db` do FastAPI usando `app.dependency_overrides[get_db]`. Isso garante que as chamadas da API usem a mesma conexão transacional limpa dos testes.
3. **Execução do Teste**: A função do teste é executada de forma completamente isolada. A fixture `db_session` (que depende do `client`) fornece acesso direto ao banco de dados para asserções e inserções auxiliares.
4. **Teardown de cada teste**: Após a finalização da execução do teste, o `pytest` limpa as substituições (`app.dependency_overrides.clear()`), encerra as sessões ativas (`session.close()`) para liberar locks de transação e remove inteiramente todas as tabelas com `Base.metadata.drop_all(bind=engine)`.

Dessa forma, cada teste inicia com um esquema de banco de dados do PostgreSQL 100% novo, limpo e sem qualquer herança de estado deixado por execuções anteriores, garantindo a atomicidade e confiabilidade da suíte.
