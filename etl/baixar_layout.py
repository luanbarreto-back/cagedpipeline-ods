from ftplib import FTP

ftp = FTP("ftp.mtps.gov.br", timeout=60)
ftp.encoding = "latin-1"
ftp.login()
ftp.cwd("/pdet/microdados/NOVO CAGED")

nome = "Layout Não-identificado Novo Caged Movimentação.xlsx"
with open("data/raw/layout_caged.xlsx", "wb") as f:
    ftp.retrbinary(f"RETR {nome}", f.write)
ftp.quit()
print("Layout baixado!")