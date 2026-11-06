// O rato do pet sentado sobre as patas de trás, de perfil, olhando para a direita.
// Mesmas cores e contorno do _rato.js, para ele não mudar de cara entre a corrida e as poses paradas.
// (0, 0) é o chão sob o pé de trás.

import { hex, TAU } from "../../core/index.js";
import { Grid } from "./_lib.js";
import { marcar, tronco } from "./_ancoras.js";

const GRID = new Grid(-30, -44, 62, 50);
const LAGRIMA = [hex("#8fd0f0"), hex("#5fa8d0")];

/** Pontos da cauda deitada no chão, atrás do rato, com uma ondinha na ponta. */
export function caudaChao(fase = 0, forca = 1) {
  const pts = [];
  for (let i = 0; i <= 6; i++) {
    const u = i / 6;
    pts.push([-7 - u * 15, -2 + u * 1.2 - Math.sin(u * 3.1) * 1.5 + Math.sin(fase * TAU - u * 3) * 1.8 * u * u * forca]);
  }
  return pts;
}

/**
 * Z: { x, y, respira (-1..1), olho, boca (0..1), orelha (0..1), cabeca: [dx, dy], cauda, patas, braco }
 * olho: "aberto", "fechado", "feliz" (^), "arregalado", "meio", "triste". lagrima: 0..1 desce pelo rosto. patas: "peito", "alto" (segura algo acima da
 * cabeça), "boca" (segura algo na boca), "acena" (a pata da frente balança, braco = 0..1).
 */
