import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";
import { item } from "./_itens.js";

export const meta = {
  name: "Rato andando",
  desc: "O rato passeia sem pressa, patas em diagonal, cabeça balançando. Com item, leva a coisa pendurada na boca.",
  tags: ["critter", "rat", "pet", "walk", "carry", "loop"],
  ...TELA,
  duration: 0.8,
  loop: true,
  fps: 15,
  bg: "dark",
  options: { ...OPCOES, item: "" },
};

/** Passo de caminhada: pares em diagonal, pé no alto só na metade do caminho para a frente. */
function passo(fase) {
  const pata = (x, off) => {
    const a = (fase + off) * TAU;
    return [x + Math.cos(a) * 3.5, -Math.max(0, Math.sin(a)) * 2];
  };
  return [pata(-7, 0.5), pata(-6, 0), pata(5, 0), pata(6, 0.5)];
}

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, a = f * TAU * 2;
  const sobe = Math.round(Math.abs(Math.sin(a)) * 1);
  const cab = Math.round(Math.sin(a) * 0.7);
  rato(p, cor, {
    x: 0, y: -sobe, pes: passo(f), cauda: cauda(f, 0.9), cabeca: [o.item ? 1 : 0, cab], orelha: 0,
    boca: o.item ? 1 : 0,
  });
  if (o.item) item(p, o.item, 13, -6 - sobe + cab, {});
}
