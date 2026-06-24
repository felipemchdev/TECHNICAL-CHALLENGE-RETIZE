# Analytics Platform - Social Media Performance Pipeline

## 1. Visão Geral da Solução

Esta solução constrói um pipeline analítico completo para análise de desempenho de conteúdo em redes sociais (Instagram e TikTok). O projeto extrai, carrega e transforma dados brutos (CSVs) em modelos dimensionais otimizados para consulta, garantindo integridade, rastreabilidade e consistência das métricas entre plataformas. Para facilitar a validação visual, foi incluído um painel interativo (Streamlit) que expõe as análises e o catálogo de tabelas dinamicamente.

## 2. Arquitetura e Fluxo Adotado

A arquitetura segue o padrão de pipeline em lote (Batch Processing) estruturada em três camadas lógicas (Medallion Architecture):

```text
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    ANALYTICS PLATFORM - VISÃO GERAL                             ║
╠══════════════╦═══════════════════════╦═══════════════════════╦══════════════════╣
║  INGESTÃO    ║      RAW (Bronze)     ║    SILVER (Staging)   ║   GOLD (Marts)   ║
║  Python      ║      PostgreSQL       ║    dbt views          ║   dbt tables     ║
╠══════════════╬═══════════════════════╬═══════════════════════╬══════════════════╣
║              ║  raw_instagram_media  ║                       ║                  ║
║  CSVs  ───►  ║  raw_instagram_      ├──► stg_instagram    ──┤                  ║
║  (data/)     ║  insights            ├──► stg_tiktok       ──┼► mart_content_   ║
║              ║  raw_tiktok_posts    ├──► stg_platform     ──┼  performance     ║
║              ║  raw_instagram_       ║    (comentários       ║                  ║
║  src/        ║  comments            ║     unificados)       ║  mart_content_   ║
║  load_data   ║  raw_tiktok_         ║                       ║  sentiment       ║
║  .py         ║  comments            ║                       ║                  ║
╚══════════════╩═══════════════════════╩═══════════════════════╩══════════════════╝
                          ▲                                           │
                   Airflow DAG                               Streamlit Dashboard
                   (orquestração)                            (validação visual)
                   dags/pipeline.py                          streamlit_app.py
```

**Granularidade das tabelas finais:**

| Tabela                     | Nível                            | Chave                    |
| -------------------------- | -------------------------------- | ------------------------ |
| `mart_content_performance` | 1 linha por post (deduplicado)   | `(platform, content_id)` |
| `mart_content_sentiment`   | 1 linha por post com comentários | `(platform, content_id)` |

### Fluxo por Camada

1. **Ingestão (Raw):** Script em Python (`src/load_data.py`) que varre o diretório `data/` e realiza o *copy* direto e tipado dos arquivos CSV para o PostgreSQL sem tratamento.

2. **Transformação Silver:** Construída via **dbt**. Normaliza nomes de contas (lowercase), converte formatos e IDs para texto (evitando falhas de inteiros gigantes), e uniformiza classificações de sentimentos (positive/negative/neutral), sem realizar agregações.

3. **Transformação Gold (Marts):** Modelos analíticos finais em **dbt**.
   - `mart_content_performance`: Unifica Instagram e TikTok deduplicando posts e garantindo métricas justas. Métricas de *reach* e *views* são consolidadas para cálculo da taxa de engajamento.
   - `mart_content_sentiment`: Agrega sentimento dos comentários por post para cálculo de taxas negativas.

4. **Visualização:** Painel Streamlit conectando ao PostgreSQL, consumindo a camada Gold com formatação regional (PT-BR) e tratamento de números e porcentagens.

## 3. Requisitos

- Docker e Docker Compose instalados
- (Opcional) Python 3.12 para rodar Streamlit localmente sem container

## 4. Configuração do Ambiente

Crie um arquivo `.env` na raiz do repositório com base em `.env.example`:

