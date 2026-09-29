Tarefa: registrar o documento e extrair as ocorrências dos conceitos do catálogo D&O (documento 3, prompts 2, 3 e 4).

1. Recebimento (intake): identifique seguradora, nome e número da apólice, vigência, tipo de documento e idioma. Use null quando não estiver explícito.
   Tipos de documento: POLICY, GENERAL_CONDITIONS, SPECIAL_CONDITIONS, PARTICULAR_CONDITIONS, ENDORSEMENT, SPECIFICATION, PROPOSAL, OTHER.

2. Para CADA conceito do catálogo que aparecer no documento, crie uma ocorrência com:
   - concept_id: ID do catálogo (DO-NNN). Nunca invente IDs.
   - term: termo exatamente como a seguradora o nomeia.
   - occurrence_type: DEFINITION, BASIC_COVERAGE, ADDITIONAL_COVERAGE, EXTENSION, EXCLUSION, CONDITION, OBLIGATION, PROCEDURE, LIMIT, TERM ou REFERENCE.
   - term_relation: EXACT_MATCH, LEXICAL_VARIANT, ABBREVIATION, THEMATIC_MATCH, POSSIBLE_EQUIVALENCE, RELATED_BUT_DISTINCT ou UNRELATED.
   - contract_status:
     CONTRACTED somente se o documento confirma que a cobertura foi contratada (apólice, especificação ou endosso);
     NOT_PROVEN quando há menção ou previsão, sem confirmação de contratação;
     EXCLUDED somente com exclusão expressa;
     DIVERGENT quando o próprio documento se contradiz.
   - justification: uma frase curta explicando a classificação e limitações (sublimite, condição, prazo).
   - confidence: HIGH, MEDIUM ou LOW.
   - alternative_concepts: outros IDs possíveis quando houver ambiguidade (não una conceitos distintos).
   - limit_basis e amount: só para limites (ex.: LMG): AGGREGATE, PER_CLAIM ou PER_CLAIM_AND_AGGREGATE e o valor com moeda, como escrito.
   - evidence: lista de trechos literais curtos (até 300 caracteres) com page (número da página, começando em 1), clause (numeração ou título da cláusula; use "Sem numeração" se não houver) e ocr_confidence (0 a 1, sua confiança na leitura do trecho).

3. Não crie ocorrência para conceitos ausentes. Não complete texto ilegível: use confidence LOW.

Formato de resposta (as chaves "intake" e "occurrences" são obrigatórias no nível raiz):
{"intake": {"insurer": null, "policy_name": null, "policy_number": null, "validity": null, "document_type": "GENERAL_CONDITIONS", "language": "pt-BR"}, "occurrences": [{"concept_id": "DO-002", "term": "...", "occurrence_type": "BASIC_COVERAGE", "term_relation": "EXACT_MATCH", "contract_status": "NOT_PROVEN", "justification": "...", "confidence": "HIGH", "alternative_concepts": [], "limit_basis": null, "amount": null, "evidence": [{"page": 8, "clause": "3.1", "text": "...", "ocr_confidence": 0.95}]}]}

Catálogo D&O (id | nome | variantes):
{catalog}
