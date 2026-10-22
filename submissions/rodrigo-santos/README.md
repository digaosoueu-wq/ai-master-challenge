# Submissão — Rodrigo Santos — Challenge 003

## Sobre mim

- **Nome:** Rodrigo Santos
- **LinkedIn:** https://www.linkedin.com/in/rodrigo-dos-santos/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma aplicação web (FastAPI + React) que o vendedor abre e vê o pipeline já ordenado por prioridade. Cada negócio aberto recebe uma nota de 0 a 100, que é a soma de três partes visíveis: chance histórica de fechar, valor e ritmo da negociação. Junto vêm o principal motivo da nota e uma sugestão do que fazer. O achado mais importante veio dos dados, não do modelo: **negócios ganhos fecham em 57 dias (mediana) e quase nenhum passa de 125, mas 85% dos negócios "em negociação" (1.357 de 1.589) já passaram desse prazo**. É ali que o vendedor perde tempo. A recomendação é usar a ferramenta para separar os 165 negócios de prioridade alta e fazer uma limpeza ativa dos negócios parados.

![Tela do pipeline](docs/tela-pipeline.png)

---

## Solução

Código, dados e instruções de setup em [`solution/`](solution/). Detalhes da lógica em [`solution/README.md`](solution/README.md).

### Como rodar

Só é preciso **Python 3.10 ou mais novo** (testado em 3.10, 3.12, 3.13 e 3.14). A tela já vem compilada e é servida pela própria API.

**Windows (PowerShell ou CMD)**, a partir desta pasta:

```
cd solution\backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app
```

**Mac / Linux**, a partir desta pasta:

```
cd solution/backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app
```

Abra **http://localhost:8000**.

