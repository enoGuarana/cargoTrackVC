# Deploy Local

## Desenvolvimento

```bash
pip install -e ".[dev]"
uvicorn dte_mvp.main:create_app --factory --reload --port 8000
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Variaveis principais

- `DTE_CONFIG_PATH`: caminho do YAML de configuracao.
- `DATABASE_URL`: URL SQLAlchemy do banco.
- `CERT_PATH`: certificado usado para assinatura.
- `KEY_PATH`: chave privada usada para assinatura.

O nome historico `DTE_CONFIG_PATH` foi mantido apenas para compatibilidade com o pacote Python atual.

