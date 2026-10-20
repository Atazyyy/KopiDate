"""
Dashboard untuk KopiDate — PT KopiXYZ Indonesia

Menjalankan: streamlit run dashboard.py
Buka: http://localhost:8501

Menampilkan:
  - KPI cards (total revenue, orders, avg ticket, outlets)
  - Revenue per outlet
  - Top 5 menu
  - Payment mix
  - Daily revenue trend (time series)
  - Cleansing report
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DB_PATH = Path(__file__).parent / "pipeline" / "KopiDate.duckdb"


def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    orders = con.execute("SELECT * FROM orders").fetchdf()
    menu = con.execute("SELECT * FROM menu").fetchdf()
    con.close()
    return orders, menu


def kpi_cards(orders: pd.DataFrame):
    total_revenue = int(orders["revenue_idr"].sum())
    total_orders = len(orders)
    avg_ticket = int(orders["revenue_idr"].mean())
    n_outlets = orders["outlet"].nunique()
    n_menu = orders["menu_item"].nunique()
    n_days = orders["order_date"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"Rp {total_revenue:,}".replace(",", "."))
    col2.metric("Total Orders", f"{total_orders:,}".replace(",", "."))
    col3.metric("Avg Ticket", f"Rp {avg_ticket:,}".replace(",", "."))
    col4.metric("Outlets", n_outlets)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Menu Items Sold", n_menu)
    col2.metric("Days Active", n_days)
    col3.metric("Peak Revenue", f"Rp {int(orders.groupby('order_date')['revenue_idr'].sum().max()):,}".replace(",", "."))
    col4.metric("Top Payment", orders["payment_method"].mode()[0])


def revenue_by_outlet(orders: pd.DataFrame):
    rev = (
        orders.groupby("outlet")
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    rev["revenue_fmt"] = rev["revenue"].apply(lambda x: f"Rp {x:,}".replace(",", "."))
    rev["avg_ticket"] = (rev["revenue"] / rev["orders"]).apply(lambda x: f"Rp {int(x):,}".replace(",", "."))

    fig = px.bar(
        rev,
        x="outlet",
        y="revenue",
        text="revenue_fmt",
        color="outlet",
        title="Revenue per Outlet",
        labels={"revenue": "Revenue (Rp)", "outlet": "Outlet"},
        color_discrete_sequence=["#6f4e37", "#8B5E3C", "#A0724A"],
    )
    fig.update_layout(showlegend=False, title_x=0)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(rev[["outlet", "orders", "revenue_fmt", "avg_ticket"]].rename(columns={
        "outlet": "Outlet", "orders": "Orders", "revenue_fmt": "Revenue", "avg_ticket": "Avg Ticket"
    }), hide_index=True)


def top_menu(orders: pd.DataFrame):
    top = (
        orders.groupby("menu_item")
        .agg(revenue=("revenue_idr", "sum"), cups=("qty", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(5)
    )
    top["revenue_fmt"] = top["revenue"].apply(lambda x: f"Rp {x:,}".replace(",", "."))

    fig = px.bar(
        top,
        x="menu_item",
        y="revenue",
        text="revenue_fmt",
        color="menu_item",
        title="Top 5 Menu by Revenue",
        labels={"revenue": "Revenue (Rp)", "menu_item": "Menu"},
        color_discrete_sequence=px.colors.sequential.Brown[2:],
    )
    fig.update_layout(showlegend=False, title_x=0)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def payment_mix(orders: pd.DataFrame):
    mix = (
        orders.groupby("payment_method")
        .agg(n=("order_id", "count"), revenue=("revenue_idr", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
    )
    mix["pct"] = (mix["n"] / mix["n"].sum() * 100).round(1)

    col_chart, col_table = st.columns([2, 1])

    fig = px.pie(
        mix,
        names="payment_method",
        values="n",
        hole=0.4,
        title="Payment Method Mix",
        color_discrete_sequence=px.colors.sequential.Brown_r,
    )
    fig.update_layout(title_x=0, showlegend=True)
    col_chart.plotly_chart(fig, use_container_width=True)

    mix["revenue_fmt"] = mix["revenue"].apply(lambda x: f"Rp {x:,}".replace(",", "."))
    col_table.dataframe(
        mix[["payment_method", "n", "pct", "revenue_fmt"]].rename(columns={
            "payment_method": "Payment", "n": "Orders", "pct": "%", "revenue_fmt": "Revenue"
        }),
        hide_index=True
    )


def daily_trend(orders: pd.DataFrame):
    daily = (
        orders.groupby(["order_date", "outlet"])
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("order_date")
    )

    fig = px.line(
        daily,
        x="order_date",
        y="revenue",
        color="outlet",
        markers=True,
        title="Daily Revenue Trend by Outlet",
        labels={"order_date": "Date", "revenue": "Revenue (Rp)", "outlet": "Outlet"},
        color_discrete_sequence=["#6f4e37", "#8B5E3C", "#A0724A"],
    )
    fig.update_layout(title_x=0)
    st.plotly_chart(fig, use_container_width=True)


def shift_performance(orders: pd.DataFrame):
    shift = (
        orders[orders["shift"].notna()]
        .groupby(["outlet", "shift"])
        .agg(revenue=("revenue_idr", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
    shift["avg_ticket"] = (shift["revenue"] / shift["orders"]).round(0)

    fig = px.bar(
        shift,
        x="outlet",
        y="revenue",
        color="shift",
        barmode="group",
        title="Revenue by Outlet & Shift",
        labels={"outlet": "Outlet", "revenue": "Revenue (Rp)", "shift": "Shift"},
        color_discrete_sequence=["#c8a97e", "#8B5E3C", "#4a3728"],
    )
    fig.update_layout(title_x=0)
    st.plotly_chart(fig, use_container_width=True)


def category_performance(orders: pd.DataFrame, menu: pd.DataFrame):
    cat = (
        orders.groupby("menu_item")["revenue_idr"]
        .sum()
        .reset_index()
        .merge(menu[["menu_item", "category"]], on="menu_item")
        .groupby("category")
        .agg(revenue=("revenue_idr", "sum"), items=("menu_item", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    cat["revenue_fmt"] = cat["revenue"].apply(lambda x: f"Rp {x:,}".replace(",", "."))

    fig = px.bar(
        cat,
        x="category",
        y="revenue",
        text="revenue_fmt",
        color="category",
        title="Revenue by Category",
        labels={"category": "Category", "revenue": "Revenue (Rp)"},
        color_discrete_sequence=px.colors.sequential.Brown,
    )
    fig.update_layout(showlegend=False, title_x=0)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def cleansing_info():
    st.markdown("---")
    st.subheader("Pipeline Cleansing Report")
    st.caption("Data source: pipeline/KopiDate.duckdb — 3 sources, 10-step cleansing")
    st.markdown("""
