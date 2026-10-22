"""
Ponto de entrada da API.

Rodar em desenvolvimento (dentro da pasta backend/):
    uvicorn app.main:app --reload

Documentação interativa: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.rotas import pipeline, resumo
from app.servicos.pontuacao import pontuar_deals_abertos


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    # Carrega e pontua os dados na subida do servidor,
    # para a primeira requisição não ficar lenta.
    pontuar_deals_abertos()
    yield


app = FastAPI(
    title="Priorização de Deals",
    description="Ajuda vendedores a decidir em quais negócios focar.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGENS_PERMITIDAS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(pipeline.roteador)
app.include_router(resumo.roteador)
