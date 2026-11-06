import { OPCOES, TELA, cores, ratoFrenteLado } from "./_rato.js";

export const meta = {
  name: "Rato correndo baixo-lado",
  desc: "O rato corre na diagonal para baixo, em três quartos de frente.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoFrenteLado(p, cores(o), t / meta.duration);
}
