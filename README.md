# CargoTrack VC - Rastreamento de Carga com Comprovante Verificavel

CargoTrack VC e um MVP didatico de logistica para demonstrar como uma operacao de transporte pode ser registrada, acompanhada e finalizada com um comprovante digital verificavel.

O projeto simula um fluxo comum no transporte de cargas: um embarcador cria uma ordem, a transportadora aceita a operacao, o motorista recebe um documento digital e o recebedor assina a entrega. Ao final, o sistema emite um comprovante em formato de Credencial Verificavel, que pode ser auditado e validado posteriormente.

Este repositorio foi pensado para portfolio: ele nao e apenas um CRUD. A proposta e mostrar arquitetura em camadas, regras de negocio, eventos de auditoria, assinatura digital, persistencia, API REST, Docker, testes e uma demo visual simples para apresentar o fluxo ponta a ponta.

## Contexto

Em operacoes logisticas reais, a entrega de uma carga depende de varios registros: pedido, aceite da transportadora, documento do motorista, eventos de trajeto, assinatura do recebedor e comprovante de entrega. Quando esses registros ficam espalhados em sistemas diferentes ou dependem de documentos manuais, surgem problemas comuns:

- dificuldade para provar que a entrega aconteceu;
- divergencia entre embarcador, transportadora e recebedor;
- baixa rastreabilidade de eventos importantes;
- pouca confianca em comprovantes enviados por imagem ou PDF simples;
- dificuldade de auditoria em caso de disputa.

O CargoTrack VC resolve esse problema em escala de MVP: cada etapa importante vira um evento rastreavel, e a entrega final gera uma credencial assinada digitalmente.

## O que o sistema faz

O sistema cobre cinco momentos principais:

1. **Criacao da ordem**
   O embarcador registra carga, origem, destino, transportadora, motorista, veiculo e recebedor.

2. **Aceite pela transportadora**
   A transportadora aceita a ordem. Nesse momento, o sistema emite a `VC-OrdemTransporte`, que funciona como documento digital da operacao.

3. **Documento digital do motorista**
   O motorista consulta suas ordens pelo CPF e baixa as credenciais associadas a viagem.

4. **Assinatura da entrega**
   No destino, o recebedor informa seus dados e confirma o recebimento da carga.

5. **Comprovante verificavel**
   O sistema emite a `VC-ComprovanteEntrega`, uma evidencia digital assinada que representa o proof of delivery.

## Atores do fluxo

| Ator | Papel no sistema |
| --- | --- |
| Embarcador | Cria a ordem de transporte. |
| Transportadora | Aceita a ordem e assume a operacao. |
| Motorista | Recebe o documento digital da carga. |
| Recebedor | Confirma e assina a entrega. |
| Validador | Consulta chaves publicas e verifica credenciais. |

## Tecnologias utilizadas

| Tecnologia | Uso no projeto |
| --- | --- |
| Python 3.11+ | Linguagem principal do backend. |
| FastAPI | Exposicao da API REST e documentacao OpenAPI/Swagger. |
| Pydantic | Validacao de entrada, contratos e modelos de dominio. |
| SQLAlchemy | Persistencia das ordens, credenciais e auditoria. |
| PostgreSQL | Banco relacional usado no ambiente Docker. |
| SQLite | Banco simples para testes locais. |
| Celery | Estrutura para processamento assincrono. |
| Redis | Broker usado pelo Celery no ambiente Docker. |
| cryptography | Assinatura digital das credenciais no MVP. |
| W3C Verifiable Credentials | Modelo conceitual das credenciais emitidas. |
| Prometheus | Exposicao de metricas basicas em `/metrics`. |
| Docker Compose | Ambiente local com API, worker, banco, Redis e Prometheus. |
| Pytest | Testes unitarios e de integracao. |

## Arquitetura

O projeto segue uma arquitetura em camadas para manter o dominio separado dos detalhes tecnicos.

```text
API FastAPI
  Recebe requisicoes HTTP e valida contratos de entrada/saida.

Services
  Coordenam os casos de uso: criar ordem, aceitar, baixar documento e assinar entrega.

Repositories
  Encapsulam acesso ao banco de dados.

Models
  Definem entidades de dominio e estruturas de dados.

Infrastructure
  Banco, configuracao, cripto, fila, notificacoes e observabilidade.
```

### Principais modulos

```text
src/dte_mvp/
  api/routes/ordens.py          Endpoints do fluxo logistico
  services/ordem_service.py     Regras do ciclo de vida da ordem
  services/vc_service.py        Emissao de credenciais verificaveis
  services/audit_service.py     Registro de auditoria
  repositories/ordem_repository.py
  repositories/vc_repository.py
  repositories/audit_repository.py
  models/ordem.py
  models/vc.py
  infra/database/
  infra/crypto/
  infra/queue/
```

## Fluxo funcional

```text
Embarcador
  -> cria ordem de transporte

Transportadora
  -> aceita ordem
  -> sistema emite VC-OrdemTransporte

Motorista
  -> consulta ordens pelo CPF
  -> baixa documento digital

Recebedor
  -> assina entrega
  -> sistema emite VC-ComprovanteEntrega

Validador
  -> usa chaves publicas para verificar credenciais
```

## Regras de negocio do MVP

