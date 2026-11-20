import pandas as pd

abas = pd.read_excel("data/raw/layout_caged.xlsx", sheet_name=None, header=None)
for nome, tabela in abas.items():
    print("=" * 60)
    print("ABA:", nome, tabela.shape)
    print(tabela.dropna(how="all").head(60).to_string(index=False, header=False))