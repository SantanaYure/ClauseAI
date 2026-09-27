# F — Base de conhecimento D&O

## 1. Papel deste documento

Este documento consolida as três bases de negócio do ClauseAI e é a **fonte de verdade de domínio** para extração, normalização, pontuação, comparação e apresentação. As specs técnicas (`specs/`, `architecture/`, `AI_SYSTEM_SPEC.md`) implementam o que está aqui; em caso de conflito, prevalece a ordem de precedência abaixo.

| Ordem | Fonte | Arquivo no repositório | Uso |
|---|---|---|---|
| 1 | Enunciado do Projeto Final (I2A2, “Plataforma Inteligente para Análise e Comparação de Apólices D&O”) | externo (`Desafios.pdf`, págs. 19–24) | requisitos mínimos, entregáveis e critérios de avaliação |
| 2 | Matriz de equivalência / dicionário D&O | [`sources/01_matriz_equivalencia_dicionario_do.xlsx`](sources/01_matriz_equivalencia_dicionario_do.xlsx) | conceitos-base, variantes, regras de extração e status |
| 3 | Pesos para análise e decisão | [`sources/02_pesos_analise_decisao_apolice.docx`](sources/02_pesos_analise_decisao_apolice.docx) | importância, pesos técnicos, Resultado-base, Fator de Ajuste, scores e pareceres |
| 4 | Prompts do agente comparador | [`sources/03_prompts_agente_comparador_apolice.docx`](sources/03_prompts_agente_comparador_apolice.docx) | comportamento da IA em cada etapa, rastreabilidade e regras contra inferência |

Os arquivos originais não devem ser editados para “corrigir” o software. Mudanças de negócio entram como nova versão do arquivo-fonte e deste documento (`knowledge_base_version`).

## 2. Fluxo exigido

O desafio e o prompt mestre definem as mesmas sete etapas, que estruturam toda a arquitetura:

1. Recebimento dos documentos.
2. Extração automática do conteúdo (leitura nativa de PDF e OCR/LLM multimodal).
3. Organização das informações por documento, seguradora, seção, cláusula, cobertura e conceito-base.
4. Armazenamento estruturado de evidências, metadados, pesos e resultados.
5. Consulta por conceito, cobertura, termo, seguradora, cláusula ou apólice.
6. Comparação entre duas ou mais apólices (o MVP compara exatamente duas).
7. Apresentação em tabelas, indicadores, pareceres e resumo executivo.

## 3. Regras invioláveis

Estas regras valem para código, prompts e UI:

1. Preservar o trecho literal da fonte, com arquivo, página, seção, cláusula e versão quando disponíveis.
2. Diferenciar **definição, previsão de cobertura, contratação, exclusão, condição e ausência de informação**.
3. Não considerar uma cobertura contratada só porque o termo aparece nas Condições Gerais.
4. Não transformar ausência de localização em exclusão (“Não localizado” ≠ “Excluído”).
5. Não tratar correspondência temática como equivalência automática.
6. Não inventar dados, limites, cláusulas, páginas ou interpretações.
7. Pesos indicam importância para a decisão; não comprovam contratação nem substituem o texto contratual.
8. Não usar ausência de evidência como vantagem automática da outra apólice.
9. Não alterar pesos silenciosamente; todo ajuste gera “Peso Ajustado” com motivo.
10. Manter separados: evidência extraída, interpretação semântica, contratação comprovada, pontuação matemática, análise qualitativa e recomendação executiva.
11. A decisão deve ser explicável, reproduzível e auditável.
12. Em ambiguidade, ausência de documento, divergência material, contratação não comprovada, OCR de baixa confiança, limite não comparável ou informação insuficiente, informar o ponto e exibir a frase padrão **“Consulte seu corretor de seguros.”** (constante `BROKER_GUIDANCE`).

## 4. Vocabulários controlados

### 4.1 Status documental (dicionário, aba “03 Status e Regras”)

| Código | Rótulo | Definição |
|---|---|---|
| `CONTRACTED` | Contratado | Cobertura identificada como aplicável; especificação ou endosso confirma contratação. |
| `NOT_FOUND` | Não localizado | Não identificado na fonte ou material recebido. |
| `DIVERGENT` | Divergente | Fontes apresentam redações ou extensões diferentes. |
| `NEEDS_VALIDATION` | Necessita validação | Redação exige conferência de alcance, limite ou cláusula. |
| `EXCLUDED` | Exclusão | Texto trata o risco como excluído (exclusão expressa). |
| `COMPARE_WORDING` | Comparar redação | Correspondência temática sem equivalência automática. |

