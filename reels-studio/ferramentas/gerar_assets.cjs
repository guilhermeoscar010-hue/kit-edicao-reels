// Gera PNGs transparentes (legendas, textos atras, cards, imagens atras) com o Chrome headless do HyperFrames.
// Substitui o render quadro a quadro do Chrome: o ffmpeg (gerar_ff.py) so cola esses PNGs no video.
// Uso: node gerar_assets.cjs <pasta-do-projeto>
// Saida: <projeto>/work/png/*.png + manifest.json [{key, file, x, y, w, h}]
const fs = require("fs"), path = require("path"), os = require("os");

const RAIZ = path.resolve(__dirname, "..");
const proj = path.resolve(process.argv[2]);
const ed = JSON.parse(fs.readFileSync(path.join(proj, "edicao.json"), "utf8"));
const est = JSON.parse(fs.readFileSync(path.join(RAIZ, "estilo-ref.json"), "utf8"));
const leg = est.legenda, atr = est.atras;

const npx = path.join(process.env.LOCALAPPDATA, "npm-cache", "_npx");
const pkg = fs.readdirSync(npx).map(d => path.join(npx, d, "node_modules", "puppeteer-core")).find(p => fs.existsSync(p));
const puppeteer = require(pkg);
const fdir = path.join(os.homedir(), ".cache", "hyperframes", "fonts", "poppins");
const walk = d => fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : e.name === "chrome-headless-shell.exe" ? [path.join(d, e.name)] : []);
const chrome = walk(path.join(os.homedir(), ".cache", "hyperframes", "chrome", "chrome-headless-shell"))[0];

// o maior .woff2 de cada peso e o subconjunto latino completo (acentos do portugues)
const fonte = peso => {
  const fs_ = fs.readdirSync(fdir).filter(f => f.startsWith(peso + "-normal")).map(f => ({ f, n: fs.statSync(path.join(fdir, f)).size }));
  return fs_.sort((a, b) => b.n - a.n)[0].f;
};
const url = p => "file:///" + p.replace(/\\/g, "/");
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

const sombra = leg.sombra.map(s => `drop-shadow(${s})`).join(" ");
const css = `
@font-face{font-family:Poppins;font-weight:800;src:url("${url(path.join(fdir, fonte(800)))}") format("woff2");}
@font-face{font-family:Poppins;font-weight:900;src:url("${url(path.join(fdir, fonte(900)))}") format("woff2");}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
.el{position:absolute;visibility:hidden}
.grupo{left:0;width:1080px;padding:70px 40px;text-align:center;filter:${sombra};font-family:Poppins;font-weight:${leg.peso};color:${leg.cor};line-height:1.02}
.l1{font-size:${leg.tamanho}px;letter-spacing:-1px}
.l2{font-size:${leg.tamanho_destaque}px;color:${leg.destaque_cor};text-transform:uppercase;letter-spacing:-2px}
.atras{left:0;width:1080px;padding:40px 0;text-align:center;font-family:Poppins;font-weight:${atr.peso};line-height:.9;letter-spacing:-4px;text-transform:uppercase}
.wrap{padding:60px;display:flex;align-items:center;justify-content:center}
.wrap img.o{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 18px 30px rgba(0,0,0,.45))}
.card{position:relative;border:5px dashed ${leg.destaque_cor};border-radius:22px;background:rgba(10,10,10,.42);box-shadow:0 0 18px rgba(245,217,10,.35);padding:14px;overflow:hidden}
.card img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 8px 14px rgba(0,0,0,.5))}
.card img.foto{object-fit:cover;border-radius:12px}
.xis{position:absolute;left:8%;right:8%;top:50%;height:14px;background:#E5322D;border-radius:7px;transform:rotate(-35deg);box-shadow:0 0 10px rgba(0,0,0,.5)}
`;

const itens = []; // {key, html}
ed.paginas.forEach((p, i) => {
  const l1 = p.palavras.filter(w => !w.d).map(w => esc(w.t)).join(" ");
  const l2 = p.palavras.filter(w => w.d).map(w => esc(w.t)).join(" ");
  itens.push({ key: `cap${i}`, html: `<div class="el grupo" style="top:${leg.y_topo - 70}px">${l1 ? `<div class="l1">${l1}</div>` : ""}${l2 ? `<div class="l2">${l2}</div>` : ""}</div>` });
});
(ed.atras || []).forEach((a, i) => {
  if (!a.texto) return;
  const maior = Math.max(...a.texto.split("|").map(x => x.length));
  const tam = Math.min(300, Math.floor(960 / (maior * 0.74)));
  itens.push({ key: `atras${i}`, html: `<div class="el atras" style="top:${atr.y_topo - 40}px;font-size:${tam}px;color:${a.cor || atr.cor}">${a.texto.split("|").map(esc).join("<br>")}</div>` });
});
(ed.imagens || []).forEach((m, i) => {
  const src = url(path.resolve(proj, m.arq));
  const h = m.h || m.w;
  if (m.modo === "atras") {
    itens.push({ key: `img${i}`, html: `<div class="el wrap" style="left:${m.x - 60}px;top:${m.y - 60}px;width:${m.w + 120}px;height:${h + 120}px"><img class="o" src="${src}"></div>` });
  } else {
    itens.push({ key: `img${i}`, html: `<div class="el wrap" style="left:${m.x - 60}px;top:${m.y - 60}px;width:${m.w + 120}px;height:${h + 120}px"><div class="card" style="width:${m.w}px;height:${h}px;transform:rotate(${m.rot || 0}deg)"><img class="${m.foto ? "foto" : ""}" src="${src}">${m.x_vermelho ? '<div class="xis"></div>' : ""}</div></div>` });
  }
});

(async () => {
  const out = path.join(proj, "work", "png");
  fs.mkdirSync(out, { recursive: true });
  const b = await puppeteer.launch({ executablePath: chrome, args: ["--allow-file-access-from-files", "--force-color-profile=srgb"] });
  const pg = await b.newPage();
  await pg.setViewport({ width: 1080, height: 1920 });
  const hp = path.join(out, "_pagina.html");
  fs.writeFileSync(hp, `<html><head><meta charset="utf-8"><style>${css}</style></head><body>${itens.map((x, i) => x.html.replace('class="el', `data-i="${i}" class="el`)).join("")}</body></html>`);
  await pg.goto(url(hp));
  await pg.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 400));
  const manifest = [];
  for (let i = 0; i < itens.length; i++) {
    const h = await pg.$(`[data-i="${i}"]`);
    await pg.evaluate(el => { el.style.visibility = "visible"; }, h);
    await Promise.all((await pg.$$eval(`[data-i="${i}"] img`, ims => ims.map(im => im.decode ? im.decode().catch(() => 0) : 0))));
    const bb = await h.boundingBox();
    const file = path.join(out, itens[i].key + ".png");
    await h.screenshot({ path: file, omitBackground: true, optimizeForSpeed: true });
    await pg.evaluate(el => { el.style.visibility = "hidden"; }, h);
    manifest.push({ key: itens[i].key, file, x: Math.round(bb.x), y: Math.round(bb.y), w: Math.round(bb.width), h: Math.round(bb.height) });
  }
  fs.writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 1));
  await b.close();
  console.log(`${manifest.length} PNGs em ${out}`);
})().catch(e => { console.error(e); process.exit(1); });
