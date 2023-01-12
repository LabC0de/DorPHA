import pandas as pd

df_samples = pd.read_excel("Entwurf.xlsx", "Analytikproben", engine="openpyxl")
df_samples["Probenmasse [g]"] = pd.to_numeric(df_samples["Probenmasse [g]"], errors='coerce')
df_samples["Tara [g]"] = pd.to_numeric(df_samples["Tara [g]"], errors='coerce')


if __name__ == "__main__":
    print(df_samples.info())
