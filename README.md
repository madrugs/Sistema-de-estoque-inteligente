# Controle de Estoque para Mercadinho

Sistema web para controle de estoque e inventário da rotina de um mercadinho
de bairro. Substitui as anotações em cadernos por um fluxo automatizado, com
histórico imutável de movimentações.

> Projeto integrador do curso (UNIVESP). O histórico de versões está em
> [CHANGELOG.md](CHANGELOG.md).

## Premissa de negócio

Nenhum saldo é editado diretamente. Toda alteração de estoque nasce de uma
**movimentação** (`ENTRADA` ou `SAIDA`) registrada no log de auditoria.

## Tecnologias

- Python 3.12 e Django 5.2 (MVT) com Django REST Framework
- SQLite em desenvolvimento e PostgreSQL em produção (via `DATABASE_URL`)
- Django Templates, HTML5 semântico, CSS e JavaScript puro
- Chart.js para gráficos do painel
- gunicorn e whitenoise para deploy (Render ou Railway)

## Como rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # ajuste os valores se necessário
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Testes

```bash
python manage.py test
```

## Deploy no Render

O arquivo `render.yaml` cria o serviço web e um banco PostgreSQL gerenciado.

1. No Render, escolha **New > Blueprint** e aponte para o repositório.
2. O Render gera `DJANGO_SECRET_KEY` automaticamente e define `DJANGO_DEBUG=0`.
3. O build roda `collectstatic`, e o start roda `migrate` antes do `gunicorn`.
4. O domínio `*.onrender.com` é lido de `RENDER_EXTERNAL_HOSTNAME`, então não precisa configurar `ALLOWED_HOSTS` manualmente.

Para criar o superusuário em produção, use o shell do serviço no Render:

```bash
python manage.py createsuperuser
```

No plano gratuito, o banco PostgreSQL expira após 30 dias. Antes disso, migre para um plano pago ou exporte os dados.

## Fluxo de branches

- `main`: versão estável entregue.
- `dev`: integração das funcionalidades.
- `feature/*`: uma branch por etapa de desenvolvimento, mesclada em `dev`
  com `--no-ff` para preservar o histórico.
