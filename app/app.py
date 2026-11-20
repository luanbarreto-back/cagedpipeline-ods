import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Carrega as variáveis do .env quando existir
env_path = Path(__file__).resolve().parents[1] / ".env"

if env_path.exists():
    load_dotenv(env_path)


# Conexão com PostgreSQL
@st.cache_resource
def get_engine():
    if env_path.exists():
        config = os.environ
    else:
        config = st.secrets

    url = URL.create(
        "postgresql+psycopg",
        username=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=int(config["DB_PORT"]),
        database=config["DB_NAME"],
        query={"sslmode": config["DB_SSLMODE"]},
    )

    return create_engine(
        url,
        connect_args={"connect_timeout": 30},
        pool_pre_ping=True,
    )


# Carregamento dos dados
@st.cache_data(ttl=3600)
def carregar():
    engine = get_engine()

    with engine.connect() as conn:
        print("Iniciando consulta agregada das movimentações...", flush=True)

        fato = pd.read_sql_query(
            text("""
                SELECT
                    CAST(f.competencia AS TEXT) AS competencia,
                    s.descricao AS setor,
                    sx.descricao AS sexo,
                    r.descricao AS raca_cor,
                    SUM(f.admissoes) AS admissoes,
                    SUM(f.desligamentos) AS desligamentos,
                    SUM(f.sal_adm_soma)::DOUBLE PRECISION AS sal_adm_soma,
                    SUM(f.sal_desl_soma)::DOUBLE PRECISION AS sal_desl_soma
                FROM fato_movimentacao f
                JOIN dim_secao s ON s.codigo = f.secao
                JOIN dim_sexo sx ON sx.codigo = f.sexo
                JOIN dim_raca_cor r ON r.codigo = f.raca_cor
                GROUP BY
                    f.competencia,
                    s.descricao,
                    sx.descricao,
                    r.descricao
            """),
            conn,
        )

        print("Grupos de movimentações carregados:", len(fato), flush=True)
        print("Iniciando consulta agregada dos motivos...", flush=True)

        motivo = pd.read_sql_query(
            text("""
                SELECT
                    CAST(m.competencia AS TEXT) AS competencia,
                    sx.descricao AS sexo,
                    r.descricao AS raca_cor,
                    t.descricao AS motivo,
                    SUM(m.qtd) AS qtd
                FROM fato_tipo_mov m
                JOIN dim_tipo_mov t ON t.codigo = m.tipo_mov
                JOIN dim_sexo sx ON sx.codigo = m.sexo
                JOIN dim_raca_cor r ON r.codigo = m.raca_cor
                WHERE t.natureza = 'desligamento'
                GROUP BY
                    m.competencia,
                    sx.descricao,
                    r.descricao,
                    t.descricao
            """),
            conn,
        )

        print("Grupos de motivos carregados:", len(motivo), flush=True)

    return fato, motivo


fato, motivo = carregar()


# Preparação dos meses
for df in (fato, motivo):
    df["mes"] = (
        df["competencia"].astype(str).str[:4]
        + "-"
        + df["competencia"].astype(str).str[4:6]
    )


# Título
st.title("Dinâmica de emprego formal e rotatividade: gênero × raça/cor")
st.caption("Bahia, Novo CAGED (MTE/PDET). ODS 5 e ODS 18.")


# Filtros
with st.sidebar:
    st.header("Filtros")

    meses = sorted(fato["mes"].unique())
    f_mes = st.multiselect("Mês", meses, default=meses)

    sexos = sorted(fato["sexo"].unique())
    f_sexo = st.multiselect("Sexo", sexos, default=sexos)

    racas = sorted(fato["raca_cor"].unique())
    f_raca = st.multiselect("Raça/cor", racas, default=racas)

    setores = sorted(fato["setor"].unique())
    f_setor = st.multiselect("Setor (CNAE)", setores, default=setores)


# Aplicação dos filtros
d = fato[
    fato["mes"].isin(f_mes)
    & fato["sexo"].isin(f_sexo)
    & fato["raca_cor"].isin(f_raca)
    & fato["setor"].isin(f_setor)
]

m = motivo[
    motivo["mes"].isin(f_mes)
    & motivo["sexo"].isin(f_sexo)
    & motivo["raca_cor"].isin(f_raca)
]

if d.empty:
    st.warning("Nenhum dado para os filtros escolhidos.")
    st.stop()


# Indicadores
adm = int(d["admissoes"].sum())
desl = int(d["desligamentos"].sum())

