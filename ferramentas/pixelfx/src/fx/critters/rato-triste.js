import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato triste",
  desc: "O rato sentado e cabisbaixo, orelha caída, respirando devagar, com uma lágrima escorrendo de vez em quando.",
  tags: ["critter", "rat", "pet", "sad", "loop"],
  ...TELA,
  duration: 2.4,
  loop: true,
  fps: 12,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU) * 0.6,
    olho: "triste",
    orelha: 1,
    cabeca: [-1, 3],
    cauda: caudaChao(0, 0.2),
    lagrima: f < 0.7 ? f / 0.7 : -1,
  });
}
