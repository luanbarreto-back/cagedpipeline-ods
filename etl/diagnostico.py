import os
import time

from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
engine = create_engine(url, connect_args={"connect_timeout": 15})

t = time.time()
with engine.connect() as c:
    print("conexão ok em", round(time.time() - t, 2), "s")
    for tab in ("fato_movimentacao", "fato_tipo_mov"):
        t = time.time()
        n = c.execute(text(f"select count(*) from {tab}")).scalar()
        print(tab, n, "linhas,", round(time.time() - t, 2), "s")
    print("por competência:", c.execute(text(
        "select competencia, count(*) from fato_movimentacao group by 1 order by 1")).all())
    print("sessões ativas:")
    for r in c.execute(text(
        "select state, wait_event_type, now() - query_start, left(query, 70) "
        "from pg_stat_activity where datname = current_database() and pid <> pg_backend_pid()")):
        print("  ", r)