import { hex, rng, seg, sparkle, TAU, WHITE } from "../../core/index.js";
import { toss } from "./_lib.js";
import { OPCOES, TELA, cauda, cores, galope, gaiolaFrente, gaiolaFundo, rato } from "./_rato.js";

export const meta = {
  name: "Rato fuga",
  desc: "O rato acorda assustado, sacode a gaiola, arrebenta a porta, salta para fora e a gaiola se desfaz em poeira.",
  tags: ["critter", "rat", "cage", "escape"],
  ...TELA,
  duration: 3,
  loop: false,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const ACORDA = 0.45, BATIDAS = [0.75, 1.05, 1.35], ABRE = 1.35, SALTO = 1.5, POUSO = 2, SOME = 2.1, FIM = 2.9;
const POEIRA = hex("#8a7f92");

export function draw(p, t, o) {
  const cor = cores(o);
  if (t >= FIM + 0.05) return;
  let shake = 0;
  for (const b of BATIDAS) if (t >= b && t < b + 0.16) shake = (Math.floor((t - b) * 15) % 2 ? -2 : 2);
  const a = 1 - seg(t, SOME, SOME + 0.5);
  const solta = t >= ABRE;

  if (a > 0) gaiolaFundo(p, cor, { dx: shake, a });
  if (t < SALTO) {
    const investe = BATIDAS.reduce((m, b) => Math.max(m, 1 - Math.abs(t - b) / 0.14), 0);
    rato(p, cor, {
      x: -1 + (t > ACORDA ? Math.max(0, investe) * 6 : 0), y: t < ACORDA ? -3 : -3,
      sq: t < ACORDA ? -0.1 : 0, olho: t < ACORDA ? "fechado" : "arregalado",
      cabeca: t < ACORDA ? [-1, 4] : [0, 0], orelha: t < ACORDA ? 1 : 0,
      cauda: cauda(t * 3, t < ACORDA ? 0 : 1),
    });
  }
  if (a > 0) gaiolaFrente(p, cor, { dx: shake, a, porta: !solta });

  if (t >= ACORDA && t < ACORDA + 0.3) p.text("!", 8, -30, hex("#ffe27a"), { font: "big", outline: cor.C[0] });
  if (t >= ABRE && t < ABRE + 0.14) sparkle(p, 12, -15, 8, WHITE, hex("#ffe27a"), 0.35);

  // a porta sai voando e girando
  if (solta) {
    const age = t - ABRE, b = toss(12, -15, 60, -120, age, 520, 0), ang = age * 11;
    if (age < 0.8 && a > 0) {
      const dx = Math.cos(ang) * 8, dy = Math.sin(ang) * 8;
      p.line(b.x - dx, b.y - dy, b.x + dx, b.y + dy, cor.M[3]);
      p.line(b.x - dx, b.y - dy + 1, b.x + dx, b.y + dy + 1, cor.M[2]);
    }
    for (let i = 0; i < 8; i++) {
      const r = rng(o.seed, i, 77), s = toss(13, -15, r.range(-70, 90), -r.range(40, 130), age, 480, 0);
      if (age < 0.5) p.dot(s.x, s.y, i % 2 ? cor.M[4] : hex("#ffe27a"), 1);
    }
  }
  // o salto, por cima de tudo, até parar de frente no chão
  if (t >= SALTO) {
    const u = seg(t, SALTO, POUSO), voo = t < POUSO;
    const age = t - POUSO;
    rato(p, cor, {
      x: 6 - 6 * u, y: voo ? -13 * 4 * u * (1 - u) + (1 - u) * -3 : 0,
      rot: voo ? -0.35 + u * 0.6 : 0, sq: !voo && age < 0.2 ? -0.22 * (1 - age / 0.2) : 0,
      pes: voo ? galope(0.3) : undefined, olho: voo ? "arregalado" : "aberto", cauda: cauda(t * 2, 1.2),
    });
  }
  // a poeira que leva a gaiola embora
  if (t >= SOME) {
    const age = t - SOME;
    for (let i = 0; i < 12; i++) {
      const r = rng(o.seed, i, 31), L = r.range(0.4, 0.75);
      if (age > L) continue;
      const an = r.range(0, TAU), k = age / L, d = 6 + k * r.range(8, 16);
      p.disc(Math.cos(an) * d * 1.3, -18 + Math.sin(an) * d - k * 5, r.range(2, 4.5) * (1 - k * 0.5), POEIRA, 0.55 * (1 - k));
    }
    if (age < 0.15) sparkle(p, 0, -18, 7, WHITE, cor.M[4], 0.4);
  }
}