### 4.2 Contratação por apólice (pesos, seção 2)

`CONTRACTED` (contratada), `NOT_PROVEN` (não comprovada: há menção, sem confirmação contratual), `NOT_FOUND` (não localizada), `EXCLUDED` (excluída), `DIVERGENT` (divergente).

Na tabela final (prompt 15): “N/A” somente quando o campo não se aplica; “Não localizado” quando a busca não encontra; “Não comprovado” quando há menção sem confirmação; “Excluído” somente com exclusão expressa.

### 4.3 Tipo de ocorrência (prompt 4)

`DEFINITION`, `BASIC_COVERAGE`, `ADDITIONAL_COVERAGE`, `EXTENSION`, `EXCLUSION`, `CONDITION`, `OBLIGATION`, `PROCEDURE`, `LIMIT`, `TERM` (prazo), `REFERENCE`.

### 4.4 Relação terminológica (prompt 4)

`EXACT_MATCH`, `LEXICAL_VARIANT`, `ABBREVIATION`, `THEMATIC_MATCH`, `POSSIBLE_EQUIVALENCE`, `RELATED_BUT_DISTINCT`, `UNRELATED`. Quando a ocorrência puder pertencer a mais de um conceito, registrar todas as hipóteses e aplicar `BROKER_GUIDANCE`.

### 4.5 Tipo de documento (prompt 2)

`POLICY` (apólice), `GENERAL_CONDITIONS`, `SPECIAL_CONDITIONS`, `PARTICULAR_CONDITIONS`, `ENDORSEMENT`, `SPECIFICATION`, `PROPOSAL`, `OTHER`. Somente Condições Gerais não bastam para declarar contratação efetiva.

### 4.6 Parecer por conceito (pesos, seção 7; prompt 7)

| Situação | Parecer |
|---|---|
| Diferença de pontos ponderados < 0,10 e sem diferença material | `EQUIVALENT` — Equivalente |
| Apólice 01 com pontuação superior e evidência suficiente | `FAVORS_A` — Favorável à Apólice 01 |
| Apólice 02 com pontuação superior e evidência suficiente | `FAVORS_B` — Favorável à Apólice 02 |
| Conflito, ausência ou evidência não comparável | `INCONCLUSIVE` — Inconclusivo |
| Ambas expressamente excluídas | `EQUIVALENT_BOTH_EXCLUDED` — Equivalente – ambas excluídas |
| Uma contratada e a outra não localizada/excluída | favorável à apólice com cobertura, **sujeito à confirmação documental** |

Nunca declarar equivalência só pelo nome da cobertura; diferenças de gatilho, limite, exclusão, beneficiário ou condição impedem `EQUIVALENT`.

## 5. Catálogo de conceitos

### 5.1 Dicionário comparativo (35 conceitos, 25 domínios)

Base extraída da comparação AKAD × KOVR. As redações das duas seguradoras são **exemplos de evidência**, não equivalências automáticas. Cada conceito tem, na aba “02 Base de Treinamento”, variantes/gatilhos, pergunta do modelo, regra de extração (“extrair trecho literal, fonte, cláusula, página e status de contratação”) e indicação de revisão humana.

