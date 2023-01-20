import pandas as pd
from dfproducts import df_prod

df_extractions = pd.read_excel("Entwurf.xlsx", "Extraktionen", engine="openpyxl")
df_extractions["Extraktionskonzentration [g/ml]"] = df_extractions["Ausgangsmasse [g]"]/df_extractions["v Lösemittel [ml]"]
df_extractions["Fällungskonzentration [g/ml]"] = df_extractions["m Extraktionslösung [g]"]/df_extractions["v Fällungsmittel [ml]"]

df_extractions = df_prod.merge(df_extractions, left_on='Versuch', right_on='Versuchskürzel')
df_extractions.rename(columns={'Produktfraktion': 'Inhalt', "Vorextraktionen [n] ": "Vorextraktionen [n]"}, inplace=True)


if __name__ == "__main__":
    print(df_extractions.info())