Para desenvolver a tela com Node.js, rodar os testes (22) ou resolver problemas comuns, veja [`solution/README.md`](solution/README.md#como-rodar).

### Abordagem

1. **Entender os dados antes de modelar.** Perfilei as 4 tabelas e encontrei:
   - inconsistências: o produto `GTXPro` no pipeline não casa com `GTX Pro` no catálogo, e o setor `technolgy` está escrito errado;
   - 1.425 negócios abertos sem conta;
   - negócios abertos sem valor de fechamento;
   - dados que terminam em 2017, então "hoje" precisa ser a última data do dataset.
2. **Descobrir o que realmente diferencia os negócios.** As taxas de vitória por produto e vendedor variam pouco (55% a 70%). Já o **tempo aberto** separa muito: nenhum negócio ganho levou mais de 138 dias, e a maioria dos abertos já passou disso. Por isso o tempo é um dos três fatores, e não um detalhe.
3. **Pontuação explicável em vez de modelo opaco.** O enunciado pede que o vendedor entenda o porquê da nota. Escolhi regras com pesos claros, em que a soma dos pontos é a nota (ex.: 35 + 26 + 30 = 91), em vez de um modelo de ML que não dá para explicar.
4. **Interface para quem não é técnico.** Quadro por etapa, selo de prioridade, motivo principal no cartão, painel "o que fazer / por quê" e uma tela "Como funciona a pontuação".

### Lógica da pontuação

| Parte | Vale até | Critério | Por quê |
|---|---|---|---|
| Chance de fechar | 35 pts | Taxa de vitória histórica de negócios do mesmo produto, vendedor, setor e conta (suavizada para grupos pequenos), comparada aos outros negócios abertos | Usa o histórico real de ganhos e perdas |
| Valor | 35 pts | Preço do produto em escala logarítmica (US$ 55 a US$ 26.768) | Sem o log, só o produto mais caro importaria |
| Ritmo | 30 pts | Todos os pontos até 88 dias aberto; zera com 125 dias (percentis 75 e 98 do ciclo dos negócios ganhos) | É o sinal mais forte nos dados |

**Prioridade:** Alta ≥ 60 · Média ≥ 40 · Baixa < 40. Todos os pesos e limites ficam em [`config.py`](solution/backend/app/config.py), e a tela de explicação lê os valores direto da API.

### Resultados

- **2.089 negócios abertos** pontuados. **165 de prioridade alta**, 824 média e 1.100 baixa.
- **1.481 negócios esfriando**: abertos há mais tempo que 75% dos negócios ganhos levaram para fechar.
- Para cada negócio, a ferramenta mostra:
  - os pontos de cada parte, que somam a nota;
  - os motivos em linguagem simples, como "Parado há 129 dias: quase nenhum negócio ganho demorou mais de 125 dias" ou "Histórico de Maureen Marcano: 69% de vitórias (acima da média de 63%)";
  - uma ação sugerida: "Priorize", "Retome o contato" ou "Reavalie e encerre".
- Filtros por vendedor, gerente, escritório, produto, prioridade e busca. Os cartões de resumo acompanham os filtros.

### Recomendações

1. **Segunda-feira de manhã:** cada vendedor filtra o próprio nome e trabalha primeiro os negócios de prioridade alta.
2. **Limpeza do pipeline:** os 1.357 negócios parados há mais de 125 dias devem receber um último contato ou ser encerrados. Mantê-los abertos distorce previsões e consome atenção.
3. **Qualidade de dados:** tornar a conta obrigatória no CRM. 1.425 negócios abertos estão sem ela, o que piora a pontuação.
4. **Gestores:** usar o filtro por gerente para acompanhar quem acumula negócios esfriando.

### Limitações

- **A pontuação não foi validada com backtest.** Os pesos são heurísticos, baseados na análise dos dados. O próximo passo seria medir, com negócios já fechados, se notas altas de fato fecham mais.
- **O valor esperado (chance × valor) está otimista**, porque a chance não desconta o tempo parado. 67% dele (US$ 2,1 mi de US$ 3,1 mi) está em negócios parados há mais de 125 dias.
- **O dataset não traz histórico de atividades** (ligações, e-mails, mudanças de etapa), que seria o sinal mais forte de engajamento.
- Os dados são de 2017, então "hoje" é a última data do dataset (configurável).
- **Ainda não está pronta para produção:** não tem login nem banco, e os dados são CSVs carregados na memória (recarregar exige reiniciar). A arquitetura isola esses pontos: trocar a fonte de dados mexe só em `carregador.py`, e trocar a pontuação por ML mexe só em `pontuacao.py`.

---

## Process Log — Como usei IA

> O registro completo da conversa está em [`process-log/`](process-log/).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (extensão do VS Code, modelo Claude Opus) | Planejamento, análise exploratória dos dados, construção do backend e do frontend, testes, verificação visual por captura de tela e fluxo de git |

### Workflow

1. **Briefing:** passei ao Claude o problema como recebi (vendedores perdendo tempo com negócios que não fecham), os requisitos (pipeline claro para quem não é técnico, começar simples, código limpo e comentado) e a estrutura dos dados.
2. **Planejamento (modo de plano):** o Claude perfilou os CSVs antes de propor qualquer código e me fez duas perguntas. Decidi **FastAPI + React** pela manutenção e expansão, e **tudo em português** (interface, código e comentários) para o time que vai manter.
3. **Primeira versão:** backend com pontuação, API e 16 testes, depois o frontend. O Claude subiu os dois servidores, testou a API e conferiu a tela por captura com o navegador em modo headless.
4. **Revisão crítica da explicabilidade:** cobrei que o vendedor precisa entender por que uma nota é alta e outra baixa. O Claude reconheceu que isso só estava parcialmente atendido e fez a segunda iteração:
   - pontos por fator que somam a nota;
   - motivo principal em cada cartão;
   - tela "Como funciona a pontuação";
   - mais 5 testes.
5. **Submissão:** fork, branch e estrutura `submissions/rodrigo-santos/`, seguindo o guia do desafio.

### Onde a IA errou e como corrigi

- **A primeira entrega não explicava a nota.** Mostrava fatores de 0 a 10 que não somavam a nota, e o cartão não mostrava motivo nenhum. Cobrei isso, e a pontuação foi refeita como uma soma de pontos visível.
- **Diferença de arredondamento:** a soma dos pontos podia diferir da nota em 1. Corrigido calculando a nota como soma dos pontos já arredondados, com teste garantindo isso.
- **Cartões pouco informativos:** centenas apareciam como "Conta não informada". Identificado na captura de tela e trocado pelo código do negócio.
- **Texto que presumia gênero:** "O vendedor Maureen..." foi reescrito como "Histórico de Maureen Marcano: ...".
- **Ambiente:**
  - a porta 5173 estava ocupada por outra aplicação, e o primeiro teste bateu na aplicação errada;
  - o proxy do Vite apontava para `localhost`, que no Node 22 pode resolver para IPv6 e não alcançar o uvicorn. Trocado por `127.0.0.1`.
- **Git:** o `.gitignore` do repositório original ignora `submissions/`. A pasta foi adicionada com `git add -f`, copiando só arquivos limpos (sem `.venv` e `node_modules`).

### O que eu adicionei que a IA sozinha não faria

- **O enquadramento do problema e o critério de sucesso:** uma ferramenta para vendedor que não é técnico, não um modelo.
- **As decisões de stack e de idioma**, pensando em quem vai manter o código.
- **A exigência de explicabilidade** que levou à segunda versão, que é exatamente o critério central do desafio.
- **A condução do processo em etapas** (solução → git → documentação) e a revisão de cada entrega antes de seguir.

---

## Evidências

- [x] Chat export: registro da conversa em [`process-log/`](process-log/)
- [x] Screenshots: [`docs/tela-pipeline.png`](docs/tela-pipeline.png) e capturas usadas na verificação
- [x] Git history: commits na branch `submission/rodrigo-santos`
- [ ] Screen recording

---

_Submissão enviada em: outubro de 2026_
