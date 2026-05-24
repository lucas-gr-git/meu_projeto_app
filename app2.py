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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Terminal B3", layout="wide", page_icon="📊")

# ==============================================================================
# --- SISTEMA DE LOGIN ---
# ==============================================================================
USUARIOS_CADASTRADOS = {
    "lucas@provedor.com.br": "senha123",
    "visitante@email.com": "acesso2026",
    "amigo@email.com": "123456"
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
# --- CÓDIGO PRINCIPAL ---
# ==============================================================================
st.title("🖥️ Terminal Profissional de Inteligência Mercado - B3")
st.markdown("Monitoramento Avançado, Análise Técnica, Fundamentalista e Notícias em Tempo Real.")

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

@st.cache_data(ttl=300)
def carregar_dados(ativos, dias):
    hoje = datetime.today().strftime('%Y-%m-%d')
    inicio = (datetime.today() - timedelta(days=dias)).strftime('%Y-%m-%d')
    dados = yf.download(ativos, start=inicio, end=hoje)
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

def fmt_br(val, is_pct=False, currency=False):
    if pd.isna(val) or val is None or val == "-": return "-"
    texto = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{texto}%"
    if currency: return f"R$ {texto}"
    return texto

def cor_variacao(val):
    if pd.isna(val) or val == "-": return "#2b2e35"
    return "#228B22" if val > 0 else "#B22222" if val < 0 else "#2b2e35"

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
        f_ant = fast.iloc[i-1]; f_at = fast.iloc[i]; s_at = slow.iloc[i]
        if pd.isna(f_at) or pd.isna(s_at) or pd.isna(f_ant): continue
        if f_ant < 0 and f_at > 0 and s_at < 0: sinais.append((fast.index[i], 'COMPRA'))
        elif f_ant > 0 and f_at < 0 and s_at > 0: sinais.append((fast.index[i], 'VENDA'))
    return sinais

def black_scholes(S, K, T, r, sigma, tipo='call'):
    if T <= 0 or sigma <= 0: return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if tipo == 'call': preco = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else: preco = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return round(preco, 4)

def calcular_gregas(S, K, T, r, sigma, tipo='call'):
    if T <= 0 or sigma <= 0: return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    nd1 = norm.pdf(d1)
    if tipo == 'call':
        delta = norm.cdf(d1); rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
        theta = (-(S * nd1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1; rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
        theta = (-(S * nd1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
    gamma = nd1 / (S * sigma * math.sqrt(T)); vega = S * nd1 * math.sqrt(T) / 100
    return {'delta': round(delta, 4), 'gamma': round(gamma, 6), 'theta': round(theta, 4), 'vega': round(vega, 4), 'rho': round(rho, 4)}

def volatilidade_historica(serie, janela=21):
    retornos = np.log(serie / serie.shift(1)).dropna()
    return float(retornos.rolling(janela).std().iloc[-1] * math.sqrt(252))

precos_fechamento, dados_completos = carregar_dados(ativos_lista, 365)

resultados = []
for ativo in ativos_lista:
    df = pd.DataFrame()
    if ativo in precos_fechamento.columns:
        df['Close'] = precos_fechamento[ativo]
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA100'] = df['Close'].rolling(window=100).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        delta_r = df['Close'].diff()
        ganho = (delta_r.where(delta_r > 0, 0)).rolling(window=14).mean()
        perda = (-delta_r.where(delta_r < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df['RSI'] = 100 - (100 / (1 + rs))
        ultimo_preco = float(df['Close'].dropna().iloc[-1]) if not df['Close'].dropna().empty else 0
        sma50 = float(df['SMA50'].dropna().iloc[-1]) if not df['SMA50'].dropna().empty else 0
        sma100 = float(df['SMA100'].dropna().iloc[-1]) if not df['SMA100'].dropna().empty else 0
        sma200 = float(df['SMA200'].dropna().iloc[-1]) if not df['SMA200'].dropna().empty else 0
        rsi = float(df['RSI'].dropna().iloc[-1]) if not df['RSI'].dropna().empty else np.nan
        variacao_diaria = float(df['Close'].dropna().pct_change().iloc[-1] * 100) if len(df['Close'].dropna()) > 1 else 0.0
        tendencia_curta = 'Alta' if ultimo_preco > sma50 else 'Baixa'
        tendencia_media = 'Alta' if ultimo_preco > sma100 else 'Baixa'
        tendencia_longa = 'Alta' if ultimo_preco > sma200 else 'Baixa' if sma200 > 0 else 'N/A'
        sentimento = 'Sobrecomprado' if rsi > 70 else 'Sobrevendido' if rsi < 30 else 'Neutro'
        resultados.append({'Ativo': ativo.replace('.SA', ''), 'Setor': ativos_setores[ativo], 'Preço (R$)': round(ultimo_preco, 2),
            'Variação (%)': round(variacao_diaria, 2), 'Tendência Curta (50D)': tendencia_curta,
            'Tendência Média (100D)': tendencia_media, 'Tendência Longa (200D)': tendencia_longa, 'Sentimento': sentimento})

df_resumo = pd.DataFrame(resultados)

# ==============================================================================
# ABAS
# ==============================================================================
tab_visao_geral, tab_analise_individual, tab_agulhadas, tab_opcoes, tab_inteligencia, tab_backtest = st.tabs([
    "🌐 Visão Geral do Mercado",
    "🔬 Análise Detalhada por Ativo",
    "🎯 Agulhadas do Didi",
    "📈 Opções — Método RCO",
    "🧠 Inteligência de Seleção",
    "⚙️ Motor de Backtest"
])

# ==============================================================================
# ABA 1: VISÃO GERAL
# ==============================================================================
with tab_visao_geral:
    st.markdown("### 📊 Mapa de Calor do Mercado")
    ids, labels, parents, values, colors, customdata = ["B3"], ["B3"], [""], [0], ["#2b2e35"], [["<b>Painel Geral B3</b>", "<b>B3</b>"]]
    for setor in df_resumo['Setor'].unique():
        ids.append(setor); labels.append(setor); parents.append("B3"); values.append(0); colors.append("#2b2e35")
        customdata.append([f"<b>Setor: {setor}</b>", f"<b>{setor}</b>"])
        ids.append(setor + "_fantasma"); labels.append(""); parents.append(setor); values.append(0.000001); colors.append("#2b2e35"); customdata.append(["", ""])
    for _, row in df_resumo.iterrows():
        ids.append(row['Ativo']); labels.append(row['Ativo']); parents.append(row['Setor']); values.append(1)
        var = row['Variação (%)']; preco = row['Preço (R$)']
        colors.append("#228B22" if var > 0.05 else "#B22222" if var < -0.05 else "#708090")
        preco_br = fmt_br(preco); var_br = f"{var:+.2f}%".replace(".", ",")
        hover = f"<b>{row['Ativo']}</b><br>Variação: {var_br}<br>Preço: R$ {preco_br}<br><br>Curta: {row['Tendência Curta (50D)']}<br>Média: {row['Tendência Média (100D)']}<br>Longa: {row['Tendência Longa (200D)']}"
        block = f"<b>{row['Ativo']}</b><br>R$ {preco_br}<br> {var_br}"
        customdata.append([hover, block])
    fig_treemap = go.Figure(go.Treemap(ids=ids, labels=labels, parents=parents, values=values, marker_colors=colors,
        customdata=customdata, texttemplate="%{customdata[1]}", hovertemplate="%{customdata[0]}<extra></extra>", textfont=dict(color="black")))
    fig_treemap.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=550, template='plotly_dark')
    st.plotly_chart(fig_treemap, use_container_width=True)
    st.subheader("📋 Resumo de Indicadores da Grade")
    col_filtro, _ = st.columns([1, 2])
    with col_filtro:
        setor_selecionado = st.selectbox("Filtrar Tabela:", ["Todos os Setores"] + sorted(list(df_resumo['Setor'].unique())))
    df_exibicao = df_resumo if setor_selecionado == "Todos os Setores" else df_resumo[df_resumo['Setor'] == setor_selecionado]
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

# ==============================================================================
# ABA 2: ANÁLISE DETALHADA
# ==============================================================================
with tab_analise_individual:
    col_busca, col_tempo = st.columns([1, 1])
    with col_busca:
        ativo_buscado = st.text_input("🔍 Digite o código do ativo (Ex: PETR4, MGLU3, AAPL):", key="search_asset").upper().strip()
    if ativo_buscado:
        if not ativo_buscado.endswith('.SA') and any(char.isdigit() for char in ativo_buscado):
            ativo_buscado += '.SA'
        with col_tempo:
            janela_tempo = st.radio("Período do Gráfico:", ["1 Mês", "6 Meses", "1 Ano", "2 Anos", "5 Anos"], index=2, horizontal=True)
            mapa_periodos = {"1 Mês": "1mo", "6 Meses": "6mo", "1 Ano": "1y", "2 Anos": "2y", "5 Anos": "5y"}
            periodo_selecionado = mapa_periodos[janela_tempo]
        with st.spinner("Processando histórico de 10 anos e fundamentos..."):
            ticker_obj = yf.Ticker(ativo_buscado)
            df_hist = yf.download(ativo_buscado, period="10y")
            if df_hist.empty:
                st.error("⚠️ Código não encontrado no banco de dados.")
            else:
                if isinstance(df_hist.columns, pd.MultiIndex): df_hist.columns = df_hist.columns.droplevel(1)
                preco_atual = float(df_hist['Close'].iloc[-1])
                def calc_retorno(df, dias_uteis):
                    if len(df) > dias_uteis:
                        preco_antigo = float(df['Close'].iloc[-dias_uteis])
                        return ((preco_atual / preco_antigo) - 1) * 100
                    return "-"
                ret_1m = calc_retorno(df_hist, 21); ret_3m = calc_retorno(df_hist, 63)
                ret_1a = calc_retorno(df_hist, 252); ret_2a = calc_retorno(df_hist, 504)
                ret_5a = calc_retorno(df_hist, 1260); ret_10a = calc_retorno(df_hist, 2520)
                info = {}
                try: info = ticker_obj.info
                except: pass
                val_var12m = ret_1a if ret_1a != "-" else info.get('52WeekChange', "-")
                val_pl = info.get('trailingPE') or info.get('forwardPE') or "-"
                val_pvp = info.get('priceToBook', "-")
                val_dy = info.get('trailingAnnualDividendYield') or info.get('dividendYield')
                if val_dy: val_dy = val_dy * 100
                else:
                    div_anual = info.get('trailingAnnualDividendRate') or info.get('dividendRate')
                    val_dy = (div_anual / preco_atual) * 100 if div_anual and preco_atual > 0 else "-"
                st.markdown(f"""<div style="display:flex;gap:15px;margin-bottom:20px;">
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">COTAÇÃO</div><div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(preco_atual, currency=True)}</div></div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">VARIAÇÃO (12M)</div><div style="padding:15px;font-size:22px;font-weight:bold;color:{cor_variacao(val_var12m)};">{fmt_br(val_var12m, is_pct=True)}</div></div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">P/L</div><div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_pl)}</div></div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">P/VP</div><div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_pvp)}</div></div>
                    <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">DY (12M)</div><div style="padding:15px;font-size:22px;font-weight:bold;color:white;">{fmt_br(val_dy, is_pct=True)}</div></div>
                </div>""", unsafe_allow_html=True)
                st.markdown(f"""<div style="border:1px solid #333;border-radius:8px;background:#1e1e1e;padding:15px;margin-bottom:15px;">
                    <div style="font-weight:bold;margin-bottom:15px;color:white;">📈 Rentabilidade Histórica</div>
                    <table style="width:100%;text-align:center;border-collapse:collapse;">
                        <tr style="color:#aaaaaa;font-size:14px;border-bottom:1px solid #333;"><th style="padding:10px;text-align:left;">Indicador</th><th style="padding:10px;">1 mês</th><th style="padding:10px;">3 meses</th><th style="padding:10px;">1 ano</th><th style="padding:10px;">2 anos</th><th style="padding:10px;">5 anos</th><th style="padding:10px;">10 anos</th></tr>
                        <tr style="font-size:16px;font-weight:bold;background:#252525;"><td style="padding:15px;text-align:left;color:white;">Rentabilidade</td>
                        <td style="color:{cor_variacao(ret_1m)};">{fmt_br(ret_1m, is_pct=True)}</td><td style="color:{cor_variacao(ret_3m)};">{fmt_br(ret_3m, is_pct=True)}</td>
                        <td style="color:{cor_variacao(ret_1a)};">{fmt_br(ret_1a, is_pct=True)}</td><td style="color:{cor_variacao(ret_2a)};">{fmt_br(ret_2a, is_pct=True)}</td>
                        <td style="color:{cor_variacao(ret_5a)};">{fmt_br(ret_5a, is_pct=True)}</td><td style="color:{cor_variacao(ret_10a)};">{fmt_br(ret_10a, is_pct=True)}</td></tr>
                    </table></div>""", unsafe_allow_html=True)
                csv_data = df_hist.to_csv().encode('utf-8')
                st.download_button(label="📥 Baixar Histórico Completo (.CSV)", data=csv_data, file_name=f"{ativo_buscado}_historico.csv", mime="text/csv")
                st.markdown("<br>", unsafe_allow_html=True)
                df_hist['SMA50'] = df_hist['Close'].rolling(window=50).mean()
                df_hist['SMA100'] = df_hist['Close'].rolling(window=100).mean()
                df_hist['SMA200'] = df_hist['Close'].rolling(window=200).mean()
                limite_data = datetime.now() - (timedelta(days=30) if janela_tempo=="1 Mês" else timedelta(days=180) if janela_tempo=="6 Meses" else timedelta(days=365) if janela_tempo=="1 Ano" else timedelta(days=730) if janela_tempo=="2 Anos" else timedelta(days=1825))
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
                    if not noticias: st.info("Nenhuma notícia recente encontrada.")
                    else:
                        for n in noticias:
                            st.markdown(f"""<div style="border:1px solid #444;border-radius:5px;padding:10px;margin-bottom:12px;background:#1e1e1e;"><a href="{n['link']}" target="_blank" style="color:#00BFFF;text-decoration:none;font-weight:bold;font-size:14px;">{n['title']}</a><p style="color:#888;font-size:11px;margin:5px 0 0 0;">{n['publisher']} • {n['time']}</p></div>""", unsafe_allow_html=True)
            st.divider()
            st.markdown("### 📊 Comparativo de Desempenho e Benchmarks")
            benchmarks_selecionados = ['IBOV','IFIX','SMLL','IDIV','IVVB11','CDI','IPCA']
            with st.spinner("Calculando Benchmarks..."):
                fig_bench = go.Figure()
                if not df_plot.empty:
                    primeiro_preco_ativo = float(df_plot['Close'].iloc[0])
                    ativo_norm = (df_plot['Close'] / primeiro_preco_ativo - 1) * 100
                    fig_bench.add_trace(go.Scatter(x=ativo_norm.index, y=ativo_norm, mode='lines', name=ativo_buscado, line=dict(color='#00BFFF', width=2.5)))
                mapa_yf = {'IBOV':'^BVSP','IFIX':'XFIX11.SA','SMLL':'SMAL11.SA','IDIV':'DIVO11.SA','IVVB11':'IVVB11.SA'}
                cores_bench = {'IBOV':'white','IFIX':'#32CD32','SMLL':'#FFD700','IDIV':'#FF69B4','IVVB11':'#FFA500','CDI':'#87CEFA','IPCA':'#FF6347'}
                data_inicio_yf = limite_data.strftime('%Y-%m-%d'); data_inicio_bcb = limite_data.strftime('%d/%m/%Y')
                for b in benchmarks_selecionados:
                    cor = cores_bench.get(b, 'white')
                    if b in mapa_yf:
                        df_b = yf.download(mapa_yf[b], start=data_inicio_yf)
                        if not df_b.empty:
                            if isinstance(df_b.columns, pd.MultiIndex): df_b.columns = df_b.columns.droplevel(1)
                            df_b_plot = df_b[df_b.index >= limite_data]
                            if not df_b_plot.empty:
                                p_preco = float(df_b_plot['Close'].iloc[0]); b_norm = (df_b_plot['Close'] / p_preco - 1) * 100
                                fig_bench.add_trace(go.Scatter(x=b_norm.index, y=b_norm, mode='lines', name=b, line=dict(color=cor, width=1.5, dash='dot' if b=='IBOV' else 'solid')))
                    elif b == 'CDI':
                        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_inicio_bcb}"
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as res: data = json.loads(res.read().decode('utf-8'))
                            df_cdi = pd.DataFrame(data); df_cdi['data'] = pd.to_datetime(df_cdi['data'], format='%d/%m/%Y'); df_cdi.set_index('data', inplace=True); df_cdi['valor'] = df_cdi['valor'].astype(float)
                            cdi_acumulado = ((1 + df_cdi['valor']/100).cumprod() - 1) * 100
                            fig_bench.add_trace(go.Scatter(x=cdi_acumulado.index, y=cdi_acumulado, mode='lines', name='CDI', line=dict(color=cor, width=1.5)))
                        except: pass
                    elif b == 'IPCA':
                        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={data_inicio_bcb}"
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as res: data = json.loads(res.read().decode('utf-8'))
                            df_ipca = pd.DataFrame(data); df_ipca['data'] = pd.to_datetime(df_ipca['data'], format='%d/%m/%Y'); df_ipca.set_index('data', inplace=True); df_ipca['valor'] = df_ipca['valor'].astype(float)
                            ipca_acumulado = ((1 + df_ipca['valor']/100).cumprod() - 1) * 100
                            idx = pd.date_range(start=ipca_acumulado.index[0], end=datetime.today()); ipca_acumulado = ipca_acumulado.reindex(idx, method='ffill')
                            fig_bench.add_trace(go.Scatter(x=ipca_acumulado.index, y=ipca_acumulado, mode='lines', name='IPCA', line=dict(color=cor, width=1.5)))
                        except: pass
                fig_bench.update_layout(template='plotly_dark', height=450, yaxis_title="Desempenho Acumulado (%)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_bench, use_container_width=True)
            st.divider()
            st.markdown("### 📅 Calendário de Eventos Corporativos")
            def buscar_dividendos_yf(t):
                try:
                    dividendos = t.dividends
                    if dividendos.empty: return None, None, None, None
                    dividendos.index = dividendos.index.tz_localize(None)
                    ultimo = dividendos.iloc[-1]; data_com = dividendos.index[-1].strftime('%d/%m/%Y')
                    valor = f"R$ {ultimo:,.4f}".replace(',','X').replace('.', ',').replace('X','.')
                    return 'Dividendo/JCP', data_com, "—", valor
                except: return None, None, None, None
            def buscar_historico_proventos_yf(t):
                try:
                    dividendos = t.dividends
                    if dividendos.empty: return pd.DataFrame()
                    dividendos.index = dividendos.index.tz_localize(None)
                    df_prov = dividendos.reset_index(); df_prov.columns = ['Data Com','Valor (R$)']
                    df_prov['Data Com'] = pd.to_datetime(df_prov['Data Com']).dt.strftime('%d/%m/%Y')
                    df_prov['Valor (R$)'] = df_prov['Valor (R$)'].apply(lambda x: f"R$ {x:,.4f}".replace(',','X').replace('.', ',').replace('X','.'))
                    df_prov['Tipo'] = 'Dividendo/JCP'
                    return df_prov[['Tipo','Data Com','Valor (R$)']].iloc[::-1].reset_index(drop=True)
                except: return pd.DataFrame()
            with st.spinner("Buscando eventos..."): tipo_div, data_com_b3, data_pgto, valor_div = buscar_dividendos_yf(ticker_obj)
            c_ev1, c_ev2, c_ev3 = st.columns(3)
            with c_ev1: st.markdown(f"""<div style="border:1px solid #333;border-radius:8px;background:#1e1e1e;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">📅 Tipo de Provento</div><div style="padding:15px;color:white;font-size:18px;font-weight:bold;">{tipo_div or "—"}</div><div style="padding:0 15px 10px;color:#888;font-size:12px;">Fonte: Yahoo Finance</div></div>""", unsafe_allow_html=True)
            with c_ev2: st.markdown(f"""<div style="border:1px solid #333;border-radius:8px;background:#1e1e1e;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">💰 Data Com (Último Evento)</div><div style="padding:15px;color:#32CD32;font-size:18px;font-weight:bold;">{data_com_b3 or "Não disponível"}</div><div style="padding:0 15px 10px;color:#888;font-size:12px;">Valor: {valor_div or "—"}</div></div>""", unsafe_allow_html=True)
            with c_ev3: st.markdown(f"""<div style="border:1px solid #333;border-radius:8px;background:#1e1e1e;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:13px;">🏦 Data de Pagamento</div><div style="padding:15px;color:#00BFFF;font-size:18px;font-weight:bold;">{data_pgto or "Não disponível"}</div><div style="padding:0 15px 10px;color:#888;font-size:12px;">Fonte: Yahoo Finance</div></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📋 Histórico de Proventos")
            df_proventos = buscar_historico_proventos_yf(ticker_obj)
            if not df_proventos.empty: st.dataframe(df_proventos, use_container_width=True, hide_index=True)
            else: st.info("Nenhum provento encontrado para este ativo.")

# ==============================================================================
# ABA 3: AGULHADAS DO DIDI
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
            sinais = detectar_agulhada(fast, slow)
            corte = pd.Timestamp.now() - pd.Timedelta(days=dias_scanner)
            sinais_recentes = [(d, t) for d, t in sinais if d >= corte]
            if sinais_recentes:
                ultimo_sinal_data, ultimo_sinal_tipo = sinais_recentes[-1]
                dias_atras = (pd.Timestamp.now() - ultimo_sinal_data).days
                serie_apos = serie[serie.index >= ultimo_sinal_data]
                preco_sinal = float(serie_apos.iloc[0]) if not serie_apos.empty else 0
                preco_atual_ag = float(serie.iloc[-1])
                retorno = ((preco_atual_ag / preco_sinal) - 1) * 100 if preco_sinal > 0 else 0
                resultados_agulhada.append({'Ativo': ativo.replace('.SA',''), 'Setor': ativos_setores[ativo], 'Sinal': ultimo_sinal_tipo,
                    'Data do Sinal': ultimo_sinal_data.strftime('%d/%m/%Y'), 'Dias Atrás': dias_atras,
                    'Preço no Sinal (R$)': round(preco_sinal, 2), 'Preço Atual (R$)': round(preco_atual_ag, 2),
                    'Retorno desde Sinal (%)': round(retorno, 2), 'Total de Sinais': len(sinais_recentes)})
    df_agulhadas = pd.DataFrame(resultados_agulhada)
    if df_agulhadas.empty:
        st.warning("Nenhuma agulhada encontrada no período selecionado.")
    else:
        total_compra = len(df_agulhadas[df_agulhadas['Sinal'] == 'COMPRA']); total_venda = len(df_agulhadas[df_agulhadas['Sinal'] == 'VENDA'])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Ativos com Sinal", len(df_agulhadas)); m2.metric("🟢 Agulhadas de Compra", total_compra)
        m3.metric("🔴 Agulhadas de Venda", total_venda); m4.metric("⚖️ Saldo (C - V)", total_compra - total_venda)
        st.markdown("<br>", unsafe_allow_html=True)
        compras = df_agulhadas[df_agulhadas['Sinal'] == 'COMPRA'].sort_values('Dias Atrás')
        vendas = df_agulhadas[df_agulhadas['Sinal'] == 'VENDA'].sort_values('Dias Atrás')
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("#### 🟢 Agulhadas de Compra")
            if not compras.empty: st.dataframe(compras[['Ativo','Setor','Data do Sinal','Dias Atrás','Preço no Sinal (R$)','Preço Atual (R$)','Retorno desde Sinal (%)']], use_container_width=True, hide_index=True)
            else: st.info("Nenhuma agulhada de compra no período.")
        with col_t2:
            st.markdown("#### 🔴 Agulhadas de Venda")
            if not vendas.empty: st.dataframe(vendas[['Ativo','Setor','Data do Sinal','Dias Atrás','Preço no Sinal (R$)','Preço Atual (R$)','Retorno desde Sinal (%)']], use_container_width=True, hide_index=True)
            else: st.info("Nenhuma agulhada de venda no período.")
        st.divider()
        st.markdown("### 🔬 Análise Individual do Sinal")
        ativos_com_sinal = df_agulhadas['Ativo'].tolist()
        ativo_ag = st.selectbox("Selecione o ativo para ver o gráfico com os sinais:", ativos_com_sinal)
        if ativo_ag:
            ativo_ag_full = ativo_ag + '.SA'
            df_ag_hist = yf.download(ativo_ag_full, period="1y")
            if not df_ag_hist.empty:
                if isinstance(df_ag_hist.columns, pd.MultiIndex): df_ag_hist.columns = df_ag_hist.columns.droplevel(1)
                fast_ag, slow_ag, sma3_ag, sma8_ag, sma20_ag = calcular_didi(df_ag_hist['Close'])
                sinais_ag = detectar_agulhada(fast_ag, slow_ag)
                fig_ag = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.55, 0.25, 0.20],
                    subplot_titles=(f'Preço {ativo_ag} com Agulhadas', 'Didi Index (Fast e Slow)', 'DMI / ADX (8)'))
                fig_ag.add_trace(go.Candlestick(x=df_ag_hist.index, open=df_ag_hist['Open'], high=df_ag_hist['High'], low=df_ag_hist['Low'], close=df_ag_hist['Close'], name='Preço', increasing_line_color='#228B22', decreasing_line_color='#B22222'), row=1, col=1)
                for s, c, n in zip([sma3_ag, sma8_ag, sma20_ag], ['#00BFFF','#FFD700','#FF69B4'], ['SMA3','SMA8','SMA20']):
                    fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=s, mode='lines', name=n, line=dict(color=c, width=1.2)), row=1, col=1)
                for data_s, tipo_s in sinais_ag:
                    if data_s not in df_ag_hist.index: continue
                    preco_s = float(df_ag_hist.loc[data_s, 'Low']) if tipo_s == 'COMPRA' else float(df_ag_hist.loc[data_s, 'High'])
                    cor_s = '#00FF00' if tipo_s == 'COMPRA' else '#FF0000'
                    simbolo = 'triangle-up' if tipo_s == 'COMPRA' else 'triangle-down'
                    fig_ag.add_trace(go.Scatter(x=[data_s], y=[preco_s], mode='markers', marker=dict(symbol=simbolo, size=14, color=cor_s, line=dict(color='white', width=1)), name=f'Agulhada {tipo_s}', showlegend=True), row=1, col=1)
                fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=fast_ag, mode='lines', name='Didi Rápida (3)', line=dict(color='#00BFFF', width=1.5)), row=2, col=1)
                fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=slow_ag, mode='lines', name='Didi Lenta (20)', line=dict(color='#FFD700', width=1.5)), row=2, col=1)
                fig_ag.add_hline(y=0, line=dict(color='white', dash='dot', width=1), row=2, col=1)
                tr1_ag = df_ag_hist['High'] - df_ag_hist['Low']; tr2_ag = (df_ag_hist['High'] - df_ag_hist['Close'].shift(1)).abs(); tr3_ag = (df_ag_hist['Low'] - df_ag_hist['Close'].shift(1)).abs()
                tr_ag = pd.concat([tr1_ag, tr2_ag, tr3_ag], axis=1).max(axis=1)
                up_ag = df_ag_hist['High'] - df_ag_hist['High'].shift(1); dn_ag = df_ag_hist['Low'].shift(1) - df_ag_hist['Low']
                pdm_ag = pd.Series(np.where((up_ag > dn_ag) & (up_ag > 0), up_ag, 0), index=df_ag_hist.index)
                ndm_ag = pd.Series(np.where((dn_ag > up_ag) & (dn_ag > 0), dn_ag, 0), index=df_ag_hist.index)
                tr8_ag = tr_ag.rolling(8).sum(); pdi_ag = 100 * pdm_ag.rolling(8).sum() / tr8_ag; ndi_ag = 100 * ndm_ag.rolling(8).sum() / tr8_ag
                adx_ag = (100 * (np.abs(pdi_ag - ndi_ag) / (pdi_ag + ndi_ag))).rolling(8).mean()
                fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=adx_ag, mode='lines', name='ADX', line=dict(color='white', width=1.5)), row=3, col=1)
                fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=pdi_ag, mode='lines', name='+DI', line=dict(color='#00BFFF', width=1.5)), row=3, col=1)
                fig_ag.add_trace(go.Scatter(x=df_ag_hist.index, y=ndi_ag, mode='lines', name='-DI', line=dict(color='#FFD700', width=1.5)), row=3, col=1)
                fig_ag.update_layout(template='plotly_dark', height=850, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig_ag.update_xaxes(rangeslider_visible=False)
                st.plotly_chart(fig_ag, use_container_width=True)
                st.markdown("#### 📐 Bandas de Bollinger (20, 2) — Padrão Didi Aguiar")
                sma20_bb = df_ag_hist['Close'].rolling(20).mean(); std20_bb = df_ag_hist['Close'].rolling(20).std()
                bb_upper = sma20_bb + 2 * std20_bb; bb_lower = sma20_bb - 2 * std20_bb; bb_width = ((bb_upper - bb_lower) / sma20_bb) * 100
                fig_bb = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25], subplot_titles=(f'Bandas de Bollinger — {ativo_ag}', 'Largura das Bandas (%)'))
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index, y=bb_upper, mode='lines', name='Banda Superior', line=dict(color='rgba(255,165,0,0.8)', width=1.5)), row=1, col=1)
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index, y=bb_lower, mode='lines', name='Banda Inferior', line=dict(color='rgba(255,165,0,0.8)', width=1.5), fill='tonexty', fillcolor='rgba(255,165,0,0.06)'), row=1, col=1)
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index, y=sma20_bb, mode='lines', name='SMA20 (Base)', line=dict(color='#FFD700', width=1.5, dash='dot')), row=1, col=1)
                fig_bb.add_trace(go.Candlestick(x=df_ag_hist.index, open=df_ag_hist['Open'], high=df_ag_hist['High'], low=df_ag_hist['Low'], close=df_ag_hist['Close'], name='Preço', increasing_line_color='#228B22', decreasing_line_color='#B22222'), row=1, col=1)
                toque_superior = df_ag_hist['High'] >= bb_upper; toque_inferior = df_ag_hist['Low'] <= bb_lower
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index[toque_superior], y=bb_upper[toque_superior], mode='markers', name='Toque Superior', marker=dict(symbol='circle', size=7, color='#FF4500', line=dict(color='white', width=1))), row=1, col=1)
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index[toque_inferior], y=bb_lower[toque_inferior], mode='markers', name='Toque Inferior', marker=dict(symbol='circle', size=7, color='#00FF7F', line=dict(color='white', width=1))), row=1, col=1)
                fig_bb.add_trace(go.Scatter(x=df_ag_hist.index, y=bb_width, mode='lines', name='Largura (%)', line=dict(color='#87CEFA', width=1.5), fill='tozeroy', fillcolor='rgba(135,206,250,0.08)'), row=2, col=1)
                fig_bb.update_layout(template='plotly_dark', height=650, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig_bb.update_xaxes(rangeslider_visible=False)
                st.plotly_chart(fig_bb, use_container_width=True)
    with st.expander("📖 Como funciona o método Didi Aguiar?"):
        st.markdown("""**🟢 Agulhada de Compra:** Fast cruza o zero para **cima** enquanto Slow ainda está **abaixo** — SMA3 > SMA8 > SMA20.\n**🔴 Agulhada de Venda:** Fast cruza o zero para **baixo** enquanto Slow ainda está **acima** — SMA3 < SMA8 < SMA20.\n> ⚠️ Sempre confirme o sinal com outros indicadores antes de operar.""")

# ==============================================================================
# ABA 4: OPÇÕES
# ==============================================================================
with tab_opcoes:
    st.markdown("### 📈 Opções — Método RCO (Jimmy Carvalho)")
    sub_calculadora, sub_scanner, sub_payoff, sub_diario = st.tabs(["📐 Calculadora de Gregas","🔍 Scanner de Oportunidades","📊 Gráfico de Payoff","📓 Diário de Operações"])
    with sub_calculadora:
        st.markdown("#### 📐 Calculadora Black-Scholes + Gregas")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: calc_ativo = st.text_input("Código do Ativo Objeto (Ex: PETR4):", key="calc_ativo").upper().strip(); calc_tipo = st.selectbox("Tipo de Opção:", ["Call (Compra)", "Put (Venda)"], key="calc_tipo")
        with col_c2: calc_strike = st.number_input("Strike (R$):", min_value=0.01, value=30.0, step=0.50, key="calc_strike"); calc_vcto = st.date_input("Vencimento:", key="calc_vcto", value=datetime.today() + timedelta(days=30))
        with col_c3: calc_taxa = st.number_input("Taxa Livre de Risco (% a.a.):", min_value=0.0, value=14.75, step=0.25, key="calc_taxa"); calc_vol_manual = st.number_input("Volatilidade Manual (% a.a.) — 0 = usar histórica:", min_value=0.0, value=0.0, step=1.0, key="calc_vol")
        if st.button("⚙️ Calcular Gregas", key="btn_calc"):
            if calc_ativo:
                ativo_bs = calc_ativo if calc_ativo.endswith('.SA') else calc_ativo + '.SA'
                with st.spinner("Buscando preço e volatilidade..."):
                    try:
                        df_bs = yf.download(ativo_bs, period="6mo", progress=False)
                        if isinstance(df_bs.columns, pd.MultiIndex): df_bs.columns = df_bs.columns.droplevel(1)
                        S = float(df_bs['Close'].iloc[-1]); vol_h = volatilidade_historica(df_bs['Close'])
                        sigma = (calc_vol_manual / 100) if calc_vol_manual > 0 else vol_h
                        K = calc_strike; T = max((calc_vcto - datetime.today().date()).days / 365, 0.001); r = calc_taxa / 100
                        tipo = 'call' if 'Call' in calc_tipo else 'put'
                        preco_bs = black_scholes(S, K, T, r, sigma, tipo); gregas = calcular_gregas(S, K, T, r, sigma, tipo)
                        if S > K * 1.02: moneyness = "🟢 ITM — In the Money"
                        elif S < K * 0.98: moneyness = "🔴 OTM — Out of the Money"
                        else: moneyness = "🟡 ATM — At the Money"
                        st.markdown(f"""<div style="display:flex;gap:12px;margin:20px 0;">
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:12px;">PREÇO ATIVO</div><div style="padding:12px;font-size:20px;font-weight:bold;color:white;">R$ {S:.2f}</div></div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:12px;">PRÊMIO JUSTO (BS)</div><div style="padding:12px;font-size:20px;font-weight:bold;color:#00BFFF;">R$ {preco_bs:.4f}</div></div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:12px;">VOLATILIDADE USADA</div><div style="padding:12px;font-size:20px;font-weight:bold;color:#FFD700;">{sigma*100:.1f}%</div></div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:12px;">DIAS ATÉ VENC.</div><div style="padding:12px;font-size:20px;font-weight:bold;color:white;">{int(T*365)} dias</div></div>
                            <div style="flex:1;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:8px;font-weight:bold;font-size:12px;">MONEYNESS</div><div style="padding:10px;font-size:13px;font-weight:bold;color:white;">{moneyness}</div></div>
                        </div>""", unsafe_allow_html=True)
                        st.markdown("##### 🔢 Gregas")
                        g1, g2, g3, g4, g5 = st.columns(5)
                        g1.metric("Delta (Δ)", f"{gregas['delta']:.4f}"); g2.metric("Gamma (Γ)", f"{gregas['gamma']:.6f}")
                        g3.metric("Theta (Θ) / dia", f"R$ {gregas['theta']:.4f}"); g4.metric("Vega (ν) / 1%vol", f"R$ {gregas['vega']:.4f}"); g5.metric("Rho (ρ) / 1%taxa", f"R$ {gregas['rho']:.4f}")
                        precos_sim = np.linspace(S * 0.7, S * 1.3, 50); premios_sim = [black_scholes(p, K, T, r, sigma, tipo) for p in precos_sim]
                        fig_sim = go.Figure(); fig_sim.add_trace(go.Scatter(x=precos_sim, y=premios_sim, mode='lines', name='Prêmio BS', line=dict(color='#00BFFF', width=2)))
                        fig_sim.add_vline(x=S, line=dict(color='white', dash='dot'), annotation_text=f"Atual: R${S:.2f}"); fig_sim.add_vline(x=K, line=dict(color='#FFD700', dash='dash'), annotation_text=f"Strike: R${K:.2f}")
                        fig_sim.update_layout(template='plotly_dark', height=350, xaxis_title="Preço do Ativo (R$)", yaxis_title="Prêmio da Opção (R$)"); st.plotly_chart(fig_sim, use_container_width=True)
                    except Exception as e: st.error(f"Erro ao calcular: {e}")
            else: st.warning("Digite o código do ativo.")
    with sub_scanner:
        st.markdown("#### 🔍 Scanner de Oportunidades — Venda Coberta e Venda de Put")
        col_sc1, col_sc2, col_sc3 = st.columns(3)
        with col_sc1: sc_dias_vcto = st.number_input("Dias até vencimento:", min_value=5, max_value=90, value=30, step=5, key="sc_dias")
        with col_sc2: sc_taxa = st.number_input("Taxa livre de risco (% a.a.):", min_value=0.0, value=14.75, step=0.25, key="sc_taxa")
        with col_sc3: sc_otm_pct = st.number_input("OTM Strike (% acima/abaixo do preço):", min_value=1.0, max_value=20.0, value=5.0, step=0.5, key="sc_otm")
        if st.button("🔍 Varrer Oportunidades", key="btn_scan"):
            with st.spinner("Calculando oportunidades em todos os ativos..."):
                scan_resultados = []; T_scan = sc_dias_vcto / 365; r_scan = sc_taxa / 100
                for ativo in ativos_lista:
                    if ativo not in precos_fechamento.columns: continue
                    serie = precos_fechamento[ativo].dropna()
                    if len(serie) < 30: continue
                    try:
                        S = float(serie.iloc[-1]); sigma = volatilidade_historica(serie)
                        if sigma <= 0: continue
                        K_call = round(S * (1 + sc_otm_pct/100), 2); K_put = round(S * (1 - sc_otm_pct/100), 2)
                        premio_call = black_scholes(S, K_call, T_scan, r_scan, sigma, 'call'); premio_put = black_scholes(S, K_put, T_scan, r_scan, sigma, 'put')
                        ret_call = (premio_call / S) * 100; ret_put = (premio_put / S) * 100
                        g_call = calcular_gregas(S, K_call, T_scan, r_scan, sigma, 'call'); g_put = calcular_gregas(S, K_put, T_scan, r_scan, sigma, 'put')
                        scan_resultados.append({'Ativo': ativo.replace('.SA',''), 'Setor': ativos_setores[ativo], 'Preço (R$)': round(S, 2), 'Vol. Hist. (%)': round(sigma*100, 1),
                            'Strike Call': K_call, 'Prêmio Call (R$)': round(premio_call, 4), 'Retorno Call (%)': round(ret_call, 2), 'Delta Call': round(g_call['delta'], 3),
                            'Strike Put': K_put, 'Prêmio Put (R$)': round(premio_put, 4), 'Retorno Put (%)': round(ret_put, 2), 'Delta Put': round(g_put['delta'], 3)})
                    except: continue
                df_scan = pd.DataFrame(scan_resultados)
                if not df_scan.empty:
                    df_scan = df_scan.sort_values('Retorno Call (%)', ascending=False)
                    st.markdown("##### 📞 Melhores Oportunidades — Venda Coberta (Call OTM)")
                    st.dataframe(df_scan[['Ativo','Setor','Preço (R$)','Vol. Hist. (%)','Strike Call','Prêmio Call (R$)','Retorno Call (%)','Delta Call']].head(15), use_container_width=True, hide_index=True)
                    st.markdown("##### 📉 Melhores Oportunidades — Venda de Put (Put OTM)")
                    df_put_sorted = df_scan.sort_values('Retorno Put (%)', ascending=False)
                    st.dataframe(df_put_sorted[['Ativo','Setor','Preço (R$)','Vol. Hist. (%)','Strike Put','Prêmio Put (R$)','Retorno Put (%)','Delta Put']].head(15), use_container_width=True, hide_index=True)
                    fig_sc = go.Figure(); fig_sc.add_trace(go.Scatter(x=df_scan['Vol. Hist. (%)'], y=df_scan['Retorno Call (%)'], mode='markers+text', text=df_scan['Ativo'], textposition='top center', marker=dict(size=8, color=df_scan['Retorno Call (%)'], colorscale='RdYlGn', showscale=True), name='Retorno Call'))
                    fig_sc.update_layout(template='plotly_dark', height=450, xaxis_title="Volatilidade Histórica (%)", yaxis_title="Retorno Estimado Call (%)", title="Retorno vs Volatilidade — Venda Coberta"); st.plotly_chart(fig_sc, use_container_width=True)
    with sub_payoff:
        st.markdown("#### 📊 Gráfico de Payoff — Monte sua Estrutura")
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            pay_estrategia = st.selectbox("Estratégia:", ["Venda Coberta (Call)","Venda de Put","Compra de Call (DITM/OTM)","Compra de Put","Trava de Alta (Bull Call Spread)","Trava de Baixa (Bear Put Spread)","Wheel (Venda Put → Venda Coberta)"], key="pay_est")
            pay_S = st.number_input("Preço Atual do Ativo (R$):", min_value=0.01, value=30.0, step=0.50, key="pay_S")
            pay_K1 = st.number_input("Strike Principal (K1) (R$):", min_value=0.01, value=32.0, step=0.50, key="pay_K1")
            pay_premio = st.number_input("Prêmio Recebido/Pago (R$):", min_value=0.0, value=0.80, step=0.05, key="pay_premio")
            pay_K2 = None; pay_premio2 = None
            if "Trava" in pay_estrategia:
                pay_K2 = st.number_input("Strike Secundário (K2) (R$):", min_value=0.01, value=34.0, step=0.50, key="pay_K2")
                pay_premio2 = st.number_input("Prêmio Pago/Recebido K2 (R$):", min_value=0.0, value=0.30, step=0.05, key="pay_p2")
            pay_qtd = st.number_input("Quantidade de Contratos (lotes de 100):", min_value=1, value=1, step=1, key="pay_qtd"); mult = pay_qtd * 100
        with col_p2:
            precos_range = np.linspace(pay_S * 0.6, pay_S * 1.4, 200); payoff = np.zeros(len(precos_range))
            if pay_estrategia == "Venda Coberta (Call)":
                for i, p in enumerate(precos_range): payoff[i] = (p - pay_S) * mult + (-max(p - pay_K1, 0) + pay_premio) * mult
                breakeven = pay_S - pay_premio; descricao = f"Breakeven: R$ {breakeven:.2f} | Ganho máx: R$ {pay_premio*mult:.2f}"
            elif pay_estrategia == "Venda de Put":
                for i, p in enumerate(precos_range): payoff[i] = (-max(pay_K1 - p, 0) + pay_premio) * mult
                breakeven = pay_K1 - pay_premio; descricao = f"Breakeven: R$ {breakeven:.2f} | Ganho máx: R$ {pay_premio*mult:.2f}"
            elif pay_estrategia == "Compra de Call (DITM/OTM)":
                for i, p in enumerate(precos_range): payoff[i] = (max(p - pay_K1, 0) - pay_premio) * mult
                breakeven = pay_K1 + pay_premio; descricao = f"Breakeven: R$ {breakeven:.2f} | Perda máx: R$ {pay_premio*mult:.2f}"
            elif pay_estrategia == "Compra de Put":
                for i, p in enumerate(precos_range): payoff[i] = (max(pay_K1 - p, 0) - pay_premio) * mult
                breakeven = pay_K1 - pay_premio; descricao = f"Breakeven: R$ {breakeven:.2f} | Perda máx: R$ {pay_premio*mult:.2f}"
            elif pay_estrategia == "Trava de Alta (Bull Call Spread)":
                credito = (pay_premio2 or 0) - pay_premio
                for i, p in enumerate(precos_range): payoff[i] = (max(p - pay_K1, 0) - max(p - (pay_K2 or pay_K1), 0) + credito) * mult
                descricao = f"Ganho máx: R$ {((pay_K2 or pay_K1)-pay_K1+credito)*mult:.2f}"
            elif pay_estrategia == "Trava de Baixa (Bear Put Spread)":
                credito = pay_premio - (pay_premio2 or 0)
                for i, p in enumerate(precos_range): payoff[i] = (max(pay_K1 - p, 0) - max((pay_K2 or pay_K1) - p, 0) + credito) * mult
                descricao = f"Ganho máx: R$ {(pay_K1-(pay_K2 or pay_K1)+credito)*mult:.2f}"
            elif pay_estrategia == "Wheel (Venda Put → Venda Coberta)":
                for i, p in enumerate(precos_range): payoff[i] = pay_premio * mult if p >= pay_K1 else (-max(pay_K1 - p, 0) + pay_premio * 2) * mult
                descricao = f"Prêmio acumulado estimado: R$ {pay_premio*2*mult:.2f}"
            else: descricao = ""
            fig_pay = go.Figure(); fig_pay.add_trace(go.Scatter(x=precos_range, y=payoff, mode='lines', name='Resultado', line=dict(color='#00BFFF', width=2.5)))
            fig_pay.add_hline(y=0, line=dict(color='white', dash='dot', width=1)); fig_pay.add_vline(x=pay_S, line=dict(color='white', dash='dash'), annotation_text=f"Atual R${pay_S:.2f}"); fig_pay.add_vline(x=pay_K1, line=dict(color='#FFD700', dash='dash'), annotation_text=f"K1 R${pay_K1:.2f}")
            if pay_K2: fig_pay.add_vline(x=pay_K2, line=dict(color='#FF69B4', dash='dash'), annotation_text=f"K2 R${pay_K2:.2f}")
            fig_pay.add_hrect(y0=min(payoff), y1=0, fillcolor="rgba(178,34,34,0.08)", line_width=0); fig_pay.add_hrect(y0=0, y1=max(payoff), fillcolor="rgba(34,139,34,0.08)", line_width=0)
            fig_pay.update_layout(template='plotly_dark', height=500, xaxis_title="Preço do Ativo no Vencimento (R$)", yaxis_title="Resultado (R$)", title=f"Payoff — {pay_estrategia}"); st.plotly_chart(fig_pay, use_container_width=True)
            st.info(f"📌 {descricao}")
    with sub_diario:
        st.markdown("#### 📓 Diário de Operações com Opções")
        if 'operacoes' not in st.session_state: st.session_state.operacoes = []
        with st.expander("➕ Registrar Nova Operação", expanded=True):
            d1, d2, d3, d4 = st.columns(4)
            with d1: op_data = st.date_input("Data de Entrada:", key="op_data"); op_ativo = st.text_input("Ativo Objeto:", key="op_ativo").upper(); op_estrategia = st.selectbox("Estratégia:", ["Venda Coberta","Venda de Put","Compra de Call","Compra de Put","Trava de Alta","Trava de Baixa","Wheel","Outra"], key="op_est")
            with d2: op_serie = st.text_input("Série da Opção:", key="op_serie").upper(); op_tipo = st.selectbox("Tipo:", ["Call","Put"], key="op_tipo"); op_direcao = st.selectbox("Direção:", ["Venda","Compra"], key="op_dir")
            with d3: op_strike = st.number_input("Strike (R$):", min_value=0.0, value=30.0, step=0.5, key="op_strike"); op_premio = st.number_input("Prêmio (R$):", min_value=0.0, value=0.80, step=0.01, key="op_prem"); op_qtd = st.number_input("Quantidade (lotes):", min_value=1, value=1, step=1, key="op_qtd")
            with d4: op_vcto = st.date_input("Vencimento:", key="op_vcto", value=datetime.today() + timedelta(days=30)); op_resultado = st.number_input("Resultado Final (R$):", value=0.0, step=1.0, key="op_res"); op_status = st.selectbox("Status:", ["Aberta","Encerrada","Exercida"], key="op_status")
            op_obs = st.text_area("Observações:", key="op_obs", height=80)
            if st.button("💾 Salvar Operação", key="btn_salvar"):
                st.session_state.operacoes.append({'Data': op_data.strftime('%d/%m/%Y'), 'Ativo': op_ativo, 'Estratégia': op_estrategia, 'Série': op_serie, 'Tipo': op_tipo, 'Direção': op_direcao, 'Strike': op_strike, 'Prêmio': op_premio, 'Qtd': op_qtd, 'Vencimento': op_vcto.strftime('%d/%m/%Y'), 'Resultado': op_resultado, 'Status': op_status, 'Obs': op_obs, 'Valor Operação': round(op_premio * op_qtd * 100, 2)})
                st.success("✅ Operação registrada com sucesso!")
        if st.session_state.operacoes:
            df_ops = pd.DataFrame(st.session_state.operacoes)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📊 Total de Operações", len(df_ops)); m2.metric("🟡 Operações Abertas", len(df_ops[df_ops['Status']=='Aberta']))
            m3.metric("💰 Prêmios Arrecadados", f"R$ {df_ops['Valor Operação'].sum():,.2f}"); m4.metric("📈 Resultado Realizado", f"R$ {df_ops['Resultado'].sum():,.2f}")
            st.dataframe(df_ops, use_container_width=True, hide_index=True)
            if st.button("🗑️ Limpar Operações", key="btn_limpar"): st.session_state.operacoes = []; st.rerun()

# ==============================================================================
# ABA 5: INTELIGÊNCIA DE SELEÇÃO
# ==============================================================================
with tab_inteligencia:
    st.markdown("### 🧠 Inteligência de Seleção de Ativos para Opções")
    sub_ivrank, sub_score, sub_calendario = st.tabs(["📊 IV Rank — Volatilidade Implícita","🏆 Score de Atratividade","📅 Calendário de Vencimentos"])
    with sub_ivrank:
        st.markdown("#### 📊 IV Rank — Volatilidade Implícita vs Histórica")
        st.markdown("- **IV Rank > 50%** 🔴 → Volatilidade CARA → **Melhor momento para VENDER opções**\n- **IV Rank < 30%** 🟢 → Volatilidade BARATA → **Melhor momento para COMPRAR opções**")
        col_iv1, _ = st.columns([1, 2])
        with col_iv1: iv_periodo = st.selectbox("Janela para cálculo:", [21, 30, 45, 63], index=1, format_func=lambda x: f"{x} dias úteis", key="iv_periodo")
        if st.button("📊 Calcular IV Rank de Todos os Ativos", key="btn_ivrank"):
            with st.spinner("Calculando volatilidade histórica e IV Rank..."):
                iv_resultados = []
                for ativo in ativos_lista:
                    if ativo not in precos_fechamento.columns: continue
                    serie = precos_fechamento[ativo].dropna()
                    if len(serie) < 252: continue
                    try:
                        retornos = np.log(serie / serie.shift(1)).dropna()
                        vol_atual = float(retornos.rolling(iv_periodo).std().iloc[-1] * math.sqrt(252) * 100)
                        vols_ano = retornos.rolling(iv_periodo).std() * math.sqrt(252) * 100; vols_ano = vols_ano.dropna().iloc[-252:]
                        vol_min = float(vols_ano.min()); vol_max = float(vols_ano.max())
                        if vol_max == vol_min: continue
                        iv_rank = ((vol_atual - vol_min) / (vol_max - vol_min)) * 100
                        classificacao = "🔴 VENDER" if iv_rank >= 50 else "🟢 COMPRAR" if iv_rank <= 30 else "🟡 NEUTRO"
                        recomendacao = "Venda Coberta / Venda de Put" if iv_rank >= 50 else "Compra de Call DITM / Spread" if iv_rank <= 30 else "Aguardar melhor momento"
                        S = float(serie.iloc[-1]); premio_est = S * (vol_atual/100) * math.sqrt(30/252)
                        iv_resultados.append({'Ativo': ativo.replace('.SA',''), 'Setor': ativos_setores[ativo], 'Preço (R$)': round(S, 2), 'Vol Atual (%)': round(vol_atual, 1), 'Vol Mín 1A (%)': round(vol_min, 1), 'Vol Máx 1A (%)': round(vol_max, 1), 'IV Rank (%)': round(iv_rank, 1), 'Classificação': classificacao, 'Estratégia': recomendacao, 'Prêmio Est. 30D (R$)': round(premio_est, 2)})
                    except: continue
                df_iv = pd.DataFrame(iv_resultados)
                if not df_iv.empty:
                    df_iv = df_iv.sort_values('IV Rank (%)', ascending=False)
                    qtd_vender = len(df_iv[df_iv['IV Rank (%)'] >= 50]); qtd_comprar = len(df_iv[df_iv['IV Rank (%)'] <= 30]); iv_medio = df_iv['IV Rank (%)'].mean()
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🔴 Momento Venda", qtd_vender); c2.metric("🟡 Neutros", len(df_iv)-qtd_vender-qtd_comprar); c3.metric("🟢 Momento Compra", qtd_comprar); c4.metric("📊 IV Rank Médio", f"{iv_medio:.1f}%")
                    st.markdown("##### 🔴 Melhores para VENDER")
                    df_venda_iv = df_iv[df_iv['IV Rank (%)'] >= 50].head(15)
                    if not df_venda_iv.empty: st.dataframe(df_venda_iv, use_container_width=True, hide_index=True)
                    st.markdown("##### 🟢 Melhores para COMPRAR")
                    df_compra_iv = df_iv[df_iv['IV Rank (%)'] <= 30].sort_values('IV Rank (%)').head(15)
                    if not df_compra_iv.empty: st.dataframe(df_compra_iv, use_container_width=True, hide_index=True)
                    fig_iv = go.Figure(); cores_iv = ['#B22222' if v >= 50 else '#228B22' if v <= 30 else '#DAA520' for v in df_iv['IV Rank (%)']]
                    fig_iv.add_trace(go.Bar(x=df_iv['Ativo'], y=df_iv['IV Rank (%)'], marker_color=cores_iv, name='IV Rank'))
                    fig_iv.add_hline(y=50, line=dict(color='#FF4500', dash='dot', width=2), annotation_text="50% — Zona de Venda"); fig_iv.add_hline(y=30, line=dict(color='#00FF7F', dash='dot', width=2), annotation_text="30% — Zona de Compra")
                    fig_iv.update_layout(template='plotly_dark', height=450, xaxis_title="Ativo", yaxis_title="IV Rank (%)"); fig_iv.update_xaxes(tickangle=45); st.plotly_chart(fig_iv, use_container_width=True)
    with sub_score:
        st.markdown("#### 🏆 Score de Atratividade para Opções")
        col_s1, _ = st.columns([1, 2])
        with col_s1: score_estrategia = st.selectbox("Estratégia de referência:", ["Venda Coberta / Venda de Put", "Compra de Call DITM", "Trava de Alta"], key="score_est")
        if st.button("🏆 Calcular Score de Todos os Ativos", key="btn_score"):
            with st.spinner("Calculando score de atratividade..."):
                score_resultados = []
                for ativo in ativos_lista:
                    if ativo not in precos_fechamento.columns: continue
                    serie = precos_fechamento[ativo].dropna()
                    if len(serie) < 200: continue
                    try:
                        S = float(serie.iloc[-1]); ret = np.log(serie / serie.shift(1)).dropna(); vol_at = float(ret.rolling(21).std().iloc[-1] * math.sqrt(252) * 100)
                        sma50_s = float(serie.rolling(50).mean().iloc[-1]); sma200_s = float(serie.rolling(200).mean().iloc[-1])
                        acima_50 = S > sma50_s; acima_200 = S > sma200_s
                        delta_s = serie.diff(); ganho_s = delta_s.where(delta_s > 0, 0).rolling(14).mean(); perda_s = (-delta_s.where(delta_s < 0, 0)).rolling(14).mean(); rs_s = ganho_s / perda_s; rsi_s = float((100 - (100 / (1 + rs_s))).iloc[-1])
                        vols_ano_s = ret.rolling(21).std() * math.sqrt(252) * 100; vols_ano_s = vols_ano_s.dropna().iloc[-252:]; vol_min_s = float(vols_ano_s.min()); vol_max_s = float(vols_ano_s.max())
                        iv_rank_s = ((vol_at - vol_min_s) / (vol_max_s - vol_min_s)) * 100 if vol_max_s != vol_min_s else 50
                        vol_diaria = float(serie.pct_change().abs().rolling(21).mean().iloc[-1] * 100)
                        if score_estrategia == "Venda Coberta / Venda de Put":
                            s_tendencia = 25 if (acima_50 and acima_200) else 15 if acima_50 else 5; s_iv_rank = min(iv_rank_s / 100 * 30, 30); s_rsi = 20 if 40 < rsi_s < 65 else 10 if rsi_s <= 40 else 5; s_volatilidade = 15 if 20 < vol_at < 50 else 8 if vol_at <= 20 else 5; s_liquidez = min(vol_diaria * 2, 10)
                        elif score_estrategia == "Compra de Call DITM":
                            s_tendencia = 30 if (acima_50 and acima_200) else 15 if acima_50 else 0; s_iv_rank = max(30 - (iv_rank_s / 100 * 30), 0); s_rsi = 20 if rsi_s > 55 else 10; s_volatilidade = 10 if vol_at > 30 else 5; s_liquidez = min(vol_diaria * 2, 10)
                        else:
                            s_tendencia = 25 if (acima_50 and acima_200) else 12 if acima_50 else 3; s_iv_rank = min(iv_rank_s / 100 * 25, 25); s_rsi = 20 if 45 < rsi_s < 70 else 8; s_volatilidade = 20 if 25 < vol_at < 60 else 8; s_liquidez = min(vol_diaria * 2, 10)
                        score_total = round(min(s_tendencia + s_iv_rank + s_rsi + s_volatilidade + s_liquidez, 100), 1)
                        estrelas = "⭐⭐⭐⭐⭐" if score_total >= 75 else "⭐⭐⭐⭐" if score_total >= 60 else "⭐⭐⭐" if score_total >= 45 else "⭐⭐" if score_total >= 30 else "⭐"
            
                        tendencia_txt = "Alta Forte" if (acima_50 and acima_200) else "Alta Parcial" if acima_50 else "Baixa"
                        score_resultados.append({"Ativo": ativo.replace(".SA",""), "Setor": ativos_setores[ativo], "Score": score_total, "Estrelas": estrelas, "Preco": round(S, 2), "Tendencia": tendencia_txt, "RSI": round(rsi_s, 1), "IV Rank (%)": round(iv_rank_s, 1), "Vol Anual (%)": round(vol_at, 1), "Pts Tendencia": round(s_tendencia, 1), "Pts IV Rank": round(s_iv_rank, 1), "Pts RSI": round(s_rsi, 1), "Pts Vol": round(s_volatilidade, 1), "Pts Liquidez": round(s_liquidez, 1)})
                    except: continue
                df_score = pd.DataFrame(score_resultados)
                if not df_score.empty:
                    df_score = df_score.sort_values("Score", ascending=False)
                    st.markdown("### 🥇 Top 5 Ativos para Operar Agora")
                    top5 = df_score.head(5); cols_top = st.columns(5)
                    for i, (_, row) in enumerate(top5.iterrows()):
                        with cols_top[i]:
                            cor_score = "#228B22" if row["Score"] >= 60 else "#DAA520" if row["Score"] >= 40 else "#B22222"
                            st.markdown(f"""<div style="background:#1e1e1e;border:2px solid {cor_score};border-radius:10px;text-align:center;padding:15px;"><div style="font-size:22px;font-weight:bold;color:white;">{row["Ativo"]}</div><div style="font-size:28px;font-weight:bold;color:{cor_score};">{row["Score"]}</div><div style="font-size:16px;">{row["Estrelas"]}</div><div style="font-size:11px;color:#aaa;">{row["Tendencia"]} | IV: {row["IV Rank (%)"]}% | RSI: {row["RSI"]}</div></div>""", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.dataframe(df_score.rename(columns={"Preco": "Preco (R$)", "Tendencia": "Tendencia", "Pts Tendencia": "Pts Tendencia", "Pts IV Rank": "Pts IV Rank", "Pts RSI": "Pts RSI", "Pts Vol": "Pts Vol", "Pts Liquidez": "Pts Liquidez"}), use_container_width=True, hide_index=True)
                    fig_score = go.Figure(); cores_score = ["#228B22" if v >= 60 else "#DAA520" if v >= 40 else "#B22222" for v in df_score["Score"]]
                    fig_score.add_trace(go.Bar(x=df_score["Ativo"], y=df_score["Score"], marker_color=cores_score, text=df_score["Score"], textposition="outside", name="Score"))
                    fig_score.add_hline(y=60, line=dict(color="#228B22", dash="dot"), annotation_text="60 Excelente"); fig_score.add_hline(y=40, line=dict(color="#DAA520", dash="dot"), annotation_text="40 Razoavel")
                    fig_score.update_layout(template="plotly_dark", height=500, xaxis_title="Ativo", yaxis_title="Score (0-100)", yaxis=dict(range=[0, 110])); fig_score.update_xaxes(tickangle=45); st.plotly_chart(fig_score, use_container_width=True)

    with sub_calendario:
        st.markdown("#### 📅 Calendario de Vencimentos de Opcoes B3")
        def calcular_terceira_segunda(ano, mes):
            primeiro_dia = datetime(ano, mes, 1); dia_semana = primeiro_dia.weekday()
            if dia_semana <= 0: primeira_segunda = primeiro_dia + timedelta(days=(0 - dia_semana))
            else: primeira_segunda = primeiro_dia + timedelta(days=(7 - dia_semana))
            return primeira_segunda + timedelta(weeks=2)
        hoje_cal = datetime.today(); vencimentos = []
        for offset in range(12):
            mes_alvo = (hoje_cal.month - 1 + offset) % 12 + 1; ano_alvo = hoje_cal.year + ((hoje_cal.month - 1 + offset) // 12)
            vcto = calcular_terceira_segunda(ano_alvo, mes_alvo)
            dias_uteis_ate = len(pd.bdate_range(hoje_cal.date(), vcto.date())); dias_corridos = (vcto.date() - hoje_cal.date()).days; passado = vcto.date() < hoje_cal.date()
            meses_br = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]; letra_opcao = ["A","B","C","D","E","F","G","H","I","J","K","L"][mes_alvo - 1]
            vencimentos.append({"Mes": f"{meses_br[mes_alvo-1]}/{ano_alvo}", "Data Vencimento": vcto.strftime("%d/%m/%Y"), "Dias Corridos": dias_corridos if not passado else "Vencido", "Dias Uteis": dias_uteis_ate if not passado else "Vencido", "Letra Call": letra_opcao, "Letra Put": chr(ord(letra_opcao) + 12), "Status": "Ativo" if not passado else "Vencido"})
        df_vcto = pd.DataFrame(vencimentos); df_proximos = df_vcto[df_vcto["Status"] == "Ativo"].head(6)
        st.markdown("### 📌 Proximos Vencimentos"); cols_vcto = st.columns(3)
        for i, (_, row) in enumerate(df_proximos.head(3).iterrows()):
            with cols_vcto[i]:
                dias = row["Dias Uteis"]; cor = "#B22222" if isinstance(dias, int) and dias <= 10 else "#DAA520" if isinstance(dias, int) and dias <= 21 else "#228B22"
                st.markdown(f"""<div style="background:#1e1e1e;border:2px solid {cor};border-radius:10px;text-align:center;padding:15px;"><div style="font-size:18px;font-weight:bold;color:#d4af37;">{row["Mes"]}</div><div style="font-size:22px;font-weight:bold;color:white;">{row["Data Vencimento"]}</div><div style="font-size:28px;font-weight:bold;color:{cor};">{dias} dias uteis</div><div style="font-size:12px;color:#aaa;margin-top:8px;">Call: <b style="color:#00BFFF;">{row["Letra Call"]}</b> | Put: <b style="color:#FFD700;">{row["Letra Put"]}</b></div></div>""", unsafe_allow_html=True)
        st.markdown("<br>"); st.dataframe(df_vcto, use_container_width=True, hide_index=True)

# ==============================================================================
# ABA 6: MOTOR DE BACKTEST
# ==============================================================================
with tab_backtest:
    st.markdown("### ⚙️ Motor de Backtest")
    st.markdown("Teste estrategias tecnicas e de opcoes no historico real de precos.")

    def calcular_rsi_bt(serie, janela=14):
        delta = serie.diff()
        ganho = delta.where(delta > 0, 0).rolling(janela).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(janela).mean()
        rs = ganho / perda
        return 100 - (100 / (1 + rs))

    def rodar_backtest(df, estrategia, params):
        df = df.copy(); close = df["Close"]
        df["SMA_r"]   = close.rolling(params.get("sma_r", 9)).mean()
        df["SMA_l"]   = close.rolling(params.get("sma_l", 21)).mean()
        df["SMA50"]   = close.rolling(50).mean()
        df["SMA200"]  = close.rolling(200).mean()
        df["RSI"]     = calcular_rsi_bt(close, params.get("rsi_janela", 14))
        df["BB_mid"]  = close.rolling(20).mean()
        df["BB_std"]  = close.rolling(20).std()
        df["BB_up"]   = df["BB_mid"] + 2 * df["BB_std"]
        df["BB_lo"]   = df["BB_mid"] - 2 * df["BB_std"]
        fast_d, slow_d, _, _, _ = calcular_didi(close)
        df["didi_f"]  = fast_d; df["didi_s"] = slow_d
        df.dropna(inplace=True)
        df["sinal"] = 0

        if estrategia == "Cruzamento de Medias (SMA)":
            df.loc[df["SMA_r"] > df["SMA_l"], "sinal"] = 1
            df.loc[df["SMA_r"] < df["SMA_l"], "sinal"] = -1
        elif estrategia == "RSI Sobrevendido/Sobrecomprado":
            df.loc[df["RSI"] < params.get("rsi_vend", 30), "sinal"] = 1
            df.loc[df["RSI"] > params.get("rsi_comp", 70), "sinal"] = -1
        elif estrategia == "Agulhada do Didi":
            for i in range(1, len(df)):
                fa = df["didi_f"].iloc[i-1]; fc = df["didi_f"].iloc[i]; sc = df["didi_s"].iloc[i]
                if fa < 0 and fc > 0 and sc < 0: df.iloc[i, df.columns.get_loc("sinal")] = 1
                elif fa > 0 and fc < 0 and sc > 0: df.iloc[i, df.columns.get_loc("sinal")] = -1
        elif estrategia == "Bollinger Bands":
            df.loc[df["Close"] <= df["BB_lo"], "sinal"] = 1
            df.loc[df["Close"] >= df["BB_up"], "sinal"] = -1
        elif estrategia == "Tendencia SMA50+SMA200":
            df.loc[(df["Close"] > df["SMA50"]) & (df["Close"] > df["SMA200"]), "sinal"] = 1
            df.loc[(df["Close"] < df["SMA50"]) & (df["Close"] < df["SMA200"]), "sinal"] = -1
        elif estrategia == "RSI + Tendencia Combinada":
            df.loc[(df["RSI"] < params.get("rsi_vend", 30)) & (df["Close"] > df["SMA200"]), "sinal"] = 1
            df.loc[(df["RSI"] > params.get("rsi_comp", 70)) & (df["Close"] < df["SMA200"]), "sinal"] = -1
        elif estrategia == "Venda Coberta Simulada":
            otm_pct = params.get("otm", 5) / 100; dias_vcto = params.get("dias_vcto", 30); r_bt = 0.1475
            df.loc[df["RSI"] < 65, "sinal"] = 1  # entra quando nao sobrecomprado

        capital = params.get("capital", 10000.0); stop_pct = params.get("stop", 5.0) / 100; alvo_pct = params.get("alvo", 10.0) / 100
        posicao = 0; preco_entrada = 0.0; trades = []; capital_hist = []

        for i in range(len(df)):
            row_bt = df.iloc[i]; preco = float(row_bt["Close"]); sinal = int(row_bt["sinal"]); data = df.index[i]
            if posicao != 0:
                var = (preco - preco_entrada) / preco_entrada * posicao
                if var <= -stop_pct or var >= alvo_pct:
                    resultado_r = capital * var; capital += resultado_r
                    motivo = "Stop Loss" if var <= -stop_pct else "Alvo Atingido"
                    trades.append({"Data Saida": data.strftime("%d/%m/%Y"), "Resultado (R$)": round(resultado_r, 2), "Resultado (%)": round(var*100, 2), "Motivo": motivo, "Preco Entrada": round(preco_entrada, 2), "Preco Saida": round(preco, 2), "Direcao": "Compra" if posicao == 1 else "Venda"})
                    posicao = 0; preco_entrada = 0.0
            if sinal != 0 and posicao == 0: posicao = sinal; preco_entrada = preco
            elif sinal != 0 and sinal != posicao:
                var = (preco - preco_entrada) / preco_entrada * posicao; resultado_r = capital * var; capital += resultado_r
                trades.append({"Data Saida": data.strftime("%d/%m/%Y"), "Resultado (R$)": round(resultado_r, 2), "Resultado (%)": round(var*100, 2), "Motivo": "Reversao de Sinal", "Preco Entrada": round(preco_entrada, 2), "Preco Saida": round(preco, 2), "Direcao": "Compra" if posicao == 1 else "Venda"})
                posicao = sinal; preco_entrada = preco
            capital_hist.append({"Data": data, "Capital": round(capital, 2)})

        df_trades = pd.DataFrame(trades); df_capital = pd.DataFrame(capital_hist).set_index("Data")
        retorno_bh = ((float(df["Close"].iloc[-1]) / float(df["Close"].iloc[0])) - 1) * 100
        if not df_trades.empty:
            trades_pos = len(df_trades[df_trades["Resultado (R$)"] > 0]); trades_neg = len(df_trades) - trades_pos
            taxa_acerto = trades_pos / len(df_trades) * 100; maior_ganho = df_trades["Resultado (R$)"].max(); maior_perda = df_trades["Resultado (R$)"].min()
            retorno_est = ((capital - params.get("capital", 10000.0)) / params.get("capital", 10000.0)) * 100
            cap_series = df_capital["Capital"]; rolling_max = cap_series.cummax(); drawdown = ((cap_series - rolling_max) / rolling_max * 100).min()
        else:
            trades_pos = trades_neg = taxa_acerto = maior_ganho = maior_perda = retorno_est = drawdown = 0
        metricas = {"Capital Inicial": params.get("capital", 10000.0), "Capital Final": round(capital, 2), "Retorno Estrategia (%)": round(retorno_est, 2), "Retorno BH (%)": round(retorno_bh, 2), "Total Trades": len(df_trades), "Trades Positivos": trades_pos, "Trades Negativos": trades_neg, "Taxa Acerto (%)": round(taxa_acerto, 2), "Maior Ganho (R$)": round(maior_ganho, 2) if trades_pos > 0 else 0, "Maior Perda (R$)": round(maior_perda, 2) if trades_neg > 0 else 0, "Drawdown Maximo (%)": round(drawdown, 2)}
        return df_trades, df_capital, metricas, df

    sub_bt_config, sub_bt_resultado, sub_bt_comparativo, sub_bt_opcoes, sub_bt_agulhada = st.tabs([
        "⚙️ Configurar", "📊 Resultados", "🔁 Multi-Ativo", "📈 Backtest Opcoes", "🎯 Backtest Agulhadas"
    ])

    with sub_bt_config:
        st.markdown("#### ⚙️ Configure os Parametros do Backtest")
        col_bt1, col_bt2, col_bt3 = st.columns(3)
        with col_bt1:
            bt_ativo = st.text_input("Ativo (Ex: PETR4):", key="bt_ativo", value="PETR4").upper().strip()
            bt_periodo = st.selectbox("Periodo historico:", ["1 ano","2 anos","3 anos","5 anos","10 anos"], index=2, key="bt_periodo")
            bt_capital = st.number_input("Capital inicial (R$):", min_value=1000.0, value=10000.0, step=1000.0, key="bt_capital")
        with col_bt2:
            bt_estrategia = st.selectbox("Estrategia:", ["Cruzamento de Medias (SMA)","RSI Sobrevendido/Sobrecomprado","Agulhada do Didi","Bollinger Bands","Tendencia SMA50+SMA200","RSI + Tendencia Combinada"], key="bt_estrategia")
            bt_stop = st.number_input("Stop Loss (%):", min_value=0.5, max_value=50.0, value=5.0, step=0.5, key="bt_stop")
            bt_alvo = st.number_input("Alvo de Ganho (%):", min_value=0.5, max_value=100.0, value=10.0, step=0.5, key="bt_alvo")
        with col_bt3:
            st.markdown("**Parametros:**")
            bt_sma_r   = st.number_input("SMA Rapida:", min_value=2, max_value=50, value=9, step=1, key="bt_sma_r")
            bt_sma_l   = st.number_input("SMA Lenta:",  min_value=5, max_value=200, value=21, step=1, key="bt_sma_l")
            bt_rsi_j   = st.number_input("RSI Janela:", min_value=2, max_value=50, value=14, step=1, key="bt_rsi_j")
            bt_rsi_sob = st.number_input("RSI Sobrecomprado:", min_value=50, max_value=95, value=70, step=1, key="bt_rsi_sob")
            bt_rsi_sov = st.number_input("RSI Sobrevendido:",  min_value=5,  max_value=50, value=30, step=1, key="bt_rsi_sov")
        if st.button("🚀 Rodar Backtest", key="btn_backtest", use_container_width=True):
            ativo_bt = bt_ativo if bt_ativo.endswith(".SA") else bt_ativo + ".SA"
            periodo_map = {"1 ano":"1y","2 anos":"2y","3 anos":"3y","5 anos":"5y","10 anos":"10y"}
            with st.spinner(f"Rodando backtest de {bt_estrategia} em {bt_ativo}..."):
                df_bt_raw = yf.download(ativo_bt, period=periodo_map[bt_periodo], progress=False)
                if df_bt_raw.empty: st.error("Ativo nao encontrado.")
                else:
                    if isinstance(df_bt_raw.columns, pd.MultiIndex): df_bt_raw.columns = df_bt_raw.columns.droplevel(1)
                    params = {"capital": bt_capital, "stop": bt_stop, "alvo": bt_alvo, "sma_r": bt_sma_r, "sma_l": bt_sma_l, "rsi_janela": bt_rsi_j, "rsi_comp": bt_rsi_sob, "rsi_vend": bt_rsi_sov}
                    df_trades, df_capital, metricas, df_full = rodar_backtest(df_bt_raw, bt_estrategia, params)
                    st.session_state["bt_trades"] = df_trades; st.session_state["bt_capital"] = df_capital
                    st.session_state["bt_metricas"] = metricas; st.session_state["bt_df_full"] = df_full
                    st.session_state["bt_ativo"] = bt_ativo; st.session_state["bt_estrat"] = bt_estrategia
                    m1,m2,m3,m4,m5,m6 = st.columns(6)
                    m1.metric("Capital Final", f"R$ {metricas['Capital Final']:,.2f}")
                    m2.metric("Retorno", f"{metricas['Retorno Estrategia (%)']:.1f}%", delta=f"{metricas['Retorno Estrategia (%)']-metricas['Retorno BH (%)']:.1f}% vs B&H")
                    m3.metric("Total Trades", metricas["Total Trades"]); m4.metric("Taxa Acerto", f"{metricas['Taxa Acerto (%)']:.1f}%")
                    m5.metric("Drawdown Max", f"{metricas['Drawdown Maximo (%)']:.1f}%"); m6.metric("Buy & Hold", f"{metricas['Retorno BH (%)']:.1f}%")
                    st.info("Vá para aba Resultados para ver os graficos completos.")

    with sub_bt_resultado:
        if "bt_capital" not in st.session_state: st.info("Configure e rode o backtest primeiro.")
        else:
            df_trades = st.session_state["bt_trades"]; df_capital = st.session_state["bt_capital"]
            metricas = st.session_state["bt_metricas"]; df_full = st.session_state["bt_df_full"]
            bt_ativo = st.session_state["bt_ativo"]; bt_estrat = st.session_state["bt_estrat"]
            st.markdown(f"#### 📊 Resultados — {bt_ativo} | {bt_estrat}")
            st.markdown(f"""<div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">CAPITAL INICIAL</div><div style="padding:10px;font-size:16px;font-weight:bold;color:white;">R$ {metricas["Capital Inicial"]:,.2f}</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">CAPITAL FINAL</div><div style="padding:10px;font-size:16px;font-weight:bold;color:{"#228B22" if metricas["Capital Final"]>=metricas["Capital Inicial"] else "#B22222"};">R$ {metricas["Capital Final"]:,.2f}</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">RETORNO ESTRAT.</div><div style="padding:10px;font-size:16px;font-weight:bold;color:{"#228B22" if metricas["Retorno Estrategia (%)"]>=0 else "#B22222"};">{metricas["Retorno Estrategia (%)"]:.2f}%</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">BUY & HOLD</div><div style="padding:10px;font-size:16px;font-weight:bold;color:{"#228B22" if metricas["Retorno BH (%)"]>=0 else "#B22222"};">{metricas["Retorno BH (%)"]:.2f}%</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">TAXA ACERTO</div><div style="padding:10px;font-size:16px;font-weight:bold;color:white;">{metricas["Taxa Acerto (%)"]:.1f}%</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">DRAWDOWN MAX</div><div style="padding:10px;font-size:16px;font-weight:bold;color:#B22222;">{metricas["Drawdown Maximo (%)"]:.1f}%</div></div>
                <div style="flex:1;min-width:130px;background:#1e1e1e;border:1px solid #333;border-radius:8px;text-align:center;overflow:hidden;"><div style="background:#2b2e35;color:#d4af37;padding:6px;font-weight:bold;font-size:11px;">TRADES +/-</div><div style="padding:10px;font-size:16px;font-weight:bold;color:white;">{metricas["Trades Positivos"]}✅/{metricas["Trades Negativos"]}❌</div></div>
            </div>""", unsafe_allow_html=True)
            fig_bt = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.4], subplot_titles=("Curva de Capital vs Buy & Hold", "Preco do Ativo com Sinais"))
            cap_norm = (df_capital["Capital"] / metricas["Capital Inicial"] - 1) * 100
            bh_norm = (df_full["Close"] / float(df_full["Close"].iloc[0]) - 1) * 100
            fig_bt.add_trace(go.Scatter(x=df_capital.index, y=cap_norm, mode="lines", name="Estrategia", line=dict(color="#00BFFF", width=2.5), fill="tozeroy", fillcolor="rgba(0,191,255,0.05)"), row=1, col=1)
            fig_bt.add_trace(go.Scatter(x=df_full.index, y=bh_norm, mode="lines", name="Buy & Hold", line=dict(color="white", width=1.5, dash="dot")), row=1, col=1)
            fig_bt.add_hline(y=0, line=dict(color="gray", dash="dot"), row=1, col=1)
            fig_bt.add_trace(go.Candlestick(x=df_full.index, open=df_full["Open"], high=df_full["High"], low=df_full["Low"], close=df_full["Close"], name="Preco", increasing_line_color="#228B22", decreasing_line_color="#B22222"), row=2, col=1)
            if not df_trades.empty:
                for _, t in df_trades.iterrows():
                    try:
                        data_s = pd.to_datetime(t["Data Saida"], format="%d/%m/%Y")
                        cor_t = "#00FF00" if t["Resultado (R$)"] > 0 else "#FF4500"
                        simbolo = "triangle-up" if t["Direcao"] == "Compra" else "triangle-down"
                        fig_bt.add_trace(go.Scatter(x=[data_s], y=[t["Preco Saida"]], mode="markers", marker=dict(symbol=simbolo, size=10, color=cor_t, line=dict(color="white", width=1)), showlegend=False, name="Trade"), row=2, col=1)
                    except: continue
            fig_bt.update_layout(template="plotly_dark", height=750, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)); fig_bt.update_xaxes(rangeslider_visible=False)
            st.plotly_chart(fig_bt, use_container_width=True)
            if not df_trades.empty:
                st.markdown("#### 📋 Historico de Trades"); st.dataframe(df_trades, use_container_width=True, hide_index=True)
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    fig_dist = go.Figure(); fig_dist.add_trace(go.Histogram(x=df_trades["Resultado (%)"], nbinsx=20, name="Distribuicao"))
                    fig_dist.add_vline(x=0, line=dict(color="white", dash="dot")); fig_dist.update_layout(template="plotly_dark", height=300, title="Distribuicao dos Resultados", xaxis_title="Resultado (%)"); st.plotly_chart(fig_dist, use_container_width=True)
                with col_d2:
                    fig_acum = go.Figure(); fig_acum.add_trace(go.Scatter(y=df_trades["Resultado (R$)"].cumsum(), mode="lines+markers", line=dict(color="#00BFFF", width=2), fill="tozeroy", fillcolor="rgba(0,191,255,0.08)", name="Acumulado"))
                    fig_acum.add_hline(y=0, line=dict(color="white", dash="dot")); fig_acum.update_layout(template="plotly_dark", height=300, title="Resultado Acumulado por Trade", yaxis_title="R$"); st.plotly_chart(fig_acum, use_container_width=True)
                csv_bt = df_trades.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Baixar Trades CSV", data=csv_bt, file_name=f"backtest_{bt_ativo}.csv", mime="text/csv")

    with sub_bt_comparativo:
        st.markdown("#### 🔁 Comparativo — Mesma Estrategia em Multiplos Ativos")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: cmp_est = st.selectbox("Estrategia:", ["Cruzamento de Medias (SMA)","RSI Sobrevendido/Sobrecomprado","Agulhada do Didi","Bollinger Bands","Tendencia SMA50+SMA200"], key="cmp_est"); cmp_per = st.selectbox("Periodo:", ["1 ano","2 anos","3 anos","5 anos"], index=1, key="cmp_per")
        with col_c2: cmp_cap = st.number_input("Capital (R$):", min_value=1000.0, value=10000.0, step=1000.0, key="cmp_cap"); cmp_stop = st.number_input("Stop (%):", min_value=0.5, value=5.0, step=0.5, key="cmp_stop"); cmp_alvo = st.number_input("Alvo (%):", min_value=0.5, value=10.0, step=0.5, key="cmp_alvo")
        with col_c3: ativos_disp = [a.replace(".SA","") for a in ativos_lista]; cmp_ativos = st.multiselect("Ativos (max 10):", options=ativos_disp, default=["PETR4","VALE3","ITUB4","BBDC4","WEGE3"], key="cmp_ativos")
        if st.button("🔁 Rodar Comparativo", key="btn_cmp", use_container_width=True):
            if not cmp_ativos: st.warning("Selecione pelo menos um ativo.")
            else:
                periodo_map = {"1 ano":"1y","2 anos":"2y","3 anos":"3y","5 anos":"5y"}; params_cmp = {"capital": cmp_cap, "stop": cmp_stop, "alvo": cmp_alvo, "sma_r": 9, "sma_l": 21, "rsi_janela": 14, "rsi_comp": 70, "rsi_vend": 30}
                cmp_resultados = []; fig_cmp = go.Figure(); cores_cmp = ["#00BFFF","#FFD700","#FF69B4","#32CD32","#FFA500","#87CEFA","#FF6347","#BA55D3","#00FF7F","#FF4500"]
                with st.spinner("Rodando comparativo..."):
                    for idx, ativo_cmp in enumerate(cmp_ativos[:10]):
                        try:
                            df_c = yf.download(ativo_cmp + ".SA", period=periodo_map[cmp_per], progress=False)
                            if df_c.empty: continue
                            if isinstance(df_c.columns, pd.MultiIndex): df_c.columns = df_c.columns.droplevel(1)
                            _, df_cap_c, met_c, _ = rodar_backtest(df_c, cmp_est, params_cmp)
                            cap_n = (df_cap_c["Capital"] / cmp_cap - 1) * 100
                            fig_cmp.add_trace(go.Scatter(x=df_cap_c.index, y=cap_n, mode="lines", name=ativo_cmp, line=dict(color=cores_cmp[idx % len(cores_cmp)], width=2)))
                            cmp_resultados.append({"Ativo": ativo_cmp, "Retorno Estrat (%)": met_c["Retorno Estrategia (%)"], "Retorno BH (%)": met_c["Retorno BH (%)"], "Taxa Acerto (%)": met_c["Taxa Acerto (%)"], "Trades": met_c["Total Trades"], "Capital Final (R$)": met_c["Capital Final"], "Drawdown (%)": met_c["Drawdown Maximo (%)"]})
                        except: continue
                    fig_cmp.add_hline(y=0, line=dict(color="gray", dash="dot")); fig_cmp.update_layout(template="plotly_dark", height=500, yaxis_title="Retorno Acumulado (%)", title=f"Comparativo — {cmp_est}"); st.plotly_chart(fig_cmp, use_container_width=True)
                    if cmp_resultados:
                        df_cmp_r = pd.DataFrame(cmp_resultados).sort_values("Retorno Estrat (%)", ascending=False); st.dataframe(df_cmp_r, use_container_width=True, hide_index=True)
                        fig_bar = go.Figure(); cores_bar = ["#228B22" if v >= 0 else "#B22222" for v in df_cmp_r["Retorno Estrat (%)"]]
                        fig_bar.add_trace(go.Bar(x=df_cmp_r["Ativo"], y=df_cmp_r["Retorno Estrat (%)"], marker_color=cores_bar, name="Estrategia", text=df_cmp_r["Retorno Estrat (%)"].round(1), textposition="outside"))
                        fig_bar.add_trace(go.Bar(x=df_cmp_r["Ativo"], y=df_cmp_r["Retorno BH (%)"], marker_color="rgba(255,255,255,0.3)", name="Buy & Hold"))
                        fig_bar.update_layout(template="plotly_dark", height=400, barmode="group", yaxis_title="Retorno (%)", title="Estrategia vs Buy & Hold"); st.plotly_chart(fig_bar, use_container_width=True)

    with sub_bt_opcoes:
        st.markdown("#### 📈 Backtest de Opcoes — Venda Coberta e Venda de Put")
        st.markdown("Simula a estrategia de venda de opcoes mês a mês no historico, calculando os premios via Black-Scholes.")
        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1: op_bt_ativo = st.text_input("Ativo (Ex: PETR4):", key="op_bt_ativo", value="PETR4").upper().strip(); op_bt_per = st.selectbox("Periodo:", ["1 ano","2 anos","3 anos","5 anos"], index=2, key="op_bt_per")
        with col_o2: op_bt_estrat = st.selectbox("Estrategia:", ["Venda Coberta (Call OTM)","Venda de Put (Put OTM)","Wheel (Put -> Coberta)"], key="op_bt_estrat"); op_bt_otm = st.number_input("OTM (% do preco):", min_value=1.0, max_value=20.0, value=5.0, step=0.5, key="op_bt_otm"); op_bt_taxa = st.number_input("Taxa livre de risco (% a.a.):", min_value=0.0, value=14.75, step=0.25, key="op_bt_taxa")
        with col_o3: op_bt_cap = st.number_input("Capital inicial (R$):", min_value=1000.0, value=10000.0, step=1000.0, key="op_bt_cap"); op_bt_dias = st.number_input("Dias por ciclo:", min_value=10, max_value=60, value=30, step=5, key="op_bt_dias")
        if st.button("📈 Rodar Backtest de Opcoes", key="btn_op_bt", use_container_width=True):
            ativo_op = op_bt_ativo if op_bt_ativo.endswith(".SA") else op_bt_ativo + ".SA"
            periodo_map2 = {"1 ano":"1y","2 anos":"2y","3 anos":"3y","5 anos":"5y"}
            with st.spinner("Simulando ciclos de opcoes no historico..."):
                df_op = yf.download(ativo_op, period=periodo_map2[op_bt_per], progress=False)
                if df_op.empty: st.error("Ativo nao encontrado.")
                else:
                    if isinstance(df_op.columns, pd.MultiIndex): df_op.columns = df_op.columns.droplevel(1)
                    capital_op = op_bt_cap; r_op = op_bt_taxa / 100; T_op = op_bt_dias / 365; ciclos = []; capital_hist_op = []
                    indices = list(range(0, len(df_op) - op_bt_dias, op_bt_dias))
                    for idx_c in indices:
                        try:
                            row_e = df_op.iloc[idx_c]; row_s = df_op.iloc[min(idx_c + op_bt_dias, len(df_op)-1)]
                            S_e = float(row_e["Close"]); S_s = float(row_s["Close"]); data_e = df_op.index[idx_c]; data_s = df_op.index[min(idx_c + op_bt_dias, len(df_op)-1)]
                            janela_vol = df_op["Close"].iloc[max(0, idx_c-21):idx_c]
                            if len(janela_vol) < 5: continue
                            ret_vol = np.log(janela_vol / janela_vol.shift(1)).dropna(); sigma_op = float(ret_vol.std() * math.sqrt(252)) if len(ret_vol) > 0 else 0.3
                            if sigma_op <= 0: sigma_op = 0.3
                            if op_bt_estrat == "Venda Coberta (Call OTM)":
                                K = round(S_e * (1 + op_bt_otm/100), 2); premio = black_scholes(S_e, K, T_op, r_op, sigma_op, "call")
                                exercido = S_s >= K
                                if exercido: resultado = (K - S_e) + premio
                                else: resultado = (S_s - S_e) + premio
                                capital_op += resultado; tipo_ciclo = "Call OTM"
                            elif op_bt_estrat == "Venda de Put (Put OTM)":
                                K = round(S_e * (1 - op_bt_otm/100), 2); premio = black_scholes(S_e, K, T_op, r_op, sigma_op, "put")
                                exercido = S_s <= K
                                if exercido: resultado = -(K - S_s) + premio
                                else: resultado = premio
                                capital_op += resultado; tipo_ciclo = "Put OTM"
                            else:
                                K = round(S_e * (1 - op_bt_otm/100), 2); premio_put = black_scholes(S_e, K, T_op, r_op, sigma_op, "put")
                                exercido_put = S_s <= K
                                if exercido_put:
                                    K2 = round(K * (1 + op_bt_otm/100), 2); premio_call = black_scholes(S_s, K2, T_op, r_op, sigma_op, "call")
                                    resultado = -(K - S_s) + premio_put + premio_call
                                else: resultado = premio_put
                                capital_op += resultado; tipo_ciclo = "Wheel"
                            ciclos.append({"Data Entrada": data_e.strftime("%d/%m/%Y"), "Data Saida": data_s.strftime("%d/%m/%Y"), "Preco Entrada": round(S_e, 2), "Preco Saida": round(S_s, 2), "Strike": round(K, 2), "Premio (R$)": round(premio if op_bt_estrat != "Wheel" else premio_put, 4), "Resultado (R$)": round(resultado, 4), "Exercido": "Sim" if (exercido_put if op_bt_estrat == "Wheel" else exercido) else "Nao", "Capital": round(capital_op, 2)})
                        except: continue
                    df_ciclos = pd.DataFrame(ciclos)
                    if not df_ciclos.empty:
                        retorno_total = ((capital_op - op_bt_cap) / op_bt_cap) * 100; retorno_bh_op = ((float(df_op["Close"].iloc[-1]) / float(df_op["Close"].iloc[0])) - 1) * 100
                        ciclos_pos = len(df_ciclos[df_ciclos["Resultado (R$)"] > 0]); taxa_ac_op = ciclos_pos / len(df_ciclos) * 100
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("Capital Final", f"R$ {capital_op:,.2f}"); m2.metric("Retorno Opcoes", f"{retorno_total:.2f}%", delta=f"{retorno_total-retorno_bh_op:.1f}% vs B&H")
                        m3.metric("Taxa Acerto Ciclos", f"{taxa_ac_op:.1f}%"); m4.metric("Total Ciclos", len(df_ciclos))
                        fig_op_bt = go.Figure()
                        fig_op_bt.add_trace(go.Scatter(x=pd.to_datetime(df_ciclos["Data Saida"], format="%d/%m/%Y"), y=(df_ciclos["Capital"] / op_bt_cap - 1) * 100, mode="lines+markers", name="Opcoes", line=dict(color="#00BFFF", width=2.5), fill="tozeroy", fillcolor="rgba(0,191,255,0.05)"))
                        bh_op_norm = (df_op["Close"] / float(df_op["Close"].iloc[0]) - 1) * 100
                        fig_op_bt.add_trace(go.Scatter(x=df_op.index, y=bh_op_norm, mode="lines", name="Buy & Hold", line=dict(color="white", width=1.5, dash="dot")))
                        fig_op_bt.add_hline(y=0, line=dict(color="gray", dash="dot")); fig_op_bt.update_layout(template="plotly_dark", height=450, yaxis_title="Retorno Acumulado (%)", title=f"Backtest {op_bt_estrat} — {op_bt_ativo}"); st.plotly_chart(fig_op_bt, use_container_width=True)
                        st.markdown("#### 📋 Historico de Ciclos"); st.dataframe(df_ciclos, use_container_width=True, hide_index=True)
                        csv_op = df_ciclos.to_csv(index=False).encode("utf-8")
                        st.download_button("📥 Baixar CSV", data=csv_op, file_name=f"backtest_opcoes_{op_bt_ativo}.csv", mime="text/csv")

    with sub_bt_agulhada:
        st.markdown("#### 🎯 Backtest da Agulhada do Didi")
        st.markdown("Testa exclusivamente a estrategia de Agulhada do Didi com varredura em todos os ativos monitorados.")
        col_ag1, col_ag2 = st.columns(2)
        with col_ag1: ag_bt_per = st.selectbox("Periodo:", ["6 meses","1 ano","2 anos","3 anos"], index=1, key="ag_bt_per"); ag_bt_cap = st.number_input("Capital (R$):", min_value=1000.0, value=10000.0, step=1000.0, key="ag_bt_cap")
        with col_ag2: ag_bt_stop = st.number_input("Stop Loss (%):", min_value=0.5, value=5.0, step=0.5, key="ag_bt_stop"); ag_bt_alvo = st.number_input("Alvo (%):", min_value=0.5, value=10.0, step=0.5, key="ag_bt_alvo")
        if st.button("🎯 Rodar Backtest Agulhadas em Todos os Ativos", key="btn_ag_bt", use_container_width=True):
            periodo_map3 = {"6 meses":"6mo","1 ano":"1y","2 anos":"2y","3 anos":"3y"}
            ag_resultados = []; params_ag = {"capital": ag_bt_cap, "stop": ag_bt_stop, "alvo": ag_bt_alvo}
            with st.spinner("Rodando backtest da Agulhada em todos os ativos..."):
                for ativo_ag_bt in ativos_lista:
                    try:
                        df_ag_raw = yf.download(ativo_ag_bt, period=periodo_map3[ag_bt_per], progress=False)
                        if df_ag_raw.empty or len(df_ag_raw) < 50: continue
                        if isinstance(df_ag_raw.columns, pd.MultiIndex): df_ag_raw.columns = df_ag_raw.columns.droplevel(1)
                        _, _, met_ag, _ = rodar_backtest(df_ag_raw, "Agulhada do Didi", params_ag)
                        ag_resultados.append({"Ativo": ativo_ag_bt.replace(".SA",""), "Setor": ativos_setores[ativo_ag_bt], "Retorno (%)": met_ag["Retorno Estrategia (%)"], "Buy & Hold (%)": met_ag["Retorno BH (%)"], "Vantagem (%)": round(met_ag["Retorno Estrategia (%)"] - met_ag["Retorno BH (%)"], 2), "Taxa Acerto (%)": met_ag["Taxa Acerto (%)"], "Trades": met_ag["Total Trades"], "Capital Final (R$)": met_ag["Capital Final"], "Drawdown (%)": met_ag["Drawdown Maximo (%)"]})
                    except: continue
                df_ag_res = pd.DataFrame(ag_resultados)
                if not df_ag_res.empty:
                    df_ag_res = df_ag_res.sort_values("Retorno (%)", ascending=False)
                    st.markdown("### 🏆 Ranking — Agulhada do Didi por Ativo")
                    top3 = df_ag_res.head(3); cols_top3 = st.columns(3)
                    for i, (_, r) in enumerate(top3.iterrows()):
                        with cols_top3[i]:
                            cor3 = "#228B22" if r["Retorno (%)"] >= 0 else "#B22222"
                            st.markdown(f"""<div style="background:#1e1e1e;border:2px solid {cor3};border-radius:10px;text-align:center;padding:15px;"><div style="font-size:22px;font-weight:bold;color:white;">#{i+1} {r["Ativo"]}</div><div style="font-size:26px;font-weight:bold;color:{cor3};">{r["Retorno (%)"]:.1f}%</div><div style="font-size:12px;color:#aaa;">{r["Setor"]}</div><div style="font-size:12px;color:#aaa;">Acerto: {r["Taxa Acerto (%)"]:.1f}% | {r["Trades"]} trades</div><div style="font-size:12px;color:{"#228B22" if r["Vantagem (%)"]>=0 else "#B22222"};">vs B&H: {r["Vantagem (%)"]:.1f}%</div></div>""", unsafe_allow_html=True)
                    st.markdown("<br>"); st.dataframe(df_ag_res, use_container_width=True, hide_index=True)
                    fig_ag_bar = go.Figure(); cores_ag = ["#228B22" if v >= 0 else "#B22222" for v in df_ag_res["Retorno (%)"]]
                    fig_ag_bar.add_trace(go.Bar(x=df_ag_res["Ativo"], y=df_ag_res["Retorno (%)"], marker_color=cores_ag, name="Agulhada", text=df_ag_res["Retorno (%)"].round(1), textposition="outside"))
                    fig_ag_bar.add_trace(go.Bar(x=df_ag_res["Ativo"], y=df_ag_res["Buy & Hold (%)"], marker_color="rgba(255,255,255,0.2)", name="Buy & Hold"))
                    fig_ag_bar.add_hline(y=0, line=dict(color="white", dash="dot")); fig_ag_bar.update_layout(template="plotly_dark", height=500, barmode="group", yaxis_title="Retorno (%)", title="Agulhada do Didi vs Buy & Hold por Ativo"); fig_ag_bar.update_xaxes(tickangle=45); st.plotly_chart(fig_ag_bar, use_container_width=True)
                    csv_ag = df_ag_res.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Baixar Resultados CSV", data=csv_ag, file_name="backtest_agulhadas.csv", mime="text/csv")

    with st.expander("📖 Como interpretar o Backtest?"):
        st.markdown("""
        | Metrica | Significado | Referencia |
        |---|---|---|
        | **Retorno Estrategia** | Rendimento da estrategia no periodo | Comparar com Buy & Hold |
        | **Buy & Hold** | Retorno de simplesmente comprar e segurar | Benchmark passivo |
        | **Taxa de Acerto** | % de trades lucrativos | Acima de 50% e positivo |
        | **Drawdown Maximo** | Maior queda do capital durante o periodo | Quanto menor, melhor |
        | **Vantagem** | Diferenca entre estrategia e Buy & Hold | Positivo = estrategia ganhou |

        **Avisos:**
        - Resultados passados nao garantem retornos futuros
        - O backtest nao considera custos de corretagem, slippage e impostos
        - Combine sempre com analise tecnica antes de operar
        """)
