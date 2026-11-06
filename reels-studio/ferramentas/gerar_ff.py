"""Compoe o video final so com ffmpeg (sem abrir o Chrome quadro a quadro: o render do HyperFrames levava ~0,6 s/quadro,
~36 min para 2 min de video). Usa edicao.json + estilo-ref.json + PNGs de gerar_assets.cjs + alfa de recortar.py.

Uso: python gerar_ff.py <pasta-do-projeto> [--saida arq.mp4] [--ate 12] [--qsv] [--bloco 6] [--paralelo 1] [--pular camadas]
  --ate N     so os primeiros N segundos (previa rapida)
  --qsv       encode pelo Quick Sync (~1,6x mais rapido que x264 veryfast neste notebook)
  --bloco S   tamanho alvo dos blocos (padrao 4 s). Com TODAS as entradas abertas de uma vez (70 PNGs + 4 recortes) o ffmpeg foi a
              28x o tempo real (RAM esgotada); em blocos com so as entradas do trecho fica em ~3-5x. Cortes so fora de recortes/efeitos.
  --pular     lista (atras,recorte,zoom,flash,cards,legendas) para isolar camadas
Camadas (baixo -> cima): video -> textos/imagens ATRAS -> recorte da pessoa -> cor -> zoom/punch/tremida -> flash -> cards -> legendas.
Os blocos so sao cortados onde nenhuma imagem/recorte/efeito esta em andamento. Audio (fala + SFX + loudnorm -14 LUFS) e feito
a parte e juntado sem recodificar o video.
"""
import json
import subprocess
import sys
import time
import wave  # noqa: F401  (reservado: duracao real de SFX)
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
args = sys.argv[1:]
proj = Path(args[0]).resolve()
opt = lambda nome, padrao=None: args[args.index(nome) + 1] if nome in args else padrao  # noqa: E731
saida = Path(opt("--saida", proj / "renders" / f"{proj.name}-ff.mp4"))
ate = float(opt("--ate")) if "--ate" in args else None
qsv = "--qsv" in args
bloco = float(opt("--bloco", 4))
paralelo = int(opt("--paralelo", 1))
pular = set(opt("--pular", "").split(",")) - {""}
saida.parent.mkdir(parents=True, exist_ok=True)
(proj / "work" / "blocos").mkdir(parents=True, exist_ok=True)

ed = json.loads((proj / "edicao.json").read_text(encoding="utf-8"))
est = json.loads((RAIZ / "estilo-ref.json").read_text(encoding="utf-8"))
man = {m["key"]: m for m in json.loads((proj / "work" / "png" / "manifest.json").read_text(encoding="utf-8"))}
DUR = ed["duracao"] if ate is None else min(ate, ed["duracao"])
FPS = 30
quad = lambda t: round(t * FPS) / FPS  # noqa: E731


def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".") or "0"


