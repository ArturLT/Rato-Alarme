// O rato do alarme e a gaiola dele: uma base só para todas as animações, para o corpo nunca mudar entre elas.
// O rato olha para a direita; (0, 0) é o chão, sob a barriga dele.

import { fit, hex, sparkle, TAU } from "../../core/index.js";
import { Grid } from "./_lib.js";

export const PELO = ["#17121c", "#352c3a", "#574b58", "#7f7278", "#a99c9c", "#d6cabf", "#fff4e6"];
export const ROSA = ["#7a2f48", "#d86a86", "#ffb4bc"];
export const METAL = ["#1c1a2a", "#3f4460", "#6f7a94", "#a8b4c0", "#e4ecf0"];
export const OPCOES = { palette: PELO, rosa: ROSA, metal: METAL, seed: 1 };
export const TELA = { size: [48, 48], origin: [24, 44] };

const GRID = new Grid(-30, -36, 62, 44);
const PARADO = [[-8, 0], [-5, 0], [5, 0], [8, 0]];

export const cores = (o) => ({ C: fit(o.palette, 7), K: fit(o.rosa, 3), M: fit(o.metal, 5) });

/** Cauda em repouso, ondulando um pouco com a fase. */
export function cauda(fase = 0, forca = 1) {
  const pts = [];
  for (let i = 0; i <= 5; i++) {
    const u = i / 5;
    pts.push([-9 - u * 12, -5 - u * 3 + Math.sin(fase * TAU - u * 4) * 2.4 * u * forca]);
  }
  return pts;
}

/** Quatro patas a galope na fase dada (0..1): traseiras e dianteiras em oposição. */
export function galope(fase) {
  const pata = (x, off) => {
    const a = (fase + off) * TAU;
    return [x + Math.cos(a) * 6.5, -Math.max(0, Math.sin(a)) * 3.5];
  };
  return [pata(-7, 0.12), pata(-6, 0), pata(5, 0.62), pata(6, 0.5)];
}

/**
 * Desenha o rato. Z: { x, y, rot, sq, pes, cauda, olho, boca, cabeca: [dx, dy], orelha, fundo }.
 * olho: "aberto", "fechado", "x", "arregalado". boca: 0 fechada, 1 ofegante.
 */
