"""
Skript zur Zusammenführung von Literatur-Exporten aus mehreren Datenbanken
und Erstellung einer duplikatbereinigten Screening-Tabelle.
Benötigt: pandas, rispy, bibtexparser, openpyxl
"""

import pandas as pd
import rispy
import bibtexparser
from pathlib import Path
import re

INPUT_FILES = [
    "Dateipfad.ris",
    "Dateipfad.bibtex",
    # beliebig weitere
]
OUTPUT_FILE = "Ausgabepfad/screening_tabelle.xlsx"

# Mapping für gängige Feldnamen der Datenbanken
FIELD_MAP = {
    "title": ["title", "TI", "primary_title"],
    "abstract": ["abstract", "AB", "notes_abstract"],
    "journal": ["journal", "journal_name", "JT", "TA", "booktitle"],
    "year": ["year", "PY", "DP"],
    "authors": ["authors", "AU", "FAU", "author"],
    "doi": ["doi", "DO", "AID", "LID"],
    "pmid": ["PMID", "pmid"],
}

def load_ris(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        records = rispy.load(f)
    return pd.DataFrame(records)

def load_bibtex(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        bibdb = bibtexparser.load(f)
    return pd.DataFrame(bibdb.entries)

def normalize_df(df_raw, source):
    def get_first(cols):
        for col in cols:
            if col in df_raw.columns:
                return df_raw[col]
        return pd.Series([None]*len(df_raw))
    df = pd.DataFrame()
    for key, variants in FIELD_MAP.items():
        val = get_first(variants)
        if key == "authors":
            df[key] = val.apply(lambda x: "; ".join(x) if isinstance(x, list) else x)
        elif key == "year":
            df[key] = val.astype(str).str.extract(r"(\d{4})", expand=False)
        elif key == "doi":
            df[key] = val.apply(lambda x: extract_doi(x))
        else:
            df[key] = val
    df["source"] = source
    return df

def extract_doi(x):
    if pd.isna(x):
        return ""
    if isinstance(x, list):
        for item in x:
            m = re.search(r"(10\.\S+)", str(item))
            if m: return m.group(1).rstrip("[];,. ")
        return ""
    m = re.search(r"(10\.\S+)", str(x))
    if m: return m.group(1).rstrip("[];,. ")
    return ""

def normalize_doi(doi):
    if pd.isna(doi): return ""
    d = str(doi).lower().strip()
    d = d.replace("https://doi.org/", "")
    d = d.replace("http://doi.org/", "")
    d = d.replace("doi:", "")
    d = d.rstrip("[];,. ")
    return d

def normalize_title(title):
    if pd.isna(title): return ""
    t = str(title).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def main():
    all_norm = []
    for file in INPUT_FILES:
        path = Path(file)
        if not path.exists():
            print(f"Warnung: Datei nicht gefunden: {file}")
            continue
        if path.suffix.lower() == ".ris":
            df = load_ris(path)
        elif path.suffix.lower() in {".bib", ".bibtex"}:
            df = load_bibtex(path)
        else:
            print(f"Warnung: unbekanntes Format: {file}")
            continue
        all_norm.append(normalize_df(df, source=path.stem))
    if not all_norm:
        raise RuntimeError("Keine gültigen Dateien geladen.")
    df_all = pd.concat(all_norm, ignore_index=True)
    df_all["doi_norm"] = df_all["doi"].apply(normalize_doi)
    df_all["title_norm"] = df_all["title"].apply(normalize_title)
    df_all["has_doi"] = df_all["doi_norm"] != ""
    # Sortierung: nach Titel, dann DOI, dann PubMed-Quelle falls gewünscht
    df_sorted = df_all.sort_values(by=["title_norm", "has_doi"], ascending=[True, False])
    df_final = df_sorted.drop_duplicates(subset=["title_norm"], keep="first").copy()
    # Zusatzspalten für das Screening
    df_final["include_title_abstract"] = ""
    df_final["include_fulltext"] = ""
    for n in range(1, 5):
        df_final[f"{n}th_exclusion_reason"] = ""
    df_final["notes"] = ""
    # Hilfsspalten entfernen
    df_final = df_final.drop(columns=["has_doi", "doi_norm", "title_norm"], errors="ignore")
    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(out_path, index=False)
    print(f"Tabelle gespeichert unter: {out_path}")
    print(f"Original: {len(df_all)}, nach Duplikatentfernung: {len(df_final)}")

if __name__ == "__main__":
    main()^
