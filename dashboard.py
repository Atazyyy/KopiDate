"""
KopiDate — Operations Dashboard
PT KopiXYZ Indonesia (dummy company for portfolio)

Run: streamlit run dashboard.py
"""

from __future__ import annotations

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DB_PATH = Path(__file__).parent / "pipeline" / "KopiDate.duckdb"

# ─────────────────────────────────────────────────────────────────────────────
# Theme tokens — semantic, mapped per mode.
# Light and dark are checked independently (per WCAG: >=4.5:1 for normal text).
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "light": {
        "bg": "#FAF7F2",
        "surface": "#FFFFFF",
        "surface2": "#F1EAE1",
        "border": "#E0D4C6",
        "text": "#2C1810",
        "text_muted": "#6B584A",
        "accent": "#92400E",
        "accent_soft": "#B45309",
        "chart_text": "#2C1810",
        "grid": "#E8DFD4",
        "series": ["#92400E", "#B45309", "#C8814A", "#6B4423", "#D9A066"],
        "dashes": ["solid", "dash", "dot", "dashdot", "longdash"],
    },
    "dark": {
        "bg": "#14110F",
        "surface": "#1F1A16",
        "surface2": "#2A231E",
        "border": "#3A312B",
        "text": "#EDE4DA",
        "text_muted": "#A8998A",
        "accent": "#D9A066",
        "accent_soft": "#C8814A",
        "chart_text": "#EDE4DA",
        "grid": "#2E2620",
        "series": ["#D9A066", "#B8814A", "#8B5E3C", "#E3B583", "#A06D45"],
        "dashes": ["solid", "dash", "dot", "dashdot", "longdash"],
    },
}


def current_mode() -> str:
    """Detect Streamlit's active theme at runtime (falls back to dark)."""
    try:
        t = st.context.theme
        if t and getattr(t, "type", None):
            return "light" if t.type == "light" else "dark"
    except Exception:
        pass
    return "dark"


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    orders = con.execute("SELECT * FROM orders").fetchdf()
    menu = con.execute("SELECT * FROM menu").fetchdf()
    con.close()
    return orders, menu


def rp(n) -> str:
    """Format Rupiah with tabular-friendly thousands separator."""
    return f"Rp {int(n):,}".replace(",", ".")


# ─────────────────────────────────────────────────────────────────────────────
# Icons — inline SVG (no emoji as icons per design rules)
# ─────────────────────────────────────────────────────────────────────────────
SVG = {
    "coffee": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/>'
        '<path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8Z"/>'
        '<line x1="6" y1="2" x2="6" y2="4"/><line x1="10" y1="2" x2="10" y2="4"/>'
        '<line x1="14" y1="2" x2="14" y2="4"/></svg>'
    ),
    "revenue": (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/>'
        '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'
    ),
    "filter": (
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>'
        '</svg>'
    ),
    "check": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
        'stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# CSS — token-driven, theme-aware