export function ratoSentado(p, cor, Z = {}) {
  const { C, K } = cor, g = GRID;
  const {
    x = 0, y = 0, respira = 0, olho = "aberto", boca = 0, orelha = 0, cabeca = [0, 0],
    patas = "peito", braco = 0, fade = 1, lagrima = -1,
  } = Z;
  const pontos = Z.cauda ?? caudaChao();
  const r = 1 + respira * 0.04;
  const hx = 5 + cabeca[0], hy = -25 + cabeca[1] - respira * 0.4;
  const dentro = (u, v) =>
    ((u + 2) / (9.6 * r)) ** 2 + ((v + 8.5) / 8.4) ** 2 <= 1 ||
    ((u - 0.5) / (7.2 * r)) ** 2 + ((v + 17 - respira * 0.3) / 6.8) ** 2 <= 1 ||
    ((u - hx) / 5.7) ** 2 + ((v - hy) / 4.7) ** 2 <= 1 ||
    (u > hx && u < hx + 8 && Math.abs(v - hy - 1.2) < 3.7 * (1 - (u - hx) / 8) + 0.4);

  g.clear();
  g.tube(pontos, (u) => 1.6 - u * 1, (u, d) => (d > 0.6 ? K[0] : K[1]));
  // pé de trás comprido, no chão
  for (let i = -5; i <= 4; i++) { g.set(i, -1, C[2]); g.set(i, 0, i > 1 ? K[1] : C[1]); }
  g.set(5, 0, K[1]); g.set(5, -1, K[1]);

  const naCabeca = (u, v) => ((u - hx) / 5.7) ** 2 + ((v - hy) / 4.7) ** 2 <= 1 || (u > hx && v < hy + 4);
  g.shade(-14, -36, 18, 1, (u, v) => {
    if (!dentro(u, v)) return 0;
    const barriga = ((u - 4.2) / 4.2) ** 2 + ((v + 12) / 7.5) ** 2 <= 1;
    const coxa = ((u + 3.5) / 6.2) ** 2 + ((v + 5.5) / 5.2) ** 2;
    const c = (k) => (!naCabeca(u, v) && v < -6.5 && (coxa > 0.9 || v < -9) ? tronco(k) : k);
    if (!dentro(u + 1.3, v + 1.8)) return c(C[2]);
    if (barriga && coxa > 1) return c(dentro(u - 1, v - 1) ? C[5] : C[4]);
    if (!dentro(u - 1.6, v - 2.2)) return c(C[4]);
    if (coxa <= 1 && coxa > 0.72 && v < -5 && u > -8) return c(C[2]);
    if (coxa <= 0.55 && v < -6) return c(C[4]);
    return c(C[3]);
  });

  // orelha grande
  const ox = hx - 3.6, oy = hy - 4.6 + orelha;
  g.ellipse(ox, oy, 3.5, 3.9 - orelha * 0.5, (nx, ny) => (nx * nx + ny * ny < 0.45 ? K[1] : ny < -0.1 ? C[4] : C[3]));

  // patas da frente
  const mao = (mx, my) => { g.set(mx, my, K[1]); g.set(mx + 1, my, K[1]); g.set(mx, my + 1, K[0]); };
  if (patas === "peito") {
    g.set(7, -18, C[3]); g.set(8, -18, C[3]); mao(8, -17);
    g.set(6, -16, C[2]); mao(6, -15);
  } else if (patas === "segura") {
    // as duas patas esticadas para a frente, agarrando um cabo vertical em x = braco
    const cx = braco || 15;
    g.line(5, -19, cx - 1, -20, C[4]); g.line(5, -18, cx - 1, -19, C[3]); mao(cx - 1, -21);
    g.line(4, -15, cx - 1, -16, C[3]); g.line(4, -14, cx - 1, -15, C[2]); mao(cx - 1, -16);
  } else if (patas === "boca") {
    g.line(4, -18, 8, -21, C[3]); mao(9, -21);
    g.line(2, -17, 7, -20, C[2]); mao(7, -20);
  } else if (patas === "acena") {
    const a = 0.25 - braco * 0.85, L = 9;
    const tx = 7 + Math.cos(a) * L, ty = -16 + Math.sin(a) * L;
    g.line(6, -17, tx, ty - 1, C[4]); g.line(6, -16, tx, ty, C[3]);
    const mx = Math.round(tx), my = Math.round(ty);
    for (const [dx, dy] of [[0, -2], [1, -2], [0, -1], [1, -1], [2, -1], [0, 0], [1, 0]]) g.set(mx + dx, my + dy, dy === -2 ? K[2] : K[1]);
    g.set(5, -13, C[2]); mao(5, -12);
  }

  const ex = Math.round(hx + 1.8), ey = Math.round(hy - 1);
  if (olho === "fechado") {
    g.line(ex - 1, ey + 1, ex + 1, ey + 1, C[0]);
  } else if (olho === "feliz") {
    g.set(ex - 1, ey + 1, C[0]); g.set(ex, ey, C[0]); g.set(ex + 1, ey + 1, C[0]);
  } else if (olho === "triste") {
    g.set(ex - 1, ey, C[0]); g.set(ex, ey + 1, C[0]); g.set(ex + 1, ey + 1, C[0]); g.set(ex, ey + 2, C[6]);
  } else if (olho === "meio") {
    g.line(ex - 1, ey, ex + 1, ey, C[1]); g.set(ex, ey + 1, C[0]); g.set(ex + 1, ey + 1, C[0]);
  } else if (olho === "arregalado") {
    g.ellipse(ex + 0.5, ey + 0.5, 2.3, 2.3, C[6]);
    g.set(ex + 1, ey + 1, C[0]); g.set(ex, ey + 1, C[0]);
  } else {
    g.set(ex, ey, C[6]); g.set(ex + 1, ey, C[0]); g.set(ex, ey + 1, C[0]); g.set(ex + 1, ey + 1, C[0]);
  }
  const nx = Math.round(hx + 8), ny = Math.round(hy + 0.6);
  g.set(nx, ny, K[1]); g.set(nx + 1, ny, K[1]); g.set(nx, ny + 1, K[0]);
  if (boca > 0.2) {
    const b = boca > 0.6 ? 2 : 1;
    for (let k = 0; k < b; k++) { g.set(nx - 3, ny + 3 + k, K[0]); g.set(nx - 2, ny + 3 + k, k ? K[2] : K[0]); }
    g.set(nx - 3, ny + 3 + b, K[1]); g.set(nx - 2, ny + 3 + b, K[1]);
  }
  g.outline(C[0]);
  g.draw(p, fade, Math.round(x), Math.round(y));
  const X = Math.round(x), Y = Math.round(y);
  marcar("lado", [X + hx - 0.5, Y + hy - 4.2], [X + ex, Y + ey], [X + hx - 3.5, Y + hy + 4.5], fade);
  if (lagrima >= 0) {
    const ly = Y + ey + 2 + lagrima * 7;
    p.dot(X + ex, Math.round(ly), LAGRIMA[0], fade * (1 - lagrima * 0.6));
    p.dot(X + ex, Math.round(ly) + 1, LAGRIMA[1], fade * (1 - lagrima * 0.6));
  }
  const bx = Math.round(x) + nx - 2, by = Math.round(y) + ny + 1;
  p.line(bx, by, bx + 5, by - 2, C[5], fade);
  p.line(bx, by + 1, bx + 5, by + 2, C[5], fade);
}
