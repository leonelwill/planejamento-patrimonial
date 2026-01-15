import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import json
import io

# --- Configuração da Página ---
st.set_page_config(
    page_title="Planejamento Patrimonial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Personalizado ---
st.markdown("""
    <style>
    /* Estilo Geral Dark */
    .stApp {
        background-color: #0E1117;
    }
    h1 { text-align: center; color: #FFFFFF !important; padding-bottom: 20px; }
    h2, h3, h4 { color: #FFFFFF !important; }
    
    /* Box do Cliente */
    .client-box {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #FFD700;
        margin-top: 20px;
    }
    .warning-box {
        background-color: #332a00;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #FFD700;
        margin-bottom: 15px;
    }
    .solution-box {
        background-color: #0e2a18;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00FF7F;
        margin-top: 10px;
    }
    
    /* Botões de Ação no Topo */
    .stButton button {
        width: 100%;
    }
    
    /* Ajuste da tabela */
    div[data-testid="stDataFrame"] { width: 100%; }
    input { text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_aliquota_pl_sp_fixa(valor_base):
    if valor_base <= 353600.00: return 2.0
    elif valor_base <= 3005600.00: return 4.0
    elif valor_base <= 9900800.00: return 6.0
    else: return 8.0

def get_color_by_tax(tax):
    if tax > 30: return '#FF4B4B'
    elif tax > 10: return '#FFD700'
    else: return '#00FF7F'

# --- Gerenciamento de Estado (Salvar/Carregar) ---
# Lista de chaves que queremos salvar
keys_to_save = [
    "nome_cliente", "is_casado", "nome_conjuge", 
    "ano_nasc_cliente", "ano_nasc_conjuge", "regime_casamento",
    "v_imoveis", "v_aplicacoes", "v_veiculos", "v_empresas", "v_outros",
    "v_prev", "incluir_prev", "estado_selecionado", "toggle_pl",
    "aliq_itcmd_input", "aliq_hon", "aliq_cart",
    "cobertura_sugerida", "anos_pagamento", "premio_anual", "taxa_reajuste"
]

def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            for key, value in data.items():
                if key in keys_to_save:
                    st.session_state[key] = value
            st.success("Dados carregados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")

def limpar_dados():
    for key in keys_to_save:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- Classe PDF Avançada (Dark Mode Layout) ---
class PDFReport(FPDF):
    def header(self):
        # Fundo Preto Total
        self.set_fill_color(14, 17, 23) 
        self.rect(0, 0, 297, 420, 'F') # A4
        
        # Título
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'Relatório de Planejamento Patrimonial', 0, 1, 'C')
        self.ln(5)

    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 255, 127) # Verde Neon
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(0, 255, 127)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def dark_metric_box(self, label, value, color_r=30, color_g=30, color_b=30, border=False):
        self.set_fill_color(color_r, color_g, color_b)
        if border:
            self.set_draw_color(255, 75, 75) # Vermelho se for alerta
            self.set_line_width(0.5)
        else:
            self.set_draw_color(50, 50, 50)
        
        x = self.get_x()
        y = self.get_y()
        self.rect(x, y, 90, 25, 'FD')
        
        self.set_xy(x+5, y+5)
        self.set_font('Arial', '', 10)
        self.set_text_color(200, 200, 200)
        self.cell(80, 5, label, 0, 2)
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(80, 8, value, 0, 0)
        self.set_xy(x + 95, y) # Move para o lado para proximo box

    def create_table_row(self, data, header=False):
        if header:
            self.set_fill_color(50, 50, 50)
            self.set_text_color(0, 255, 127)
            self.set_font('Arial', 'B', 9)
        else:
            self.set_fill_color(30, 30, 30)
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', '', 9)
            
        # Larguras das colunas
        w = [20, 20, 40, 40, 40, 30] 
        
        for i, datum in enumerate(data):
            self.cell(w[i], 8, str(datum), 1, 0, 'C', True)
        self.ln()

# --- BARRA LATERAL (MENU DE ARQUIVO) ---
with st.sidebar:
    st.header("📂 Gerenciar Dados")
    
    # Botão Salvar
    # Criamos um dict com os valores atuais
    current_data = {key: st.session_state.get(key) for key in keys_to_save}
    json_str = json.dumps(current_data)
    
    st.download_button(
        label="💾 Salvar Preenchimento (JSON)",
        data=json_str,
        file_name="planejamento_patrimonial.json",
        mime="application/json"
    )
    
    # Botão Carregar
    uploaded_file = st.file_uploader("📂 Carregar Preenchimento", type=["json"])
    if uploaded_file:
        if st.button("Confirmar Carregamento"):
            carregar_dados(uploaded_file)
            
    st.divider()
    
    # Botão Limpar
    if st.button("🗑️ Limpar Tudo", type="primary"):
        limpar_dados()

# --- Título e Dados do Cliente ---
st.title("Calculadora de Planejamento Patrimonial")

col_dados1, col_dados2, col_dados3 = st.columns([1.5, 0.5, 1.5])
with col_dados1:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva", key="nome_cliente")
with col_dados2:
    st.write("") 
    st.write("") 
    is_casado = st.toggle("Casado(a)?", key="is_casado")
with col_dados3:
    if is_casado:
        nome_conjuge = st.text_input("Nome do Cônjuge", placeholder="Ex: Maria da Silva", key="nome_conjuge")

col_nasc1, col_nasc2, col_nasc3 = st.columns([1.5, 0.5, 1.5])
ano_atual = datetime.now().year
idade_cliente = 0
idade_conjuge = 0
regime_casamento = "Separação Total de Bens"
percentual_meacao = 0.0

with col_nasc1:
    ano_nasc_cliente = st.number_input("Ano de Nascimento (Cliente)", min_value=1920, max_value=ano_atual, value=1975, step=1, key="ano_nasc_cliente")
    idade_cliente = ano_atual - ano_nasc_cliente

with col_nasc2: st.write("")

with col_nasc3:
    if is_casado:
        col_c_nasc, col_c_reg = st.columns([1, 1])
        with col_c_nasc:
            ano_nasc_conjuge = st.number_input("Ano Nascimento (Cônjuge)", min_value=1920, max_value=ano_atual, value=1978, step=1, key="ano_nasc_conjuge")
            idade_conjuge = ano_atual - ano_nasc_conjuge
        with col_c_reg:
            regime_casamento = st.selectbox("Regime de Bens", 
                ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Separação Total de Bens", "Participação Final nos Aquestos"], key="regime_casamento")
            if regime_casamento in ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Participação Final nos Aquestos"]:
                percentual_meacao = 0.50
            else:
                percentual_meacao = 0.0

st.markdown("---")

col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# SEÇÃO 1: PATRIMÔNIO
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores totais (Enter para formatar)")
    
    val_imoveis = st.number_input("Imóveis", min_value=0.0, step=100000.0, format="%.2f", key="v_imoveis")
    val_aplicacoes = st.number_input("Aplicações Financeiras", min_value=0.0, step=100000.0, format="%.2f", key="v_aplicacoes")
    val_veiculos = st.number_input("Veículos", min_value=0.0, step=100000.0, format="%.2f", key="v_veiculos")
    val_empresas = st.number_input("Participação em Empresas", min_value=0.0, step=100000.0, format="%.2f", key="v_empresas")
    val_outros = st.number_input("Outros Bens", min_value=0.0, step=100000.0, format="%.2f", key="v_outros")
    
    col_prev_input, col_prev_check = st.columns([0.7, 0.3])
    with col_prev_input:
        val_previdencia = st.number_input("Saldo em Previdência *", min_value=0.0, step=100000.0, format="%.2f", key="v_prev")
    with col_prev_check:
        st.write("") 
        st.write("")
        incluir_prev = st.checkbox("Incluir?", value=False, key="incluir_prev")
    
    st.caption("* Previdência (VGBL) geralmente não entra no inventário.")

    total_patrimonio_bruto = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if incluir_prev:
        total_patrimonio_bruto += val_previdencia

    valor_meacao = total_patrimonio_bruto * percentual_meacao
    base_calculo_imposto = total_patrimonio_bruto - valor_meacao

    st.divider()
    col_total1, col_total2 = st.columns([1,1])
    with col_total1:
        st.metric(label="Patrimônio Total", value=format_currency(total_patrimonio_bruto))
    with col_total2:
        if is_casado and percentual_meacao > 0:
            st.metric(label="Base Tributável (Sua Parte)", value=format_currency(base_calculo_imposto), delta="- Meação do Cônjuge")
        else:
            st.metric(label="Base Tributável", value=format_currency(base_calculo_imposto))

# SEÇÃO 2: CUSTOS DE INVENTÁRIO
with col_custos:
    st.subheader("2. Custos de Sucessão")
    
    col_uf, col_pl = st.columns([1, 1])
    with col_uf:
        estados = ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"]
        estado_selecionado = st.selectbox("Estado Base:", estados, key="estado_selecionado")
    
    with col_pl:
        st.write("") 
        st.write("") 
        usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    if 'ultimo_estado_pl' not in st.session_state: st.session_state.ultimo_estado_pl = usar_pl
    if 'aliq_itcmd_input' not in st.session_state: st.session_state.aliq_itcmd_input = 4.0

    val_sugerido = 4.0
    if usar_pl:
        val_sugerido = obter_aliquota_pl_sp_fixa(base_calculo_imposto)
    elif estado_selecionado == "Minas Gerais (MG)":
        val_sugerido = 5.0
    
    if st.session_state.ultimo_estado_pl != usar_pl:
        st.session_state.aliq_itcmd_input = val_sugerido
        st.session_state.ultimo_estado_pl = usar_pl

    st.markdown("#### Detalhamento (Sobre a Base Tributável)")
    
    c_itcmd1, c_itcmd2, c_itcmd3 = st.columns([3, 1.5, 2])
    with c_itcmd1: st.write("ITCMD (Imposto)")
    with c_itcmd2: aliquota_itcmd = st.number_input("Aliq ITCMD", min_value=0.0, max_value=20.0, step=0.5, label_visibility="collapsed", key="aliq_itcmd_input")
    with c_itcmd3: 
        val_itcmd = base_calculo_imposto * (aliquota_itcmd / 100)
        st.write(f"**{format_currency(val_itcmd)}**")

    c_hon1, c_hon2, c_hon3 = st.columns([3, 1.5, 2])
    with c_hon1: st.write("Honorários Advocatícios")
    with c_hon2: aliquota_hon = st.number_input("Aliq Hon", value=6.0, step=0.5, label_visibility="collapsed", key="aliq_hon")
    with c_hon3: 
        val_hon = base_calculo_imposto * (aliquota_hon / 100)
        st.write(f"{format_currency(val_hon)}")

    c_cart1, c_cart2, c_cart3 = st.columns([3, 1.5, 2])
    with c_cart1: st.write("Custos Cartório/Outros")
    with c_cart2: aliquota_cart = st.number_input("Aliq Cart", value=2.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
    with c_cart3: 
        val_cart = base_calculo_imposto * (aliquota_cart / 100)
        st.write(f"{format_currency(val_cart)}")

    st.divider()

    custo_total = val_itcmd + val_hon + val_cart
    percentual_total = (custo_total / base_calculo_imposto * 100) if base_calculo_imposto > 0 else 0

    st.markdown(
        f"""
        <div style="background-color: #4a1515; padding: 15px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center;">
            <p style="color: white; margin:0; font-size: 1.2rem;">Custo Inventário ({nome_cliente if nome_cliente else 'Cliente'})</p>
            <h1 style="color: #ff4b4b; margin: 5px 0; font-size: 2.8rem;">{format_currency(custo_total)}</h1>
            <p style="color: #ddd; margin:0;">Comprometimento da Herança: <b>{percentual_total:.2f}%</b></p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    if is_casado and percentual_meacao > 0:
        st.markdown(f"""
        <div style="margin-top: 10px; text-align: center; color: #888; font-size: 0.9rem;">
            ⚠️ <b>Atenção:</b> O cônjuge ({nome_conjuge}) possui exposição idêntica de <b>{format_currency(custo_total)}</b> sobre a parte dele(a).
        </div>
        """, unsafe_allow_html=True)

    if usar_pl:
        custo_base_itcmd = base_calculo_imposto * 0.04
        delta = val_itcmd - custo_base_itcmd
        if delta > 0:
            st.error(f"🚨 IMPACTO DA NOVA LEI: + {format_currency(delta)} de Imposto a pagar.")

# SEÇÃO 3: CENÁRIO GLOBAL
st.write("")
st.subheader("3. Cenário Global de Sucessão")
st.caption("Verde: ≤10% | Amarelo: 11-30% | Vermelho: >30%")

aliquota_efetiva = aliquota_itcmd
data_globo = [
    {"pais": "Japão", "lat": 36.204, "lon": 138.252, "tax": 55},
    {"pais": "Coreia do Sul", "lat": 35.907, "lon": 127.766, "tax": 50},
    {"pais": "França", "lat": 46.227, "lon": 2.213, "tax": 45},
    {"pais": "EUA", "lat": 37.090, "lon": -95.712, "tax": 40},
    {"pais": "Reino Unido", "lat": 55.378, "lon": -3.436, "tax": 40},
    {"pais": "Alemanha", "lat": 51.165, "lon": 10.451, "tax": 30},
    {"pais": "Brasil (Você)", "lat": -14.235, "lon": -51.925, "tax": aliquota_efetiva},
    {"pais": "Chile", "lat": -35.675, "lon": -71.543, "tax": 25},
    {"pais": "Equador", "lat": -1.831, "lon": -78.183, "tax": 35},
    {"pais": "Peru", "lat": -9.190, "lon": -75.015, "tax": 4},
    {"pais": "Argentina", "lat": -38.416, "lon": -63.616, "tax": 5},
    {"pais": "Uruguai", "lat": -32.522, "lon": -55.765, "tax": 4},
]
df_globo = pd.DataFrame(data_globo)
df_globo['color'] = df_globo['tax'].apply(get_color_by_tax)
df_globo['size'] = df_globo['pais'].apply(lambda x: 25 if "Você" in x else 12)
df_chart = df_globo.sort_values(by='tax', ascending=True)

col_chart, col_globo = st.columns([1, 1], gap="medium")
with col_chart:
    fig_bar = px.bar(df_chart, x='tax', y='pais', orientation='h', text='tax', title="Ranking de Alíquotas Máximas")
    fig_bar.update_traces(marker_color=df_chart['color'], texttemplate='%{text:.1f}%', textposition='outside')
    fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white',
        xaxis=dict(showgrid=False, title="Alíquota (%)", range=[0, 60]), yaxis=dict(title=None), margin=dict(l=0, r=0, t=40, b=0), height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_globo:
    fig_globe = go.Figure(data=go.Scattergeo(
        lon = df_globo['lon'], lat = df_globo['lat'], text = df_globo['pais'] + ": " + df_globo['tax'].astype(str) + "%",
        mode = 'markers', marker = dict(size = df_globo['size'], color = df_globo['color'], line = dict(width=1, color='white'), opacity = 0.9)
    ))
    fig_globe.update_layout(geo = dict(projection_type = "orthographic", showland = True, landcolor = "#f3f4f6", showocean = True, oceancolor = "#a4d4f2", showcountries = True, countrycolor = "#888888", projection_rotation = dict(lon=-50, lat=-15, roll=0)),
        margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', height=400, font=dict(color="black"))
    st.plotly_chart(fig_globe, use_container_width=True)

# SEÇÃO 5: SOLUÇÃO (SIMULADOR EVOLUTIVO)
st.markdown("---")
st.subheader("🛠️ Solução: Liquidez e Alavancagem Fiscal")

if is_casado and percentual_meacao > 0:
    st.markdown(f"""
    <div class="warning-box">
        <b>⚠️ Atenção ao Casal:</b> Devido ao regime de <b>{regime_casamento}</b>, 
        a simulação abaixo considera a <b>parte individual</b>. O ideal é duplicar a proteção.
    </div>
    """, unsafe_allow_html=True)

col_sol_1, col_sol_2, col_sol_3 = st.columns([1, 1, 1])
with col_sol_1:
    cobertura_sugerida = st.number_input("Capital Segurado Necessário (Hoje)", value=custo_total, step=50000.0, format="%.2f", key="cobertura_sugerida")
with col_sol_2:
    anos_pagamento = st.slider("Tempo de Pagamento (Anos)", 1, 30, 10, key="anos_pagamento")
with col_sol_3:
    premio_anual = st.number_input("Prêmio Anual Inicial (Investimento)", value=(cobertura_sugerida * 0.04), step=1000.0, format="%.2f", key="premio_anual")
    taxa_reajuste = st.number_input("Taxa de Reajuste Anual (IPCA/IGP-M %)", value=5.0, step=0.5, format="%.1f", key="taxa_reajuste")

st.write("### 📈 Evolução da Liquidez e Multiplicador")

if 'simulacao_anos' not in st.session_state:
    st.session_state.simulacao_anos = 16

data_simulacao = []
capital_atual = cobertura_sugerida
premio_atual = premio_anual
acumulado = 0.0
idade_atual = idade_cliente

for i in range(1, st.session_state.simulacao_anos + 1):
    ano_calendario = ano_atual + i
    idade_simulada = idade_atual + i
    
    if i <= anos_pagamento:
        aporte_do_ano_str = format_currency(premio_atual)
        acumulado += premio_atual
        acumulado_str = format_currency(acumulado)
        if acumulado > 0:
            alavancagem_x = f"{(capital_atual / acumulado):.1f}x"
        else:
            alavancagem_x = "0x"
        premio_proximo = premio_atual * (1 + (taxa_reajuste/100))
    else:
        aporte_do_ano_str = "-"
        acumulado_str = "-"
        alavancagem_x = "-"
        premio_proximo = 0.0

    data_simulacao.append({
        "Ano": ano_calendario,
        "Idade": idade_simulada,
        "Capital Segurado": format_currency(capital_atual),
        "Aporte Anual": aporte_do_ano_str,
        "Total Pago": acumulado_str,
        "Multiplicador": alavancagem_x
    })
    
    capital_atual = capital_atual * (1 + (taxa_reajuste/100))
    premio_atual = premio_proximo

df_simulacao = pd.DataFrame(data_simulacao)

def highlight_mult(s):
    return ['color: #00FF7F; font-weight: bold' if col == 'Multiplicador' else '' for col in s.index]

styler = df_simulacao.style.apply(highlight_mult, axis=1)
styler.set_properties(**{'background-color': '#262730', 'color': 'white', 'border-color': '#444444'})
st.dataframe(styler, use_container_width=True, hide_index=True)

if st.button("Carregar +10 Anos"):
    st.session_state.simulacao_anos += 10
    st.rerun()

# SEÇÃO 6: DIAGNÓSTICO E PDF
st.markdown("### 6. Diagnóstico Final & Relatório")

saudacao = f"Prezados <b>{nome_cliente}</b> e <b>{nome_conjuge}</b>" if is_casado and nome_conjuge else f"Prezado(a) <b>{nome_cliente}</b>"
texto_meacao = f"Considerando o regime de <b>{regime_casamento}</b>, calculamos o risco individual de cada cônjuge." if is_casado else "Cálculo realizado sobre a totalidade dos bens."

texto_diagnostico = f"""
<div class="client-box">
    <p class="client-text">
        {saudacao}, o patrimônio total da família é de <span class="highlight">{format_currency(total_patrimonio_bruto)}</span>.
        {texto_meacao}
    </p>
    <p class="client-text">
        Identificamos um custo sucessório estimado de <span class="highlight">{format_currency(custo_total)}</span>.
        A solução de liquidez permite quitar esse custo com um deságio financeiro significativo.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)

# --- BOTÃO DOWNLOAD PDF ---
if st.button("📄 Baixar Relatório Completo (PDF Style)"):
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        # 1. Dados Iniciais
        pdf.section_title("1. Dados do Cliente e Patrimonio")
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(220, 220, 220)
        pdf.cell(0, 7, f"Cliente: {nome_cliente} (Idade: {ano_atual - ano_nasc_cliente})", 0, 1)
        if is_casado: pdf.cell(0, 7, f"Conjuge: {nome_conjuge} (Idade: {ano_atual - ano_nasc_conjuge}) - {regime_casamento}", 0, 1)
        pdf.ln(3)
        
        # Boxes de Patrimonio
        pdf.dark_metric_box("Patrimonio Total", format_currency(total_patrimonio_bruto), 30, 30, 30)
        pdf.dark_metric_box("Base Tributavel", format_currency(base_calculo_imposto), 30, 30, 30)
        pdf.ln(30)
        
        # 2. Custos
        pdf.section_title("2. Custos de Sucessao (Estimado)")
        pdf.cell(0, 7, f"Estado Base: {estado_selecionado} | PL 7/2024: {'Sim' if usar_pl else 'Nao'}", 0, 1)
        
        # Box de Destaque Vermelho
        pdf.ln(3)
        pdf.dark_metric_box("Custo Inventario", format_currency(custo_total), 60, 20, 20, border=True) # Avermelhado
        pdf.dark_metric_box("% do Patrimonio", f"{percentual_total:.2f}%", 30, 30, 30)
        pdf.ln(30)
        
        # 3. Solução
        pdf.section_title("3. Solucao de Liquidez (Seguro)")
        pdf.cell(0, 7, f"Capital Segurado: {format_currency(cobertura_sugerida)}", 0, 1)
        pdf.cell(0, 7, f"Premio Inicial: {format_currency(premio_anual)} (por {anos_pagamento} anos)", 0, 1)
        pdf.ln(5)
        
        # Tabela Recriada no PDF
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "Evolucao do Multiplicador Patrimonial", 0, 1)
        
        # Header Tabela
        headers = ["Ano", "Idade", "Capital", "Aporte", "Total Pago", "Mult (x)"]
        pdf.create_table_row(headers, header=True)
        
        # Dados Tabela (Recalculando para o PDF os primeiros 15 anos para caber na folha)
        cap_pdf = cobertura_sugerida
        prem_pdf = premio_anual
        acum_pdf = 0.0
        
        for i in range(1, 16):
            if i <= anos_pagamento:
                row_aporte = format_currency(prem_pdf)
                acum_pdf += prem_pdf
                row_acum = format_currency(acum_pdf)
                row_mult = f"{(cap_pdf/acum_pdf):.1f}x"
                prem_next = prem_pdf * (1 + (taxa_reajuste/100))
            else:
                row_aporte = "-"
                row_acum = "-"
                row_mult = "-"
                prem_next = 0
                
            row_data = [
                str(ano_atual + i),
                str(idade_cliente + i),
                f"R$ {cap_pdf:,.0f}", # Simplificado para caber
                f"R$ {prem_pdf:,.0f}" if i <= anos_pagamento else "-",
                f"R$ {acum_pdf:,.0f}" if i <= anos_pagamento else "-",
                row_mult
            ]
            pdf.create_table_row(row_data, header=False)
            cap_pdf = cap_pdf * (1 + (taxa_reajuste/100))
            prem_pdf = prem_next
            
        # Salva e Baixa
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf.output(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                pdf_data = f.read()
        
        st.download_button(
            label="⬇️ Download PDF Completo",
            data=pdf_data,
            file_name=f"Relatorio_{nome_cliente.split()[0]}.pdf",
            mime="application/pdf"
        )
            
    except Exception as e:
        st.error(f"Erro no PDF: {e}")
