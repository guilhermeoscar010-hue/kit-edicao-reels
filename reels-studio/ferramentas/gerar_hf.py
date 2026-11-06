"""Gera o index.html (HyperFrames) de um projeto a partir de edicao.json + estilo.json.

Uso: python gerar_hf.py <pasta-do-projeto>
- <projeto>/edicao.json: {"duracao", "paginas": [{inicio, fim, palavras: [{t, d}]}],
                         "efeitos": [{tipo: punch|afasta, inicio, fim, sfx, zoom}],
                         "cortesZoom": [{inicio, zoom}]}
- estilo.json (pasta reels-studio): fonte, cores, sombra, posicao da legenda, volumes de SFX.
Video em <projeto>/assets/video.mp4 (1080x1920 H.264 CFR); SFX em <projeto>/assets/sfx/<nome>.wav.
"""
import html
import json
import sys
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
proj = Path(sys.argv[1]).resolve()
ed = json.loads((proj / "edicao.json").read_text(encoding="utf-8"))
est = json.loads((RAIZ / "estilo.json").read_text(encoding="utf-8"))
leg = est["legenda"]
DUR = round(ed["duracao"], 3)


def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# tamanho unico: o da pagina mais longa cabendo em uma linha
maior = max(len(" ".join(w["t"] for w in p["palavras"])) for p in ed["paginas"])
tam = min(leg["tamanho_max"], int(leg["largura_max"] / (maior * leg["largura_por_char"])))

grupos, js = [], []
for i, p in enumerate(ed["paginas"]):
    ini = max(p["inicio"], 0.1) if i == 0 else p["inicio"]  # legenda em 0 s parece pre-existente
    dur = p["fim"] - ini
    if dur <= 0.04:
        continue
    spans = "".join(
        f'<span class="w{" d" if w["d"] else ""}">{html.escape(w["t"])}</span>' for w in p["palavras"]
    )
    grupos.append(
        f'<div id="g{i}" class="clip grupo" data-start="{f(ini)}" data-duration="{f(dur)}" data-track-index="2">'
        f'<div class="linha">{spans}</div></div>'
    )
    js.append(f'tl.fromTo("#g{i} .linha",{{opacity:0,y:18,scale:0.86}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"back.out(2)"}},{f(ini)});')
    if any(w["d"] for w in p["palavras"]):
        js.append(f'tl.fromTo("#g{i} .d",{{scale:0.7}},{{scale:1,duration:0.26,ease:"back.out(2.4)",stagger:0.05}},{f(ini + 0.04)});')

# camera: #corte recebe os cortes de zoom; #punch recebe punch-in / zoom-out / tremida
for c in ed["cortesZoom"]:
    js.append(f'tl.set("#corte",{{scale:{c["zoom"]}}},{f(c["inicio"])});')
sfx, n = [], 0
for e in ed["efeitos"]:
    de, ate, z = e["inicio"], e["fim"], e["zoom"]
    if e["tipo"] == "punch":
        js.append(f'tl.fromTo("#punch",{{scale:1}},{{scale:{1 + z},duration:0.22,ease:"back.out(2)",immediateRender:false,overwrite:"auto"}},{f(de)});')
        js.append(f'tl.to("#punch",{{scale:1,duration:0.33,ease:"power2.inOut",overwrite:"auto"}},{f(max(ate, de + 0.3))});')
        js.append(f'tl.to("#punch",{{keyframes:{{x:[9,-7,5,-3,0],y:[-5,4,-3,2,0]}},duration:0.27,ease:"none"}},{f(de)});')
        js.append(f'tl.fromTo("#flash",{{opacity:{est["flash"]["opacidade"]}}},{{opacity:0,duration:0.2,ease:"power1.out",immediateRender:false}},{f(de)});')
    else:  # afasta = zoom out: entra perto e abre ate o enquadramento normal
        js.append(f'tl.fromTo("#punch",{{scale:{1 + z}}},{{scale:1,duration:{f(ate - de + 0.33)},ease:"power3.out",immediateRender:false,overwrite:"auto"}},{f(de)});')
    if e.get("sfx"):
        n += 1
        arq = proj / "assets" / "sfx" / f'{e["sfx"]}.wav'
        vol = est["sfx_volume"].get(e["sfx"], 0.35)
        with wave.open(str(arq)) as w:  # slot = duracao real do arquivo
            dur_sfx = w.getnframes() / w.getframerate()
        sfx.append(
            f'<audio id="sfx{n}" class="clip" src="assets/sfx/{e["sfx"]}.wav" data-start="{f(max(0, de - 0.05))}" '
            f'data-duration="{f(min(dur_sfx, DUR - de))}" data-volume="{vol}" data-track-index="{3 + n % 2}"></audio>'
        )
        if not arq.exists():
            print("AVISO: falta", arq)

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
      .grupo {{ position: absolute; left: 0; right: 0; top: {leg["y_centro"] - tam // 2}px; text-align: center; overflow: visible; }}
      .linha {{ display: inline-flex; gap: {round(tam * 0.3)}px; filter: {sombra};
        font-family: "{leg["fonte"]}", sans-serif; font-weight: {leg["peso"]}; font-size: {tam}px;
        line-height: 1.1; letter-spacing: {leg["espacamento"]}px; white-space: nowrap; color: {leg["cor"]};
        text-transform: {"lowercase" if leg["minusculo"] else "none"}; }}
      .w {{ display: inline-block; transform-origin: 50% 60%; }}
      .d {{ background-image: {leg["destaque_gradiente"]}; -webkit-background-clip: text; background-clip: text; color: transparent; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{f(DUR)}" data-width="1080" data-height="1920">
      <div id="corte"><div id="punch">
        <video id="a-roll" class="clip" src="assets/video.mp4" playsinline data-has-audio="true" data-start="0"
          data-duration="{f(DUR)}" data-track-index="0" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>
      </div></div>
      <div id="flash"></div>
      {chr(10).join("      " + g for g in grupos).strip()}
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
print(f"index.html: {len(grupos)} legendas, {len(ed['efeitos'])} efeitos, {n} sfx, fonte {tam}px")
