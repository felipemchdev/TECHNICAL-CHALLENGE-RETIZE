# Desafio Técnico de Engenharia de Dados - Retize

## 1. Visão Geral da Solução
Esta solução foi desenvolvida para responder a 5 perguntas de negócio fundamentais analisando dados extraídos do Instagram e TikTok. O projeto constrói um pipeline analítico completo, focado em extrair, carregar e transformar os dados brutos (CSVs) em modelos dimensionais otimizados para consulta, garantindo a integridade, rastreabilidade e consistência das métricas entre as duas plataformas. Para facilitar a validação visual por parte das áreas de negócio, foi incluído um painel interativo (Streamlit) capaz de expor as respostas e o catálogo de tabelas dinamicamente.

## 2. Arquitetura e Fluxo Adotado
A arquitetura segue o padrão de pipeline em lote (Batch Processing) e foi estruturada em três camadas lógicas (Medallion Architecture):

1. **Ingestão (Raw):** Script em Python (`src/load_data.py`) que varre o diretório `data/` e realiza o _copy_ direto e tipado dos arquivos CSV para o PostgreSQL sem nenhum tratamento.
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
Crie ou configure o arquivo `.env` na raiz do repositório contendo as variáveis que guiarão todo o cluster:
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
Isso criará uma rede isolada garantindo que todas as aplicações conversem com o banco na porta interna `5432` (exposta na porta `55432` para uso na sua máquina local).

## 5. Como Executar a Ingestão
Com os serviços rodando, utilize o container do Airflow para executar o script de ingestão bruta (que irá ler a pasta `/data` e popular as tabelas `raw_`):

```bash
docker compose exec -T airflow bash -lc "cd /opt/project && python src/load_data.py"
```
Você verá logs indicando `table_loaded` com a quantidade de linhas para os 5 CSVs base.

## 6. Como Executar as Transformações e Testes (dbt)
Após popular o PostgreSQL, execute o pipeline do dbt para tratar, transformar e testar as tabelas analíticas:

```bash
# Para executar a criação das Views (Silver) e Tabelas (Gold)
docker compose exec -T airflow bash -lc "cd /opt/project/retize_dbt && dbt run --profiles-dir /opt/project/retize_dbt"

# Para rodar as asserções de qualidade de dados (Edge cases, Not Null, Relacionamentos)
docker compose exec -T airflow bash -lc "cd /opt/project/retize_dbt && dbt test --profiles-dir /opt/project/retize_dbt"
```

## 7. Como Rodar as Queries
Você tem duas opções para validar as respostas do desafio:

