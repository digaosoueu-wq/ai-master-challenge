"""
Consultas usadas pelas rotas: filtrar deals, montar o resumo e converter
linhas do DataFrame no formato da API.

As rotas não acessam pandas diretamente; passam por aqui.
"""

from dataclasses import asdict, dataclass

import pandas as pd

from app.dados.carregador import ETAPA_GANHO, ETAPAS_FECHADAS, carregar_deals
from app.servicos.pontuacao import (
    PRIORIDADE_ALTA,
    PRIORIDADE_BAIXA,
    PRIORIDADE_MEDIA,
    explicar_deal,
    explicar_fatores,
    pontuar_deals_abertos,
    sugerir_acao,
)


@dataclass
class Filtros:
    """Filtros escolhidos na tela. None significa "todos"."""

    vendedor: str | None = None
    manager: str | None = None
    escritorio: str | None = None
    produto: str | None = None
    prioridade: str | None = None
    busca: str | None = None  # texto livre: conta ou id do deal


# Filtro da tela -> coluna nos dados.
COLUNAS_FILTRO = {
    "vendedor": "sales_agent",
    "manager": "manager",
    "escritorio": "regional_office",
    "produto": "product",
    "prioridade": "prioridade",
}


def _aplicar_filtros(deals: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    """Aplica os filtros que existirem como colunas no DataFrame recebido."""
    for campo, coluna in COLUNAS_FILTRO.items():
        valor = getattr(filtros, campo)
        if valor and coluna in deals.columns:
            deals = deals[deals[coluna] == valor]

    if filtros.busca:
        texto = filtros.busca.strip().lower()
        deals = deals[
            deals["account"].str.lower().str.contains(texto, regex=False)
            | deals["opportunity_id"].str.lower().str.contains(texto, regex=False)
        ]
    return deals


def _sem_nan(valor):
    """Converte NaN do pandas em None (JSON não aceita NaN)."""
    return None if pd.isna(valor) else valor


def _para_resumo(deal: pd.Series) -> dict:
    """Converte uma linha do DataFrame no formato DealResumo."""
    dias = _sem_nan(deal["dias_aberto"])
    return {
        "id": deal["opportunity_id"],
        "etapa": deal["deal_stage"],
        "vendedor": deal["sales_agent"],
        "manager": deal["manager"],
        "escritorio": deal["regional_office"],
        "conta": deal["account"],
        "conta_informada": bool(deal["conta_informada"]),
        "setor": _sem_nan(deal["sector"]),
        "produto": deal["product"],
        "valor": float(deal["valor"]),
        "chance": round(float(deal["chance"]), 4),
        "valor_esperado": round(float(deal["valor_esperado"]), 2),
        "dias_aberto": int(dias) if dias is not None else None,
        "score": int(deal["score"]),
        "prioridade": deal["prioridade"],
        "esfriando": bool(deal["esfriando"]),
        "motivo_principal": deal["motivo_principal"],
    }


def listar_deals(filtros: Filtros) -> list[dict]:
    """Deals abertos filtrados, já ordenados por prioridade."""
    deals = _aplicar_filtros(pontuar_deals_abertos(), filtros)
    return [_para_resumo(deal) for _, deal in deals.iterrows()]


def detalhar_deal(id_deal: str) -> dict | None:
    """Deal com fatores, motivos e sugestão. None se não existir ou já estiver fechado."""
    deals = pontuar_deals_abertos()
    encontrados = deals[deals["opportunity_id"] == id_deal]
    if encontrados.empty:
        return None

    deal = encontrados.iloc[0]
    return {
        **_para_resumo(deal),
        "fatores": [asdict(f) for f in explicar_fatores(deal)],
        "motivos": [{"texto": m.texto, "tipo": m.tipo} for m in explicar_deal(deal)],
        "sugestao": sugerir_acao(deal),
    }


def montar_resumo(filtros: Filtros) -> dict:
    """KPIs do topo da tela para o recorte filtrado."""
    abertos = _aplicar_filtros(pontuar_deals_abertos(), filtros)

    # Taxa de vitória: histórico de deals fechados do mesmo recorte
    # (prioridade e busca não se aplicam a deals fechados).
    filtros_historico = Filtros(
        vendedor=filtros.vendedor,
        manager=filtros.manager,
        escritorio=filtros.escritorio,
        produto=filtros.produto,
    )
    todos = carregar_deals()
    fechados = _aplicar_filtros(todos[todos["deal_stage"].isin(ETAPAS_FECHADAS)], filtros_historico)
    taxa = float((fechados["deal_stage"] == ETAPA_GANHO).mean()) if len(fechados) else 0.0

    return {
        "total_abertos": len(abertos),
        "valor_esperado_total": round(float(abertos["valor_esperado"].sum()), 2),
        "qtd_prioridade_alta": int((abertos["prioridade"] == PRIORIDADE_ALTA).sum()),
        "qtd_esfriando": int(abertos["esfriando"].sum()),
        "taxa_vitoria": round(taxa, 4),
    }


def opcoes_filtro() -> dict:
    """Listas ordenadas para preencher os campos de filtro."""
    deals = carregar_deals()

    def unicos(coluna: str) -> list[str]:
        return sorted(deals[coluna].dropna().unique().tolist())

    return {
        "vendedores": unicos("sales_agent"),
        "managers": unicos("manager"),
        "escritorios": unicos("regional_office"),
        "produtos": unicos("product"),
        "prioridades": [PRIORIDADE_ALTA, PRIORIDADE_MEDIA, PRIORIDADE_BAIXA],
    }