export function rato(p, cor, Z = {}) {
  const { C, K } = cor, g = GRID;
  const { x = 0, y = 0, rot = 0, sq = 0, pes = PARADO, olho = "aberto", boca = 0, cabeca = [0, 0], orelha = 0, fade = 1 } = Z;
  const pontos = Z.cauda ?? cauda();
  const cs = Math.cos(rot), sn = Math.sin(rot), sx = 1 - sq * 0.6, sy = 1 + sq;
  const hx = 8 + cabeca[0], hy = -9 + cabeca[1];
  const paraMundo = (u, v) => [(u * sx) * cs - ((v + 6) * sy) * sn, (u * sx) * sn + ((v + 6) * sy) * cs - 6];
  const paraRato = (a, b) => [(a * cs + (b + 6) * sn) / sx, (-a * sn + (b + 6) * cs) / sy - 6];
  const corpo = (u, v) =>
    ((u + 1.5) / 9.5) ** 2 + ((v + 6.5) / 5.8) ** 2 <= 1 ||
    ((u + 5.5) / 6.2) ** 2 + ((v + 7.5) / 6.2) ** 2 <= 1 ||
    ((u - hx) / 5.6) ** 2 + ((v - hy) / 4.3) ** 2 <= 1 ||
    (u > hx && u < hx + 7.5 && Math.abs(v - hy - 1) < 3.6 * (1 - (u - hx) / 7.5) + 0.4);

  g.clear();
  // cauda e patas de trás ficam atrás do corpo
  g.tube(pontos.map(([a, b]) => paraMundo(a, b)), (u) => 1.5 - u * 0.9, (u, d) => (d > 0.6 ? K[0] : K[1]));
  const perna = ([fx, fy], base, c) => {
    const [ax, ay] = paraMundo(base, -4), [bx, by] = paraMundo(fx, 0);
    g.line(ax, ay, bx, fy - 1, c);
    g.line(ax + 1, ay, bx + 1, fy - 1, c);
    g.line(bx - 1, fy - 0.5, bx + 2, fy - 0.5, K[1]);
  };
  perna(pes[1], -6, C[2]);
  perna(pes[3], 5, C[2]);

  g.shade(-24, -30, 26, 2, (a, b) => {
    const [u, v] = paraRato(a, b);
    if (!corpo(u, v)) return 0;
    if (v > -3.6 && u > -7 && u < 4) return C[5];
    if (!corpo(u + 1.2, v + 2)) return C[2];
    if (!corpo(u - 1.6, v - 2.4)) return C[4];
    return C[3];
  });
  // orelha grande, com o miolo rosa
  const [ox, oy] = paraMundo(hx - 3.5, hy - 4.2 + orelha);
  g.ellipse(ox, oy, 3.4, 3.8 - orelha * 0.4, (nx, ny) => (nx * nx + ny * ny < 0.45 ? K[1] : ny < -0.1 ? C[4] : C[3]));
  perna(pes[0], -5, C[3]);
  perna(pes[2], 6, C[3]);

  const [ex, ey] = paraMundo(hx + 1.6, hy - 1).map(Math.round);
  if (olho === "fechado") {
    g.line(ex - 1, ey + 1, ex + 1, ey + 1, C[0]);
  } else if (olho === "x") {
    for (const k of [-1, 0, 1]) { g.set(ex + k, ey + k, C[0]); g.set(ex + k, ey - k, C[0]); }
  } else if (olho === "arregalado") {
    g.ellipse(ex + 0.5, ey + 0.5, 2.3, 2.3, C[6]);
    g.set(ex + 1, ey + 1, C[0]);
    g.set(ex, ey + 1, C[0]);
  } else {
    g.set(ex, ey, C[0]); g.set(ex + 1, ey, C[0]); g.set(ex, ey + 1, C[0]); g.set(ex + 1, ey + 1, C[0]);
    g.set(ex, ey, C[6]);
  }
  const [nx, ny] = paraMundo(hx + 7, hy + 0.8).map(Math.round);
  g.set(nx, ny, K[1]); g.set(nx + 1, ny, K[1]); g.set(nx, ny + 1, K[0]);
  if (boca) {
    g.set(nx - 3, ny + 3, K[0]); g.set(nx - 2, ny + 3, K[0]);
    g.set(nx - 3, ny + 4, K[2]); g.set(nx - 2, ny + 4, K[1]);
  }
  g.outline(C[0]);
  g.draw(p, fade, Math.round(x), Math.round(y));
  // bigodes por cima do contorno
  const bx = Math.round(x) + nx - 2, by = Math.round(y) + ny + 1;
  p.line(bx, by, bx + 5, by - 2, C[5], fade);
  p.line(bx, by + 1, bx + 5, by + 2, C[5], fade);
}

const TOPO = (x) => -29 - 8 * Math.sqrt(Math.max(0, 1 - (x / 21) ** 2));

/** Barras de trás: ficam atrás do rato. */
export function gaiolaFundo(p, cor, { dx = 0, a = 1 } = {}) {
  const { M } = cor;
  for (const x of [-17, -3, 11]) p.line(x + dx, -3, x + dx, TOPO(x) + 1, M[1], a);
}

const BARRAS = [-21, -14, -7, 0, 7, 14, 21];

/** Barras da frente, base e argola. porta: false quando ela já voou longe. */
export function gaiolaFrente(p, cor, { dx = 0, a = 1, porta = true } = {}) {
  const { M } = cor;
  for (const x of BARRAS) {
    const daPorta = x === 7 || x === 14;
    if (!porta && daPorta) p.line(x + dx, TOPO(x), x + dx, -28, M[2], a);
    else p.line(x + dx, -3, x + dx, TOPO(x), daPorta ? M[3] : M[2], a);
  }
  for (let x = -21; x <= 21; x++) {
    p.dot(x + dx, TOPO(x), x < 0 ? M[4] : M[3], a);
    const vao = x > 0 && x < 21;
    if (!vao || porta) p.dot(x + dx, -28, vao ? M[4] : M[3], a);
    if (vao && porta) p.dot(x + dx, -5, M[4], a);
  }
  if (porta) for (let y = -17; y <= -14; y++) { p.dot(17 + dx, y, M[4], a); p.dot(18 + dx, y, M[3], a); }
  for (let y = -40; y <= -37; y++) { p.dot(-2 + dx, y, M[3], a); p.dot(2 + dx, y, M[2], a); }
  for (let x = -1; x <= 1; x++) p.dot(x + dx, -41, M[4], a);
  for (let x = -23; x <= 23; x++) {
    p.dot(x + dx, -3, M[4], a);
    p.dot(x + dx, -2, M[2], a);
    p.dot(x + dx, -1, M[1], a);
    p.dot(x + dx, 0, M[0], a);
  }
}

