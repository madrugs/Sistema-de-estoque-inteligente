# Histórico de versões

Registro das etapas de desenvolvimento do sistema, do que foi criado e do que
foi alterado em cada uma. Cada versão corresponde a uma etapa mesclada em
`dev` com tag no Git.

## v0.5.0 — Painel com indicadores e gráficos

**Criado**
- Painel inicial (`/`) com agregações do ORM: `Sum` (capital imobilizado =
  saldo x preço de custo, e unidades em estoque), `Count` (itens cadastrados
  e produtos abaixo do mínimo) e `Avg` (preço médio de venda).
- Gráficos com Chart.js (CDN cdnjs): volume em estoque por categoria (barras) e
  movimentações por tipo (rosca).
- Tabela das últimas 5 movimentações.
- `static/js/painel.js`: se o Chart.js não carregar, a página mostra um aviso
  em `aria-live` e os números continuam disponíveis.

**Alterado**
- `/` deixa de redirecionar para o estoque e passa a ser o painel.
- 39 testes no total (painel: indicadores, dados dos gráficos e login).

## v0.4.0 — Telas web e interatividade

**Criado**
- Telas em Django Templates: Estoque (`/estoque/`), Movimentar (`/movimentar/`),
  Histórico (`/historico/`) e login (`/contas/login/`).
- `templates/base.html` com HTML5 semântico (`header`, `nav`, `main`), link
  "pular para o conteúdo" e foco visível em todos os controles.
- `static/js/busca-estoque.js`: filtro em tempo real pelo evento `input`, por
  nome ou código, e filtro "somente abaixo do mínimo", sem recarregar a página.
- `static/js/movimentacao.js`: subtotal, saldo previsto e aviso de saldo
  insuficiente calculados na hora. O registro é feito com `fetch()` na API, e
  saldo e mensagem são atualizados sem refresh.
- `static/js/utils.js`: funções compartilhadas (token CSRF, moeda em R$,
  mensagens de erro da API).
- `static/js/fornecedor_cep.js`: no cadastro de fornecedor (Django admin), o
  endereço é preenchido ao digitar o CEP.
- Acessibilidade: `label for`, `aria-live="polite"` nas mensagens de estoque
  baixo e de retorno, `aria-current` no menu e tabelas com `caption` e
  `scope`.
- Redirecionamento de `/` (nome `dashboard`) para o estoque. Será substituído
  pelo painel na próxima versão.

**Alterado**
- `estoque/admin.py`: `FornecedorAdmin` carrega o script de CEP.
- `WHITENOISE_USE_FINDERS` ativado em desenvolvimento, para servir `static/`
  sem `collectstatic`.

**Corrigido durante a verificação no navegador**
- Valores monetários dos atributos `data-*` saíam com vírgula (`28,50`) por
  causa da localização pt-BR, e o cálculo virava `NaN`. Agora são enviados sem
  formatação.
- Ao trocar o tipo de movimentação, o motivo podia ficar vazio. Agora sempre
  seleciona a primeira opção válida.

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
