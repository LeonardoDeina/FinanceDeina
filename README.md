# FinanceDeina

Sistema de gestão e previsão financeira pessoal — V1 (Finance Manager), local-first,
com suporte nativo a múltiplas moedas.

Baseado nos documentos comercial e técnico do produto, com uma extensão em relação à
especificação original: a V1 documentada previa operar com uma única moeda-base; como o
uso real envolve receitas e despesas em EUR, USD e BRL simultaneamente, este V1 já
suporta múltiplas moedas nas contas e transações (ver "Multi-moeda" abaixo).

## Stack

- Backend: Python 3.12 + FastAPI + SQLAlchemy + Alembic + MySQL 8.
- Frontend: React + TypeScript + Vite.
- Execução local via Docker Compose.

## Escopo desta versão (V1 — Finance Manager)

- Contas (múltiplas moedas), categorias e tags.
- Transações manuais (planejado/realizado, INCOME/EXPENSE), transferências entre contas
  (inclusive entre moedas diferentes, com taxa de câmbio explícita).
- Recorrências (semanal, quinzenal, mensal, trimestral, semestral, anual).
- Orçamentos por categoria/período, com progresso planejado x realizado.
- Dashboard com saldo, receitas, despesas, economia e taxa de poupança — consolidados na
  moeda-base e detalhados por moeda.
- Motor de previsão (forecast) com base em transações futuras, recorrências e orçamento
  residual (sem dupla contagem), com snapshots persistidos.
- Estimativa de capacidade de poupança (mediana robusta dos últimos 6 meses).
- Fechamento mensal (planejado x realizado), com reabertura rastreável.
- Backup/restauração (mysqldump) e exportação de transações em CSV.

Fora do escopo desta versão (previstos para V2/V3 pela documentação): importação de
extratos bancários (CSV/OFX/XLSX) e conciliação, caixas/metas com alocação, e o
assistente de IA.

## Multi-moeda

- Cada conta tem sua própria moeda (`accounts.currency`); cada transação também guarda a
  moeda em que ocorreu.
- Taxas de câmbio são cadastradas manualmente em `exchange_rates` (a especificação técnica
  explicitamente deixa a conversão automática em tempo real fora do escopo da V1). O
  sistema usa a taxa mais recente na data de referência e, se o par exato não existir,
  tenta uma ponte pela moeda-base do usuário (ex.: USD→BRL via USD→EUR e BRL→EUR).
- Transferências entre contas de moedas diferentes calculam o valor recebido usando a
  taxa vigente na data da transferência.
- Uma conta cuja moeda ainda não tem taxa cadastrada continua funcionando normalmente
  (mostra seu próprio saldo); apenas o valor consolidado na moeda-base fica indisponível
  até a taxa ser cadastrada — o sistema nunca trava por causa disso.

## Rodando localmente

```bash
cp .env.example .env
# edite .env e defina senhas de MySQL antes de subir em qualquer ambiente compartilhado

docker compose up --build
```

- Backend: http://localhost:8000 (docs interativos em `/docs`)
- Frontend: http://localhost:5173
- MySQL: localhost:3306 (apenas para acesso local/depuração)

Na primeira subida, o backend aplica as migrations do Alembic e cria automaticamente o
perfil local e as moedas EUR/USD/BRL/GBP/CHF. Cadastre as taxas de câmbio necessárias em
Configurações → Taxas de câmbio.

## Desenvolvimento

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                      # suíte de testes das regras de negócio
alembic upgrade head        # aplica migrations (requer MySQL acessível via DATABASE_URL)
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testes

A suíte `backend/app/tests` cobre as regras de negócio centrais do documento técnico:
cálculo de economia e taxa de poupança, exclusão de transferências do resultado mensal,
saldo por conta, geração de recorrências (incluindo virada de mês), conversão de moeda
(direta, inversa e por ponte), orçamento residual sem dupla contagem, fechamento e
reabertura de mês, e serialização decimal (nunca float) dos valores monetários.

```bash
cd backend && pytest
```

## Estrutura

```
backend/
  app/
    accounts/ categories/ transactions/ recurring/ budgets/
    forecasting/ closings/ reports/ currency/ audit/ users/ backup/
    core/ db/
  migrations/          # Alembic
frontend/
  src/
    pages/ components/ api/ context/ lib/
docker-compose.yml
```

## Backup e restauração

- `POST /api/v1/backup` gera um dump (`mysqldump`) versionado por data/hora em
  `BACKUP_DIR`.
- `POST /api/v1/backup/{filename}/restore?confirm=true` restaura um backup após validar
  seu cabeçalho de versão de schema — nunca restaura um arquivo sem esse marcador.
- `GET /api/v1/transactions/export.csv` exporta transações respeitando os filtros
  aplicados.
