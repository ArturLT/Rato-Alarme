import { hex, TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato com placa",
  desc: "O rato sentado ergue um cabo de madeira com as duas patas; a placa com o recado fica na ponta, acima do quadro.",
  tags: ["critter", "rat", "pet", "sign", "loop"],
  ...TELA,
  duration: 2.4,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const MADEIRA = ["#3a2010", "#7a4a20", "#b07838"].map(hex);
// O cabo fica parado: a placa de verdade é desenhada pelo app, presa no topo dele.
export const CABO_X = 16;

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  for (let y = -44; y <= -10; y++) {
    p.px(CABO_X, y, MADEIRA[1]);
    p.px(CABO_X + 1, y, MADEIRA[y % 4 === 0 ? 1 : 2]);
    p.px(CABO_X - 1, y, MADEIRA[0]);
    p.px(CABO_X + 2, y, MADEIRA[0]);
  }
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU * 2),
    patas: "segura",
    braco: CABO_X,
    olho: f > 0.5 && f < 0.55 ? "fechado" : "aberto",
    cabeca: [0, 1],
    cauda: caudaChao(f, 1),
  });
}
