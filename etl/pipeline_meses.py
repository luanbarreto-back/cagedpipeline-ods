import os
import subprocess
import sys
from ftplib import FTP

import py7zr
from sqlalchemy import create_engine, text

MESES = [f"2025{m:02d}" for m in range(2, 13)]
os.makedirs("data/raw", exist_ok=True)
falhas = []

for comp in MESES:
    nome = f"CAGEDMOV{comp}.7z"
    destino = f"data/raw/{nome}"
    txt = f"data/raw/CAGEDMOV{comp}.txt"
    print(f"\n=== {comp} ===", flush=True)
    try:
        ftp = FTP("ftp.mtps.gov.br", timeout=120)
        ftp.encoding = "latin-1"
        ftp.login()
        ftp.cwd(f"/pdet/microdados/NOVO CAGED/{comp[:4]}/{comp}")
        with open(destino, "wb") as f:
            ftp.retrbinary(f"RETR {nome}", f.write)
        ftp.quit()

        with py7zr.SevenZipFile(destino) as z:
            z.extractall("data/raw")

        subprocess.run([sys.executable, "etl/carregar.py", txt], check=True)
    except Exception as e:
        print("FALHOU:", comp, e)
        falhas.append(comp)
    finally:
        for arq in (txt, destino):
            if os.path.exists(arq):
                os.remove(arq)

print("\nMeses com falha:", falhas or "nenhum")

engine = create_engine(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
with engine.connect() as c:
    print("\ncompetencia | admissoes | desligamentos | saldo")
    consulta = text("""
        select competencia, sum(admissoes), sum(desligamentos), sum(saldo)
        from fato_movimentacao group by 1 order by 1
    """)
    for linha in c.execute(consulta):
        print(*linha, sep=" | ")