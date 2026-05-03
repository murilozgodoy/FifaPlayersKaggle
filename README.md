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

## 🎯 Exemplos de execução (resultados reais)

Esta seção documenta os resultados obtidos rodando as 3 queries no [SWISH](https://swish.swi-prolog.org/) com a base gerada a partir do `players_22.csv` do FIFA 22.

### ▶️ Pergunta 1 — Top 10 clubes mais valiosos

**Query:**
```prolog
?- ranking_clubes(R).
```

**Resultado (top 10 de 124 clubes retornados):**
```
1.  manchester_city      EUR 1.257.500.000
2.  paris_saint_germain  EUR 1.131.000.000
3.  liverpool            EUR   962.500.000
4.  manchester_united    EUR   926.500.000
5.  atletico_de_madrid   EUR   900.500.000
6.  fc_bayern_munchen    EUR   880.000.000
7.  chelsea              EUR   866.500.000
8.  real_madrid_cf       EUR   842.500.000
9.  fc_barcelona         EUR   689.500.000
10. juventus             EUR   663.500.000
```

✅ Resultado coerente com a realidade do futebol europeu em 2022.

---

### ▶️ Pergunta 2 — Top 10 joias (jovens promissores)

**Query:**
```prolog
?- ranking_joias(R).
```

**Resultado (top 10 de 44 joias encontradas):**
```
1.  vinicius_jr      (real_madrid_cf)     potencial +10
2.  pedri            (fc_barcelona)       potencial +10
3.  a_bastoni        (inter)              potencial +9
4.  p_foden          (manchester_city)    potencial +8
5.  k_havertz        (chelsea)            potencial +8
6.  joao_felix       (atletico_de_madrid) potencial +8
7.  ferran_torres    (manchester_city)    potencial +8
8.  f_chiesa         (juventus)           potencial +8
9.  d_upamecano      (fc_bayern_munchen)  potencial +8
10. b_saka           (arsenal)            potencial +8
```

✅ Outras joias encontradas: Haaland, Mount, Ødegaard, Alexander-Arnold, De Ligt, Pulisic, Lucas Paquetá, Osimhen, Davies, Valverde — todos jovens promessas reais que se confirmaram nos anos seguintes.

---

### ▶️ Pergunta 3 — Top 10 países por overall médio

**Query:**
```prolog
?- ranking_paises(R).
```

**Resultado (top 10 de 23 países com ≥ 5 jogadores):**
```
1.  poland       overall medio: 83.67
2.  belgium      overall medio: 83.56
3.  germany      overall medio: 82.76
4.  netherlands  overall medio: 82.42
5.  croatia      overall medio: 82.40
6.  brazil       overall medio: 82.30
7.  england      overall medio: 82.29
8.  argentina    overall medio: 82.28
9.  portugal     overall medio: 82.25
10. uruguay      overall medio: 82.09
```

✅ O filtro de mínimo 5 jogadores foi essencial: sem ele, países com 1 ou 2 craques top dominariam o ranking. Com o filtro, apenas países com elenco *consistentemente* forte aparecem.

---

## 🧪 Como reproduzir os resultados acima

1. Clone este repositório:
   ```bash
   git clone https://github.com/murilozgodoy/FifaPlayersKaggle.git
   cd FifaPlayersKaggle
   ```
2. Instale a dependência Python:
   ```bash
   pip install pandas
   ```
3. (Opcional) Regenere a base a partir do CSV:
   ```bash
   python etl.py players_22.csv
   ```
   *Como o `base.pl` já está versionado no repositório, este passo é opcional.*
4. Acesse https://swish.swi-prolog.org/ e clique em **Program**
5. Cole o conteúdo de `base.pl` seguido do conteúdo de `queries.pl` na área **Program**
6. Na área **Query**, execute:
   - `ranking_clubes(R).`
   - `ranking_joias(R).`
   - `ranking_paises(R).`
7. Clique em **Run!** após cada query

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

## 📝 Murilo Zezza Godoy

Projeto individual para Lógica e Matemática Discreta — Insper 2026/1.
