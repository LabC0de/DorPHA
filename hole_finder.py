import pandas as pd


if __name__ == "__main__":
    df_ex = pd.read_excel("Entwurf.xlsx", "Extraktionen", engine="openpyxl")
    df_tr = pd.read_excel("Entwurf.xlsx", "Trocknungen", engine="openpyxl")
    df_vb = pd.read_excel("Entwurf.xlsx", "Vorbehandlungen Bis", engine="openpyxl")
    df_vd = pd.read_excel("Entwurf.xlsx", "Verdauungen", engine="openpyxl")

    df_samples = pd.read_excel("Entwurf.xlsx", "Analytikproben", engine="openpyxl")
    df_prod = pd.read_excel("Entwurf.xlsx", "Produktfraktionen", engine="openpyxl")
    df_hplc = pd.read_excel("Entwurf.xlsx", "HPLC-Messungen", engine="openpyxl")
    df_gc = pd.read_excel("Entwurf.xlsx", "GC-Messungen", engine="openpyxl")

    gc_measured = set(df_gc["D5-AP Nr."].unique())
    hplc_measured = set(df_hplc["D5-AP Nr."].unique())
    gc_samples = set(df_samples[df_samples["Analyse Methode"] == "GC"]["D5-AP Nr."].unique())
    hplc_samples = set(df_samples[df_samples["Analyse Methode"] == "HPLC"]["D5-AP Nr."].unique())

    analysed_experiments = set(df_samples["Versuch"])
    products = set(df_prod["Versuch"])
    experiments = set(df_ex["Versuchskürzel"].
                      append(df_tr["Versuchskürzel"]).
                      append(df_vb["Versuchskürzel"]).
                      append(df_vd["Versuchskürzel"]))

    print(f"[!] Not measured GC samples:\n\n{gc_samples.difference(gc_measured)}\n\n")
    print(f"[!] GC measurements without sample:\n\n{gc_measured.difference(gc_samples)}\n\n")

    print(f"[!] Not measured HPLC samples:\n\n{hplc_samples.difference(hplc_measured)}\n\n")
    print(f"[!] HPLC measurements without sample:\n\n{hplc_measured.difference(hplc_samples)}\n\n")

    print(f"[!] Experiments without Samples:\n\n{experiments.difference(analysed_experiments)}\n\n")
    print(f"[!] Samples without Experiments:\n\n{analysed_experiments.difference(experiments)}\n\n")

    print(f"[!] Experiments without Products:\n\n{experiments.difference(products)}\n\n")
    print(f"[!] Products without Experiments:\n\n{products.difference(experiments)}\n\n")
