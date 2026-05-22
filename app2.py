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

# ==============================================================================
# --- CONFIGURAÇÃO DA PÁGINA ---
# ==============================================================================
st.set_page_config(
    page_title="Terminal B3", 
    layout="wide", 
    page_icon="📊"
)

st.title("🖥️ Terminal Profissional de Inteligência Mercado - B3")
st.markdown("Monitoramento Avançado, Análise Técnica, Fundamentalista e Notícias em Tempo Real.")

# ==============================================================================
# --- LISTA DAS TOP 70 AÇÕES SEPARADAS POR SETOR ---
# ==============================================================================
ativos_setores = {
    'ITUB4.SA': 'Financeiro', 
    'BBDC4.SA': 'Financeiro', 
    'BBAS3.SA': 'Financeiro', 
    'SANB11.SA': 'Financeiro', 
    'BPAC11.SA': 'Financeiro', 
    'B3SA3.SA': 'Financeiro', 
    'BBSE3.SA': 'Financeiro', 
    'CXSE3.SA': 'Financeiro', 
    'IRBR3.SA': 'Financeiro', 
    'PSSA3.SA': 'Financeiro',
    'PETR4.SA': 'Petróleo e Gás', 
    'PETR3.SA': 'Petróleo e Gás', 
    'PRIO3.SA': 'Petróleo e Gás', 
    'RECV3.SA': 'Petróleo e Gás', 
    'ENAT3.SA': 'Petróleo e Gás', 
    'RRRP3.SA': 'Petróleo e Gás', 
    'UGPA3.SA': 'Petróleo e Gás', 
    'VBBR3.SA': 'Petróleo e Gás', 
    'CSAN3.SA': 'Petróleo e Gás',
    'VALE3.SA': 'Mineração', 
    'GGBR4.SA': 'Mineração', 
    'GOAU4.SA': 'Mineração', 
    'CSNA3.SA': 'Mineração', 
    'USIM5.SA': 'Mineração', 
    'CMIN3.SA': 'Mineração', 
    'BRAP4.SA': 'Mineração',
    'ELET3.SA': 'Energia', 
    'ELET6.SA': 'Energia', 
    'EQTL3.SA': 'Energia', 
    'CMIG4.SA': 'Energia', 
    'CPLE6.SA': 'Energia', 
    'ENGI11.SA': 'Energia', 
    'TAEE11.SA': 'Energia', 
    'TRPL4.SA': 'Energia', 
    'EGIE3.SA': 'Energia',
    'WEGE3.SA': 'Indústria', 
    'EMBR3.SA': 'Indústria',
    'LREN3.SA': 'Varejo', 
    'MGLU3.SA': 'Varejo', 
    'ARZZ3.SA': 'Varejo', 
    'ALOS3.SA': 'Varejo', 
    'RENT3.SA': 'Varejo', 
    'NTCO3.SA': 'Varejo', 
    'ASAI3.SA': 'Varejo', 
    'CRFB3.SA': 'Varejo', 
    'PCAR3.SA': 'Varejo', 
    'VIVA3.SA': 'Varejo',
    'HAPV3.SA': 'Saúde', 
    'RDOR3.SA': 'Saúde', 
    'RADL3.SA': 'Saúde', 
    'FLRY3.SA': 'Saúde', 
    'MATD3.SA': 'Saúde',
    'ABEV3.SA': 'Alimentos e Bebidas', 
    'JBSS3.SA': 'Alimentos e Bebidas', 
    'MRFG3.SA': 'Alimentos e Bebidas', 
    'BEEF3.SA': 'Alimentos e Bebidas', 
    'BRFS3.SA': 'Alimentos e Bebidas', 
    'SMTO3.SA': 'Alimentos e Bebidas',
    'RAIL3.SA': 'Logística', 
    'CCRO3.SA': 'Logística', 
    'AZUL4.SA': 'Logística', 
    'GOLL4.SA': 'Logística',
    'VIVT3.SA': 'Telecom e TI', 
    'TIMS3.SA': 'Telecom e TI', 
    'TOTVS3.SA': 'Telecom e TI',
    'SBSP3.SA': 'Saneamento', 
    'CSMG3.SA': 'Saneamento', 
    'SAPR11.SA': 'Saneamento',
    'SUZB3.SA': 'Papel e Celulose', 
    'KLBN11.SA': 'Papel e Celulose',
    'CYRE3.SA': 'Construção', 
    'MRVE3.SA': 'Construção', 
    'EZTC3.SA': 'Construção', 
    'TEND3.SA': 'Construção'
}
ativos_lista = list(ativos_setores.keys())