| Regra | Descricao |
| --- | --- |
| Idempotencia | A mesma `chave_ordem` nao cria ordens duplicadas. |
| Aceite | Apenas ordens com status `criada` podem ser aceitas. |
| Acesso do motorista | O documento so e entregue ao CPF vinculado a ordem. |
| Entrega | Apenas ordens `aceita` ou `em_transito` podem ser finalizadas. |
| Auditoria | Criacao, aceite, download e entrega sao registrados. |
| Comprovante verificavel | A entrega gera uma `VC-ComprovanteEntrega` assinada. |

## Endpoints principais

| Metodo | Endpoint | Descricao |
| --- | --- | --- |
| `POST` | `/api/v1/ordens` | Cria ordem de transporte. |
| `POST` | `/api/v1/ordens/{ordem_id}/aceite` | Aceita a ordem e emite documento digital. |
| `GET` | `/api/v1/ordens?cpf={cpf}` | Lista ordens ativas do motorista. |
| `GET` | `/api/v1/ordens/{ordem_id}/documento?cpf={cpf}` | Baixa credenciais da ordem. |
| `POST` | `/api/v1/ordens/{ordem_id}/entrega` | Assina entrega e emite comprovante. |
| `GET` | `/api/v1/public-keys` | Retorna chaves publicas do emissor. |
| `GET` | `/api/v1/health` | Verifica saude da API. |

## Exemplo de uso da API

### 1. Criar ordem

```bash
curl -X POST "http://localhost:8000/api/v1/ordens" \
  -H "Content-Type: application/json" \
  -d '{
    "numero_ordem": "OT-2026-0001",
    "chave_ordem": "SHIP-2026-0001",
    "embarcador": "Agro Origem Ltda",
    "cnpj_embarcador": "12345678000195",
    "transportadora": "TransLog Brasil",
    "cnpj_transportadora": "22345678000190",
    "motorista_nome": "Ana Motorista",
    "cpf_motorista": "12345678901",
    "placa": "ABC1D23",
    "recebedor": "Centro de Distribuicao Santos",
    "cnpj_recebedor": "32345678000191",
    "origem": "Rondonopolis/MT",
    "destino": "Santos/SP",
    "descricao_carga": "Carga paletizada de alimentos",
    "quantidade": 18000,
    "unidade": "kg",
    "valor_frete": 9500,
    "data_coleta_prevista": "2026-07-02T10:00:00Z"
  }'
```

### 2. Aceitar ordem

```bash
curl -X POST "http://localhost:8000/api/v1/ordens/{ordem_id}/aceite"
```

### 3. Baixar documento do motorista

```bash
curl "http://localhost:8000/api/v1/ordens/{ordem_id}/documento?cpf=12345678901"
```

### 4. Assinar entrega

```bash
curl -X POST "http://localhost:8000/api/v1/ordens/{ordem_id}/entrega" \
  -H "Content-Type: application/json" \
  -d '{
    "recebedor_nome": "Bruno Recebedor",
    "documento_recebedor": "1234567",
    "latitude": -23.9608,
    "longitude": -46.3336,
    "observacao": "Carga recebida sem avarias."
  }'
```

## Como rodar localmente

### Opcao 1: Python local

Requisitos:

- Python 3.11 ou superior
- pip

Instale as dependencias:

```bash
pip install -e ".[dev]"
```

Execute a API:

```bash
uvicorn dte_mvp.main:create_app --factory --reload --port 8000
```

Acesse:

- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- Metricas: `http://localhost:8000/metrics`

### Opcao 2: Docker Compose

Requisitos:

- Docker
- Docker Compose

Suba o ambiente:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Servicos iniciados:

| Servico | Porta | Descricao |
| --- | --- | --- |
| API | `8000` | Backend FastAPI. |
| PostgreSQL | `5433` | Banco da aplicacao. |
| Redis | `6379` | Broker do Celery. |
| Prometheus | `9090` | Coleta de metricas. |

## Demo visual

O diretorio `demo/` contem uma simulacao visual do fluxo.

Abra no navegador:

```text
demo/simulador-cargotrack.html
```

Na tela, informe a URL da API:

```text
http://localhost:8000/api/v1
```

A demo percorre as etapas de criacao da ordem, aceite, documento do motorista, assinatura do recebedor e emissao do comprovante verificavel.

## Testes

Execute os testes unitarios:

```bash
pytest tests/unit -v
```

Execute os testes de integracao:

```bash
pytest tests/integration -v
```

Execute com cobertura:

```bash
pytest tests/ -v --cov=dte_mvp --cov-report=term-missing
```

## Estrutura do repositorio

```text
config/                  Configuracoes YAML
demo/                    Demo visual em HTML, CSS e JavaScript
docker/                  Dockerfile, Compose e Prometheus
docs/                    Documentacao complementar
secrets/                 Orientacao para chaves locais
src/dte_mvp/             Codigo fonte da API
tests/                   Testes unitarios e de integracao
```

## Seguranca e limitacoes do MVP

O projeto demonstra conceitos de seguranca, mas nao deve ser usado em producao sem endurecimento adicional.

Implementado no MVP:

- assinatura das credenciais;
- chaves publicas expostas para validacao;
- minimizacao de dados para busca por motorista;
- trilha de auditoria;
- idempotencia na criacao da ordem;
- separacao entre dominio, API e infraestrutura.

Fora do escopo do MVP:

- autenticacao real por ator;
- autorizacao granular;
- revogacao de credenciais;
- verificacao criptografica completa no frontend;
- gestao real de certificados;
- integracao com sistemas logisticos externos.


