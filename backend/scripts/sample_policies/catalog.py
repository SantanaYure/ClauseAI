"""As cinco apólices fictícias: seguradoras, perfis de risco e diferenças de cobertura."""

from .model import Cov, Endorsement, Spec, Vocab

ALL_KEYS = (
    "side_a", "side_b", "side_c", "defesa", "defesa_patrimonial", "bloqueio", "depositos",
    "emergencial", "investigacao", "salvamento", "entidade_externa", "extradicao", "avalista",
    "inabilitacao", "multas", "novas_subs", "trabalhista", "imagem", "tributaria", "adv_internos",
    "contadores", "corporais", "materiais", "morais", "eo", "regulatorios", "crise", "herdeiros",
    "solidaria", "ambiental", "sociedade_contra", "sxs", "tac", "atos_lesivos", "exterior",
    "aposentados", "demissao",
)  # fmt: skip

LMG = "Até o LMG"


def c(limit: str = LMG, deductible: str = "Conforme Cobertura B", note: str = "") -> Cov:
    return Cov("C", limit, deductible, note)


def n() -> Cov:
    return Cov("N", "—", "—")


def e() -> Cov:
    return Cov("E", "—", "—")


def coverages(**given: Cov) -> dict[str, Cov]:
    missing = set(given) - set(ALL_KEYS)
    if missing:
        raise KeyError(f"Coberturas desconhecidas: {sorted(missing)}")
    return {key: given.get(key, n()) for key in ALL_KEYS}


SANCTIONS = Endorsement(
    "Cláusula de sanções econômicas",
    (
        "Fica entendido e acordado que nenhuma cobertura, pagamento de sinistro ou benefício será "
        "devido se sua prestação expuser a Seguradora, ou qualquer de suas resseguradoras, a "
        "sanção, proibição ou restrição imposta por resolução das Nações Unidas ou por leis e "
        "regulamentos de sanções econômicas ou comerciais aplicáveis.",
        "Permanecem inalteradas as demais disposições da apólice não alteradas por este endosso.",
    ),
)


def known_matters(date: str, text: str) -> Endorsement:
    return Endorsement(
        "Exclusão de fatos e processos conhecidos",
        (
            f"Ficam excluídas, com efeito a partir de {date}, as Reclamações decorrentes de, "
            f"baseadas em ou relacionadas com {text}, bem como qualquer processo ou "
            "circunstância nele descrito, ainda que a Reclamação seja apresentada durante a "
            "vigência desta apólice.",
        ),
    )


