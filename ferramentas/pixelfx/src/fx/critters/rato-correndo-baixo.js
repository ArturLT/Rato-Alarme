import { OPCOES, TELA, cores, ratoCostas, virado } from "./_rato.js";

export const meta = {
  name: "Rato correndo baixo",
  desc: "O rato corre para baixo, visto de costas: a corrida para cima espelhada na vertical.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoCostas(virado(p), cores(o), t / meta.duration);
}
