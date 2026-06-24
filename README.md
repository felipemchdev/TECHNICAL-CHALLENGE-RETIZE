# Desafio Técnico de Engenharia de Dados - Retize

## 1. Visão Geral da Solução

Esta solução foi desenvolvida para responder a 5 perguntas de negócio fundamentais analisando dados extraídos do Instagram e TikTok. O projeto constrói um pipeline analítico completo, focado em extrair, carregar e transformar os dados brutos (CSVs) em modelos dimensionais otimizados para consulta, garantindo a integridade, rastreabilidade e consistência das métricas entre as duas plataformas. Para facilitar a validação visual por parte das áreas de negócio, foi incluído um painel interativo (Streamlit) capaz de expor as respostas e o catálogo de tabelas dinamicamente.

## 2. Arquitetura e Fluxo Adotado

A arquitetura segue o padrão de pipeline em lote (Batch Processing) e foi estruturada em três camadas lógicas (Medallion Architecture):

```text
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         PIPELINE RETIZE — VISÃO GERAL                          ║
╠══════════════╦═══════════════════════╦═══════════════════════╦══════════════════╣
║  INGESTÃO    ║      RAW (Bronze)     ║    SILVER (Staging)   ║   GOLD (Marts)   ║
║  Python      ║      PostgreSQL       ║    dbt views          ║   dbt tables     ║
╠══════════════╬═══════════════════════╬═══════════════════════╬══════════════════╣
║              ║  raw_instagram_media  ║                       ║                  ║
║  CSVs  ───►  ║  raw_ig_insights     ├──► stg_instagram    ──┤                  ║
║  (data/)     ║  raw_tiktok_posts    ├──► stg_tiktok       ──┼► mart_content_   ║
║              ║                       ║                       ║  performance     ║
║  src/        ║  raw_instagram_       ║                       ║                  ║
║  load_data   ║  comments            ├──► stg_platform     ──┼► mart_content_   ║
║  .py         ║  raw_tiktok_         ║    (comentários       ║  sentiment       ║
║              ║  comments            ║     unificados)       ║                  ║
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

1. **Ingestão (Raw):** Script em Python (`src/load_data.py`) que varre o diretório `data/` e realiza o *copy* direto e tipado dos arquivos CSV para o PostgreSQL sem nenhum tratamento.
2. **Transformação Silver:** Construída via **dbt**. Normaliza nomes de contas (lowercase), converte formatos e IDs para texto (evitando falhas de inteiros gigantes), e uniformiza as classificações de sentimentos (positive/negative/neutral), sem realizar agregações.
3. **Transformação Gold (Marts):** Modelos analíticos finais em **dbt**.
  - `mart_content_performance`: Unifica Instagram e TikTok deduplicando posts e garantindo métricas justas. As métricas de *reach* e *views* são expostas de forma clara e consolidada para o cálculo da taxa de engajamento final.
    - `mart_content_sentiment`: Agrega o sentimento dos comentários nível postagem para o cálculo de taxas negativas.
4. **Visualização:** Painel construído em Streamlit conectando diretamente no Banco PostgreSQL, consumindo a camada Gold para exibir métricas com tratativas brasileiras de números e porcentagens. Opcionalmente, pode-se usar as queries contidas na pasta `queries/`.

## 3. Como Preparar o Ambiente


**Requisitos:**

- Docker e Docker Compose instalados na máquina.
- (Opcional) Python 3.12 caso deseje rodar o painel visual localmente sem o container.

**Passo a passo inicial:**  
Crie ou configure o arquivo `.env` na raiz do repositório, com base em `.env.example` que contém as variáveis que guiarão todo o cluster:

```env
POSTGRES_USER=techtest
POSTGRES_PASSWORD=123
POSTGRES_DB=views_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

## 4. Como Subir o PostgreSQL e o Cluster com Docker Compose

Para inicializar os serviços do banco de dados (PostgreSQL), orquestrador (Airflow) e visualização (Streamlit), execute no terminal:

```bash
docker compose up -d --build
```

Isso criará uma rede isolada garantindo que todas as aplicações conversem com o banco na porta interna `5434` (exposta na porta `55436` para uso na sua máquina local).

## 5. Como Executar o Pipeline

O fluxo completo de ingestão e transformação (dbt) deve ser executado através da interface (UI) do Airflow. 

Com os serviços rodando, acesse em seu navegador:

