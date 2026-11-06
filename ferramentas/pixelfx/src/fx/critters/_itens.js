// Coisas que o rato carrega na boca e larga pela tela. Cada item é desenhado com o ponto (x, y) no
// lugar onde o rato o morde (o topo do item), para o mesmo desenho servir na boca e no chão.

import { hex } from "../../core/index.js";
import { Grid } from "./_lib.js";

const G = new Grid(-16, -16, 32, 32);
const c = (s) => hex(s);

const QUEIJO = ["#5a3a10", "#b8801c", "#f0c040", "#ffe27a", "#fff4b0"].map(c);
const MEIA = ["#2a1a3a", "#d8d0e0", "#ffffff", "#d84860", "#8a2040"].map(c);
const PAPEL = ["#3a3440", "#a8a0b0", "#e8e4ee", "#ffffff", "#4060a0"].map(c);
const OURO = ["#5a3008", "#b87010", "#f0b020", "#ffe070", "#fffbe0"].map(c);
const FLOR = ["#3a0a1a", "#b02040", "#f05070", "#ffb0c0", "#2a5a20", "#58a038", "#ffe070"].map(c);
const MIGALHA = ["#5a3a10", "#c89040", "#f0d090"].map(c);

export const ITENS = ["queijo", "meia", "bilhete", "moeda", "flor"];

function queijo(g) {
  // fatia em cunha, com a casca escura embaixo e furinhos
  for (let y = 0; y <= 6; y++) {
    const w = Math.round(2 + y * 1.3);
    for (let x = -w; x <= w - 1; x++) {
      let k = 2;
      if (y === 6) k = 1;
      else if (y === 0 || x === -w) k = 3;
      g.set(x, y, QUEIJO[k]);
    }
  }
  for (const [x, y] of [[-2, 3], [2, 4], [-5, 5], [4, 2]]) { g.set(x, y, QUEIJO[1]); g.set(x + 1, y, QUEIJO[1]); }
  g.set(-1, 1, QUEIJO[4]); g.set(0, 1, QUEIJO[4]);
}

function meia(g) {
  // cano listrado na vertical, pé virado para a direita
  for (let y = 0; y <= 7; y++) for (let x = -2; x <= 1; x++) g.set(x, y, y % 3 === 1 ? MEIA[3] : MEIA[1 + (x < 0 ? 1 : 0)]);
  for (let x = -2; x <= 4; x++) for (let y = 8; y <= 10; y++) g.set(x, y, x > 2 && y === 8 ? 0 : y === 10 ? MEIA[1] : MEIA[2]);
  for (let x = 3; x <= 4; x++) for (let y = 8; y <= 10; y++) g.set(x, y, MEIA[3]);
  for (let x = -2; x <= 1; x++) g.set(x, 0, MEIA[4]);
}

function bilhete(g) {
  for (let y = 0; y <= 7; y++) for (let x = -5; x <= 5; x++) g.set(x, y, x === 5 || y === 7 ? PAPEL[1] : PAPEL[x + y < -2 ? 3 : 2]);
  for (const y of [2, 4]) for (let x = -3; x <= 3; x++) if (x !== 0 || y === 2) g.set(x, y, PAPEL[4]);
  g.set(4, 0, PAPEL[1]); g.set(5, 0, 0); g.set(5, 1, PAPEL[1]);
}

function moeda(g, brilho = 0) {
  g.ellipse(0, 4, 4.4, 4.4, (nx, ny) => (nx * nx + ny * ny > 0.7 ? (nx + ny > 0 ? OURO[1] : OURO[3]) : nx + ny > 0.3 ? OURO[2] : OURO[3]));
  for (let y = 2; y <= 6; y++) g.set(0, y, OURO[1]);
  g.set(-1, 2, OURO[1]); g.set(1, 6, OURO[1]);
  if (brilho > 0) { g.set(-2, 1, OURO[4]); g.set(-3, 2, OURO[4]); }
}

function flor(g) {
  for (let y = 4; y <= 10; y++) g.set(0, y, FLOR[5]);
  g.set(1, 8, FLOR[5]); g.set(2, 7, FLOR[5]); g.set(2, 8, FLOR[4]);
  for (const [dx, dy] of [[-2, 0], [2, 0], [0, -2], [0, 2], [-1, -1], [1, 1], [1, -1], [-1, 1]]) {
    g.ellipse(dx * 1.2, 2 + dy * 1.2, 1.6, 1.6, () => (dy < 0 ? FLOR[3] : FLOR[2]));
  }
  g.set(0, 2, FLOR[6]); g.set(1, 2, FLOR[6]); g.set(0, 3, FLOR[6]);
}

const DESENHOS = { queijo, meia, bilhete, moeda, flor };
const CONTORNO = { queijo: QUEIJO[0], meia: MEIA[0], bilhete: PAPEL[0], moeda: OURO[0], flor: FLOR[0] };

/** Desenha o item com o topo em (x, y). rot em passos de 90 graus não; só inclina com dx no topo. */
export function item(p, nome, x, y, { fade = 1, brilho = 0 } = {}) {
  G.clear();
  DESENHOS[nome](G, brilho);
  G.outline(CONTORNO[nome]);
  G.draw(p, fade, Math.round(x), Math.round(y));
}

/** Farelos que caem ou ficam no chão. */
export function migalhas(p, pontos, fade = 1) {
  for (const [x, y, k] of pontos) p.dot(Math.round(x), Math.round(y), MIGALHA[k % 3], fade);
}
