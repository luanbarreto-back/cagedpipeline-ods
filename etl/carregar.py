import glob
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, inspect, text

UF = "29"  # Bahia
COLS = {
    "competênciamov": "competencia", "uf": "uf", "seção": "secao",
    "saldomovimentação": "saldo", "graudeinstrução": "grau_instrucao",
    "idade": "idade", "raçacor": "raca_cor", "sexo": "sexo",
    "tipomovimentação": "tipo_mov", "salário": "salario",
}
CHAVE = ["competencia", "secao", "sexo", "raca_cor", "faixa_etaria", "grau_instrucao"]


def tratar(df):
    df = df.rename(columns=COLS)
    df = df[df["uf"] == UF].copy()
    df = df[~df["tipo_mov"].isin(["70", "80"])]  # exclui transferências
    df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce")
    df = df.dropna(subset=["saldo"])
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    df["salario"] = pd.to_numeric(df["salario"].str.replace(",", ".", regex=False), errors="coerce")
    df["faixa_etaria"] = pd.cut(
        df["idade"], bins=[-1, 17, 24, 29, 39, 49, 59, 200],
        labels=["<18", "18-24", "25-29", "30-39", "40-49", "50-59", "60+"],
    ).astype(str).replace("nan", "ND")
    df["admissoes"] = (df["saldo"] == 1).astype(int)
    df["desligamentos"] = (df["saldo"] == -1).astype(int)
    df["sal_adm_soma"] = df["salario"].where(df["admissoes"] == 1, 0).fillna(0)
    df["sal_desl_soma"] = df["salario"].where(df["desligamentos"] == 1, 0).fillna(0)
    return df


txt = sys.argv[1] if len(sys.argv) > 1 else glob.glob("data/raw/CAGEDMOV*.txt")[0]
print("Lendo", txt)

fatos, tipos = [], []
leitor = pd.read_csv(txt, sep=";", encoding="utf-8", dtype=str,
                     usecols=list(COLS), chunksize=500_000)
for i, chunk in enumerate(leitor, 1):
    df = tratar(chunk)
    fatos.append(df.groupby(CHAVE, as_index=False)[
        ["admissoes", "desligamentos", "sal_adm_soma", "sal_desl_soma"]].sum())
    tipos.append(df.groupby(["competencia", "sexo", "raca_cor", "tipo_mov"],
                            as_index=False).size().rename(columns={"size": "qtd"}))
    print("chunk", i, "ok")

fato = pd.concat(fatos).groupby(CHAVE, as_index=False).sum()
fato["saldo"] = fato["admissoes"] - fato["desligamentos"]
tipo = pd.concat(tipos).groupby(
    ["competencia", "sexo", "raca_cor", "tipo_mov"], as_index=False).sum()

engine = create_engine(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
comps = fato["competencia"].unique().tolist()
insp = inspect(engine)

with engine.begin() as conn:
    for tabela in ("fato_movimentacao", "fato_tipo_mov"):
        if insp.has_table(tabela):
            conn.execute(text(f"delete from {tabela} where competencia = any(:c)"), {"c": comps})
    fato.to_sql("fato_movimentacao", conn, if_exists="append", index=False,
                method="multi", chunksize=2000)
    tipo.to_sql("fato_tipo_mov", conn, if_exists="append", index=False,
                method="multi", chunksize=2000)

with engine.connect() as conn:
    print("fato_movimentacao:", conn.execute(text("select count(*) from fato_movimentacao")).scalar(), "linhas")
    print("Tamanho do banco:", conn.execute(
        text("select pg_size_pretty(pg_database_size(current_database()))")).scalar())