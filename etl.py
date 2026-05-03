"""
ETL - Knowledge Engine FIFA Players
====================================
Le um CSV do dataset FIFA (Kaggle) e gera um arquivo base.pl
com fatos Prolog no formato:

    jogador(Nome, Nacionalidade, Clube, Posicao, Idade, Overall, Potencial, Valor).

Uso:
    python etl.py <caminho_do_csv>

Exemplo:
    python etl.py players_22.csv
"""

import pandas as pd
import unicodedata
import re
import sys
from pathlib import Path


# =============================================================================
# Configuracoes
# =============================================================================

# Mapeamento flexivel: tentamos varios nomes possiveis para cada campo,
# pois diferentes versoes do dataset FIFA usam nomes diferentes.
CAMPOS_POSSIVEIS = {
    "nome":          ["short_name", "name", "long_name", "Name"],
    "nacionalidade": ["nationality_name", "nationality", "Nationality"],
    "clube":         ["club_name", "club", "Club"],
    "posicao":       ["player_positions", "position", "Position", "club_position"],
    "idade":         ["age", "Age"],
    "overall":       ["overall", "Overall"],
    "potencial":     ["potential", "Potential"],
    "valor":         ["value_eur", "value", "Value", "wage_eur"],
}

# Quantos jogadores manter no dataset final (pega os melhores por overall).
# Mantemos um numero moderado para o SWISH nao travar.
TOP_N = 600


# =============================================================================
# Limpeza de strings para Prolog
# =============================================================================

def normalizar(texto):
    """
    Converte uma string para o formato Prolog: minusculas, sem acentos,
    sem espacos, sem caracteres especiais.

    Em Prolog, atomos (constantes) precisam comecar com letra minuscula
    e nao podem ter caracteres especiais sem aspas. Vamos garantir isso.
    """
    if pd.isna(texto):
        return "desconhecido"

    texto = str(texto).strip().lower()

    # Remover acentos (NFD decompoe acentos, depois filtramos)
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")

    # Substituir qualquer caractere nao alfanumerico por _
    texto = re.sub(r"[^a-z0-9]+", "_", texto)

    # Tirar _ no comeco e no fim
    texto = texto.strip("_")

    # Se ficou vazio, retornar default
    if not texto:
        return "desconhecido"

    # Prolog exige que atomos comecem com letra minuscula.
    # Se comecou com numero, prefixar com _
    if texto[0].isdigit():
        texto = "n_" + texto

    return texto


# =============================================================================
# Detectar campos no CSV
# =============================================================================

def detectar_campo(df, nomes_possiveis):
    """Encontra qual coluna do DF corresponde a um campo logico."""
    for nome in nomes_possiveis:
        if nome in df.columns:
            return nome
    return None


def mapear_colunas(df):
    """Cria um dicionario {campo_logico: nome_real_no_csv}."""
    mapa = {}
    faltando = []
    for campo, possiveis in CAMPOS_POSSIVEIS.items():
        coluna = detectar_campo(df, possiveis)
        if coluna is None:
            faltando.append(campo)
        else:
            mapa[campo] = coluna
    return mapa, faltando


# =============================================================================
# ETL principal
# =============================================================================

def gerar_base(caminho_csv, caminho_saida="base.pl"):
    """Le o CSV e gera o arquivo base.pl com os fatos Prolog."""

    print(f"Lendo CSV: {caminho_csv}")
    df = pd.read_csv(caminho_csv, low_memory=False)
    print(f"  Linhas originais: {len(df)}")
    print(f"  Colunas disponiveis: {list(df.columns)[:15]}...")

    # Detectar quais colunas usar
    mapa, faltando = mapear_colunas(df)

    if faltando:
        print("\n[ERRO] Nao consegui encontrar as seguintes colunas no CSV:")
        for campo in faltando:
            print(f"  - {campo} (tentei: {CAMPOS_POSSIVEIS[campo]})")
        print(f"\nColunas que existem no seu CSV:\n{list(df.columns)}")
        print("\nEdite o dicionario CAMPOS_POSSIVEIS no inicio do script para incluir o nome correto.")
        sys.exit(1)

    print("\nMapeamento de colunas detectado:")
    for campo, coluna in mapa.items():
        print(f"  {campo:15s} -> {coluna}")

    # Selecionar e renomear colunas
    df = df[[mapa[c] for c in CAMPOS_POSSIVEIS.keys()]].copy()
    df.columns = list(CAMPOS_POSSIVEIS.keys())

    # Remover linhas com dados faltantes nos campos criticos
    df = df.dropna(subset=["nome", "overall", "potencial", "valor"])

    # Manter apenas os TOP_N melhores por overall
    df = df.sort_values("overall", ascending=False).head(TOP_N).reset_index(drop=True)
    print(f"\nApos filtrar e pegar top {TOP_N}: {len(df)} jogadores")

    # Gerar fatos Prolog
    fatos = []
    nomes_vistos = {}  # para desambiguar nomes duplicados

    for _, row in df.iterrows():
        nome_base = normalizar(row["nome"])

        # Se ja vimos esse nome, adicionar sufixo numerico
        if nome_base in nomes_vistos:
            nomes_vistos[nome_base] += 1
            nome = f"{nome_base}_{nomes_vistos[nome_base]}"
        else:
            nomes_vistos[nome_base] = 1
            nome = nome_base

        nacionalidade = normalizar(row["nacionalidade"])
        clube         = normalizar(row["clube"])

        # Posicao pode vir como "ST, CF, RW" - pegamos so a primeira
        posicao_raw = str(row["posicao"]).split(",")[0].strip()
        posicao     = normalizar(posicao_raw)

        # Numericos
        try:
            idade     = int(row["idade"])
            overall   = int(row["overall"])
            potencial = int(row["potencial"])
            valor     = int(float(row["valor"]))
        except (ValueError, TypeError):
            continue

        fato = (
            f"jogador({nome}, {nacionalidade}, {clube}, {posicao}, "
            f"{idade}, {overall}, {potencial}, {valor})."
        )
        fatos.append(fato)

    # Escrever arquivo .pl
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("% =====================================================\n")
        f.write("% Base de Conhecimento - FIFA Players\n")
        f.write("% Gerado automaticamente por etl.py\n")
        f.write("%\n")
        f.write("% Predicado: jogador/8\n")
        f.write("%   jogador(Nome, Nacionalidade, Clube, Posicao,\n")
        f.write("%           Idade, Overall, Potencial, Valor).\n")
        f.write(f"% Total de jogadores: {len(fatos)}\n")
        f.write("% =====================================================\n\n")
        for fato in fatos:
            f.write(fato + "\n")

    print(f"\n[OK] Arquivo gerado: {caminho_saida}")
    print(f"   Total de fatos: {len(fatos)}")
    print(f"\nProximo passo:")
    print(f"   1. Abra https://swish.swi-prolog.org/")
    print(f"   2. Cole o conteudo de {caminho_saida} + queries.pl na area Program")
    print(f"   3. Faca queries como: ?- ranking_clubes(R).")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python etl.py <caminho_do_csv> [arquivo_saida.pl]")
        print("Exemplo: python etl.py players_22.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "base.pl"

    if not Path(csv_path).exists():
        print(f"[ERRO] Arquivo nao encontrado: {csv_path}")
        sys.exit(1)

    gerar_base(csv_path, out_path)
