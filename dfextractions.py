import pandas as pd

df_extractions = pd.read_excel("Entwurf.xlsx", "Extraktionen", engine="openpyxl")
df_extractions["Extraktionskonzentration [g/ml]"] = df_extractions["Ausgangsmasse [g]"]/df_extractions["v Lösemittel [ml]"]
df_extractions["Fällungskonzentration [g/ml]"] = df_extractions["m Extraktionslösung [g]"]/df_extractions["v Fällungsmittel [ml]"]


if __name__ == "__main__":
    print(df_extractions.info())
