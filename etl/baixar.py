
from ftplib import FTP
import os

os.makedirs("data/raw", exist_ok=True)

ftp = FTP("ftp.mtps.gov.br", timeout=60)
ftp.encoding = "latin-1"
ftp.login()
ftp.cwd("/pdet/microdados")

pastas = ftp.nlst()
print("Em /pdet/microdados:", pastas)
novo = [p for p in pastas if "NOVO" in p.upper()][0]
ftp.cwd(novo)

print("Anos:", ftp.nlst())
ftp.cwd("2025")

print("Meses:", ftp.nlst())
ftp.cwd("202501")

arquivos = ftp.nlst()
print("Arquivos:", arquivos)
alvo = [a for a in arquivos if os.path.basename(a).upper().startswith("CAGEDMOV")][0]
nome = os.path.basename(alvo)

print("Baixando", nome, "...")
with open(f"data/raw/{nome}", "wb") as f:
    ftp.retrbinary(f"RETR {nome}", f.write)
ftp.quit()
print("Pronto!")