| ID | Domínio | Conceito-base | Status na base | Revisão humana |
|---|---|---|---|---|
| DO-001 | Partes | Segurado | A comparar | Recomendada |
| DO-002 | Coberturas básicas | Cobertura A – Indenização ou reembolso em nome dos administradores (Garantia A) | Necessita validação | Sim |
| DO-003 | Coberturas básicas | Cobertura B – Reembolso à Sociedade (Garantia B) | Necessita validação | Sim |
| DO-004 | Coberturas adicionais | Cobertura C – Cobertura à Sociedade (valores mobiliários, CVM) | Não localizado em uma fonte | Sim |
| DO-005 | Defesa | Adiantamento de custos de defesa | A comparar | Recomendada |
| DO-006 | Defesa patrimonial | Custo de defesa – bens e liberdade | A comparar | Recomendada |
| DO-007 | Defesa patrimonial | Bloqueio e indisponibilidade de bens / penhora on-line | A comparar | Recomendada |
| DO-008 | Investigação | Custos de investigação | A comparar | Recomendada |
| DO-009 | Multas | Custo de defesa / depósitos recursais para multas | A comparar | Recomendada |
| DO-010 | Emergencial | Custos emergenciais | A comparar | Recomendada |
| DO-011 | Entidades externas | Diretor de entidade externa | Necessita validação | Sim |
| DO-012 | Patrimonial | Extradição | A comparar | Recomendada |
| DO-013 | Garantias pessoais | Avalistas, fiadores e fiel depositário | A comparar | Recomendada |
| DO-014 | Inabilitação | Inabilitação de um segurado | A comparar | Recomendada |
| DO-015 | Multas | Multas e penalidades | A comparar | Recomendada |
| DO-016 | Societário | Novas subsidiárias | A comparar | Recomendada |
| DO-017 | Trabalhista | Práticas trabalhistas | A comparar | Recomendada |
| DO-018 | Prazos | Prazo complementar para aposentados | Necessita validação | Sim |
| DO-019 | Prazos | Prazo complementar para demissões voluntárias | A comparar | Recomendada |
| DO-020 | Imagem | Proteção da imagem pessoal / relações públicas | A comparar | Recomendada |
| DO-021 | Tributária | Responsabilidade tributária | A comparar | Recomendada |
| DO-022 | Profissional | Advogados internos | Necessita validação | Sim |
| DO-023 | Profissional | Contadores internos, gerentes de riscos e auditores internos | A comparar | Recomendada |
| DO-024 | Danos | Danos corporais | A comparar | Recomendada |
| DO-025 | Danos | Danos materiais | A comparar | Recomendada |
| DO-026 | Danos | Danos morais | A comparar | Recomendada |
| DO-027 | Profissional | Erros e omissões (E&O) | A comparar | Recomendada |
| DO-028 | Crise | Eventos extraordinários com reguladores | Necessita validação | Sim |
| DO-029 | Crise | Gerenciamento de crise (PJ) | A comparar | Recomendada |
| DO-030 | Sucessão | Herdeiros, sucessores, representantes legais, espólio, cônjuge e companheiro | Necessita validação | Sim |
| DO-031 | Responsabilidade solidária | Cobertura para responsabilidade solidária de bens | A comparar | Recomendada |
| DO-032 | Ambiental | Responsabilidade civil ambiental por poluição | A comparar | Recomendada |
| DO-033 | Relacionamento | Reclamações contra o Segurado pelo Tomador, acionista ou sócio (Sociedade contra Segurado) | Não localizado em uma fonte | Sim |
| DO-034 | Relacionamento | Reclamações contra o Segurado por outro Segurado (Segurado contra Segurado) | Não localizado em uma fonte | Sim |
| DO-035 | Acordos | TAC, TC e acordos | Não localizado em uma fonte | Sim |

A planilha grafa “Extradiação” em DO-012; o catálogo usa “Extradição” e mantém a grafia original como variante de busca.

### 5.2 Conceitos acrescentados pela matriz de pesos

A matriz de pesos usa conceitos que não existem no dicionário. Eles recebem IDs novos no catálogo, com status inicial `NEEDS_VALIDATION` e variantes a completar pela equipe de seguros:

| ID | Domínio | Conceito-base | Variantes iniciais |
|---|---|---|---|
| DO-036 | Limites | LMG – Limite Máximo de Garantia | LMG; limite máximo de garantia; limite máximo de indenização; LMI agregado |
| DO-037 | Prazos | Retroatividade | data retroativa; período de retroatividade; cobertura retroativa |
| DO-038 | Âmbito | Territorialidade | âmbito territorial; território; abrangência geográfica; jurisdição |
| DO-039 | Prazos | Prazo complementar | prazo complementar; período complementar para apresentação de reclamações |
| DO-040 | Prazos | Prazo suplementar | prazo suplementar; período suplementar; extensão contratável pós-vigência |
| DO-041 | Sinistro | Cláusula de notificação | notificação de circunstância; aviso de fatos ou circunstâncias |
| DO-042 | Anticorrupção | Atos lesivos | atos lesivos; Lei 12.846/2013; lei anticorrupção |
| DO-043 | Âmbito | Processos no exterior | processos no exterior; reclamações fora do Brasil; jurisdição estrangeira |
| DO-044 | Sinistro | Salvamento e contenção | despesas de salvamento; contenção de sinistro; mitigação |