- **URL:** [http://localhost:8080](http://localhost:8080)
- **Usuário:** admin
- **Senha:** 123

Na tela inicial do Airflow, localize a DAG chamada `analytics_dbt` e clique no botão de **"Trigger DAG"** (ícone de *play*) para iniciar a execução manual. O pipeline irá orquestrar sequencialmente a ingestão dos dados e a execução das transformações e testes do dbt.

### Alternativa: Execução via CLI

Caso prefira rodar as etapas separadamente via terminal, você pode executar os comandos diretamente no container do Airflow:

**Ingestão:**

```bash
docker compose exec -T airflow bash -lc "cd /opt/project && python src/load_data.py"
```

**Transformações e Testes (dbt):**

```bash
# Para executar a criação das Views (Silver) e Tabelas (Gold)
docker compose exec -T airflow bash -lc "cd /opt/project/analytics_dbt && dbt run --profiles-dir /opt/project/analytics_dbt"

# Para rodar as asserções de qualidade de dados
docker compose exec -T airflow bash -lc "cd /opt/project/analytics_dbt && dbt test --profiles-dir /opt/project/analytics_dbt"
```

## 6. Como Rodar as Queries

Você tem duas opções para validar as respostas do desafio:

**Opção A: Painel Streamlit (Recomendado)**
Acesse [http://localhost:8501](http://localhost:8501) no seu navegador (o streamlit já irá estar rodando no container automaticamente). As respostas já estarão processadas, os formatos de números padronizados no formato PT-BR, com tratamento de porcentagens e sem quebras visuais de IDs.

**Opção B: Via CLI (Queries SQL brutas)**
Caso prefira avaliar diretamente os scripts SQL disponíveis na pasta `queries/`, rode os comandos contra o container do postgres:

```bash
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/01_best_weekday_by_account.sql
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/02_platform_with_highest_negative_ratio_by_account.sql
# ... e assim por diante.
```

## 7. Principais Decisões Técnicas

- **Tipagem de IDs Gigantes:** Os IDs do Instagram extrapolam o limite de precisão numérico de aplicações front-end (Javascript 2^53). Para garantir que IDs como `17842135350559775` não se quebrem nem entrem em formato de notação científica ou ganhem separadores de milhares, eles foram convertidos via CAST explícito (`::text`) logo na camada Silver do dbt, propagando-se em formato de texto seguro para o Streamlit e queries finais.
- **Unificação de Views e Reach no Engajamento:** Para tornar a Taxa de Engajamento padronizada e justa entre Instagram e TikTok, a fórmula utilizada no denominador seleciona `GREATEST(COALESCE(reach, 0), COALESCE(views, 0))`. Isso garante que casos onde as Views são muito maiores que o Reach (ex: 16 Milhões de Views vs 8 Milhões de Reach num post do IG) a métrica real mais expressiva de exposição assuma a base do cálculo do engajamento.
- **Proteção contra Infinito/Divisão por Zero:** A função `NULLIF` foi acoplada ao denominador da métrica de engajamento e sentimentos. Posts sem tracking de views ou sem comentários não recebem taxas irreais "infinitas", permitindo cálculos de média (`AVG`) limpos no final do pipeline.
- **Padronização Textual:** Colunas de agrupamento categórico como `format`, `account_id` e `day_of_week` foram padronizadas em letra minúscula e em inglês (ex: `video`, `monday`), evitando duplicidade em tabelas dinâmicas.

## 8. Justificativas para Escolhas de Modelagem e Tecnologia

- **PostgreSQL:** Escolhido por ser um banco transacional e analítico extremamente confiável e portável via Docker, ideal para servir de base (Data Warehouse local) validando conceitos sem exigir provisionamento na nuvem para avaliação técnica.
- **dbt (Data Build Tool):** Optado ao invés de codificar transformações no Pandas por centralizar a lógica de negócio diretamente no banco (Push-down). Além de modularizar SQL (DRY), garante baterias de testes em relacionamentos e constraints out-of-the-box.
- **Streamlit:** Adicionado para fechar a jornada de dados comprovando a viabilidade visual da tabela Gold. Demonstra clareza, formatação regional e auto-atendimento de negócio sobre dados complexos.

## 9. Limitações, Premissas e Melhorias Futuras

**Premissas:** 

- Presumiu-se que posts ausentes de visualização ou alcance registrados legitimamente deveriam ter o seu engajamento anulado (NULL) e ignorado em médias.

**Limitações Atuais:**

- A ingestão bruta lê os dados em memória através do Pandas no `load_data.py`. Embora seja rápido e aplicável para o volume do desafio, isso criará gargalo em projetos maiores.
  
- O pipeline é disparado manualmente via UI do Airflow (`schedule_interval=None`). Essa decisão é intencional para o contexto do desafio; Em produção, o schedule seria configurado para `@daily` ou baseado em evento de chegada de dados.

**Melhorias Futuras:**

- **Refatorar Ingestão (Raw):** Substituir os DFs carregados em RAM por abordagens eficientes utilizando a feature de `COPY` nativo direto para o PostgreSQL via streams ou usando bibliotecas preparadas como DuckDB/Polars em caso de arquivos GCS/S3.
  
- **Data Quality Avançado:** Acoplar bibliotecas extras como o `dbt-expectations` para prever anomalias numéricas ou variação no volume.

- **Processamento Incremental:** Neste desafio, a tabela de performance atualiza realizando *Full Refresh*. Para tabelas maiores seria bom os modelos no dbt operarem de forma particionada e Incremental.

## 10. Uso de IA (Inteligência Artificial)

Neste projeto, ferramentas de IA (como Claude) foram utilizadas pontualmente como assistentes de codificação para:

- Aceleração na escrita e formatação do arquivo `README.md`.
- Geração de *boilerplates* estruturais para os testes `.yml` e asserções do `dbt`.
- Revisão ortográfica e sintática de queries SQL.  
- Todas as decisões de modelagem (como a escolha do `GREATEST` no engajamento, tipagem em texto para IDs e padronização) foram tomadas humanamente com base no contexto do desafio.

