"""
Estatísticas históricas, calculadas a partir dos deals já fechados (ganhos ou perdidos).

São a base do score: "como deals parecidos com este se saíram no passado?".
"""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from app import config
from app.dados.carregador import ETAPA_GANHO, ETAPAS_FECHADAS, carregar_deals

# Mapeia cada dimensão do score para a coluna correspondente nos dados.
COLUNAS_DIMENSAO = {
    "produto": "product",
    "vendedor": "sales_agent",
    "setor": "sector",
    "conta": "account",
}


@dataclass(frozen=True)
class EstatisticasHistoricas:
    """Resumo do histórico usado para pontuar os deals abertos."""

    # Taxa de vitória da empresa toda (0 a 1).
    taxa_vitoria_geral: float

    # Taxa de vitória suavizada por valor, para cada dimensão.
    # Ex.: taxas_por_dimensao["produto"]["GTX Pro"] -> 0.61
    taxas_por_dimensao: dict[str, dict[str, float]]

    # Ciclo de vendas dos deals ganhos (dias entre início e fechamento).
    ciclo_mediano_dias: int  # o "normal" para exibir ao vendedor
    ciclo_normal_dias: int   # até aqui o deal está no prazo
    ciclo_limite_dias: int   # passou disso, quase nenhum deal foi ganho

    # Faixa de preços dos produtos (para normalizar o fator valor).
    preco_minimo: float
    preco_maximo: float


def _taxas_suavizadas(fechados: pd.DataFrame, coluna: str, taxa_geral: float) -> dict[str, float]:
    """
    Calcula a taxa de vitória de cada valor da coluna, puxando grupos
    com poucos deals para perto da média geral (suavização bayesiana simples):

        taxa = (ganhos + m * taxa_geral) / (total + m)
    """
    m = config.SUAVIZACAO_AMOSTRAS
    agrupado = fechados.groupby(coluna)["ganho"].agg(ganhos="sum", total="count")
    taxas = (agrupado["ganhos"] + m * taxa_geral) / (agrupado["total"] + m)
    return taxas.to_dict()


@lru_cache(maxsize=1)
def calcular_estatisticas() -> EstatisticasHistoricas:
    """Calcula (uma vez) as estatísticas históricas a partir dos deals fechados."""
    deals = carregar_deals()

    fechados = deals[deals["deal_stage"].isin(ETAPAS_FECHADAS)].copy()
    fechados["ganho"] = fechados["deal_stage"] == ETAPA_GANHO
    taxa_geral = float(fechados["ganho"].mean())

    # Deals sem conta não entram na taxa por conta (não dizem nada sobre ela).
    taxas = {}
    for dimensao, coluna in COLUNAS_DIMENSAO.items():
        base = fechados[fechados["conta_informada"]] if dimensao == "conta" else fechados
        taxas[dimensao] = _taxas_suavizadas(base, coluna, taxa_geral)

    ganhos = fechados[fechados["ganho"]]
    ciclo = (ganhos["close_date"] - ganhos["engage_date"]).dt.days

    precos = deals["sales_price"].dropna()

    return EstatisticasHistoricas(
        taxa_vitoria_geral=taxa_geral,
        taxas_por_dimensao=taxas,
        ciclo_mediano_dias=int(ciclo.median()),
        ciclo_normal_dias=int(ciclo.quantile(config.PERCENTIL_CICLO_NORMAL)),
        ciclo_limite_dias=int(ciclo.quantile(config.PERCENTIL_CICLO_LIMITE)),
        preco_minimo=float(precos.min()),
        preco_maximo=float(precos.max()),
    )
