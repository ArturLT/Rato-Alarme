import { OPCOES, TELA, cores, ratoCostas } from "./_rato.js";

export const meta = {
  name: "Rato correndo cima",
  desc: "O rato corre para cima, visto de costas, com a cauda balançando.",
  tags: ["critter", "rat", "run", "loop"],
  ...TELA,
  duration: 0.4,
  loop: true,
  fps: 20,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  ratoCostas(p, cores(o), t / meta.duration);
}
