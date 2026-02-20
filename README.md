# Cupido - Mensagens Anonimas via WhatsApp

Servico de mensagens anonimas via WhatsApp. Compre um plano na Lowify, preencha o formulario, e o Cupido entrega a mensagem para a pessoa especial.

## Como Funciona

1. Pessoa compra um plano na Lowify
2. Recebe link no WhatsApp para preencher formulario
3. Preenche mensagem + telefone do destinatario
4. Cupido envia mensagem anonima para o destinatario

## Planos

| Plano | Descricao |
|-------|-----------|
| Basico | 1 mensagem de texto anonima |
| Com Audio | Texto + audio gerado por IA (Eleven Labs) |
| Multi Mensagem | Ate 5 mensagens sequenciais |
| Premium Historia | Slideshow com fotos + legendas |

## Stack

- **Backend:** FastAPI + Python 3.11
- **Database:** Supabase (PostgreSQL)
- **WhatsApp:** UAZAPI
- **Audio:** Eleven Labs TTS
- **Cache:** Redis (opcional)
- **Deploy:** Railway + Docker

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env com suas credenciais
uvicorn src.api:app --reload
```

## Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/webhook/lowify` | Webhook de pagamento Lowify |
| POST | `/webhook/lowify-debug` | Debug de payloads |
| GET | `/form/{token}` | Formulario do comprador |
| POST | `/form/{token}/submit` | Submissao do formulario |
| POST | `/form/{token}/upload` | Upload premium (imagens) |
| GET | `/p/{presentation_id}` | Visualizador slideshow |
| GET | `/health` | Health check |

## Database

Execute `setup_cupido.sql` no Supabase SQL Editor para criar as tabelas.
Crie o bucket `cupido-assets` (publico) no Supabase Storage.
