# Arquitetura CargoTrack VC

O projeto segue uma arquitetura em camadas simples para fins didaticos.

```text
Embarcador -> API -> Ordem criada
Transportadora -> API -> Ordem aceita + VC-OrdemTransporte
Motorista -> Wallet -> Documento digital da carga
Recebedor -> API -> Assinatura de entrega + VC-ComprovanteEntrega
Validador -> Cache de chaves -> Verificacao do comprovante
```

## Camadas

- `api/routes`: contratos HTTP.
- `services`: casos de uso e regras de negocio.
- `repositories`: persistencia SQLAlchemy.
- `models`: modelos Pydantic de dominio.
- `infra`: banco, cripto, fila, notificacoes e configuracao.

## Decisoes do MVP

- O backend continua transacional e simples.
- A ordem usa `chave_ordem` como idempotencia.
- Dados sensiveis sao minimizados com hash para consultas por motorista.
- Credenciais verificaveis sao assinadas com ECDSA P-256 no prototipo.
- A auditoria registra eventos principais com cadeia de hashes.

## Credenciais emitidas

- `VC-OrdemTransporte`: documento digital do motorista apos aceite.
- `VC-EventoLogistico`: evidencia simples para eventos da ordem.
- `VC-ComprovanteEntrega`: proof of delivery emitido apos assinatura do recebedor.

