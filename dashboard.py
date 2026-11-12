import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Ativos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estado da Sessão ---
if "dashboard_assets" not in st.session_state:
    st.session_state.dashboard_assets = ["BTLG11", "SAPR11", "BBAS3"]

if "available_assets" not in st.session_state:
    st.session_state.available_assets = [
        "BTLG11", "SAPR11", "BBAS3", "IVVB11", "TAEE11",
        "PETR4", "VALE3", "ITUB4", "HGLG11", "MXRF11"
    ]

# --- Funções Auxiliares ---
def get_ticker_symbol(ticker):
    """Adiciona o sufixo .SA para ativos da B3."""
    return f"{ticker}.SA"

def fetch_data(ticker, period):
    """Busca dados históricos do Yahoo Finance."""
    symbol = get_ticker_symbol(ticker)

    period_map = {
        "1d": "1d",
        "1s": "5d",
        "1m": "1mo",
        "1a": "1y",
        "5a": "5y",
        "Max": "max"
    }

    if period in ["1d", "1s"]:
        interval = "5m"
    elif period == "1m":
        interval = "1h"
    else:
        interval = "1d"

    try:
        data = yf.download(symbol, period=period_map[period], interval=interval, progress=False)

        if data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data
    except Exception:
        return None

def create_chart(data, ticker, period_label):
    """Cria o gráfico de candlestick ou linha com Plotly."""
    if data is None or data.empty:
        return None

    fig = go.Figure()

    if period_label in ["1d", "1s"]:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Preço',
            line=dict(color='#00CC96', width=2)
        ))
    else:
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='OHLC',
            increasing_line_color='#00CC96',
            decreasing_line_color='#EF553B'
        ))

    fig.update_layout(
        title=f"{ticker} ({period_label})",
        xaxis_title=None,
        yaxis_title="Preço (R$)",
        template="plotly_dark",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    return fig

# --- Sidebar ---
with st.sidebar:
    st.header("Gerenciar Ativos")

    period_option = st.selectbox(
        "Período do Gráfico",
        options=["1d", "1s", "1m", "1a", "5a", "Max"],
        index=2
    )

    st.divider()

    st.subheader("Adicionar / Remover")

    for asset in st.session_state.available_assets:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{asset}**")
        with col2:
            if st.button("+", key=f"add_{asset}"):
                if asset not in st.session_state.dashboard_assets:
                    if len(st.session_state.dashboard_assets) < 5:
                        st.session_state.dashboard_assets.append(asset)
                        st.rerun()
                    else:
                        st.warning("Máximo de 5 gráficos atingido.")
        with col3:
            if st.button("-", key=f"rem_{asset}"):
                if asset in st.session_state.dashboard_assets:
                    st.session_state.dashboard_assets.remove(asset)
                    st.rerun()

    st.divider()

    new_asset = st.text_input("Adicionar novo ativo (ex: PETR4)")
    if st.button("Incluir na Lista"):
        if new_asset and new_asset.upper() not in st.session_state.available_assets:
            st.session_state.available_assets.append(new_asset.upper())
            st.rerun()

# --- Corpo Principal (Dashboard) ---
st.title("📊 Dashboard de Ativos Financeiros")

if not st.session_state.dashboard_assets:
    st.info("Nenhum ativo selecionado. Use a barra lateral para adicionar gráficos.")
else:
    @st.fragment(run_every=60)
    def render_charts():
        assets = st.session_state.dashboard_assets
        num_assets = len(assets)

        # Layout: 1 ativo -> 1 coluna; demais -> 2 colunas (grade)
        n_cols = 1 if num_assets == 1 else 2

        # Distribui os ativos em linhas de n_cols colunas
        for row_start in range(0, num_assets, n_cols):
            row_assets = assets[row_start:row_start + n_cols]
            cols = st.columns(n_cols)
            for idx, ticker in enumerate(row_assets):
                with cols[idx]:
                    with st.container(border=True):
                        df = fetch_data(ticker, period_option)
                        if df is not None and not df.empty:
                            fig = create_chart(df, ticker, period_option)
                            if fig:
                                st.plotly_chart(
                                    fig,
                                    use_container_width=True,
                                    key=f"chart_{ticker}_{period_option}_{row_start}_{idx}"
                                )
                            else:
                                st.warning(f"Não foi possível gerar o gráfico para {ticker}.")
                        else:
                            st.error(f"Falha ao carregar dados de {ticker}. Verifique o código ou a conexão.")

    render_charts()

# --- Rodapé ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; padding: 10px 0; color: #888; font-size: 14px;">
        Criado por <strong>Wallison Ferreira</strong><br>
        <a href="https://github.com/wallisonferreira" target="_blank"
           style="color: #00CC96; text-decoration: none;">
           github.com/wallisonferreira
        </a>
    </div>
    """,
    unsafe_allow_html=True
)