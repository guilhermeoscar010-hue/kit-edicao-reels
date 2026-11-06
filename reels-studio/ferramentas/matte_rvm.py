"""Gera o matte (alpha) da pessoa com RobustVideoMatting ONNX.

Uso: python -I matte_rvm.py <video.mp4> <saida.mkv> <modelo.onnx> [downsample=0.5] [frame_ini=0] [n_frames=0=todos] [escala=0.5]
Saida: video FFV1 em tons de cinza (branco = pessoa) em (1080*escala)x(1920*escala), mesmo fps/frames do video.
O compositor (gerar_ff.py) amplia o alfa pra 1080x1920. escala 0.5 = ~4x mais rapido que 1080p (o refinador do RVM e o custo).
"""
import subprocess
import sys
import time

import numpy as np
import onnxruntime as ort

src, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
ds = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
ini = int(sys.argv[5]) if len(sys.argv) > 5 else 0
n = int(sys.argv[6]) if len(sys.argv) > 6 else 0
esc = float(sys.argv[7]) if len(sys.argv) > 7 else 0.5
W, H, FPS = int(1080 * esc) // 2 * 2, int(1920 * esc) // 2 * 2, 30

dec_cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"select=gte(n\\,{ini}),scale={W}:{H}:flags=bilinear", "-fps_mode", "passthrough"]
if n:
    dec_cmd += ["-frames:v", str(n)]
dec_cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE)
enc = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", str(FPS),
     "-i", "-", "-c:v", "ffv1", "-pix_fmt", "gray", out],
    stdin=subprocess.PIPE,
)

opts = ort.SessionOptions()
opts.intra_op_num_threads = 8
sess = ort.InferenceSession(model, opts, providers=["CPUExecutionProvider"])
rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
dsr = np.array([ds], dtype=np.float32)

t0, i = time.time(), 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    fgr, pha, *rec = sess.run(None, {"src": img, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": dsr})
    enc.stdin.write((np.clip(pha[0, 0], 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    i += 1
    if i % 60 == 0:
        print(f"{i} frames  {i / (time.time() - t0):.2f} fps", flush=True)

enc.stdin.close()
enc.wait()
dec.wait()
print(f"ok: {i} frames em {time.time() - t0:.0f}s -> {out}")
