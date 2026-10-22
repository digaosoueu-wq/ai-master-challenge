/** Números principais do recorte filtrado, no topo da tela. */

import type { Resumo } from "../tipos";
import { formatarMoedaCompacta, formatarNumero, formatarPorcentagem } from "../utils/formatadores";

interface Props {
  resumo: Resumo | null;
}

export default function CartoesResumo({ resumo }: Props) {
  // Enquanto carrega, mostra "–" para manter o layout estável.
  const valor = (texto: string | number) => (resumo ? texto : "–");

  return (
    <section className="cartoes-resumo">
      <div className="cartao-resumo">
        <span className="rotulo">Negócios abertos</span>
        <strong>{valor(formatarNumero(resumo?.total_abertos ?? 0))}</strong>
      </div>
      <div className="cartao-resumo destaque-alta">
        <span className="rotulo">Prioridade alta</span>
        <strong>{valor(resumo?.qtd_prioridade_alta ?? 0)}</strong>
        <span className="dica">Foque nestes primeiro</span>
      </div>
      <div className="cartao-resumo destaque-esfriando">
        <span className="rotulo">Esfriando</span>
        <strong>{valor(formatarNumero(resumo?.qtd_esfriando ?? 0))}</strong>
        <span className="dica">Abertos há mais tempo que o normal</span>
      </div>
      <div className="cartao-resumo">
        <span className="rotulo">Valor esperado</span>
        <strong>{valor(formatarMoedaCompacta(resumo?.valor_esperado_total ?? 0))}</strong>
        <span className="dica">Soma de valor × chance</span>
      </div>
      <div className="cartao-resumo">
        <span className="rotulo">Taxa de vitória</span>
        <strong>{valor(formatarPorcentagem(resumo?.taxa_vitoria ?? 0))}</strong>
        <span className="dica">Histórico de negócios fechados</span>
      </div>
    </section>
  );
}
