/**
 * Painel "Como funciona a pontuação": explica ao vendedor, sem jargão,
 * de onde vem a nota de cada negócio e o que significa cada prioridade.
 *
 * Os números (pesos, prazos, faixas) vêm da API (/api/regras), então
 * este texto se atualiza sozinho quando alguém muda backend/app/config.py.
 */

import { useEffect, useState } from "react";

import { api } from "../api/cliente";
import type { RegrasPontuacao } from "../tipos";
import { formatarMoeda, formatarPorcentagem } from "../utils/formatadores";
import SeloPrioridade from "./SeloPrioridade";

interface Props {
  aoFechar: () => void;
}

export default function ComoFunciona({ aoFechar }: Props) {
  const [regras, setRegras] = useState<RegrasPontuacao | null>(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    api.regras().then(setRegras).catch(() => setErro(true));
  }, []);

  // Fecha com a tecla Esc.
  useEffect(() => {
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [aoFechar]);

  return (
    <div className="fundo-painel" onClick={aoFechar}>
      <aside className="painel" onClick={(e) => e.stopPropagation()} aria-label="Como funciona a pontuação">
        <button className="botao-fechar" onClick={aoFechar} aria-label="Fechar">
          ×
        </button>
        <h2>Como funciona a pontuação</h2>

        {erro && <p className="aviso-erro">Não foi possível carregar as regras.</p>}
        {!regras && !erro && <p>Carregando…</p>}

        {regras && (
          <>
            <p className="introducao">
              Cada negócio aberto recebe uma nota de <strong>0 a 100</strong>, que é a soma de três partes.
              A nota compara o negócio com o histórico de negócios já ganhos e perdidos.
            </p>

            <div className="regras-fator">
              <h4>
                <span>Chance de fechar</span>
                <span>até {regras.pontos_maximos.chance} pts</span>
              </h4>
              <p>
                Olhamos quantas vezes negócios parecidos foram ganhos: mesmo produto, mesmo vendedor, mesmo
                setor e mesma conta. Na média, a empresa ganha {formatarPorcentagem(regras.taxa_vitoria_geral)}{" "}
                dos negócios. Quem tem chance melhor que a dos outros negócios abertos ganha mais pontos.
              </p>
            </div>

            <div className="regras-fator">
              <h4>
                <span>Valor do negócio</span>
                <span>até {regras.pontos_maximos.valor} pts</span>
              </h4>
              <p>
                Quanto mais caro o produto, mais pontos. Os preços vão de {formatarMoeda(regras.preco_minimo)} a{" "}
                {formatarMoeda(regras.preco_maximo)}.
              </p>
            </div>

            <div className="regras-fator">
              <h4>
                <span>Ritmo da negociação</span>
                <span>até {regras.pontos_maximos.tempo} pts</span>
              </h4>
              <p>
                Negócios ganhos costumam fechar em <strong>{regras.ciclo_mediano_dias} dias</strong>. Até{" "}
                {regras.ciclo_normal_dias} dias de negociação o negócio ganha todos os pontos. Depois disso ele
                começa a <strong>esfriar</strong> e perde pontos, até zerar com {regras.ciclo_limite_dias} dias,
                prazo que quase nenhum negócio ganho ultrapassou. Negócios em prospecção ganham metade dos pontos.
              </p>
            </div>

            <h3>O que a nota significa</h3>
            <div className="regras-faixas">
              <div>
                <SeloPrioridade prioridade="Alta" />
                <span>{regras.limite_alta} pontos ou mais: foque nestes primeiro.</span>
              </div>
              <div>
                <SeloPrioridade prioridade="Média" />
                <span>
                  De {regras.limite_media} a {regras.limite_alta - 1} pontos: acompanhe regularmente.
                </span>
              </div>
              <div>
                <SeloPrioridade prioridade="Baixa" />
                <span>Menos de {regras.limite_media} pontos: dedique tempo depois dos prioritários.</span>
              </div>
            </div>

            <h3>Como ler um negócio</h3>
            <p className="introducao">
              Em cada cartão aparece o <strong>principal motivo</strong> da nota: o ponto forte (▲) nos negócios
              de prioridade alta e o que mais tirou pontos (▼) nos demais. Clique no negócio para ver os pontos de
              cada parte e o que fazer.
            </p>
          </>
        )}
      </aside>
    </div>
  );
}