recortes_all = [r for r in ed.get("recortes", []) if r["inicio"] < DUR and (proj / r["arq"]).exists()] if "recorte" not in pular else []
efeitos = ed["efeitos"]
enc = (["-c:v", "h264_qsv", "-global_quality", "20", "-look_ahead", "0", "-bf", "0", "-g", "15"] if qsv
       else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-bf", "0", "-g", "15"])


def montar(idx, c0, c1):
    """Um bloco [c0, c1): so as entradas desse trecho; todos os tempos viram relativos a c0."""
    D = c1 - c0
    inp = ["-ss", f(c0), "-i", str(proj / "assets" / "video.mp4")]
    graf, n_in = [], [1]

    def entrada(argv):
        inp.extend(argv)
        n_in[0] += 1
        return n_in[0] - 1

    def estatico(key, ini, fim, fade_in, fade_out=0.18):
        m = man[key]
        ini_r, fim_r = max(ini, c0) - c0, min(fim, c1) - c0
        cortado = ini < c0
        d = fim_r - ini_r
        fim_real = fim <= c1 + 1e-6
        # se o bloco corta antes do fim, o PNG ganha folga: terminar exatamente no fim do bloco perde os 2 ultimos quadros (EOF antes do video)
        k = entrada(["-loop", "1", "-framerate", str(FPS), "-t", f(d if fim_real else d + 0.5), "-i", m["file"]])
        # fade-in so se o elemento nasce neste bloco; fade-out so no fim REAL (no corte, o bloco seguinte continua opaco)
        fi = "" if cortado else f",fade=t=in:st=0:d={f(fade_in)}:alpha=1"
        fo = f",fade=t=out:st={f(max(d - fade_out, 0))}:d={f(fade_out)}:alpha=1" if fim_real else ""
        graf.append(f"[{k}:v]format=rgba{fi}{fo},setpts=PTS-STARTPTS+{f(ini_r)}/TB[s{k}]")
        return f"s{k}", m["x"], m["y"], ini_r, fim_r, cortado

    def sobrepor(base, key, ini, fim, desliza=28, fade_in=0.28):
        rot, x, y, ini_r, fim_r, cortado = estatico(key, ini, fim, fade_in)
        nome = f"o{n_in[0]}"
        dz = 0 if cortado else desliza
        graf.append(f"[{base}][{rot}]overlay=x={x}:y='{y}+{dz}*max(0,1-(t-{f(ini_r)})/0.3)':format=auto:eof_action=pass:"
                    f"enable='between(t,{f(ini_r)},{f(fim_r)})'[{nome}]")
        return nome

    rec = [r for r in recortes_all if r["inicio"] < c1 and r["fim"] > c0 and r["inicio"] >= c0 - 1e-6 and r["fim"] <= c1 + 1e-6]
    graf.append(f"[0:v]format=yuv420p,split={len(rec) + 1}[base]" + "".join(f"[pc{j}]" for j in range(len(rec)))
                if rec else "[0:v]format=yuv420p[base]")
    atual = "base"

    # 1) ATRAS (antes do recorte, pra cabeca ficar na frente)
    itens = [(a["inicio"], a["fim"], f"atras{i}") for i, a in enumerate(ed.get("atras", [])) if a.get("texto")]
    itens += [(m["inicio"], m["fim"], f"img{i}") for i, m in enumerate(ed.get("imagens", [])) if m["modo"] == "atras"]
    for ini, fim, key in sorted(itens):
        if ini < c1 and fim > c0 and "atras" not in pular:
            atual = sobrepor(atual, key, ini, fim)

    # 2) recorte da pessoa: pedaco do proprio video + alfa (cinza) do RVM
    for j, r in enumerate(rec):
        k = entrada(["-i", str(proj / r["arq"])])
        q0, q1 = quad(r["inicio"]) - c0, min(r["fim"], c1) - c0
        graf.append(f"[pc{j}]trim=start={f(q0)}:end={f(q1)},setpts=PTS-STARTPTS[pv{j}]")
        graf.append(f"[{k}:v]scale=1080:1920:flags=bicubic,format=gray,setpts=PTS-STARTPTS[mg{j}]")
        graf.append(f"[pv{j}][mg{j}]alphamerge,setpts=PTS-STARTPTS+{f(q0)}/TB[pm{j}]")
        nome = f"o{n_in[0]}"
        graf.append(f"[{atual}][pm{j}]overlay=format=auto:eof_action=pass:enable='between(t,{f(q0)},{f(q1)})'[{nome}]")
        atual = nome

    # 3) cor viva
    graf.append(f"[{atual}]{est.get('eq', 'eq=saturation=1.28:contrast=1.08:brightness=0.02')}[cor]")
    atual = "cor"

    # 4) camera: corte de zoom (degraus) x punch/afasta (envelopes) + tremida
    corte = "1"
    for c in sorted(ed.get("cortesZoom", []), key=lambda c: c["inicio"]):
        if c["inicio"] < c1:
            corte = f"if(gte(t,{f(c['inicio'] - c0)}),{c['zoom']},{corte})"
    env, shx, shy, flashes = [], [], [], []
    for e in efeitos:
        de, ate_e, z = e["inicio"] - c0, e["fim"] - c0, e.get("zoom", 0)
        if e["inicio"] >= c1 or e["fim"] + 0.8 < c0:
            continue
        if e["tipo"] == "punch":
            he = max(ate_e, de + 0.3)
            env.append(f"{z}*(between(t,{f(de)},{f(de + 0.2)})*sin((t-{f(de)})/0.2*1.5708)+between(t,{f(de + 0.2)},{f(he)})+"
                       f"between(t,{f(he)},{f(he + 0.35)})*cos((t-{f(he)})/0.35*1.5708))")
            shx.append(f"between(t,{f(de)},{f(de + 0.25)})*8*sin((t-{f(de)})*90)*(1-(t-{f(de)})/0.25)")
            shy.append(f"between(t,{f(de)},{f(de + 0.25)})*5*cos((t-{f(de)})*90)*(1-(t-{f(de)})/0.25)")
            flashes.append(de)
        elif e["tipo"] == "afasta":
            d = ate_e - de + 0.33
            env.append(f"{z}*between(t,{f(de)},{f(de + d)})*pow(max(0,1-(t-{f(de)})/{f(d)}),3)")
    Z = f"({corte})*(1+{'+'.join(env) if env else '0'})"
    SX, SY = ("+".join(shx) if shx else "0"), ("+".join(shy) if shy else "0")
    if "zoom" in pular:
        graf.append(f"[{atual}]null[zoom]")
    else:
        graf.append(f"[{atual}]scale=w='trunc(1080*{Z}/2)*2':h='trunc(1920*{Z}/2)*2':eval=frame:flags=bilinear,"
                    f"crop=1080:1920:x='(in_w-1080)*0.5+{SX}':y='(in_h-1920)*0.3+{SY}':exact=1[zoom]")
    atual = "zoom"

    # 5) flash do punch
    if flashes and "flash" not in pular:
        cor = est["flash"]["cor"].lstrip("#")
        cad = ",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=0x{cor}@{est['flash']['opacidade']}:t=fill:enable='between(t,{f(de)},{f(de + 0.07)})'"
                       for de in flashes)
        graf.append(f"[{atual}]{cad}[fl]")
        atual = "fl"

    # 6) cards e legendas por cima de tudo
    if "cards" not in pular:
        for i, m in enumerate(ed.get("imagens", [])):
            if m["modo"] != "atras" and m["inicio"] < c1 and m["fim"] > c0:
                atual = sobrepor(atual, f"img{i}", m["inicio"], m["fim"], desliza=-22)
    if "legendas" not in pular:
        for i, p in enumerate(ed["paginas"]):
            ini = max(p["inicio"], 0.1) if i == 0 else p["inicio"]
            if ini < c1 and p["fim"] > c0 and p["fim"] - ini > 0.04:
                atual = sobrepor(atual, f"cap{i}", ini, p["fim"], desliza=14, fade_in=0.12)
    graf.append(f"[{atual}]format=yuv420p[vout]")

    script = proj / "work" / "blocos" / f"graf{idx}.txt"
    script.write_text(";\n".join(graf), encoding="utf-8")
    out = proj / "work" / "blocos" / f"b{idx}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex_script", str(script), "-map", "[vout]", "-an", "-t", f(D),
           "-r", str(FPS), *enc, "-pix_fmt", "yuv420p", str(out)]
    t0 = time.time()
    r = subprocess.run(cmd)
    return idx, r.returncode, out, n_in[0], time.time() - t0


