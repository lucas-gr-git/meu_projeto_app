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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Terminal B3", layout="wide", page_icon="📊")
st.title("🖥️ Terminal Profissional de Inteligência Mercado - B3")
st.markdown("Monitoramento Avançado, Análise Técnica, Fundamentalista e Notícias em Tempo Real.")

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
    except Exception as e:
        return []

# FUNÇÕES AUXILIARES DE FORMATAÇÃO
def fmt_br(val, is_pct=False, currency=False):
    if pd.isna(val) or val is None or val == "-": return "-"
    texto = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if is_pct: return f"{texto}%"
    if currency: return f"R$ {texto}"
    return texto

def cor_variacao(val):
    if pd.isna(val) or val == "-": return "#FFFFFF"
    return "#228B22" if val > 0 else "#B22222" if val < 0 else "#FFFFFF"

# Baixa 365 dias para garantir o cálculo das médias
precos_fechamento, dados_completos = carregar_dados(ativos_lista, 365)

# --- PROCESSAMENTO DE MÉTRICAS (PAINEL GERAL) ---
resultados = []
for ativo in ativos_lista:
    df = pd.DataFrame()
    if ativo in precos_fechamento.columns:
        df['Close'] = precos_fechamento[ativo]
        
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA100'] = df['Close'].rolling(window=100).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        delta = df['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
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

        resultados.append({
            'Ativo': ativo.replace('.SA', ''), 'Setor': ativos_setores[ativo], 'Preço (R$)': round(ultimo_preco, 2),
            'Variação (%)': round(variacao_diaria, 2), 'Tendência Curta (50D)': tendencia_curta,
            'Tendência Média (100D)': tendencia_media, 'Tendência Longa (200D)': tendencia_longa, 'Sentimento': sentimento
        })

df_resumo = pd.DataFrame(resultados)


# ==============================================================================
# --- CRIAÇÃO DAS ABAS DO SCRIPT ---
# ==============================================================================
tab_visao_geral, tab_analise_individual = st.tabs(["🌐 Visão Geral do Mercado", "🔬 Análise Detalhada por Ativo"])