```env
POSTGRES_USER=techtest
POSTGRES_PASSWORD=123
POSTGRES_DB=views_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

## 5. Inicializando os Serviços

Para subir PostgreSQL, Airflow e Streamlit:

```bash
docker compose up -d --build
```

Isso criará uma rede isolada garantindo que todas as aplicações conversem com o banco na porta interna `5434` (exposta na porta `55436` para uso na sua máquina local).

## 6. Executando o Pipeline

O fluxo completo de ingestão e transformação (dbt) é orquestrado via Airflow.

### Via UI do Airflow (Recomendado)

Acesse em seu navegador:

- **URL:** http://localhost:8080
- **Usuário:** admin
- **Senha:** 123

Na tela inicial do Airflow, localize a DAG chamada `analytics_dbt` e clique no botão de **"Trigger DAG"** (ícone de *play*) para iniciar a execução manual. O pipeline irá orquestrar sequencialmente a ingestão dos dados e a execução das transformações e testes do dbt.

### Via CLI

Ingestão:

```bash
docker compose exec -T airflow bash -lc "cd /opt/project && python src/load_data.py"
```

Transformações e Testes (dbt):

```bash
# Para executar a criação das Views (Silver) e Tabelas (Gold)
docker compose exec -T airflow bash -lc "cd /opt/project/analytics_dbt && dbt run --profiles-dir /opt/project/analytics_dbt"

# Para rodar as asserções de qualidade de dados
docker compose exec -T airflow bash -lc "cd /opt/project/analytics_dbt && dbt test --profiles-dir /opt/project/analytics_dbt"
```

## 7. Validando os Resultados

### Opção A: Painel Streamlit (Recomendado)

Acesse http://localhost:8501 no seu navegador. O painel expõe as análises processadas com formatação PT-BR, números sem quebras e tratamento visual de IDs.

### Opção B: Queries SQL Brutas

Execute os scripts SQL disponíveis em `queries/`:

```bash
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/01_best_weekday_by_account.sql
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/02_platform_with_highest_negative_ratio_by_account.sql
# ... e assim por diante.
```

## 8. Principais Decisões Técnicas

- **Tipagem de IDs Gigantes:** IDs do Instagram extrapolam o limite de precisão numérico de front-end (JavaScript 2^53). Foram convertidos via CAST explícito (`::text`) na camada Silver, propagando em formato seguro para Streamlit e queries.

- **Unificação de Reach e Views:** Para manter a Taxa de Engajamento padronizada e justa entre Instagram e TikTok, o denominador usa `GREATEST(COALESCE(reach, 0), COALESCE(views, 0))`. Garante que a métrica de exposição mais expressiva assuma a base do cálculo.

- **Proteção contra Divisão por Zero:** A função `NULLIF` protege métricas contra valores "infinitos". Posts sem tracking não recebem taxas irreais, permitindo cálculos de média (`AVG`) limpos.

- **Padronização Textual:** Colunas categóricas (`format`, `account_id`, `day_of_week`) em minúsculas e inglês, evitando duplicidade em tabelas dinâmicas.

## 9. Escolhas de Tecnologia

- **PostgreSQL:** Banco transacional e analítico confiável, portável via Docker. Ideal como Data Warehouse local validando conceitos sem exigir provisionamento em nuvem.

- **dbt (Data Build Tool):** Centraliza lógica de negócio diretamente no banco (Push-down). Modulariza SQL (DRY) e oferece testes de relacionamentos e constraints out-of-the-box.

- **Streamlit:** Painel visual para validação de dados finais, demonstrando formatação regional e auto-atendimento de negócio sobre dados complexos.

- **Airflow:** Orquestração de pipeline com UI acessível e controle granular das dependências entre tarefas.

## 10. Limitações e Melhorias Futuras

**Limitações Atuais:**

- Ingestão bruta lê dados em memória via Pandas (`load_data.py`). Funciona para este volume; gargalo em projetos maiores.
- Pipeline disparado manualmente (`schedule_interval=None`). Em produção seria `@daily` ou baseado em evento.

**Melhorias Futuras:**

- Substituir ingestão por `COPY` nativo ou streaming direto (DuckDB/Polars com GCS/S3).
- Acoplar `dbt-expectations` para anomalias numéricas e variação de volume.
- Implementar modelos incrementais e particionados no dbt para atualizações eficientes.

## 11. Estrutura do Repositório

```
.
├── data/                      # CSVs de entrada
├── src/
│   └── load_data.py          # Script de ingestão bruta
├── dbt/                       # Transformações dbt
│   ├── models/
│   │   ├── staging/          # Silver layer (views)
│   │   └── marts/            # Gold layer (tabelas)
│   ├── tests/                # Asserções de qualidade
│   └── schema.yml            # Documentação de modelos
├── dags/
│   └── pipeline.py           # DAG Airflow
├── queries/                  # SQL para validação
├── streamlit_app.py          # Dashboard visual
├── docker-compose.yaml       # Orquestração de containers
└── README.md                 # Este arquivo
```

## 12. Contribuindo

Para sugestões ou melhorias, abra uma issue ou pull request no repositório.
