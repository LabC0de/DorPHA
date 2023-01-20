import pandas as pd
import numpy as np
from dfsamples import df_samples

df_hplc_results = pd.read_excel("Entwurf.xlsx", "HPLC-Messungen", engine="openpyxl")
df_hplc_results = df_hplc_results.merge(df_samples[['D5-AP Nr.', 'Inhalt', 'Versuch']], left_on='D5-AP Nr.', right_on='D5-AP Nr.')
df_hplc_stat = df_hplc_results.groupby(["Versuch", "Inhalt"])[["Mp", "Mn", "Mw", "PDI", "max. Ret."]].agg([np.mean, np.std])
df_hplc_stat.columns = ['Mp (mean)', 'Mp (std)',
                        'Mn (mean)', 'Mn (std)',
                        'Mw (mean)', 'Mw (std)',
                        'PDI (mean)', 'PDI (std)',
                        'max. Ret. (mean)', 'max. Ret. (std)']
df_hplc_stat = df_hplc_stat.reset_index()

if __name__ == "__main__":
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, "display.width", 400):
        print(df_hplc_stat)