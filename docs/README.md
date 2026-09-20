# ClauseAI — documentação técnica do MVP

## Objetivo

Esta pasta é a fonte de verdade para o MVP acadêmico de análise e comparação inteligente de apólices D&O. Ela descreve contratos, limites, estados, dependências, decisões, testes e questões que ainda dependem de validação da equipe de seguros.

O sistema é um monólito modular com React/TypeScript/SCSS no frontend, Python/FastAPI no backend, Firestore/Storage na persistência e uma camada própria de orquestração de IA. Não há código de produção nesta etapa.

## Como usar esta documentação

1. Ler [`architecture/ARCHITECTURE_OVERVIEW.md`](architecture/ARCHITECTURE_OVERVIEW.md).
2. Usar [`architecture/MODULE_STRUCTURE.md`](architecture/MODULE_STRUCTURE.md) e [`architecture/DOMAIN_MODEL.md`](architecture/DOMAIN_MODEL.md) para orientar a estrutura do código.
3. Implementar na ordem do [`ROADMAP.md`](ROADMAP.md).
4. Para cada incremento, seguir a spec correspondente em [`specs/SDD_SPECIFICATIONS.md`](specs/SDD_SPECIFICATIONS.md).
5. Registrar qualquer mudança estrutural em [`adrs/ADRS.md`](adrs/ADRS.md).
6. Seguir o fluxo Git/CI em [`development/git-workflow.md`](development/git-workflow.md).

## Regras de precedência

- Requisito explícito desta documentação prevalece sobre uma preferência de implementação.
- Regra de negócio não confirmada deve ser marcada como `PENDING_BUSINESS_VALIDATION` e não pode ser inventada pelo software ou pela IA.
- Contratos públicos só mudam com atualização da spec, dos testes e, quando aplicável, de um ADR.
- O resultado determinístico é a fonte factual da comparação; a IA acrescenta interpretação rastreável, nunca decisão jurídica.

## Escopo do MVP

### Incluído

- Upload de PDF ou imagem com validação básica.
- Armazenamento do original e dos metadados.
- Processamento assíncrono interno.
- Extração estruturada com Gemini 3.5 Flash Lite.
- Persistência de apólice, seções, coberturas, exclusões, limites, franquias e cláusulas.
- Consulta de documentos e apólices.
- Comparação determinística de duas apólices.
- Comparação semântica e explicação com GPT-OSS-120B via Groq.
- Interface web para upload, acompanhamento, seleção e leitura da comparação.
- Event Bus em memória, correlação, idempotência e logs estruturados.

### Fora do MVP

- Microserviços, Kubernetes, Kafka, RabbitMQ e Event Sourcing completo.
- Aconselhamento jurídico, recomendação de compra ou classificação universal de “melhor apólice”.
- OCR proprietário separado, caso o provedor multimodal consiga processar o arquivo diretamente; um adaptador local poderá ser incluído se os testes exigirem.
- Autenticação, autorização multiusuário e workflow de aprovação, salvo se o ambiente acadêmico exigir posteriormente.

## Estado de maturidade

`DRAFT_FOR_IMPLEMENTATION`: os contratos técnicos estão definidos para iniciar o desenvolvimento. Campos e semântica específicos de D&O marcados `PENDING_BUSINESS_VALIDATION` precisam ser confirmados pela equipe de seguros antes de virarem regras de cálculo.

## Árvore sugerida de `/docs`

```text
docs/
├── README.md
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
- Campos extraídos: sempre que possível, `value`, `source_text`, `page` e `confidence`.
- Erros: resposta REST com `code`, `message`, `correlation_id` e `details` opcional.
- Versionamento: `schema_version`, `event_version` e `prompt_version` explícitos.
