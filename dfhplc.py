import pandas as pd
from dfsamples import df_samples

df_hplc_results = pd.read_excel("Entwurf.xlsx", "HPLC-Messungen", engine="openpyxl")
df_hplc_results = df_hplc_results.merge(df_samples[['D5-AP Nr.', 'Inhalt', 'Versuch']], left_on='D5-AP Nr.', right_on='D5-AP Nr.')