/** Estrelinhas girando sobre a cabeça, com fase 0..1. */
export function tontura(p, cor, x, y, fase, n = 3) {
  for (let i = 0; i < n; i++) {
    const a = (fase + i / n) * TAU;
    sparkle(p, x + Math.cos(a) * 7, y + Math.sin(a) * 2, 1.5, hex("#ffe27a"), hex("#fff8d0"), 0.15);
  }
}

// ---- As outras vistas da corrida. Todas recebem a fase 0..1 do galope. ----

const onda = (ox, oy, dx, dy, fase, forca = 3.5, n = 6) => {
  const l = Math.hypot(dx, dy) || 1, pts = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, w = Math.sin(fase * TAU - u * 4) * forca * u;
    pts.push([ox + dx * u - (dy / l) * w, oy + dy * u + (dx / l) * w]);
  }
  return pts;
};
const pelo = (C) => (nx, ny) => (nx * 0.6 + ny * 0.8 > 0.72 ? C[2] : nx * -0.6 + ny * -0.8 > 0.68 ? C[4] : C[3]);
const pe = (g, K, x, y) => { for (let k = -1; k <= 1; k++) g.set(x + k, y, K[1]); g.set(x, y - 1, K[0]); };
const cauda3 = (g, K, pts) => g.tube(pts, (u) => 1.5 - u * 0.9, (u, d) => (d > 0.6 ? K[0] : K[1]));

function elipseGirada(g, cx, cy, rx, ry, ang, c) {
  const cs = Math.cos(ang), sn = Math.sin(ang), R = Math.max(rx, ry) + 1;
  g.shade(cx - R, cy - R, cx + R, cy + R, (x, y) => {
    const dx = x - cx, dy = y - cy, u = (dx * cs + dy * sn) / rx, v = (-dx * sn + dy * cs) / ry;
    return u * u + v * v > 1 ? 0 : c(u * cs - v * sn, u * sn + v * cs, u, v);
  });
}

/** Correndo para cima: o rato de costas, com a cauda balançando embaixo. */
export function ratoCostas(p, cor, f) {
  const { C, K } = cor, g = GRID, a = f * TAU, up = (o) => Math.max(0, Math.sin(a + o)) * 3;
  const roll = Math.round(Math.sin(a));
  g.clear();
  cauda3(g, K, onda(0, -5, 0, 10, f * 2, 5));
  g.ellipse(-6 + roll, -25, 3.4, 3.8, pelo(C));
  g.ellipse(6 + roll, -25, 3.4, 3.8, pelo(C));
  g.ellipse(roll, -21, 5.6, 4.8, pelo(C));
  g.line(-8, -13 - up(Math.PI) , -9, -9 - up(Math.PI), C[3]);
  g.line(8, -13 - up(0), 9, -9 - up(0), C[3]);
  g.ellipse(0, -10, 8.6, 9.4, pelo(C));
  for (const [x, y] of [[-3, -5], [3, -5], [-2, -4], [2, -4]]) g.set(x, y, C[2]);
  g.ellipse(0, -14, 4.5, 3, () => C[4]);
  pe(g, K, -6, -1 - up(0));
  pe(g, K, 6, -1 - up(Math.PI));
  g.outline(C[0]);
  g.draw(p, 1, 0, -4 - Math.round(Math.abs(Math.sin(a)) * 2));
}

/** Correndo em diagonal para cima e para a direita: três quartos de costas. */
export function ratoCostasLado(p, cor, f) {
  const { C, K } = cor, g = GRID, a = f * TAU, up = (o) => Math.max(0, Math.sin(a + o)) * 3;
  g.clear();
  cauda3(g, K, onda(-7, -7, -12, 8, f * 2, 3.5));
  pe(g, K, -2, -2 - up(Math.PI));
  pe(g, K, 9, -9 - up(0));
  g.ellipse(10, -25, 3, 3.4, pelo(C));
  elipseGirada(g, -1, -11, 11, 7, -0.75, pelo(C));
  g.ellipse(8, -20, 5.2, 4.4, pelo(C));
  g.ellipse(3, -24, 3.4, 3.8, pelo(C));
  g.set(11, -21, C[0]); g.set(12, -21, C[0]);
  g.set(13, -20, K[1]); g.set(13, -21, K[1]);
  pe(g, K, -9, -2 - up(0));
  pe(g, K, 3, -5 - up(Math.PI));
  g.outline(C[0]);
  g.draw(p, 1, 0, -Math.round(Math.abs(Math.sin(a)) * 2));
}

