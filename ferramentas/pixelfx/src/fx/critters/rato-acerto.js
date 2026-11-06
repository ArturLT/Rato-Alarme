import { hex, rng, seg, sparkle, TAU, WHITE } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato acerto",
  desc: "O clique acerta o rato: ele achata, pisca em branco, solta estrelas e volta com um susto.",
  tags: ["critter", "rat", "hit"],
  ...TELA,
  duration: 0.5,
  loop: false,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o);
  if (t >= 0.45) return;
  const k = seg(t, 0, 0.3);
  rato(p, cor, { sq: -0.32 * (1 - k), olho: "arregalado", cauda: cauda(t * 6, 1.4), orelha: 1 - k });
  if (t < 0.1) sparkle(p, 4, -12, 7, WHITE, hex("#ffe27a"), 0.3);
  for (let i = 0; i < 7; i++) {
    const r = rng(o.seed, i, 9), an = r.range(Math.PI, TAU), d = 6 + t * r.range(30, 50);
    sparkle(p, 4 + Math.cos(an) * d, -10 + Math.sin(an) * d, 3 * (1 - k), hex("#ffe27a"), WHITE, 0.3);
  }
}