AURELIUS = Spec(
    stem="01_Aurelius_DO_Energia_Capital_Aberto",
    variant=0,
    insurer="Aurelius Seguros S.A.",
    insurer_cnpj="11.204.877/0001-30",
    insurer_susep="06.412",
    insurer_address="Av. Brigadeiro Faria Lima, 4.100, 12º andar, São Paulo/SP",
    ouvidoria="0800 700 0118, ouvidoria@aurelius.example",
    apolice="AUR-0351-2026-000118",
    proposta="AUR-P-2026-045210",
    processo="15414.900118/2019-71",
    emissao="29/09/2026",
    vig_ini="10/10/2026",
    vig_fim="10/10/2027",
    tomador="Aurora Energia Renovável S.A.",
    tomador_cnpj="21.630.455/0001-08",
    tomador_address="Av. das Nações Unidas, 12.995, 20º andar, São Paulo/SP",
    tomador_profile="Geração e comercialização de energia eólica e solar; companhia aberta "
    "com ações negociadas na B3 (Novo Mercado).",
    corretor="Meridiano Corretora de Seguros Ltda.",
    corretor_susep="202045118",
    vocab=Vocab(),
    lmg=50_000_000,
    side_a_dic=10_000_000,
    premio_liquido=1_180_000,
    parcelas=4,
    franquia_a="Sem franquia.",
    franquia_b="R$ 100.000,00 por Reclamação.",
    franquia_c="R$ 250.000,00 por Reclamação.",
    participacao="Não há participação obrigatória do Segurado.",
    retro_style="ilimitada",
    comp_months=36,
    comp_auto=True,
    supl_months=72,
    supl_premium_pct=60,
    supl_deadline_days=30,
    notice_days=30,
    territory="Mundial.",
    jurisdiction="Qualquer jurisdição, observada a Cláusula de Sanções.",
    territory_style="mundial",
    arbitration=True,
    forum_city="São Paulo/SP",
    pollution_style="cleanup_only",
    coverages=coverages(
        side_a=c("R$ 50.000.000,00", "Sem franquia"),
        side_b=c("R$ 50.000.000,00", "R$ 100.000,00 por Reclamação"),
        side_c=c(LMG, "R$ 250.000,00 por Reclamação"),
        defesa=c("Integrante do LMG"),
        defesa_patrimonial=c(),
        bloqueio=c("R$ 3.000.000,00"),
        depositos=c(),
        emergencial=c("R$ 1.000.000,00"),
        investigacao=c(),
        salvamento=c("R$ 2.000.000,00"),
        entidade_externa=c("R$ 5.000.000,00"),
        multas=c("R$ 5.000.000,00"),
        novas_subs=c(),
        trabalhista=c(),
        imagem=c("R$ 1.000.000,00"),
        tributaria=c(),
        adv_internos=c(),
        contadores=c(),
        corporais=c("R$ 5.000.000,00"),
        materiais=c("R$ 5.000.000,00"),
        morais=c(),
        eo=e(),
        regulatorios=c("R$ 2.000.000,00"),
        crise=c("R$ 1.000.000,00"),
        herdeiros=c(),
        solidaria=c(),
        ambiental=c("R$ 5.000.000,00"),
        sociedade_contra=c(),
        sxs=c(),
        tac=c("R$ 3.000.000,00"),
        atos_lesivos=c("R$ 5.000.000,00 (só Custos de Defesa)"),
        exterior=c(),
        aposentados=c("72 (setenta e dois) meses"),
        demissao=c("36 (trinta e seis) meses"),
    ),
    insureds=(
        ("Conselho de Administração", "Todos os membros titulares e suplentes."),
        ("Diretoria Estatutária", "Todos os diretores estatutários."),
        (
            "Conselho Fiscal e comitês",
            "Membros do Conselho Fiscal e dos comitês de assessoramento.",
        ),
        ("Empregados com poderes de gestão", "Gerentes e superintendentes com procuração."),
    ),
    subsidiaries=(
        ("Aurora Eólica Nordeste S.A.", "100%"),
        ("Aurora Solar Centro-Oeste Ltda.", "80%"),
        ("Aurora Transmissão Sul S.A.", "51%"),
    ),
    endorsements=(
        SANCTIONS,
        Endorsement(
            "Inclusão de subsidiária",
            (
                "Fica incluída como Subsidiária, a partir de 10/10/2026, a sociedade Aurora "
                "Transmissão Sul S.A., com participação de 51% do Tomador, cobertos os atos "
                "praticados a partir da data da aquisição do controle.",
            ),
        ),
        known_matters(
            "10/10/2026",
            "o processo administrativo sancionador nº 19957.004321/2025-14, em curso perante a "
            "CVM, envolvendo a divulgação de fato relevante em 2025",
        ),
    ),
)

