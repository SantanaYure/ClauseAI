"""Monta o documento (lista de blocos) de uma apólice a partir de sua `Spec`."""

from dataclasses import asdict

from .model import STATUS_LABEL, Block, Cov, Spec, Table
from .texts import (
    CLAUSE_4_KEYS,
    CLAUSE_5_KEYS,
    COVERAGE_TEXTS,
    POLLUTION_TEXTS,
)

NBSP = " "


def brl(value: int) -> str:
    formatted = f"{value:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {formatted}"


def days(count: int) -> str:
    words = {15: "quinze", 30: "trinta", 45: "quarenta e cinco", 60: "sessenta", 90: "noventa"}
    return f"{count} ({words.get(count, str(count))}) dias"


def months(count: int) -> str:
    words = {
        3: "três",
        6: "seis",
        12: "doze",
        24: "vinte e quatro",
        36: "trinta e seis",
        60: "sessenta",
    }
    words.update({72: "setenta e dois", 84: "oitenta e quatro", 120: "cento e vinte"})
    return f"{count} ({words.get(count, str(count))}) meses"


class Clauses:
    """Acumula blocos e numera cláusulas e subcláusulas (1, 1.1, 1.2...)."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec
        self.blocks: list[Block] = []
        self.number = 0
        self._item = 0
        self.ctx: dict[str, str] = {**asdict(spec.vocab)}
        for letter in "ABC":
            self.ctx[letter] = getattr(spec.vocab, f"{letter.lower()}_name").split(" –")[0]

    def pick(self, first: str, second: str) -> str:
        return first if self.spec.variant % 2 == 0 else second

    def fmt(self, text: str, **extra: str) -> str:
        once = text.format_map({**self.ctx, **extra})
        return once.format_map(self.ctx) if "{" in once else once

    def clause(self, title: str) -> None:
        self.number += 1
        self._item = 0
        self.blocks.append(Block("h2", f"CLÁUSULA {self.number} – {title.upper()}"))

    def item(self, text: str, **extra: str) -> str:
        self._item += 1
        number = f"{self.number}.{self._item}"
        self.blocks.append(Block("item", self.fmt(text, **extra), number=number))
        return number

    def sub(self, text: str, **extra: str) -> None:
        self.blocks.append(Block("bullet", self.fmt(text, **extra)))

    def note(self, text: str) -> None:
        self.blocks.append(Block("note", text))


def _label(spec: Spec, key: str) -> str:
    return spec.labels.get(key) or COVERAGE_TEXTS[key][0]


def _limit_phrase(spec: Spec, cov: Cov) -> str:
    abbr = spec.vocab.L_abbr
    if cov.limit.startswith("Até o"):
        return f"até o {abbr}, sem sublimite específico"
    return f"limitada ao sublimite de {cov.limit}, que integra e não se soma ao {abbr}"


def _coverage_items(c: Clauses, keys: tuple[str, ...]) -> list[str]:
    """Escreve as coberturas contratadas de `keys`; devolve as não contratadas."""

    optional: list[str] = []
    for key in keys:
        cov = c.spec.coverages.get(key)
        if cov is None or cov.status == "E":
            continue
        title, texts, _ = COVERAGE_TEXTS[key]
        if cov.status == "N":
            optional.append(_label(c.spec, key))
            continue
        text = texts[c.spec.variant % 2]
        if "Custos de Defesa" in cov.limit:
            text += (
                " A cobertura limita-se aos Custos de Defesa; não se pagam indenizações, "
                "multas ou condenações."
            )
        c.item(f"{_label(c.spec, key)}. {text}", lim=_limit_phrase(c.spec, cov))
        if cov.note:
            c.sub(cov.note)
    return optional


def _optional_text(c: Clauses, names: list[str]) -> None:
    if not names:
        return
    c.item(
        "As coberturas a seguir constam destas Condições Gerais apenas como opção. Não foram "
        "contratadas, não integram a Especificação e só passarão a vigorar mediante endosso "
        "específico e pagamento de prêmio adicional. A menção ao termo nestas Condições Gerais "
        "não gera direito a indenização:"
    )
    for index, name in enumerate(names):
        c.sub(f"{chr(97 + index)}) {name}.")


# ---------------------------------------------------------------- capa e quadro resumo
def _cover(spec: Spec) -> list[Block]:
    v = spec.vocab
    return [
        Block(
            "title",
            "APÓLICE DE SEGURO DE RESPONSABILIDADE CIVIL DE ADMINISTRADORES E DIRETORES (D&O)",
        ),
        Block(
            "subtitle",
            f"{spec.insurer} – CNPJ {spec.insurer_cnpj} – Código SUSEP {spec.insurer_susep}",
        ),
        Block("note", f"{spec.insurer_address}. Ouvidoria: {spec.ouvidoria}."),
        Block(
            "table",
            table=Table(
                ("Campo", "Informação"),
                (
                    ("Apólice nº", spec.apolice),
                    ("Proposta nº", spec.proposta),
                    ("Processo SUSEP nº", f"{spec.processo} (fictício)"),
                    (
                        "Ramo / Modalidade",
                        "0351 – Responsabilidade Civil de Administradores e "
                        "Diretores (D&O) – base de reclamações (claims made) com notificação",
                    ),
                    ("Data de emissão", spec.emissao),
                    ("Vigência", f"Das 24h de {spec.vig_ini} às 24h de {spec.vig_fim}"),
                    (f"{v.T} / Segurado principal", f"{spec.tomador} – CNPJ {spec.tomador_cnpj}"),
                    ("Endereço", spec.tomador_address),
                    ("Atividade", spec.tomador_profile),
                    (
                        "Corretor de seguros",
                        f"{spec.corretor} – SUSEP nº {spec.corretor_susep} (fictício)",
                    ),
                ),
                (0.32, 0.68),
            ),
        ),
        Block(
            "p",
            f"A Seguradora, em contraprestação ao prêmio e com base nas declarações "
            f"prestadas na proposta, garante ao {v.T} e aos {v.S_pl} as coberturas contratadas "
            "indicadas nas Condições Particulares, nos termos destas Condições Gerais e dos "
            "endossos emitidos, observada a Circular SUSEP nº 637, de 27 de julho de 2021, e "
            "os arts. 757 a 802 do Código Civil (Lei nº 10.406/2002).",
        ),
        Block(
            "note",
            "Documento fictício, criado exclusivamente para testes do ClauseAI. As "
            "empresas, números, processos e pessoas citados não existem e o texto não tem "
            "valor contratual. O registro do produto na SUSEP é automático e não representa "
            "aprovação ou recomendação por parte da autarquia.",
        ),
    ]


def _limits_table(spec: Spec) -> Table:
    v = spec.vocab
    rows: list[tuple[str, ...]] = []
    side_b = v.b_name.split(" –")[0]

    def row(label: str, cov: Cov) -> tuple[str, ...]:
        limit = cov.limit.replace("LMG", v.L_abbr)
        deductible = cov.deductible.replace("Cobertura B", side_b)
        return (label, STATUS_LABEL[cov.status], limit, deductible)

    core = (
        ("side_a", v.a_name),
        ("side_b", v.b_name),
        ("side_c", v.c_name),
        ("defesa", "Custos de Defesa (adiantamento)"),
    )
    for key, label in core:
        cov = spec.coverages[key]
        rows.append(row(label, cov))
    keys = CLAUSE_4_KEYS + CLAUSE_5_KEYS
    for key in keys:
        cov = spec.coverages.get(key)
        if cov is None:
            continue
        rows.append(row(_label(spec, key), cov))
    return Table(
        ("Cobertura", "Situação", "Limite / Sublimite", "Franquia"),
        tuple(rows),
        (0.38, 0.14, 0.26, 0.22),
        caption="Quadro 1 – Limite Máximo de Garantia, coberturas e sublimites",
    )


def _summary(spec: Spec) -> list[Block]:
    v = spec.vocab
    net = spec.premio_liquido
    iof = round(net * 0.0738)
    total = net + iof
    per = total // spec.parcelas
    blocks: list[Block] = [
        Block("h1", "SEÇÃO I – CONDIÇÕES PARTICULARES E QUADRO RESUMO"),
        Block(
            "p",
            f"Apólice nº {spec.apolice} · {v.T}: {spec.tomador}. Somente as coberturas "
            "indicadas como Contratada estão em vigor. As coberturas Não contratadas ou "
            "Excluídas não geram direito a indenização, ainda que mencionadas nas Condições "
            "Gerais.",
        ),
        Block(
            "table",
            table=Table(
                ("Item", "Condição"),
                (
                    (
                        f"{v.L} ({v.L_abbr})",
                        f"{brl(spec.lmg)} por vigência, em base agregada, para todas as "
                        "Coberturas, "
                        "Perdas e Custos de Defesa, salvo quando indicado em contrário.",
                    ),
                    (
                        "Limite adicional exclusivo da Cobertura A (DIC)",
                        f"{brl(spec.side_a_dic)}, disponível apenas ao {v.S} após o esgotamento do "
                        f"{v.L_abbr}."
                        if spec.side_a_dic
                        else "Não contratado.",
                    ),
                    (
                        "Moeda",
                        "Real (R$). Reclamações em moeda estrangeira serão convertidas "
                        "pela taxa PTAX de venda do Banco Central do Brasil na data do pagamento.",
                    ),
                    ("Prêmio líquido", brl(net)),
                    ("IOF (7,38%)", brl(iof)),
                    (
                        "Prêmio total",
                        f"{brl(total)}, em {spec.parcelas} parcelas mensais de {brl(per)}",
                    ),
                ),
                (0.34, 0.66),
                caption="Quadro 0 – Limite, moeda e prêmio",
            ),
        ),
        Block("table", table=_limits_table(spec)),
        Block(
            "table",
            table=Table(
                ("Item", "Condição"),
                (
                    (v.a_name.split(" –")[0], spec.franquia_a),
                    (f"{v.b_name.split(' –')[0]} e adicionais", spec.franquia_b),
                    (v.c_name.split(" –")[0], spec.franquia_c),
                    ("Participação obrigatória do Segurado", spec.participacao),
                ),
                (0.34, 0.66),
                caption="Quadro 2 – Franquias, retenção e participação obrigatória",
            ),
        ),
        Block(
            "table",
            table=Table(
                ("Categoria de Segurado", "Abrangência"),
                spec.insureds,
                (0.34, 0.66),
                caption="Quadro 3 – Segurados",
            ),
        ),
    ]
    if spec.subsidiaries:
        blocks.append(
            Block(
                "table",
                table=Table(
                    ("Subsidiária", "Participação / país"),
                    spec.subsidiaries,
                    (0.6, 0.4),
                    caption="Quadro 4 – Subsidiárias cobertas",
                ),
            )
        )
    blocks.append(Block("table", table=_terms_table(spec)))
    return blocks


def _retro_summary(spec: Spec) -> str:
    if spec.retro_style == "ilimitada":
        return "Retroatividade ilimitada, exceto fatos ou circunstâncias conhecidos."
    if spec.retro_style == "datada":
        return (
            f"Data de retroatividade: {spec.retro_value}. "
            "Atos anteriores a essa data não estão cobertos."
        )
    return f"Período de retroatividade de {spec.retro_value} anteriores ao início da vigência."


def _terms_table(spec: Spec) -> Table:
    comp = (
        f"{months(spec.comp_months)}, automático e sem prêmio adicional, em caso de não renovação."
        if spec.comp_auto
        else f"{months(spec.comp_months)}, mediante requerimento e prêmio adicional de "
        f"{spec.comp_premium_pct}% do prêmio anual."
    )
    supl = (
        f"{months(spec.supl_months)}, contratável mediante prêmio adicional de "
        f"{spec.supl_premium_pct}% do prêmio anual, solicitado em até {spec.supl_deadline_days} "
        "dias do fim da vigência."
        if spec.supl_months
        else "Não disponível nesta apólice."
    )
    rows = [
        ("Retroatividade", _retro_summary(spec)),
        ("Prazo complementar", comp),
        ("Prazo suplementar", supl),
    ]
    if spec.runoff_months:
        rows.append(("Cauda / run-off", spec.runoff_text))
    rows += [
        ("Âmbito territorial", spec.territory),
        ("Jurisdição", spec.jurisdiction),
        (
            "Notificação de circunstâncias",
            f"Até {days(spec.notice_days)} após o conhecimento do fato ou "
            "circunstância, e sempre até o fim do prazo complementar.",
        ),
        ("Foro / solução de disputas", _forum_summary(spec)),
    ]
    return Table(
        ("Item", "Condição"),
        tuple(rows),
        (0.28, 0.72),
        caption="Quadro 5 – Retroatividade, prazos, território e notificação",
    )


def _forum_summary(spec: Spec) -> str:
    if spec.arbitration:
        return f"Arbitragem, sede em {spec.forum_city}, nos termos da Cláusula 19."
    return f"Foro do domicílio do Segurado ou {spec.forum_city}, nos termos da Cláusula 19."


# ---------------------------------------------------------------- condições gerais
def _objeto_e_definicoes(c: Clauses) -> None:
    s = c.spec
    c.clause("Objeto do seguro")
    c.item(
        "Este seguro garante, até o {L} ({L_abbr}) indicado na Especificação, o pagamento das "
        "{P} decorrentes de Reclamações apresentadas contra o {S} durante a vigência, o "
        "Prazo Complementar ou o Prazo Suplementar, por {ato} praticado no exercício de suas "
        "funções no {T} ou em Subsidiária, {retro}.",
        retro="a partir da data ou do período de retroatividade indicado nas Condições Particulares"
        if s.retro_style != "ilimitada"
        else "sem limite de data anterior, ressalvados os fatos e circunstâncias conhecidos",
    )
    c.item(
        "O seguro é contratado na modalidade de base de reclamações (claims made), com "
        "notificação, e rege-se pelas Condições Particulares, por estas Condições Gerais, pelos "
        "endossos, pela Circular SUSEP nº 637/2021 e pelo Código Civil. Em caso de "
        "divergência, prevalecem os endossos, depois as Condições Particulares."
    )
    c.item(
        "A contratação de cada cobertura somente se comprova pela Especificação e pelas "
        "Condições Particulares. A previsão de uma cobertura nestas Condições Gerais não "
        "implica sua contratação."
    )

    c.clause("Definições")
    defs = [
        (
            "Apólice",
            "instrumento que formaliza o contrato, composto pela proposta, Condições "
            "Particulares, Condições Gerais e endossos.",
        ),
        (
            "{T}",
            "a pessoa jurídica indicada na capa da apólice, que contrata o seguro em favor "
            "dos {S_pl} e responde pelo pagamento do prêmio.",
        ),
        (
            "Subsidiária",
            "sociedade em que o {T} detenha, direta ou indiretamente, mais de "
            "50% (cinquenta por cento) do capital votante, ou o poder de eleger "
            "a maioria dos administradores, indicada no Quadro 4 ou incluída por "
            "endosso.",
        ),
        (
            "{S}",
            "as pessoas físicas indicadas no Quadro 3, presentes, passadas ou futuras, que "
            "exerçam ou tenham exercido cargo de administração, em conselho, comitê "
            "estatutário ou função de gestão com poderes de representação no {T} ou em "
            "Subsidiária, inclusive, quando previsto, o espólio e os herdeiros.",
        ),
        (
            "{ato}",
            "ato ou omissão culposa, erro, declaração inexata, violação de dever legal, "
            "estatutário ou fiduciário, real ou alegado, praticado pelo {S} no "
            "exercício de suas funções.",
        ),
        (
            "Reclamação",
            "(a) citação ou notificação judicial em ação civil, criminal ou "
            "administrativa; (b) pedido escrito de indenização ou reparação; (c) "
            "instauração de processo arbitral; (d) Investigação Formal contra o {S}.",
        ),
        (
            "Sinistro",
            "toda Reclamação, ou conjunto de Reclamações decorrentes do mesmo {ato} ou "
            "de {ato_pl} relacionados, considerado um único Sinistro na data da primeira "
            "Reclamação.",
        ),
        (
            "{P}",
            "valores que o {S} for obrigado a pagar por decisão judicial, arbitral ou acordo "
            "aprovado pela Seguradora, inclusive Custos de Defesa, exceto tributos, multas "
            "e sanções que a lei aplicável proíba segurar, e as demais exclusões desta "
            "apólice.",
        ),
        (
            "Custos de Defesa",
            "honorários advocatícios e periciais, custas judiciais, cauções "
            "e demais despesas razoáveis e necessárias à defesa do {S}, "
            "aprovadas pela Seguradora.",
        ),
        (
            "Investigação Formal",
            "procedimento formal de apuração instaurado por autoridade "
            "pública, regulador ou autorregulador, em que o {S} seja "
            "intimado ou convocado.",
        ),
        (
            "Circunstância",
            "fato ou situação específica, conhecida durante a vigência, que possa "
            "razoavelmente originar uma Reclamação.",
        ),
        (
            "{L} ({L_abbr})",
            "valor máximo de responsabilidade da Seguradora por todas as {P}, "
            "Custos de Defesa e coberturas, na vigência.",
        ),
        (
            "Franquia",
            "parcela das {P} que fica a cargo do {T} ou do {S}, deduzida de cada "
            "Reclamação, conforme o Quadro 2.",
        ),
        (
            "Poluentes",
            "qualquer substância sólida, líquida, gasosa ou térmica irritante ou "
            "contaminante, inclusive fumaça, vapor, fuligem, resíduos, rejeitos, "
            "agrotóxicos e efluentes.",
        ),
        (
            "Entidade Externa",
            "pessoa jurídica sem fins lucrativos, que não seja Subsidiária, em "
            "que o {S} ocupe cargo por indicação escrita do {T}.",
        ),
        (
            "Evento de Crise",
            "fato que, a juízo razoável do {T}, possa gerar Reclamação relevante "
            "ou dano grave à reputação do {T} ou do {S}.",
        ),
        (
            "Prazo Complementar",
            "período posterior ao fim da vigência, em que Reclamações por "
            "atos anteriores ao término podem ser apresentadas e notificadas.",
        ),
        (
            "Prazo Suplementar",
            "extensão contratável do período de apresentação de Reclamações "
            "após o fim da vigência, nas condições do Quadro 5.",
        ),
    ]
    for term, text in defs:
        c.item(f"“{term}”: {text}", ato_pl="Atos Danosos")
    # Ajuste do plural: as definições usam o termo da seguradora.


def _basic_coverages(c: Clauses) -> None:
    s = c.spec
    c.clause("Coberturas básicas")
    c.item(
        "{a_name}. A Seguradora pagará diretamente ao {S}, ou reembolsará quem o tiver "
        "feito, as {P} decorrentes de Reclamação por {ato}, quando o {T} não puder ou não "
        "estiver legalmente autorizado a indenizá-lo (Side A), dentro do {L_abbr}."
    )
    c.item(
        "{b_name}. A Seguradora reembolsará ao {T} as {P} que este, na forma da lei ou de seu "
        "estatuto, tenha pago ou adiantado em nome do {S} em razão de Reclamação coberta "
        "(Side B), aplicada a franquia do Quadro 2."
    )
    side_c = s.coverages["side_c"]
    if side_c.status == "C":
        c.item(
            "{c_name}. A Seguradora pagará as {P} do próprio {T} decorrentes de Reclamação "
            "de investidores em razão de violação da Lei 6.385/1976, da Lei 6.404/1976 ou de "
            "normas da Comissão de Valores Mobiliários (CVM), na oferta ou negociação de valores "
            "mobiliários do {T} (Side C), {lim}.",
            lim=_limit_phrase(s, side_c),
        )
    elif side_c.status == "N":
        c.item(
            "{c_name}. Cobertura à sociedade por Reclamações de valores mobiliários prevista "
            "apenas como opção. Não foi contratada nesta apólice e depende de endosso específico."
        )
    else:
        c.item(
            "Não há {C}. Estão excluídas as Reclamações contra o {T} como pessoa jurídica, "
            "bem como as decorrentes de oferta, emissão ou negociação de valores mobiliários."
        )
    if s.side_a_dic:
        c.item(
            f"Limite adicional exclusivo da {{A}} (Difference in Conditions – DIC). Esgotado o "
            f"{{L_abbr}}, ou quando a apólice não puder indenizar por recusa do {{T}}, a "
            f"Seguradora pagará ao {{S}} até {brl(s.side_a_dic)} adicionais, exclusivamente para "
            "Perdas não indenizadas pelo {T}. Esse valor não é compartilhado com o {T} nem "
            "com a {B}."
        )


def _defesa(c: Clauses) -> None:
    s = c.spec
    defesa = s.coverages["defesa"]
    c.clause("Custos de defesa e despesas correlatas")
    additional = "Adicional" in defesa.limit
    c.item(
        "Adiantamento de Custos de Defesa. A Seguradora adiantará, à medida que forem "
        "incorridos e em até 30 (trinta) dias da apresentação da documentação, os Custos de "
        "Defesa razoáveis do {S} em Reclamação que possa ser coberta. {limite}",
        limite=(
            "Os Custos de Defesa são pagos em adição ao {L_abbr}, dentro do valor indicado no "
            "Quadro 1."
            if additional
            else "Os Custos de Defesa integram o {L_abbr} e reduzem sua disponibilidade."
        ),
    )
    c.item(
        "O {S} escolherá o advogado dentre os indicados pelo {T} ou aprovados pela Seguradora, "
        "cuja anuência não será negada sem justo motivo. A Seguradora não responde por "
        "honorários acima de valores razoáveis de mercado para a matéria."
    )
    c.item(
        "Se, ao final, ficar demonstrado que a Reclamação não estava coberta, ou se houver "
        "decisão definitiva reconhecendo dolo, fraude ou vantagem indevida, o {S} restituirá os "
        "valores adiantados corrigidos monetariamente, na forma da Cláusula 9."
    )
    optional = _coverage_items(c, CLAUSE_4_KEYS)
    _optional_text(c, optional)


def _extensions(c: Clauses) -> None:
    c.clause("Extensões de cobertura")
    c.item(
        "Sujeitas ao {L_abbr}, às Franquias e às exclusões destas Condições Gerais, estão "
        "contratadas as extensões abaixo, nos limites do Quadro 1. Sublimites integram o "
        "{L_abbr} e não são adicionais a ele."
    )
    optional = _coverage_items(c, CLAUSE_5_KEYS)
    _optional_text(c, optional)


def _limits(c: Clauses) -> None:
    s = c.spec
    c.clause("Limites, sublimites, franquia e erosão")
    c.item(
        "O {L_abbr} é o valor máximo agregado que a Seguradora pagará na vigência, incluindo o "
        "Prazo Complementar, para todas as Reclamações, Perdas e coberturas, independentemente "
        "do número de Segurados, Reclamações ou reclamantes."
    )
    c.item(
        "Sublimites, quando indicados no Quadro 1, são agregados por vigência, integram o "
        "{L_abbr} e não se somam a ele. O pagamento de um sublimite erode o {L_abbr}."
    )
    c.item(
        "A Franquia do Quadro 2 é deduzida de cada Reclamação. Quando mais de uma Franquia "
        "for aplicável a um mesmo Sinistro, prevalecerá a maior. Não se aplica Franquia aos "
        "Custos de Defesa da {A}."
    )
    c.item(
        "Ordem de pagamento. Existindo Reclamações simultâneas, a Seguradora pagará primeiro as "
        "{P} da {A}, depois as da {B} e, por último, as demais coberturas, "
        "podendo suspender pagamentos da {B} ou da {C}, para não comprometer o {L_abbr} "
        "em prejuízo dos {S_pl}."
    )
    c.item(
        "Esgotado o {L_abbr}, cessam todas as obrigações da Seguradora, inclusive o adiantamento "
        "de Custos de Defesa, salvo o Limite adicional da {A}, se contratado.",
    )
    if not s.side_a_dic:
        c.item("Não há reinstalação de limite nem limite adicional exclusivo da {A}.")


def _vigencia(c: Clauses) -> None:
    s = c.spec
    c.clause("Vigência, retroatividade, prazo complementar e suplementar")
    c.item(
        "A vigência da apólice é a indicada na capa, com início e término às 24 horas das datas "
        "ali informadas."
    )
    if s.retro_style == "ilimitada":
        c.item(
            "Retroatividade ilimitada. O seguro cobre Reclamações por {ato} praticado a "
            "qualquer tempo antes da vigência, desde que nenhum {S} ou o {T} tenha tido "
            "conhecimento, antes do início da vigência, de fato ou Circunstância que "
            "razoavelmente pudesse originar a Reclamação (Cláusula 9)."
        )
    elif s.retro_style == "datada":
        c.item(
            "Retroatividade datada. Somente estão cobertas Reclamações por {ato} praticado em "
            "ou após {data}. Não se cobrem atos anteriores, ainda que desconhecidos, nem "
            "atos praticados por sociedades adquiridas antes de sua aquisição pelo {T}.",
            data=s.retro_value,
        )
    else:
        c.item(
            "Período de retroatividade. Estão cobertas Reclamações por {ato} praticado nos "
            "{periodo} imediatamente anteriores ao início da vigência. Atos anteriores a esse "
            "período não estão cobertos, salvo endosso específico.",
            periodo=s.retro_value,
        )
    if s.comp_auto:
        c.item(
            "Prazo Complementar. Em caso de cancelamento por iniciativa da Seguradora, ou de "
            "não renovação sem substituição por apólice que preserve a retroatividade, "
            "aplica-se automaticamente, sem cobrança de prêmio adicional, Prazo Complementar de "
            f"{months(s.comp_months)}, para Reclamações por atos anteriores ao término da "
            "vigência, notificadas nos termos da Cláusula 11."
        )
    else:
        c.item(
            f"Prazo Complementar. Mediante requerimento escrito em até 30 (trinta) dias do término "
            f"da vigência e pagamento de prêmio adicional de {s.comp_premium_pct}% do prêmio "
            f"anual, será concedido Prazo Complementar de {months(s.comp_months)}. Não havendo "
            "requerimento, a cobertura cessa no fim da vigência."
        )
    if s.supl_months:
        c.item(
            f"Prazo Suplementar. Além do Prazo Complementar, o {{T}} poderá contratar Prazo "
            f"Suplementar de {months(s.supl_months)} mediante prêmio adicional de "
            f"{s.supl_premium_pct}% do prêmio anual, requerido em até {s.supl_deadline_days} "
            "dias após o término da vigência. O Prazo Suplementar não reinstala o limite e "
            "cobre somente atos anteriores ao término."
        )
    else:
        c.item(
            "Prazo Suplementar. Esta apólice não oferece Prazo Suplementar ou extensão "
            "contratável pós-vigência. Encerrado o Prazo Complementar, cessa qualquer "
            "cobertura."
        )
    if s.runoff_months:
        c.item(f"Cauda / run-off. {s.runoff_text}")
    for key, title, who in (
        (
            "aposentados",
            "Segurados aposentados",
            "se aposentar ou deixar o cargo por término de mandato",
        ),
        ("demissao", "Demissão voluntária e desligamento", "se desligar por demissão voluntária"),
    ):
        cov = s.coverages.get(key)
        if cov is None:
            continue
        if cov.status == "C":
            c.item(
                f"{title}. O {{S}} que, durante a vigência, {who} terá Prazo Complementar de "
                f"{cov.limit} "
                "para Reclamações por atos anteriores ao desligamento, independentemente da "
                "renovação da apólice."
            )
        else:
            c.item(
                f"{title}. Não há prazo especial para {title.lower()}; aplica-se o Prazo "
                "Complementar geral, salvo endosso."
            )


def _territory(c: Clauses) -> None:
    s = c.spec
    c.clause("Âmbito territorial e jurisdição")
    text = {
        "mundial": "A cobertura vale em todo o mundo, para Reclamações apresentadas em qualquer "
        "jurisdição, inclusive Estados Unidos e Canadá, sem sublimite específico.",
        "brasil": "A cobertura vale para Reclamações apresentadas no território brasileiro. "
        "Reclamações apresentadas fora do Brasil não estão cobertas.",
        "mercosul": "A cobertura vale no Brasil e nos países do Mercosul em que o {T} possua "
        "Subsidiária indicada no Quadro 4, para Reclamações apresentadas nesses "
        "territórios. Fora deles, não há cobertura.",
        "mundial_eua": "A cobertura vale em todo o mundo. Para Reclamações apresentadas nos "
        "Estados Unidos da América ou no Canadá, ou fundadas em suas leis, aplica-se "
        "o sublimite e a Franquia indicados no Quadro 1 (Processos no Exterior).",
    }[s.territory_style]
    c.item(text)
    c.item(f"Jurisdição: {s.jurisdiction}")
    c.item(
        "Sanções. A Seguradora não presta cobertura, nem paga sinistro ou benefício, se isso a "
        "expuser a sanção, proibição ou restrição decorrente de resoluções da ONU, ou de leis "
        "de sanções econômicas ou comerciais do Brasil, da União Europeia, do Reino Unido ou "
        "dos Estados Unidos da América."
    )


def _general_exclusions(c: Clauses) -> None:
    s = c.spec
    c.clause("Exclusões gerais")
    c.item(
        "Além dos riscos excluídos por lei, a Seguradora não responde por Reclamações, {P} "
        "ou Custos de Defesa:"
    )
    items = [
        "decorrentes de ato doloso, fraude, ato de improbidade ou vantagem pessoal indevida do "
        "{S}, reconhecidos em decisão judicial ou arbitral definitiva. Até a decisão, os Custos "
        "de Defesa serão adiantados, com restituição posterior;",
        "por lucro, remuneração ou vantagem a que o {S} não tinha direito legal, inclusive "
        "operações com partes relacionadas em condições não equitativas;",
        "fundadas em fatos, atos ou Circunstâncias conhecidos pelo {T} ou pelo {S} antes do início "
        "da vigência, ou já notificados a outra apólice;",
        "decorrentes de processo judicial, arbitral ou administrativo pendente, ou de "
        "litígio anterior, ou de fatos neles alegados;",
        "por guerra, invasão, atos de inimigo estrangeiro, guerra civil, terrorismo, "
        "radiação, contaminação nuclear ou reação nuclear;",
        "por responsabilidade assumida por contrato, garantia ou promessa, salvo se a "
        "responsabilidade existisse independentemente do contrato;",
        "por Reclamação relativa a benefícios de previdência complementar, Lei ERISA "
        "ou administração de plano de benefícios;",
        "por multa, sanção ou penalidade que a lei proíba segurar, ou de caráter punitivo ou "
        "exemplar;",
        "por descumprimento de obrigação de pagar prêmios, tributos, encargos ou verbas "
        "trabalhistas próprios do {T};",
        "por propriedade intelectual, patentes, marcas, segredos industriais ou direitos "
        "autorais, salvo Custos de Defesa;",
        "por atos do {S} em outra sociedade não indicada como Subsidiária ou Entidade Externa "
        "coberta;",
        "por Reclamação apresentada em jurisdição ou por pessoa sujeita a sanção que impeça o "
        "pagamento (Cláusula 8).",
    ]
    for index, text in enumerate(items):
        c.sub(f"{chr(97 + index)}) {c.fmt(text)}")
    for text in s.extra_exclusions:
        c.item(text)


def _specific_exclusions(c: Clauses) -> None:
    s = c.spec
    c.clause("Exclusões específicas")
    c.item("Poluição. " + POLLUTION_TEXTS[s.pollution_style][0])
    for extra in POLLUTION_TEXTS[s.pollution_style][1:]:
        c.item(extra)
    for key in COVERAGE_TEXTS:
        cov = s.coverages.get(key)
        if cov is None or cov.status != "E":
            continue
        excluded = COVERAGE_TEXTS[key][2]
        if excluded:
            c.item(f"{_label(s, key)}. {excluded}", lim=_limit_phrase(s, cov))
    if s.cyber_exclusion:
        c.item(
            "Dados e sistemas. Ficam excluídas Reclamações por violação de segurança de "
            "sistemas, vazamento ou tratamento indevido de dados pessoais (Lei 13.709/2018 – "
            "LGPD), ataque cibernético e falha de tecnologia, salvo Custos de Defesa do {S} "
            "pela {A}, quando decorrentes de falha de supervisão da administração."
        )
    if s.coverages["side_c"].status == "E":
        c.item(
            "Valores mobiliários. Não estão cobertas Reclamações relativas à oferta pública ou "
            "privada de valores mobiliários do {T}, ressalvada a {A} do {S}."
        )


def _notificacao(c: Clauses) -> None:
    s = c.spec
    c.clause("Notificação de Reclamações e Circunstâncias")
    c.item(
        f"O {{T}} ou o {{S}} deverá notificar a Seguradora, por escrito, de qualquer Reclamação "
        f"assim que dela tomar conhecimento e em até {days(s.notice_days)}, "
        "e sempre até o fim da vigência ou do Prazo Complementar, o que ocorrer primeiro."
    )
    c.item(
        "Notificação de Circunstâncias. Se, durante a vigência, o {T} ou o {S} tiver "
        "conhecimento de Circunstância que possa originar Reclamação, poderá notificá-la à "
        "Seguradora com descrição dos fatos, das pessoas envolvidas, da data e dos possíveis "
        "reclamantes. A Reclamação posterior será tratada como apresentada na vigência em que "
        "a Circunstância foi notificada."
    )
    c.item(
        "A notificação tardia não prejudica a cobertura se realizada dentro da vigência ou do "
        "Prazo Complementar, mas a Seguradora não responde por Custos de Defesa incorridos antes "
        "da notificação sem sua anuência."
    )


def _sinistro(c: Clauses) -> None:
    c.clause("Sinistro, defesa e cooperação")
    c.item(
        "O {S} e o {T} cooperarão com a Seguradora, fornecendo documentos e informações, e não "
        "admitirão responsabilidade, não firmarão acordo nem incorrerão em despesas sem prévia "
        "anuência da Seguradora, que não a negará sem justo motivo."
    )
    c.item(
        "A Seguradora tem o direito de participar da defesa e das negociações. Se o {S} recusar "
        "acordo recomendado pela Seguradora e aceito pelo reclamante, a Seguradora responde "
        "apenas até o valor do acordo recusado mais os Custos de Defesa razoáveis até então "
        "incorridos."
    )
    c.item(
        "A Seguradora tem 30 (trinta) dias, contados da entrega de todos os documentos, para "
        "se manifestar sobre a cobertura. O pedido de documentos complementares suspende "
        "esse prazo uma única vez. O pagamento será feito em até 30 (trinta) dias da decisão, "
        "sob pena de atualização monetária pelo IPCA e juros moratórios de 1% (um por cento) "
        "ao mês."
    )


def _regresso(c: Clauses) -> None:
    c.clause("Direito de regresso e sub-rogação")
    c.item(
        "Paga a indenização, a Seguradora fica sub-rogada, até o limite do valor pago, nos "
        "direitos e ações do {S} ou do {T} contra terceiros, nos termos do art. 786 do Código "
        "Civil, obrigando-se o {S} a colaborar e a não praticar ato que os prejudique."
    )
    c.item(
        "A Seguradora não exercerá direito de regresso contra o {S}, exceto se a Reclamação "
        "for excluída por dolo ou fraude, hipótese em que poderá cobrar os valores "
        "pagos, atualizados. Não haverá regresso contra o {S} por culpa, ainda que grave."
    )
    c.item(
        "Também não haverá sub-rogação contra herdeiros, cônjuge ou companheiro do {S}, "
        "salvo nas hipóteses de dolo ou fraude."
    )


def _rateio(c: Clauses) -> None:
    c.clause("Rateio, alocação e outros seguros")
    c.item(
        "Quando a Reclamação envolver Perdas cobertas e não cobertas, ou Segurados cobertos e "
        "não cobertos, aplicar-se-á alocação justa e proporcional às exposições, envidando as "
        "partes seus melhores esforços para acordá-la. Os Custos de Defesa serão alocados "
        "integralmente à parte coberta quando a defesa beneficiar ambas."
    )
    c.item(
        "Este seguro é excedente a qualquer outro seguro válido e cobrável, inclusive de "
        "Entidade Externa, salvo o seguro contratado especificamente como excedente desta apólice."
    )
    c.item(
        "Havendo mais de uma apólice da Seguradora que cubra a mesma Reclamação, a "
        "responsabilidade total da Seguradora não excederá o maior limite aplicável."
    )


def _final_clauses(c: Clauses) -> None:
    s = c.spec
    c.clause("Declarações, agravamento do risco e perda de direitos")
    c.item(
        "O {T} e o {S} declaram ser verdadeiras as informações da proposta, base desta "
        "apólice. Nos termos dos arts. 765 e 766 do Código Civil, a omissão ou inexatidão "
        "de má-fé, ou que influa na aceitação ou no prêmio, implica perda do direito à "
        "garantia. Se sem má-fé, a indenização será reduzida proporcionalmente à diferença "
        "de prêmio."
    )
    c.item(
        "O {T} comunicará à Seguradora, em até 15 (quinze) dias, fusão, incorporação, cisão, "
        "alienação de controle, liquidação, recuperação judicial ou extrajudicial ou falência, "
        "de que resulte mudança do risco, nos termos do art. 769 do Código Civil."
    )
    c.item(
        "Perde direito à indenização quem agravar intencionalmente o risco, nos termos do art. "
        "768 do Código Civil, ou quem prestar declaração falsa na notificação do Sinistro."
    )

    c.clause("Prêmio e pagamento")
    c.item(
        f"O prêmio será pago em {s.parcelas} parcelas mensais nas datas indicadas na proposta. "
        "O atraso de pagamento de qualquer parcela sujeita o valor a atualização monetária e "
        "juros de 1% (um por cento) ao mês e multa de 2% (dois por cento)."
    )
    c.item(
        "A falta de pagamento de parcela, após notificação do {T}, por 30 (trinta) dias, "
        "poderá levar ao cancelamento da apólice, conforme a Circular SUSEP nº 637/2021. "
        "Ocorrido o sinistro, as parcelas vincendas serão deduzidas da indenização."
    )

    c.clause("Cancelamento e renovação")
    c.item(
        "A apólice poderá ser cancelada pelo {T}, a qualquer tempo, com devolução do prêmio "
        "proporcional ao prazo a decorrer, deduzida a parcela relativa às despesas de emissão, "
        "salvo se houver Reclamação notificada, caso em que o prêmio não será devolvido."
    )
    c.item(
        "A Seguradora somente poderá cancelar por falta de pagamento (Cláusula 16), por fraude "
        "ou por agravamento do risco (Cláusula 15), mediante aviso prévio de 30 (trinta) dias."
    )
    c.item(
        "A renovação depende de nova proposta e de aceitação pela Seguradora, que informará "
        "eventuais alterações com antecedência mínima de 60 (sessenta) dias. Não há renovação "
        "automática."
    )

    c.clause("Prescrição")
    c.item(
        "Os prazos prescricionais são os previstos em lei. A pretensão do {S} ou do {T} contra a "
        "Seguradora prescreve em 1 (um) ano, contado da ciência do fato gerador da pretensão "
        "(art. 206, § 1º, inciso II, do Código Civil)."
    )
    c.item(
        "O pedido de indenização à Seguradora suspende o prazo prescricional até a ciência do "
        "{S} ou do {T} da decisão, nos termos da Súmula 229 do Superior Tribunal de Justiça."
    )

    if s.arbitration:
        c.clause("Arbitragem")
        c.item(
            "Qualquer controvérsia sobre esta apólice será resolvida por arbitragem, na forma da "
            f"Lei 9.307/1996, por três árbitros, com sede em {s.forum_city}, em português e "
            "conforme o regulamento da câmara de arbitragem indicada na Especificação."
        )
        c.item(
            "Ficam ressalvadas as medidas de urgência perante o Poder Judiciário e a possibilidade "
            "de o {T} ou o {S}, na condição de consumidor, optar pelo Poder Judiciário, nos "
            f"termos da lei. O foro da comarca de {s.forum_city} será o competente para essas "
            "medidas."
        )
    else:
        c.clause("Foro")
        c.item(
            "As controvérsias decorrentes desta apólice serão submetidas ao foro do domicílio do "
            f"{{S}} ou do {{T}}, com renúncia a qualquer outro. Na execução por uma "
            f"das partes, será competente o foro de {s.forum_city}."
        )
        c.item(
            "As partes poderão, de comum acordo e após a controvérsia, optar por mediação "
            "ou arbitragem."
        )

    c.clause("Disposições finais")
    c.item(
        "Os dados pessoais são tratados nos termos da Lei 13.709/2018 (LGPD), exclusivamente "
        "para a gestão desta apólice e de eventuais sinistros."
    )
    c.item(
        f"Reclamações, dúvidas e sugestões: SAC da Seguradora e Ouvidoria ({s.ouvidoria}). "
        "Sem solução, o segurado pode consultar a SUSEP pelo telefone 0800 021 8484 ou em "
        "www.gov.br/susep."
    )
    c.item(
        f"Corretor: {s.corretor}. O corretor indicado é o intermediário da contratação, sem "
        "poderes "
        "para alterar estas Condições."
    )


def _endorsements(spec: Spec) -> list[Block]:
    blocks = [Block("h1", "SEÇÃO III – ENDOSSOS E CLÁUSULAS ESPECIAIS")]
    for index, endorsement in enumerate(spec.endorsements, start=1):
        blocks.append(Block("h2", f"ENDOSSO Nº {index:03d} – {endorsement.title.upper()}"))
        for paragraph in endorsement.paragraphs:
            blocks.append(Block("p", paragraph))
    blocks.append(
        Block(
            "p",
            f"Local e data: {spec.forum_city.split('/')[0]}, {spec.emissao}. "
            f"{spec.insurer} – Diretoria Técnica. Corretor: {spec.corretor}.",
        )
    )
    return blocks


def build_document(spec: Spec) -> list[Block]:
    c = Clauses(spec)
    c.blocks.append(Block("h1", "SEÇÃO II – CONDIÇÕES GERAIS"))
    c.blocks.append(
        Block(
            "p",
            f"Condições Gerais do Seguro de Responsabilidade Civil de "
            f"Administradores e Diretores (D&O), Processo SUSEP nº {spec.processo} (fictício).",
        )
    )
    for step in (
        _objeto_e_definicoes,
        _basic_coverages,
        _defesa,
        _extensions,
        _limits,
        _vigencia,
        _territory,
        _general_exclusions,
        _specific_exclusions,
        _notificacao,
        _sinistro,
        _regresso,
        _rateio,
        _final_clauses,
    ):
        step(c)
    return [
        *_cover(spec),
        Block("pagebreak"),
        *_summary(spec),
        Block("pagebreak"),
        *c.blocks,
        Block("pagebreak"),
        *_endorsements(spec),
    ]
