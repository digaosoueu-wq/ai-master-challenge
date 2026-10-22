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

**Pré-requisito:** Python 3.10 ou mais novo (testado em 3.10, 3.12, 3.13 e 3.14).
Node.js só é necessário para alterar a tela (opção B).

Todos os comandos abaixo partem da pasta `solution/`.

### Opção A — Ver a aplicação (só Python, recomendado)

A tela já vem compilada em `frontend/dist`, e a própria API a serve.

**Windows (PowerShell ou CMD)**

```
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app
```

**Mac / Linux**

```
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app
```

Quando aparecer `Application startup complete`, abra **http://localhost:8000**.
A documentação da API fica em http://localhost:8000/docs. Para parar, use `Ctrl+C`.

> Os comandos chamam o Python de dentro do `.venv` diretamente, então não é preciso
> "ativar" o ambiente virtual (o que às vezes é bloqueado no PowerShell).

### Opção B — Desenvolver a tela (Python + Node.js 18 ou mais novo)

Deixe a API da opção A rodando e, em **outro terminal**, a partir de `solution/`:

```
cd frontend
npm install
npm run dev
```

Abra o endereço que o Vite mostrar (normalmente http://localhost:5173). As alterações no
código aparecem na hora. As chamadas `/api` são repassadas para a API na porta 8000
(ver `frontend/vite.config.ts`).

Depois de alterar a tela, rode `npm run build` para atualizar `frontend/dist`
(a versão servida na opção A).

### Testes

```
cd backend
.venv\Scripts\python -m pytest        # Windows
.venv/bin/python -m pytest             # Mac / Linux
```

### Problemas comuns

| Sintoma | Solução |
|---|---|
| `python` não é reconhecido (Windows) | Use `py` no lugar de `python` no comando que cria o `.venv`, ou instale o Python em python.org marcando "Add python.exe to PATH". |
| Erro de "Long Path" ao instalar (Windows) | O caminho da pasta ficou longo demais. Clone o repositório numa pasta curta, como `C:\projetos\`. |
| `address already in use` / porta 8000 ocupada | Outro programa usa a porta. Rode com `--port 8001` e abra http://localhost:8001. Na opção B, ajuste também a porta em `frontend/vite.config.ts`. |
| A tela mostra "Não foi possível carregar o pipeline" | A API não está rodando, ou não está na porta 8000. Veja o terminal da API. |
| http://localhost:8000 mostra `{"detail":"Not Found"}` | A pasta `frontend/dist` não existe. Rode `npm install` e `npm run build` em `frontend/` (ou use a opção B). |

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
