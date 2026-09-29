"""Biblioteca de redações de cobertura, com duas variantes por conceito e a exclusão correspondente.

Os marcadores entre chaves são preenchidos com o vocabulário da seguradora (`Vocab`) e com o
sublimite da cobertura (`{lim}`), de modo que o quadro de limites e as cláusulas nunca divergem.
"""

# chave -> (título padrão, (redação A, redação B), texto de exclusão específico ou "")
COVERAGE_TEXTS: dict[str, tuple[str, tuple[str, str], str]] = {
    "defesa_patrimonial": (
        "Custos de Defesa – Bens e Liberdade",
        (
            "Estão garantidos os Custos de Defesa do {S} em processos, cíveis ou criminais, que "
            "coloquem em risco sua liberdade ou seu patrimônio pessoal, {lim}, ainda que a "
            "Reclamação tenha sido apresentada apenas contra a pessoa física.",
            "A Seguradora responderá pelos honorários e custas de defesa técnica do {S} em "
            "ações penais e medidas constritivas patrimoniais decorrentes de {ato}, {lim}.",
        ),
        "",
    ),
    "bloqueio": (
        "Bloqueio e Indisponibilidade de Bens e Penhora On-line",
        (
            "Determinado bloqueio, arresto, sequestro ou indisponibilidade de bens ou de contas "
            "correntes do {S}, inclusive por penhora on-line, a Seguradora custeará as despesas "
            "necessárias ao seu levantamento e, quando decorrente de decisão judicial ou "
            "administrativa, a manutenção de sua subsistência, {lim}.",
            "Fica garantido o pagamento das despesas jurídicas para desconstituição de "
            "constrição patrimonial, inclusive bloqueio de conta corrente e penhora eletrônica "
            "(BacenJud/SISBAJUD), imposta ao {S} em razão de {ato}, {lim}.",
        ),
        "Não estão cobertas as despesas relativas a bloqueio ou indisponibilidade de bens do "
        "{S}, ainda que decorrentes de Reclamação garantida.",
    ),
    "depositos": (
        "Depósitos Recursais, Cauções e Garantias Judiciais",
        (
            "A Seguradora arcará com o custo de fianças, cauções, seguros-garantia e depósitos "
            "recursais exigidos do {S} para recorrer de decisão relativa a Reclamação coberta, "
            "{lim}. Os valores depositados em dinheiro serão devolvidos à Seguradora quando "
            "liberados.",
            "Serão reembolsados os prêmios e encargos de garantias judiciais e os depósitos "
            "recursais que o {S} for obrigado a prestar para interposição de recurso, {lim}.",
        ),
        "",
    ),
    "emergencial": (
        "Custos Emergenciais de Defesa",
        (
            "Em situação de urgência, e quando não for possível obter a prévia anuência da "
            "Seguradora, os Custos de Defesa emergenciais incorridos nas primeiras 72 (setenta e "
            "duas) horas serão reembolsados, {lim}, desde que o Sinistro seja comunicado em até "
            "5 (cinco) dias úteis.",
            "A Seguradora aceita, sem anuência prévia, honorários de defesa urgente incorridos "
            "até 3 (três) dias após a citação, intimação ou medida de busca e apreensão, {lim}.",
        ),
        "",
    ),
    "investigacao": (
        "Custos de Investigação",
        (
            "A Seguradora reembolsará ou adiantará os Custos de Defesa razoáveis do {S} em razão "
            "de Investigação Formal instaurada por autoridade administrativa, policial, "
            "regulatória ou autorreguladora, ainda que não tenha havido Reclamação, desde que o "
            "{S} seja intimado a prestar depoimento ou esclarecimentos, {lim}.",
            "Estão garantidos os custos de assessoria jurídica do {S} para comparecimento e "
            "defesa em inquéritos, processos administrativos sancionadores e comissões "
            "parlamentares de inquérito, {lim}, desde que a intimação seja notificada nos termos "
            "da Cláusula 11.",
        ),
        "Ficam excluídos os custos de investigações, inquéritos e processos administrativos "
        "sancionadores instaurados antes da notificação prevista na Cláusula 11.",
    ),
    "salvamento": (
        "Salvamento e Contenção",
        (
            "A Seguradora reembolsará as despesas razoáveis, previamente autorizadas, que o {S} ou "
            "o {T} tenham realizado para evitar ou reduzir a Perda decorrente de {ato} já "
            "notificado (salvamento e contenção do Sinistro), {lim}, nos termos do art. 771, "
            "parágrafo único, do Código Civil.",
            "Serão indenizadas as despesas de mitigação e contenção do Sinistro, comprovadamente "
            "necessárias para limitar o valor da Reclamação, {lim}.",
        ),
        "",
    ),
    "entidade_externa": (
        "Diretor de Entidade Externa",
        (
            "Estende-se a cobertura ao {S} que, por indicação escrita do {T}, exerça cargo em "
            "Entidade Externa, {lim}. Esta cobertura é excedente a qualquer seguro ou "
            "indenização prestado pela Entidade Externa.",
            "Fica coberta a atuação do {S} como conselheiro ou diretor de entidade sem fins "
            "lucrativos ou associação setorial indicada pelo {T}, {lim}, em caráter excedente.",
        ),
        "",
    ),
    "extradicao": (
        "Extradição",
        (
            "Estão garantidos os Custos de Defesa do {S} em processo de extradição requerido por "
            "Estado estrangeiro em razão de {ato}, {lim}.",
            "A Seguradora reembolsará as despesas de defesa em pedido de extradição ou de "
            "cooperação penal internacional contra o {S}, {lim}.",
        ),
        "",
    ),
    "avalista": (
        "Avalistas, Fiadores e Fiel Depositário",
        (
            "A cobertura se estende ao {S} que tenha prestado aval, fiança ou garantia pessoal, "
            "ou assumido encargo de fiel depositário, em favor do {T} ou de Subsidiária, em razão "
            "do exercício de suas funções, {lim}.",
            "Ficam garantidas as Reclamações contra o {S} na condição de avalista, fiador ou "
            "depositário de bens do {T}, desde que a garantia tenha sido aprovada por órgão "
            "competente, {lim}.",
        ),
        "Não estão cobertas Reclamações contra o {S} na qualidade de avalista, fiador ou "
        "depositário de bens do {T}.",
    ),
    "inabilitacao": (
        "Inabilitação de Segurado",
        (
            "A Seguradora reembolsará os Custos de Defesa do {S} em processo que possa resultar "
            "em sua inabilitação temporária para o exercício de cargos de administração, {lim}.",
            "Fica garantida a defesa do {S} em processo de inabilitação ou desqualificação "
            "profissional promovido por órgão regulador, {lim}.",
        ),
        "",
    ),
    "multas": (
        "Multas e Penalidades",
        (
            "Estão cobertas as multas e penalidades civis e administrativas impostas "
            "pessoalmente ao {S}, na medida em que sejam seguráveis pela lei aplicável, {lim}. "
            "A Seguradora pagará também os Custos de Defesa do processo que as originou.",
            "A Seguradora indenizará as sanções pecuniárias aplicadas ao {S} por autoridades "
            "administrativas ou reguladoras, exceto multas de natureza penal ou de caráter "
            "punitivo não segurável, {lim}.",
        ),
        "Ficam excluídas multas, penalidades e sanções pecuniárias de qualquer natureza "
        "impostas ao {S}, restando garantidos apenas os Custos de Defesa do respectivo "
        "processo, se contratados.",
    ),
    "novas_subs": (
        "Novas Subsidiárias",
        (
            "Consideram-se automaticamente Subsidiárias as sociedades constituídas ou adquiridas "
            "pelo {T} após o início da vigência cujo ativo total não exceda 25% (vinte e cinco "
            "por cento) do ativo consolidado do {T}. Acima desse percentual, a inclusão depende "
            "de aceitação pela Seguradora e de eventual prêmio adicional. A extensão é concedida {lim}.",
            "As sociedades adquiridas ou constituídas durante a vigência passam a ser cobertas "
            "por 90 (noventa) dias, por atos posteriores à aquisição, prazo em que o {T} deverá "
            "requerer a inclusão definitiva, sob pena de cessação da cobertura. A extensão é concedida {lim}.",
        ),
        "",
    ),
    "trabalhista": (
        "Práticas Trabalhistas Indevidas",
        (
            "Estão cobertas as Reclamações contra o {S} por Práticas Trabalhistas Indevidas, "
            "assim entendidas demissão sem justa causa alegadamente abusiva, discriminação, "
            "assédio moral ou sexual e retaliação, {lim}. A cobertura não abrange verbas "
            "rescisórias, salários, encargos e benefícios devidos pelo {T}.",
            "Fica garantida a responsabilidade do {S} por Reclamação de empregado, ex-empregado "
            "ou candidato a emprego fundada em assédio, discriminação ou dispensa "
            "discriminatória, {lim}, excluídas as obrigações trabalhistas e previdenciárias "
            "próprias do empregador.",
        ),
        "Ficam excluídas as Reclamações decorrentes de relação de emprego, inclusive assédio, "
        "discriminação e dispensa, restando garantidos apenas os Custos de Defesa do {S}, "
        "quando houver sublimite indicado no Quadro 1.",
    ),
    "imagem": (
        "Proteção da Imagem Pessoal e Relações Públicas",
        (
            "A Seguradora reembolsará as despesas com consultoria de comunicação e relações "
            "públicas contratadas com sua prévia aprovação para proteger a imagem pessoal do "
            "{S} após a notificação de Reclamação coberta, {lim}.",
            "Estão garantidas as despesas razoáveis de assessoria de imprensa e de resposta "
            "pública destinadas a restaurar a reputação do {S} atingida por Reclamação coberta, "
            "{lim}.",
        ),
        "",
    ),
    "tributaria": (
        "Responsabilidade Tributária e Previdenciária",
        (
            "Estão cobertas as Reclamações que atribuam ao {S} responsabilidade pessoal por "
            "tributos e contribuições não recolhidos pelo {T} (arts. 135 do Código Tributário "
            "Nacional e 50 do Código Civil), {lim}. O tributo em si, seus acréscimos e "
            "a multa fiscal ficam excluídos, salvo se expressamente indicados no Quadro 1.",
            "Fica garantida a defesa e a condenação do {S} em redirecionamento de execução "
            "fiscal ou cobrança de contribuições previdenciárias por responsabilidade pessoal "
            "do administrador, {lim}.",
        ),
        "Ficam excluídos tributos, contribuições, encargos e multas fiscais, bem como "
        "Reclamações decorrentes de responsabilidade tributária ou previdenciária do {S}, "
        "ressalvados os Custos de Defesa quando houver sublimite indicado no Quadro 1.",
    ),
    "adv_internos": (
        "Advogados Internos",
        (
            "O empregado do {T} que exerça função jurídica interna é {S} apenas quando atuar "
            "como membro de órgão de administração ou por delegação expressa da diretoria, "
            "{lim}. Não estão cobertas Reclamações por serviços jurídicos prestados a terceiros.",
            "Equiparam-se a {S_pl} os advogados internos do {T} pelos atos praticados no "
            "exercício de suas funções de assessoramento à administração, {lim}.",
        ),
        "Não são {S_pl} os advogados internos do {T}, salvo se integrarem órgão estatutário.",
    ),
    "contadores": (
        "Contadores, Gerentes de Riscos e Auditores Internos",
        (
            "São equiparados ao {S} os contadores, gerentes de riscos, de conformidade e "
            "auditores internos do {T}, pelos atos praticados nessa função e dentro do escopo "
            "de suas atribuições, {lim}.",
            "Estende-se a cobertura aos empregados que atuem como contador, auditor interno ou "
            "gestor de riscos, exclusivamente por falhas de gestão, {lim}.",
        ),
        "",
    ),
    "corporais": (
        "Danos Corporais",
        (
            "Estão cobertas as Reclamações por danos corporais, inclusive morte, sofridos por "
            "terceiros, quando imputados ao {S} por falha de gestão, {lim}.",
            "Fica garantida a responsabilidade pessoal do {S} por lesões físicas a terceiros "
            "decorrentes de decisão administrativa, {lim}.",
        ),
        "Ficam excluídas Reclamações por lesão corporal, doença, sofrimento físico ou morte "
        "de qualquer pessoa, salvo Custos de Defesa se houver sublimite indicado no Quadro 1.",
    ),
    "materiais": (
        "Danos Materiais",
        (
            "Estão cobertas as Reclamações por danos materiais causados a terceiros por {ato} "
            "do {S}, {lim}.",
            "Fica garantida a indenização por danos patrimoniais a terceiros decorrentes de "
            "{ato}, {lim}.",
        ),
        "Ficam excluídas Reclamações por danos ou perda de bens tangíveis, inclusive sua "
        "privação de uso, salvo Custos de Defesa se houver sublimite indicado no Quadro 1.",
    ),
    "morais": (
        "Danos Morais",
        (
            "Estão cobertas as indenizações por danos morais impostas ao {S} em decorrência de "
            "Reclamação coberta, {lim}.",
            "A expressão “Perdas” compreende a condenação por dano moral, individual ou "
            "coletivo, imposta ao {S} em Reclamação coberta, {lim}.",
        ),
        "",
    ),
    "eo": (
        "Erros e Omissões – Prestação de Serviços Profissionais",
        (
            "Estende-se a cobertura às Reclamações de clientes do {T} por falha na prestação de "
            "serviços profissionais descritos na Especificação, {lim}, exclusivamente quando "
            "a Reclamação for dirigida também contra o {S} pessoa física.",
            "A Seguradora responderá pela responsabilidade do {S} em Reclamações de terceiros "
            "por erro, omissão ou negligência na prestação dos serviços profissionais do {T}, "
            "{lim}, em caráter excedente a qualquer seguro de responsabilidade civil profissional.",
        ),
        "Ficam excluídas Reclamações decorrentes da prestação ou da omissão de prestação de "
        "serviços profissionais a terceiros, em qualquer atividade (erros e omissões), "
        "ressalvada a cobertura de administradores por falha de supervisão, se contratada.",
    ),
    "regulatorios": (
        "Eventos Extraordinários com Reguladores",
        (
            "Estão cobertos os Custos de Defesa e de assessoria do {S} em eventos "
            "extraordinários iniciados por reguladores, como fiscalização especial, intervenção, "
            "regime especial ou termo de cessação, {lim}.",
            "A Seguradora reembolsará as despesas do {S} decorrentes de ato extraordinário de "
            "órgão regulador ou supervisor que dê origem a Investigação Formal, {lim}.",
        ),
        "",
    ),
    "crise": (
        "Gerenciamento de Crise",
        (
            "A Seguradora reembolsará ao {T} as despesas com consultoria de gerenciamento de "
            "crise contratada após um Evento de Crise notificado, pelo prazo de até 90 dias, "
            "{lim}.",
            "Fica garantido o custo de consultores de comunicação e de crise contratados pelo "
            "{T} para conter os efeitos reputacionais de um Evento de Crise, {lim}.",
        ),
        "",
    ),
    "herdeiros": (
        "Herdeiros, Sucessores, Espólio, Cônjuge e Companheiro",
        (
            "A cobertura se estende a herdeiros, sucessores, representantes legais, ao espólio "
            "e ao cônjuge ou companheiro do {S}, quando Reclamados exclusivamente por "
            "ato do {S} coberto por esta apólice, {lim}.",
            "Em caso de morte, incapacidade ou falência do {S}, a cobertura beneficia seu "
            "espólio, herdeiros e representantes legais, bem como o cônjuge ou companheiro, "
            "em relação a bens comuns, {lim}.",
        ),
        "",
    ),
    "solidaria": (
        "Responsabilidade Solidária sobre Bens",
        (
            "Fica garantida a Reclamação em que o patrimônio comum do {S} e de seu cônjuge ou "
            "companheiro responda solidariamente por dívida decorrente de {ato} coberto, {lim}.",
            "Estão cobertas as Perdas decorrentes da solidariedade patrimonial do {S}, por "
            "regime de bens, em Reclamação coberta, {lim}.",
        ),
        "",
    ),
    "ambiental": (
        "Responsabilidade Civil Ambiental",
        (
            "Estão cobertas as Reclamações contra o {S} por dano ambiental decorrente de "
            "decisão de gestão, com base nos arts. 3º e 14 da Lei 6.938/1981 e 225 da "
            "Constituição Federal, {lim}. Ficam excluídos os custos de limpeza, remediação e "
            "recuperação da área, a cargo do {T}.",
            "A Seguradora responderá, {lim}, pelos Custos de Defesa e pelas indenizações "
            "a terceiros impostas ao {S} em ação civil pública ou processo administrativo por "
            "poluição, nas condições da Cláusula 10.",
        ),
        "",
    ),
    "sociedade_contra": (
        "Reclamações da Sociedade, Acionistas ou Sócios contra o Segurado",
        (
            "Estão cobertas as Reclamações contra o {S} apresentadas pelo {T}, por acionista "
            "ou por sócio, inclusive ação social de responsabilidade (art. 159 da Lei 6.404/1976) "
            "e ação derivada, {lim}.",
            "Fica garantida a Reclamação proposta contra o {S} por acionistas, quotistas ou "
            "pela própria sociedade, quando decorrente de {ato}, {lim}.",
        ),
        "Ficam excluídas Reclamações apresentadas contra o {S} pelo {T}, por acionistas ou por "
        "sócios, salvo ação derivada proposta sem a colaboração ativa do {T} ou do {S}.",
    ),
    "sxs": (
        "Reclamações entre Segurados",
        (
            "Estão cobertas as Reclamações apresentadas por um {S} contra outro {S}, desde que "
            "não instigadas por outro {S}, {lim}.",
            "Fica garantida a Reclamação entre {S_pl}, ressalvadas as decorrentes de "
            "litígio societário controlado, {lim}.",
        ),
        "Ficam excluídas as Reclamações apresentadas por um {S} contra outro {S}, salvo as "
        "originadas de denúncia de irregularidade (whistleblower) ou de ação derivada.",
    ),
    "tac": (
        "TAC, Termos de Compromisso e Acordos com Autoridades",
        (
            "A Seguradora arcará com os Custos de Defesa e com os valores acordados pelo {S} em "
            "Termo de Ajustamento de Conduta (TAC), Termo de Compromisso (TC) ou acordo "
            "administrativo com autoridade, {lim}, desde que precedidos de consentimento.",
            "Estão cobertas as despesas de negociação e o valor pago pelo {S} em TAC, TC, "
            "acordo de leniência ou de não persecução, na parte segurável, {lim}.",
        ),
        "Ficam excluídos os valores pagos em TAC, TC, acordos de leniência e congêneres.",
    ),
    "atos_lesivos": (
        "Atos Lesivos à Administração Pública (Lei 12.846/2013)",
        (
            "Estão garantidos os Custos de Defesa do {S} em processo administrativo ou judicial "
            "fundado na Lei 12.846/2013 (Lei Anticorrupção), {lim}, não se pagando multas, "
            "ressarcimentos ou perdimento de bens.",
            "A Seguradora responderá pelos honorários de defesa em investigação ou "
            "responsabilização por Atos Lesivos à Administração Pública, {lim}, restando "
            "excluída qualquer condenação pecuniária.",
        ),
        "Ficam excluídas Reclamações e Investigações relacionadas a Atos Lesivos à "
        "Administração Pública, corrupção, suborno ou lavagem de dinheiro, inclusive os "
        "Custos de Defesa, até decisão final que afaste a ocorrência.",
    ),
    "exterior": (
        "Processos no Exterior",
        (
            "Estão cobertas as Reclamações e Investigações Formais apresentadas fora do Brasil, "
            "em qualquer jurisdição não sancionada, {lim}, observados o Âmbito Territorial e a "
            "Cláusula de Sanções.",
            "Fica garantida a defesa e a indenização do {S} em processo instaurado em "
            "jurisdição estrangeira, {lim}. A indenização será paga em reais, à taxa de câmbio "
            "PTAX de venda do dia do pagamento.",
        ),
        "Ficam excluídas Reclamações e Investigações apresentadas ou processadas fora do "
        "território brasileiro, ainda que decorrentes de {ato} praticado no Brasil.",
    ),
}

