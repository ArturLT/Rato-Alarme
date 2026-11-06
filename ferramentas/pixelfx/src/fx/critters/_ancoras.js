// Pontos de encaixe e máscara da roupa, para o app vestir o rato depois.
// Os desenhos do rato chamam marcar() com os pontos da cabeça; o exportador lê ANCORAS.pontos a cada quadro.
// Com ANCORAS.mascara ligado, o tronco é pintado de MAGENTA: é onde a roupa entra.

import { hex } from "../../core/index.js";

export const MAGENTA = hex("#ff00ff");
export const ANCORAS = { pontos: {}, mascara: false };

/** vista: "lado", "frente" ou "costas". topo: alto da cabeça; olho; pescoco. fade: 0..1. */
export function marcar(vista, topo, olho, pescoco, fade = 1) {
  const r = (q) => (q ? [Math.round(q[0]), Math.round(q[1])] : null);
  ANCORAS.pontos = { vista, topo: r(topo), olho: r(olho), pescoco: r(pescoco), fade };
}

/** Na máscara, o tronco vira magenta; fora dela, fica a cor de sempre. */
export const tronco = (c) => (ANCORAS.mascara ? MAGENTA : c);