const orelhaFrente = (C, K) => (nx, ny) => (nx * nx + ny * ny < 0.34 ? K[1] : ny < -0.1 ? C[4] : C[3]);
// Faixa escura sob a peça: separa cabeça e orelhas do corpo, que têm a mesma cor.
const comContorno = (g, C, x, y, rx, ry, c) => { g.ellipse(x, y, rx + 1, ry + 1, () => C[1]); g.ellipse(x, y, rx, ry, c); };
const olhos = (g, C, y, xs) => {
  for (const x of xs) { g.set(x, y, C[6]); g.set(x + 1, y, C[0]); g.set(x, y + 1, C[0]); g.set(x + 1, y + 1, C[0]); }
};
const perna = (g, C, K, x0, y0, x, y) => { g.line(x0, y0, x, y - 1, C[3]); g.line(x0 + 1, y0, x + 1, y - 1, C[2]); pe(g, K, x, y); };

/** Correndo para baixo: mesma silhueta da vista de costas, com a cabeça na frente e o rosto à mostra. */
export function ratoFrente(p, cor, f) {
  const { C, K } = cor, g = GRID, a = f * TAU, up = (o) => Math.max(0, Math.sin(a + o)) * 3;
  const roll = Math.round(Math.sin(a)), dy = -Math.round(Math.abs(Math.sin(a)) * 2);
  g.clear();
  cauda3(g, K, onda(0, -28, 0, -7, f * 2, 4));
  perna(g, C, K, -7, -22, -9, -18 - up(0));
  perna(g, C, K, 6, -22, 9, -18 - up(Math.PI));
  g.ellipse(0, -21, 7.8, 8.4, pelo(C));
  g.ellipse(0, -24, 4, 2.4, () => C[4]);
  perna(g, C, K, -5, -8, -5, -1 - up(Math.PI));
  perna(g, C, K, 4, -8, 5, -1 - up(0));
  for (const s of [-1, 1]) comContorno(g, C, roll + s * 7, -16, 3.6, 4, orelhaFrente(C, K));
  comContorno(g, C, roll, -10, 6.4, 5.4, pelo(C));
  g.ellipse(roll, -7.5, 3.2, 2.2, () => C[5]);
  olhos(g, C, -12, [roll - 4, roll + 3]);
  g.set(roll - 1, -9, K[1]); g.set(roll, -9, K[1]); g.set(roll, -8, K[0]);
  g.outline(C[0]);
  g.draw(p, 1, 0, dy);
  for (const s of [-1, 1]) {
    p.line(roll + s * 4, -8 + dy, roll + s * 8, -9 + dy, C[4]);
    p.line(roll + s * 4, -7 + dy, roll + s * 8, -6 + dy, C[4]);
  }
}

/** Correndo em diagonal para baixo e para a direita: três quartos de frente. */
export function ratoFrenteLado(p, cor, f) {
  const { C, K } = cor, g = GRID, a = f * TAU, up = (o) => Math.max(0, Math.sin(a + o)) * 3;
  const dy = -Math.round(Math.abs(Math.sin(a)) * 2);
  g.clear();
  cauda3(g, K, onda(-9, -22, -12, -6, f * 2, 3.5));
  perna(g, C, K, 0, -12, 0, -7 - up(0));
  perna(g, C, K, 10, -6, 11, -1 - up(Math.PI));
  elipseGirada(g, -2, -16, 11, 7, 0.6, (nx, ny, u, v) => (v > 0.5 ? C[5] : pelo(C)(nx, ny)));
  comContorno(g, C, 11, -15, 3, 3.4, orelhaFrente(C, K));
  comContorno(g, C, 3, -15, 3.4, 3.8, orelhaFrente(C, K));
  comContorno(g, C, 7, -9, 6, 5.2, pelo(C));
  g.ellipse(10, -6.5, 3, 2.2, () => C[5]);
  olhos(g, C, -11, [5, 10]);
  g.set(12, -8, K[1]); g.set(13, -8, K[1]); g.set(12, -7, K[0]);
  perna(g, C, K, -6, -12, -7, -7 - up(Math.PI));
  perna(g, C, K, 3, -6, 3, -1 - up(0));
  g.outline(C[0]);
  g.draw(p, 1, 0, dy);
  p.line(11, -6 + dy, 15, -7 + dy, C[4]);
  p.line(11, -5 + dy, 15, -4 + dy, C[4]);
}
