import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato sentado",
  desc: "O rato do pet sentado nas patas de trás, respirando, piscando e mexendo a cauda e a orelha.",
  tags: ["critter", "rat", "pet", "idle", "loop"],
  ...TELA,
  duration: 3.2,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  const pisca = (f > 0.62 && f < 0.66) || (f > 0.7 && f < 0.73);
  const orelha = f > 0.2 && f < 0.26 ? 1 : 0;
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU * 2),
    olho: pisca ? "fechado" : "aberto",
    orelha,
    cabeca: [0, Math.round(Math.sin(f * TAU * 2) * 0.6)],
    cauda: caudaChao(f, 1),
  });
}
