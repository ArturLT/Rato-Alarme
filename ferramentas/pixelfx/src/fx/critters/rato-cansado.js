import { hex, TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato cansado",
  desc: "O rato para ofegante, com a língua de fora, o corpo arfando e uma gota de suor caindo.",
  tags: ["critter", "rat", "tired", "loop"],
  ...TELA,
  duration: 0.8,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, ar = Math.sin(f * TAU * 2);
  rato(p, cor, {
    sq: -0.06 + ar * 0.09, boca: 1, olho: "fechado", cabeca: [0, 1 + ar * 0.7], orelha: 1,
    cauda: cauda(0, 0),
  });
  const k = f;
  for (const [dx, dy, c] of [[0, 0, "#8fd0f0"], [1, 0, "#8fd0f0"], [0, -1, "#d8f2ff"], [0, 1, "#5fa8d0"]]) p.px(5 - k * 6 + dx, -20 + k * k * 8 + dy, hex(c));
}
