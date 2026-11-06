import { TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato falando",
  desc: "O rato sentado conversa: a boca abre e fecha, a cabeça acompanha as sílabas e ele pisca no meio.",
  tags: ["critter", "rat", "pet", "talk", "loop"],
  ...TELA,
  duration: 1.2,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

// sílabas: quanto a boca abre em cada sexto do ciclo
const SILABAS = [1, 0.3, 0.9, 0, 0.7, 0.2];

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  const s = SILABAS[Math.floor(f * SILABAS.length) % SILABAS.length];
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU),
    boca: s,
    olho: f > 0.78 && f < 0.85 ? "fechado" : "aberto",
    cabeca: [Math.round(s * 0.6), -Math.round(s)],
    cauda: caudaChao(f, 1.2),
  });
}
