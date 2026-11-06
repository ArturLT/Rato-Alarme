import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, rato } from "./_rato.js";

export const meta = {
  name: "Rato puxando",
  desc: "O rato morde algo à frente e anda de ré, inclinado para trás, fincando as patas para arrastar.",
  tags: ["critter", "rat", "pet", "pull", "drag", "loop"],
  ...TELA,
  duration: 0.5,
  loop: true,
  fps: 16,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  const pata = (x, off) => {
    const a = -(f + off) * TAU;
    return [x + Math.cos(a) * 3, -Math.max(0, Math.sin(a)) * 1.5];
  };
  rato(p, cor, {
    x: -1, rot: -0.14 + Math.sin(f * TAU * 2) * 0.03, sq: -0.04, boca: 1, olho: "fechado",
    pes: [pata(-8, 0.5), pata(-7, 0), pata(4, 0), pata(5, 0.5)], cauda: cauda(f * 2, 1.6),
    cabeca: [1, 1], orelha: 1,
  });
}
