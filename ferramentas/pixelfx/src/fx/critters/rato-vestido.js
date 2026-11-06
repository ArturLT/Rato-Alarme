// Só para conferir os acessórios no rato (o app faz essa montagem sozinho). Não é exportado.
import { OPCOES, TELA, cauda, cores, galope, rato, ratoCostas, ratoFrente } from "./_rato.js";
import { caudaChao, ratoSentado } from "./_rato-sentado.js";
import { ANCORAS } from "./_ancoras.js";
import { peca } from "./_acessorios.js";

export const meta = {
  name: "Rato vestido (prévia)",
  desc: "Prévia dos acessórios encaixados no rato, em várias poses.",
  tags: ["critter", "rat", "preview"],
  ...TELA,
  duration: 1,
  loop: true,
  fps: 5,
  bg: "dark",
  options: { ...OPCOES, pose: "sentado", pecas: [] },
};

export function draw(p, t, o) {
  const cor = cores(o), f = t / meta.duration;
  if (o.pose === "sentado") ratoSentado(p, cor, { cauda: caudaChao(f, 1) });
  else if (o.pose === "correndo") rato(p, cor, { x: 2, pes: galope(f), cauda: cauda(f * 2, 1.4), orelha: 1 });
  else if (o.pose === "costas") ratoCostas(p, cor, f);
  else ratoFrente(p, cor, f);
  const a = ANCORAS.pontos;
  for (const id of o.pecas) {
    const onde = { chapeu: a.topo, cabelo: a.topo, rosto: a.olho, pescoco: a.pescoco };
    const slot = id.split(":")[0], nome = id.split(":")[1];
    const q = onde[slot];
    if (q) peca(p, nome, a.vista, q[0], q[1]);
  }
}