**Opção A: Painel Streamlit (Recomendado)**
Acesse [http://localhost:8501](http://localhost:8501) no seu navegador. As respostas já estarão processadas, os formatos de números padronizados no formato PT-BR, com tratamento de porcentagens e sem quebras visuais de Javascript graças à tipagem correta de IDs.

**Opção B: Via CLI (Queries SQL brutas)**
Caso prefira avaliar diretamente os scripts SQL disponíveis na pasta `queries/`, rode os comandos contra o container do postgres:
```bash
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/01_best_weekday_by_account.sql
docker compose exec -T postgres psql -U techtest -d views_db -f /opt/project/queries/02_platform_with_highest_negative_ratio_by_account.sql
# ... e assim por diante.
```

## 8. Principais Decisões Técnicas

- **Tipagem de IDs Gigantes:** Os IDs do Instagram extrapolam o limite de precisão numérico de aplicações front-end (Javascript 2^53). Para garantir que IDs como `17842135350559775` não se quebrem nem entrem em formato de notação científica ou ganhem separadores de milhares, eles foram convertidos via CAST explícito (`::text`) logo na camada Silver do dbt, propagando-se em formato de texto seguro para o Streamlit e queries finais.
- **Unificação de Views e Reach no Engajamento:** Para tornar a Taxa de Engajamento padronizada e justa entre Instagram e TikTok, a fórmula utilizada no denominador seleciona `GREATEST(COALESCE(reach, 0), COALESCE(views, 0))`. Isso garante que casos onde as Views são muito maiores que o Reach (ex: 16 Milhões de Views vs 8 Milhões de Reach num post do IG) a métrica real mais expressiva de exposição assuma a base do cálculo do engajamento.
- **Proteção contra Infinito/Divisão por Zero:** A função `NULLIF` foi acoplada ao denominador da métrica de engajamento e sentimentos. Posts sem tracking de views ou sem comentários não recebem taxas irreais "infinitas", permitindo cálculos de média (`AVG`) limpos no final do pipeline.
- **Padronização Textual:** Colunas de agrupamento categórico como `format`, `account_id` e `day_of_week` foram padronizadas em letra minúscula e em inglês (ex: `video`, `monday`), evitando duplicidade em tabelas dinâmicas.

## 9. Justificativas para Escolhas de Modelagem e Tecnologia
- **PostgreSQL:** Escolhido por ser um banco transacional e analítico extremamente confiável e portável via Docker, ideal para servir de base (Data Warehouse local) validando conceitos sem exigir provisionamento na nuvem para avaliação técnica.
- **dbt (Data Build Tool):** Optado ao invés de codificar transformações no Pandas por centralizar a lógica de negócio diretamente no banco (Push-down). Além de modularizar SQL (DRY), garante baterias de testes em relacionamentos e constraints out-of-the-box.
- **Streamlit:** Adicionado para fechar a jornada de dados comprovando a viabilidade visual da tabela Gold. Demonstra clareza, formatação regional e auto-atendimento de negócio sobre dados complexos.

## 10. Limitações, Premissas e Melhorias Futuras

**Premissas:** 
- Assumiu-se que o timestamp gerado nas plataformas base reflete o fuso horário correto da análise ou que estava consolidado em UTC. 
- Presumiu-se que posts ausentes de visualização ou alcance registrados legitimamente deveriam ter o seu engajamento anulado (NULL) e ignorado em médias.

**Limitações Atuais:**
- A ingestão bruta lê os dados em memória através do Pandas no `load_data.py`. Embora seja rápido e aplicável para o volume do desafio, isso criará gargalo de RAM se o arquivo bater na casa das dezenas de gigabytes. 
- Orquestração de Jobs é puramente manual. As dependências (DAGs) existem no Airflow, mas não agendam automaticamente por padrão (`schedule_interval=None`).

**Melhorias Futuras:**
- **Refatorar Ingestão (Raw):** Substituir os DFs carregados em RAM por abordagens eficientes utilizando a feature de `COPY` nativo direto para o PostgreSQL via streams ou usando bibliotecas preparadas como DuckDB/Polars em caso de arquivos GCS/S3.
- **Data Quality Avançado:** Acoplar bibliotecas extras como o `dbt-expectations` para prever anomalias numéricas ou variação abrupta no volume (ex: alertando caso o número de posts dobre subitamente de um dia para outro).
- **Processamento Incremental:** Neste desafio, a tabela de performance atualiza realizando _Full Refresh_. Para tabelas massivas de Big Data, deve-se modificar os modelos no dbt para operarem de forma particionada e _Incremental_.

## 11. Uso de IA (Inteligência Artificial)

Neste projeto, ferramentas de IA (como ChatGPT/Claude/Gemini) foram utilizadas pontualmente como assistentes de codificação para:
- Aceleração na escrita e formatação do arquivo `README.md`.
- Geração de *boilerplates* estruturais para os testes `.yml` e asserções do `dbt`.
- Revisão ortográfica e sintática de queries SQL.
Todas as decisões de modelagem (como a escolha do `GREATEST` no engajamento, tipagem em texto para IDs e padronização) foram tomadas humanamente com base no contexto do desafio. particionada e _Incremental_.