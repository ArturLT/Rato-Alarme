// Gera as folhas de sprites do rato com o PixelFX e copia para alarma/folhas.
//   node ferramentas/exportar-folhas.mjs
// Cada entrada: [nome no app, efeito do PixelFX, opções].

import { execFileSync } from "node:child_process";
import { copyFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const PIXELFX = join(AQUI, "pixelfx");
const DESTINO = join(AQUI, "..", "alarma", "folhas");

const ITENS = ["queijo", "meia", "bilhete", "moeda", "flor"];
const FOLHAS = [
  // o alarme
  ...["acerto", "cansado", "correndo", "correndo-baixo", "correndo-baixo-lado", "correndo-cima", "correndo-cima-lado",
    "dormindo", "fuga", "pego", "sumindo"].map((n) => [`rato-${n}`, `critters/rato-${n}`]),
  // o pet
  ...["sentado", "falando", "placa", "acenando", "comendo", "feliz", "cochilando", "andando", "puxando", "surgindo"]
    .map((n) => [`rato-${n}`, `critters/rato-${n}`]),
  ...ITENS.map((i) => [`rato-andando-${i}`, "critters/rato-andando", { item: i }]),
  ...[...ITENS, "migalhas", "pegadas"].map((i) => [`objeto-${i}`, "critters/objeto-tela", { item: i }]),
];

const pasta = mkdtempSync(join(tmpdir(), "folhas-"));
try {
  for (const [nome, efeito, opcoes] of FOLHAS) {
    const saida = join(pasta, nome);
    const args = ["tools/render.mjs", efeito, "--sheet", "--max", "2", "--out", saida];
    if (opcoes) args.push("--opts", JSON.stringify(opcoes));
    execFileSync("node", args, { cwd: PIXELFX, stdio: "ignore" });
    const base = efeito.split("/")[1];
    for (const ext of ["png", "json"]) copyFileSync(join(saida, efeito, `${base}.${ext}`), join(DESTINO, `${nome}.${ext}`));
    console.log(`${nome}  <-  ${efeito}${opcoes ? " " + JSON.stringify(opcoes) : ""}`);
  }
} finally {
  rmSync(pasta, { recursive: true, force: true });
}
