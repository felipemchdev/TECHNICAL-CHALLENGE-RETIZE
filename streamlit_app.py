import math
import os
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ──────────────────────────────────────────────
# SKEUOMORPHIC DARK THEME
# ──────────────────────────────────────────────
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0f0f0f;
    color: #e2e2e2;
}

/* Main app background */
.stApp {
    background: radial-gradient(ellipse at top, #1a1a2e 0%, #0f0f0f 60%);
}

/* Skeuomorphic card panels */
div[data-testid="stVerticalBlock"] > div {
    border-radius: 12px;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    background: linear-gradient(135deg, #1c1c1c, #252525);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 9px;
    color: #888;
    font-weight: 500;
    font-size: 0.82rem;
    padding: 8px 16px;
    transition: all 0.2s ease;
    border: none;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7c3aed, #5b21b6) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.5), inset 0 1px 0 rgba(255,255,255,0.15);
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(145deg, #1e1e2e, #16161e);
    border: 1px solid #2a2a3e;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
}

div[data-testid="metric-container"] label {
    color: #888 !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #a78bfa !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: linear-gradient(145deg, #1e1e2e, #16161e) !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #e2e2e2 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.4) !important;
}

/* Text inputs in sidebar */
input[type="text"], input[type="password"] {
    background: linear-gradient(145deg, #1a1a2a, #111118) !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #e2e2e2 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.5) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #5b21b6);
    border: none;
    border-radius: 8px;
    color: #fff;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 20px;
    box-shadow: 0 3px 10px rgba(124,58,237,0.4), inset 0 1px 0 rgba(255,255,255,0.15);
    transition: all 0.2s ease;
    cursor: pointer;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6, #6d28d9);
    box-shadow: 0 4px 16px rgba(124,58,237,0.6);
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
    box-shadow: 0 2px 6px rgba(124,58,237,0.3);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141420 0%, #0f0f18 100%);
    border-right: 1px solid #2a2a3e;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a78bfa;
}

/* Header banner */
.analytics-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
    border: 1px solid #4338ca;
    border-radius: 14px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 6px 24px rgba(67,56,202,0.3), inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative;
    overflow: hidden;
}

.analytics-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 60%);
    pointer-events: none;
}

.analytics-header h1 {
    color: #fff;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0 0 4px 0;
    letter-spacing: -0.02em;
}

.analytics-header p {
    color: #a78bfa;
    font-size: 0.85rem;
    margin: 0;
    font-weight: 400;
}

/* Section cards */
.card-section {
    background: linear-gradient(145deg, #1a1a2a, #141420);
    border: 1px solid #2a2a3e;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
}

.card-section h3 {
    color: #c4b5fd;
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0 0 12px 0;
    letter-spacing: 0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Status badges */
.badge-connected {
    display: inline-block;
    background: linear-gradient(135deg, #065f46, #047857);
    border: 1px solid #10b981;
    color: #6ee7b7;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f0f0f; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #555; }

/* Subheader override */
h2, h3 { color: #c4b5fd !important; }
.stCaption { color: #666 !important; font-size: 0.75rem !important; }
</style>
"""

# ──────────────────────────────────────────────
# DB HELPERS
# ──────────────────────────────────────────────
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


@st.cache_resource
def get_engine(db_url: str):
    return create_engine(db_url, pool_size=2, max_overflow=2)


def _build_url(cfg: dict) -> str:
    user = quote_plus(cfg["user"])
    password = quote_plus(cfg["password"])
    db_name = quote_plus(cfg["db"])
    return f"postgresql+pg8000://{user}:{password}@{cfg['host']}:{cfg['port']}/{db_name}"


def load_dataframe(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    base_cfg = _db_config(
        st.session_state["db_host"], st.session_state["db_port"],
        st.session_state["db_user"], st.session_state["db_password"],
        st.session_state["db_name"],
    )
    dotenv_cfg = _db_config(
        st.session_state["env_host"], st.session_state["env_port"],
        st.session_state["env_user"], st.session_state["env_password"],
        st.session_state["env_db"],
    )
    candidates = [base_cfg]
    if dotenv_cfg not in candidates:
        candidates.append(dotenv_cfg)
    for c in [base_cfg, dotenv_cfg]:
        if c["host"] in ("localhost", "127.0.0.1"):
            for p in ("5543", "5433", "5432"):
                alt = dict(c, port=p)
                if alt not in candidates:
                    candidates.append(alt)

    last_exc: Optional[Exception] = None
    for cfg in candidates:
        try:
            engine = get_engine(_build_url(cfg))
            with engine.begin() as conn:
                return pd.read_sql(text(sql), conn, params=params or {})
        except Exception as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError("Falha inesperada ao consultar o banco.")


def check_connection() -> tuple[bool, str]:
    try:
        load_dataframe("SELECT 1 AS ok")
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ──────────────────────────────────────────────
# FORMATTING
# ──────────────────────────────────────────────
def format_br(val, is_pct: bool = False) -> str:
    if isinstance(val, (int, float)):
        try:
            fval = float(val)
        except (ValueError, TypeError):
            return str(val)
        if math.isnan(fval):
            return "-"
        if is_pct:
            s = f"{fval * 100:,.2f}%"
        else:
            s = f"{int(fval):,}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return str(val)


def format_df(df: pd.DataFrame):
    rate_cols = ["engagement_rate", "avg_engagement_rate", "negative_ratio"]
    count_cols = ["likes", "comments_count", "reach", "views", "total_comments", "negative_comments", "views_or_reach"]

    for col in df.columns:
        if col == "id" or col.endswith("_id") or col == "item_id":
            df[col] = df[col].astype(str)
        elif col in count_cols or col in rate_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    ALL_TABLES = {t for tables in LAYER_OPTIONS.values() for t in tables}

    format_dict = {}
    for col in df.columns:
        if col in rate_cols:
            format_dict[col] = "{:.2%}"
        elif col in count_cols:
            format_dict[col] = "{:,.0f}"

    if format_dict:
        return df.style.format(formatter=format_dict, decimal=",", thousands=".", precision=0, na_rep="-")
    return df.style.format(decimal=",", thousands=".", precision=0, na_rep="-")


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────
LAYER_OPTIONS = {
    "raw": ["raw_instagram_media", "raw_instagram_media_insights", "raw_instagram_comments", "raw_tiktok_posts", "raw_tiktok_comments"],
    "silver": ["silver_instagram_content", "silver_tiktok_content", "silver_comments"],
    "gold": ["mart_content_performance", "mart_content_sentiment"],
}
ALL_TABLES = {t for tables in LAYER_OPTIONS.values() for t in tables}

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="analytics Challenge · Social Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(THEME_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────
dotenv_values = _load_dotenv()
if "db_host" not in st.session_state:
    for key, env_key, default in [
        ("env_host", "POSTGRES_HOST", "localhost"),
        ("env_port", "POSTGRES_PORT", "5432"),
        ("env_user", "POSTGRES_USER", "techtest"),
        ("env_password", "POSTGRES_PASSWORD", "123"),
        ("env_db", "POSTGRES_DB", "views_db"),
    ]:
        st.session_state[key] = dotenv_values.get(env_key, os.getenv(env_key, default))
    st.session_state["db_host"] = st.session_state["env_host"]
    st.session_state["db_port"] = st.session_state["env_port"]
    st.session_state["db_user"] = st.session_state["env_user"]
    st.session_state["db_password"] = st.session_state["env_password"]
    st.session_state["db_name"] = st.session_state["env_db"]

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Conexão")
    if st.button("↺ Resetar com .env", use_container_width=True):
        st.session_state["db_host"] = st.session_state["env_host"]
        st.session_state["db_port"] = st.session_state["env_port"]
        st.session_state["db_user"] = st.session_state["env_user"]
        st.session_state["db_password"] = st.session_state["env_password"]
        st.session_state["db_name"] = st.session_state["env_db"]
        st.rerun()
    st.session_state["db_host"] = st.text_input("Host", value=st.session_state["db_host"])
    st.session_state["db_port"] = st.text_input("Porta", value=st.session_state["db_port"])
    st.session_state["db_name"] = st.text_input("Database", value=st.session_state["db_name"])
    st.session_state["db_user"] = st.text_input("Usuário", value=st.session_state["db_user"])
    st.session_state["db_password"] = st.text_input("Senha", value=st.session_state["db_password"], type="password")
    st.caption("Fora do Docker: localhost. Dentro: postgres.")
    st.divider()
    st.markdown("## 🔍 Filtros")

# ──────────────────────────────────────────────
# HEADER BANNER
# ──────────────────────────────────────────────
st.markdown("""
<div class="analytics-header">
  <h1>📊 analytics · Social Analytics</h1>
  <p>Pipeline analítico · Instagram & TikTok · Medallion Architecture</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONNECTION CHECK
# ──────────────────────────────────────────────
is_connected, conn_error = check_connection()
if not is_connected:
    st.error("❌ Não foi possível conectar ao PostgreSQL.")
    st.markdown(
        "Verifique se o banco está no ar:\n"
        "- `POSTGRES_HOST=localhost`\n"
        "- `POSTGRES_PORT=5433`\n"
        "- `POSTGRES_DB=views_db`\n\n"
        "Suba com `docker compose up -d`."
    )
    st.code(conn_error)
    st.stop()

st.markdown('<span class="badge-connected">● Connected</span>', unsafe_allow_html=True)
st.write("")

try:
    load_dataframe("SELECT 1 FROM mart_content_performance LIMIT 1")
except Exception as exc:
    st.warning("⚠️ As tabelas analíticas ainda não foram criadas.")
    st.markdown(
        "Execute o pipeline via **Airflow** em [http://localhost:8080](http://localhost:8080), "
        "ou diretamente:\n\n"
        "```bash\n"
        "docker compose exec -T airflow bash -lc \"cd /opt/project && python src/load_data.py\"\n"
        "docker compose exec -T airflow bash -lc \"cd /opt/project/analytics_dbt && dbt run --profiles-dir /opt/project/analytics_dbt\"\n"
        "```"
    )
    st.code(str(exc))
    st.stop()

# ──────────────────────────────────────────────
# SIDEBAR FILTERS (after connection confirmed)
# ──────────────────────────────────────────────
accounts_df = load_dataframe("SELECT DISTINCT account_id FROM mart_content_performance ORDER BY account_id")
account_options = ["(todas)"] + accounts_df["account_id"].dropna().astype(str).tolist()
selected_account = st.sidebar.selectbox("Conta", account_options, index=0)
selected_platform = st.sidebar.selectbox("Plataforma", ["(todas)", "instagram", "tiktok"], index=0)

params: dict = {}
account_filter_sql = ""
platform_filter_sql = ""
if selected_account != "(todas)":
    account_filter_sql = " AND account_id = :account_id"
    params["account_id"] = selected_account
if selected_platform != "(todas)":
    platform_filter_sql = " AND platform = :platform"
    params["platform"] = selected_platform

# ──────────────────────────────────────────────
# TABLE EXPLORER
# ──────────────────────────────────────────────
st.markdown('<div class="card-section"><h3>🗄️ Explorador de Camadas</h3></div>', unsafe_allow_html=True)
col_layer, col_table = st.columns([1, 2])
with col_layer:
    selected_layer = st.selectbox("Camada", list(LAYER_OPTIONS.keys()), index=2)
with col_table:
    selected_table = st.selectbox("Tabela", LAYER_OPTIONS[selected_layer], index=0)

if selected_table not in ALL_TABLES:
    st.error("Tabela inválida.")
    st.stop()

st.caption(f"Exibindo até 10.000 linhas · {selected_table}")
st.dataframe(format_df(load_dataframe(f'SELECT * FROM "{selected_table}" LIMIT 10000')), use_container_width=True)

st.divider()
st.markdown("## 📈 Perguntas de Negócio")

# ──────────────────────────────────────────────
# BUSINESS QUERIES — TABS
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Melhor Dia",
    "😠 Plataforma Negativa",
    "🏆 Top 10 Conteúdos",
    "🎯 Top 3 por Conta",
    "🎬 Melhor Formato",
])

with tab1:
    st.subheader("Melhor dia da semana por conta")
    q1 = f"""
    WITH base AS (
        SELECT account_id, day_of_week, engagement_rate
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL {account_filter_sql} {platform_filter_sql}
    ),
    avg_by_day AS (
        SELECT account_id, day_of_week, AVG(engagement_rate) AS avg_engagement_rate
        FROM base GROUP BY account_id, day_of_week
    ),
    ranked AS (
        SELECT account_id, day_of_week, avg_engagement_rate,
               ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY avg_engagement_rate DESC) AS rn
        FROM avg_by_day
    )
    SELECT account_id, day_of_week AS best_day_of_week, avg_engagement_rate
    FROM ranked WHERE rn = 1 ORDER BY account_id
    """
    df_q1 = load_dataframe(q1, params)
    st.metric("Contas avaliadas", format_br(len(df_q1)))
    st.dataframe(format_df(df_q1), use_container_width=True)

with tab2:
    st.subheader("Plataforma com maior proporção de comentários negativos")
    q2 = f"""
    WITH perf_accounts AS (
        SELECT DISTINCT account_id, platform, content_id FROM mart_content_performance
        WHERE 1=1 {account_filter_sql} {platform_filter_sql}
    ),
    joined AS (
        SELECT p.account_id, s.platform, s.negative_comments, s.total_comments
        FROM mart_content_sentiment s
        JOIN perf_accounts p ON p.content_id = s.content_id AND p.platform = s.platform
    ),
    agg AS (
        SELECT account_id, platform,
               SUM(negative_comments)::float / NULLIF(SUM(total_comments), 0) AS negative_ratio
        FROM joined GROUP BY account_id, platform
    ),
    ranked AS (
        SELECT account_id, platform, negative_ratio,
               ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY negative_ratio DESC) AS rn
        FROM agg
    )
    SELECT account_id, platform AS worst_platform_by_negative_ratio, negative_ratio
    FROM ranked WHERE rn = 1 ORDER BY account_id
    """
    df_q2 = load_dataframe(q2, params)
    st.metric("Contas com plataforma crítica", format_br(len(df_q2)))
    st.dataframe(format_df(df_q2), use_container_width=True)

with tab3:
    st.subheader("Top 10 conteúdos com maior taxa de engajamento")
    q3 = f"""
    SELECT account_id, platform, content_id, post_date, format,
           likes, comments_count, reach, views, engagement_rate
    FROM mart_content_performance
    WHERE engagement_rate IS NOT NULL {account_filter_sql} {platform_filter_sql}
    ORDER BY engagement_rate DESC LIMIT 10
    """
    df_q3 = load_dataframe(q3, params)
    st.metric("Maior engajamento", format_br(float(df_q3["engagement_rate"].max()) if not df_q3.empty else 0.0, is_pct=True))
    st.dataframe(format_df(df_q3), use_container_width=True)

with tab4:
    st.subheader("Top 3 conteúdos por conta")
    q4 = f"""
    WITH ranked AS (
        SELECT account_id, platform, content_id, post_date, format,
               likes, comments_count, reach, views, engagement_rate,
               ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY engagement_rate DESC) AS rn
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL {account_filter_sql} {platform_filter_sql}
    )
    SELECT account_id, platform, content_id, post_date, format,
           likes, comments_count, reach, views, engagement_rate
    FROM ranked WHERE rn <= 3 ORDER BY account_id, rn
    """
    df_q4 = load_dataframe(q4, params)
    st.metric("Linhas retornadas", format_br(len(df_q4)))
    st.dataframe(format_df(df_q4), use_container_width=True)

with tab5:
    st.subheader("Melhor formato por conta")
    q5 = f"""
    WITH avg_format AS (
        SELECT account_id, format, AVG(engagement_rate) AS avg_engagement_rate
        FROM mart_content_performance
        WHERE engagement_rate IS NOT NULL {account_filter_sql} {platform_filter_sql}
        GROUP BY account_id, format
    ),
    ranked AS (
        SELECT account_id, format, avg_engagement_rate,
               ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY avg_engagement_rate DESC) AS rn
        FROM avg_format
    )
    SELECT account_id, format AS best_format, avg_engagement_rate
    FROM ranked WHERE rn = 1 ORDER BY account_id
    """
    df_q5 = load_dataframe(q5, params)
    st.metric("Contas com melhor formato", format_br(len(df_q5)))
    st.dataframe(format_df(df_q5), use_container_width=True)