BOREAL = Spec(
    stem="02_Boreal_DO_Industria_Capital_Fechado",
    variant=1,
    insurer="Boreal Proteção Seguros S.A.",
    insurer_cnpj="33.518.902/0001-47",
    insurer_susep="04.877",
    insurer_address="Rua da Bahia, 1.148, 9º andar, Belo Horizonte/MG",
    ouvidoria="0800 600 3105, ouvidoria@boreal.example",
    apolice="BOR-0351-2026-004512",
    proposta="BOR-P-2026-011873",
    processo="15414.601245/2021-33",
    emissao="15/09/2026",
    vig_ini="01/10/2026",
    vig_fim="01/10/2027",
    tomador="Ferrolar Indústria Metalúrgica S.A.",
    tomador_cnpj="08.443.190/0001-52",
    tomador_address="Rodovia MG-050, km 42, Distrito Industrial, Itaúna/MG",
    tomador_profile="Fabricação de componentes metálicos e peças forjadas; sociedade anônima de "
    "capital fechado, controle familiar.",
    corretor="Alvorada Corretagem de Seguros S/S Ltda.",
    corretor_susep="100387554",
    vocab=Vocab(
        T="Contratante",
        S="Administrador Segurado",
        S_pl="Administradores Segurados",
        P="Perdas Indenizáveis",
        ato="Ato de Gestão Danoso",
        L="Limite Máximo de Indenização",
        L_abbr="LMI",
        a_name="Garantia A – Proteção Individual dos Administradores",
        b_name="Garantia B – Reembolso à Sociedade",
        c_name="Garantia C – Valores Mobiliários da Sociedade",
    ),
    lmg=20_000_000,
    premio_liquido=312_000,
    parcelas=6,
    franquia_a="Sem franquia.",
    franquia_b="R$ 250.000,00 por Reclamação.",
    franquia_c="Não se aplica (cobertura excluída).",
    participacao="Participação obrigatória de 10% (dez por cento) do Administrador Segurado nas "
    "Perdas Indenizáveis da Garantia A, limitada a R$ 100.000,00 por Reclamação.",
    retro_style="datada",
    retro_value="01/03/2021 (início do primeiro seguro D&O contínuo da Contratante)",
    comp_months=12,
    comp_auto=True,
    supl_months=0,
    notice_days=60,
    territory="Brasil.",
    jurisdiction="Exclusivamente tribunais e câmaras arbitrais brasileiros.",
    territory_style="brasil",
    arbitration=False,
    forum_city="Belo Horizonte/MG",
    pollution_style="absolute",
    cyber_exclusion=True,
    coverages=coverages(
        side_a=c("R$ 20.000.000,00", "Sem franquia"),
        side_b=c("R$ 20.000.000,00", "R$ 250.000,00 por Reclamação"),
        side_c=e(),
        defesa=c("Integrante do LMI"),
        investigacao=c("R$ 2.000.000,00"),
        emergencial=c("R$ 500.000,00"),
        multas=e(),
        novas_subs=c("Até o LMI", note="A inclusão automática limita-se a 90 (noventa) dias."),
        trabalhista=c("R$ 1.000.000,00 (somente Custos de Defesa)"),
        tributaria=c("R$ 1.000.000,00 (somente Custos de Defesa)"),
        corporais=e(),
        materiais=e(),
        morais=c("R$ 2.000.000,00"),
        eo=e(),
        herdeiros=c(),
        ambiental=e(),
        sxs=e(),
        tac=e(),
        atos_lesivos=e(),
        exterior=e(),
    ),
    insureds=(
        ("Conselho de Administração", "Membros titulares."),
        ("Diretoria", "Diretores estatutários e diretor-presidente."),
        ("Conselho Fiscal", "Membros titulares e suplentes."),
    ),
    subsidiaries=(("Ferrolar Forjaria Ltda.", "100%"),),
    extra_exclusions=(
        "Sócio controlador. Ficam excluídas as Reclamações movidas por sócio ou acionista "
        "titular de 10% (dez por cento) ou mais do capital da Contratante, ou por seus "
        "parentes até o segundo grau, salvo Custos de Defesa da Garantia A.",
    ),
    endorsements=(
        SANCTIONS,
        Endorsement(
            "Exclusão de dados pessoais e sistemas",
            (
                "Ficam excluídas Reclamações decorrentes de incidente de segurança, acesso "
                "indevido ou tratamento de dados pessoais, na forma da Lei 13.709/2018.",
            ),
        ),
        known_matters(
            "01/10/2026",
            "a ação trabalhista coletiva nº 0010455-82.2024.5.03.0055, em curso perante o TRT "
            "da 3ª Região, e a autuação fiscal nº 10680.720411/2024-19",
        ),
    ),
)

