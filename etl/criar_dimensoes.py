import os
import pandas as pd
from sqlalchemy import create_engine

ARQ = "data/raw/layout_caged.xlsx"
ADMISSAO = {"10", "20", "25", "35", "70", "97"}
DESLIGAMENTO = {"31", "32", "33", "40", "43", "45", "50", "60", "80", "90", "98"}
TRANSFERENCIA = {"70", "80"}


def aba(nome):
    df = pd.read_excel(ARQ, sheet_name=nome, dtype=str).iloc[:, :2]
    df.columns = ["codigo", "descricao"]
    df = df.dropna()
    df["codigo"] = df["codigo"].str.strip()
    return df.reset_index(drop=True)


tipo = aba("tipomovimentação")
tipo["natureza"] = tipo["codigo"].map(
    lambda c: "admissao" if c in ADMISSAO else ("desligamento" if c in DESLIGAMENTO else "outro"))
tipo["transferencia"] = tipo["codigo"].isin(TRANSFERENCIA)

tabelas = {
    "dim_sexo": aba("sexo"),
    "dim_raca_cor": aba("raçacor"),
    "dim_secao": aba("seção"),
    "dim_grau_instrucao": aba("graudeinstrução"),
    "dim_tipo_mov": tipo,
}

engine = create_engine(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
with engine.begin() as conn:
    for nome, df in tabelas.items():
        df.to_sql(nome, conn, if_exists="replace", index=False)
        print(nome, len(df), "linhas")