# ==============================================================================
# --- FUNÇÕES DE CARREGAMENTO E APOIO ---
# ==============================================================================
@st.cache_data(ttl=300)
def carregar_dados_geral(ativos, dias):
    hoje = datetime.today().strftime('%Y-%m-%d')
    inicio = (datetime.today() - timedelta(days=dias)).strftime('%Y-%m-%d')
    
    # Download em lote para o painel geral (progresso desativado para logs limpos)
    dados = yf.download(ativos, start=inicio, end=hoje, progress=False)
    return dados['Close']

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
            
            # Validação estrita para não exibir caixas de notícias "Sem título"
            if titulo is not None and titulo != "None" and "Sem título" not in titulo and len(titulo) > 5:
                link = item.find('link').text
                
                fonte_tag = item.find('source')
                if fonte_tag is not None:
                    fonte = fonte_tag.text
                else:
                    fonte = 'Google News'
                    
                pub_date = item.find('pubDate').text
                
                try:
                    partes = pub_date.split(' ')
                    data_formatada = f"{partes[1]} {partes[2]} {partes[3]} • {partes[4][:5]}"
                except:
                    data_formatada = pub_date
                    
                noticias.append({
                    'title': titulo, 
                    'link': link, 
                    'publisher': fonte, 
                    'time': data_formatada
                })
                
        return noticias
    except Exception:
        return []

def fmt_br(val, is_pct=False, currency=False):
    if pd.isna(val) or val is None or val == "-": 
        return "-"
    
    try:
        val_float = float(val)
        texto = f"{val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if is_pct: 
            return f"{texto}%"
        
        if currency: 
            return f"R$ {texto}"
            
        return texto
    except:
        return "-"

def cor_variacao(val):
    if pd.isna(val) or val == "-": 
        return "#2B2E35"
        
    try:
        val_float = float(val)
        if val_float > 0: 
            return "#228B22"
        elif val_float < 0: 
            return "#B22222"
        else: 
            return "#2B2E35"
    except:
        return "#2B2E35"

# ==============================================================================
# --- PROCESSAMENTO DO PAINEL GERAL ---
# ==============================================================================
precos_fechamento = carregar_dados_geral(ativos_lista, 365)
resultados = []

for ativo in ativos_lista:
    df = pd.DataFrame()
    
    if ativo in precos_fechamento.columns:
        df['Close'] = precos_fechamento[ativo]
        
        # Criação das Médias Móveis
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        # Limpeza e captura do último preço válido
        serie_limpa = df['Close'].dropna()
        if not serie_limpa.empty:
            ultimo_preco = float(serie_limpa.iloc[-1])
        else:
            ultimo_preco = 0
            
        # Captura das últimas médias válidas
        serie_sma50 = df['SMA50'].dropna()
        if not serie_sma50.empty:
            sma50 = float(serie_sma50.iloc[-1])
        else:
            sma50 = 0
            
        serie_sma200 = df['SMA200'].dropna()
        if not serie_sma200.empty:
            sma200 = float(serie_sma200.iloc[-1])
        else:
            sma200 = 0
            
        # Cálculo da Variação Diária (%)
        if len(serie_limpa) > 1:
            variacao_diaria = float(serie_limpa.pct_change().iloc[-1] * 100)
        else:
            variacao_diaria = 0.0
            
        # Avaliação de Tendência (Cruzamento de Preço vs Média)
        tendencia_curta = 'Alta' if ultimo_preco > sma50 else 'Baixa'
        tendencia_media = 'Alta' if ultimo_preco > sma50 else 'Baixa'
        
        if sma200 > 0:
            tendencia_longa = 'Alta' if ultimo_preco > sma200 else 'Baixa'
        else:
            tendencia_longa = 'N/A'
        
        # Adiciona ao dicionário de resultados
        resultados.append({
            'Ativo': ativo.replace('.SA', ''), 
            'Setor': ativos_setores[ativo], 
            'Preço (R$)': round(ultimo_preco, 2),
            'Variação (%)': round(variacao_diaria, 2), 
            'Tendência (50D)': tendencia_curta,
            'Tendência (100D)': tendencia_media,
            'Tendência (200D)': tendencia_longa
        })

