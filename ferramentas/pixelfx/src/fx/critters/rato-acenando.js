import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato acenando",
  desc: "O rato sentado dá oi: a pata da frente balança no alto, olhos fechadinhos de alegria e a boca aberta.",
  tags: ["critter", "rat", "pet", "wave", "hello", "loop"],
  ...TELA,
  duration: 0.8,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU),
    patas: "acena",
    braco: 0.5 + Math.sin(f * TAU) * 0.5,
    olho: "feliz",
    boca: 0.8,
    cabeca: [0, Math.round(Math.sin(f * TAU))],
    cauda: caudaChao(f * 2, 1.4),
  });
}
