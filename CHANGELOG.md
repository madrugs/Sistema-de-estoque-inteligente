# Histórico de versões

Registro das etapas de desenvolvimento do sistema, do que foi criado e do que
foi alterado em cada uma. Cada versão corresponde a uma etapa mesclada em
`dev` com tag no Git.

## v0.3.0 — API REST e consulta de CEP

**Criado**
- Endpoints JSON em `/api/` (Django REST Framework), todos exigindo login:
  - `produtos/` (listagem e detalhe) com filtros `q`, `categoria` e
    `abaixo_minimo=1`.
  - `movimentacoes/` (listagem e registro por POST). Não há PUT, PATCH nem
    DELETE: o histórico não pode ser alterado pela API.
  - `fornecedores/` (listagem e detalhe).
  - `cep/<cep>/`: consulta ao ViaCEP pelo backend, com tratamento de CEP
    inválido (400), não encontrado (404) e serviço fora do ar (503).
- `estoque/serializers.py`: o saldo nunca é aceito do cliente. A movimentação
  é sempre gravada pelo serviço, e a resposta devolve `saldo_apos`.
- `estoque/cep.py`: normalização do CEP e chamada ao ViaCEP com timeout de 5 s.
- Testes de integração de views/endpoints (status 200/201/400/404/503,
  JSON esperado e bloqueio de saídas inválidas). Total: 32 testes.

**Alterado**
- `SaldoInsuficienteError` agora usa erro por campo (`quantidade`), para que a
  API devolva o erro no campo certo.

## v0.2.0 — Modelos de dados e regras de estoque

**Criado**
- `Categoria`, `Fornecedor`, `Produto` e `MovimentacaoEstoque` em
  `estoque/models.py`, com as migrações iniciais.
- `Produto.abaixo_do_minimo` (saldo menor que o estoque mínimo) e
  `Produto.valor_imobilizado` (saldo x preço de custo).
- `estoque/services.py`: `registrar_movimentacao`, único caminho para alterar
  o saldo. Roda em transação, bloqueia o produto (`select_for_update`) e recusa
  saídas maiores que o saldo (`SaldoInsuficienteError`).
- Registro no Django admin. Movimentações são somente leitura.
- `estoque/tests.py` com 13 testes unitários: regra de estoque mínimo, cálculo
  de saldo em entrada e saída, bloqueio de saída sem saldo, compatibilidade
  motivo x tipo e imutabilidade do log.

**Decisões**
- `quantidade` (saldo) não é editável no admin, para respeitar a premissa de
  log de auditoria.
- Movimentação não pode ser alterada nem apagada (`PermissionError`).
- Preços em `DecimalField`, nunca em float.

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