# ─────────────────────────────────────────────────────────────────────────────
def inject_css(t: dict) -> None:
    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

    :root {{
        --bg: {t['bg']};
        --surface: {t['surface']};
        --surface2: {t['surface2']};
        --border: {t['border']};
        --text: {t['text']};
        --text-muted: {t['text_muted']};
        --accent: {t['accent']};
        --accent-soft: {t['accent_soft']};
    }}

    html, body, [class*="css"] {{ font-family: 'Fira Sans', system-ui, sans-serif; }}

    /* Page background — override Streamlit defaults */
    .stApp, [data-testid="stAppViewContainer"], .reportView-container,
    [data-testid="stMainBlockContainer"], [data-testid="stMain"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }}
    [data-testid="stHeader"] {{ background-color: var(--bg) !important; }}
    [data-testid="stToolbar"] {{ right: 0; }}
    footer, [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}

    /* ── Header ─────────────────────────────────────────────────────── */
    .kopi-header {{
        background: linear-gradient(135deg, #1A1008 0%, #2C1810 55%, #3D2314 100%);
        color: #F5E6D3;
        padding: 18px 26px;
        border-radius: 0 0 14px 14px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 14px;
        border-bottom: 1px solid #4A3223;
    }}
    .kopi-header .icon {{
        color: #D9A066; display: flex; align-items: center;
        width: 42px; height: 42px; border-radius: 10px;
        background: rgba(217,160,102,0.14);
        align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .kopi-header h1 {{
        margin: 0; font-size: 1.45rem; font-weight: 700;
        color: #F5E6D3; letter-spacing: -0.3px; line-height: 1.2;
    }}
    .kopi-header .sub {{
        margin: 3px 0 0; font-size: 0.8rem; color: #C08A5E;
        font-family: 'Fira Code', monospace;
    }}

    /* ── KPI cards ──────────────────────────────────────────────────── */
    div[data-testid="stMetric"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 14px 10px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: border-color 180ms ease, transform 180ms ease;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: var(--accent);
        transform: translateY(-1px);
    }}
    [data-testid="stMetricLabel"] {{
        color: var(--text-muted) !important;
        font-size: 0.68rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--accent) !important;
        font-size: 1.28rem !important;
        font-weight: 600 !important;
        font-family: 'Fira Code', monospace;
        font-variant-numeric: tabular-nums;
    }}

    /* ── Cards ──────────────────────────────────────────────────────── */
    .kopi-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 16px;
        height: 100%;
    }}
    .kopi-card-title {{
        color: var(--text-muted);
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 12px;
        display: flex; align-items: center; gap: 6px;
    }}

    /* ── Section title ──────────────────────────────────────────────── */
    .kopi-section {{
        color: var(--text);
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding-bottom: 6px;
        margin-bottom: 10px;
        border-bottom: 1px solid var(--border);
    }}

    /* ── Data table ─────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {{
        background: var(--surface) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
    }}
    [data-testid="stDataFrame"] th {{
        background: var(--surface2) !important;
        color: var(--text-muted) !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    [data-testid="stDataFrame"] td {{
        background: var(--surface) !important;
        color: var(--text) !important;
        font-size: 0.82rem !important;
        font-family: 'Fira Code', monospace;
        font-variant-numeric: tabular-nums;
    }}
    [data-testid="stDataFrame"] tr:hover td {{
        background: var(--surface2) !important;
    }}

    /* ── Sidebar ────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: var(--surface) !important;
        border-right: 1px solid var(--border);
    }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{ color: var(--text) !important; }}
    [data-testid="stSidebar"] label {{ color: var(--text-muted) !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 1rem; }}

    /* ── Filter chips (multiselect) ─────────────────────────────────── */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
        color: var(--text) !important; font-size: 0.78rem;
    }}

    /* ── Misc ───────────────────────────────────────────────────────── */
    .st-caption, [data-testid="stCaptionContainer"] p {{
        color: var(--text-muted) !important; font-size: 0.75rem !important;
    }}
    hr {{ border-color: var(--border) !important; }}

    /* Focus visibility (a11y) */
    a:focus-visible, button:focus-visible, [tabindex]:focus-visible {{
        outline: 2px solid var(--accent) !important;
        outline-offset: 2px !important;
    }}

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {{
        * {{ transition: none !important; animation: none !important; }}
    }}

    /* Plotly container background must be transparent in both modes */
    .js-plotly-plot .plotly .main-svg {{ background: transparent !important; }}
    .plot-container {{ background: transparent !important; }}
    </style>
    """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chart helpers
# ─────────────────────────────────────────────────────────────────────────────
def style_fig(fig: go.Figure, t: dict, height: int = 300, showlegend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=34, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["chart_text"], size=11, family="Fira Sans, sans-serif"),
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="left",
            x=0,
            font=dict(color=t["text_muted"], size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.97),
        hoverlabel=dict(
            bgcolor=t["surface2"],
            bordercolor=t["border"],
            font=dict(color=t["text"], size=11, family="Fira Code, monospace"),
        ),
    )
    fig.update_xaxes(
        gridcolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text_muted"], size=10),
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text_muted"], size=10),
        tickprefix="Rp ",
        zeroline=False,
    )
    return fig


def cat_bar(df: pd.DataFrame, x: str, y: str, t: dict, title: str, height: int = 300) -> go.Figure:
    """Horizontal bar — best for category comparison (label readability)."""
    fig = px.bar(
        df, x=y, y=x, orientation="h",
        text=[rp(v) for v in df[y]],
        color=x,
        color_discrete_sequence=t["series"],
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickprefix="", title="")
    fig.update_yaxes(tickprefix="", title="")
    fig.update_traces(
        textposition="outside",
        textfont=dict(color=t["chart_text"], size=10, family="Fira Code, monospace"),
        marker=dict(line=dict(width=0)),
        hovertemplate=f"<b>%{{y}}</b><br>%{{x}}<extra></extra>",
    )
    fig.update_layout(title=dict(text=title, font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.98))
    return style_fig(fig, t, height=height, showlegend=False)


# ─────────────────────────────────────────────────────────────────────────────
# Sections
# ─────────────────────────────────────────────────────────────────────────────
def header(t: dict) -> None:
    st.markdown(
        f"""
    <div class="kopi-header">
        <div class="icon">{SVG['coffee']}</div>
        <div>
            <h1>KopiDate — Operations Dashboard</h1>
            <p class="sub">PT KopiXYZ Indonesia &nbsp;·&nbsp; Jan–Feb 2024 &nbsp;·&nbsp; 3 outlets &nbsp;·&nbsp; DuckDB warehouse</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def kpi_row(orders: pd.DataFrame, t: dict) -> None:
    rev = int(orders["revenue_idr"].sum())
    n = len(orders)
    avg = int(orders["revenue_idr"].mean())
    peak = int(orders.groupby("order_date")["revenue_idr"].sum().max())
    top_pay = orders["payment_method"].mode()[0]
    top_menu = orders.groupby("menu_item")["revenue_idr"].sum().idxmax()

    r1 = st.columns(4, gap="small")
    r1[0].metric("Total Revenue", rp(rev))
    r1[1].metric("Total Orders", f"{n:,}".replace(",", "."))
    r1[2].metric("Avg Ticket", rp(avg))
    r1[3].metric("Outlets", orders["outlet"].nunique())

    r2 = st.columns(4, gap="small")
    r2[0].metric("Peak Day", rp(peak))
    r2[1].metric("Top Payment", top_pay)
    r2[2].metric("Top Menu", top_menu)
    r2[3].metric("Avg Cup Price", rp(int(orders["price_idr"].mean())))


