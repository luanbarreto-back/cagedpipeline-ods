import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Rotatividade no emprego formal | Bahia 2025", layout="wide")


@st.cache_resource
def get_engine():
    url = os.environ.get("DATABASE_URL") or st.secrets["DATABASE_URL"]
    return create_engine(url.replace("postgres://", "postgresql://", 1))


@st.cache_data(ttl=3600)
def carregar():
    e = get_engine()
    fato = pd.read_sql("""
        select f.competencia, s.descricao as setor, sx.descricao as sexo,
               r.descricao as raca_cor, f.faixa_etaria,
               f.admissoes, f.desligamentos, f.sal_adm_soma, f.sal_desl_soma
        from fato_movimentacao f
        join dim_secao s on s.codigo = f.secao
        join dim_sexo sx on sx.codigo = f.sexo
        join dim_raca_cor r on r.codigo = f.raca_cor
    """, e)
    motivo = pd.read_sql("""
        select m.competencia, sx.descricao as sexo, r.descricao as raca_cor,
               t.descricao as motivo, m.qtd
        from fato_tipo_mov m
        join dim_tipo_mov t on t.codigo = m.tipo_mov
        join dim_sexo sx on sx.codigo = m.sexo
        join dim_raca_cor r on r.codigo = m.raca_cor
        where t.natureza = 'desligamento'
    """, e)
    return fato, motivo


fato, motivo = carregar()
for df in (fato, motivo):
    df["mes"] = df["competencia"].str[:4] + "-" + df["competencia"].str[4:]

st.title("Dinâmica de emprego formal e rotatividade: gênero × raça/cor")
st.caption("Bahia, Novo CAGED (MTE/PDET). ODS 5 e ODS 18.")

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

d = fato[fato["mes"].isin(f_mes) & fato["sexo"].isin(f_sexo)
         & fato["raca_cor"].isin(f_raca) & fato["setor"].isin(f_setor)]
m = motivo[motivo["mes"].isin(f_mes) & motivo["sexo"].isin(f_sexo)
           & motivo["raca_cor"].isin(f_raca)]

if d.empty:
    st.warning("Nenhum dado para os filtros escolhidos.")
    st.stop()

adm, desl = int(d["admissoes"].sum()), int(d["desligamentos"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Admissões", f"{adm:,}".replace(",", "."))
c2.metric("Desligamentos", f"{desl:,}".replace(",", "."))
c3.metric("Saldo", f"{adm - desl:,}".replace(",", "."))
c4.metric("Desligamentos por admissão", f"{desl / adm:.2f}" if adm else "-")

# Métrica 1: razão desligamentos/admissões por sexo × raça/cor
perfil = d.groupby(["sexo", "raca_cor"], as_index=False)[["admissoes", "desligamentos"]].sum()
perfil["razao"] = (perfil["desligamentos"] / perfil["admissoes"].where(perfil["admissoes"] > 0)).round(3)
fig1 = px.bar(perfil, x="raca_cor", y="razao", color="sexo", barmode="group",
              title="1. Desligamentos por admissão, por sexo e raça/cor (acima de 1 = perda líquida)",
              labels={"raca_cor": "Raça/cor", "razao": "Desligamentos / admissões", "sexo": "Sexo"})

# Métrica 2: saldo por setor e sexo
setor = d.groupby(["setor", "sexo"], as_index=False)[["admissoes", "desligamentos"]].sum()
setor["saldo"] = setor["admissoes"] - setor["desligamentos"]
fig2 = px.bar(setor, x="saldo", y="setor", color="sexo", orientation="h", barmode="group", height=650,
              title="2. Saldo de empregos por setor e sexo",
              labels={"setor": "", "saldo": "Saldo (admissões - desligamentos)", "sexo": "Sexo"})

# Métrica 3: salário médio na admissão e no desligamento
sal = d.groupby(["sexo", "raca_cor"], as_index=False)[
    ["admissoes", "desligamentos", "sal_adm_soma", "sal_desl_soma"]].sum()
sal["Admissão"] = sal["sal_adm_soma"] / sal["admissoes"].where(sal["admissoes"] > 0)
sal["Desligamento"] = sal["sal_desl_soma"] / sal["desligamentos"].where(sal["desligamentos"] > 0)
sal = sal.melt(id_vars=["sexo", "raca_cor"], value_vars=["Admissão", "Desligamento"],
               var_name="momento", value_name="salario_medio")
fig3 = px.bar(sal, x="raca_cor", y="salario_medio", color="sexo", barmode="group", facet_col="momento",
              title="3. Salário médio (R$) na admissão e no desligamento",
              labels={"raca_cor": "Raça/cor", "salario_medio": "Salário médio (R$)", "sexo": "Sexo"})

# Métrica 4: evolução mensal
evo = d.groupby("mes", as_index=False)[["admissoes", "desligamentos"]].sum()
evo = evo.melt(id_vars="mes", var_name="tipo", value_name="qtd")
fig4 = px.line(evo, x="mes", y="qtd", color="tipo", markers=True,
               title="4. Evolução mensal de admissões e desligamentos",
               labels={"mes": "Mês", "qtd": "Movimentações", "tipo": ""})

# Métrica 5: motivos de desligamento
mot = m.groupby(["motivo", "sexo"], as_index=False)["qtd"].sum()
fig5 = px.bar(mot, x="qtd", y="motivo", color="sexo", orientation="h", barmode="group", height=500,
              title="5. Tipos de desligamento por sexo",
              labels={"motivo": "", "qtd": "Desligamentos", "sexo": "Sexo"})

col_a, col_b = st.columns(2)
col_a.plotly_chart(fig1, use_container_width=True)
col_b.plotly_chart(fig4, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig5, use_container_width=True)

st.caption(
    "Notas: a base pública do Novo CAGED é anonimizada e não traz identificador do trabalhador "
    "nem tempo de emprego, então a permanência é analisada de forma agregada (razão entre "
    "desligamentos e admissões). Transferências entre estabelecimentos (códigos 70 e 80) foram "
    "excluídas. O filtro de setor não se aplica ao gráfico 5."
)