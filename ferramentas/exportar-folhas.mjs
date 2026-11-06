// Gera as folhas de sprites do rato com o PixelFX e copia para alarma/folhas.
//   node ferramentas/exportar-folhas.mjs
//
// Para cada animação do rato saem três arquivos:
//   rato-X.png / rato-X.json   a folha de sempre; no JSON, meta.ancoras traz, quadro a quadro, onde ficam
//                              o topo da cabeça, o olho e o pescoço, e de que lado ele está virado
//   rato-X.mascara.png         a mesma folha com o tronco em magenta, onde o app pinta a roupa
// Os acessórios saem em alarma/folhas/acessorios/<peça>-<vista>.png, com o encaixe no meio (ENCAIXE).

import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const PIXELFX = join(AQUI, "pixelfx");
const DESTINO = join(AQUI, "..", "alarma", "folhas");
const ACESSORIOS = join(DESTINO, "acessorios");

const { loadEffect, renderFrames, spriteSheet } = await import(join(PIXELFX, "tools", "lib", "fxlib.mjs"));
const { resolveOptions } = await import(join(PIXELFX, "src", "core", "fx.js"));
const { createFrame, painterFor, composite } = await import(join(PIXELFX, "src", "core", "index.js"));
const { ANCORAS } = await import(join(PIXELFX, "src", "fx", "critters", "_ancoras.js"));
const { PECAS, peca } = await import(join(PIXELFX, "src", "fx", "critters", "_acessorios.js"));
const { ITENS } = await import(join(PIXELFX, "src", "fx", "critters", "_itens.js"));
const { encodePNG } = await import(join(PIXELFX, "tools", "lib", "png.mjs"));

const ALARME = ["acerto", "cansado", "correndo", "correndo-baixo", "correndo-baixo-lado", "correndo-cima", "correndo-cima-lado",
  "dormindo", "fuga", "pego", "reclamando", "sumindo"];
const PET = ["sentado", "falando", "placa", "acenando", "comendo", "feliz", "cochilando", "andando", "puxando", "surgindo",
  "triste", "morto", "pendurado"];
const FOLHAS = [
  ...[...ALARME, ...PET].map((n) => [`rato-${n}`, `critters/rato-${n}`, null, true]),
  ...ITENS.map((i) => [`rato-andando-${i}`, "critters/rato-andando", { item: i }, true]),
  ...[...ITENS, "migalhas", "pegadas", "lapide"].map((i) => [`objeto-${i}`, "critters/objeto-tela", { item: i }, false]),
];

// Um pintor que não pinta nada: serve para rodar o desenho só para ler os encaixes.
const MUDO = new Proxy({}, { get: (_, k) => (k === "measure" ? () => 0 : () => MUDO) });

function encaixes(fx, opcoes, n, fps) {
  const opts = resolveOptions(fx.meta, opcoes ?? {}), D = fx.meta.duration;
  const lista = [];
  let t = 0;
  for (let i = 0; i < n; i++) {
    if (i > 0) t += 1 / fps;
    ANCORAS.pontos = {};
    fx.mod.draw(MUDO, fx.meta.loop ? t % D : Math.min(t, D), opts);
    const a = ANCORAS.pontos, [ox, oy] = fx.meta.origin;
    const mover = (q) => (q ? [q[0] + ox, q[1] + oy] : null);
    lista.push(a.vista ? { vista: a.vista, topo: mover(a.topo), olho: mover(a.olho), pescoco: mover(a.pescoco), fade: +a.fade.toFixed(2) } : null);
  }
  return lista;
}

for (const [nome, efeito, opcoes, eRato] of FOLHAS) {
  const fx = await loadEffect(efeito);
  ANCORAS.mascara = false;
  const r = renderFrames(fx, { options: opcoes ?? undefined, bg: "none" });
  const folha = spriteSheet(fx, r, nome);
  if (eRato) {
    folha.json.meta.ancoras = encaixes(fx, opcoes, r.n, r.fps);
    ANCORAS.mascara = true;
    const m = renderFrames(fx, { options: opcoes ?? undefined, bg: "none" });
    ANCORAS.mascara = false;
    writeFileSync(join(DESTINO, `${nome}.mascara.png`), spriteSheet(fx, m, nome).png);
  }
  writeFileSync(join(DESTINO, `${nome}.png`), folha.png);
  writeFileSync(join(DESTINO, `${nome}.json`), JSON.stringify(folha.json, null, 1));
  console.log(`${nome}  <-  ${efeito}${opcoes ? " " + JSON.stringify(opcoes) : ""}${eRato ? "  +máscara +encaixes" : ""}`);
}

// Acessórios: 32x32, encaixe em (16, 16).
const LADO = 32, ENCAIXE = 16;
rmSync(ACESSORIOS, { recursive: true, force: true });
mkdirSync(ACESSORIOS, { recursive: true });
const catalogo = {};
for (const [id, pc] of Object.entries(PECAS)) {
  catalogo[id] = { slot: pc.slot, nome: pc.nome, vistas: [] };
  for (const vista of ["lado", "frente", "costas"]) {
    if (vista === "costas" && pc.costas === false) continue;
    const quadro = createFrame(LADO, LADO, 0, 0);
    const p = painterFor(quadro);
    p.place(ENCAIXE, ENCAIXE, false, 0);
    peca(p, id, vista, 0, 0);
    const rgba = composite(quadro, new Uint8ClampedArray(LADO * LADO * 4), null);
    writeFileSync(join(ACESSORIOS, `${id}-${vista}.png`), encodePNG(LADO, LADO, rgba));
    catalogo[id].vistas.push(vista);
  }
}
writeFileSync(join(ACESSORIOS, "catalogo.json"), JSON.stringify({ lado: LADO, encaixe: ENCAIXE, pecas: catalogo }, null, 1));
console.log(`${Object.keys(PECAS).length} acessórios em ${ACESSORIOS}`);
