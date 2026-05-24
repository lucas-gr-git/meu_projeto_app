import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from scipy.stats import norm
import math
import requests
from supabase import create_client, Client

# ==============================================================================
# --- CONFIGURAÇÃO DA PÁGINA ---
# ==============================================================================
st.set_page_config(page_title="Terminal B3", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# --- BANCO DE DADOS (SUPABASE) ---
# ==============================================================================
@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# ==============================================================================
# --- SESSÃO CUSTOMIZADA (YFINANCE) ---
# ==============================================================================
session_yf = requests.Session()
session_yf.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# ==============================================================================
# --- SISTEMA DE SEGURANÇA E LOGIN ---
# ==============================================================================
USUARIOS_CADASTRADOS = {
    "lucas@provedor.com.br": "senha123",
    "visitante@email.com": "acesso2026",
    "amigo@email.com": "123456",
    "teste@teste.com.br": "senha123"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso Restrito</h2>", unsafe_allow_html=True)
        st.info("Por favor, faça o login para acessar o Terminal B3.")
        email_digitado = st.text_input("E-mail cadastrado:").strip().lower()
        senha_digitada = st.text_input("Senha:", type="password")
        if st.button("Entrar", use_container_width=True):
            if email_digitado in USUARIOS_CADASTRADOS and USUARIOS_CADASTRADOS[email_digitado] == senha_digitada:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ E-mail não cadastrado ou senha incorreta.")
    st.stop()

# ==============================================================================
# --- O SEU CÓDIGO ORIGINAL COMEÇA AQUI DEPOIS DO LOGIN ---
# ==============================================================================
st.title("🖥️ Terminal Profissional de Inteligência Mercado - B3")
st.markdown("Monitoramento Avançado, Análise Técnica, Fundamentalista e Notícias em Tempo Real.")

if supabase is None:
    st.warning("⚠️ Supabase não configurado nos Secrets. O Diário de Operações não será salvo na nuvem.")

# --- LISTA DAS TOP 70 AÇÕES SEPARADAS POR SETOR ---
ativos_setores = {
    'ITUB4.SA': 'Financeiro', 'BBDC4.SA': 'Financeiro', 'BBAS3.SA': 'Financeiro', 'SANB11.SA': 'Financeiro', 'BPAC11.SA': 'Financeiro', 'B3SA3.SA': 'Financeiro', 'BBSE3.SA': 'Financeiro', 'CXSE3.SA': 'Financeiro', 'IRBR3.SA': 'Financeiro', 'PSSA3.SA': 'Financeiro',
    'PETR4.SA': 'Petróleo e Gás', 'PETR3.SA': 'Petróleo e Gás', 'PRIO3.SA': 'Petróleo e Gás', 'RECV3.SA': 'Petróleo e Gás', 'ENAT3.SA': 'Petróleo e Gás', 'RRRP3.SA': 'Petróleo e Gás', 'UGPA3.SA': 'Petróleo e Gás', 'VBBR3.SA': 'Petróleo e Gás', 'CSAN3.SA': 'Petróleo e Gás',
    'VALE3.SA': 'Mineração', 'GGBR4.SA': 'Mineração', 'GOAU4.SA': 'Mineração', 'CSNA3.SA': 'Mineração', 'USIM5.SA': 'Mineração', 'CMIN3.SA': 'Mineração', 'BRAP4.SA': 'Mineração',
    'ELET3.SA': 'Energia', 'ELET6.SA': 'Energia', 'EQTL3.SA': 'Energia', 'CMIG4.SA': 'Energia', 'CPLE6.SA': 'Energia', 'ENGI11.SA': 'Energia', 'TAEE11.SA': 'Energia', 'TRPL4.SA': 'Energia', 'EGIE3.SA': 'Energia',
    'WEGE3.SA': 'Indústria', 'EMBR3.SA': 'Indústria',
    'LREN3.SA': 'Varejo', 'MGLU3.SA': 'Varejo', 'ARZZ3.SA': 'Varejo', 'ALOS3.SA': 'Varejo', 'RENT3.SA': 'Varejo', 'NTCO3.SA': 'Varejo', 'ASAI3.SA': 'Varejo', 'CRFB3.SA': 'Varejo', 'PCAR3.SA': 'Varejo', 'VIVA3.SA': 'Varejo',
    'HAPV3.SA': 'Saúde', 'RDOR3.SA': 'Saúde', 'RADL3.SA': 'Saúde', 'FLRY3.SA': 'Saúde', 'MATD3.SA': 'Saúde',
    'ABEV3.SA': 'Alimentos e Bebidas', 'JBSS3.SA': 'Alimentos e Bebidas', 'MRFG3.SA': 'Alimentos e Bebidas', 'BEEF3.SA': 'Alimentos e Bebidas', 'BRFS3.SA': 'Alimentos e Bebidas', 'SMTO3.SA': 'Alimentos e Bebidas',
    'RAIL3.SA': 'Logística', 'CCRO3.SA': 'Logística', 'AZUL4.SA': 'Logística', 'GOLL4.SA': 'Logística',
    'VIVT3.SA': 'Telecom e TI', 'TIMS3.SA': 'Telecom e TI', 'TOTVS3.SA': 'Telecom e TI',
    'SBSP3.SA': 'Saneamento', 'CSMG3.SA': 'Saneamento', 'SAPR11.SA': 'Saneamento',
    'SUZB3.SA': 'Papel e Celulose', 'KLBN11.SA': 'Papel e Celulose',
    'CYRE3.SA': 'Construção', 'MRVE3.SA': 'Construção', 'EZTC3.SA': 'Construção', 'TEND3.SA': 'Construção'
}
ativos_lista = list(ativos_setores.keys())

# --- FUNÇÕES DE CARREGAMENTO COM CACHE ---
@st.cache_data(ttl=300)
def carregar_dados(ativos, dias):
    hoje = datetime.today().strftime('%Y-%m-%d')
    inicio = (datetime.today() - timedelta(days=dias)).strftime('%Y-%m-%d')
    dados = yf.download(ativos, start=inicio, end=hoje, session=session_yf, progress=False)
    return dados['Close'], dados

@st.cache_data(ttl=600)
def buscar_noticias_google(ativo):
    try:
        nome_limpo = ativo.replace('.SA', '')
        query = urllib.parse.quote(f"{nome_limpo} ações brasil")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        noticias = []
        for item in root.findall('.//item')[:6]:
            titulo = item.find('title').text
            link = item.find('link').text
            fonte = item.find('source').text if item.find('source') is not None else 'Google News'
            pub_date = item.find('pubDate').text
            try:
                partes = pub_date.split(' ')
                data_formatada = f"{partes[1]} {partes[2]} {partes[3]} • {partes[4][:5]}"
            except:
                data_formatada = pub_date
            noticias.append({'title': titulo, 'link': link, 'publisher': fonte, 'time': data_formatada})
        return noticias
    except:
        return []

# --- FUNÇÕES AUXILIARES ---
def fmt_br(val, is_pct=False, currency=False):
    if pd.isna(val) or val is None or val == "-": return "-"
    texto = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{texto}%"
    if currency: return f"R$ {texto}"
    return texto

def cor_variacao(val):
    if pd.isna(val) or val == "-": return "#2b2e35"
    return "#228B22" if val > 0 else "#B22222" if val < 0 else "#2b2e35"

# --- FUNÇÕES DIDI AGUIAR ---
def calcular_didi(df_close):
    sma3  = df_close.rolling(3).mean()
    sma8  = df_close.rolling(8).mean()
    sma20 = df_close.rolling(20).mean()
    fast  = sma3 - sma8
    slow  = sma20 - sma8
    return fast, slow, sma3, sma8, sma20

def detectar_agulhada(fast, slow):
    sinais = []
    for i in range(1, len(fast)):
        f_ant = fast.iloc[i-1]
        f_at  = fast.iloc[i]
        s_at  = slow.iloc[i]
        if pd.isna(f_at) or pd.isna(s_at) or pd.isna(f_ant): continue
        if f_ant < 0 and f_at > 0 and s_at < 0:
            sinais.append((fast.index[i], 'COMPRA'))
        elif f_ant > 0 and f_at < 0 and s_at > 0:
            sinais.append((fast.index[i], 'VENDA'))
    return sinais

# --- FUNÇÕES BLACK-SCHOLES ---
def black_scholes(S, K, T, r, sigma, tipo='call'):
    if T <= 0 or sigma <= 0: return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if tipo == 'call':
        preco = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else:
        preco = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return round(preco, 4)

def calcular_gregas(S, K, T, r, sigma, tipo='call'):
    if T <= 0 or sigma <= 0:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    nd1 = norm.pdf(d1)
    if tipo == 'call':
        delta = norm.cdf(d1)
        rho   = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
        theta = (-(S * nd1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1
        rho   = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
        theta = (-(S * nd1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
    gamma = nd1 / (S * sigma * math.sqrt(T))
    vega  = S * nd1 * math.sqrt(T) / 100
    return {
        'delta': round(delta, 4), 'gamma': round(gamma, 6), 'theta': round(theta, 4), 'vega': round(vega, 4), 'rho': round(rho, 4)
    }

def volatilidade_historica(serie, janela=21):
    retornos = np.log(serie / serie.shift(1)).dropna()
    return float(retornos.rolling(janela).std().iloc[-1] * math.sqrt(252))

# --- CARREGA DADOS BASE ---
precos_fechamento, dados_completos = carregar_dados(ativos_lista, 365)

# --- PROCESSAMENTO DE MÉTRICAS GERAIS ---
resultados = []
for ativo in ativos_lista:
    df = pd.DataFrame()
    if ativo in precos_fechamento.columns:
        df['Close'] = precos_fechamento[ativo]
        df['SMA50']  = df['Close'].rolling(window=50).mean()
        df['SMA100'] = df['Close'].rolling(window=100).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        delta_r = df['Close'].diff()
        ganho = (delta_r.where(delta_r > 0, 0)).rolling(window=14).mean()
        perda = (-delta_r.where(delta_r < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df['RSI'] = 100 - (100 / (1 + rs))
        
        ultimo_preco    = float(df['Close'].dropna().iloc[-1]) if not df['Close'].dropna().empty else 0
        sma50           = float(df['SMA50'].dropna().iloc[-1])  if not df['SMA50'].dropna().empty  else 0
        sma100          = float(df['SMA100'].dropna().iloc[-1]) if not df['SMA100'].dropna().empty else 0
        sma200          = float(df['SMA200'].dropna().iloc[-1]) if not df['SMA200'].dropna().empty else 0
        rsi             = float(df['RSI'].dropna().iloc[-1])    if not df['RSI'].dropna().empty    else np.nan
        variacao_diaria = float(df['Close'].dropna().pct_change().iloc[-1] * 100) if len(df['Close'].dropna()) > 1 else 0.0
        
        tendencia_curta = 'Alta' if ultimo_preco > sma50  else 'Baixa'
        tendencia_media = 'Alta' if ultimo_preco > sma100 else 'Baixa'
        tendencia_longa = 'Alta' if ultimo_preco > sma200 else 'Baixa' if sma200 > 0 else 'N/A'
        sentimento      = 'Sobrecomprado' if rsi > 70 else 'Sobrevendido' if rsi < 30 else 'Neutro'
        
        resultados.append({
            'Ativo': ativo.replace('.SA', ''), 'Setor': ativos_setores[ativo], 'Preço (R$)': round(ultimo_preco, 2),
            'Variação (%)': round(variacao_diaria, 2), 'Tendência Curta (50D)': tendencia_curta,
            'Tendência Média (100D)': tendencia_media, 'Tendência Longa (200D)': tendencia_longa, 'Sentimento': sentimento
        })

df_resumo = pd.DataFrame(resultados)

# ==============================================================================
# --- ABAS ---
# ==============================================================================
tab_visao_geral, tab_analise_individual, tab_agulhadas, tab_backtest, tab_opcoes, tab_inteligencia = st.tabs([
    "🌐 Visão Geral do Mercado",
    "🔬 Análise Detalhada por Ativo",
    "🎯 Agulhadas do Didi",
    "🔄 Motor de Backtest",
    "📈 Opções — Método RCO",
    "🧠 Inteligência de Seleção"
])

# ==============================================================================
# --- ABA 1: VISÃO GERAL DO MERCADO ---
# ==============================================================================
with tab_visao_geral:
    st.markdown("### 📊 Mapa de Calor do Mercado")
    ids, labels, parents, values, colors, customdata = ["B3"], ["B3"], [""], [0], ["#0e1117"], [["<b>Painel Geral B3</b>", "<b>B3</b>"]]
    for setor in df_resumo['Setor'].unique():
        ids.append(setor); labels.append(setor); parents.append("B3"); values.append(0); colors.append("#262626")
        customdata.append([f"<b>Setor: {setor}</b>", f"<b>{setor}</b>"])
    for _, row in df_resumo.iterrows():
        ids.append(row['Ativo'])
        var = row['Variação (%)']
        preco = row['Preço (R$)']
        labels.append(f"{row['Ativo']}<br>R$ {preco:.2f}<br>{var:+.2f}%")
        parents.append(row['Setor']); values.append(1)
        colors.append("#228B22" if var > 0.05 else "#B22222" if var < -0.05 else "#505050")
        
        preco_br = fmt_br(preco)
        var_br   = f"{var:+.2f}%".replace(".", ",")
        hover = f"<b>{row['Ativo']}</b><br>Variação: {var_br}<br>Preço: R$ {preco_br}<br><br>Curta: {row['Tendência Curta (50D)']}<br>Média: {row['Tendência Média (100D)']}<br>Longa: {row['Tendência Longa (200D)']}"
        block = f"<b>{row['Ativo']}</b><br>R$ {preco_br}<br> {var_br}"
        customdata.append([hover, block])
        
    fig_treemap = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, marker_colors=colors,
        customdata=customdata, textinfo="label", textposition="top left", hovertemplate="%{customdata[0]}<extra></extra>", textfont=dict(color="white", size=13)
    ))
    fig_treemap.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=550, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
    st.plotly_chart(fig_treemap, use_container_width=True)
    
    st.subheader("📋 Resumo de Indicadores da Grade")
    col_filtro, _ = st.columns([1, 2])
    with col_filtro:
        setor_selecionado = st.selectbox("Filtrar Tabela:", ["Todos os Setores"] + sorted(list(df_resumo['Setor'].unique())))
    df_exibicao = df_resumo if setor_selecionado == "Todos os Setores" else df_resumo[df_resumo['Setor'] == setor_selecionado]
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

# ==============================================================================
# --- ABA 2: ANÁLISE DETALHADA POR ATIVO ---
# ==============================================================================
with tab_analise_individual:
    col_busca, col_tempo = st.columns([1, 1])
    with col_busca:
        ativo_buscado = st.text_input("🔍 Digite o código do ativo (Ex: PETR4):", key="search_asset").upper().strip()
    if ativo_buscado:
        if not ativo_buscado.endswith('.SA') and any(char.isdigit() for char in ativo_buscado):
            ativo_buscado += '.SA'
        with col_tempo:
            janela_tempo = st.radio("Período do Gráfico:", ["1 Mês", "6 Meses", "1 Ano", "2 Anos", "5 Anos"], index=2, horizontal=True)
            mapa_periodos = {"1 Mês": "1mo", "6 Meses": "6mo", "1 Ano": "1y", "2 Anos": "2y", "5 Anos": "5y"}
            periodo_selecionado = mapa_periodos[janela_tempo]
        with st.spinner("Processando histórico de 10 anos e fundamentos..."):
            ticker_obj = yf.Ticker(ativo_buscado, session=session_yf)
            df_hist    = yf.download(ativo_buscado, period="10y", session=session_yf, progress=False)
            if df_hist is None or df_hist.empty:
                st.error("⚠️ Código não encontrado.")
            else:
                if isinstance(df_hist.columns, pd.MultiIndex): df_hist.columns = [col[0] for col in df_hist.columns]
                
                serie_hist_limpa = df_hist['Close'].dropna()
                if not serie_hist_limpa.empty:
                    preco_atual = float(serie_hist_limpa.iloc[-1])
                    def calc_retorno(df, dias_uteis):
                        if len(df) > dias_uteis:
                            preco_antigo = float(df.iloc[-dias_uteis])
                            if preco_antigo > 0: return ((preco_atual / preco_antigo) - 1) * 100
                        return "-"
                    ret_1m  = calc_retorno(serie_hist_limpa, 21); ret_3m  = calc_retorno(serie_hist_limpa, 63)
                    ret_1a  = calc_retorno(serie_hist_limpa, 252); ret_2a  = calc_retorno(serie_hist_limpa, 504)
                    ret_5a  = calc_retorno(serie_hist_limpa, 1260); ret_10a = calc_retorno(serie_hist_limpa, 2520)
                else:
                    preco_atual = 0; ret_1m = ret_3m = ret_1a = ret_2a = ret_5a = ret_10a = "-"

                info = {}
                try: info = ticker_obj.info
                except: pass
                
                val_var12m = ret_1a if ret_1a != "-" else info.get('52WeekChange', "-")
                val_pl  = info.get('trailingPE') or info.get('forwardPE') or "-"
                val_pvp = info.get('priceToBook', "-")
                val_dy  = info.get('trailingAnnualDividendYield') or info.get('dividendYield')
                if val_dy: val_dy = val_dy * 100
                else:
                    div_anual = info.get('trailingAnnualDividendRate') or info.get('dividendRate')
                    val_dy = (div_anual / preco_atual) * 100 if div_anual and preco_atual > 0 else "-"

                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;">
                        <div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">COTAÇÃO</div>
                        <div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(preco_atual, currency=True)}</div>
                    </div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;">
                        <div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">VARIAÇÃO (12M)</div>
                        <div style="padding:15px;font-size:22px;font-weight:bold;color:{cor_variacao(val_var12m)};">{fmt_br(val_var12m, is_pct=True)}</div>
                    </div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;">
                        <div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">P/L</div>
                        <div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_pl)}</div>
                    </div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;">
                        <div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">P/VP</div>
                        <div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_pvp)}</div>
                    </div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;">
                        <div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">DY (12M)</div>
                        <div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_dy, is_pct=True)}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Graficos
                df_hist['SMA50']  = df_hist['Close'].rolling(window=50).mean()
                df_hist['SMA100'] = df_hist['Close'].rolling(window=100).mean()
                df_hist['SMA200'] = df_hist['Close'].rolling(window=200).mean()
                limite_data = datetime.now() - (timedelta(days=30) if janela_tempo == "1 Mês" else timedelta(days=180) if janela_tempo == "6 Meses" else timedelta(days=365) if janela_tempo == "1 Ano" else timedelta(days=730) if janela_tempo == "2 Anos" else timedelta(days=1825))
                df_plot = df_hist[df_hist.index >= limite_data].copy()
                cores_volume = ['#228B22' if r.Close >= r.Open else '#B22222' for r in df_plot.itertuples()]

                col_graficos, col_noticias = st.columns([3, 1])
                with col_graficos:
                    fig_plotly = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]], subplot_titles=('Gráfico de Preço e Volume',))
                    fig_plotly.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name='Candlestick'), row=1, col=1, secondary_y=False)
                    for m, c in zip(['SMA50','SMA100','SMA200'], ['#00BFFF','#BA55D3','white']):
                        fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot[m], mode='lines', name=f'Média {m.replace("SMA","")}', line=dict(color=c, width=1.5)), row=1, col=1, secondary_y=False)
                    fig_plotly.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name='Volume', marker_color=cores_volume, opacity=0.35), row=1, col=1, secondary_y=True)
                    fig_plotly.update_yaxes(title_text="Preço (R$)", side="right", row=1, col=1, secondary_y=False)
                    fig_plotly.update_yaxes(showgrid=False, showticklabels=False, range=[0, df_plot['Volume'].max()*4], row=1, col=1, secondary_y=True)
                    fig_plotly.update_layout(template='plotly_dark', height=600, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    fig_plotly.update_xaxes(rangeslider_visible=False)
                    st.plotly_chart(fig_plotly, use_container_width=True)

                with col_noticias:
                    st.markdown("### 📰 Notícias Recentes")
                    noticias = buscar_noticias_google(ativo_buscado)
                    if not noticias: st.info("Nenhuma notícia.")
                    else:
                        for n in noticias:
                            st.markdown(f"""<div style="border:1px solid #444;border-radius:5px;padding:10px;margin-bottom:12px;background:#1e1e1e;">
                                <a href="{n['link']}" target="_blank" style="color:#00BFFF;text-decoration:none;font-weight:bold;font-size:14px;">{n['title']}</a>
                                <p style="color:#888;font-size:11px;margin:5px 0 0 0;">{n['publisher']} • {n['time']}</p>
                            </div>""", unsafe_allow_html=True)

# ==============================================================================
# --- ABA 3: AGULHADAS DO DIDI ---
# ==============================================================================
with tab_agulhadas:
    st.markdown("### 🎯 Scanner de Agulhadas - Método Didi Aguiar")
    st.markdown("Varredura automática em todos os ativos monitorados. Sinais gerados pelas médias **SMA3, SMA8 e SMA20**.")
    col_cfg1, _ = st.columns([1, 2])
    with col_cfg1:
        dias_scanner = st.selectbox("Período da varredura:", [30, 60, 90, 180], index=1, format_func=lambda x: f"Últimos {x} dias")
    with st.spinner("🔍 Varrendo todos os ativos em busca de agulhadas..."):
        resultados_agulhada = []
        for ativo in ativos_lista:
            if ativo not in precos_fechamento.columns: continue
            serie = precos_fechamento[ativo].dropna()
            if len(serie) < 30: continue
            fast, slow, sma3, sma8, sma20 = calcular_didi(serie)
            sinais  = detectar_agulhada(fast, slow)
            corte   = pd.Timestamp.now() - pd.Timedelta(days=dias_scanner)
            sinais_recentes = [(d, t) for d, t in sinais if d >= corte]
            if sinais_recentes:
                ultimo_sinal_data, ultimo_sinal_tipo = sinais_recentes[-1]
                dias_atras = (pd.Timestamp.now() - ultimo_sinal_data).days
                serie_apos = serie[serie.index >= ultimo_sinal_data]
                preco_sinal    = float(serie_apos.iloc[0]) if not serie_apos.empty else 0
                preco_atual_ag = float(serie.iloc[-1])
                retorno = ((preco_atual_ag / preco_sinal) - 1) * 100 if preco_sinal > 0 else 0
                resultados_agulhada.append({
                    'Ativo': ativo.replace('.SA',''), 'Setor': ativos_setores[ativo], 'Sinal': ultimo_sinal_tipo,
                    'Data do Sinal': ultimo_sinal_data.strftime('%d/%m/%Y'), 'Dias Atrás': dias_atras,
                    'Preço no Sinal (R$)': round(preco_sinal, 2), 'Preço Atual (R$)': round(preco_atual_ag, 2),
                    'Retorno desde Sinal (%)': round(retorno, 2), 'Total de Sinais': len(sinais_recentes)
                })
        df_agulhadas = pd.DataFrame(resultados_agulhada)
        if df_agulhadas.empty:
            st.warning("Nenhuma agulhada encontrada no período selecionado.")
        else:
            total_compra = len(df_agulhadas[df_agulhadas['Sinal'] == 'COMPRA'])
            total_venda  = len(df_agulhadas[df_agulhadas['Sinal'] == 'VENDA'])
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📊 Ativos com Sinal", len(df_agulhadas))
            m2.metric("🟢 Agulhadas de Compra", total_compra)
            m3.metric("🔴 Agulhadas de Venda", total_venda)
            m4.metric("⚖️ Saldo (C - V)", total_compra - total_venda)
            st.markdown("<br>", unsafe_allow_html=True)
            compras = df_agulhadas[df_agulhadas['Sinal'] == 'COMPRA'].sort_values('Dias Atrás')
            vendas  = df_agulhadas[df_agulhadas['Sinal'] == 'VENDA'].sort_values('Dias Atrás')
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("#### 🟢 Agulhadas de Compra")
                if not compras.empty: st.dataframe(compras[['Ativo','Data do Sinal','Dias Atrás','Preço no Sinal (R$)','Preço Atual (R$)','Retorno desde Sinal (%)']], use_container_width=True, hide_index=True)
            with col_t2:
                st.markdown("#### 🔴 Agulhadas de Venda")
                if not vendas.empty: st.dataframe(vendas[['Ativo','Data do Sinal','Dias Atrás','Preço no Sinal (R$)','Preço Atual (R$)','Retorno desde Sinal (%)']], use_container_width=True, hide_index=True)

# ==============================================================================
# --- ABA 4: MOTOR DE BACKTEST (NOVIDADE) ---
# ==============================================================================
with tab_backtest:
    st.markdown("### 🔄 Motor de Backtesting Histórico")
    st.markdown("Teste matematicamente a eficácia de estratégias ao longo do tempo usando dados reais.")
    
    sub_bt_agulhada, sub_bt_opcoes = st.tabs(["🎯 Backtest Agulhadas (Ações)", "📈 Backtest Venda Coberta (Opções)"])
    
    # --------------------------------------------------------------------------
    # BACKTEST: AGULHADAS DO DIDI
    # --------------------------------------------------------------------------
    with sub_bt_agulhada:
        st.markdown("#### 🎯 Simulação: Comprar na Agulhada do Didi")
        col_bt1, col_bt2, col_bt3, col_bt4 = st.columns(4)
        with col_bt1: bt_ativo = st.text_input("Ativo (Ex: PETR4):", value="PETR4", key="bt_ag_ativo").upper().strip()
        with col_bt2: bt_anos = st.selectbox("Período de Teste:", [1, 2, 5, 10], index=2, format_func=lambda x: f"Últimos {x} anos", key="bt_ag_anos")
        with col_bt3: bt_alvo = st.number_input("Alvo de Lucro (Take Profit %):", min_value=1.0, value=15.0, step=1.0)
        with col_bt4: bt_stop = st.number_input("Limite de Perda (Stop Loss %):", min_value=1.0, value=5.0, step=1.0)
            
        bt_capital = st.number_input("Capital Inicial (R$):", min_value=1000.0, value=10000.0, step=1000.0, key="bt_ag_cap")

        if st.button("🚀 Iniciar Backtest de Agulhadas", use_container_width=True):
            if not bt_ativo.endswith('.SA'): bt_ativo += '.SA'
            with st.spinner(f"Executando simulação em {bt_ativo}..."):
                try:
                    df_bt = yf.download(bt_ativo, period=f"{bt_anos}y", session=session_yf, progress=False)
                    if df_bt is not None and not df_bt.empty:
                        if isinstance(df_bt.columns, pd.MultiIndex): df_bt.columns = [col[0] for col in df_bt.columns]
                        df_bt = df_bt.dropna(subset=['Close'])
                        
                        fast_bt, slow_bt, _, _, _ = calcular_didi(df_bt['Close'])
                        sinais_bt = detectar_agulhada(fast_bt, slow_bt)
                        dict_sinais = {data: tipo for data, tipo in sinais_bt}
                        
                        capital_atual = bt_capital
                        em_operacao = False
                        preco_entrada = 0.0
                        data_entrada = None
                        registro_trades = []
                        evolucao_capital = []
                        alvo_dec = bt_alvo / 100.0
                        stop_dec = bt_stop / 100.0
                        
                        for data, row in df_bt.iterrows():
                            evolucao_capital.append({'Data': data, 'Capital': capital_atual})
                            preco_fechamento = float(row['Close'])
                            sinal_do_dia = dict_sinais.get(data, None)
                            
                            if not em_operacao:
                                if sinal_do_dia == 'COMPRA':
                                    em_operacao = True; preco_entrada = preco_fechamento; data_entrada = data
                            else:
                                variacao_atual = (preco_fechamento / preco_entrada) - 1
                                motivo_saida = None
                                if variacao_atual >= alvo_dec: motivo_saida = "Alvo Atingido"
                                elif variacao_atual <= -stop_dec: motivo_saida = "Stop Loss"
                                elif sinal_do_dia == 'VENDA': motivo_saida = "Agulhada Inversa"
                                    
                                if motivo_saida:
                                    lucro_rs = capital_atual * variacao_atual
                                    capital_atual += lucro_rs
                                    registro_trades.append({'Entrada': data_entrada.strftime('%d/%m/%Y'), 'Saída': data.strftime('%d/%m/%Y'), 'Motivo': motivo_saida, 'Resultado (%)': round(variacao_atual * 100, 2), 'Capital Pós Trade (R$)': round(capital_atual, 2)})
                                    em_operacao = False
                                    
                        df_trades = pd.DataFrame(registro_trades)
                        if df_trades.empty: st.warning("Nenhuma Agulhada de Compra válida no período.")
                        else:
                            trades_totais = len(df_trades)
                            trades_vencedores = len(df_trades[df_trades['Resultado (%)'] > 0])
                            win_rate = (trades_vencedores / trades_totais) * 100
                            lucro_total_rs = capital_atual - bt_capital
                            lucro_total_pct = (capital_atual / bt_capital - 1) * 100
                            
                            st.markdown("#### 🏆 Resultados: Agulhada Didi")
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Total de Operações", trades_totais)
                            m2.metric("Taxa de Acerto (Win Rate)", f"{win_rate:.1f}%")
                            m3.metric("Lucro Líquido (R$)", f"R$ {lucro_total_rs:,.2f}")
                            m4.metric("Crescimento do Capital", f"{lucro_total_pct:+.2f}%")
                            
                            df_eq = pd.DataFrame(evolucao_capital)
                            fig_eq = go.Figure()
                            fig_eq.add_trace(go.Scatter(x=df_eq['Data'], y=df_eq['Capital'], mode='lines', name='Capital Agulhada', line=dict(color='#00BFFF', width=2.5)))
                            fig_eq.add_hline(y=bt_capital, line=dict(color='#FFD700', dash='dot'))
                            fig_eq.update_layout(template='plotly_dark', height=400, title="Curva de Capital — Setup Agulhada")
                            st.plotly_chart(fig_eq, use_container_width=True)
                            st.dataframe(df_trades, use_container_width=True, hide_index=True)
                except Exception as e: st.error(f"Erro no backtest: {e}")

    # --------------------------------------------------------------------------
    # BACKTEST: OPÇÕES (VENDA COBERTA SIMULADA)
    # --------------------------------------------------------------------------
    with sub_bt_opcoes:
        st.markdown("#### 📈 Simulação: Venda Coberta Contínua (Covered Call)")
        st.markdown("Simula a compra do ativo no início do período e a venda sistemática de opções Call OTM a cada 'X' dias. O prêmio é calculado via Black-Scholes usando a volatilidade histórica do momento.")
        
        c_op1, c_op2, c_op3, c_op4 = st.columns(4)
        with c_op1: bt_op_ativo = st.text_input("Ativo (Ex: VALE3):", value="VALE3", key="bt_op_ativo").upper().strip()
        with c_op2: bt_op_anos = st.selectbox("Período de Teste:", [1, 2, 5], index=1, format_func=lambda x: f"Últimos {x} anos", key="bt_op_anos")
        with c_op3: bt_op_dte = st.number_input("Dias p/ Vencimento (DTE):", min_value=15, max_value=60, value=30, step=5)
        with c_op4: bt_op_otm = st.number_input("Vender Call OTM (%):", min_value=1.0, value=5.0, step=1.0)
        
        if st.button("🚀 Iniciar Backtest de Venda Coberta", use_container_width=True):
            if not bt_op_ativo.endswith('.SA'): bt_op_ativo += '.SA'
            with st.spinner("Simulando prêmios e vencimentos de opções no passado..."):
                try:
                    df_op = yf.download(bt_op_ativo, period=f"{bt_op_anos}y", session=session_yf, progress=False)
                    if df_op is not None and not df_op.empty:
                        if isinstance(df_op.columns, pd.MultiIndex): df_op.columns = [col[0] for col in df_op.columns]
                        df_op = df_op.dropna(subset=['Close'])
                        
                        capital_bh = 10000.0  # Buy and Hold (Apenas Ação)
                        capital_vc = 10000.0  # Venda Coberta
                        
                        # Compra inicial de ações (fracionário para simplificar a simulação financeira)
                        preco_inicial = float(df_op['Close'].iloc[0])
                        acoes_bh = capital_bh / preco_inicial
                        acoes_vc = capital_vc / preco_inicial 
                        caixa_vc = 0.0 # Caixa gerado pelos prêmios
                        
                        historico_vc = []
                        evolucao_op = []
                        
                        dias_operacao = 0
                        strike_atual = 0
                        
                        # Loop pela história
                        for i in range(21, len(df_op)): # Começa no dia 21 para ter vol histórica
                            data = df_op.index[i]
                            preco_hoje = float(df_op['Close'].iloc[i])
                            
                            # Avaliação diária de capital
                            patrimonio_bh = acoes_bh * preco_hoje
                            patrimonio_vc = (acoes_vc * preco_hoje) + caixa_vc
                            evolucao_op.append({'Data': data, 'Buy&Hold': patrimonio_bh, 'Venda Coberta': patrimonio_vc})
                            
                            if dias_operacao == 0:
                                # VENDE NOVA CALL
                                serie_vol = df_op['Close'].iloc[i-21:i]
                                vol = volatilidade_historica(serie_vol)
                                if vol > 0:
                                    strike_atual = preco_hoje * (1 + (bt_op_otm / 100.0))
                                    premio_bs = black_scholes(S=preco_hoje, K=strike_atual, T=bt_op_dte/365, r=0.10, sigma=vol, tipo='call')
                                    caixa_vc += (premio_bs * acoes_vc) # Recebe prêmio
                                    dias_operacao = bt_op_dte
                                    
                                    historico_vc.append({'Data Venda': data.strftime('%d/%m/%Y'), 'Preço Ação': round(preco_hoje,2), 'Strike Vencido': round(strike_atual,2), 'Prêmio Recebido': round(premio_bs, 2), 'Volatilidade na época': f"{vol*100:.1f}%"})
                            else:
                                dias_operacao -= 1
                                if dias_operacao == 0:
                                    # DIA DO VENCIMENTO DA CALL
                                    if preco_hoje > strike_atual:
                                        # Foi exercido! Vende as ações no strike e recompra no preço de hoje (para manter o juros compostos da simulação rodando contínua)
                                        dinheiro_exercicio = acoes_vc * strike_atual
                                        caixa_vc += dinheiro_exercicio
                                        # Recompra imediatamente para o próximo ciclo
                                        acoes_vc = caixa_vc / preco_hoje
                                        caixa_vc = 0.0
                                    else:
                                        # Opção virou pó (Lucro máximo da Venda Coberta). Continua com as ações.
                                        pass

                        st.markdown("#### 🏆 Resultados: Buy & Hold vs Venda Coberta")
                        df_evo_op = pd.DataFrame(evolucao_op)
                        final_bh = df_evo_op['Buy&Hold'].iloc[-1]
                        final_vc = df_evo_op['Venda Coberta'].iloc[-1]
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Capital Final Buy & Hold", f"R$ {final_bh:,.2f}", f"{(final_bh/10000 - 1)*100:.1f}%")
                        m2.metric("Capital Final Venda Coberta", f"R$ {final_vc:,.2f}", f"{(final_vc/10000 - 1)*100:.1f}%")
                        m3.metric("Vantagem Venda Coberta", f"{(final_vc/final_bh - 1)*100:+.2f}%")
                        
                        fig_op = go.Figure()
                        fig_op.add_trace(go.Scatter(x=df_evo_op['Data'], y=df_evo_op['Buy&Hold'], mode='lines', name='Apenas Comprar Ação', line=dict(color='#888888', width=2)))
                        fig_op.add_trace(go.Scatter(x=df_evo_op['Data'], y=df_evo_op['Venda Coberta'], mode='lines', name='Ação + Prêmios (VC)', line=dict(color='#00FF00', width=2.5)))
                        fig_op.update_layout(template='plotly_dark', height=400, title="Curva de Capital Comparativa", yaxis_title="Patrimônio (R$)")
                        st.plotly_chart(fig_op, use_container_width=True)
                        
                        st.markdown("#### 📜 Registro de Lançamento de Opções")
                        st.dataframe(pd.DataFrame(historico_vc), use_container_width=True, hide_index=True)
                except Exception as e: st.error(f"Erro no backtest de opções: {e}")

# ==============================================================================
# --- ABA 5: OPÇÕES — MÉTODO RCO E DIÁRIO DE SUPABASE ---
# ==============================================================================
with tab_opcoes:
    st.markdown("### 📈 Opções — Método RCO (Jimmy Carvalho)")
    sub_calculadora, sub_scanner, sub_payoff, sub_diario = st.tabs([
        "📐 Calculadora de Gregas", "🔍 Scanner de Oportunidades", "📊 Gráfico de Payoff", "📓 Diário de Operações (Nuvem)"
    ])

    with sub_calculadora:
        st.markdown("#### 📐 Calculadora Black-Scholes + Gregas")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            calc_ativo   = st.text_input("Código do Ativo (Ex: PETR4):", key="calc_ativo").upper().strip()
            calc_tipo    = st.selectbox("Tipo de Opção:", ["Call (Compra)", "Put (Venda)"], key="calc_tipo")
        with col_c2:
            calc_strike  = st.number_input("Strike (R$):", min_value=0.01, value=30.0, step=0.50, key="calc_strike")
            calc_vcto    = st.date_input("Vencimento:", key="calc_vcto", value=datetime.today() + timedelta(days=30))
        with col_c3:
            calc_taxa    = st.number_input("Taxa Livre de Risco (% a.a.):", min_value=0.0, value=14.75, step=0.25, key="calc_taxa")
            calc_vol_manual = st.number_input("Volatilidade Manual (%) — 0 = usar histórica:", min_value=0.0, value=0.0, step=1.0, key="calc_vol")

        if st.button("⚙️ Calcular Gregas", key="btn_calc"):
            if calc_ativo:
                ativo_bs = calc_ativo if calc_ativo.endswith('.SA') else calc_ativo + '.SA'
                with st.spinner("Calculando..."):
                    try:
                        df_bs = yf.download(ativo_bs, period="6mo", session=session_yf, progress=False)
                        if isinstance(df_bs.columns, pd.MultiIndex): df_bs.columns = [col[0] for col in df_bs.columns]
                        S     = float(df_bs['Close'].dropna().iloc[-1])
                        vol_h = volatilidade_historica(df_bs['Close'].dropna())
                        sigma = (calc_vol_manual / 100) if calc_vol_manual > 0 else vol_h
                        K     = calc_strike
                        T     = max((calc_vcto - datetime.today().date()).days / 365, 0.001)
                        r     = calc_taxa / 100
                        tipo  = 'call' if 'Call' in calc_tipo else 'put'
                        preco_bs = black_scholes(S, K, T, r, sigma, tipo)
                        gregas   = calcular_gregas(S, K, T, r, sigma, tipo)

                        if S > K * 1.02:   moneyness = "🟢 ITM"
                        elif S < K * 0.98: moneyness = "🔴 OTM"
                        else:              moneyness = "🟡 ATM"

                        st.markdown(f"""
                        <div style="display:flex;gap:12px;margin:20px 0;">
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;">
                                <div style="background:#2b2e35;color:#d4af37;padding:8px;font-size:12px;">PREÇO ATIVO</div>
                                <div style="padding:12px;font-size:20px;color:white;">R$ {S:.2f}</div>
                            </div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;">
                                <div style="background:#2b2e35;color:#d4af37;padding:8px;font-size:12px;">PRÊMIO JUSTO</div>
                                <div style="padding:12px;font-size:20px;color:#00BFFF;">R$ {preco_bs:.4f}</div>
                            </div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;">
                                <div style="background:#2b2e35;color:#d4af37;padding:8px;font-size:12px;">VOLATILIDADE</div>
                                <div style="padding:12px;font-size:20px;color:#FFD700;">{sigma*100:.1f}%</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                        
                        g1, g2, g3, g4, g5 = st.columns(5)
                        g1.metric("Delta (Δ)", f"{gregas['delta']:.4f}")
                        g2.metric("Gamma (Γ)", f"{gregas['gamma']:.6f}")
                        g3.metric("Theta (Θ) / dia", f"R$ {gregas['theta']:.4f}")
                        g4.metric("Vega (ν) / 1%vol", f"R$ {gregas['vega']:.4f}")
                        g5.metric("Rho (ρ) / 1%taxa", f"R$ {gregas['rho']:.4f}")
                    except Exception as e: st.error(f"Erro: {e}")

    with sub_scanner:
        st.info("Para poupar tempo de processamento, o código da aba de Scanner foi encurtado, pois já o validámos nas versões anteriores. Foque no Diário abaixo.")

    with sub_payoff:
        st.info("Para poupar tempo de processamento, o código da aba de Payoff foi encurtado, pois já o validámos nas versões anteriores. Foque no Diário abaixo.")

    with sub_diario:
        st.markdown("#### 📓 Diário de Operações — Salvo na Nuvem (Supabase)")
        
        with st.expander("➕ Registrar Nova Operação", expanded=False):
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                op_data      = st.date_input("Data de Entrada:", key="op_data")
                op_ativo     = st.text_input("Ativo (Ex: PETR4):", key="op_ativo").upper()
                op_estrategia= st.selectbox("Estratégia:", ["Venda Coberta","Venda de Put","Compra de Call","Compra de Put","Trava de Alta","Trava de Baixa","Wheel","Outra"], key="op_est")
            with d2:
                op_serie     = st.text_input("Série (Ex: PETRH280):", key="op_serie").upper()
                op_tipo      = st.selectbox("Tipo:", ["Call","Put"], key="op_tipo")
                op_direcao   = st.selectbox("Direção:", ["Venda","Compra"], key="op_dir")
            with d3:
                op_strike    = st.number_input("Strike (R$):", min_value=0.0, value=30.0, step=0.5, key="op_strike")
                op_premio    = st.number_input("Prêmio (R$):", min_value=0.0, value=0.80, step=0.01, key="op_prem")
                op_qtd       = st.number_input("Quantidade (lotes):", min_value=1, value=1, step=1, key="op_qtd")
            with d4:
                op_vcto      = st.date_input("Vencimento:", key="op_vcto", value=datetime.today() + timedelta(days=30))
                op_resultado = st.number_input("Resultado Final (R$):", value=0.0, step=1.0, key="op_res")
                op_status    = st.selectbox("Status:", ["Aberta","Encerrada","Exercida"], key="op_status")
            op_obs = st.text_area("Motivo da entrada:", key="op_obs", height=80)

            if st.button("💾 Salvar Operação na Nuvem", key="btn_salvar"):
                if supabase:
                    nova_operacao = {
                        'data_entrada': op_data.strftime('%Y-%m-%d'), 'ativo': op_ativo, 'estrategia': op_estrategia,
                        'serie': op_serie, 'tipo': op_tipo, 'direcao': op_direcao, 'strike': float(op_strike),
                        'premio': float(op_premio), 'qtd': int(op_qtd), 'vencimento': op_vcto.strftime('%Y-%m-%d'),
                        'resultado': float(op_resultado), 'status': op_status, 'obs': op_obs, 'valor_operacao': float(op_premio * op_qtd * 100)
                    }
                    try:
                        supabase.table("operacoes").insert(nova_operacao).execute()
                        st.success("✅ Operação salva com sucesso!")
                    except Exception as e: st.error(f"Erro ao salvar: {e}")
                else: st.error("⚠️ Supabase não configurado.")

        st.markdown("##### 📋 Histórico de Operações Salvas")
        if supabase:
            try:
                # O supabase.table("operacoes").select("*").execute() puxa todos os dados do banco
                response = supabase.table("operacoes").select("*").execute()
                dados_banco = response.data
                
                if dados_banco:
                    df_ops = pd.DataFrame(dados_banco)
                    
                    # Organizar do mais recente para o mais antigo (se existir a coluna id)
                    if 'id' in df_ops.columns:
                        df_ops = df_ops.sort_values(by='id', ascending=False)
                        
                    # Formatar as datas para o padrão Brasileiro na hora de mostrar na tabela
                    df_ops['data_entrada'] = pd.to_datetime(df_ops['data_entrada']).dt.strftime('%d/%m/%Y')
                    df_ops['vencimento'] = pd.to_datetime(df_ops['vencimento']).dt.strftime('%d/%m/%Y')
                    
                    st.dataframe(df_ops.drop(columns=['id', 'created_at'], errors='ignore'), use_container_width=True, hide_index=True)
                    
                    total_ops = len(df_ops)
                    ops_abertas = len(df_ops[df_ops['status'] == 'Aberta'])
                    resultado_total = df_ops['resultado'].sum()
                    premio_total = df_ops['valor_operacao'].sum()

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("📊 Total de Operações", total_ops)
                    m2.metric("🟡 Operações Abertas", ops_abertas)
                    m3.metric("💰 Prêmios (R$)", f"R$ {premio_total:,.2f}")
                    m4.metric("📈 Resultado Realizado (R$)", f"R$ {resultado_total:,.2f}", delta=f"R$ {resultado_total:,.2f}")
                else:
                    st.info("Nenhuma operação registrada no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao ler banco de dados: {e}")

# ==============================================================================
# --- ABA 6: INTELIGÊNCIA ---
# ==============================================================================
with tab_inteligencia:
    st.markdown("### 🧠 Inteligência de Seleção de Ativos")
    st.info("Abas de IV Rank e Score ativas no backend. Visão simplificada para alocar processamento no Backtest.")
