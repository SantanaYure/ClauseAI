# Estrutura do repositório

## Direção de dependências

```text
presentation ─┐
infrastructure ─┼──> application ───> domain
shared ────────┘
```

O desenho é uma regra de organização, não uma autorização para o domínio importar frameworks. `app/main.py` é o composition root: cria settings, Event Bus e aplicação FastAPI. No futuro, repositories, Storage e providers serão conectados nesse ponto.

## Backend

- `domain/`: entidades, value objects, serviços puros e interfaces/ports.
- `application/`: commands, queries, DTOs e casos de uso.
- `infrastructure/`: implementações Firebase, Storage, IA e eventos.
- `presentation/api/`: FastAPI, rotas, schemas e handlers HTTP.
- `shared/`: configuração, logs, exceções e tipos transversais pequenos.
- `tests/`: unitários, integração e fixtures não confidenciais.

## Frontend

- `app/`: composição da aplicação e telas base.
- `components/`, `pages/`, `hooks/`: UI e comportamento reutilizável conforme o produto crescer.
- `services/api/`: único ponto de chamadas HTTP.
- `types/`: contratos de dados do frontend.
- `config/`: leitura segura de variáveis `VITE_*`.
- `styles/`: SCSS global e estilos de componentes.

## Pastas vazias reservadas

Pastas sem implementação de domínio existem apenas quando representam uma fronteira aprovada da arquitetura. Cada nova pasta deve receber código ou uma justificativa na documentação; não criar camadas genéricas para antecipar necessidades hipotéticas.

## O que não pertence à fundação

Não adicionar nesta etapa upload, persistência real, SDK Firebase, SDK Gemini/Groq, regras de D&O, comparação, autenticação ou broker externo. Esses itens têm specs e decisões próprias na documentação principal.
