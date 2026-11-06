import { hex, TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato morto",
  desc: "O rato de barriga para cima, olhos em X e patas para o alto; uma alminha translúcida sobe e some.",
  tags: ["critter", "rat", "pet", "dead", "loop"],
  ...TELA,
  duration: 3,
  loop: true,
  fps: 12,
  bg: "dark",
  options: OPCOES,
};

const ALMA = [hex("#e8f0ff"), hex("#a8c0e8")];

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  rato(p, cor, {
    x: 0, y: -12, rot: Math.PI, olho: "x", cabeca: [0, 0], orelha: 1,
    pes: [[-8, -1], [-5, -2], [5, -2], [8, -1]], cauda: cauda(0, 0.1),
  });
  // a alminha: um fantasminha com a mesma cara, subindo e sumindo
  const k = f, y = -14 - k * 22, x = Math.sin(k * TAU * 1.5) * 3, a = 0.9 * (1 - k) * Math.min(1, k * 6);
  p.disc(x, y, 4.5, ALMA[0], a);
  p.disc(x - 2, y + 4, 2.5, ALMA[1], a * 0.8);
  p.disc(x + 2, y + 4, 2.5, ALMA[1], a * 0.8);
  if (a > 0.15) { p.dot(Math.round(x) - 1, Math.round(y) - 1, cor.C[0], a); p.dot(Math.round(x) + 2, Math.round(y) - 1, cor.C[0], a); }
}