# ==============================================================================
# --- ABA 1: VISÃO GERAL DO MERCADO ---
# ==============================================================================
with tab_visao_geral:
    st.markdown("### 📊 Mapa de Calor do Mercado")
    
    ids, labels, parents, values, colors, customdata = ["B3"], ["B3"], [""], [0], ["#2b2e35"], [["<b>Painel Geral B3</b>", "<b>B3</b>"]]
    
    for setor in df_resumo['Setor'].unique():
        ids.append(setor); labels.append(setor); parents.append("B3"); values.append(0); colors.append("#2b2e35")
        customdata.append([f"<b>Setor: {setor}</b>", f"<b>{setor}</b>"])
        ids.append(setor + "_fantasma"); labels.append(""); parents.append(setor); values.append(0.000001); colors.append("#FFFFFF"); customdata.append(["", ""])

    for _, row in df_resumo.iterrows():
        ids.append(row['Ativo']); labels.append(row['Ativo']); parents.append(row['Setor']); values.append(1)
        var = row['Variação (%)']; preco = row['Preço (R$)']
        colors.append("#228B22" if var > 0.05 else "#B22222" if var < -0.05 else "#708090")
        
        preco_br = fmt_br(preco)
        var_br = f"{var:+.2f}%".replace(".", ",")
        
        hover = f"<b>{row['Ativo']}</b><br>Variação: {var_br}<br>Preço: R$ {preco_br}<br><br>Curta: {row['Tendência Curta (50D)']}<br>Média: {row['Tendência Média (100D)']}<br>Longa: {row['Tendência Longa (200D)']}"
        block = f"<b>{row['Ativo']}</b><br>R$ {preco_br}<br> {var_br}"
        customdata.append([hover, block])

    fig_treemap = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, marker_colors=colors,
        customdata=customdata, texttemplate="%{customdata[1]}", hovertemplate="%{customdata[0]}<extra></extra>", textfont=dict(color="black")
    ))
    fig_treemap.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=550, template='plotly_dark')
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
            
            # Baixando histórico gigante para a Rentabilidade (10 Anos)
            df_hist = yf.download(ativo_buscado, period="10y")
            
            if df_hist.empty:
                st.error("⚠️ Código não encontrado no banco de dados.")
            else:
                if isinstance(df_hist.columns, pd.MultiIndex):
                    df_hist.columns = df_hist.columns.droplevel(1)

                # --- CÁLCULO DAS RENTABILIDADES HISTÓRICAS ---
                preco_atual = float(df_hist['Close'].iloc[-1])
                
                def calc_retorno(df, dias_uteis):
                    if len(df) > dias_uteis:
                        preco_antigo = float(df['Close'].iloc[-dias_uteis])
                        return ((preco_atual / preco_antigo) - 1) * 100
                    return "-"

                ret_1m = calc_retorno(df_hist, 21)
                ret_3m = calc_retorno(df_hist, 63)
                ret_1a = calc_retorno(df_hist, 252)
                ret_2a = calc_retorno(df_hist, 504)
                ret_5a = calc_retorno(df_hist, 1260)
                ret_10a = calc_retorno(df_hist, 2520)

                # --- BUSCA FUNDAMENTALISTA ---
                info = {}
                try: 
                    info = ticker_obj.info
                except: 
                    pass

                val_var12m = ret_1a if ret_1a != "-" else info.get('52WeekChange', "-")
                if val_var12m != "-" and isinstance(val_var12m, float) and '52WeekChange' in info:
                    val_var12m = val_var12m * 100 if val_var12m < 1 else val_var12m

                val_pl = info.get('trailingPE', "-")
                val_pvp = info.get('priceToBook', "-")
                
                val_dy = info.get('trailingAnnualDividendYield')
                if val_dy is None:
                    val_dy = info.get('dividendYield', "-")
                
                if val_dy != "-": 
                    val_dy = val_dy * 100

                # --- CARDS ESTILO STATUS INVEST ---
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">COTAÇÃO</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(preco_atual, currency=True)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">VARIAÇÃO (12M)</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: {cor_variacao(val_var12m)};">{fmt_br(val_var12m, is_pct=True)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">P/L</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(val_pl)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">P/VP</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(val_pvp)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">DY (12M)</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(val_dy, is_pct=True)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- TABELA DE RENTABILIDADE HISTÓRICA ---
                st.markdown(f"""
                <div style="border: 1px solid #333; border-radius: 8px; background-color: #1e1e1e; padding: 15px; margin-bottom: 15px;">
                    <div style="font-weight: bold; margin-bottom: 15px; color: white;">📈 Rentabilidade Histórica</div>
                    <table style="width: 100%; text-align: center; border-collapse: collapse;">
                        <tr style="color: #aaaaaa; font-size: 14px; border-bottom: 1px solid #333;">
                            <th style="padding: 10px; text-align: left;">Indicador</th>
                            <th style="padding: 10px;">1 mês</th>
                            <th style="padding: 10px;">3 meses</th>
                            <th style="padding: 10px;">1 ano</th>
                            <th style="padding: 10px;">2 anos</th>
                            <th style="padding: 10px;">5 anos</th>
                            <th style="padding: 10px;">10 anos</th>
                        </tr>
                        <tr style="font-size: 16px; font-weight: bold; background-color: #252525;">
                            <td style="padding: 15px; text-align: left; color: white;">Rentabilidade</td>
                            <td style="color: {cor_variacao(ret_1m)};">{fmt_br(ret_1m, is_pct=True)}</td>
                            <td style="color: {cor_variacao(ret_3m)};">{fmt_br(ret_3m, is_pct=True)}</td>
                            <td style="color: {cor_variacao(ret_1a)};">{fmt_br(ret_1a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(ret_2a)};">{fmt_br(ret_2a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(ret_5a)};">{fmt_br(ret_5a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(ret_10a)};">{fmt_br(ret_10a, is_pct=True)}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                # --- BOTÃO DE EXPORTAÇÃO ---
                csv_data = df_hist.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Baixar Histórico Completo e Indicadores (.CSV)",
                    data=csv_data,
                    file_name=f"{ativo_buscado}_historico.csv",
                    mime="text/csv"
                )
                st.markdown("<br>", unsafe_allow_html=True)

                # --- CÁLCULOS TÉCNICOS NO HISTÓRICO COMPLETO ---
                df_hist['SMA50'] = df_hist['Close'].rolling(window=50).mean()
                df_hist['SMA100'] = df_hist['Close'].rolling(window=100).mean()
                df_hist['SMA200'] = df_hist['Close'].rolling(window=200).mean()
                
                sma3 = df_hist['Close'].rolling(window=3).mean()
                sma8 = df_hist['Close'].rolling(window=8).mean()
                sma20_didi = df_hist['Close'].rolling(window=20).mean()
                df_hist['DidiFast'] = sma3 - sma8
                df_hist['DidiSlow'] = sma20_didi - sma8
                
                tr1 = df_hist['High'] - df_hist['Low']
                tr2 = (df_hist['High'] - df_hist['Close'].shift(1)).abs()
                tr3 = (df_hist['Low'] - df_hist['Close'].shift(1)).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                
                up_m = df_hist['High'] - df_hist['High'].shift(1)
                dn_m = df_hist['Low'].shift(1) - df_hist['Low']
                pos_dm = pd.Series(np.where((up_m > dn_m) & (up_m > 0), up_m, 0), index=df_hist.index)
                neg_dm = pd.Series(np.where((dn_m > up_m) & (dn_m > 0), dn_m, 0), index=df_hist.index)
                
                tr8 = tr.rolling(8).sum()
                df_hist['PDI'] = 100 * pos_dm.rolling(8).sum() / tr8
                df_hist['NDI'] = 100 * neg_dm.rolling(8).sum() / tr8
                df_hist['ADX'] = (100 * (np.abs(df_hist['PDI'] - df_hist['NDI']) / (df_hist['PDI'] + df_hist['NDI']))).rolling(window=8).mean()

                # --- CORTE DE DADOS PARA EXIBIÇÃO NO GRÁFICO ---
                limite_data = datetime.now() - (timedelta(days=30) if janela_tempo == "1 Mês" else timedelta(days=180) if janela_tempo == "6 Meses" else timedelta(days=365) if janela_tempo == "1 Ano" else timedelta(days=730) if janela_tempo == "2 Anos" else timedelta(days=1825))
                df_plot = df_hist[df_hist.index >= limite_data].copy()
                
                cores_volume = ['#228B22' if r.Close >= r.Open else '#B22222' for r in df_plot.itertuples()]
                cores_didi_bg = ['rgba(0, 150, 0, 0.12)' if p > n else 'rgba(200, 0, 0, 0.12)' for p, n in zip(df_plot['PDI'], df_plot['NDI'])]

                # --- LAYOUT: GRÁFICOS VS NOTÍCIAS ---
                col_graficos, col_noticias = st.columns([3, 1])

                with col_graficos:
                    fig_plotly = make_subplots(
                        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.20, 0.20],
                        specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]],
                        subplot_titles=('Gráfico de Preço e Volume', 'Didi Plus (3, 8, 20)', 'DMI / ADX (8)')
                    )
                    
                    fig_plotly.add_trace(go.Candlestick(
                        x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name='Candlestick'
                    ), row=1, col=1, secondary_y=False)
                    
                    for m, c in zip(['SMA50','SMA100','SMA200'], ['#00BFFF', '#BA55D3', 'white']):
                        fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot[m], mode='lines', name=f'Média {m.replace("SMA","")}', line=dict(color=c, width=1.5)), row=1, col=1, secondary_y=False)
                    
                    fig_plotly.add_trace(go.Bar(
                        x=df_plot.index, y=df_plot['Volume'], name='Volume', marker_color=cores_volume, opacity=0.35
                    ), row=1, col=1, secondary_y=True)
                    
                    max_y_didi = max(df_plot['DidiFast'].abs().max(), df_plot['DidiSlow'].abs().max()) * 1.4
                    if pd.isna(max_y_didi) or max_y_didi == 0: max_y_didi = 1
                    
                    fig_plotly.add_trace(go.Bar(x=df_plot.index, y=[max_y_didi] * len(df_plot), marker_color=cores_didi_bg, marker_line_width=0, showlegend=False, hoverinfo='skip'), row=2, col=1)
                    fig_plotly.add_trace(go.Bar(x=df_plot.index, y=[-max_y_didi] * len(df_plot), marker_color=cores_didi_bg, marker_line_width=0, showlegend=False, hoverinfo='skip'), row=2, col=1)
                    
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=np.zeros(len(df_plot)), mode='lines', name='Didi Normal', line=dict(color='white', width=1, dash='dot')), row=2, col=1)
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DidiSlow'], mode='lines', name='Didi Lenta (20)', line=dict(color='#FFD700', width=2)), row=2, col=1)
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot['DidiFast'], mode='lines', name='Didi Rápida (3)', line=dict(color='#00BFFF', width=2)), row=2, col=1)
                    
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ADX'], mode='lines', name='ADX', line=dict(color='white', width=1.5)), row=3, col=1)
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot['PDI'], mode='lines', name='+DI', line=dict(color='#00BFFF', width=1.5)), row=3, col=1)
                    fig_plotly.add_trace(go.Scatter(x=df_plot.index, y=df_plot['NDI'], mode='lines', name='-DI', line=dict(color='#FFD700', width=1.5)), row=3, col=1)

                    fig_plotly.update_yaxes(title_text="Preço (R$)", side="right", row=1, col=1, secondary_y=False)
                    fig_plotly.update_yaxes(showgrid=False, showticklabels=False, range=[0, df_plot['Volume'].max() * 4], row=1, col=1, secondary_y=True)
                    
                    fig_plotly.update_layout(
                        template='plotly_dark', height=900, showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        barmode='relative'
                    )
                    fig_plotly.update_xaxes(rangeslider_visible=False)
                    st.plotly_chart(fig_plotly, use_container_width=True)

                with col_noticias:
                    st.markdown("### 📰 Notícias Recentes")
                    noticias = buscar_noticias_google(ativo_buscado)
                    
                    if not noticias:
                        st.info("Nenhuma notícia recente encontrada para este ativo.")
                    else:
                        for n in noticias:
                            st.markdown(f"""
                            <div style="border: 1px solid #444444; border-radius: 5px; padding: 10px; margin-bottom: 12px; background-color: #1e1e1e;">
                                <a href="{n['link']}" target="_blank" style="color: #00BFFF; text-decoration: none; font-weight: bold; font-size: 14px;">{n['title']}</a>
                                <p style="color: #888888; font-size: 11px; margin: 5px 0 0 0;">{n['publisher']} • {n['time']}</p>
                            </div>
                            """, unsafe_allow_html=True)

            st.divider()

            # ==============================================================================
            # --- BENCHMARK IBOVESPA E OUTROS ÍNDICES (MULTILINE) ---
            # ==============================================================================
            st.markdown(f"### 📊 Comparativo de Desempenho e Benchmarks")
            
            benchmarks_selecionados = ['IBOV', 'IFIX', 'SMLL', 'IDIV', 'IVVB11', 'CDI', 'IPCA']

            with st.spinner("Calculando Benchmarks e normalizando as escalas..."):
                fig_bench = go.Figure()

                # 1. Plota o Ativo Principal Normalizado
                if not df_plot.empty:
                    primeiro_preco_ativo = float(df_plot['Close'].iloc[0])
                    ativo_norm = (df_plot['Close'] / primeiro_preco_ativo - 1) * 100
                    fig_bench.add_trace(go.Scatter(x=ativo_norm.index, y=ativo_norm, mode='lines', name=ativo_buscado, line=dict(color='#00BFFF', width=2.5)))

                # 2. Configuração dos Benchmarks
                mapa_yf = {
                    'IBOV': '^BVSP', 'IFIX': 'XFIX11.SA', 'SMLL': 'SMAL11.SA', 
                    'IDIV': 'DIVO11.SA', 'IVVB11': 'IVVB11.SA'
                }
                cores_bench = {
                    'IBOV': 'white', 'IFIX': '#32CD32', 'SMLL': '#FFD700', 
                    'IDIV': '#FF69B4', 'IVVB11': '#FFA500', 'CDI': '#87CEFA', 'IPCA': '#FF6347'
                }

                data_inicio_yf = limite_data.strftime('%Y-%m-%d')
                data_inicio_bcb = limite_data.strftime('%d/%m/%Y')

                for b in benchmarks_selecionados:
                    cor = cores_bench.get(b, 'white')

                    # BUSCA NO YAHOO FINANCE (ETFs e Índices)
                    if b in mapa_yf:
                        df_b = yf.download(mapa_yf[b], start=data_inicio_yf)
                        if not df_b.empty:
                            if isinstance(df_b.columns, pd.MultiIndex):
                                df_b.columns = df_b.columns.droplevel(1)
                            df_b_plot = df_b[df_b.index >= limite_data]
                            if not df_b_plot.empty:
                                p_preco = float(df_b_plot['Close'].iloc[0])
                                b_norm = (df_b_plot['Close'] / p_preco - 1) * 100
                                fig_bench.add_trace(go.Scatter(x=b_norm.index, y=b_norm, mode='lines', name=b, line=dict(color=cor, width=1.5, dash='dot' if b=='IBOV' else 'solid')))

                    # BUSCA NO BANCO CENTRAL DO BRASIL (CDI - SGS 12)
                    elif b == 'CDI':
                        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_inicio_bcb}"
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as res:
                                data = json.loads(res.read().decode('utf-8'))
                            df_cdi = pd.DataFrame(data)
                            df_cdi['data'] = pd.to_datetime(df_cdi['data'], format='%d/%m/%Y')
                            df_cdi.set_index('data', inplace=True)
                            df_cdi['valor'] = df_cdi['valor'].astype(float)
                            cdi_acumulado = ((1 + df_cdi['valor'] / 100).cumprod() - 1) * 100
                            fig_bench.add_trace(go.Scatter(x=cdi_acumulado.index, y=cdi_acumulado, mode='lines', name='CDI', line=dict(color=cor, width=1.5)))
                        except: pass

                    # BUSCA NO BANCO CENTRAL DO BRASIL (IPCA - SGS 433)
                    elif b == 'IPCA':
                        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={data_inicio_bcb}"
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as res:
                                data = json.loads(res.read().decode('utf-8'))
                            df_ipca = pd.DataFrame(data)
                            df_ipca['data'] = pd.to_datetime(df_ipca['data'], format='%d/%m/%Y')
                            df_ipca.set_index('data', inplace=True)
                            df_ipca['valor'] = df_ipca['valor'].astype(float)
                            ipca_acumulado = ((1 + df_ipca['valor'] / 100).cumprod() - 1) * 100
                            # Preenche os dias vazios do mês mantendo o valor contínuo na tela
                            idx = pd.date_range(start=ipca_acumulado.index[0], end=datetime.today())
                            ipca_acumulado = ipca_acumulado.reindex(idx, method='ffill')
                            fig_bench.add_trace(go.Scatter(x=ipca_acumulado.index, y=ipca_acumulado, mode='lines', name='IPCA', line=dict(color=cor, width=1.5)))
                        except: pass

                fig_bench.update_layout(
                    template='plotly_dark', height=450,
                    yaxis_title="Desempenho Acumulado (%)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_bench, use_container_width=True)

            st.divider()

            # ==============================================================================
            # --- EVENTOS CORPORATIVOS ---
            # ==============================================================================
            st.markdown("### 📅 Calendário de Eventos Corporativos")
            
            ex_div_ts = info.get('exDividendDate')
            earn_ts = info.get('earningsTimestamp', info.get('earningsTimestampStart'))
            
            def format_data_evento(ts):
                if pd.isna(ts) or ts is None: 
                    return "Não divulgado ou indisponível"
                return datetime.fromtimestamp(ts).strftime('%d/%m/%Y')
                
            data_div = format_data_evento(ex_div_ts)
            data_bal = format_data_evento(earn_ts)
            
            c_ev1, c_ev2, _ = st.columns([1, 1, 2])
            with c_ev1:
                st.info(f"🧾 **Próximo Balanço (Earnings):**\n\n{data_bal}")
            with c_ev2:
                st.success(f"💰 **Data Com (Dividendos):**\n\n{data_div}")
