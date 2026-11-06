import { hex, rng, seg, sparkle, TAU, WHITE } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato surgindo",
  desc: "Puf: uma nuvenzinha de poeira estoura no chão e, quando ela se desfaz, o rato já está sentado ali.",
  tags: ["critter", "rat", "pet", "spawn", "poof"],
  ...TELA,
  duration: 1.0,
  loop: false,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const NUVEM = ["#4a4258", "#8a7f92", "#c8bfcc", "#f0eaf2"].map(hex);

export function draw(p, t, o) {
  const cor = cores(o);
  const aparece = seg(t, 0.25, 0.45);
  if (aparece > 0) ratoSentado(p, cor, { olho: t < 0.6 ? "arregalado" : "aberto", cauda: caudaChao(0, 1), fade: aparece });
  for (let i = 0; i < 12; i++) {
    const r = rng(o.seed, i, 31), an = r.range(Math.PI, TAU) + (i % 2 ? 0 : r.range(-0.3, 0.3));
    const inicio = r.range(0, 0.08), age = t - inicio, L = r.range(0.45, 0.75);
    if (age < 0 || age > L) continue;
    const k = age / L, d = 3 + (1 - (1 - k) ** 3) * r.range(8, 13);
    const raio = r.range(3, 6) * (1 - k * 0.7);
    const x = Math.cos(an) * d * 1.2, y = -10 + Math.sin(an) * d * 0.8 - k * 4;
    p.disc(x, y, raio, NUVEM[k < 0.3 ? 3 : k < 0.6 ? 2 : 1], 0.85 * (1 - k));
  }
  for (let i = 0; i < 4; i++) {
    const r = rng(o.seed, i, 77), inicio = r.range(0.05, 0.3), age = t - inicio;
    if (age >= 0 && age < 0.3) sparkle(p, r.range(-14, 14), r.range(-30, -6), 3 * (1 - age / 0.3), WHITE, hex("#ffe27a"), 0.2);
  }
  if (t > meta.duration - 0.02) return;
}