CERRADO = Spec(
    stem="03_Cerrado_DO_Agronegocio",
    variant=0,
    insurer="Cerrado Riscos Corporativos S.A.",
    insurer_cnpj="27.906.331/0001-64",
    insurer_susep="05.230",
    insurer_address="Av. T-4, 1.360, sala 1.201, Setor Bueno, Goiânia/GO",
    ouvidoria="0800 500 7310, ouvidoria@cerradoriscos.example",
    apolice="CER-0351-2026-000731",
    proposta="CER-P-2026-002904",
    processo="15414.700731/2020-58",
    emissao="18/09/2026",
    vig_ini="20/10/2026",
    vig_fim="20/10/2027",
    tomador="Agropecuária Vale do Rio Claro S.A.",
    tomador_cnpj="14.880.276/0001-19",
    tomador_address="Rodovia GO-174, km 12, Zona Rural, Rio Verde/GO",
    tomador_profile="Produção de soja, milho e algodão, beneficiamento e armazenagem de grãos; "
    "sociedade anônima de capital fechado, com operações no Paraguai.",
    corretor="Safra Grande Corretora de Seguros Ltda.",
    corretor_susep="200558316",
    vocab=Vocab(
        a_name="Cobertura A – Reembolso em nome dos Administradores",
        b_name="Cobertura B – Reembolso à Sociedade",
        c_name="Cobertura C – Reclamações de Mercado de Capitais",
    ),
    lmg=30_000_000,
    premio_liquido=468_000,
    parcelas=5,
    franquia_a="Sem franquia.",
    franquia_b="R$ 150.000,00 por Reclamação; R$ 300.000,00 para Reclamações ambientais.",
    franquia_c="Não se aplica (cobertura não contratada).",
    participacao="Não há participação obrigatória do Segurado.",
    retro_style="periodo",
    retro_value="24 (vinte e quatro) meses",
    comp_months=12,
    comp_auto=False,
    comp_premium_pct=25,
    supl_months=36,
    supl_premium_pct=75,
    supl_deadline_days=30,
    notice_days=45,
    territory="Brasil e Paraguai (onde o Tomador possua Subsidiária indicada no Quadro 4).",
    jurisdiction="Tribunais brasileiros e paraguaios, nas matérias das Subsidiárias indicadas.",
    territory_style="mercosul",
    arbitration=False,
    forum_city="Goiânia/GO",
    pollution_style="coverage",
    coverages=coverages(
        side_a=c("R$ 30.000.000,00", "Sem franquia"),
        side_b=c("R$ 30.000.000,00", "R$ 150.000,00 por Reclamação"),
        side_c=n(),
        defesa=c("Adicional ao LMG, até R$ 7.500.000,00"),
        defesa_patrimonial=c("R$ 3.000.000,00"),
        bloqueio=c("R$ 2.000.000,00"),
        depositos=c("R$ 2.000.000,00"),
        emergencial=c("R$ 500.000,00"),
        investigacao=c("R$ 3.000.000,00"),
        salvamento=c("R$ 1.000.000,00"),
        entidade_externa=c("R$ 1.000.000,00"),
        avalista=c("R$ 5.000.000,00"),
        multas=c("R$ 5.000.000,00"),
        novas_subs=c(),
        trabalhista=c("R$ 5.000.000,00"),
        imagem=c("R$ 500.000,00"),
        tributaria=c("R$ 5.000.000,00"),
        contadores=c(),
        corporais=c("R$ 2.000.000,00"),
        materiais=c("R$ 5.000.000,00"),
        morais=c(),
        regulatorios=c("R$ 1.000.000,00"),
        crise=c("R$ 500.000,00"),
        herdeiros=c(),
        solidaria=c(),
        ambiental=c("R$ 10.000.000,00", "R$ 300.000,00 por Reclamação"),
        sociedade_contra=c(),
        sxs=c(),
        tac=c("R$ 3.000.000,00"),
        atos_lesivos=e(),
        aposentados=c("24 (vinte e quatro) meses"),
        demissao=c("12 (doze) meses"),
    ),
    insureds=(
        ("Conselho de Administração", "Membros titulares e suplentes."),
        ("Diretoria", "Diretores estatutários e não estatutários com poderes de representação."),
        ("Conselho Consultivo", "Membros do conselho consultivo familiar."),
        ("Gestores de fazenda", "Superintendentes de unidade com procuração."),
    ),
    subsidiaries=(
        ("Vale do Rio Claro Armazéns Gerais Ltda.", "100%"),
        ("Rio Claro Paraguay S.A. (Ciudad del Este, Paraguai)", "75%"),
    ),
    endorsements=(
        SANCTIONS,
        Endorsement(
            "Poluição gradual e licenças ambientais",
            (
                "A exclusão de poluição gradual da Cláusula 10 não alcança Reclamações por "
                "evento súbito e acidental de derramamento de defensivos agrícolas ou de "
                "efluentes, notificado à Seguradora em até 45 dias.",
                "Aplica-se ao evento súbito a Franquia de R$ 300.000,00 do Quadro 2.",
            ),
        ),
        Endorsement(
            "Extensão de Prazo Suplementar para safra plurianual",
            (
                "O Prazo Suplementar da Cláusula 7 poderá ser requerido em até 60 dias do fim "
                "da vigência quando houver safra plurianual em curso, permanecendo inalterado o "
                "prêmio adicional de 75% do prêmio anual.",
            ),
        ),
    ),
)

