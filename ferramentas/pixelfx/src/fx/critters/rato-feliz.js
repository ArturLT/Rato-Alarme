import { hex, TAU } from "../../core/index.js";
import { OPCOES, TELA, cores } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";

export const meta = {
  name: "Rato feliz",
  desc: "Depois do carinho, o rato dá pulinhos sentado com os olhos fechados de alegria e corações subindo.",
  tags: ["critter", "rat", "pet", "happy", "love", "loop"],
  ...TELA,
  duration: 1.2,
  loop: true,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const CORACAO = ["#7a1030", "#e03858", "#ff8aa0"].map(hex);
const FORMA = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."];

function coracao(p, x, y, a) {
  FORMA.forEach((linha, j) => [...linha].forEach((ch, i) => {
    if (ch !== "#") return;
    const c = j === 0 || i === 0 ? CORACAO[2] : i > 4 || j > 3 ? CORACAO[0] : CORACAO[1];
    p.dot(Math.round(x) + i - 3, Math.round(y) + j - 3, c, a);
  }));
}

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  const pulo = Math.max(0, Math.sin(f * TAU * 2)) * 3;
  ratoSentado(p, cor, {
    y: -Math.round(pulo),
    respira: Math.sin(f * TAU * 2),
    olho: "feliz",
    boca: 0.7,
    orelha: pulo > 1.5 ? 1 : 0,
    cauda: caudaChao(f * 2, 1.6),
  });
  for (let i = 0; i < 3; i++) {
    const k = (f + i / 3) % 1;
    coracao(p, 12 + Math.sin((k + i) * TAU) * 3 - i * 6, -30 - k * 12, 1 - k * k);
  }
}