## 6. Matriz de pesos

### 6.1 Pesos técnicos (peso-base)

Escala declarada de 1 a 10; a matriz inicial usa as faixas 10, 7, 4 e 2.

| Peso | Nível | Conceito | ID(s) no catálogo | Justificativa |
|---|---|---|---|---|
| 10 | Crítica | LMG | DO-036 | Capacidade financeira máxima da apólice. |
| 10 | Crítica | Garantia A | DO-002 | Proteção patrimonial direta do administrador. |
| 10 | Crítica | Garantia B | DO-003 | Reembolso à sociedade quando esta indeniza o administrador. |
| 10 | Crítica | Custos de Defesa | DO-005 (principal), DO-006 (relacionado) | Cobertura central e frequentemente acionada em D&O. |
| 10 | Crítica | Retroatividade | DO-037 | Proteção para atos ou fatos anteriores à vigência. |
| 10 | Crítica | Territorialidade | DO-038 | Define a abrangência geográfica da proteção. |
| 10 | Crítica | Prazo Complementar | DO-039 | Proteção para reclamações após o fim da vigência. |
| 10 | Crítica | Prazo Suplementar | DO-040 | Extensão contratável da proteção após a vigência. |
| 10 | Crítica | Cláusula de Notificação | DO-041 | Preserva a cobertura futura quando a circunstância é comunicada. |
| 10 | Crítica | Atos Lesivos | DO-042 | Exposição a riscos anticorrupção e exclusões aplicáveis. |
| 7 | Alta | Investigação | DO-008 | Parte relevante dos eventos de D&O começa por investigação. |
| 7 | Alta | Práticas Trabalhistas Indevidas | DO-017 | Fonte recorrente de reclamações contra administradores. |
| 7 | Alta | Responsabilidade Tributária | DO-021 | Pode atingir o patrimônio pessoal do administrador. |
| 7 | Alta | Segurado contra Segurado | DO-034 | Conflitos entre pessoas protegidas pela apólice. |
| 7 | Alta | Sociedade contra Segurado | DO-033 | Reclamações da sociedade contra administradores. |
| 7 | Alta | Segurados Aposentados | DO-018 | Reclamações tardias após desligamento. |
| 7 | Alta | Multas e Penalidades | DO-015 (principal), DO-009 (relacionado) | Impacto financeiro relevante. |
| 7 | Alta | Responsabilidade Ambiental | DO-032 | Exposição crescente ligada a decisões de gestão. |
| 7 | Alta | Danos Materiais | DO-025 | Danos patrimoniais a terceiros. |
| 7 | Alta | Danos Corporais | DO-024 | Danos físicos a terceiros. |
| 7 | Alta | Danos Morais | DO-026 | Litígios envolvendo reputação e personalidade. |
| 4 | Média | Proteção de Imagem | DO-020 | Apoio à gestão de crise reputacional. |
| 4 | Média | Bloqueio de Conta Corrente | DO-007 | Suporte financeiro durante constrição judicial. |
| 4 | Média | Defesa Emergencial | DO-010 | Atuação imediata em situação crítica. |
| 4 | Média | Prestação de Serviços Profissionais | DO-027 | Responsabilidade por serviços prestados. |
| 4 | Média | Novas Subsidiárias | DO-016 | Acompanha crescimento societário. |
| 2 | Baixa | Gerenciamento de Crise | DO-029 (principal), DO-028 (relacionado) | Mitigação reputacional complementar. |
| 2 | Baixa | Inabilitação | DO-014 | Proteção para situação específica. |
| 2 | Baixa | Avalista ou Fiador | DO-013 | Proteção ligada a garantias pessoais. |
| 2 | Baixa | Processos no Exterior | DO-043 | Relevante para operações internacionais. |
| 2 | Baixa | Salvamento e Contenção | DO-044 | Mitigação das consequências do sinistro. |

Total de pesos ativos por padrão: **207** (10 × 10 + 11 × 7 + 5 × 4 + 5 × 2).

Conceitos do dicionário sem peso (DO-001, DO-004, DO-011, DO-012, DO-019, DO-022, DO-023, DO-030, DO-031, DO-035) são extraídos, consultáveis e exibidos na comparação, mas ficam com `Ativo? = não` no score até a equipe de seguros atribuir peso. Os conceitos marcados “relacionado” são avaliados junto ao conceito principal, sem somar peso duas vezes.

