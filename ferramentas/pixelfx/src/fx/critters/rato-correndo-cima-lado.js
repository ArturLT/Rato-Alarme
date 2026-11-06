import { OPCOES, TELA, cores, ratoCostasLado } from "./_rato.js";

export const meta = {
  name: "Rato correndo cima-lado",
  desc: "O rato corre na diagonal para cima, em três quartos de costas.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoCostasLado(p, cores(o), t / meta.duration);
}
