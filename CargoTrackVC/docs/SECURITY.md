# Seguranca

Este MVP foi desenhado para demonstrar boas praticas de seguranca em um fluxo logistico.

- Chaves privadas ficam fora do codigo e sao carregadas por configuracao.
- Credenciais verificaveis sao assinadas pelo emissor.
- A wallet/validador pode manter cache de chaves publicas.
- Dados sensiveis sao minimizados quando usados para busca.
- Eventos importantes entram em trilha de auditoria.

Para uso real, faltariam endurecimento de autenticacao, controle de acesso por ator, rotacao de chaves, revogacao de credenciais e verificacao criptografica completa no front.

