# Histórico de versões

Registro das etapas de desenvolvimento do sistema, do que foi criado e do que
foi alterado em cada uma. Cada versão corresponde a uma etapa mesclada em
`dev` com tag no Git.

## v0.1.0 — Configuração base do projeto

**Criado**
- Projeto Django `config/` (settings, urls, wsgi, asgi).
- Configurações lidas de variáveis de ambiente (`.env`), com
  `.env.example` como modelo.
- Suporte a SQLite (desenvolvimento) e PostgreSQL via `DATABASE_URL`
  (produção).
- Aplicativo `estoque` registrado, ainda sem modelos.
- `requirements.txt` com Django, Django REST Framework, whitenoise,
  gunicorn, dj-database-url, python-dotenv e psycopg.
- `README.md` com instruções de execução e fluxo de branches.
- `.gitignore` (exclui `.venv`, `.env`, banco local e arquivos gerados).

**Decisões**
- Autenticação por sessão e permissão padrão "usuário autenticado" na API,
  pois a API permite registrar movimentações de estoque.
- `whitenoise` para servir os arquivos estáticos sem servidor separado.
