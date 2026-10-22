# Priorização de Deals

Ferramenta web que ajuda vendedores a decidir **em quais negócios focar**.
Ela lê o histórico de vendas, dá uma pontuação de 0 a 100 para cada negócio
aberto e explica, em linguagem simples, o porquê da nota e o que fazer.

```
backend/   API em Python (FastAPI + pandas): carrega os dados e calcula o score
frontend/  Tela em React + TypeScript (Vite): só exibe o que a API entrega
dados/     CSVs de origem (accounts, products, sales_pipeline, sales_teams)
```

## Como rodar

Pré-requisitos: Python 3.10+ e Node 18+.

**1. Backend** (terminal 1)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API em http://localhost:8000 — documentação interativa em http://localhost:8000/docs.

**2. Frontend** (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Abra http://localhost:5173. O Vite repassa as chamadas `/api` para o backend
(ver `frontend/vite.config.ts`). Se a porta 5173 estiver ocupada, o Vite usa a próxima livre.

**Testes do backend:** `cd backend && pytest`

## Como funciona o score

Só os negócios **abertos** (Prospecção e Em negociação) recebem nota.
O histórico de negócios **fechados** (ganhos e perdidos) é a base de comparação.

| Fator | O que mede | Pontos (máx.) |
|---|---|---|
| Chance | Taxa de vitória histórica do mesmo produto, vendedor, setor e conta (média ponderada, suavizada para grupos com poucos negócios). Convertida em posição relativa entre os negócios abertos. | 35 |
| Valor | Preço de tabela do produto, em escala logarítmica (de US$ 55 a US$ 26.768). | 35 |
| Tempo | Todos os pontos enquanto o negócio está no prazo normal (até 88 dias); cai até zero quando passa do tempo que quase nenhum negócio ganho levou (125 dias). Prospecção recebe metade dos pontos. | 30 |

- **Nota = soma dos pontos dos três fatores** (ex.: 35 + 26 + 30 = 91). A mesma conta aparece no detalhe de cada negócio.
- **Principal motivo:** frase no cartão com o ponto forte (prioridade alta) ou o fator que mais tirou pontos (demais).
- **Na tela:** o botão "Como funciona a pontuação" explica as regras com os valores atuais de `config.py` (via `GET /api/regras`).
- **Prioridade:** Alta (≥ 60), Média (≥ 40), Baixa (< 40).
- **Esfriando:** aberto há mais dias que 75% dos negócios ganhos levaram para fechar.
- **Valor esperado:** chance × valor.

Todos os pesos e limites ficam em [`backend/app/config.py`](backend/app/config.py).

### O que os dados mostram

- Negócios ganhos fecham em **57 dias** (mediana) e quase nenhum passa de **125 dias**.
- Mais da metade dos negócios em negociação já está aberta há mais de **165 dias**:
  são esses que tomam o tempo do vendedor com pouca chance de retorno.
- As taxas de vitória por produto e vendedor variam pouco (55% a 70%), então
  tempo e valor pesam mais na decisão do que "quem vende o quê".

### Tratamento dos dados (`backend/app/dados/carregador.py`)

- Produto `GTXPro` no pipeline é corrigido para `GTX Pro`.
- Setor `technolgy` é corrigido para `technology`.
- 1.425 negócios abertos não têm conta: aparecem como "sem conta" e o score
  usa só os demais fatores.
- Negócios abertos não têm valor fechado: usamos o preço de tabela do produto.
- Os dados terminam em 31/12/2017, então essa é a data de "hoje"
  (`DATA_REFERENCIA` em `config.py`).

## Arquitetura do backend

```
app/
  main.py               cria a API e registra as rotas
  config.py             tudo que é ajustável
  esquemas.py           formato das respostas (Pydantic)
  dados/carregador.py   lê e limpa os CSVs        ← único ponto que conhece a origem dos dados
  servicos/
    estatisticas.py     taxas de vitória e ciclo de vendas históricos
    pontuacao.py        score, prioridade, motivos e sugestão   ← regra de negócio
    consultas.py        filtros, resumo e conversão para a API
  rotas/                endpoints HTTP (finos, só chamam os serviços)
```

Endpoints: `GET /api/pipeline`, `GET /api/deals/{id}`, `GET /api/resumo`, `GET /api/filtros`, `GET /api/regras`.
`/api/pipeline` e `/api/resumo` aceitam os filtros `vendedor`, `manager`,
`escritorio`, `produto`, `prioridade` e `busca`.

Os dados são carregados e pontuados uma vez, na subida do servidor, e ficam em memória.

## Próximos passos possíveis

- **Banco de dados:** reescrever `carregar_deals()` para ler de um banco, mantendo as colunas. O resto não muda.
- **Machine learning:** trocar o cálculo em `pontuar_deals_abertos()` por um modelo treinado com os negócios fechados, mantendo as colunas de saída.
- **Login por vendedor:** abrir a tela já filtrada pelo vendedor logado.
- **Atualização dos dados:** hoje é preciso reiniciar o servidor para recarregar os CSVs.
