"""
Formato das respostas da API (validado e documentado automaticamente em /docs).
"""

from pydantic import BaseModel, Field


class DealResumo(BaseModel):
    """Dados de um deal exibidos no quadro/lista do pipeline."""

    id: str
    etapa: str = Field(description="Prospecting ou Engaging")
    vendedor: str
    manager: str
    escritorio: str
    conta: str
    conta_informada: bool
    setor: str | None
    produto: str
    valor: float = Field(description="Preço de tabela do produto (US$)")
    chance: float = Field(description="Chance histórica de fechar (0 a 1)")
    valor_esperado: float = Field(description="chance × valor (US$)")
    dias_aberto: int | None = Field(description="Dias desde o início da negociação")
    score: int = Field(description="Prioridade de 0 a 100")
    prioridade: str = Field(description="Alta, Média ou Baixa")
    esfriando: bool = Field(description="Aberto há mais tempo que o normal")
    motivo_principal: str = Field(description="Frase curta com o que mais explica o score")


class FatorScore(BaseModel):
    """Pontos que um fator deu ao deal. A soma dos pontos de todos os fatores é o score."""

    chave: str = Field(description="chance, valor ou tempo")
    nome: str
    pontos: int
    maximo: int = Field(description="Máximo de pontos que o fator pode dar")
    explicacao: str


class Motivo(BaseModel):
    texto: str
    tipo: str = Field(description="positivo, negativo ou neutro")


class DealDetalhe(DealResumo):
    """Deal com a explicação completa do score."""

    fatores: list[FatorScore]
    motivos: list[Motivo]
    sugestao: str


class ListaDeals(BaseModel):
    total: int
    deals: list[DealResumo]


class Resumo(BaseModel):
    """Números do topo da tela (respeitando os filtros)."""

    total_abertos: int
    valor_esperado_total: float
    qtd_prioridade_alta: int
    qtd_esfriando: int
    taxa_vitoria: float = Field(description="Taxa de vitória histórica do recorte filtrado")


class RegrasPontuacao(BaseModel):
    """Regras atuais do score, para explicar a lógica ao vendedor."""

    pontos_maximos: dict[str, int] = Field(description="Pontos máximos por fator (somam 100)")
    limite_alta: int
    limite_media: int
    taxa_vitoria_geral: float
    ciclo_mediano_dias: int
    ciclo_normal_dias: int
    ciclo_limite_dias: int
    preco_minimo: float
    preco_maximo: float


class OpcoesFiltro(BaseModel):
    """Valores disponíveis para os filtros da tela."""

    vendedores: list[str]
    managers: list[str]
    escritorios: list[str]
    produtos: list[str]
    prioridades: list[str]
