# ClauseAI: instruções para o Claude Code

Responda sempre em português do Brasil.

## Equipe de subagentes (obrigatória)

Os subagentes ficam em `.claude/agents/` e devem ser usados em toda tarefa de melhoria do sistema. Nunca decida trabalhar sem eles. Se a sessão for interrompida (limite de uso, container reciclado), retome a tarefa acionando os mesmos agentes.

| Agente | Função |
|---|---|
| `ux-ui-norman` | Experiência do usuário na linha de Don Norman. Entrega decisões, não código. |
| `interface-designer` | Fontes, cores, tokens e remake visual inspirado no EasyPay. Mantém as cores de notificação. |
| `frontend-specialist` | React/TypeScript seguindo UX, Interface, Clean Code, SOLID, eventos e SDD. |
| `backend-specialist` | FastAPI, extração PDF/DOCX, comparação, com SOLID, Clean Code, eventos e SDD. |
| `software-engineer-docs` | Atualiza `docs/` a cada decisão da equipe. Documentação clara e objetiva. |
| `qa` | Fecha arestas, escreve testes, valida o fluxo completo com os demais. |
| `devops` | CI/CD, commits, PR, merge e deploy, somente quando solicitado. |

## Fluxo

`ux-ui-norman` decide → `interface-designer` e `frontend-specialist` implementam → `backend-specialist` entrega a API → `software-engineer-docs` documenta → `qa` valida → `devops` publica quando pedido.

A documentação em `docs/` é a fonte de verdade (SDD). Comandos de qualidade estão em `CONTRIBUTING.md`.

## Critérios de conclusão da meta atual

1. Comparação correta de apólices em PDF e DOCX, inclusive misturando formatos, e envio de apólices sem falhas.
2. As apólices de exemplo em `Policy/` parecidas com apólices reais.
3. Aparência do sistema no nível da referência EasyPay, com as fontes (IBM Plex Sans, Roboto) e cores da marca (`#000000`, `#F9EFE5`, `#FFD700`, base `#7F8790`, `#8F92A1`, `#F8F8F8`) e as cores de notificação preservadas.
