import { hex, TAU } from "../../core/index.js";
import { item, migalhas } from "./_itens.js";

export const meta = {
  name: "Objeto do rato",
  desc: "Uma coisa que o rato largou na tela: queijo, meia, bilhete, moeda brilhando ou flor, parada no chão.",
  tags: ["critter", "rat", "pet", "item", "loop"],
  size: [24, 24],
  origin: [12, 20],
  duration: 1.6,
  loop: true,
  fps: 10,
  bg: "dark",
  options: { item: "queijo", seed: 1 },
};

const SOMBRA = hex("#000000");

export function draw(p, t, o) {
  const f = t / meta.duration;
  if (o.item === "migalhas") {
    migalhas(p, [[-5, 0, 0], [-2, -1, 1], [0, 0, 2], [3, 0, 1], [5, -1, 0], [1, -2, 2], [-3, 0, 2]]);
    return;
  }
  if (o.item === "pegadas") {
    const pe = [[0, 0], [2, -1], [-1, -2], [1, -3], [3, -2]];
    for (const [bx, by] of [[-7, 0], [-1, -5], [5, -1]]) for (const [dx, dy] of pe) p.px(bx + dx, by + dy, hex("#6a5a70"));
    return;
  }
  const altura = { queijo: 7, meia: 11, bilhete: 8, moeda: 9, flor: 11 }[o.item] ?? 8;
  for (let x = -5; x <= 5; x++) p.dot(x, 1, SOMBRA, 0.35);
  item(p, o.item, 0, -altura + 1 - (o.item === "moeda" ? Math.round(Math.sin(f * TAU)) : 0), { brilho: f < 0.25 ? 1 : 0 });
}
