# Guia de Contribuição

## Padrões de Código

### Python

- **PEP 8** com line-length 100
- **Type hints** obrigatórios (mypy strict mode)
- **Docstrings** no formato Google Style
- **Async/await** para todas operações I/O

### Commits

Formato: `<tipo>(<escopo>): <descrição>`

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `security`

Exemplo: `feat(crypto): add HSM support via PKCS#11`

### Pull Requests

1. Todos os testes devem passar
2. Cobertura mínima: 80%
3. `ruff check` e `mypy` sem erros
4. Review obrigatório de 1 aprovador

## Estrutura de Branches

- `main` — produção
- `develop` — integração
- `feature/*` — novas funcionalidades
- `fix/*` — correções
- `hotfix/*` — correções urgentes em produção