c1, c2, c3, c4 = st.columns(4)

c1.metric("Admissões", f"{adm:,}".replace(",", "."))
c2.metric("Desligamentos", f"{desl:,}".replace(",", "."))
c3.metric("Saldo", f"{adm - desl:,}".replace(",", "."))
c4.metric(
    "Desligamentos por admissão",
    f"{desl / adm:.2f}" if adm else "-",
)


# Gráfico 1: desligamentos por admissão
perfil = d.groupby(
    ["sexo", "raca_cor"], as_index=False
)[["admissoes", "desligamentos"]].sum()

perfil["razao"] = (
    perfil["desligamentos"]
    / perfil["admissoes"].where(perfil["admissoes"] > 0)
).round(3)

fig1 = px.bar(
    perfil,
    x="raca_cor",
    y="razao",
    color="sexo",
    barmode="group",
    title="1. Desligamentos por admissão, por sexo e raça/cor",
    labels={
        "raca_cor": "Raça/cor",
        "razao": "Desligamentos / admissões",
        "sexo": "Sexo",
    },
)


# Gráfico 2: saldo por setor e sexo
setor = d.groupby(
    ["setor", "sexo"], as_index=False
)[["admissoes", "desligamentos"]].sum()

setor["saldo"] = setor["admissoes"] - setor["desligamentos"]

fig2 = px.bar(
    setor,
    x="saldo",
    y="setor",
    color="sexo",
    orientation="h",
    barmode="group",
    height=650,
    title="2. Saldo de empregos por setor e sexo",
    labels={
        "setor": "",
        "saldo": "Saldo (admissões - desligamentos)",
        "sexo": "Sexo",
    },
)


# Gráfico 3: salário médio
sal = d.groupby(
    ["sexo", "raca_cor"], as_index=False
)[
    [
        "admissoes",
        "desligamentos",
        "sal_adm_soma",
        "sal_desl_soma",
    ]
].sum()

sal["Admissão"] = (
    sal["sal_adm_soma"]
    / sal["admissoes"].where(sal["admissoes"] > 0)
)

sal["Desligamento"] = (
    sal["sal_desl_soma"]
    / sal["desligamentos"].where(sal["desligamentos"] > 0)
)

sal = sal.melt(
    id_vars=["sexo", "raca_cor"],
    value_vars=["Admissão", "Desligamento"],
    var_name="momento",
    value_name="salario_medio",
)

fig3 = px.bar(
    sal,
    x="raca_cor",
    y="salario_medio",
    color="sexo",
    barmode="group",
    facet_col="momento",
    title="3. Salário médio (R$) na admissão e no desligamento",
    labels={
        "raca_cor": "Raça/cor",
        "salario_medio": "Salário médio (R$)",
        "sexo": "Sexo",
    },
)


# Gráfico 4: evolução mensal
evo = d.groupby(
    "mes", as_index=False
)[["admissoes", "desligamentos"]].sum()

evo = evo.melt(
    id_vars="mes",
    var_name="tipo",
    value_name="qtd",
)

fig4 = px.line(
    evo,
    x="mes",
    y="qtd",
    color="tipo",
    markers=True,
    title="4. Evolução mensal de admissões e desligamentos",
    labels={
        "mes": "Mês",
        "qtd": "Movimentações",
        "tipo": "",
    },
)


# Gráfico 5: motivos de desligamento
mot = m.groupby(
    ["motivo", "sexo"], as_index=False
)["qtd"].sum()

fig5 = px.bar(
    mot,
    x="qtd",
    y="motivo",
    color="sexo",
    orientation="h",
    barmode="group",
    height=500,
    title="5. Tipos de desligamento por sexo",
    labels={
        "motivo": "",
        "qtd": "Desligamentos",
        "sexo": "Sexo",
    },
)


# Exibição dos gráficos
col_a, col_b = st.columns(2)

col_a.plotly_chart(fig1, use_container_width=True)
col_b.plotly_chart(fig4, use_container_width=True)

st.plotly_chart(fig3, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig5, use_container_width=True)


# Observações metodológicas
st.caption(
    "Notas: a base pública do Novo CAGED é anonimizada e não traz "
    "identificador do trabalhador nem tempo de emprego, então a permanência "
    "é analisada de forma agregada (razão entre desligamentos e admissões). "
    "Transferências entre estabelecimentos (códigos 70 e 80) foram excluídas. "
    "O filtro de setor não se aplica ao gráfico 5."
)