### 6.2 Resultado-base (por conceito e apólice)

| Valor | Critério |
|---|---|
| 1,00 | Cobertura contratada ou comprovada, com redação suficiente e alcance plenamente aderente. |
| 0,75 | Cobertura identificada com pequena limitação, subcondição ou redação menos ampla. |
| 0,50 | Correspondência temática ou cobertura parcial, com diferença relevante de alcance. |
| 0,25 | Menção, previsão incerta ou cobertura muito restrita. |
| 0,00 | Não localizada, expressamente excluída ou sem correspondência. |

### 6.3 Fator de Ajuste

| Valor | Aplicação |
|---|---|
| 1,00 | Sem ajuste relevante. |
| 0,90 | Limitação pequena, sem impacto material esperado. |
| 0,75 | Sublimite, condicionante ou alcance parcialmente restritivo. |
| 0,50 | Restrição material, divergência documental ou cobertura parcial. |
| 0,25 | Evidência muito limitada, condição gravosa ou aplicabilidade incerta. |
| 0,00 | Exclusão, ausência ou impossibilidade de confirmar proteção. |

Toda pontuação diferente de 1,00 exige justificativa. Não reduzir duas vezes pelo mesmo motivo. Exclusão expressa zera o conceito.

### 6.4 Fórmulas

```text
Pontos Ponderados      = Peso Técnico × Resultado-base × Fator de Ajuste
Score Bruto            = Σ Pontos Ponderados (conceitos ativos)
Máximo Possível        = Σ Pesos Técnicos ativos
Score de Aderência     = Score Bruto / Máximo Possível
Score Documental       = Σ Pontos dos conceitos com evidência suficiente / Σ Pesos desses conceitos
Índice de Completude   = Σ Pesos dos conceitos com evidência suficiente / Σ Pesos ativos
Índice de Capacidade   = LMG da apólice / maior LMG entre as apólices (somente se comparáveis)
```

Percentuais são apresentados com uma casa decimal. O backend calcula com `Decimal` e arredonda apenas na apresentação.

Indicadores adicionais obrigatórios: diferença de score entre apólices; quantidade de conceitos favoráveis a cada apólice, equivalentes e inconclusivos; peso total inconclusivo; peso de coberturas críticas sem confirmação; os cinco conceitos que mais alteraram o resultado.

### 6.5 Limites, valores e prazos

- **LMG e sublimites:** comparar valor, moeda, limite agregado ou por evento, sublimite, erosão, franquia, participação obrigatória, condições de aplicação e relação com o LMG total.
- **Retroatividade, prazo complementar e suplementar:** comparar data/extensão, se é automático ou contratável, eventos de ativação, notificação, elegibilidade e a diferença entre complementar e suplementar.
- **Territorialidade:** comparar território, local do ato, local da reclamação, jurisdição, processos no exterior e limitações por sanções ou legislação local.
- Valores ou prazos não comparáveis não geram vantagem automática: registrar a divergência e aplicar `BROKER_GUIDANCE`.

## 7. Decisão

A decisão é apresentada em três níveis e sempre separada da análise documental:

1. **Resultado técnico geral:** maior Score de Aderência com pesos-base.
2. **Resultado por perfil de risco:** pesos ajustados, preservando os originais.
3. **Resultado condicionado:** se a diferença entre scores for pequena, se o Índice de Completude for baixo ou se o resultado depender de conceitos críticos inconclusivos, as duas apólices são apresentadas como alternativas condicionadas, sem “vencedora absoluta”.

### 7.1 Perfis de risco

| Perfil | Conceitos priorizados |
|---|---|
| Financeiro | LMG, Garantia A, Garantia B, Custos de Defesa |
| Internacional | Territorialidade, Processos no Exterior, Retroatividade, Prazo Complementar, Prazo Suplementar |
| Regulatório | Investigação, Multas e Penalidades, Responsabilidade Tributária, Responsabilidade Ambiental |
| Cauda | Retroatividade, Cláusula de Notificação, Prazo Complementar, Prazo Suplementar |
| Trabalhista e reputacional | Práticas Trabalhistas Indevidas, Danos Morais, Proteção de Imagem, Gerenciamento de Crise, Custos de Defesa |

