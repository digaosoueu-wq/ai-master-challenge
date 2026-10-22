"""
Configurações centrais da aplicação.

Tudo que um dev ou gestor possa querer ajustar (caminhos, pesos do score,
faixas de prioridade) fica aqui, para não precisar mexer na lógica.
"""

from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

# Pasta raiz do projeto (testeAiMaster/), dois níveis acima deste arquivo.
PASTA_RAIZ = Path(__file__).resolve().parents[2]

# Pasta com os CSVs de origem.
PASTA_DADOS = PASTA_RAIZ / "dados"

# ---------------------------------------------------------------------------
# Data de referência ("hoje")
# ---------------------------------------------------------------------------

# Os dados históricos terminam em 2017. Se for None, usamos a maior data
# encontrada nos CSVs como "hoje". Quando os dados forem reais/atuais,
# basta trocar por date.today().
DATA_REFERENCIA: date | None = None

# ---------------------------------------------------------------------------
# Score de prioridade
# ---------------------------------------------------------------------------

# Peso de cada fator no score final (a soma deve ser 1.0).
PESOS_SCORE = {
    "chance": 0.35,  # chance histórica de fechar
    "valor": 0.35,   # quanto o deal vale
    "tempo": 0.30,   # se o deal está "fresco" ou parado há muito tempo
}

# Peso de cada dimensão no cálculo da chance de fechar.
# Se a conta não estiver informada, os pesos restantes são redistribuídos.
PESOS_CHANCE = {
    "produto": 0.30,
    "vendedor": 0.30,
    "setor": 0.20,
    "conta": 0.20,
}

# Suavização das taxas de vitória: quantos deals "imaginários" com a taxa
# média da empresa somamos a cada grupo. Evita que um vendedor com 2 deals
# ganhos de 2 apareça com 100% de chance.
SUAVIZACAO_AMOSTRAS = 20

# Valor do fator tempo para deals em prospecção (ainda sem data de início).
FATOR_TEMPO_NEUTRO = 0.5

# Percentis do ciclo de vendas (dias entre início e fechamento dos deals
# GANHOS) usados para avaliar se um deal está parado:
#   - até o percentil "normal": tempo dentro do esperado (fator = 1)
#   - a partir do percentil "limite": quase nenhum deal ganho demorou tanto (fator = 0)
PERCENTIL_CICLO_NORMAL = 0.75
PERCENTIL_CICLO_LIMITE = 0.98

# Faixas de prioridade pelo score (0 a 100).
LIMITE_PRIORIDADE_ALTA = 60
LIMITE_PRIORIDADE_MEDIA = 40

# Diferença mínima (em pontos percentuais) entre uma taxa de vitória e a média
# da empresa para que ela vire um "motivo" exibido ao vendedor.
DIFERENCA_RELEVANTE_PP = 2.0

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

# Origens autorizadas a chamar a API (front-end em desenvolvimento).
ORIGENS_PERMITIDAS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
