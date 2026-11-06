"""Gera o index.html (HyperFrames) no estilo das referencias (videoJB) a partir de edicao.json + estilo-ref.json.

Uso: python gerar_ref.py <pasta-do-projeto>
- edicao.json: {"duracao",
    "paginas": [{inicio, fim, palavras: [{t, d}]}]   d=true -> palavra vai pra 2a linha, amarela e maior,
    "atras": [{texto, inicio, fim, cor?}]             texto gigante ATRAS da pessoa (precisa assets/pessoa.webm),
    "topo": [{texto, destaque?, inicio, fim}]         titulo de gancho em italico no topo,
    "efeitos": [{tipo: punch|afasta, inicio, fim, sfx, zoom}],
    "cortesZoom": [{inicio, zoom}]}
Video em assets/video.mp4; recorte da pessoa em assets/pessoa.webm (hyperframes remove-background).
"""
import html
import json
import sys
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
proj = Path(sys.argv[1]).resolve()
ed = json.loads((proj / "edicao.json").read_text(encoding="utf-8"))
est = json.loads((RAIZ / "estilo-ref.json").read_text(encoding="utf-8"))
leg, atr = est["legenda"], est["atras"]
DUR = round(ed["duracao"], 3)


def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


el, js = [], []
for i, p in enumerate(ed["paginas"]):
    ini = max(p["inicio"], 0.1) if i == 0 else p["inicio"]
    dur = p["fim"] - ini
    if dur <= 0.04:
        continue
    l1 = " ".join(html.escape(w["t"]) for w in p["palavras"] if not w["d"])
    l2 = " ".join(html.escape(w["t"]) for w in p["palavras"] if w["d"])
    linhas = (f'<div class="l1">{l1}</div>' if l1 else "") + (f'<div class="l2">{l2}</div>' if l2 else "")
    el.append(f'<div id="g{i}" class="clip grupo" data-start="{f(ini)}" data-duration="{f(dur)}" data-track-index="6">{linhas}</div>')
    js.append(f'tl.fromTo("#g{i} .l1",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.16,ease:"power2.out"}},{f(ini)});')
    if l2:
        js.append(f'tl.fromTo("#g{i} .l2",{{opacity:0,scale:0.55}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2.6)"}},{f(ini + 0.05)});')

for i, a in enumerate(ed.get("atras", [])):
    if not a["texto"]:  # janela so de recorte (imagem atras da pessoa, sem texto)
        continue
    dur = a["fim"] - a["inicio"]
    tam = min(300, int(960 / (max(len(x) for x in a["texto"].split("|")) * 0.74)))
    txt = "<br>".join(html.escape(x) for x in a["texto"].split("|"))
    el.append(f'<div id="a{i}" class="clip atras" data-start="{f(a["inicio"])}" data-duration="{f(dur)}" data-track-index="2" '
              f'style="font-size:{tam}px;color:{a.get("cor", atr["cor"])}">{txt}</div>')
    js.append(f'tl.fromTo("#a{i}",{{opacity:0,scale:1.35,filter:"blur(14px)"}},{{opacity:1,scale:1,filter:"blur(0px)",duration:0.35,ease:"power3.out"}},{f(a["inicio"])});')
    js.append(f'tl.to("#a{i}",{{opacity:0,y:-30,duration:0.2,ease:"power1.in"}},{f(a["fim"] - 0.2)});')

