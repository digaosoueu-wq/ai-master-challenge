/**
 * Tipos dos dados retornados pela API.
 * Espelham os modelos de backend/app/esquemas.py — se mudar lá, mude aqui.
 */

export type Prioridade = "Alta" | "Média" | "Baixa";
export type Etapa = "Prospecting" | "Engaging";

export interface DealResumo {
  id: string;
  etapa: Etapa;
  vendedor: string;
  manager: string;
  escritorio: string;
  conta: string;
  conta_informada: boolean;
  setor: string | null;
  produto: string;
  valor: number;
  chance: number;
  valor_esperado: number;
  dias_aberto: number | null;
  score: number;
  prioridade: Prioridade;
  esfriando: boolean;
  /** Frase curta com o que mais explica a nota (ex.: "Parado há 129 dias"). */
  motivo_principal: string;
}

export interface Motivo {
  texto: string;
  tipo: "positivo" | "negativo" | "neutro";
}

/** Pontos que um fator deu ao deal. A soma dos pontos dos fatores é o score. */
export interface FatorScore {
  chave: "chance" | "valor" | "tempo";
  nome: string;
  pontos: number;
  maximo: number;
  explicacao: string;
}

export interface DealDetalhe extends DealResumo {
  fatores: FatorScore[];
  motivos: Motivo[];
  sugestao: string;
}

export interface ListaDeals {
  total: number;
  deals: DealResumo[];
}

export interface Resumo {
  total_abertos: number;
  valor_esperado_total: number;
  qtd_prioridade_alta: number;
  qtd_esfriando: number;
  taxa_vitoria: number;
}

/** Regras atuais da pontuação (definidas em backend/app/config.py). */
export interface RegrasPontuacao {
  pontos_maximos: { chance: number; valor: number; tempo: number };
  limite_alta: number;
  limite_media: number;
  taxa_vitoria_geral: number;
  ciclo_mediano_dias: number;
  ciclo_normal_dias: number;
  ciclo_limite_dias: number;
  preco_minimo: number;
  preco_maximo: number;
}

export interface OpcoesFiltro {
  vendedores: string[];
  managers: string[];
  escritorios: string[];
  produtos: string[];
  prioridades: Prioridade[];
}

/** Filtros escolhidos na tela. Campo vazio ("") significa "todos". */
export interface Filtros {
  vendedor: string;
  manager: string;
  escritorio: string;
  produto: string;
  prioridade: string;
  busca: string;
}

export const FILTROS_VAZIOS: Filtros = {
  vendedor: "",
  manager: "",
  escritorio: "",
  produto: "",
  prioridade: "",
  busca: "",
};
