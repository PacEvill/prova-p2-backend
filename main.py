import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, Field, field_validator

# 1. Configuração do Banco de Dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres_dev")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelo SQLAlchemy
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)

# Criação das tabelas no banco se elas não existirem (relevante para desenvolvimento local)
# Nos testes, o conftest.py criará e destruirá as tabelas por teste.
Base.metadata.create_all(bind=engine)

# 3. Schemas Pydantic (Validação)
class ProdutoBase(BaseModel):
    nome: str
    preco: float
    estoque: int = 0
    ativo: bool = True

class ProdutoCreate(ProdutoBase):
    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("O nome do produto não pode ser vazio")
        return v.strip()

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("O preço deve ser maior que zero")
        return v

    @field_validator("estoque")
    @classmethod
    def validar_estoque(cls, v: int) -> int:
        if v < 0:
            raise ValueError("A quantidade em estoque não pode ser negativa")
        return v

class ProdutoResponse(ProdutoBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# 4. Inicialização do App FastAPI
app = FastAPI(
    title="API de Gerenciamento de Produtos",
    description="API REST de catálogo de produtos para pequeno e-commerce",
    version="1.0.0"
)

# Dependência do Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. Endpoints
@app.get("/produtos", response_model=List[ProdutoResponse], status_code=status.HTTP_200_OK)
def listar_produtos(db: Session = Depends(get_db)):
    produtos = db.query(Produto).all()
    return produtos

@app.post("/produtos", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(produto_in: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = Produto(
        nome=produto_in.nome,
        preco=produto_in.preco,
        estoque=produto_in.estoque,
        ativo=produto_in.ativo
    )
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.get("/produtos/{id}", response_model=ProdutoResponse, status_code=status.HTTP_200_OK)
def obter_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    return produto

@app.delete("/produtos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    db.delete(produto)
    db.commit()
    return None
