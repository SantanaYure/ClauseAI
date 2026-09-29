# ClauseAI — documentação técnica do MVP

## Objetivo

Esta pasta é a fonte de verdade para o MVP acadêmico de análise e comparação inteligente de apólices D&O, desenvolvido como Projeto Final do I2A2 (“Plataforma Inteligente para Análise e Comparação de Apólices D&O”). Ela descreve contratos, limites, estados, dependências, decisões, testes e questões que ainda dependem de validação da equipe de seguros.

O domínio é definido por três bases de negócio — dicionário D&O, matriz de pesos e prompts do agente comparador — consolidadas em [`domain/DO_KNOWLEDGE_BASE.md`](domain/DO_KNOWLEDGE_BASE.md).

O sistema é um monólito modular com React/TypeScript/SCSS no frontend, Python/FastAPI no backend, Firestore/Storage na persistência e uma camada própria de orquestração de IA. Não há código de produção nesta etapa.

## Como usar esta documentação

1. Ler [`domain/DO_KNOWLEDGE_BASE.md`](domain/DO_KNOWLEDGE_BASE.md) e [`architecture/ARCHITECTURE_OVERVIEW.md`](architecture/ARCHITECTURE_OVERVIEW.md).
2. Usar [`architecture/MODULE_STRUCTURE.md`](architecture/MODULE_STRUCTURE.md) e [`architecture/DOMAIN_MODEL.md`](architecture/DOMAIN_MODEL.md) para orientar a estrutura do código.
3. Implementar na ordem do [`ROADMAP.md`](ROADMAP.md).
4. Para cada incremento, seguir a spec correspondente em [`specs/SDD_SPECIFICATIONS.md`](specs/SDD_SPECIFICATIONS.md).
5. Registrar qualquer mudança estrutural em [`adrs/ADRS.md`](adrs/ADRS.md).
6. Seguir o fluxo Git/CI em [`development/git-workflow.md`](development/git-workflow.md).

## Regras de precedência

1. Enunciado do Projeto Final (requisitos mínimos, entregáveis e critérios de avaliação).
2. Bases de negócio em [`domain/sources/`](domain/sources/), consolidadas em [`domain/DO_KNOWLEDGE_BASE.md`](domain/DO_KNOWLEDGE_BASE.md).
3. Specs, arquitetura e ADRs desta pasta.
4. Preferências de implementação.

- Regra de negócio não confirmada deve ser marcada como `PENDING_BUSINESS_VALIDATION` e não pode ser inventada pelo software ou pela IA.
- Contratos públicos só mudam com atualização da spec, dos testes e, quando aplicável, de um ADR.
- Evidências extraídas são a fonte factual; pesos e pontuação são parâmetros de decisão e não comprovam contratação.
- A recomendação é ponderada, explicável e condicionada; nunca é aconselhamento jurídico. Em qualquer ambiguidade relevante, o sistema exibe “Consulte seu corretor de seguros.”

## Escopo do MVP

### Incluído

- Upload de PDF ou imagem com validação básica e registro do tipo de documento (apólice, condições gerais, especificação, endosso etc.).
- Armazenamento do original e dos metadados.
- Processamento assíncrono interno.
- Extração com leitura nativa de PDF e, quando necessário, OCR/leitura multimodal com Gemini 3.5 Flash Lite, preservando evidências literais.
- Normalização das evidências contra o catálogo de conceitos D&O (DO-001 a DO-044).
- Persistência de documento, evidências, apólice, coberturas, exclusões, limites, franquias, cláusulas, ocorrências de conceito, pesos e resultados.
- Consulta por apólice, documento, conceito, variante, seguradora, cláusula, página, importância, peso e status.
- Comparação determinística de duas apólices e avaliação por conceito (Resultado-base e Fator de Ajuste) com Gemini 3.5 Flash Lite.
- Pontuação ponderada determinística: Pontos Ponderados, Score de Aderência, Score Documental e Índice de Completude.
- Decisão por perfil de risco (financeiro, internacional, regulatório, cauda, trabalhista e reputacional) e resumo executivo condicionado.
- Interface web com tabela comparativa, pesos, scores, evidências, alertas e resumo executivo.
- Event Bus em memória, correlação, idempotência e logs estruturados.

### Fora do MVP

- Microserviços, Kubernetes, Kafka, RabbitMQ e Event Sourcing completo.
- Aconselhamento jurídico, recomendação de compra incondicional ou “vencedora absoluta” desacompanhada de completude, perfil e evidências.
- Integração com sistemas reais de seguradoras, alta disponibilidade e cobertura de todos os tipos de apólice (fora do esperado pelo desafio).
- Autenticação, autorização multiusuário e workflow de aprovação, salvo se o ambiente acadêmico exigir posteriormente.

## Estado de maturidade

`DRAFT_FOR_IMPLEMENTATION`: os contratos técnicos estão definidos para iniciar o desenvolvimento. Conceitos, pesos, escalas e fórmulas já estão definidos pelas bases de negócio; apenas os pontos listados na seção 10 da base de conhecimento continuam `PENDING_BUSINESS_VALIDATION`.

## Entregáveis do Projeto Final

Prazo: 06/10/2026, 23h59. O repositório deve ser público e conter:

- código-fonte e instruções de instalação/execução;
- README com descrição, instalação, execução, tecnologias, integrantes e licença MIT;
- pasta [`Projeto_Final_Artefatos/`](../Projeto_Final_Artefatos/) com o relatório técnico (PDF), o pitch deck `InsurMinds_Projeto_Final.pptx`, o vídeo `InsurMinds_Projeto_Final.mp4` (até 5 minutos) e demais artefatos.

O relatório técnico deve cobrir arquitetura, tecnologias, agentes, fluxo completo, justificativas arquiteturais, limitações conhecidas e evolução futura; esta pasta é sua fonte principal.

## Árvore sugerida de `/docs`

```text
docs/
├── README.md
├── domain/
│   ├── DO_KNOWLEDGE_BASE.md
│   └── sources/
├── architecture/
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── MODULE_STRUCTURE.md
│   ├── DOMAIN_MODEL.md
│   └── PERSISTENCE_AND_API.md
├── AI_SYSTEM_SPEC.md
├── specs/
│   └── SDD_SPECIFICATIONS.md
├── adrs/
│   └── ADRS.md
└── ROADMAP.md
```

## Convenções

- IDs: `document_id`, `policy_id`, `comparison_id`, `processing_id`, `event_id`, `correlation_id`.
- Datas: ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`).
- Valores monetários: objeto com `amount`, `currency` e, se necessário, `basis`; nunca usar float para persistência.
- Campos extraídos: sempre que possível, `value`, `source_text`, `page`, `clause_ref`, `section_ref` e `confidence`.
- Conceitos: IDs `DO-NNN` do catálogo; pesos e fatores como decimais, nunca float.
- Orientação padrão ao usuário: constante `BROKER_GUIDANCE` = “Consulte seu corretor de seguros.”
- Erros: resposta REST com `code`, `message`, `correlation_id` e `details` opcional.
- Versionamento: `schema_version`, `event_version`, `prompt_version` e `knowledge_base_version` explícitos.
