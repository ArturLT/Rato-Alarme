import { hex, rng, seg, sparkle, TAU, WHITE } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, gaiolaFrente, gaiolaFundo, rato } from "./_rato.js";

export const meta = {
  name: "Rato sumindo",
  desc: "A gaiola com o rato dormindo se desfaz aos poucos em poeira e brilhos até não sobrar nada.",
  tags: ["critter", "rat", "cage", "vanish"],
  ...TELA,
  duration: 1.2,
  loop: false,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const POEIRA = hex("#8a7f92");

export function draw(p, t, o) {
  const cor = cores(o);
  if (t >= 1.15) return;
  const a = 1 - seg(t, 0.1, 0.8);
  if (a > 0) {
    gaiolaFundo(p, cor, { a });
    rato(p, cor, {
      x: -1, y: -3, sq: -0.1, olho: "fechado", cabeca: [-1, 4], orelha: 1,
      pes: [[-7, 0], [-5, 0], [3, 0], [5, 0]], cauda: cauda(0, 0), fade: a,
    });
    gaiolaFrente(p, cor, { a });
  }
  for (let i = 0; i < 14; i++) {
    const r = rng(o.seed, i, 53), L = r.range(0.45, 0.8), inicio = r.range(0.1, 0.35), age = t - inicio;
    if (age < 0 || age > L) continue;
    const an = r.range(0, TAU), k = age / L, d = 4 + k * r.range(6, 13);
    p.disc(Math.cos(an) * d * 1.3, -16 + Math.sin(an) * d - k * 7, r.range(2, 4) * (1 - k * 0.5), POEIRA, 0.5 * (1 - k));
  }
  for (let i = 0; i < 5; i++) {
    const r = rng(o.seed, i, 71), inicio = r.range(0.5, 0.85), age = t - inicio;
    if (age >= 0 && age < 0.25) sparkle(p, r.range(-14, 14), r.range(-30, -6), 3 * (1 - age / 0.25), WHITE, hex("#ffe27a"), 0.2);
  }
}
