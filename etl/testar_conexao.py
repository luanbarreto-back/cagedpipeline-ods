import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
engine = create_engine(url)

with engine.connect() as conn:
    print(conn.execute(text("select version()")).scalar())
    print("Tamanho do banco:", conn.execute(
        text("select pg_size_pretty(pg_database_size(current_database()))")
    ).scalar())