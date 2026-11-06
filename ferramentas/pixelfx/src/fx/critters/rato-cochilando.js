import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato cochilando",
  desc: "O rato dorme encolhido no chão, fora da gaiola, com a barriga subindo e descendo e zzz flutuando.",
  tags: ["critter", "rat", "pet", "sleep", "loop"],
  ...TELA,
  duration: 2.4,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, ar = Math.sin(f * TAU);
  rato(p, cor, {
    x: 0, y: 0, sq: -0.12 + ar * 0.05, olho: "fechado", cabeca: [-1, 4], orelha: 1,
    pes: [[-7, 0], [-5, 0], [3, 0], [5, 0]], cauda: cauda(0, 0.2),
  });
  for (let i = 0; i < 2; i++) {
    const k = (f + i / 2) % 1;
    p.text("z", 10 + i * 2 + Math.sin(k * TAU) * 2, -16 - k * 14, cor.C[6], { font: "mini", a: 1 - k * k });
  }
}
