import { hex, TAU } from "../../core/index.js";
import { altura as alturaDe, item, migalhas } from "./_itens.js";

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
const PEDRA = ["#2a2632", "#5a5468", "#8a8498", "#b8b2c4"].map(hex);
const GRAMA = ["#2a5a20", "#58a038"].map(hex);

/** Lápide arredondada com uma cruzinha gravada e grama na base. */
function lapide(p, f) {
  for (let y = -16; y <= 0; y++) for (let x = -6; x <= 6; x++) {
    const topo = y < -11 && (x * x) / 36 + ((y + 11) * (y + 11)) / 25 > 1;
    if (topo) continue;
    const borda = Math.abs(x) === 6 || y === 0 || (y < -11 && (x * x) / 25 + ((y + 11) * (y + 11)) / 16 > 1);
    p.px(x, y, borda ? PEDRA[0] : x < -3 ? PEDRA[3] : x > 3 ? PEDRA[1] : PEDRA[2]);
  }
  for (let y = -12; y <= -5; y++) p.px(0, y, PEDRA[0]);
  for (let x = -2; x <= 2; x++) p.px(x, -10, PEDRA[0]);
  for (let x = -8; x <= 8; x++) p.px(x, 1, GRAMA[(x + 8) % 3 === 0 ? 1 : 0]);
  for (const x of [-7, -3, 4, 7]) p.px(x, 0, GRAMA[1]);
  void f;
}

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
  if (o.item === "lapide") return lapide(p, f);
  const altura = alturaDe(o.item);
  for (let x = -5; x <= 5; x++) p.dot(x, 1, SOMBRA, 0.35);
  item(p, o.item, 0, -altura + 1 - (o.item === "moeda" ? Math.round(Math.sin(f * TAU)) : 0), { brilho: f < 0.25 ? 1 : 0 });
}
