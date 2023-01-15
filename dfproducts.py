import pandas as pd

df_prod = pd.read_excel("Entwurf.xlsx", "Produktfraktionen", engine="openpyxl")

if __name__ == "__main__":
    print(df_prod.info())