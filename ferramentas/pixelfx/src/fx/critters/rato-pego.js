import { hex, rng, seg, sparkle, TAU, WHITE } from "../../core/index.js";
import { OPCOES, TELA, cauda, cores, gaiolaFrente, gaiolaFundo, rato, tontura } from "./_rato.js";

export const meta = {
  name: "Rato pego",
  desc: "O rato fica tonto com estrelas na cabeça, a gaiola cai do alto sobre ele com um baque e ele se encolhe.",
  tags: ["critter", "rat", "cage", "caught"],
  ...TELA,
  duration: 2,
  loop: false,
  fps: 15,
  bg: "dark",
  options: OPCOES,
};

const QUEDA = 0.8, BAQUE = 1.15, FIM = 1.95;

export function draw(p, t, o) {
  const cor = cores(o);
  if (t >= FIM) return;
  const u = seg(t, QUEDA, BAQUE), caiu = t >= BAQUE, age = t - BAQUE;
  const dy = t < QUEDA ? -80 : caiu ? 0 : -80 * (1 - u * u);
  const tremor = caiu && age < 0.2 ? (Math.floor(age * 15) % 2 ? 1 : -1) : 0;
  const quieto = seg(t, BAQUE + 0.3, FIM);

  if (t >= QUEDA) {
    gaiolaFundoEm(p, cor, dy, tremor);
  }
  rato(p, cor, {
    x: -quieto, y: -3 * quieto, sq: caiu ? -0.16 * (1 - seg(age, 0, 0.3)) - 0.1 * quieto : 0,
    olho: quieto > 0.6 ? "fechado" : "x", cabeca: [-quieto, 2 + 2 * quieto], orelha: 1,
    cauda: cauda(0, 0),
  });
  if (t < BAQUE + 0.3) tontura(p, cor, 9, -19, t * 1.8);
  if (t >= QUEDA) gaiolaFrenteEm(p, cor, dy, tremor);

  if (caiu && age < 0.5) {
    for (let i = 0; i < 10; i++) {
      const r = rng(o.seed, i, 41), s = r.sign(), k = age / 0.5;
      p.disc(s * (16 + k * r.range(4, 9)), -2 - k * r.range(1, 5), r.range(1.5, 3) * (1 - k * 0.4), hex("#8a7f92"), 0.55 * (1 - k));
    }
    if (age < 0.08) sparkle(p, 0, -2, 9, WHITE, cor.M[4], 0.4);
  }
}

function gaiolaFundoEm(p, cor, dy, dx) {
  const q = deslocado(p, dy);
  gaiolaFundo(q, cor, { dx });
}
function gaiolaFrenteEm(p, cor, dy, dx) {
  const q = deslocado(p, dy);
  gaiolaFrente(q, cor, { dx });
}
// um painter que desce tudo em dy, para a gaiola cair sem duplicar o desenho dela
function deslocado(p, dy) {
  return {
    line: (x0, y0, x1, y1, c, a) => p.line(x0, y0 + dy, x1, y1 + dy, c, a),
    dot: (x, y, c, a) => p.dot(x, y + dy, c, a),
  };
}