def sidebar_filters(orders: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    st.sidebar.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:8px;color:var(--accent);margin-bottom:4px;">
        {SVG['filter']}<span style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.7px;color:var(--text);">Filters</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    outlets = sorted(orders["outlet"].unique())
    sel_outlets = st.sidebar.multiselect("Outlet", outlets, default=outlets)

    categories = sorted(orders["menu_item"].unique())
    sel_menu = st.sidebar.multiselect(
        "Menu", categories, default=categories, help="Filter by menu item"
    )

    payments = sorted(orders["payment_method"].unique())
    sel_pay = st.sidebar.multiselect("Payment", payments, default=payments)

    min_d = orders["order_date"].min()
    max_d = orders["order_date"].max()
    date_range = st.sidebar.date_input(
        "Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
    <div style="color:var(--text-muted);font-size:0.72rem;line-height:1.6;">
        <div style="color:var(--text);font-weight:600;margin-bottom:6px;">Pipeline</div>
        3 sources → 10-step cleansing → DuckDB<br>
        <span style="color:var(--accent);">{SVG['check']} 464 rows in</span><br>
        <span style="color:var(--accent);">{SVG['check']} 364 rows out</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    f = orders[
        orders["outlet"].isin(sel_outlets)
        & orders["menu_item"].isin(sel_menu)
        & orders["payment_method"].isin(sel_pay)
    ]
    if len(date_range) == 2:
        # DuckDB returns datetime64; date_input returns datetime.date — normalise both
        lo, hi = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        f = f[(f["order_date"] >= lo) & (f["order_date"] <= hi)]
    return f.reset_index(drop=True), {
        "outlets": sel_outlets,
        "menu": sel_menu,
        "payment": sel_pay,
        "dates": date_range,
    }


def revenue_by_outlet(orders: pd.DataFrame, t: dict) -> None:
    rev = (
        orders.groupby("outlet")
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=True)
    )
    fig = px.bar(
        rev, x="revenue", y="outlet", orientation="h",
        text=[rp(v) for v in rev["revenue"]],
        color="outlet",
        color_discrete_sequence=t["series"],
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickprefix="Rp ", title="")
    fig.update_yaxes(tickprefix="", title="")
    fig.update_traces(
        textposition="outside",
        textfont=dict(color=t["chart_text"], size=11, family="Fira Code, monospace"),
        marker=dict(line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Revenue: Rp %{x:,.0f}<extra></extra>",
    )
    fig.update_layout(title=dict(text="Revenue per Outlet", font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.98))
    st.plotly_chart(style_fig(fig, t, height=260, showlegend=False), width="stretch",
                     config={"displayModeBar": False})


def top_menu_chart(orders: pd.DataFrame, t: dict) -> None:
    top = (
        orders.groupby("menu_item")
        .agg(revenue=("revenue_idr", "sum"), cups=("qty", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=True)
        .tail(5)
    )
    fig = cat_bar(top, "menu_item", "revenue", t, "Top 5 Menu by Revenue", height=260)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def payment_mix(orders: pd.DataFrame, t: dict) -> None:
    mix = (
        orders.groupby("payment_method")
        .agg(n=("order_id", "count"), revenue=("revenue_idr", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
    )
    mix["pct"] = (mix["n"] / mix["n"].sum() * 100).round(1)

    fig = px.pie(
        mix, names="payment_method", values="n",
        hole=0.55,
        color="payment_method",
        color_discrete_sequence=t["series"][: len(mix)],
    )
    fig.update_traces(
        textposition="outside",
        textinfo="percent",
        textfont=dict(color=t["chart_text"], size=10, family="Fira Code, monospace"),
        marker=dict(line=dict(width=0)),
        hovertemplate="<b>%{label}</b><br>%{value} orders<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        height=260,
        margin=dict(l=8, r=8, t=34, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["chart_text"], size=11),
        showlegend=True,
        legend=dict(
            orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
            font=dict(color=t["text_muted"], size=10), bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(text="Payment Method Mix", font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.98),
        hoverlabel=dict(bgcolor=t["surface2"], bordercolor=t["border"],
                        font=dict(color=t["text"], size=11)),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def daily_trend(orders: pd.DataFrame, t: dict) -> None:
    """Line chart with distinct dash styles per series — never color alone."""
    daily = (
        orders.groupby(["order_date", "outlet"])
        .agg(revenue=("revenue_idr", "sum"))
        .reset_index()
        .sort_values("order_date")
    )
    outlets = sorted(daily["outlet"].unique())

    fig = go.Figure()
    for i, outlet in enumerate(outlets):
        d = daily[daily["outlet"] == outlet]
        fig.add_trace(go.Scatter(
            x=d["order_date"], y=d["revenue"],
            name=outlet,
            mode="lines+markers",
            line=dict(
                color=t["series"][i % len(t["series"])],
                width=2.2,
                dash=t["dashes"][i % len(t["dashes"])],
            ),
            marker=dict(size=5, symbol=["circle", "square", "triangle-up", "diamond", "x"][i % 5]),
            hovertemplate=f"<b>{outlet}</b><br>%{{x|%d %b %Y}}<br>Rp %{{y:,.0f}}<extra></extra>",
        ))

    fig.update_xaxes(title="", tickformat="%d %b")
    fig.update_yaxes(title="")
    fig.update_layout(title=dict(text="Daily Revenue Trend", font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.97))
    st.plotly_chart(style_fig(fig, t, height=290), width="stretch",
                     config={"displayModeBar": False})


def shift_chart(orders: pd.DataFrame, t: dict) -> None:
    shift = (
        orders[orders["shift"].notna()]
        .groupby(["shift", "outlet"])
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
    order_map = {"Pagi": 0, "Siang": 1, "Malam": 2}
    shift["ord"] = shift["shift"].map(order_map)
    shift = shift.sort_values(["ord", "outlet"])

    fig = px.bar(
        shift, x="shift", y="revenue", color="outlet",
        barmode="group",
        color_discrete_sequence=t["series"],
        category_orders={"shift": ["Pagi", "Siang", "Malam"]},
    )
    fig.update_traces(
        marker=dict(line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    fig.update_layout(
        title=dict(text="Revenue by Shift", font=dict(color=t["chart_text"], size=13), x=0, xanchor="left", y=0.98),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    font=dict(color=t["text_muted"], size=10), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(style_fig(fig, t, height=260), width="stretch",
                     config={"displayModeBar": False})


def category_chart(orders: pd.DataFrame, menu: pd.DataFrame, t: dict) -> None:
    cat = (
        orders.groupby("menu_item")["revenue_idr"].sum().reset_index()
        .merge(menu[["menu_item", "category"]], on="menu_item")
        .groupby("category")
        .agg(revenue=("revenue_idr", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=True)
    )
    fig = cat_bar(cat, "category", "revenue", t, "Revenue by Category", height=250)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def cleansing_panel(t: dict) -> None:
    st.markdown('<div class="kopi-section">Pipeline Health</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown(
            f"""
        <div class="kopi-card">
            <div class="kopi-card-title">Cleansing Report</div>
            <div style="display:grid;grid-template-columns:1fr auto;gap:6px 12px;font-size:0.82rem;color:var(--text);">
                <span style="color:var(--text-muted);">Input rows</span><span style="font-family:'Fira Code',monospace;">464</span>
                <span style="color:var(--text-muted);">Output rows</span><span style="font-family:'Fira Code',monospace;color:var(--accent);">364</span>
                <span style="color:var(--text-muted);">Dropped (duplicate)</span><span style="font-family:'Fira Code',monospace;">84</span>
                <span style="color:var(--text-muted);">Dropped (unknown payment)</span><span style="font-family:'Fira Code',monospace;">10</span>
                <span style="color:var(--text-muted);">Dropped (invalid qty)</span><span style="font-family:'Fira Code',monospace;">6</span>
                <span style="color:var(--text-muted);">Price recomputed</span><span style="font-family:'Fira Code',monospace;">9</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
        <div class="kopi-card">
            <div class="kopi-card-title">Data Quality</div>
            <div style="display:grid;grid-template-columns:1fr auto;gap:6px 12px;font-size:0.82rem;color:var(--text);">
                <span style="color:var(--text-muted);">Unknown outlet</span><span style="font-family:'Fira Code',monospace;color:var(--accent);">0</span>
                <span style="color:var(--text-muted);">Unknown size</span><span style="font-family:'Fira Code',monospace;color:var(--accent);">0</span>
                <span style="color:var(--text-muted);">Unknown menu</span><span style="font-family:'Fira Code',monospace;color:var(--accent);">0</span>
                <span style="color:var(--text-muted);">Date parse success</span><span style="font-family:'Fira Code',monospace;color:var(--accent);">100%</span>
                <span style="color:var(--text-muted);">NULL shift (expected)</span><span style="font-family:'Fira Code',monospace;">80</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="KopiDate Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    mode = current_mode()
    t = THEMES[mode]
    inject_css(t)

    if not DB_PATH.exists():
        st.error("Database not found. Run: `python pipeline/pipeline.py`")
        st.stop()

    try:
        orders, menu = load_data()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    header(t)

    filtered, _ = sidebar_filters(orders)

    if filtered.empty:
        st.warning("No data matches the current filters.")
        return

    kpi_row(filtered, t)
    st.markdown("")

    # Row 1 — trend spans full width (primary insight)
    daily_trend(filtered, t)

    # Row 2 — outlet + top menu
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown('<div class="kopi-section">Outlet Performance</div>', unsafe_allow_html=True)
        revenue_by_outlet(filtered, t)
    with c2:
        st.markdown('<div class="kopi-section">Product Performance</div>', unsafe_allow_html=True)
        top_menu_chart(filtered, t)

    # Row 3 — payment + shift
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        st.markdown('<div class="kopi-section">Payment Mix</div>', unsafe_allow_html=True)
        payment_mix(filtered, t)
    with c4:
        st.markdown('<div class="kopi-section">Shift Performance</div>', unsafe_allow_html=True)
        shift_chart(filtered, t)

    # Row 4 — category + health
    c5, c6 = st.columns(2, gap="medium")
    with c5:
        st.markdown('<div class="kopi-section">Category Mix</div>', unsafe_allow_html=True)
        category_chart(filtered, menu, t)
    with c6:
        cleansing_panel(t)

    st.markdown("")
    st.caption(
        "KopiDate · data source: pipeline/KopiDate.duckdb · "
        "built with Streamlit + Plotly + DuckDB · data is synthetic"
    )


if __name__ == "__main__":
    main()