# Converte resultados para DataFrame final
df_resumo = pd.DataFrame(resultados)

# ==============================================================================
# --- CRIAÇÃO DAS ABAS (TABS) ---
# ==============================================================================
aba_visao_geral, aba_analise_individual = st.tabs([
    "🌐 Visão Geral do Mercado", 
    "🔬 Análise Detalhada por Ativo"
])

# ==============================================================================
# --- ABA 1: VISÃO GERAL DO MERCADO (TREEMAP E TABELA) ---
# ==============================================================================
with aba_visao_geral:
    st.markdown("### 📊 Mapa de Calor do Mercado")
    
    # Estrutura inicial do Plotly Treemap
    ids = ["B3"]
    labels = ["B3"]
    parents = [""]
    values = [0]
    colors = ["#FFFFFF"]
    customdata = [["<b>Painel Geral B3</b>", "<b>B3</b>"]]
    
    # Construção dos nós de Setor
    for setor in df_resumo['Setor'].unique():
        ids.append(setor)
        labels.append(setor)
        parents.append("B3")
        values.append(0)
        colors.append("#FFFFFF")
        customdata.append([f"<b>Setor: {setor}</b>", f"<b>{setor}</b>"])
        
        # Nó fantasma para forçar a cor de fundo do cabeçalho do setor
        ids.append(setor + "_fantasma")
        labels.append("")
        parents.append(setor)
        values.append(0.000001)
        colors.append("#FFFFFF")
        customdata.append(["", ""])

    # Construção dos nós de Ações (Folhas)
    for index, row in df_resumo.iterrows():
        ids.append(row['Ativo'])
        labels.append(row['Ativo'])
        parents.append(row['Setor'])
        values.append(1)
        
        var = row['Variação (%)']
        preco = row['Preço (R$)']
        
        # Aplicação de cores com base na variação
        if var > 0.05:
            colors.append("#228B22") # Verde
        elif var < -0.05:
            colors.append("#B22222") # Vermelho
        else:
            colors.append("#708090") # Cinza
            
        preco_br = fmt_br(preco)
        var_br = f"{var:+.2f}%".replace(".", ",")
        
        # Formatação do texto interno e do texto ao passar o rato (Hover)
        hover_text = f"<b>{row['Ativo']}</b><br>Var: {var_br}<br>Preço: R$ {preco_br}"
        block_text = f"<b>{row['Ativo']}</b><br>R$ {preco_br}<br> {var_br}"
        customdata.append([hover_text, block_text])

    # Geração do Gráfico Treemap
    figura_treemap = go.Figure(go.Treemap(
        ids=ids, 
        labels=labels, 
        parents=parents, 
        values=values, 
        marker_colors=colors,
        customdata=customdata, 
        texttemplate="%{customdata[1]}", 
        textposition="top left", # Alinhamento fiel à imagem enviada
        hovertemplate="%{customdata[0]}<extra></extra>", 
        textfont=dict(color="black", size=14) # Letra a negro fiel à imagem enviada
    ))
    
    figura_treemap.update_layout(
        margin=dict(t=10, l=10, r=10, b=10), 
        height=550, 
        template='plotly_dark'
    )
    
    st.plotly_chart(figura_treemap, use_container_width=True)

    # Tabela Resumo com Filtro de Setor
    st.subheader("📋 Resumo de Indicadores da Grade")
    
    coluna_filtro, coluna_vazia = st.columns([1, 2])
    with coluna_filtro:
        opcoes_setores = ["Todos os Setores"] + sorted(list(df_resumo['Setor'].unique()))
        setor_selecionado = st.selectbox("Filtrar Tabela:", opcoes_setores)
    
    if setor_selecionado == "Todos os Setores":
        df_exibicao = df_resumo
    else:
        df_exibicao = df_resumo[df_resumo['Setor'] == setor_selecionado]
        
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# ==============================================================================
# --- ABA 2: ANÁLISE DETALHADA POR ATIVO ---
# ==============================================================================
with aba_analise_individual:
    coluna_busca, coluna_tempo = st.columns([1, 1])
    
    with coluna_busca:
        ativo_buscado = st.text_input(
            "🔍 Digite o código do ativo (Ex: PETR4, MGLU3):", 
            key="search_asset"
        ).upper().strip()
    
    if ativo_buscado:
        # Tratamento automático para sufixo de ações brasileiras
        if not ativo_buscado.endswith('.SA') and any(char.isdigit() for char in ativo_buscado):
            ativo_buscado += '.SA'
            
        with coluna_tempo:
            opcoes_tempo = ["1 Mês", "6 Meses", "1 Ano", "2 Anos", "5 Anos"]
            janela_tempo = st.radio(
                "Período do Gráfico:", 
                opcoes_tempo, 
                index=2, 
                horizontal=True
            )
            
            mapa_periodos = {
                "1 Mês": "1mo", 
                "6 Meses": "6mo", 
                "1 Ano": "1y", 
                "2 Anos": "2y", 
                "5 Anos": "5y"
            }
            periodo_selecionado = mapa_periodos[janela_tempo]

        with st.spinner("Processando histórico de 10 anos e dados fundamentalistas..."):
            
            ticker_obj = yf.Ticker(ativo_buscado)
            
            # Histórico completo baixado de uma vez para cálculos robustos
            df_hist = yf.download(ativo_buscado, period="10y", progress=False)
            
            if df_hist is None or df_hist.empty:
                st.error("⚠️ Código não encontrado ou sem dados no momento.")
            else:
                # Remoção de MultiIndex que quebra cálculos (depende da versão do pandas/yfinance)
                if isinstance(df_hist.columns, pd.MultiIndex):
                    df_hist.columns = [col[0] for col in df_hist.columns]

                # --------------------------------------------------------------
                # CÁLCULO DE RENTABILIDADES HISTÓRICAS
                # --------------------------------------------------------------
                serie_hist_limpa = df_hist['Close'].dropna()
                
                if not serie_hist_limpa.empty:
                    preco_atual = float(serie_hist_limpa.iloc[-1])
                    
                    def calcular_retorno(serie, dias_uteis):
                        if len(serie) > dias_uteis:
                            preco_antigo = float(serie.iloc[-dias_uteis])
                            if preco_antigo > 0:
                                retorno = ((preco_atual / preco_antigo) - 1) * 100
                                return retorno
                        return "-"

                    retorno_1m = calcular_retorno(serie_hist_limpa, 21)
                    retorno_3m = calcular_retorno(serie_hist_limpa, 63)
                    retorno_1a = calcular_retorno(serie_hist_limpa, 252)
                    retorno_2a = calcular_retorno(serie_hist_limpa, 504)
                    retorno_5a = calcular_retorno(serie_hist_limpa, 1260)
                    retorno_10a = calcular_retorno(serie_hist_limpa, 2520)
                else:
                    preco_atual = 0
                    retorno_1m = retorno_3m = retorno_1a = retorno_2a = retorno_5a = retorno_10a = "-"

                # --------------------------------------------------------------
                # DADOS FUNDAMENTALISTAS (Com tolerância a falhas na Cloud)
                # --------------------------------------------------------------
                info = {}
                try: 
                    info = ticker_obj.info
                except Exception: 
                    pass

                # Variação Anual
                if retorno_1a != "-":
                    valor_var12m = retorno_1a
                else:
                    valor_var12m = info.get('52WeekChange', 0) * 100
                    
                # Múltiplos
                valor_pl = info.get('trailingPE', "-")
                valor_pvp = info.get('priceToBook', "-")
                
                # Dividend Yield
                valor_dy = info.get('trailingAnnualDividendYield')
                
                if valor_dy is None:
                    valor_dy = info.get('dividendYield')
                    
                if valor_dy is not None and valor_dy != "-": 
                    valor_dy = valor_dy * 100
                else:
                    valor_dy = "-"

                # --------------------------------------------------------------
                # BLOCO HTML: CARDS ESTILO STATUS INVEST
                # --------------------------------------------------------------
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">COTAÇÃO</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(preco_atual, currency=True)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">VARIAÇÃO (12M)</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: {cor_variacao(valor_var12m)};">{fmt_br(valor_var12m, is_pct=True)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">P/L</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(valor_pl)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">P/VP</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(valor_pvp)}</div>
                    </div>
                    <div style="flex: 1; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; text-align: center; overflow: hidden;">
                        <div style="background-color: #2b2e35; color: #d4af37; padding: 8px; font-weight: bold; font-size: 13px;">DY (12M)</div>
                        <div style="padding: 15px; font-size: 22px; font-weight: bold; color: white;">{fmt_br(valor_dy, is_pct=True)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --------------------------------------------------------------
                # BLOCO HTML: TABELA DE RENTABILIDADE HISTÓRICA
                # --------------------------------------------------------------
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
                            <td style="color: {cor_variacao(retorno_1m)};">{fmt_br(retorno_1m, is_pct=True)}</td>
                            <td style="color: {cor_variacao(retorno_3m)};">{fmt_br(retorno_3m, is_pct=True)}</td>
                            <td style="color: {cor_variacao(retorno_1a)};">{fmt_br(retorno_1a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(retorno_2a)};">{fmt_br(retorno_2a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(retorno_5a)};">{fmt_br(retorno_5a, is_pct=True)}</td>
                            <td style="color: {cor_variacao(retorno_10a)};">{fmt_br(retorno_10a, is_pct=True)}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                # --------------------------------------------------------------
                # EXPORTAÇÃO CSV
                # --------------------------------------------------------------
                conteudo_csv = df_hist.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Baixar Histórico Completo e Indicadores Técnicos (.CSV)",
                    data=conteudo_csv,
                    file_name=f"{ativo_buscado}_historico.csv",
                    mime="text/csv"
                )
                st.markdown("<br>", unsafe_allow_html=True)

                # --------------------------------------------------------------
                # PROCESSAMENTO TÉCNICO (MÉDIAS, DIDI E DMI)
                # --------------------------------------------------------------
                df_hist['SMA20'] = df_hist['Close'].rolling(window=20).mean()
                df_hist['SMA50'] = df_hist['Close'].rolling(window=50).mean()
                df_hist['SMA100'] = df_hist['Close'].rolling(window=100).mean()
                df_hist['SMA200'] = df_hist['Close'].rolling(window=200).mean()
                
                # Didi Index
                linha_rapida = df_hist['Close'].rolling(window=3).mean()
                linha_referencia = df_hist['Close'].rolling(window=8).mean()
                linha_lenta = df_hist['Close'].rolling(window=20).mean()
                
                df_hist['DidiFast'] = linha_rapida - linha_referencia
                df_hist['DidiSlow'] = linha_lenta - linha_referencia
                
                # ADX e DMI
                true_range_1 = df_hist['High'] - df_hist['Low']
                true_range_2 = (df_hist['High'] - df_hist['Close'].shift(1)).abs()
                true_range_3 = (df_hist['Low'] - df_hist['Close'].shift(1)).abs()
                
                dataframe_tr = pd.concat([true_range_1, true_range_2, true_range_3], axis=1)
                true_range = dataframe_tr.max(axis=1)
                
                movimento_alto = df_hist['High'] - df_hist['High'].shift(1)
                movimento_baixo = df_hist['Low'].shift(1) - df_hist['Low']
                
                direcional_positivo = pd.Series(
                    np.where(
                        (movimento_alto > movimento_baixo) & (movimento_alto > 0), 
                        movimento_alto, 
                        0
                    ), 
                    index=df_hist.index
                )
                
                direcional_negativo = pd.Series(
                    np.where(
                        (movimento_baixo > movimento_alto) & (movimento_baixo > 0), 
                        movimento_baixo, 
                        0
                    ), 
                    index=df_hist.index
                )
                
                tr_suavizado = true_range.rolling(8).sum()
                
                df_hist['PDI'] = 100 * direcional_positivo.rolling(8).sum() / tr_suavizado
                df_hist['NDI'] = 100 * direcional_negativo.rolling(8).sum() / tr_suavizado
                
                diferenca_dmi = np.abs(df_hist['PDI'] - df_hist['NDI'])
                soma_dmi = df_hist['PDI'] + df_hist['NDI']
                
                df_hist['ADX'] = (100 * (diferenca_dmi / soma_dmi)).rolling(window=8).mean()

                # --------------------------------------------------------------
                # CORTE DE TEMPO PARA OS GRÁFICOS
                # --------------------------------------------------------------
                if janela_tempo == "1 Mês":
                    limite_data = datetime.now() - timedelta(days=30)
                elif janela_tempo == "6 Meses":
                    limite_data = datetime.now() - timedelta(days=180)
                elif janela_tempo == "1 Ano":
                    limite_data = datetime.now() - timedelta(days=365)
                elif janela_tempo == "2 Anos":
                    limite_data = datetime.now() - timedelta(days=730)
                else:
                    limite_data = datetime.now() - timedelta(days=1825)
                    
                df_plot = df_hist[df_hist.index >= limite_data].copy()
                
                # Cores Dinâmicas Volume e Didi
                cores_volume = []
                for row_tuple in df_plot.itertuples():
                    if row_tuple.Close >= row_tuple.Open:
                        cores_volume.append('#228B22')
                    else:
                        cores_volume.append('#B22222')
                        
                cores_didi_fundo = []
                for p_val, n_val in zip(df_plot['PDI'], df_plot['NDI']):
                    if p_val > n_val:
                        cores_didi_fundo.append('rgba(0, 150, 0, 0.12)')
                    else:
                        cores_didi_fundo.append('rgba(200, 0, 0, 0.12)')

                # --------------------------------------------------------------
                # ESTRUTURA VISUAL: GRÁFICOS À ESQUERDA, NOTÍCIAS À DIREITA
                # --------------------------------------------------------------
                coluna_graficos, coluna_noticias = st.columns([3, 1])

                with coluna_graficos:
                    # Configuração Subplots
                    figura_tecnica = make_subplots(
                        rows=3, 
                        cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.6, 0.20, 0.20],
                        specs=[
                            [{"secondary_y": True}], 
                            [{"secondary_y": False}], 
                            [{"secondary_y": False}]
                        ],
                        subplot_titles=(
                            'Gráfico de Preço e Volume', 
                            'Didi Plus (3, 8, 20)', 
                            'DMI / ADX (8)'
                        )
                    )
                    
                    if not df_plot.empty:
                        # Preço Principal
                        figura_tecnica.add_trace(
                            go.Candlestick(
                                x=df_plot.index, 
                                open=df_plot['Open'], 
                                high=df_plot['High'], 
                                low=df_plot['Low'], 
                                close=df_plot['Close'], 
                                name='Candlestick'
                            ), 
                            row=1, 
                            col=1, 
                            secondary_y=False
                        )
                        
                        # Médias
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['SMA50'], 
                                mode='lines', 
                                name='Média 50', 
                                line=dict(color='#00BFFF', width=1.5)
                            ), 
                            row=1, 
                            col=1, 
                            secondary_y=False
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['SMA200'], 
                                mode='lines', 
                                name='Média 200', 
                                line=dict(color='white', width=1.5)
                            ), 
                            row=1, 
                            col=1, 
                            secondary_y=False
                        )
                        
                        # Volume Secundário
                        figura_tecnica.add_trace(
                            go.Bar(
                                x=df_plot.index, 
                                y=df_plot['Volume'], 
                                name='Volume', 
                                marker_color=cores_volume, 
                                opacity=0.35
                            ), 
                            row=1, 
                            col=1, 
                            secondary_y=True
                        )
                        
                        # Didi Fundo e Linhas
                        maximo_y_didi = max(df_plot['DidiFast'].abs().max(), df_plot['DidiSlow'].abs().max()) * 1.4
                        if pd.isna(maximo_y_didi) or maximo_y_didi == 0: 
                            maximo_y_didi = 1
                            
                        figura_tecnica.add_trace(
                            go.Bar(
                                x=df_plot.index, 
                                y=[maximo_y_didi] * len(df_plot), 
                                marker_color=cores_didi_fundo, 
                                marker_line_width=0, 
                                showlegend=False, 
                                hoverinfo='skip'
                            ), 
                            row=2, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Bar(
                                x=df_plot.index, 
                                y=[-maximo_y_didi] * len(df_plot), 
                                marker_color=cores_didi_fundo, 
                                marker_line_width=0, 
                                showlegend=False, 
                                hoverinfo='skip'
                            ), 
                            row=2, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=np.zeros(len(df_plot)), 
                                mode='lines', 
                                name='Eixo Zero', 
                                line=dict(color='white', width=1, dash='dot')
                            ), 
                            row=2, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['DidiSlow'], 
                                mode='lines', 
                                name='Linha Lenta', 
                                line=dict(color='#FF00FF', width=2)
                            ), 
                            row=2, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['DidiFast'], 
                                mode='lines', 
                                name='Linha Rápida', 
                                line=dict(color='#00BFFF', width=2)
                            ), 
                            row=2, 
                            col=1
                        )
                        
                        # ADX
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['ADX'], 
                                mode='lines', 
                                name='Força (ADX)', 
                                line=dict(color='white', width=1.5)
                            ), 
                            row=3, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['PDI'], 
                                mode='lines', 
                                name='Compradores (+DI)', 
                                line=dict(color='#00BFFF', width=1.5)
                            ), 
                            row=3, 
                            col=1
                        )
                        
                        figura_tecnica.add_trace(
                            go.Scatter(
                                x=df_plot.index, 
                                y=df_plot['NDI'], 
                                mode='lines', 
                                name='Vendedores (-DI)', 
                                line=dict(color='#FFD700', width=1.5)
                            ), 
                            row=3, 
                            col=1
                        )

                    # Estilos Finais Gráfico Principal
                    figura_tecnica.update_yaxes(
                        title_text="Preço (R$)", 
                        side="right", 
                        row=1, 
                        col=1, 
                        secondary_y=False
                    )
                    
                    figura_tecnica.update_yaxes(
                        showgrid=False, 
                        showticklabels=False, 
                        range=[0, df_plot['Volume'].max() * 4] if not df_plot.empty else [0, 1], 
                        row=1, 
                        col=1, 
                        secondary_y=True
                    )
                    
                    figura_tecnica.update_layout(
                        template='plotly_dark', 
                        height=900, 
                        showlegend=True, 
                        legend=dict(
                            orientation="h", 
                            yanchor="bottom", 
                            y=1.02, 
                            xanchor="right", 
                            x=1
                        ), 
                        barmode='relative', 
                        xaxis_rangeslider_visible=False
                    )
                    
                    st.plotly_chart(figura_tecnica, use_container_width=True)

                    # ----------------------------------------------------------
                    # BENCHMARKS FIXOS E BLINDADOS CONTRA ERROS
                    # ----------------------------------------------------------
                    st.markdown("### 📊 Comparativo Contra Benchmarks Nacionais")
                    
                    figura_benchmarks = go.Figure()
                    
                    if not df_plot.empty:
                        primeiro_preco_ativo = float(df_plot['Close'].iloc[0])
                        if primeiro_preco_ativo > 0:
                            ativo_normalizado = (df_plot['Close'] / primeiro_preco_ativo - 1) * 100
                            
                            figura_benchmarks.add_trace(
                                go.Scatter(
                                    x=ativo_normalizado.index, 
                                    y=ativo_normalizado, 
                                    name=ativo_buscado, 
                                    line=dict(color='#00BFFF', width=2.5)
                                )
                            )
                    
                    mapa_indicadores = {
                        'IBOV (Mercado Geral)': '^BVSP', 
                        'IFIX (Fundos Imobiliários)': 'XFIX11.SA', 
                        'SMLL (Small Caps)': 'SMAL11.SA', 
                        'IDIV (Pagadoras de Dividendos)': 'DIVO11.SA', 
                        'IVVB11 (S&P 500)': 'IVVB11.SA'
                    }
                    
                    for nome_indicador, ticker_indicador in mapa_indicadores.items():
                        try:
                            # Busca ignorando erros de rede
                            df_benchmark = yf.download(ticker_indicador, start=limite_data, progress=False)
                            
                            if df_benchmark is not None and not df_benchmark.empty:
                                if isinstance(df_benchmark.columns, pd.MultiIndex):
                                    df_benchmark.columns = [col[0] for col in df_benchmark.columns]
                                    
                                df_benchmark = df_benchmark[~df_benchmark.index.duplicated(keep='first')]
                                
                                if 'Close' in df_benchmark.columns:
                                    serie_bench_limpa = df_benchmark['Close'].dropna()
                                    
                                    # Validação crucial contra Index Error
                                    if not serie_bench_limpa.empty and len(serie_bench_limpa) > 0:
                                        primeiro_preco_benchmark = float(serie_bench_limpa.iloc[0])
                                        
                                        if primeiro_preco_benchmark > 0:
                                            benchmark_normalizado = (serie_bench_limpa / primeiro_preco_benchmark - 1) * 100
                                            
                                            figura_benchmarks.add_trace(
                                                go.Scatter(
                                                    x=benchmark_normalizado.index, 
                                                    y=benchmark_normalizado, 
                                                    name=nome_indicador, 
                                                    line=dict(width=1.5, dash='dot')
                                                )
                                            )
                        except Exception:
                            pass # Ignora silenciosamente e mantem o app de pé
                            
                    figura_benchmarks.update_layout(
                        template='plotly_dark', 
                        height=400, 
                        yaxis_title="Desempenho Acumulado (%)",
                        legend=dict(
                            orientation="h", 
                            yanchor="bottom", 
                            y=1.02, 
                            xanchor="right", 
                            x=1
                        )
                    )
                    
                    st.plotly_chart(figura_benchmarks, use_container_width=True)

                with coluna_noticias:
                    st.markdown("### 📰 Notícias Corporativas")
                    lista_noticias = buscar_noticias_google(ativo_buscado)
                    
                    if not lista_noticias:
                        st.info("Não há comunicados recentes registados para este ativo no feed do Google Notícias.")
                    else:
                        for noticia in lista_noticias:
                            titulo_noticia = noticia['title']
                            link_noticia = noticia['link']
                            fonte_noticia = noticia['publisher']
                            data_noticia = noticia['time']
                            
                            st.markdown(f"""
                            <div style="border: 1px solid #444444; border-radius: 5px; padding: 10px; margin-bottom: 12px; background-color: #1e1e1e;">
                                <a href="{link_noticia}" target="_blank" style="color: #00BFFF; text-decoration: none; font-weight: bold; font-size: 14px;">{titulo_noticia}</a>
                                <p style="color: #888888; font-size: 11px; margin: 5px 0 0 0;">{fonte_noticia} • {data_noticia}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                # --------------------------------------------------------------
                # AGENDA CORPORATIVA
                # --------------------------------------------------------------
                st.divider()
                st.markdown("### 📅 Agenda de Eventos")
                
                coluna_evento_1, coluna_evento_2 = st.columns(2)
                
                balanco_timestamp = info.get('earningsTimestamp')
                if balanco_timestamp is None:
                    balanco_timestamp = info.get('earningsTimestampStart', 0)
                    
                if balanco_timestamp:
                    data_balanco = datetime.fromtimestamp(balanco_timestamp).strftime('%d/%m/%Y')
                else:
                    data_balanco = 'Sem previsão oficial'
                    
                dividendo_timestamp = info.get('exDividendDate', 0)
                if dividendo_timestamp:
                    data_dividendo = datetime.fromtimestamp(dividendo_timestamp).strftime('%d/%m/%Y')
                else:
                    data_dividendo = 'Indisponível na base'
                
                coluna_evento_1.info(f"🧾 **Próxima Divulgação de Resultados (Balanço):** {data_balanco}")
                coluna_evento_2.success(f"💰 **Data Com (Direito a Proventos):** {data_dividendo}")
