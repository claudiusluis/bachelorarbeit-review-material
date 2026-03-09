#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import csv
from pathlib import Path
import pandas as pd

LATEX_SUBS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

def latex_escape(s):
    if s is None:
        return ""
    s = str(s).replace("\r\n","\n").replace("\r","\n").strip()
    s = s.replace("−", "-")
    s = "".join(LATEX_SUBS.get(ch, ch) for ch in s)
    s = s.replace("\n", r"\\ ")
    s = re.sub(r"\s{2,}", " ", s)
    return s

def sniff_delimiter(sample):
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except Exception:
        return ";"

def read_csv_robust(path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    sep = sniff_delimiter("\n".join(raw.splitlines()[:30]))
    df = pd.read_csv(path, sep=sep, engine="python", encoding="utf-8-sig")
    df = df.dropna(axis=1, how="all").fillna("").astype(str)
    df.columns = [c.strip() for c in df.columns]
    return df

def dataframe_to_exact_tex(df):
    # Spaltenbeschriftungen gemäß Vorlage
    headers = [
        r"\textbf{Autor (Jahr)}",
        r"\textbf{Studiendesign}",
        r"\textbf{Stichprobe (N)}",
        r"\textbf{Population}",
        r"\textbf{Trainingsstatus}",
        r"\textbf{Studiendauer}"
    ]
    N = 6  # number of columns
    lines = [
        r"\section{Studien- und Populationseigenschaften}",
        r"\begin{sidewaystable}",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.75}",
        "",
        r"\begin{xltabular}{\linewidth}{@{}>{\RaggedRight\arraybackslash}p{3.2cm}>{\RaggedRight\arraybackslash}p{3.8cm}>{\RaggedRight\arraybackslash}X>{\RaggedRight\arraybackslash}X>{\RaggedRight\arraybackslash}X>{\RaggedRight\arraybackslash}p{2.2cm}@{}}",
        r"\caption{Studien- und Populationseigenschaften}\label{tab:studien\_population}\\",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endhead",
        rf"\midrule \multicolumn{{{N}}}{{r}}{{\emph{{Fortsetzung auf der nächsten Seite}}}} \\",
        r"\midrule",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
    ]
    # Body
    for _, row in df.iterrows():
        cells = [latex_escape(row[c]) for c in df.columns[:N]]
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{xltabular}", r"\end{sidewaystable}", ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="----> Studien- und Populationseigenschaften Tabelle .tex GEN")
    parser.add_argument("csv_path", help="Path to CSV")
    parser.add_argument("-o", "--out", default="TabelleStudienUndPopulationseigenschaften.tex")
    args = parser.parse_args()
    df = read_csv_robust(Path(args.csv_path))
    tex = dataframe_to_exact_tex(df)
    Path(args.out).write_text(tex, encoding="utf-8")
    print(f"Wrote table snippet: {Path(args.out).resolve()}")

if __name__ == "__main__":
    main()