# imagens PNG: "atras" = objeto grande atras da pessoa (dentro da camera, sob o recorte); "card" = moldura amarela
# tracejada acima da cabeca (estilo videoJB). {arq, inicio, fim, modo, x, y, w, h?, rot?, foto?, x_vermelho?}
for i, m in enumerate(ed.get("imagens", [])):
    dur = m["fim"] - m["inicio"]
    h = m.get("h", m["w"])
    estilo = f'left:{m["x"]}px;top:{m["y"]}px;width:{m["w"]}px;height:{h}px'
    risco = '<div class="xis"></div>' if m.get("x_vermelho") else ""
    if m["modo"] == "atras":
        el.append(f'<div id="m{i}" class="clip img-atras" data-start="{f(m["inicio"])}" data-duration="{f(dur)}" data-track-index="2" '
                  f'style="{estilo}"><img src="{m["arq"]}" alt=""></div>')
    else:
        el.append(f'<div id="m{i}" class="clip card" data-start="{f(m["inicio"])}" data-duration="{f(dur)}" data-track-index="{10 + i % 3}" '
                  f'style="{estilo}"><img src="{m["arq"]}" alt="" class="{"foto" if m.get("foto") else ""}">{risco}</div>')
    js.append(f'tl.fromTo("#m{i}",{{opacity:0,scale:0.5,rotation:{m.get("rot", 0) - 8}}},{{opacity:1,scale:1,rotation:{m.get("rot", 0)},duration:0.32,ease:"back.out(2.2)"}},{f(m["inicio"])});')
    js.append(f'tl.to("#m{i}",{{y:-18,duration:{f(max(dur - 0.5, 0.2))},ease:"sine.inOut"}},{f(m["inicio"] + 0.32)});')
    js.append(f'tl.to("#m{i}",{{opacity:0,scale:0.85,duration:0.18,ease:"power1.in"}},{f(m["fim"] - 0.18)});')

for i, t in enumerate(ed.get("topo", [])):
    dur = t["fim"] - t["inicio"]
    dest = f'<span class="td">{html.escape(t["destaque"])}</span>' if t.get("destaque") else ""
    el.append(f'<div id="t{i}" class="clip topo" data-start="{f(t["inicio"])}" data-duration="{f(dur)}" data-track-index="7">'
              f'{dest}<span class="tt">{html.escape(t["texto"])}</span></div>')
    js.append(f'tl.fromTo("#t{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{f(t["inicio"])});')
    js.append(f'tl.to("#t{i}",{{opacity:0,duration:0.2}},{f(t["fim"] - 0.2)});')

for c in ed["cortesZoom"]:
    js.append(f'tl.set("#corte",{{scale:{c["zoom"]}}},{f(c["inicio"])});')
sfx, n = [], 0
for e in ed["efeitos"]:
    de, ate, z = e["inicio"], e["fim"], e["zoom"]
    if e["tipo"] == "punch":
        js.append(f'tl.fromTo("#punch",{{scale:1}},{{scale:{1 + z},duration:0.2,ease:"back.out(2)",immediateRender:false,overwrite:"auto"}},{f(de)});')
        js.append(f'tl.to("#punch",{{scale:1,duration:0.35,ease:"power2.inOut",overwrite:"auto"}},{f(max(ate, de + 0.3))});')
        js.append(f'tl.to("#punch",{{keyframes:{{x:[8,-6,4,-2,0],y:[-4,3,-2,1,0]}},duration:0.25,ease:"none"}},{f(de)});')
        js.append(f'tl.fromTo("#flash",{{opacity:{est["flash"]["opacidade"]}}},{{opacity:0,duration:0.2,ease:"power1.out",immediateRender:false}},{f(de)});')
    elif e["tipo"] == "afasta":
        js.append(f'tl.fromTo("#punch",{{scale:{1 + z}}},{{scale:1,duration:{f(ate - de + 0.33)},ease:"power3.out",immediateRender:false,overwrite:"auto"}},{f(de)});')
    if e.get("sfx"):
        n += 1
        arq = proj / "assets" / "sfx" / f'{e["sfx"]}.wav'
        with wave.open(str(arq)) as w:
            dur_sfx = w.getnframes() / w.getframerate()
        sfx.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{e["sfx"]}.wav" data-start="{f(max(0, de - 0.05))}" '
                   f'data-duration="{f(min(dur_sfx, DUR - de))}" data-volume="{est["sfx_volume"].get(e["sfx"], 0.35)}" data-track-index="{8 + n % 2}"></audio>')

# recorte em trechos curtos (assets/pessoa-<i>.webm, so na janela de cada texto atras): o recorte inteiro
# em 1080p derruba a captura do Chrome em maquina com pouca memoria
trechos = [(i, a) for i, a in enumerate(ed.get("atras", [])) if "recorte_inicio" in a and (proj / "assets" / f"pessoa-{i}.webm").exists()]
tem_recorte = bool(trechos) or ((proj / "assets" / "pessoa.webm").exists() and ed.get("atras"))
if trechos:
    recorte = "\n        ".join(
        f'<video id="pessoa{i}" class="clip" src="assets/pessoa-{i}.webm" muted playsinline data-start="{f(a["recorte_inicio"])}" '
        f'data-duration="{f(a["recorte_dur"])}" data-track-index="{3 + i % 2}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>'
        for i, a in trechos)