def zonas_proibidas():
    """Trechos em que NAO se pode cortar o bloco: imagem/recorte/efeito em andamento."""
    # PNGs parados (cards, textos, imagens) podem ser cortados no meio: o bloco seguinte os recomeca sem fade (estatico() trata)
    z = [(r["inicio"], r["fim"]) for r in ed.get("recortes", [])]
    for e in efeitos:
        if e["tipo"] == "punch":
            z.append((e["inicio"], max(e["fim"], e["inicio"] + 0.3) + 0.4))
        elif e["tipo"] == "afasta":
            z.append((e["inicio"], e["fim"] + 0.4))
    return z


def planejar():
    proib = zonas_proibidas()
    livre = lambda t: not any(a - 1e-6 < t < b + 1e-6 for a, b in proib)  # noqa: E731
    cand = sorted({quad(p["inicio"]) for p in ed["paginas"]})
    cortes, c0 = [], 0.0
    while c0 < DUR - 0.5:
        prox = [t for t in cand if t >= c0 + bloco and t < DUR - 0.5 and livre(t)]
        c1 = prox[0] if prox else DUR
        cortes.append((c0, c1))
        c0 = c1
    return cortes or [(0.0, DUR)]


blocos = planejar()
t0 = time.time()
with ThreadPoolExecutor(max_workers=max(1, paralelo)) as ex:
    res = sorted(ex.map(lambda a: montar(a[0], *a[1]), enumerate(blocos)))
for idx, rc, out, n, dt in res:
    c0, c1 = blocos[idx]
    print(f"  bloco {idx} [{c0:.1f}-{c1:.1f}s] {n} entradas: {dt:.0f}s ({dt / (c1 - c0):.1f}x)", flush=True)
if any(rc for _, rc, *_ in res):
    sys.exit("FALHOU em algum bloco")

# audio: fala + SFX + loudnorm, uma passada so (sem video: rapido)
inp_a = ["-i", str(proj / "assets" / "video.mp4")]
mix, rot = ["[0:a]anull[a0]"], ["[a0]"]
sfx = [e for e in efeitos if e.get("sfx") and e["inicio"] < DUR]
for j, e in enumerate(sfx, 1):
    inp_a += ["-i", str(proj / "assets" / "sfx" / f"{e['sfx']}.wav")]
    ms = int(max(0, e["inicio"] - 0.05) * 1000)
    mix.append(f"[{j}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},volume={est['sfx_volume'].get(e['sfx'], 0.35)}[a{j}]")
    rot.append(f"[a{j}]")
mix.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=first,loudnorm=I=-14:TP=-1:LRA=11[aout]")
audio = proj / "work" / "blocos" / "audio.m4a"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", *inp_a, "-filter_complex", ";".join(mix), "-map", "[aout]", "-t", f(DUR),
                    "-c:a", "aac", "-b:a", "256k", str(audio)])
if r.returncode:
    sys.exit("FALHOU no audio")

lista = proj / "work" / "blocos" / "lista.txt"
lista.write_text("".join(f"file '{out.as_posix()}'\n" for _, _, out, *_ in res), encoding="utf-8")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(audio),
                    "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart", str(saida)])
tot = time.time() - t0
print(f"{'OK' if r.returncode == 0 else 'FALHOU'} {saida.name}: {DUR:.1f}s de video em {tot:.0f}s ({tot / DUR:.2f}x), {len(blocos)} blocos")
sys.exit(r.returncode)
