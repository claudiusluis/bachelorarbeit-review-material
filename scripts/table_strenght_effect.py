import pandas as pd
from pathlib import Path
import re

INPUT_FILE = "KraftEffekteReihenfolge.csv" # Name der Datei
OUTPUT_TEX = "KraftEffekteReihenfolge_table.tex" # Name der Datei
CAPTION = "Kraft-Effekte der Trainingsreihenfolge"
LABEL = "tab:kraft_effekte_reihenfolge"
ARRAYSTRETCH = 1.5

def latex_escape(s):
    if s is None:
        return ""
    s = str(s).strip()

    # 1) Gewünschte Math-Ausdrücke direkt einsetzen
    s = s.replace("L0", "$L_0$")
    s = s.replace("LO", "$L_0$")
    s = s.replace("≈", r"$\approx$")

    # 2) Normale LaTeX-Sonderzeichen escapen
    #    WICHTIG: $ und _ und \ NICHT escapen, damit Math-Formeln intakt bleiben
    for k, v in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        s = s.replace(k, v)

    # 3) Zeilenumbrüche innerhalb einer Zelle
    s = s.replace("\n", r"\\ ")

    return s

def main():
    path = Path(INPUT_FILE)
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc, dtype=str).fillna("")
            if df.shape[1] >= 3:
                break
        except Exception: pass
    else:
        raise RuntimeError("Konnte CSV nicht lesen.")
    
    df = df.iloc[:, :3]
    headers = [
        r"Studie", 
        r"Kraftparameter", 
        r"Hauptergebnisse"
    ]

    # Kopfzeile kleiner drucken
    head = " & ".join([r"\footnotesize\textbf{" + h + "}" for h in headers]) + r" \\"
    body = "\n".join(" & ".join(latex_escape(cell) for cell in row) + r" \\"
                     for row in df.values)

    latex = fr"""\renewcommand{{\arraystretch}}{{{ARRAYSTRETCH}}}
\setlength{{\tabcolsep}}{{4pt}}
\small

\begin{{xltabular}}{{\textwidth}}{{@{{}}>{{\RaggedRight\arraybackslash}}p{{2.8cm}} >{{\RaggedRight\arraybackslash}}p{{3.5cm}} >{{\RaggedRight\arraybackslash}}X@{{}}}}
\caption{{{CAPTION}}}
\label{{{LABEL}}} \\

\toprule
{head}
\midrule
\endfirsthead

\toprule
{head}
\midrule
\endhead

\midrule
\multicolumn{{3}}{{r}}{{\textit{{Fortsetzung auf der nächsten Seite}}}} \\
\midrule
\endfoot

\bottomrule
\endlastfoot

{body}

\bottomrule
\end{{xltabular}}
"""

    Path(OUTPUT_TEX).write_text(latex, encoding="utf-8")

if __name__ == "__main__":
    main()