Para cada perfil: apólice vencedora no perfil, score ajustado, conceitos decisivos, limitações, sensibilidade da decisão e orientação final.

### 7.2 Resumo executivo

Apólice com maior score documental; score de cada apólice; Índice de Completude; principais vantagens de cada apólice; coberturas críticas equivalentes; diferenças de maior impacto; pontos de atenção; recomendação por perfil; conclusão condicionada. Se score matemático e análise qualitativa apontarem apólices diferentes, explicar a divergência e quais critérios qualitativos mudaram a leitura.

## 8. Apresentação

A UI deve mostrar: documentos processados, qualidade da extração, seletor de Apólice 01 e 02, filtro por nível de importância, tabela comparativa com peso e score por conceito, destaques de diferenças críticas, Score de Aderência, Índice de Completude, indicador comparativo, resumo executivo, visualização da evidência literal com fonte, cláusula e página, e alertas de ausência, divergência ou contratação não comprovada.

| Cor | Significado |
|---|---|
| Vermelho | diferença crítica, exclusão ou ausência relevante |
| Laranja | diferença de alta importância |
| Amarelo | diferença de média importância |
| Verde | equivalência ou vantagem documental comprovada |
| Cinza | informação não localizada |

Não usar verde para contratação quando houver apenas menção nas Condições Gerais. Cor nunca é o único sinal: toda célula também tem rótulo textual.

## 9. Mapeamento dos prompts

| Prompt do documento 3 | Prompt versionado | Etapa |
|---|---|---|
| 1 — Mestre | `P-SYSTEM-001` | instruções comuns a todas as chamadas |
| 2 — Recebimento | `P-INTAKE-001` | classificação do documento |
| 3 — Extração PDF/imagem | `P-EXTRACT-001` | extração de evidências |
| 4 — Organização e normalização | `P-NORMALIZE-001` | vínculo evidência → conceito |
| 5 — Armazenamento | contrato de persistência (sem LLM) | `PERSISTENCE_AND_API.md` |
| 6 — Consulta | `P-QUERY-001` | resposta a consultas |
| 7, 9 e 10 — Comparação, pontuação, limites/prazos | `P-ASSESS-001` | avaliação por conceito |
| 8 e 11 — Pesos e score geral | cálculo determinístico (sem LLM) | `ScoringService` |
| 12 e 13 — Perfil e decisão executiva | `P-EXECUTIVE-001` | resumo sobre números já calculados |
| 14 e 15 — Apresentação e tabela | contrato de UI/API (sem LLM) | `SPEC-010` |
| 16 — Controle de qualidade | `QualityGate` determinístico + `P-QA-001` opcional | auditoria antes da exibição |
| 17 — Prompt curto | referência de operação | README e demonstração |
| 18 — Governança | regras da seção 3 | todo o sistema |

## 10. Inconsistências conhecidas nas bases

| Ponto | Tratamento adotado |
|---|---|
| Os documentos 2 e 3 contêm marcas “[file:39]” e “[file:41]” de uma ferramenta anterior. | Ignoradas; não são referências válidas. |
| Exemplo do material: score 77,6 % (Apólice 01) × 79,4 % (Apólice 02), mas recomendação técnica favorável à Apólice 01. | Caso de teste obrigatório de divergência entre score e análise qualitativa (seção 7.2). |
| Exemplo de LMG R$ 50 mi × R$ 10 mi, retroatividade e prazos. | Dados do exemplo analisado, não regras universais; usar apenas como fixture. |
| Dicionário tem 35 conceitos; a matriz de pesos usa 31, nove deles ausentes do dicionário. | IDs DO-036 a DO-044 criados; variantes pendentes de validação. |
| Documento 2 nomeia “perfil de exposição trabalhista”; documento 3, “trabalhista e reputacional” com mais conceitos. | Adotada a versão do documento 3 (mais recente e completa). |
| Multiplicador dos pesos ajustados por perfil não é definido. | Parâmetro versionado `profile_multiplier`, padrão proposto 1,5 para conceitos priorizados, `PENDING_BUSINESS_VALIDATION`. |
| Limiar de “diferença pequena” entre scores para decisão condicionada e de “completude baixa” não são definidos. | Parâmetros `close_score_threshold` (proposto 3,0 p.p.) e `min_completeness` (proposto 70,0 %), `PENDING_BUSINESS_VALIDATION`. |
