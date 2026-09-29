Tarefa: avaliar cada conceito nas duas apólices usando exatamente os mesmos critérios (documento 3, prompts 7, 9 e 10).

Para cada conceito recebido, compare definição, beneficiário, gatilho, despesas, danos, limites, sublimites, franquias, prazos, territorialidade, exclusões e condições, usando SOMENTE as evidências fornecidas.

Atribua para a Apólice 01 (a) e a Apólice 02 (b):
- base_result (Resultado-base), somente um destes valores:
  1.0 cobertura contratada ou comprovada, com alcance plenamente aderente;
  0.75 cobertura identificada com limitação pequena;
  0.5 correspondência temática ou cobertura parcial;
  0.25 menção, previsão incerta ou cobertura muito restrita;
  0.0 não localizada, expressamente excluída ou sem correspondência.
- adjustment_factor (Fator de Ajuste), somente um destes valores:
  1.0 sem ajuste; 0.9 limitação pequena; 0.75 sublimite, condicionante ou alcance parcialmente restritivo;
  0.5 restrição material, divergência documental ou cobertura parcial; 0.25 evidência muito limitada ou aplicabilidade incerta;
  0.0 exclusão ou ausência de proteção aplicável.
- justification: obrigatória quando base_result ou adjustment_factor for diferente de 1.0.
- confidence: HIGH, MEDIUM ou LOW.

Regras:
- Não reduza duas vezes pelo mesmo motivo.
- Exclusão expressa: base_result 0.0 e adjustment_factor 0.0.
- NOT_PROVEN (só menção) nunca passa de 0.25 no base_result.
- Limites ou prazos em bases diferentes não geram vantagem automática: descreva a diferença.
- Nunca use apenas o nome da cobertura para declarar equivalência.
- main_difference: uma frase objetiva com a principal diferença entre as apólices, ou "Sem diferença material identificada."
- Não calcule pontos nem scores.

Formato de resposta:
{"assessments": [{"concept_id": "DO-NNN", "a": {"base_result": 1.0, "adjustment_factor": 1.0, "justification": null, "confidence": "HIGH"}, "b": {...}, "main_difference": "..."}]}

Conceitos:
{concepts}
