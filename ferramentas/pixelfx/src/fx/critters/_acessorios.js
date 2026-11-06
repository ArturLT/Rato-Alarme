// Acessórios para vestir o rato: chapéus, cabelos, coisas do rosto e do pescoço.
// Cada um é um desenhinho em texto com o ponto de encaixe marcado. O app cola o desenho no ponto que o
// rato marca em cada quadro (topo da cabeça, olho ou pescoço), na vista certa: lado, frente ou costas.
// O cabelo usa as cores CABELO, que o app troca pela cor escolhida.

import { hex } from "../../core/index.js";

export const CABELO = ["#ff0010", "#ff0020", "#ff0030", "#ff0040"];

const K = "#17121c";
// Cada peça: { slot, nome, lado, frente, costas? } com arte em linhas; "@" é o ponto de encaixe
// (fica com a cor da letra que estaria ali: use "@" só onde for transparente, ou "A" etc. com encaixe no
// campo ancora). costas: false some de costas; omitido usa a arte de frente.
export const PECAS = {
  // ---------- chapéus (encaixe: topo da cabeça) ----------
  bone: {
    slot: "chapeu", nome: "Boné",
    cores: { k: K, r: "#d03838", R: "#ff6a5a", d: "#8a1c2c", w: "#fff4e6" },
    lado: [
      "..kkkkk.....",
      ".kRRRrrk....",
      "kRrrrrrrk...",
      "krrwrrrrdkkk",
      "kdddddddddrk",
      ".kkkkkkk.kk.",
    ],
    ancora: [5, 5],
    frente: [
      "..kkkkkk..",
      ".kRRRrrrk.",
      "kRrrwwrrdk",
      "krrrrrrrdk",
      "kddddddddk",
      ".kkkkkkkk.",
    ],
    ancoraFrente: [5, 5],
  },
  cartola: {
    slot: "chapeu", nome: "Cartola",
    cores: { k: K, b: "#2a2238", B: "#4a3f5c", r: "#c03050" },
    lado: [
      ".kkkkkk.",
      ".kBbbbk.",
      ".kBbbbk.",
      ".kBbbbk.",
      ".krrrrk.",
      "kkkkkkkk",
      "kbbbbbbk",
      "kkkkkkkk",
    ],
    ancora: [4, 7],
    frente: [
      "..kkkkkk..",
      "..kBbbbk..",
      "..kBbbbk..",
      "..kBbbbk..",
      "..krrrrk..",
      "kkkkkkkkkk",
      "kbbbbbbbbk",
      "kkkkkkkkkk",
    ],
    ancoraFrente: [5, 7],
  },
  festa: {
    slot: "chapeu", nome: "Chapéu de festa",
    cores: { k: K, a: "#ffd23a", b: "#3a8cff", c: "#ff4f8b", w: "#ffffff" },
    lado: [
      "...w...",
      "..kak..",
      "..kbk..",
      ".kcaak.",
      ".kbbck.",
      "kaacbbk",
      "kkkkkkk",
    ],
    ancora: [3, 6],
  },
  coroa: {
    slot: "chapeu", nome: "Coroa",
    cores: { k: "#5a3008", g: "#f0b020", G: "#ffe070", r: "#e03050", b: "#3a8cff" },
    lado: [
      "k..k..k..",
      "kGkGkGkGk",
      "kgggggggk",
      "kgrgggbgk",
      "kgggggggk",
      "kkkkkkkkk",
    ],
    ancora: [4, 5],
  },
  gorro: {
    slot: "chapeu", nome: "Gorro",
    cores: { k: K, a: "#3a8cff", A: "#7ab8ff", w: "#fff4e6", W: "#d6cabf" },
    lado: [
      "....kk...",
      "...kwwk..",
      "..kkWWk..",
      ".kAAaak..",
      "kAaaaaak.",
      "kAaaaaaak",
      "kwWwWwWwk",
      "kkkkkkkkk",
    ],
    ancora: [4, 7],
  },
  bruxo: {
    slot: "chapeu", nome: "Chapéu de bruxo",
    cores: { k: K, p: "#5a2d8c", P: "#8a5ac8", y: "#ffe070" },
    lado: [
      "....kk....",
      "...kPk....",
      "...kPpk...",
      "..kPpyk...",
      "..kPppk...",
      ".kPpppyk..",
      ".kPppppk..",
      "kkkkkkkkkk",
      "kppppppppk",
      "kkkkkkkkkk",
    ],
    ancora: [5, 9],
  },
  palha: {
    slot: "chapeu", nome: "Chapéu de palha",
    cores: { k: "#5a3a10", y: "#e8c060", Y: "#ffe08a", r: "#c03050" },
    lado: [
      "...kkkkk....",
      "..kYyyyyk...",
      "..kyyyyyk...",
      "..krrrrrk...",
      "kkyyyyyyykkk",
      "kYyyyyyyyyyk",
      ".kkkkkkkkkk.",
    ],
    ancora: [6, 6],
  },
  viking: {
    slot: "chapeu", nome: "Capacete viking",
    cores: { k: K, m: "#8a94a8", M: "#c8d0dc", w: "#fff4e6", W: "#d6cabf" },
    lado: [
      "k.........k",
      "Wk.kkkkk.kW",
      "wWkMMmmmkWw",
      ".kMMmmmmmk.",
      ".kmmMmmmmk.",
      ".kkkkkkkkk.",
    ],
    ancora: [5, 5],
  },
  flor: {
    slot: "chapeu", nome: "Florzinha",
    cores: { k: "#3a0a1a", p: "#f05070", P: "#ffb0c0", y: "#ffe070", g: "#58a038" },
    lado: [
      ".kkk.",
      "kPpPk",
      "kpypk",
      "kPpPk",
      ".kgk.",
    ],
    ancora: [2, 4],
  },
  // ---------- cabelos (encaixe: topo da cabeça) ----------
  topete: {
    slot: "cabelo", nome: "Topete",
    cores: { k: K, a: CABELO[0], b: CABELO[1], c: CABELO[2], d: CABELO[3] },
    lado: [
      "....kkk..",
      "..kkdddk.",
      ".kcdddcck",
      "kbccccbk.",
      "kbbbbbk..",
    ],
    ancora: [4, 4],
    frente: [
      "...kkkk...",
      ".kkddddk..",
      "kcddddcckk",
      "kbccccbbbk",
      ".kbbbbbbk.",
    ],
    ancoraFrente: [5, 4],
  },
  moicano: {
    slot: "cabelo", nome: "Moicano",
    cores: { k: K, a: CABELO[0], b: CABELO[1], c: CABELO[2], d: CABELO[3] },
    lado: [
      ".k.k.k.k..",
      "kdkdkdkdk.",
      "kcdcdcdck.",
      "kbcbcbcbk.",
      ".kbbbbbk..",
    ],
    ancora: [4, 4],
    frente: [
      ".kk.",
      "kddk",
      "kcdk",
      "kcck",
      "kbck",
      "kbbk",
    ],
    ancoraFrente: [2, 5],
  },
  franja: {
    slot: "cabelo", nome: "Franja",
    cores: { k: K, a: CABELO[0], b: CABELO[1], c: CABELO[2], d: CABELO[3] },
    lado: [
      "..kkkkkk..",
      ".kddddddk.",
      "kcdccccdck",
      "kbcbbbbcbk",
      ".kbk.kbbk.",
      "..k...kbk.",
      "........k.",
    ],
    ancora: [4, 3],
    frente: [
      "..kkkkkk..",
      ".kddddddk.",
      "kcdccccdck",
      "kbcbbbbcbk",
      "kbkbbkbkbk",
      ".k.kk.k.k.",
    ],
    ancoraFrente: [5, 3],
  },
  cachos: {
    slot: "cabelo", nome: "Cachinhos",
    cores: { k: K, a: CABELO[0], b: CABELO[1], c: CABELO[2], d: CABELO[3] },
    lado: [
      "..kk.kk...",
      ".kdckdckk.",
      "kdcbkcbdck",
      "kcbkdcbcbk",
      ".kbkcbkbk.",
      "..k.kk.k..",
    ],
    ancora: [4, 4],
    frente: [
      ".kk.kk.kk.",
      "kdckdckdck",
      "kcbkcbkcbk",
      "kbkdcbkbbk",
      ".k.kbk.kk.",
    ],
    ancoraFrente: [5, 4],
  },
  rabo: {
    slot: "cabelo", nome: "Rabo de cavalo",
    cores: { k: K, a: CABELO[0], b: CABELO[1], c: CABELO[2], d: CABELO[3], r: "#e03050" },
    lado: [
      ".....kkkkk..",
      "kkk.kdddddk.",
      "kdckrkccccdk",
      "kccbrkbbbbck",
      ".kbbk.kkkkk.",
      "..kk........",
    ],
    ancora: [8, 4],
    frente: [
      "..kkkkkk..",
      ".kddddddk.",
      "kcdccccdck",
      "kbbbbbbbbk",
      ".kkkkkkkk.",
    ],
    ancoraFrente: [5, 4],
  },
  // ---------- rosto (encaixe: olho) ----------
  oculos: {
    slot: "rosto", nome: "Óculos",
    cores: { k: K, w: "#cfe8ff" },
    lado: [
      "kkkkk",
      "k.wwk",
      "kkkkk",
    ],
    ancora: [2, 1],
    frente: [
      "kkkk.kkkk",
      "kwwkkkwwk",
      "kkkk.kkkk",
    ],
    ancoraFrente: [4, 1],
    costas: false,
  },
  escuros: {
    slot: "rosto", nome: "Óculos escuros",
    cores: { k: K, b: "#2a2238", w: "#6f7a94" },
    lado: [
      "kkkkkk",
      "kbbbwk",
      ".kbbk.",
    ],
    ancora: [2, 1],
    frente: [
      "kkkkkkkkkk",
      "kbbwkkbbwk",
      ".kbk..kbk.",
    ],
    ancoraFrente: [4, 1],
    costas: false,
  },
  monoculo: {
    slot: "rosto", nome: "Monóculo",
    cores: { k: "#5a3008", g: "#f0b020", w: "#cfe8ff" },
    lado: [
      ".ggg.",
      "gwwwg",
      "gw.wg",
      ".ggg.",
      "...g.",
      "...g.",
    ],
    ancora: [2, 2],
    frente: [
      ".ggg.",
      "gwwwg",
      "gw.wg",
      ".ggg.",
      "...g.",
    ],
    ancoraFrente: [2, 2],
    costas: false,
  },
  tapaolho: {
    slot: "rosto", nome: "Tapa-olho",
    cores: { k: K, b: "#17121c" },
    lado: [
      "k.....",
      ".kkkk.",
      "kkbbbk",
      ".kbbk.",
    ],
    ancora: [3, 2],
    frente: [
      "kkk......k",
      "..kkkkkkk.",
      ".kbbbk....",
      "..kbk.....",
    ],
    ancoraFrente: [3, 2],
    costas: false,
  },
  bigode: {
    slot: "rosto", nome: "Bigodão",
    cores: { k: K, b: "#3a2a20", B: "#6a4a30" },
    lado: [
      "....kk.k",
      "..kkBbkb",
      ".kbbbbbk",
      ".k.kkkk.",
    ],
    ancora: [1, -2],
    frente: [
      ".kk...kk.",
      "kBbk.kbBk",
      "kbbbkbbbk",
      ".kk...kk.",
    ],
    ancoraFrente: [4, -2],
    costas: false,
  },
  // ---------- pescoço (encaixe: pescoço) ----------
  gravata: {
    slot: "pescoco", nome: "Gravata",
    cores: { k: K, r: "#d03838", R: "#ff6a5a" },
    lado: [
      "kkk",
      "kRk",
      "krk",
      "kRrk",
      "krrk",
      ".kk.",
    ],
    ancora: [1, 0],
    frente: [
      ".kkk.",
      ".kRk.",
      ".krk.",
      "kRrrk",
      "krrrk",
      ".krk.",
      "..k..",
    ],
    ancoraFrente: [2, 0],
    costas: false,
  },
  borboleta: {
    slot: "pescoco", nome: "Gravata-borboleta",
    cores: { k: K, r: "#d03838", R: "#ff6a5a" },
    lado: [
      "kk.kk",
      "kRkRk",
      "krkrk",
      "kk.kk",
    ],
    ancora: [2, 1],
    frente: [
      "kk...kk",
      "kRk.kRk",
      "krrkrrk",
      "kRk.kRk",
      "kk...kk",
    ],
    ancoraFrente: [3, 2],
    costas: false,
  },
  cachecol: {
    slot: "pescoco", nome: "Cachecol",
    cores: { k: K, a: "#3aa060", b: "#ffe070", A: "#6ad090" },
    lado: [
      ".kkkkkk.",
      "kAaAbAak",
      "kaabaabk",
      ".kkkkbak",
      "....kaak",
      "....kbak",
      "....kkk.",
    ],
    ancora: [4, 1],
    frente: [
      "kkkkkkkkk",
      "kAaAbAaAk",
      "kaabaabak",
      "kkkkkbakk",
      "....kaak.",
      "....kbak.",
      "....kkk..",
    ],
    ancoraFrente: [4, 1],
  },
  colar: {
    slot: "pescoco", nome: "Colar de pérolas",
    cores: { k: "#3a3440", w: "#ffffff", W: "#e8e4ee" },
    lado: [
      "w.....",
      "Ww...w",
      ".WwwW.",
    ],
    ancora: [3, 1],
    frente: [
      "w.....w",
      "Ww...wW",
      ".WwwwW.",
      "...k...",
    ],
    ancoraFrente: [3, 1],
    costas: false,
  },
  sino: {
    slot: "pescoco", nome: "Coleira com sino",
    cores: { k: K, r: "#d03838", g: "#f0b020", G: "#ffe070" },
    lado: [
      "kkkkkkk",
      "rrrrrrk",
      "kkkGkkk",
      "...gg..",
      "..kgGk.",
      "..kkkk.",
    ],
    ancora: [3, 1],
    frente: [
      "kkkkkkkkk",
      "krrrrrrrk",
      "kkkkGkkkk",
      "...kggk..",
      "...kgGk..",
      "....kk...",
    ],
    ancoraFrente: [4, 1],
    costas: false,
  },
  laco: {
    slot: "pescoco", nome: "Laço",
    cores: { k: "#5a1030", p: "#ff6aa0", P: "#ffb0c8" },
    lado: [
      "kk.kk",
      "kPkPk",
      "kpkpk",
      "kk.kk",
      ".k.k.",
    ],
    ancora: [2, 1],
    frente: [
      "kk...kk",
      "kPkkkPk",
      "kppkppk",
      "kk.k.kk",
      ".k...k.",
    ],
    ancoraFrente: [3, 1],
    costas: false,
  },
};

/** Desenha a peça com o encaixe em (x, y). vista: "lado", "frente" ou "costas". */
export function peca(p, id, vista, x, y, fade = 1) {
  const pc = PECAS[id];
  if (!pc) return;
  let arte = pc.lado, ancora = pc.ancora;
  if (vista !== "lado") {
    if (vista === "costas" && pc.costas === false) return;
    if (pc.frente) (arte = pc.frente), (ancora = pc.ancoraFrente ?? pc.ancora);
  }
  const cores = Object.fromEntries(Object.entries(pc.cores).map(([k, v]) => [k, hex(v)]));
  arte.forEach((linha, j) => [...linha].forEach((ch, i) => {
    if (ch === "." || !cores[ch]) return;
    p.dot(Math.round(x) + i - ancora[0], Math.round(y) + j - ancora[1], cores[ch], fade);
  }));
}
