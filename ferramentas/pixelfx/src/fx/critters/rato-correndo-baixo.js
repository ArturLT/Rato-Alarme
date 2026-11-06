import { OPCOES, TELA, cores, ratoFrente } from "./_rato.js";

export const meta = {
  name: "Rato correndo baixo",
  desc: "O rato corre para baixo, visto de frente, com os dentes à mostra.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoFrente(p, cores(o), t / meta.duration);
}
