"""
Dashboard untuk KopiDate — PT KopiXYZ Indonesia

Menjalankan: streamlit run dashboard.py
Buka: http://localhost:8501
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent / "pipeline" / "KopiDate.duckdb"

# ── Palette ────────────────────────────────────────────────────────────────────
BROWN_DARK  = "#3D2314"
BROWN_MED   = "#6F4E37"
BROWN_LIGHT = "#A0724A"
CREAM       = "#F5F0EB"
CREAM_DARK  = "#E8DFD5"
ORANGE_ACC  = "#D4852F"
WHITE       = "#FFFFFF"


def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    orders = con.execute("SELECT * FROM orders").fetchdf()
    menu   = con.execute("SELECT * FROM menu").fetchdf()
    con.close()
    return orders, menu


def fmt_rp(n):
    return f"Rp {int(n):,}".replace(",", ".")


# ── KPI Cards ─────────────────────────────────────────────────────────────────
def kpi_cards(orders):
    rev     = int(orders["revenue_idr"].sum())
    n_order = len(orders)
    avg_t    = int(orders["revenue_idr"].mean())
    n_outlet = orders["outlet"].nunique()
    n_days   = orders["order_date"].nunique()
    peak_rev = int(orders.groupby("order_date")["revenue_idr"].sum().max())
    top_pay  = orders["payment_method"].mode()[0]

    row1 = st.columns([1, 1, 1, 1])
    with row1[0]: st.metric("Total Revenue", fmt_rp(rev))
    with row1[1]: st.metric("Total Orders", f"{n_order:,}".replace(",", "."))
    with row1[2]: st.metric("Avg Ticket", fmt_rp(avg_t))
    with row1[3]: st.metric("Outlets", n_outlet)

    row2 = st.columns([1, 1, 1, 1])
    with row2[0]: st.metric("Days Active", n_days)
    with row2[1]: st.metric("Peak Daily Rev", fmt_rp(peak_rev))
    with row2[2]: st.metric("Top Payment", top_pay)
    with row2[3]: st.metric("Avg Cup Price", fmt_rp(int(orders["price_idr"].mean())))


# ── Revenue by Outlet ──────────────────────────────────────────────────────────
def revenue_by_outlet(orders):
    rev = (
        orders.groupby("outlet")
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    rev["avg_ticket"] = rev["revenue"] / rev["orders"]
    colors = [BROWN_DARK, BROWN_MED, BROWN_LIGHT]

    fig = px.bar(
        rev, x="outlet", y="revenue",
        text=[fmt_rp(r) for r in rev["revenue"]],
        color="outlet",
        color_discrete_map=dict(zip(rev["outlet"], colors * 3)),
    )
    fig.update_layout(
        title={"text": "Revenue per Outlet", "font": {"size": 18, "color": BROWN_DARK}},
        showlegend=False,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(title="", tickfont={"color": BROWN_MED}),
        yaxis=dict(title="Revenue (Rp)", tickprefix="Rp ", gridcolor=CREAM_DARK),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(textposition="outside", textfont={"color": BROWN_DARK, "size": 13})
    st.plotly_chart(fig, use_container_width=True)

    det = rev.copy()
    det["revenue_fmt"]    = det["revenue"].apply(fmt_rp)
    det["avg_ticket_fmt"] = det["avg_ticket"].apply(fmt_rp)
    det = det[["outlet", "orders", "revenue_fmt", "avg_ticket_fmt"]]
    det.columns = ["Outlet", "Orders", "Revenue", "Avg Ticket"]
    st.dataframe(det, hide_index=True, use_container_width=True)


# ── Top Menu ───────────────────────────────────────────────────────────────────
def top_menu(orders):
    top = (
        orders.groupby("menu_item")
        .agg(revenue=("revenue_idr", "sum"), cups=("qty", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(5)
    )

    fig = px.bar(
        top, x="menu_item", y="revenue",
        text=[fmt_rp(r) for r in top["revenue"]],
        color="revenue",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(
        title={"text": "Top 5 Menu by Revenue", "font": {"size": 18, "color": BROWN_DARK}},
        showlegend=False,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(title="", tickfont={"color": BROWN_MED, "size": 11}),
        yaxis=dict(title="Revenue (Rp)", tickprefix="Rp ", gridcolor=CREAM_DARK),
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    fig.update_traces(textposition="outside", textfont={"color": BROWN_DARK, "size": 13})
    st.plotly_chart(fig, use_container_width=True)


# ── Payment Mix ────────────────────────────────────────────────────────────────
def payment_mix(orders):
    mix = (
        orders.groupby("payment_method")
        .agg(n=("order_id", "count"), revenue=("revenue_idr", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
    )
    mix["pct"] = (mix["n"] / mix["n"].sum() * 100).round(1)
    palette = [BROWN_DARK, BROWN_MED, "#7A5A3A", BROWN_LIGHT, "#C4956A", ORANGE_ACC, "#E8B87A"]

    fig = px.pie(
        mix, names="payment_method", values="n",
        hole=0.5,
        color="payment_method",
        color_discrete_map=dict(zip(mix["payment_method"], palette[:len(mix)])),
    )
    fig.update_layout(
        title={"text": "Payment Method Mix", "font": {"size": 18, "color": BROWN_DARK}},
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(font={"color": BROWN_MED}),
    )
    fig.update_traces(
        textposition="outside",
        textfont={"color": BROWN_DARK, "size": 12},
        textinfo="percent+label",
    )
    st.plotly_chart(fig, use_container_width=True)

    tbl = mix.copy()
    tbl["revenue_fmt"] = tbl["revenue"].apply(fmt_rp)
    tbl = tbl[["payment_method", "n", "pct", "revenue_fmt"]]
    tbl.columns = ["Payment", "Orders", "%", "Revenue"]
    st.dataframe(tbl, hide_index=True, use_container_width=True)


# ── Daily Trend ────────────────────────────────────────────────────────────────
def daily_trend(orders):
    daily = (
        orders.groupby(["order_date", "outlet"])
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("order_date")
    )
    colors = {"Dago": BROWN_DARK, "Setiabudi": BROWN_MED, "Buah Batu": BROWN_LIGHT}

    fig = px.line(
        daily, x="order_date", y="revenue",
        color="outlet",
        color_discrete_map=colors,
        markers=True,
    )
    fig.update_layout(
        title={"text": "Daily Revenue Trend by Outlet", "font": {"size": 18, "color": BROWN_DARK}},
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(gridcolor=CREAM_DARK, tickfont={"color": BROWN_MED}),
        yaxis=dict(tickprefix="Rp ", gridcolor=CREAM_DARK, tickfont={"color": BROWN_MED}),
        legend=dict(font={"color": BROWN_MED}),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(line={"width": 2.5}, marker={"size": 7})
    st.plotly_chart(fig, use_container_width=True)


# ── Shift Performance ─────────────────────────────────────────────────────────
def shift_performance(orders):
    shift = (
        orders[orders["shift"].notna()]
        .groupby(["outlet", "shift"])
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
    shift["avg_ticket"] = shift["revenue"] / shift["orders"]

    fig = px.bar(
        shift, x="outlet", y="revenue",
        color="shift",
        barmode="group",
        color_discrete_map={"Pagi": CREAM, "Siang": BROWN_LIGHT, "Malam": BROWN_DARK},
        text=[fmt_rp(r) for r in shift["revenue"]],
    )
    fig.update_layout(
        title={"text": "Revenue by Outlet & Shift", "font": {"size": 18, "color": BROWN_DARK}},
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(title="", tickfont={"color": BROWN_MED}),
        yaxis=dict(tickprefix="Rp ", gridcolor=CREAM_DARK, tickfont={"color": BROWN_MED}),
        legend=dict(font={"color": BROWN_MED}),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(textposition="outside", textfont={"color": BROWN_DARK, "size": 10})
    st.plotly_chart(fig, use_container_width=True)


# ── Category Performance ───────────────────────────────────────────────────────
def category_performance(orders, menu):
    cat = (
        orders.groupby("menu_item")["revenue_idr"]
        .sum().reset_index()
        .merge(menu[["menu_item", "category"]], on="menu_item")
        .groupby("category")
        .agg(revenue=("revenue_idr", "sum"), items=("menu_item", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

    fig = px.bar(
        cat, x="category", y="revenue",
        color="category",
        color_discrete_sequence=["#6F4E37","#8B6240","#A0724A","#C4956A","#D4852F","#E8B87A"],
        text=[fmt_rp(r) for r in cat["revenue"]],
    )
    fig.update_layout(
        title={"text": "Revenue by Category", "font": {"size": 18, "color": BROWN_DARK}},
        showlegend=False,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(title="", tickfont={"color": BROWN_MED}),
        yaxis=dict(tickprefix="Rp ", gridcolor=CREAM_DARK, tickfont={"color": BROWN_MED}),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(textposition="outside", textfont={"color": BROWN_DARK, "size": 12})
    st.plotly_chart(fig, use_container_width=True)


# ── Cleansing Report ───────────────────────────────────────────────────────────
def cleansing_info():
    st.markdown("### Pipeline Cleansing Report")
    st.caption("3 sumber data · 10 langkah cleansing · DuckDB warehouse")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Rows**")
        st.markdown(f"- Input: `464`")
        st.markdown(f"- Output: `364`")
        st.markdown(f"- Dropped: `100`")
    with c2:
        st.markdown("**Quality**")
        st.markdown(f"- Unknown outlet: `0`")
        st.markdown(f"- Unknown size: `0`")
        st.markdown(f"- Price repaired: `9`")

    st.markdown("---")
    st.markdown("### Cleansing Breakdown")
    rows = [
        ("Drop: Unknown Payment", "10"),
        ("Drop: Invalid Qty", "6"),
        ("Drop: Duplicate", "84"),
        ("Drop: Unknown Size", "0"),
        ("Drop: Unknown Menu", "0"),
        ("Price Recomputed", "9"),
    ]
    for label, val in rows:
        st.markdown(f"- **{label}:** `{val}`")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="KopiDate — Operations Dashboard",
        page_icon="☕",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Custom CSS
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {CREAM}; }}
    [data-testid="stMetric"] {{
        background-color: {WHITE};
        border: 1px solid {CREAM_DARK};
        border-radius: 10px;
        padding: 14px 10px;
    }}
    [data-testid="stMetricLabel"] {{ color: {BROWN_MED}; font-size: 0.78rem; }}
    [data-testid="stMetricValue"] {{ color: {BROWN_DARK}; font-size: 1.4rem; font-weight: 700; }}
    h2 {{ color: {BROWN_DARK} !important; font-weight: 700 !important; }}
    hr {{ border-color: {CREAM_DARK}; }}
    </style>
    """, unsafe_allow_html=True)

    # Header bar
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {BROWN_DARK} 0%, {BROWN_MED} 100%);
        color: {WHITE};
        padding: 24px 32px;
        border-radius: 0 0 16px 16px;
        margin-bottom: 28px;
        box-shadow: 0 4px 12px rgba(61,35,20,0.15);
    ">
        <h1 style="margin:0; font-size:1.9rem; font-weight:800; letter-spacing:-0.5px;">
            ☕ KopiDate — Daily Operations Dashboard
        </h1>
        <p style="margin:6px 0 0; color:#C4956A; font-size:0.88rem;">
            PT KopiXYZ Indonesia &nbsp;·&nbsp; Jan–Feb 2024 &nbsp;·&nbsp; 3 Outlets
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not DB_PATH.exists():
        st.error(f"Database tidak ditemukan. Jalankan: python pipeline/pipeline.py")
        st.stop()

    try:
        orders, menu = load_data()
    except Exception as e:
        st.error(f"Gagal load data: {e}")
        st.stop()

    kpi_cards(orders)
    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a: revenue_by_outlet(orders)
    with col_b: top_menu(orders)

    col_c, col_d = st.columns(2)
    with col_c: payment_mix(orders)
    with col_d: shift_performance(orders)

    daily_trend(orders)

    col_e, col_f = st.columns(2)
    with col_e: category_performance(orders, menu)
    with col_f: cleansing_info()


if __name__ == "__main__":
    main()
