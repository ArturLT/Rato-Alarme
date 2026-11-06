import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato reclamando",
  desc: "O rato reclama sem parar: a boca abre e fecha em sílabas, a sobrancelha franzida, a pata apontando e a cauda chicoteando.",
  tags: ["critter", "rat", "talk", "loop"],
  ...TELA,
  duration: 1.2,
  loop: true,
  fps: 10,
  bg: "dark",
  options: OPCOES,
};

const SILABAS = [0, 2, 3, 1, 3, 2, 0, 1, 3, 2, 1, 0];

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  const quadro = Math.floor(f * SILABAS.length + 1e-6) % SILABAS.length;
  const fala = SILABAS[quadro], gesto = Math.sin(f * TAU * 3);
  rato(p, cor, {
    fala, olho: "bravo", sq: fala * 0.012,
    cabeca: [0, -fala * 0.35 + gesto * 0.4], orelha: fala > 1 ? 1 : 0,
    pes: [[-8, 0], [-5, 0], [4 + gesto, -2 - gesto * 2], [8, 0]],
    cauda: cauda(f * 3, 1.5),
  });
}
