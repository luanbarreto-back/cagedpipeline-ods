import glob
import py7zr
import pandas as pd

arq = glob.glob("data/raw/CAGEDMOV*.7z")[0]
with py7zr.SevenZipFile(arq) as z:
    z.extractall("data/raw")

txt = glob.glob("data/raw/CAGEDMOV*.txt")[0]
df = pd.read_csv(txt, sep=";", encoding="utf-8", nrows=2000, dtype=str)

print(df.columns.tolist())
print(df.head(3).T)