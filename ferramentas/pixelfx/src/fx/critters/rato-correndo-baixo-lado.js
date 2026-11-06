import { OPCOES, TELA, cores, ratoCostasLado, virado } from "./_rato.js";

export const meta = {
  name: "Rato correndo baixo-lado",
  desc: "O rato corre na diagonal para baixo: a diagonal para cima espelhada na vertical.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoCostasLado(virado(p), cores(o), t / meta.duration);
}
