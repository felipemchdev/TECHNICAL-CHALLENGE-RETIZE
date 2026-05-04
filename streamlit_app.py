import os
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


def _load_dotenv(path: str = ".env") -> dict[str, str]:
    env_file = Path(path)
    data: dict[str, str] = {}
    if not env_file.exists():
        return data
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _normalize_host(host: str) -> str:
    if host == "postgres":
        try:
            socket.gethostbyname(host)
            return host
        except OSError:
            return "localhost"
    return host


def _db_config(host: str, port: str, user: str, password: str, db: str) -> dict:
    return {
        "user": user.strip(),
        "password": password.strip(),
        "host": _normalize_host(host.strip()),
        "port": port.strip(),
        "db": db.strip(),
    }


def get_engine(cfg: dict):
    user = quote_plus(cfg["user"])
    password = quote_plus(cfg["password"])
    db_name = quote_plus(cfg["db"])
    db_url = (
        f"postgresql+pg8000://{user}:{password}"
        f"@{cfg['host']}:{cfg['port']}/{db_name}"
    )
    return create_engine(db_url)


def load_dataframe(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    base_cfg = _db_config(
        st.session_state["db_host"],
        st.session_state["db_port"],
        st.session_state["db_user"],
        st.session_state["db_password"],
        st.session_state["db_name"],
    )
    dotenv_cfg = _db_config(
        st.session_state["env_host"],
        st.session_state["env_port"],
        st.session_state["env_user"],
        st.session_state["env_password"],
        st.session_state["env_db"],
    )
    candidates = [base_cfg]
    if dotenv_cfg not in candidates:
        candidates.append(dotenv_cfg)
    if base_cfg["host"] in ("localhost", "127.0.0.1"):
        for fallback_port in ("55432", "5433", "5432"):
            alt_cfg = dict(base_cfg)
            alt_cfg["port"] = fallback_port
            if alt_cfg not in candidates:
                candidates.append(alt_cfg)
    if dotenv_cfg["host"] in ("localhost", "127.0.0.1"):
        for fallback_port in ("55432", "5433", "5432"):
            dotenv_alt = dict(dotenv_cfg)
            dotenv_alt["port"] = fallback_port
            if dotenv_alt not in candidates:
                candidates.append(dotenv_alt)

    last_exc: Optional[Exception] = None
    for cfg in candidates:
        try:
            engine = get_engine(cfg)
            with engine.begin() as conn:
                return pd.read_sql(text(sql), conn, params=params or {})
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Falha inesperada ao consultar o banco.")


def check_connection() -> tuple[bool, str]:
    try:
        load_dataframe("SELECT 1 AS ok")
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def format_br(val, is_pct: bool = False) -> str:
    """Formata numeros para o padrao brasileiro: ponto para milhar, virgula para decimal. Opcionalmente formata como %"""
    if isinstance(val, (int, float)) or type(val).__name__ == "Decimal":
        try:
            fval = float(val)
        except (ValueError, TypeError):
            return str(val)
            
        if fval == fval: # check nan
            if is_pct:
                s = f"{fval * 100:,.2f}%"
            else:
                # Retira as casas decimais (remove tudo pos virgula) para valores que nao sao taxa (rate)
                s = f"{int(fval):,}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return str(val)

def format_df(df: pd.DataFrame):
    """Aplica formatacao brasileira no pandas DataFrame e % em taxas."""
    
    rate_cols = ['engagement_rate', 'avg_engagement_rate', 'negative_ratio']
    count_cols = ['likes', 'comments_count', 'reach', 'views', 'total_comments', 'negative_comments', 'views_or_reach']
    
    # 1. Ajuste robusto de tipos para evitar o ValueError(Unknown format code '%') no styler
    for col in df.columns:
        if col == 'id' or col.endswith("_id") or col == 'item_id':
            df[col] = df[col].astype(str) # Garante que ids fiquem como texto puro
        elif col in count_cols or col in rate_cols:
            # Qualquer nulo ou string perdida em coluna numerica vira NaN confiavelmente (float)
            df[col] = pd.to_numeric(df[col], errors='coerce') 

    # 2. Cria dicionario de formatacao customizado
    format_dict = {}
    for col in df.columns:
        if col in rate_cols:
            format_dict[col] = "{:.2%}" # Mantem % com duas casas decimais
        elif col in count_cols:
            format_dict[col] = "{:,.0f}" # Remove todos os decimais e formata no padrao de inteiros
            
    # 3. Formata Dataframe (na_rep '-' previne nulos de exibirem nan ou string bugada)
    if format_dict:
        return df.style.format(formatter=format_dict, decimal=",", thousands=".", precision=0, na_rep="-")
    return df.style.format(decimal=",", thousands=".", precision=0, na_rep="-")


st.set_page_config(page_title="Retize Social Analytics", layout="wide", initial_sidebar_state="collapsed")
st.title("Analytics Table Viewer")
st.caption("Retize Social Analytics Challenge")

dotenv_values = _load_dotenv()

if "db_host" not in st.session_state:
    st.session_state["env_host"] = dotenv_values.get("POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost"))
    st.session_state["env_port"] = dotenv_values.get("POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))
    st.session_state["env_user"] = dotenv_values.get("POSTGRES_USER", os.getenv("POSTGRES_USER", "techtest"))
    st.session_state["env_password"] = dotenv_values.get("POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "123"))
    st.session_state["env_db"] = dotenv_values.get("POSTGRES_DB", os.getenv("POSTGRES_DB", "views_db"))

    st.session_state["db_host"] = st.session_state["env_host"]
    st.session_state["db_port"] = st.session_state["env_port"]
    st.session_state["db_user"] = st.session_state["env_user"]
    st.session_state["db_password"] = st.session_state["env_password"]
    st.session_state["db_name"] = st.session_state["env_db"]

with st.sidebar:
    st.header("Conexao")
    if st.button("Resetar com .env", use_container_width=True):
        st.session_state["db_host"] = st.session_state["env_host"]
        st.session_state["db_port"] = st.session_state["env_port"]
        st.session_state["db_user"] = st.session_state["env_user"]
        st.session_state["db_password"] = st.session_state["env_password"]
        st.session_state["db_name"] = st.session_state["env_db"]
        st.rerun()
    st.session_state["db_host"] = st.text_input("Host", value=st.session_state["db_host"])
    st.session_state["db_port"] = st.text_input("Porta", value=st.session_state["db_port"])
    st.session_state["db_name"] = st.text_input("Database", value=st.session_state["db_name"])
    st.session_state["db_user"] = st.text_input("Usuario", value=st.session_state["db_user"])
    st.session_state["db_password"] = st.text_input(
        "Senha", value=st.session_state["db_password"], type="password"
    )
    st.caption("Fora do Docker: localhost. Dentro do Docker: postgres.")
    st.caption(
        f".env carregado -> host={st.session_state['env_host']} port={st.session_state['env_port']} "
        f"user={st.session_state['env_user']} db={st.session_state['env_db']}"
    )

is_connected, conn_error = check_connection()
if not is_connected:
    st.error("Nao foi possivel conectar ao Postgres.")
    st.markdown(
        "Verifique se o banco esta no ar e se as variaveis locais estao corretas:\n"
        "- `POSTGRES_HOST=localhost`\n"
        "- `POSTGRES_PORT=55432` (preferencial), `5433` ou `5432`\n"
        "- `POSTGRES_DB=views_db`\n"
        "- `POSTGRES_USER` e `POSTGRES_PASSWORD` validos\n\n"
        "Suba o banco com `docker compose up -d` antes de abrir o app."
    )
    st.code(conn_error)
    st.stop()

try:
    load_dataframe("SELECT 1 FROM mart_content_performance LIMIT 1")
except Exception as exc:
    st.warning("As tabelas analíticas ainda não foram criadas no banco de dados.")
    st.markdown(
        "O banco de dados está online e conectado, mas a tabela `mart_content_performance` não existe. "
        "Isso acontece porque o pipeline de dados (ingestão e dbt) ainda não foi executado.\n\n"
        "**Para resolver, execute os comandos abaixo no seu terminal:**\n\n"
        "1. Ingestão dos dados (raw):\n"
        "```bash\n"
        "docker compose exec -T airflow bash -lc \"cd /opt/project && python src/load_data.py\"\n"
        "```\n"
        "2. Transformações do dbt (silver/gold):\n"
        "```bash\n"
        "docker compose exec -T airflow bash -lc \"cd /opt/project/retize_dbt && dbt run --profiles-dir /opt/project/retize_dbt\"\n"
        "```\n"
        "Após rodar os comandos, **atualize a página**."
    )
    st.code(str(exc))
    st.stop()

accounts_df = load_dataframe(
    "SELECT DISTINCT account_id FROM mart_content_performance ORDER BY account_id"
)
account_options = ["(todas)"] + accounts_df["account_id"].dropna().astype(str).tolist()
selected_account = st.sidebar.selectbox("Conta", account_options, index=0)

platform_options = ["(todas)", "instagram", "tiktok"]
selected_platform = st.sidebar.selectbox("Plataforma", platform_options, index=0)


account_filter_sql = ""
platform_filter_sql = ""
params = {}

if selected_account != "(todas)":
    account_filter_sql = " AND account_id = :account_id"
    params["account_id"] = selected_account

if selected_platform != "(todas)":
    platform_filter_sql = " AND platform = :platform"
    params["platform"] = selected_platform

st.subheader("Explorador de tabelas por camada")
layer_options = {
    "raw": [
        "raw_instagram_media",
        "raw_instagram_media_insights",
        "raw_instagram_comments",
        "raw_tiktok_posts",
        "raw_tiktok_comments",
    ],
    "silver": ["silver_instagram_content", "silver_tiktok_content", "silver_comments"],
    "gold": ["mart_content_performance", "mart_content_sentiment"],
}
selected_layer = st.selectbox("Camada", list(layer_options.keys()), index=2)
selected_table = st.selectbox("Tabela", layer_options[selected_layer], index=0)
st.caption(f"Mostrando até 10.000 linhas da tabela {selected_table}. Clique no cabecalho de uma coluna para ordenar.")
st.dataframe(format_df(load_dataframe(f'SELECT * FROM "{selected_table}" LIMIT 10000')), use_container_width=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "1) Melhor Dia",
        "2) Plataforma Negativa",
        "3) Top 10 Conteudos",
        "4) Top 3 por Conta",
        "5) Melhor Formato",
    ]
)

with tab1:
    st.subheader("Melhor dia da semana por conta (engajamento medio)")
    q1 = f"""
    WITH base AS (
        SELECT account_id, day_of_week, engagement_rate
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL
        {account_filter_sql}
        {platform_filter_sql}
    ),
    avg_by_day AS (
        SELECT account_id, day_of_week, AVG(engagement_rate) AS avg_engagement_rate
        FROM base
        GROUP BY account_id, day_of_week
    ),
    ranked AS (
        SELECT
            account_id,
            day_of_week,
            avg_engagement_rate,
            ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY avg_engagement_rate DESC) AS rn
        FROM avg_by_day
    )
    SELECT account_id, day_of_week AS best_day_of_week, avg_engagement_rate
    FROM ranked
    WHERE rn = 1
    ORDER BY account_id
    """
    df_q1 = load_dataframe(q1, params)
    st.metric("Contas avaliadas", format_br(len(df_q1)))
    st.dataframe(format_df(df_q1), use_container_width=True)

with tab2:
    st.subheader("Plataforma com maior proporcao de comentarios negativos por conta")
    q2 = f"""
    WITH perf_accounts AS (
        SELECT DISTINCT account_id, platform, content_id
        FROM mart_content_performance
        WHERE 1=1
        {account_filter_sql}
        {platform_filter_sql}
    ),
    joined AS (
        SELECT p.account_id, s.platform, s.negative_comments, s.total_comments
        FROM mart_content_sentiment s
        JOIN perf_accounts p ON p.content_id = s.content_id AND p.platform = s.platform
    ),
    agg AS (
        SELECT
            account_id,
            platform,
            SUM(negative_comments)::float / NULLIF(SUM(total_comments), 0) AS negative_ratio
        FROM joined
        GROUP BY account_id, platform
    ),
    ranked AS (
        SELECT
            account_id,
            platform,
            negative_ratio,
            ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY negative_ratio DESC) AS rn
        FROM agg
    )
    SELECT
        account_id,
        platform AS worst_platform_by_negative_ratio,
        negative_ratio
    FROM ranked
    WHERE rn = 1
    ORDER BY account_id
    """
    df_q2 = load_dataframe(q2, params)
    st.metric("Contas com plataforma critica", format_br(len(df_q2)))
    st.dataframe(format_df(df_q2), use_container_width=True)

with tab3:
    st.subheader("Top 10 conteudos com maior taxa de engajamento")
    q3 = f"""
    SELECT account_id, platform, content_id, post_date, format, likes, comments_count, reach, views, engagement_rate
    FROM mart_content_performance
    WHERE engagement_rate IS NOT NULL
    {account_filter_sql}
    {platform_filter_sql}
    ORDER BY engagement_rate DESC
    LIMIT 10
    """
    df_q3 = load_dataframe(q3, params)
    st.metric("Maior engagement", format_br(float(df_q3["engagement_rate"].max()) if not df_q3.empty else 0.0, is_pct=True))
    st.dataframe(format_df(df_q3), use_container_width=True)

with tab4:
    st.subheader("Top 3 conteudos por conta (taxa de engajamento)")
    q4 = f"""
    WITH ranked AS (
        SELECT
            account_id,
            platform,
            content_id,
            post_date,
            format,
            likes,
            comments_count,
            reach,
            views,
            engagement_rate,
            ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY engagement_rate DESC) AS rn
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL
        {account_filter_sql}
        {platform_filter_sql}
    )
    SELECT account_id, platform, content_id, post_date, format, likes, comments_count, reach, views, engagement_rate
    FROM ranked
    WHERE rn <= 3
    ORDER BY account_id, rn
    """
    df_q4 = load_dataframe(q4, params)
    st.metric("Linhas retornadas", format_br(len(df_q4)))
    st.dataframe(format_df(df_q4), use_container_width=True)

with tab5:
    st.subheader("5. Para cada conta, qual formato de conteúdo apresenta o melhor desempenho médio de engajamento?")
    q5 = f"""
    WITH avg_format AS (
        SELECT
            account_id,
            format,
            AVG(engagement_rate) AS avg_engagement_rate
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL
        {account_filter_sql}
        {platform_filter_sql}
        GROUP BY account_id, format
    ),
    ranked AS (
        SELECT
            account_id,
            format,
            avg_engagement_rate,
            ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY avg_engagement_rate DESC) AS rn
        FROM avg_format
    )
    SELECT account_id, format AS best_format, avg_engagement_rate
    FROM ranked
    WHERE rn = 1
    ORDER BY account_id
    """
    df_q5 = load_dataframe(q5, params)
    st.metric("Contas com melhor formato", format_br(len(df_q5)))
    st.dataframe(format_df(df_q5), use_container_width=True)
ataframe(format_df(df_q5), use_container_width=True)