else:
    recorte = (f'<video id="pessoa" class="clip" src="assets/pessoa.webm" muted playsinline data-start="0" data-duration="{f(DUR)}" '
               f'data-track-index="3" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>') if tem_recorte else ""
sombra = " ".join(f"drop-shadow({s})" for s in leg["sombra"])
doc = f"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #corte, #punch {{ position: absolute; inset: 0; }}
      #flash {{ position: absolute; inset: 0; background: {est["flash"]["cor"]}; opacity: 0; }}
      .grupo {{ position: absolute; left: 40px; right: 40px; top: {leg["y_topo"]}px; text-align: center; filter: {sombra};
        font-family: "{leg["fonte"]}", sans-serif; font-weight: {leg["peso"]}; color: {leg["cor"]}; line-height: 1.02; }}
      .l1 {{ font-size: {leg["tamanho"]}px; letter-spacing: -1px; }}
      .l2 {{ font-size: {leg["tamanho_destaque"]}px; color: {leg["destaque_cor"]}; text-transform: uppercase; letter-spacing: -2px; transform-origin: 50% 60%; }}
      .atras {{ position: absolute; left: 0; right: 0; top: {atr["y_topo"]}px; text-align: center; font-family: "{atr["fonte"]}", sans-serif;
        font-weight: {atr["peso"]}; line-height: 0.9; letter-spacing: -4px; text-transform: uppercase; }}
      .topo {{ position: absolute; left: 60px; right: 60px; top: {est["topo"]["y_topo"]}px; font-family: "{leg["fonte"]}", sans-serif;
        font-weight: 800; font-style: italic; text-transform: uppercase; filter: {sombra}; display: flex; align-items: center; gap: 18px; }}
      #corte {{ filter: {est.get("cor", "none")}; }}
      .img-atras {{ position: absolute; }}
      .img-atras img {{ width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 18px 30px rgba(0,0,0,0.45)); }}
      .card {{ position: absolute; border: 5px dashed {leg["destaque_cor"]}; border-radius: 22px; background: rgba(10,10,10,0.42);
        box-shadow: 0 0 18px rgba(245,217,10,0.35); padding: 14px; overflow: hidden; }}
      .card img {{ width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 8px 14px rgba(0,0,0,0.5)); }}
      .card img.foto {{ object-fit: cover; border-radius: 12px; }}
      .xis {{ position: absolute; left: 8%; right: 8%; top: 50%; height: 14px; background: #E5322D; border-radius: 7px; transform: rotate(-35deg);
        box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
      .td {{ font-size: 96px; color: {leg["destaque_cor"]}; }}
      .tt {{ font-size: 46px; color: #fff; line-height: 1.05; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{f(DUR)}" data-width="1080" data-height="1920">
      <div id="corte"><div id="punch">
        <video id="a-roll" class="clip" src="assets/video.mp4" playsinline data-has-audio="true" data-start="0"
          data-duration="{f(DUR)}" data-track-index="0" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>
        {chr(10).join("        " + x for x in el if 'class="clip atras"' in x or 'class="clip img-atras"' in x).strip()}
        {recorte}
      </div></div>
      <div id="flash"></div>
      {chr(10).join("      " + x for x in el if 'class="clip atras"' not in x and 'class="clip img-atras"' not in x).strip()}
      {chr(10).join("      " + s for s in sfx).strip()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      gsap.set(["#corte", "#punch"], {{ transformOrigin: "{est["camera"]["origem"]}" }});
      tl.set("#punch", {{ scale: 1, x: 0, y: 0 }}, 0);
      tl.set("#flash", {{ opacity: 0 }}, 0);
      {chr(10).join("      " + j for j in js).strip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
(proj / "index.html").write_text(doc, encoding="utf-8")
print(f"index.html: {len(ed['paginas'])} legendas, {len(ed.get('atras', []))} textos atras, {len(ed['efeitos'])} efeitos, {n} sfx, recorte={'sim' if tem_recorte else 'nao'}")