| Metric | Value |
|--------|-------|
| Input rows | 464 |
| Output rows | 364 |
| Dropped (unknown payment) | 10 |
| Dropped (invalid qty) | 6 |
| Dropped (duplicate) | 84 |
| Price recomputed | 9 |
| Unknown outlet | 0 |
| Unknown size | 0 |
| Unknown menu | 0 |
    """.strip())


def main():
    st.set_page_config(
        page_title="KopiXYZ — Daily Dashboard",
        page_icon="☕",
        layout="wide",
    )

    st.title("KopiXYZ Indonesia — Daily Operations Dashboard")
    st.caption(f"Warehouse: KopiDate.duckdb · {DB_PATH}")

    if not DB_PATH.exists():
        st.error(f"Database tidak ditemukan. Jalankan pipeline dulu: python pipeline/pipeline.py")
        st.stop()

    try:
        orders, menu = load_data()
    except Exception as e:
        st.error(f"Gagal load data: {e}")
        st.stop()

    kpi_cards(orders)

    st.markdown("---")

    col_left, col_right = st.columns(2)
    with col_left:
        revenue_by_outlet(orders)
    with col_right:
        top_menu(orders)

    col_pay, col_shift = st.columns(2)
    with col_pay:
        payment_mix(orders)
    with col_shift:
        shift_performance(orders)

    daily_trend(orders)
    category_performance(orders, menu)
    cleansing_info()


if __name__ == "__main__":
    main()
