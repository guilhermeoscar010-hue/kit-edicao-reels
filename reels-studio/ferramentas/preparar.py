"""Passo 1 de toda edicao: cria o projeto, converte o video e transcreve. Rodar com o Python do Whisper:

  %USERPROFILE%\\.venvs\\whisper\\Scripts\\python.exe ferramentas/preparar.py <video> [nome] [--modelo medium|small]

Gera em projetos/<nome>/:
  assets/video.mp4   1080x1920 H.264 30 fps CFR (o HyperFrames e o Chrome leem sem erro; HEVC do iPhone nao)
  assets/sfx/        copia da biblioteca de SFX
  work/palavras.json [{text, start, end, prob}] por palavra
  work/lista.txt     indice, tempos, probabilidade (<< = conferir) e palavra
  work/folha.jpg     folha de quadros (enquadramento, onde ficam os rostos)
  index.html/hyperframes.json/package.json do HyperFrames (via init)
"""
import json
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
HF = "hyperframes@0.8.189"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
modelo = "medium"
if "--modelo" in sys.argv:
    modelo = sys.argv[sys.argv.index("--modelo") + 1]
    args = [a for a in args if a != modelo]
video = Path(args[0]).resolve()
nome = args[1] if len(args) > 1 else video.stem.lower().replace(" ", "-")
proj = RAIZ / "projetos" / nome
(proj / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
(proj / "work").mkdir(exist_ok=True)
t0 = time.time()


def ffprobe_dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout
    return float(out.strip())


# 1. conversao do video e extracao do audio em paralelo
# iPhone grava em HDR (HLG/BT.2020): o HyperFrames entra no caminho "hdr_layered" e o render quebra no meio
# (Unable to capture screenshot). Converte pra SDR BT.709 ja aqui.
trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                      "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip()
# MEDIDO (i5-1235U, 8 s de 4K HEVC HDR): tonemap em 4K + x264 fast = 150 s; ESCALAR ANTES do tonemap + x264 veryfast = 61 s;
# + encode Quick Sync (h264_qsv) = 32 s. O piso (~25 s) e o decode do HEVC 10 bits em software (hwaccel nao ajudou).
sdr = (",zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv"
       if trc in ("arib-std-b67", "smpte2084") else "")
tem_qsv = "h264_qsv" in subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
enc = (["-c:v", "h264_qsv", "-global_quality", "18", "-bf", "0", "-g", "15"] if tem_qsv
       else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-bf", "0", "-g", "15"])
conv = subprocess.Popen([
    "ffmpeg", "-v", "error", "-y", "-i", str(video),
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase:flags=bilinear,crop=1080:1920,fps=30" + sdr + ",format=yuv420p",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", *enc,
    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(proj / "assets" / "video.mp4")])
wav = proj / "work" / "voz16k.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
for s in (RAIZ / "sfx").glob("*.wav"):
    shutil.copy2(s, proj / "assets" / "sfx" / s.name)

# 2. transcricao com tempo por palavra; o glossario entra como contexto pro Whisper acertar termos do nicho
gl = (RAIZ / "glossario.txt").read_text(encoding="utf-8").splitlines()
termos = [l.strip() for l in gl if l.strip() and not l.startswith("#") and "=>" not in l]
from faster_whisper import WhisperModel  # noqa: E402

with wave.open(str(wav)) as w:  # array em vez de caminho: PyAV novo quebra o faster-whisper 1.2.1
    sinal = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
# MEDIDO (26 s de audio): cpu_threads padrao (4) + conversao do 4K em paralelo = 493 s no total; com cpu_threads=10,
# medium beam 5 = 42 s, medium beam 1 = 25 s (mesmas 84 palavras), small beam 1 = 8 s.
model = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=10)
segs, _ = model.transcribe(sinal, language="pt", word_timestamps=True, beam_size=1, vad_filter=False,
                           condition_on_previous_text=False, initial_prompt=", ".join(termos)[:800])
pal = []
for seg in segs:
    for w in seg.words:
        pal.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3), "prob": round(w.probability, 3)})
(proj / "work" / "palavras.json").write_text(json.dumps(pal, ensure_ascii=False, indent=1), encoding="utf-8")
with open(proj / "work" / "lista.txt", "w", encoding="utf-8") as f:
    for i, w in enumerate(pal):
        f.write(f"{i:3d} {w['start']:6.2f} {w['end']:6.2f} {w['prob']:.2f} {'<<' if w['prob'] < 0.5 else '  '} {w['text']}\n")

# 3. espera a conversao, gera folha de quadros e o esqueleto HyperFrames
conv.wait()
if conv.returncode:
    sys.exit("falha na conversao do video")
dur = ffprobe_dur(proj / "assets" / "video.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "assets" / "video.mp4"),
                "-vf", f"fps=12/{dur:.2f},scale=216:384,tile=6x2", "-frames:v", "1", str(proj / "work" / "folha.jpg")])
if not (proj / "hyperframes.json").exists():
    for arq in ("hyperframes.json", "package.json"):
        (proj / arq).write_text((RAIZ / "modelo" / arq).read_text(encoding="utf-8").replace("{{nome}}", nome), encoding="utf-8")
(proj / "work" / "info.json").write_text(json.dumps({"fonte": str(video), "duracao": round(dur, 3), "modelo": modelo},
                                                   ensure_ascii=False), encoding="utf-8")
duvidas = sum(1 for w in pal if w["prob"] < 0.5)
print(f"OK {nome}: {dur:.1f}s, {len(pal)} palavras ({duvidas} p/ conferir), {time.time() - t0:.0f}s -> {proj}")
