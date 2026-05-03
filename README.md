# Knowledge Engine - FIFA Players

Projeto da disciplina **Lógica e Matemática Discreta (2026/1) - Insper**.

Construção de um mecanismo de busca utilizando **Lógica de Primeira Ordem** (Prolog) sobre uma base de jogadores do FIFA.

---

## 📂 Estrutura do projeto

```
.
├── etl.py          # Script Python: lê o CSV e gera base.pl
├── base.pl         # Base de conhecimento gerada (fatos Prolog)
├── queries.pl      # Regras (sentenças) que respondem as 3 perguntas
├── fifa_data.csv   # Dataset original (Kaggle - não versionado)
└── README.md       # Este arquivo
```

---

## 📊 Sobre o Dataset

**Fonte:** [FIFA Complete Player Dataset (Kaggle)](https://www.kaggle.com/datasets/stefanoleone992/fifa-22-complete-player-dataset)

Selecionei **8 campos** de uma única tabela, misturando variáveis qualitativas e quantitativas:

| Campo           | Tipo         | Descrição                              |
|-----------------|--------------|----------------------------------------|
| `Nome`          | qualitativa  | Nome do jogador                        |
| `Nacionalidade` | qualitativa  | País de origem                         |
| `Clube`         | qualitativa  | Clube atual                            |
| `Posicao`       | qualitativa  | Posição principal (ST, CB, GK, etc.)   |
| `Idade`         | quantitativa | Idade em anos                          |
| `Overall`       | quantitativa | Nota geral atual (0-99)                |
| `Potencial`     | quantitativa | Nota máxima estimada (0-99)            |
| `Valor`         | quantitativa | Valor de mercado em EUR                |

Foram mantidos os **600 jogadores com maior overall** para manter a base trabalhável no SWISH.

---

## 🔧 Como rodar

### 1. Gerar a base de conhecimento

Baixe o CSV do Kaggle, salve como `fifa_data.csv` na raiz do projeto, e execute:

```bash
pip install pandas
python etl.py fifa_data.csv
```

Isso gera o arquivo `base.pl` com fatos no formato:

```prolog
jogador(lionel_messi, argentina, paris_saint_germain, rw, 35, 93, 93, 54000000).
jogador(kylian_mbappe, france, paris_saint_germain, st, 23, 91, 95, 190500000).
...
```

### 2. Rodar as queries em Prolog

**Opção A — SWISH online (recomendado):**

1. Acesse https://swish.swi-prolog.org/
2. Cole o conteúdo de `base.pl` **e** `queries.pl` na área **Program**
3. Faça queries na área **Query** (veja exemplos abaixo)

**Opção B — SWI-Prolog local:**

```bash
swipl
?- consult(base).
?- consult(queries).
?- ranking_clubes(R).
```

---

## ❓ As 3 Perguntas

Todas as perguntas usam **agregação, ordenação e composição de regras** — não são filtros diretos.

### Pergunta 1 — Ranking de clubes por valor total de elenco

> "Quais os clubes mais valiosos, ordenados pelo valor total de seus jogadores?"

**Sofisticação:** agregação (`sum_list`) + ordenação (`setof`) + composição de 3 regras encadeadas.

**Predicados auxiliares construídos:**
- `clube/1` — lista clubes únicos (evita variável livre no `findall`)
- `valor_clube/2` — soma os valores dos jogadores de um clube
- `ranking_clubes/1` — ordena todos os clubes por valor total

**Query:**
```prolog
?- ranking_clubes(R).
R = [3572603585-atletico_madrid, 3006235426-manchester_city, ...]

?- valor_clube(real_madrid, V).
V = 2870451100
```

---

### Pergunta 2 — Joias escondidas (jovens promissores)

> "Quais jogadores são 'joias': jovens (≤ 23 anos) com potencial maior que o overall atual (diferença ≥ 5)?"

**Sofisticação:** composição de múltiplas regras + comparações aritméticas + cálculo derivado (a diferença não está nos dados originais — é computada).

**Predicados auxiliares construídos:**
- `jovem/1` — filtra jogadores com idade ≤ 23
- `promissor/2` — filtra jogadores com gap de potencial ≥ 5 e retorna a diferença
- `joia/3` — combina os dois critérios (interseção)
- `ranking_joias/1` — ordena pelas maiores diferenças

**Query:**
```prolog
?- ranking_joias(R).
R = [10-(vinicius_jr, real_madrid_cf), 10-(pedri, fc_barcelona), ...]

?- joia(Nome, Clube, Dif).
Nome = vinicius_jr, Clube = real_madrid_cf, Dif = 10 ;
...
```

---

### Pergunta 3 — Top países por overall médio (com mínimo de jogadores)

> "Quais os países com maior overall médio, considerando apenas países com pelo menos 5 jogadores no dataset?"

**Sofisticação:** **agregação dupla** (contagem + soma para calcular média) + **filtro condicional** (mínimo de 5 jogadores) + ordenação. Sem o filtro condicional, países com 1 jogador top dominariam o ranking.

**Predicados auxiliares construídos:**
- `pais/1` — lista países únicos
- `conta_jogadores_pais/2` — conta jogadores por país
- `soma_overall_pais/2` — soma os overalls do país
- `media_overall_pais/2` — combina contagem e soma com filtro `Total >= 5`
- `ranking_paises/1` — ordena pela média

**Query:**
```prolog
?- ranking_paises(R).
R = [83.91-netherlands, 83.17-uruguay, 82.87-brazil, ...]

?- media_overall_pais(brazil, M).
M = 82.87
```

---

## 🧠 Por que essas perguntas são "sofisticadas"?

Conforme a rubrica do projeto:

> *pergunta sofisticada = agregação, comparação, ordenação, composição de regras ou uso de predicados auxiliares.*

| Pergunta | Agregação | Comparação | Ordenação | Composição | Aux. |
|----------|:---------:|:----------:|:---------:|:----------:|:----:|
| 1        | ✅ `sum_list` | — | ✅ `setof + reverse` | ✅ 3 regras encadeadas | ✅ |
| 2        | — | ✅ `=<`, `>=`, `is` | ✅ `setof + reverse` | ✅ 4 regras compostas | ✅ |
| 3        | ✅ `length + sum_list` | ✅ filtro `>= 5` | ✅ `setof + reverse` | ✅ 5 regras encadeadas | ✅ |

---

## ⚙️ Decisões de modelagem

- **Normalização agressiva de strings:** Prolog exige átomos minúsculos sem acentos/espaços. O ETL converte `"Atlético Madrid"` → `atletico_madrid`, `"Müller"` → `muller`, etc.
- **Desambiguação de nomes:** quando dois jogadores têm o mesmo nome normalizado, o ETL acrescenta um sufixo numérico (`luka_modric`, `luka_modric_2`).
- **Filtro de top 600:** evita travar o SWISH e mantém os jogadores mais relevantes.
- **Posição única:** o CSV traz múltiplas posições por jogador (`"ST, CF, RW"`); mantemos apenas a primeira (principal).

---

## 🐛 Erros comuns que evitamos

- ✅ Maiúsculas/minúsculas — todas constantes em minúsculo
- ✅ Ponto final em todas as cláusulas
- ✅ Separação clara entre **Program** (base + regras) e **Query** (perguntas)
- ✅ Uso de predicados auxiliares (`clube/1`, `pais/1`) para evitar variáveis livres no `findall`

---

## 📝 Autor

Projeto individual para Lógica e Matemática Discreta — Insper 2026/1.
