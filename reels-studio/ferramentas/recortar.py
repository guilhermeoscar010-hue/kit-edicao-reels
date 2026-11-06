"""Gera o alfa da pessoa (RVM MobileNetV3) SO nas janelas em que ha texto/imagem ATRAS dela.

O recorte e o passo mais caro por segundo de video (~4 fps em CPU, ~7x o tempo real) e o `hyperframes remove-background`
levava mais de 30 min para 4 s: por isso so as janelas de "atras" sao recortadas, nunca o video inteiro.

Uso: python recortar.py <pasta-do-projeto>     (rodar com o Python do Whisper: tem onnxruntime)
Le edicao.json (atras[].texto/inicio/fim e imagens[modo=atras]) e grava assets/matte-<j>.mkv (cinza, 0,4x) e
edicao.json -> "recortes": [{inicio, fim, arq}] que o gerar_ff.py usa. Janelas que nao mudaram sao reaproveitadas.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
proj = Path(sys.argv[1]).resolve()
FPS, ESCALA, DS = 30, 0.4, 0.25
MODELO = RAIZ / "modelos" / "rvm_mobilenetv3_fp32.onnx"

ed = json.loads((proj / "edicao.json").read_text(encoding="utf-8"))
dur = ed["duracao"]
jan = [(a["inicio"], a["fim"]) for a in ed.get("atras", []) if a.get("texto")]
jan += [(m["inicio"], m["fim"]) for m in ed.get("imagens", []) if m["modo"] == "atras"]
jan = sorted((max(0, i - 0.05), min(dur, f + 0.02)) for i, f in jan)

fund = []  # une janelas que se encostam
for i, f in jan:
    if fund and i <= fund[-1][1] + 0.1:
        fund[-1][1] = max(fund[-1][1], f)
    else:
        fund.append([i, f])

antigos = {(round(r["inicio"], 3), round(r["fim"], 3)): r["arq"] for r in ed.get("recortes", [])}
novos, t0, quadros = [], time.time(), 0
for j, (i, f) in enumerate(fund):
    q0 = round(i * FPS)
    n = max(1, round((f - i) * FPS))
    ini, fim = q0 / FPS, (q0 + n) / FPS
    arq = f"assets/matte-{j}.mkv"
    if antigos.get((round(ini, 3), round(fim, 3))) == arq and (proj / arq).exists():
        novos.append({"inicio": ini, "fim": fim, "arq": arq})
        continue
    r = subprocess.run([sys.executable, "-I", str(RAIZ / "ferramentas" / "matte_rvm.py"), str(proj / "assets" / "video.mp4"),
                        str(proj / arq), str(MODELO), str(DS), str(q0), str(n), str(ESCALA)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"falha no recorte {j}: {r.stderr[-400:]}")
    quadros += n
    novos.append({"inicio": ini, "fim": fim, "arq": arq})
ed["recortes"] = novos
(proj / "edicao.json").write_text(json.dumps(ed, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(novos)} janelas de recorte ({quadros} quadros novos) em {time.time() - t0:.0f}s")
