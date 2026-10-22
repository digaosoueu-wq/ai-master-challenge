"""Testes do score e das explicações."""

from app.servicos.estatisticas import calcular_estatisticas
from app.servicos.pontuacao import (
    explicar_deal,
    explicar_fatores,
    pontos_maximos,
    pontuar_deals_abertos,
    sugerir_acao,
)


def test_pontua_apenas_deals_abertos():
    deals = pontuar_deals_abertos()
    assert len(deals) == 2089
    assert set(deals["deal_stage"]) == {"Prospecting", "Engaging"}


def test_score_entre_0_e_100_e_ordenado():
    scores = pontuar_deals_abertos()["score"]
    assert scores.between(0, 100).all()
    assert scores.is_monotonic_decreasing


def test_fatores_entre_0_e_1():
    deals = pontuar_deals_abertos()
    for coluna in ["fator_chance", "fator_valor", "fator_tempo", "chance"]:
        assert deals[coluna].between(0, 1).all(), coluna


def test_deal_muito_parado_tem_fator_tempo_zero():
    estat = calcular_estatisticas()
    deals = pontuar_deals_abertos()
    muito_parados = deals[deals["dias_aberto"] >= estat.ciclo_limite_dias]
    assert not muito_parados.empty
    assert (muito_parados["fator_tempo"] == 0).all()


def test_todo_deal_tem_motivos_e_sugestao():
    for _, deal in pontuar_deals_abertos().head(50).iterrows():
        assert explicar_deal(deal), deal["opportunity_id"]
        assert sugerir_acao(deal)


def test_deal_muito_parado_recebe_sugestao_de_reavaliar():
    estat = calcular_estatisticas()
    deals = pontuar_deals_abertos()
    deal = deals[deals["dias_aberto"] >= estat.ciclo_limite_dias].iloc[0]
    assert sugerir_acao(deal).startswith("Reavalie")


def test_score_e_a_soma_dos_pontos_dos_fatores():
    for _, deal in pontuar_deals_abertos().head(100).iterrows():
        fatores = explicar_fatores(deal)
        assert sum(f.pontos for f in fatores) == deal["score"]
        assert all(0 <= f.pontos <= f.maximo for f in fatores)


def test_pontos_maximos_somam_100():
    assert sum(pontos_maximos().values()) == 100


def test_motivo_principal_explica_nota_baixa_e_alta():
    deals = pontuar_deals_abertos()
    assert deals["motivo_principal"].str.len().gt(0).all()
    # O pior deal deve ter um motivo negativo, nunca um elogio.
    assert not deals.iloc[-1]["motivo_principal"].startswith(("Boa", "Alto", "Negociação no prazo"))
