import { rng, wrap } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, galope, rato } from "./_rato.js";

export const meta = {
  name: "Rato correndo",
  desc: "O rato galopa em disparada, com a cauda chicoteando e um pouco de poeira nas patas.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, a = f * Math.PI * 2;
  rato(p, cor, {
    x: 2, y: -Math.abs(Math.sin(a)) * 3, rot: Math.sin(a) * 0.14, sq: Math.cos(a * 2) * 0.05,
    pes: galope(f), cauda: cauda(f * 2, 1.4), cabeca: [1, Math.sin(a) * 0.8], orelha: 1,
  });
  for (let i = 0; i < 3; i++) {
    const r = rng(o.seed, i, 5), k = wrap(f + i / 3, 1);
    p.dot(-12 - k * 9, -1 - k * 2 + r.range(-1, 0), cor.C[4], 1 - k);
  }
}