DELFOS = Spec(
    stem="04_Delfos_DO_Tecnologia",
    variant=1,
    insurer="Delfos Seguradora S.A.",
    insurer_cnpj="19.377.048/0001-92",
    insurer_susep="07.019",
    insurer_address="Rua Funchal, 418, 22º andar, Vila Olímpia, São Paulo/SP",
    ouvidoria="0800 800 2019, ouvidoria@delfosseg.example",
    apolice="DEL-0351-2026-002019",
    proposta="DEL-P-2026-007766",
    processo="15414.902019/2022-06",
    emissao="22/09/2026",
    vig_ini="01/11/2026",
    vig_fim="01/11/2027",
    tomador="Nimbus Soluções Digitais S.A.",
    tomador_cnpj="36.120.845/0001-73",
    tomador_address="Rua Bandeira Paulista, 702, 8º andar, São Paulo/SP",
    tomador_profile="Plataforma de software como serviço (SaaS) para o setor financeiro; sociedade "
    "anônima de capital fechado, com investidores de venture capital e subsidiárias nos "
    "Estados Unidos e em Portugal.",
    corretor="Vértice Brokers de Seguros Ltda.",
    corretor_susep="202561409",
    vocab=Vocab(
        a_name="Cobertura A – Proteção Pessoal dos Administradores (Side A)",
        b_name="Cobertura B – Reembolso à Companhia (Side B)",
        c_name="Cobertura C – Cobertura à Companhia (Side C)",
    ),
    lmg=40_000_000,
    premio_liquido=905_000,
    parcelas=4,
    franquia_a="Sem franquia.",
    franquia_b="R$ 500.000,00 por Reclamação; R$ 2.000.000,00 para Reclamações nos EUA e Canadá.",
    franquia_c="R$ 750.000,00 por Reclamação.",
    participacao="Não há participação obrigatória do Segurado.",
    retro_style="datada",
    retro_value="15/08/2022 (data de constituição do Tomador)",
    comp_months=3,
    comp_auto=True,
    supl_months=60,
    supl_premium_pct=200,
    supl_deadline_days=30,
    runoff_months=72,
    runoff_text=(
        "Em caso de Mudança de Controle, entendida como a aquisição, direta ou indireta, de mais "
        "de 50% (cinquenta por cento) do capital votante do Tomador por terceiro, ou sua fusão "
        "ou incorporação, a apólice segue até o término da vigência e passa a cobrir apenas "
        "atos anteriores à data da operação, por 72 (setenta e dois) meses (run-off), mediante "
        "prêmio adicional de 150% (cento e cinquenta por cento) do prêmio anual, a ser pago "
        "em até 30 (trinta) dias da operação."
    ),
    notice_days=90,
    territory="Mundial, com sublimite para Estados Unidos e Canadá.",
    jurisdiction="Qualquer jurisdição, com sublimite e Franquia próprios para Estados Unidos e "
    "Canadá, observada a Cláusula de Sanções.",
    territory_style="mundial_eua",
    arbitration=True,
    forum_city="São Paulo/SP",
    pollution_style="standard",
    cyber_exclusion=True,
    coverages=coverages(
        side_a=c("R$ 40.000.000,00", "Sem franquia"),
        side_b=c("R$ 40.000.000,00", "R$ 500.000,00 por Reclamação"),
        side_c=c(LMG, "R$ 750.000,00 por Reclamação"),
        defesa=c("Integrante do LMG"),
        defesa_patrimonial=c("R$ 2.000.000,00"),
        bloqueio=c("R$ 1.000.000,00"),
        emergencial=c("R$ 1.000.000,00"),
        investigacao=c(),
        salvamento=c("R$ 1.000.000,00"),
        extradicao=c("R$ 500.000,00"),
        multas=c("R$ 3.000.000,00"),
        novas_subs=c(note="Para subsidiárias nos EUA, exige-se notificação prévia em 30 dias."),
        trabalhista=c("R$ 5.000.000,00"),
        imagem=c("R$ 1.000.000,00"),
        adv_internos=c(),
        contadores=c(),
        corporais=e(),
        materiais=e(),
        morais=c("R$ 3.000.000,00"),
        eo=c("R$ 5.000.000,00"),
        regulatorios=c("R$ 2.000.000,00"),
        crise=c("R$ 2.000.000,00"),
        herdeiros=c(),
        ambiental=e(),
        sociedade_contra=c(note="Inclui Reclamações de investidores de venture capital."),
        sxs=c(),
        atos_lesivos=c("R$ 3.000.000,00 (só Custos de Defesa)"),
        exterior=c("R$ 10.000.000,00 (Estados Unidos e Canadá)", "R$ 1.000.000,00 por Reclamação"),
        demissao=c("12 (doze) meses"),
    ),
    insureds=(
        ("Conselho de Administração", "Membros titulares, inclusive indicados por investidores."),
        ("Diretoria", "Diretores estatutários e Chief Officers (CEO, CFO, CTO, CISO)."),
        ("Comitê de Auditoria", "Membros do comitê de auditoria e de ética."),
        ("Empregados com poderes de gestão", "Vice-presidentes e diretores executivos."),
    ),
    subsidiaries=(
        ("Nimbus Digital Inc. (Delaware, EUA)", "100%"),
        ("Nimbus Soluções Digitais Unipessoal Lda. (Lisboa, Portugal)", "100%"),
    ),
    endorsements=(
        SANCTIONS,
        Endorsement(
            "Cláusula de jurisdição e lei dos Estados Unidos e Canadá",
            (
                "Para Reclamações apresentadas nos Estados Unidos da América ou no Canadá, "
                "aplica-se o sublimite de R$ 10.000.000,00 do Quadro 1, a Franquia de "
                "R$ 2.000.000,00 e a regra de que os Custos de Defesa integram o sublimite.",
                "A Seguradora poderá indicar escritório de advocacia local aprovado. Os "
                "honorários serão limitados às tarifas usuais de mercado na jurisdição.",
            ),
        ),
        Endorsement(
            "Rodada de investimento e Mudança de Controle",
            (
                "O Tomador notificará a Seguradora de rodada de investimento que altere a "
                "composição do capital em mais de 25% (vinte e cinco por cento), em até 30 dias. "
                "Não havendo Mudança de Controle, a apólice permanece inalterada.",
            ),
        ),
    ),
)

