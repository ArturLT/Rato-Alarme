import { rng, TAU, wrap } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";
import { item, migalhas } from "./_itens.js";

export const meta = {
  name: "Rato comendo",
  desc: "O rato sentado segura um queijo na boca com as duas patas e rói rapidinho, soltando farelos.",
  tags: ["critter", "rat", "pet", "eat", "cheese", "loop"],
  ...TELA,
  duration: 0.8,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration, mordida = Math.round((Math.sin(f * TAU * 4) + 1) / 2);
  ratoSentado(p, cor, {
    respira: Math.sin(f * TAU),
    patas: "boca",
    olho: "feliz",
    boca: mordida,
    cabeca: [0, mordida],
    cauda: caudaChao(f, 1),
  });
  item(p, "queijo", 11, -22 + mordida);
  const pts = [];
  for (let i = 0; i < 5; i++) {
    const r = rng(o.seed, i, 7), k = wrap(f * 2 + i / 5, 1);
    pts.push([10 + r.range(-3, 3) + k * r.range(-2, 2), -14 + k * 14, i]);
  }
  migalhas(p, pts);
}
