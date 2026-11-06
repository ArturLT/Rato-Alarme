import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato pendurado",
  desc: "Pego pelo cangote: o rato fica de pé no ar, cabeça para cima, patinhas balançando e cauda girando.",
  tags: ["critter", "rat", "pet", "held", "loop"],
  ...TELA,
  duration: 0.6,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, a = f * TAU;
  const pe = (x, off) => [x + Math.sin(a * 2 + off) * 2, 2 + Math.cos(a * 2 + off) * 1.5];
  const pts = [];
  for (let i = 0; i <= 5; i++) {
    const u = i / 5;
    pts.push([-9 - u * 10, -5 + Math.sin(a - u * 3) * 4 * u]);
  }
  rato(p, cor, {
    x: 2, y: -7, rot: -Math.PI / 2 + Math.sin(a) * 0.12, olho: "arregalado", boca: 1, orelha: 0,
    pes: [pe(-8, 0), pe(-5, 1.5), pe(5, 3), pe(8, 4.5)], cauda: pts,
  });
}
