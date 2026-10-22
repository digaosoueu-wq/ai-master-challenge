"""
Pontuação (score) dos deals abertos.

O score vai de 0 a 100 e combina três fatores, cada um entre 0 e 1:

1. CHANCE  — taxa de vitória histórica de deals parecidos (mesmo produto,
             vendedor, setor e conta). Convertida em posição relativa entre
             os deals abertos (1 = melhor chance do pipeline).
2. VALOR   — preço do produto, em escala logarítmica (os preços vão de
             US$ 55 a US$ 26.768; sem o log, só o produto mais caro importaria).
3. TEMPO   — 1 se o deal está dentro do prazo normal de vendas; cai até 0
             quando passa do tempo que quase nenhum deal ganho levou.

    pontos de cada fator = peso × 100 × fator   (ex.: chance vale até 35 pontos)
    score = soma dos pontos dos três fatores

Todos os pesos e limites ficam em `app/config.py`.

Para trocar por um modelo de machine learning no futuro, basta manter a
saída de `pontuar_deals_abertos()` (mesmas colunas).
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from app import config
from app.dados.carregador import (
    ETAPA_PROSPECCAO,
    ETAPAS_ABERTAS,
    carregar_deals,
    obter_data_referencia,
)
from app.servicos.estatisticas import COLUNAS_DIMENSAO, EstatisticasHistoricas, calcular_estatisticas

PRIORIDADE_ALTA = "Alta"
PRIORIDADE_MEDIA = "Média"
PRIORIDADE_BAIXA = "Baixa"


# ---------------------------------------------------------------------------
# Cálculo dos fatores
# ---------------------------------------------------------------------------

def _calcular_chance(deals: pd.DataFrame, estat: EstatisticasHistoricas) -> pd.Series:
    """
    Média ponderada das taxas de vitória de cada dimensão.
    Dimensões sem informação (ex.: deal sem conta) são ignoradas e
    o peso é redistribuído entre as demais.
    """
    soma_ponderada = pd.Series(0.0, index=deals.index)
    soma_pesos = pd.Series(0.0, index=deals.index)

    for dimensao, peso in config.PESOS_CHANCE.items():
        taxa = deals[f"taxa_{dimensao}"]
        tem_dado = taxa.notna()
        soma_ponderada += taxa.fillna(0) * peso
        soma_pesos += tem_dado * peso

    # Se nenhuma dimensão tiver dado, usa a taxa geral da empresa.
    return (soma_ponderada / soma_pesos.replace(0, np.nan)).fillna(estat.taxa_vitoria_geral)


def _calcular_fator_valor(valor: pd.Series, estat: EstatisticasHistoricas) -> pd.Series:
    """Normaliza o valor entre 0 e 1 em escala logarítmica."""
    minimo, maximo = np.log(estat.preco_minimo), np.log(estat.preco_maximo)
    return ((np.log(valor) - minimo) / (maximo - minimo)).clip(0, 1)


def _calcular_fator_tempo(dias_aberto: pd.Series, estat: EstatisticasHistoricas) -> pd.Series:
    """
    1.0 até o ciclo normal, caindo linearmente até 0 no ciclo limite.
    Deals sem data de início (prospecção) recebem o valor neutro.
    """
    normal, limite = estat.ciclo_normal_dias, estat.ciclo_limite_dias
    fator = 1 - (dias_aberto - normal) / (limite - normal)
    return fator.clip(0, 1).fillna(config.FATOR_TEMPO_NEUTRO)


def _classificar_prioridade(score: float) -> str:
    if score >= config.LIMITE_PRIORIDADE_ALTA:
        return PRIORIDADE_ALTA
    if score >= config.LIMITE_PRIORIDADE_MEDIA:
        return PRIORIDADE_MEDIA
    return PRIORIDADE_BAIXA


@lru_cache(maxsize=1)
def pontuar_deals_abertos() -> pd.DataFrame:
    """
    Retorna os deals abertos (prospecção e negociação) com score,
    prioridade e todos os fatores usados no cálculo, ordenados do
    mais prioritário para o menos.
    """
    estat = calcular_estatisticas()
    hoje = obter_data_referencia()
    deals = carregar_deals()
    deals = deals[deals["deal_stage"].isin(ETAPAS_ABERTAS)].copy()

    # Taxa histórica de cada dimensão (NaN quando não há informação).
    for dimensao, coluna in COLUNAS_DIMENSAO.items():
        deals[f"taxa_{dimensao}"] = deals[coluna].map(estat.taxas_por_dimensao[dimensao])
    deals.loc[~deals["conta_informada"], "taxa_conta"] = np.nan

    # Deals abertos ainda não têm valor fechado: usamos o preço de tabela.
    deals["valor"] = deals["sales_price"]
    deals["chance"] = _calcular_chance(deals, estat)
    deals["valor_esperado"] = deals["chance"] * deals["valor"]
    deals["dias_aberto"] = (hoje - deals["engage_date"]).dt.days  # NaN em prospecção

    deals["fator_chance"] = deals["chance"].rank(pct=True)
    deals["fator_valor"] = _calcular_fator_valor(deals["valor"], estat)
    deals["fator_tempo"] = _calcular_fator_tempo(deals["dias_aberto"], estat)

    # Pontos de cada fator (ex.: chance vale até 35 pontos). O score é a soma
    # dos pontos já arredondados, para que a conta mostrada ao vendedor feche.
    for fator in FATORES:
        deals[f"pontos_{fator}"] = (pontos_maximos()[fator] * deals[f"fator_{fator}"]).round().astype(int)
    deals["score"] = sum(deals[f"pontos_{fator}"] for fator in FATORES)

    deals["prioridade"] = deals["score"].apply(_classificar_prioridade)
    deals["esfriando"] = deals["dias_aberto"] > estat.ciclo_normal_dias
    deals["motivo_principal"] = deals.apply(motivo_principal, axis=1)

    return deals.sort_values(["score", "valor_esperado"], ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Pontos por fator
# ---------------------------------------------------------------------------

# Ordem em que os fatores aparecem para o vendedor.
FATORES = ["chance", "valor", "tempo"]

NOMES_FATORES = {
    "chance": "Chance de fechar",
    "valor": "Valor do negócio",
    "tempo": "Ritmo da negociação",
}


def pontos_maximos() -> dict[str, int]:
    """Quantos pontos (de 100) cada fator pode dar. Ex.: {"chance": 35, ...}"""
    return {fator: round(peso * 100) for fator, peso in config.PESOS_SCORE.items()}


@dataclass(frozen=True)
class FatorExplicado:
    """Quanto um fator contribuiu para o score e por quê."""

    chave: str
    nome: str
    pontos: int
    maximo: int
    explicacao: str


def explicar_fatores(deal: pd.Series) -> list[FatorExplicado]:
    """Detalha os pontos de cada fator. A soma dos pontos é o score do deal."""
    estat = calcular_estatisticas()

    if deal["deal_stage"] == ETAPA_PROSPECCAO:
        texto_tempo = "Negociação ainda não começou: recebe nota neutra (metade dos pontos)"
    else:
        texto_tempo = (
            f"Aberto há {deal['dias_aberto']:.0f} dias. Até {estat.ciclo_normal_dias} dias ganha "
            f"todos os pontos; perde pontos depois disso e chega a zero com "
            f"{estat.ciclo_limite_dias} dias"
        )

    explicacoes = {
        "chance": (
            f"Negócios parecidos fecharam {deal['chance']:.0%} das vezes. Melhor chance que "
            f"{deal['fator_chance']:.0%} dos negócios abertos"
        ),
        "valor": (
            f"Preço de {_formatar_moeda(deal['valor'])}. Os produtos vão de "
            f"{_formatar_moeda(estat.preco_minimo)} a {_formatar_moeda(estat.preco_maximo)}"
        ),
        "tempo": texto_tempo,
    }

    maximos = pontos_maximos()
    return [
        FatorExplicado(
            chave=fator,
            nome=NOMES_FATORES[fator],
            pontos=int(deal[f"pontos_{fator}"]),
            maximo=maximos[fator],
            explicacao=explicacoes[fator],
        )
        for fator in FATORES
    ]


def motivo_principal(deal: pd.Series) -> str:
    """
    Uma frase curta com o que mais explica a nota, para exibir no cartão:
      - prioridade alta: o fator mais forte (por que vale a pena);
      - demais: o fator que mais tirou pontos (por que a nota é baixa).
    """
    aproveitamento = {fator: deal[f"fator_{fator}"] for fator in FATORES}
    alta = deal["prioridade"] == PRIORIDADE_ALTA
    fator = max(aproveitamento, key=aproveitamento.get) if alta else min(aproveitamento, key=aproveitamento.get)
    valor = _formatar_moeda(deal["valor"])

    if fator == "chance":
        return (f"Boa chance de fechar ({deal['chance']:.0%})" if alta
                else f"Chance de fechar menor que a dos outros ({deal['chance']:.0%})")
    if fator == "valor":
        return f"Alto valor ({valor})" if alta else f"Valor baixo ({valor})"
    if deal["deal_stage"] == ETAPA_PROSPECCAO:
        return "Negociação ainda não começou"
    return (f"Negociação no prazo ({deal['dias_aberto']:.0f} dias)" if alta
            else f"Parado há {deal['dias_aberto']:.0f} dias")


def regras_pontuacao() -> dict:
    """Regras atuais do score, para a tela "Como funciona a pontuação"."""
    estat = calcular_estatisticas()
    return {
        "pontos_maximos": pontos_maximos(),
        "limite_alta": config.LIMITE_PRIORIDADE_ALTA,
        "limite_media": config.LIMITE_PRIORIDADE_MEDIA,
        "taxa_vitoria_geral": round(estat.taxa_vitoria_geral, 4),
        "ciclo_mediano_dias": estat.ciclo_mediano_dias,
        "ciclo_normal_dias": estat.ciclo_normal_dias,
        "ciclo_limite_dias": estat.ciclo_limite_dias,
        "preco_minimo": estat.preco_minimo,
        "preco_maximo": estat.preco_maximo,
    }


# ---------------------------------------------------------------------------
# Explicação do score em linguagem simples
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Motivo:
    """Uma frase explicando algo que pesou no score."""

    texto: str
    tipo: str  # "positivo", "negativo" ou "neutro"


def _formatar_moeda(valor: float) -> str:
    """Formata em dólar no padrão brasileiro: US$ 5.482."""
    return "US$ " + f"{valor:,.0f}".replace(",", ".")


def _motivo_taxa(rotulo: str, taxa: float, taxa_geral: float) -> Motivo | None:
    """Gera um motivo se a taxa de vitória for bem diferente da média da empresa."""
    if pd.isna(taxa):
        return None
    diferenca_pp = (taxa - taxa_geral) * 100
    if abs(diferenca_pp) < config.DIFERENCA_RELEVANTE_PP:
        return None
    comparacao = "acima" if diferenca_pp > 0 else "abaixo"
    return Motivo(
        texto=f"Histórico {rotulo}: {taxa:.0%} de vitórias ({comparacao} da média de {taxa_geral:.0%})",
        tipo="positivo" if diferenca_pp > 0 else "negativo",
    )


def explicar_deal(deal: pd.Series) -> list[Motivo]:
    """Lista os motivos que explicam o score de um deal, do mais ao menos importante."""
    estat = calcular_estatisticas()
    geral = estat.taxa_vitoria_geral
    motivos: list[Motivo] = []

    # Tempo: é o sinal mais forte nos dados, por isso vem primeiro.
    if deal["deal_stage"] == ETAPA_PROSPECCAO:
        motivos.append(Motivo("Ainda em prospecção: a negociação não começou", "neutro"))
    elif deal["dias_aberto"] >= estat.ciclo_limite_dias:
        motivos.append(Motivo(
            f"Parado há {deal['dias_aberto']:.0f} dias: quase nenhum negócio ganho "
            f"demorou mais de {estat.ciclo_limite_dias} dias",
            "negativo",
        ))
    elif deal["esfriando"]:
        motivos.append(Motivo(
            f"Esfriando: aberto há {deal['dias_aberto']:.0f} dias "
            f"(negócios ganhos costumam fechar em {estat.ciclo_mediano_dias})",
            "negativo",
        ))
    else:
        motivos.append(Motivo(
            f"Negociação dentro do prazo normal ({deal['dias_aberto']:.0f} dias)",
            "positivo",
        ))

    # Valor.
    valor = _formatar_moeda(deal["valor"])
    if deal["fator_valor"] >= 0.65:
        motivos.append(Motivo(f"Alto valor: {valor}", "positivo"))
    elif deal["fator_valor"] <= 0.2:
        motivos.append(Motivo(f"Valor baixo: {valor}", "negativo"))

    # Taxas de vitória por dimensão.
    rotulos = {
        "vendedor": f"de {deal['sales_agent']}",
        "produto": f"do produto {deal['product']}",
        "setor": f"do setor {deal['sector']}",
        "conta": f"da conta {deal['account']}",
    }
    for dimensao, rotulo in rotulos.items():
        motivo = _motivo_taxa(rotulo, deal[f"taxa_{dimensao}"], geral)
        if motivo:
            motivos.append(motivo)

    if not deal["conta_informada"]:
        motivos.append(Motivo(
            "Conta não informada: cadastre a conta para uma análise mais precisa",
            "neutro",
        ))

    return motivos


def sugerir_acao(deal: pd.Series) -> str:
    """Recomendação direta para o vendedor, baseada no score e no tempo parado."""
    estat = calcular_estatisticas()

    if deal["dias_aberto"] >= estat.ciclo_limite_dias:
        return "Reavalie: este negócio está parado há muito tempo. Faça um último contato ou encerre."
    if deal["prioridade"] == PRIORIDADE_ALTA:
        return "Priorize: boa chance de fechar e bom valor. Dedique tempo a este negócio agora."
    if deal["esfriando"]:
        return "Retome o contato logo: o negócio está esfriando."
    if deal["prioridade"] == PRIORIDADE_MEDIA:
        return "Mantenha o acompanhamento regular."
    return "Baixa prioridade: dedique tempo depois dos negócios prioritários."
