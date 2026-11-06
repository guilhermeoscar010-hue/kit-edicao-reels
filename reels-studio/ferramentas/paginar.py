"""Passo 2: transcricao -> edicao.json (rascunho automatico que o Claude so revisa).

  python ferramentas/paginar.py projetos/<nome>

Regras (estilo.json + ESTILO.md):
- pagina de legenda com no maximo N palavras (legenda.max_palavras), minusculo, sem pontuacao final;
- quebra em ponto/virgula/interrogacao, em pausa >= 0,25 s ou no limite de palavras;
- pagina com menos de 0,4 s na tela junta com a vizinha se couber no limite;
- correcoes do glossario ("errado => certo") aplicadas antes;
- destaque automatico: termos do glossario e numeros;
- efeitos sugeridos: punch nos termos-chave do glossario (no maximo 1 a cada 3 s), zoom-out em numeros/datas;
- corte de zoom (1.0 / 1.08 alternado) no inicio de cada frase.
Escreve projetos/<nome>/edicao.json e work/legenda.txt (leitura rapida: *palavra* = destaque).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
proj = Path(sys.argv[1]).resolve()
est = json.loads((RAIZ / "estilo.json").read_text(encoding="utf-8"))
MAX = est["legenda"]["max_palavras"]
pal = json.loads((proj / "work" / "palavras.json").read_text(encoding="utf-8"))
dur = json.loads((proj / "work" / "info.json").read_text(encoding="utf-8"))["duracao"]


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in s if not unicodedata.combining(c))).strip()


gl = (RAIZ / "glossario.txt").read_text(encoding="utf-8").splitlines()
linhas = [l.strip() for l in gl if l.strip() and not l.startswith("#") and "=>" not in l]
termos = sorted({norm(l) for l in linhas if not l.startswith("~")}, key=lambda t: -len(t.split()))  # ~ = so contexto
impacto = {norm(l) for l in linhas if l.startswith("!")}  # ! = punch + ding
correcoes = [(norm(a), b.strip()) for a, b in (l.split("=>") for l in gl if "=>" in l and not l.startswith("#"))]

# 1. tokens com texto limpo + correcoes do glossario (podem trocar varias palavras por outras)
toks = [{"t": w["text"], "s": w["start"], "e": w["end"], "n": norm(w["text"])} for w in pal]
for errado, certo in correcoes:
    k = len(errado.split())
    i = 0
    while i + k <= len(toks):
        if " ".join(t["n"] for t in toks[i:i + k]) == errado:
            novos = certo.split()
            bloco = toks[i:i + k]
            pont = re.search(r"[.,?!]+$", bloco[-1]["t"])
            passo = (bloco[-1]["e"] - bloco[0]["s"]) / len(novos)
            toks[i:i + k] = [{"t": p + (pont.group() if pont and j == len(novos) - 1 else ""), "n": norm(p),
                              "s": bloco[0]["s"] + j * passo, "e": bloco[0]["s"] + (j + 1) * passo}
                             for j, p in enumerate(novos)]
        i += 1
INTERJ = {"o", "ah", "eh", "hum", "uhum", "ne"}
toks = [t for t, w in zip(toks, pal + [{"prob": 1}] * len(toks)) if t["n"] and not (t["n"] in INTERJ and w["prob"] < 0.2)]

# 2. destaques: termos do glossario (o mais longo primeiro) e numeros
dest = [False] * len(toks)
grupo = list(range(len(toks)))  # tokens do mesmo termo multi-palavra compartilham o indice do 1o
de_impacto = [False] * len(toks)
for termo in termos:
    k = len(termo.split())
    for i in range(len(toks) - k + 1):
        if not any(dest[i:i + k]) and " ".join(t["n"] for t in toks[i:i + k]) == termo:
            for j in range(i, i + k):
                dest[j], grupo[j], de_impacto[j] = True, i, termo in impacto
for i, t in enumerate(toks):
    if re.search(r"\d", t["t"]):
        dest[i] = True

# 3. paginas: frases (quebra forte em . ? ! e pausa >= 0,25 s) divididas no melhor ponto
FUNCAO = {"um", "uma", "o", "a", "os", "as", "no", "na", "nos", "nas", "de", "da", "do", "das", "dos", "em", "e",
          "que", "pra", "para", "por", "com", "se", "nessa", "nesse", "esse", "essa", "ao", "te", "me", "eu", "ele", "voce"}
frases, atual = [], []
for i, t in enumerate(toks):
    atual.append(i)
    forte = bool(re.search(r"[.?!]$", t["t"])) or (i + 1 < len(toks) and toks[i + 1]["s"] - t["e"] >= 0.25)
    if forte or i == len(toks) - 1:
        frases.append(atual)
        atual = []


def custo_bloco(b):
    c = 1.0
    if len(b) == 1:
        c += 0.6
    if toks[b[-1]]["n"] in FUNCAO and b[-1] != frase[-1]:
        c += 1.2  # nao terminar pagina em artigo/preposicao
    if b[-1] != frase[-1] and grupo[b[-1] + 1] == grupo[b[-1]]:
        c += 6  # nao partir termo do glossario
    if re.search(r",$", toks[b[-1]]["t"]):
        c -= 0.4  # virgula e um bom lugar pra quebrar
    if toks[b[-1]]["e"] - toks[b[0]]["s"] < 0.4:
        c += 0.8  # pagina curta demais pra ler
    return c


paginas = []
for frase in frases:
    n = len(frase)
    melhor = [0.0] + [1e9] * n
    corte = [0] * (n + 1)
    for j in range(1, n + 1):
        for k in range(max(0, j - MAX), j):
            v = melhor[k] + custo_bloco(frase[k:j])
            if v < melhor[j]:
                melhor[j], corte[j] = v, k
    blocos, j = [], n
    while j > 0:
        blocos.insert(0, frase[corte[j]:j])
        j = corte[j]
    paginas += blocos


def limpa(t):
    return re.sub(r"[.,?!]+$", "", t["t"]).lower() if not re.fullmatch(r"\d+,", t["t"]) else t["t"]


saida = []
for k, p in enumerate(paginas):
    ini = toks[p[0]]["s"] - 0.05 if k else 0.1
    fim = toks[paginas[k + 1][0]]["s"] - 0.05 if k + 1 < len(paginas) else dur
    if fim - toks[p[-1]]["e"] > 0.6:  # pausa longa: legenda sai antes
        fim = toks[p[-1]]["e"] + 0.35
    saida.append({"inicio": round(max(ini, 0), 3), "fim": round(fim, 3),
                  "palavras": [{"t": limpa(toks[i]), "d": dest[i]} for i in p]})

# 4. efeitos sugeridos e cortes de zoom
candidatos = []
for p in paginas:
    ids = [i for i in p if dest[i]]
    if not ids:
        continue
    numero = any(re.search(r"\d", toks[i]["t"]) for i in ids)
    forte = any(de_impacto[i] for i in ids)
    candidatos.append((3 if forte else 2 if numero else 1, toks[ids[0]]["s"], toks[ids[-1]]["e"], numero, forte))
escolhidos = []  # prioridade: impacto > numero > termo; no minimo 3 s entre efeitos
for c in sorted(candidatos, key=lambda c: (-c[0], c[1])):
    if all(abs(c[1] - e[1]) >= 3 for e in escolhidos):
        escolhidos.append(c)
efeitos = []
for _, de, ate, numero, forte in sorted(escolhidos, key=lambda c: c[1]):
    if numero:
        tipo, som, z = "afasta", "whoosh", 0.12
    elif forte:
        tipo, som, z = "punch", "ding", 0.14
    else:
        tipo, som, z = "punch", ["whip", "whoosh"][len(efeitos) % 2], 0.1  # alterna pra nao soar template
    efeitos.append({"tipo": tipo, "inicio": round(de, 3), "fim": round(ate, 3), "sfx": som, "zoom": z})
cortes, z = [{"inicio": 0.0, "zoom": 1.0}], 1.0
for i in range(1, len(toks)):
    if re.search(r"[.?!]$", toks[i - 1]["t"]) and toks[i]["s"] - cortes[-1]["inicio"] > 3:
        z = 1.08 if z == 1.0 else 1.0
        cortes.append({"inicio": round(toks[i]["s"], 3), "zoom": z})

ed = {"duracao": dur, "paginas": saida, "efeitos": efeitos, "cortesZoom": cortes}
(proj / "edicao.json").write_text(json.dumps(ed, ensure_ascii=False, indent=1), encoding="utf-8")
with open(proj / "work" / "legenda.txt", "w", encoding="utf-8") as f:
    for k, p in enumerate(saida):
        f.write(f"{k:3d} {p['inicio']:6.2f}-{p['fim']:6.2f}  " + " ".join(f"*{w['t']}*" if w["d"] else w["t"] for w in p["palavras"]) + "\n")
    f.write("\nEFEITOS\n" + "\n".join(f"{e['inicio']:6.2f} {e['tipo']:6s} {e['sfx']}" for e in efeitos))
print(f"edicao.json: {len(saida)} paginas, {sum(dest)} palavras em destaque, {len(efeitos)} efeitos, {len(cortes)} cortes de zoom")