# Coberturas tratadas na Cláusula 4 (defesa e despesas) e na Cláusula 5 (extensões).
CLAUSE_4_KEYS = (
    "defesa_patrimonial",
    "bloqueio",
    "depositos",
    "emergencial",
    "investigacao",
    "salvamento",
)
CLAUSE_5_KEYS = (
    "entidade_externa",
    "extradicao",
    "avalista",
    "inabilitacao",
    "multas",
    "novas_subs",
    "trabalhista",
    "imagem",
    "tributaria",
    "adv_internos",
    "contadores",
    "corporais",
    "materiais",
    "morais",
    "eo",
    "regulatorios",
    "crise",
    "herdeiros",
    "solidaria",
    "ambiental",
    "sociedade_contra",
    "sxs",
    "tac",
    "atos_lesivos",
    "exterior",
)

POLLUTION_TEXTS: dict[str, tuple[str, ...]] = {
    "absolute": (
        "Fica excluída, de forma absoluta, toda Reclamação direta ou indiretamente decorrente "
        "de, baseada em, atribuível a ou relacionada com poluição, contaminação, emissão, "
        "descarga, dispersão, liberação ou vazamento de Poluentes, real, suposto ou "
        "ameaçado, bem como qualquer ordem, exigência ou pedido de limpeza, remoção, "
        "remediação, contenção ou tratamento de Poluentes.",
        "A exclusão do item anterior prevalece sobre qualquer outra disposição desta apólice e "
        "alcança, inclusive, os Custos de Defesa, as Coberturas A e B e qualquer endosso, "
        "ainda que a Reclamação seja fundada em falha de gestão, de supervisão ou de "
        "divulgação de informações sobre o risco ambiental.",
    ),
    "sidea_carveback": (
        "Ficam excluídas as Reclamações decorrentes de poluição, contaminação ou dano ambiental "
        "de qualquer natureza, inclusive as ordens de limpeza e remediação.",
        "Em exceção à exclusão anterior, a Seguradora pagará as Perdas da Cobertura A do "
        "{S} quando o {T} estiver impedido de indenizá-lo por insolvência ou por vedação "
        "legal, sem sublimite específico, excluídos os Custos de Defesa do {T}.",
    ),
    "standard": (
        "Ficam excluídas as Reclamações baseadas em poluição, assim entendida a presença, a "
        "emissão ou a liberação de Poluentes, e em custos de limpeza ou remediação.",
        "A exclusão não se aplica à Cobertura A, nem às Reclamações de acionistas por queda no "
        "valor de suas participações, desde que não fundadas em ordem de remediação.",
    ),
    "cleanup_only": (
        "Ficam excluídos os custos de limpeza, remoção, remediação, monitoramento e "
        "recuperação de área contaminada, ainda que impostos ao {S}, bem como Reclamações "
        "por poluição intencional ou por descumprimento de licença ou ordem ambiental "
        "conhecida.",
        "Observada a exclusão, as Reclamações por dano ambiental decorrentes de decisão de "
        "gestão estão cobertas nos termos da Cláusula 5, dentro do sublimite indicado no "
        "Quadro 1.",
    ),
    "coverage": (
        "Fica excluída a poluição gradual, contínua ou previsível, assim como a decorrente "
        "de descumprimento doloso da legislação ambiental ou de licenças conhecidas do {T} "
        "antes do início da vigência.",
        "Fora as hipóteses anteriores, as Reclamações por dano ambiental, inclusive multas "
        "ambientais seguráveis, estão cobertas nos termos da Cláusula 5. Ficam excluídos "
        "apenas os custos de limpeza e remediação que constituam obrigação própria do {T}.",
    ),
}
