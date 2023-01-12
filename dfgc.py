import pandas as pd
from dfsamples import df_samples

df_gc = pd.read_excel("Entwurf.xlsx", "GC-Messungen", engine="openpyxl")
df_gc_standards = pd.read_excel("Entwurf.xlsx", "GC-Standards", engine="openpyxl")
df_gc_standards["cal HHx m corr"] = df_gc_standards["cal HHx m"] * df_gc_standards["HHx Korrekturfaktor"]
df_gc = df_gc.merge(df_gc_standards, left_on="GC-IS Nr.", right_on="GC-IS Nr.")
df_gc["m HB"] = df_gc["A HB"] / df_gc["A IS"] * df_gc["cal HB m"]
df_gc["m HHx"] = df_gc["A HHx"] / df_gc["A IS"] * df_gc["cal HHx m corr"]
df_gc = df_gc.merge(df_samples[['D5-AP Nr.', 'Inhalt', 'Versuch', 'Probenmasse [g]']], left_on='D5-AP Nr.', right_on='D5-AP Nr.')
df_gc['Reinheit [%]'] = df_gc["m HHx"] + df_gc["m HB"] / df_gc['Probenmasse [g]']
df_gc['n HB [mol]'] = df_gc["m HB"]/86.092
df_gc['n HHx [mol]'] = df_gc["m HHx"]/114.144
df_gc['x HHx [%]'] = df_gc['n HHx [mol]'] / (df_gc["n HHx [mol]"] + df_gc["n HB [mol]"])
df_gc['x HB [%]'] = df_gc['n HB [mol]'] / (df_gc["n HHx [mol]"] + df_gc["n HB [mol]"])
df_gc = df_gc.drop(['GC-IS Nr.', 'Probenmasse [g]', 'HHx Korrekturfaktor', 'cal HHx m'], axis=1)

if __name__ == "__main__":
    print(df_gc.info())