FENIX = Spec(
    stem="05_Fenix_Austral_DO_Financeiro",
    variant=0,
    insurer="Fênix Austral Seguros S.A.",
    insurer_cnpj="42.660.119/0001-25",
    insurer_susep="08.154",
    insurer_address="Av. Rio Branco, 156, 18º andar, Centro, Rio de Janeiro/RJ",
    ouvidoria="0800 900 0057, ouvidoria@fenixaustral.example",
    apolice="FEN-0351-2026-000057",
    proposta="FEN-P-2026-000913",
    processo="15414.900057/2018-92",
    emissao="25/09/2026",
    vig_ini="15/10/2026",
    vig_fim="15/10/2027",
    tomador="Terra Nova Financeira S.A.",
    tomador_cnpj="30.774.512/0001-01",
    tomador_address="Av. República do Chile, 230, 14º andar, Rio de Janeiro/RJ",
    tomador_profile="Instituição financeira autorizada pelo Banco Central do Brasil (banco "
    "múltiplo com carteira comercial e de investimento) e controladora de gestora de recursos e "
    "corretora de valores; companhia aberta.",
    corretor="Horizonte Marsh Corretora de Seguros Ltda.",
    corretor_susep="200912345",
    vocab=Vocab(
        a_name="Cobertura A – Indenização ao Segurado (Side A)",
        b_name="Cobertura B – Reembolso ao Tomador (Side B)",
        c_name="Cobertura C – Reclamações de Valores Mobiliários e Investidores",
    ),
    lmg=100_000_000,
    side_a_dic=25_000_000,
    premio_liquido=3_240_000,
    parcelas=6,
    franquia_a="Sem franquia.",
    franquia_b="R$ 1.000.000,00 por Reclamação.",
    franquia_c="R$ 2.000.000,00 por Reclamação.",
    participacao="Não há participação obrigatória do Segurado.",
    retro_style="ilimitada",
    comp_months=60,
    comp_auto=True,
    supl_months=120,
    supl_premium_pct=100,
    supl_deadline_days=60,
    runoff_months=84,
    runoff_text=(
        "Em caso de liquidação extrajudicial, intervenção, regime de administração especial "
        "temporária, incorporação, fusão, cisão ou perda do controle do Tomador (cauda ou "
        "run-off), a apólice cobre atos anteriores ao evento, por 84 (oitenta e quatro) meses, "
        "sem prêmio adicional, para todos os Segurados que tenham exercido função até a data do "
        "evento, sem redução do LMG."
    ),
    notice_days=30,
    territory="Mundial.",
    jurisdiction="Qualquer jurisdição, observadas as sanções da OFAC, da União Europeia e do "
    "Reino Unido (Cláusula de Sanções).",
    territory_style="mundial",
    arbitration=True,
    forum_city="Rio de Janeiro/RJ",
    pollution_style="sidea_carveback",
    coverages=coverages(
        side_a=c("R$ 100.000.000,00", "Sem franquia"),
        side_b=c("R$ 100.000.000,00", "R$ 1.000.000,00 por Reclamação"),
        side_c=c("R$ 50.000.000,00", "R$ 2.000.000,00 por Reclamação"),
        defesa=c("Integrante do LMG"),
        defesa_patrimonial=c(),
        bloqueio=c("R$ 5.000.000,00"),
        depositos=c("R$ 5.000.000,00"),
        emergencial=c("R$ 2.000.000,00"),
        investigacao=c("R$ 10.000.000,00"),
        salvamento=c("R$ 3.000.000,00"),
        entidade_externa=c("R$ 5.000.000,00"),
        extradicao=c("R$ 2.000.000,00"),
        inabilitacao=c("R$ 5.000.000,00"),
        multas=c("R$ 10.000.000,00"),
        novas_subs=c(),
        trabalhista=e(),
        imagem=c("R$ 1.500.000,00"),
        tributaria=c("R$ 5.000.000,00"),
        adv_internos=c(),
        contadores=c(),
        corporais=e(),
        materiais=e(),
        morais=c("R$ 5.000.000,00"),
        eo=e(),
        regulatorios=c("R$ 15.000.000,00"),
        crise=c("R$ 3.000.000,00"),
        herdeiros=c(),
        solidaria=c(),
        ambiental=e(),
        sociedade_contra=c(),
        sxs=c(),
        tac=c("R$ 5.000.000,00"),
        atos_lesivos=c("R$ 10.000.000,00 (só Custos de Defesa)"),
        exterior=c(),
        aposentados=c("120 (cento e vinte) meses"),
        demissao=c("24 (vinte e quatro) meses"),
    ),
    insureds=(
        ("Conselho de Administração", "Todos os membros, inclusive independentes e suplentes."),
        (
            "Diretoria Estatutária",
            "Diretores estatutários, inclusive responsáveis por área regulada (BACEN, CVM, COAF).",
        ),
        ("Comitês", "Comitês de auditoria, de riscos, de remuneração e de compliance."),
        (
            "Empregados com poderes de gestão",
            "Gestores, gerentes executivos e oficiais de compliance.",
        ),
    ),
    subsidiaries=(
        ("Terra Nova Gestão de Recursos Ltda.", "100%"),
        ("Terra Nova Corretora de Valores S.A.", "100%"),
        ("Terra Nova Securities LLC (Nova York, EUA)", "100%"),
    ),
    endorsements=(
        SANCTIONS,
        Endorsement(
            "Sublimite regulatório e ordem de pagamento",
            (
                "Os sublimites de Custos de Investigação (R$ 10.000.000,00) e de Eventos "
                "Extraordinários com Reguladores (R$ 15.000.000,00) aplicam-se a investigações e "
                "processos do Banco Central do Brasil, da CVM, do CADE, do COAF e da SUSEP.",
                "Os sublimites integram o LMG e não são adicionais a ele.",
            ),
        ),
        Endorsement(
            "Cauda de run-off e mudança de controle",
            (
                "Comprovada a ocorrência de evento descrito na Cláusula 7, o Tomador notificará "
                "a Seguradora em até 30 dias. O run-off de 84 meses passará a vigorar "
                "automaticamente, sem prêmio adicional, a partir da data do evento.",
            ),
        ),
    ),
)

SPECS: tuple[Spec, ...] = (AURELIUS, BOREAL, CERRADO, DELFOS, FENIX)
