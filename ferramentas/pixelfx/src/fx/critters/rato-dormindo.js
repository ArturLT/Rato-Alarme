import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, gaiolaFrente, gaiolaFundo, rato } from "./_rato.js";

export const meta = {
  name: "Rato dormindo",
  desc: "O rato dorme encolhido na gaiola, com a barriga subindo e descendo e um z flutuando.",
  tags: ["critter", "rat", "cage", "sleep", "loop"],
  ...TELA,
  duration: 2.4,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, ar = Math.sin(f * TAU);
  gaiolaFundo(p, cor);
  rato(p, cor, {
    x: -1, y: -3, sq: -0.1 + ar * 0.05, olho: "fechado", cabeca: [-1, 4], orelha: 1,
    pes: [[-7, 0], [-5, 0], [3, 0], [5, 0]], cauda: cauda(0, 0),
  });
  gaiolaFrente(p, cor);
  const k = (f * 2) % 1;
  p.text("z", 10 + Math.sin(k * TAU) * 2, -18 - k * 12, cor.C[6], { font: "mini", a: 1 - k * k });
}
