# CargoTrack VC API

Base local: `http://localhost:8000/api/v1`

## Criar ordem

`POST /ordens`

Usado pelo embarcador para criar a ordem de transporte.

## Aceitar ordem

`POST /ordens/{ordem_id}/aceite`

Usado pela transportadora. Emite a `VC-OrdemTransporte`.

## Listar ordens do motorista

`GET /ordens?cpf=12345678901`

Retorna ordens aceitas ou em transito vinculadas ao CPF.

## Baixar documento digital

`GET /ordens/{ordem_id}/documento?cpf=12345678901`

Retorna as credenciais verificaveis da ordem.

## Assinar entrega

`POST /ordens/{ordem_id}/entrega`

Registra a assinatura do recebedor e emite `VC-ComprovanteEntrega`.

## Chaves publicas

`GET /public-keys`

Usado por wallets e validadores para manter cache local de chaves do emissor.

