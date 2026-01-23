import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import json
import tempfile 

# --- Configuração da Página ---
st.set_page_config(
    page_title="Planejamento Patrimonial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DEFINIÇÃO DE CORES (PALETA BLUE TECH) ---
COLOR_ACCENT = "#00D4FF"      
COLOR_HEADER_BG = "#003C50"   
COLOR_TEXT_STD = "#E0E0E0"    
COLOR_RED = "#FF4B4B"         

# --- CSS Personalizado ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; }}
    h1 {{ text-align: center; color: #FFFFFF !important; padding-bottom: 20px; }}
    h2, h3, h4 {{ color: #FFFFFF !important; }}
    .client-box {{
        background-color: #161B22; padding: 25px; border-radius: 10px;
        border-left: 5px solid {COLOR_ACCENT}; margin-top: 20px;
    }}
    .client-text {{ color: {COLOR_TEXT_STD}; font-size: 1.1rem; line-height: 1.6; }}
    .highlight {{ color: {COLOR_RED}; font-weight: bold; }}
    .highlight-blue {{ color: {COLOR_ACCENT}; font-weight: bold; }}
    
    /* Cabeçalho da Tabela Azul */
    [data-testid="stDataFrame"] thead th {{
        background-color: {COLOR_HEADER_BG} !important;
        color: white !important;
        border-bottom: 2px solid {COLOR_ACCENT} !important;
    }}
    
    input {{ text-align: right; }}
    .stButton button {{ width: 100%; border-radius: 5px; }}
    div[data-testid="stDataFrame"] {{ width: 100%; }}
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
    else: return '#00D4FF' 

# --- INICIALIZAÇÃO DE ESTADO ---
defaults = {
    "nome_cliente": "", "is_casado": False, "nome_conjuge": "",
    "ano_nasc_cliente": 1975, "ano_nasc_conjuge": 1978, "regime_casamento": "Separação Total de Bens",
    "v_imoveis": 0.0, "v_aplicacoes": 0.0, "v_veiculos": 0.0, "v_empresas": 0.0, "v_outros": 0.0,
    "v_prev": 0.0, "incluir_prev": False,
    "estado_selecionado": "São Paulo (SP)", "toggle_pl": False,
    "aliq_itcmd_input": 4.0, "aliq_hon": 6.0, "aliq_cart": 2.0,
    "cobertura_sugerida": 0.0, "anos_pagamento": 10, "premio_anual": 0.0, "taxa_reajuste": 5.0,
    "ultimo_estado_pl": False, "simulacao_anos": 16
}

for key, default_val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

keys_to_save = list(defaults.keys())

def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            for key, value in data.items():
                if key in st.session_state:
                    st.session_state[key] = value
            st.success("Dados carregados!")
            st.rerun()
        except Exception as e: st.error(f"Erro: {e}")

def limpar_dados():
    for key in keys_to_save:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

# --- Classe PDF Otimizada (Com Acentos) ---
class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(14, 17, 23) 
        self.rect(0, 0, 297, 420, 'F') 
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, self.safe_txt('Relatório de Planejamento Patrimonial'), 0, 1, 'C')
        self.ln(5)

    def safe_txt(self, text):
        try:
            return text.encode('latin-1', 'replace').decode('latin-1')
        except:
            return text

    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 212, 255) 
        self.cell(0, 10, self.safe_txt(title), 0, 1, 'L')
        self.set_draw_color(0, 212, 255)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def dark_metric_box(self, label, value, color_r=25, color_g=35, color_b=45, border=False):
        self.set_fill_color(color_r, color_g, color_b)
        if border:
            self.set_draw_color(255, 75, 75); self.set_line_width(0.5)
        else:
            self.set_draw_color(60, 60, 60)
        x = self.get_x(); y = self.get_y()
        self.rect(x, y, 90, 25, 'FD')
        self.set_xy(x+5, y+5)
        self.set_font('Arial', '', 10); self.set_text_color(200, 200, 200)
        self.cell(80, 5, self.safe_txt(label), 0, 2)
        self.set_font('Arial', 'B', 14); self.set_text_color(255, 255, 255)
        self.cell(80, 8, self.safe_txt(value), 0, 0)
        self.set_xy(x + 95, y) 

    def create_table_row(self, data, header=False, zebra=False):
        if header:
            self.set_fill_color(0, 60, 80); self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 9); self.set_draw_color(0, 212, 255)
        else:
            if zebra: self.set_fill_color(22, 27, 34) 
            else: self.set_fill_color(14, 17, 23)
            self.set_text_color(220, 220, 220); self.set_font('Arial', '', 9); self.set_draw_color(40, 40, 40)
        w = [20, 20, 40, 40, 40, 30] 
        for i, datum in enumerate(data):
            if not header and i == 5: self.set_text_color(0, 212, 255); self.set_font('Arial', 'B', 9)
            elif not header: self.set_text_color(220, 220, 220); self.set_font('Arial', '', 9)
            self.cell(w[i], 8, self.safe_txt(str(datum)), 1, 0, 'C', True)
        self.ln()
    
    def write_colored_conclusion(self, saudacao, custo, multiplicador_txt):
        self.set_font('Arial', '', 11)
        self.set_text_color(220, 220, 220)
        self.write(5, self.safe_txt(f"Prezado(a) {saudacao}, o custo sucessório estimado é "))
        
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 75, 75) 
        self.write(5, self.safe_txt(custo))
        
        self.set_font('Arial', '', 11)
        self.set_text_color(220, 220, 220)
        self.write(5, self.safe_txt(". A solução de liquidez permite quitar esse custo com um deságio financeiro significativo. Observe na tabela acima o "))
        
        self.set_font('Arial', 'B', 11)
        self.set_text_color(0, 212, 255)
        self.write(5, self.safe_txt("Multiplicador"))
        
        self.set_font('Arial', '', 11)
        self.set_text_color(220, 220, 220)
        self.write(5, self.safe_txt(", que indica quantas vezes o benefício supera o custo."))
        self.ln(10)

    def write_warning_box(self, text):
        self.ln(5)
        self.set_fill_color(60, 10, 10) # Fundo Vermelho Escuro
        self.set_draw_color(255, 75, 75) # Borda Vermelha Clara
        self.set_text_color(255, 200, 200) # Texto Claro
        self.set_font('Arial', 'B', 10)
        
        # Salva posição Y
        y_start = self.get_y()
        self.rect(10, y_start, 190, 10, 'FD')
        self.set_xy(12, y_start + 2)
        self.cell(0, 6, self.safe_txt(text), 0, 1, 'L')
        self.ln(2)

# --- BARRA LATERAL (AJUSTE 3: Expander) ---
with st.sidebar:
    st.header("📂 Menu")
    # Colocamos as opções de salvar/carregar dentro de um expander para esconder/abrir
    with st.expander("💾 Gerenciar Dados (Salvar/Abrir)", expanded=False):
        current_data = {key: st.session_state[key] for key in keys_to_save if key in st.session_state}
        json_str = json.dumps(current_data)
        st.download_button("⬇️ Baixar Preenchimento", json_str, "planejamento.json", "application/json")
        
        st.divider()
        uploaded_file = st.file_uploader("📂 Carregar Arquivo", type=["json"])
        if uploaded_file and st.button("Confirmar Carregamento"): carregar_dados(uploaded_file)
        
        st.divider()
        if st.button("🗑️ Limpar Tudo", type="primary"): limpar_dados()

# --- APP ---
st.title("Calculadora de Planejamento Patrimonial")

col_d1, col_d2, col_d3 = st.columns([1.5, 0.5, 1.5])
with col_d1: st.text_input("Nome do Cliente", placeholder="Ex: João", key="nome_cliente")
with col_d2: st.write(""); st.write(""); st.toggle("Casado(a)?", key="is_casado")
with col_d3:
    if st.session_state.is_casado: st.text_input("Nome do Cônjuge", placeholder="Ex: Maria", key="nome_conjuge")

col_n1, col_n2, col_n3 = st.columns([1.5, 0.5, 1.5])
ano_atual = datetime.now().year # 2026 conforme contexto
idade_cliente = 0; idade_conjuge = 0
regime_casamento = "Separação Total de Bens"; percentual_meacao = 0.0

with col_n1:
    ano_cli = st.number_input("Ano Nasc. (Cliente)", 1920, ano_atual, step=1, key="ano_nasc_cliente")
    idade_cliente = ano_atual - ano_cli
with col_n3:
    if st.session_state.is_casado:
        c1, c2 = st.columns(2)
        with c1:
            ano_conj = st.number_input("Ano Nasc. (Cônjuge)", 1920, ano_atual, step=1, key="ano_nasc_conjuge")
            idade_conjuge = ano_atual - ano_conj
        with c2:
            reg = st.selectbox("Regime", ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Separação Total de Bens", "Participação Final nos Aquestos"], key="regime_casamento")
            regime_casamento = reg
            if reg in ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Participação Final nos Aquestos"]: percentual_meacao = 0.50

st.markdown("---")
col_pat, col_cus = st.columns([1, 1.2], gap="large")

with col_pat:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores totais")
    val_imoveis = st.number_input("Imóveis", 0.0, step=100000.0, format="%.2f", key="v_imoveis")
    val_aplicacoes = st.number_input("Aplicações Financeiras", 0.0, step=100000.0, format="%.2f", key="v_aplicacoes")
    val_veiculos = st.number_input("Veículos", 0.0, step=100000.0, format="%.2f", key="v_veiculos")
    val_empresas = st.number_input("Part. Empresas", 0.0, step=100000.0, format="%.2f", key="v_empresas")
    val_outros = st.number_input("Outros Bens", 0.0, step=100000.0, format="%.2f", key="v_outros")
    c_prev, c_chk = st.columns([0.7, 0.3])
    with c_prev: val_prev = st.number_input("Previdência Privada", 0.0, step=100000.0, format="%.2f", key="v_prev")
    with c_chk: st.write(""); st.write(""); st.checkbox("Incluir?", key="incluir_prev")

    total_patrimonio_bruto = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if st.session_state.incluir_prev: total_patrimonio_bruto += val_prev
    valor_meacao = total_patrimonio_bruto * percentual_meacao
    base_calculo_imposto = total_patrimonio_bruto - valor_meacao

    st.divider()
    c_t1, c_t2 = st.columns(2)
    with c_t1: st.metric("Patrimônio Total", format_currency(total_patrimonio_bruto))
    with c_t2: st.metric("Base Tributável", format_currency(base_calculo_imposto), delta="- Meação" if percentual_meacao > 0 else None)

with col_cus:
    st.subheader("2. Custos de Sucessão")
    c_uf, c_pl = st.columns(2)
    with c_uf: estado_sel = st.selectbox("Estado", ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"], key="estado_selecionado")
    with c_pl: st.write(""); st.write(""); usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    # --- AJUSTE 1: Lógica do PL n.7 ---
    # Recalcula a alíquota sugerida com base nos valores ATUAIS
    val_sugerido = 4.0
    if usar_pl: 
        val_sugerido = obter_aliquota_pl_sp_fixa(base_calculo_imposto)
        # SE PL ESTIVER LIGADO, FORÇAMOS A ATUALIZAÇÃO DO INPUT PARA ACOMPANHAR O CÁLCULO
        # Isso garante que se o patrimônio mudar, a alíquota muda junto.
        st.session_state.aliq_itcmd_input = val_sugerido
    elif estado_sel == "Minas Gerais (MG)": 
        val_sugerido = 5.0
        # Se PL desligado, só atualiza se houve mudança de estado para não atrapalhar edição manual
        if st.session_state.ultimo_estado_pl != usar_pl:
             st.session_state.aliq_itcmd_input = val_sugerido

    st.session_state.ultimo_estado_pl = usar_pl

    st.markdown("#### Detalhamento")
    c1, c2, c3 = st.columns([3, 1.5, 2])
    with c1: st.write("ITCMD")
    with c2: aliq_itcmd = st.number_input("Aliq ITCMD", 0.0, 20.0, step=0.5, label_visibility="collapsed", key="aliq_itcmd_input")
    with c3: st.write(f"**{format_currency(base_calculo_imposto * (aliq_itcmd/100))}**")
    
    c1, c2, c3 = st.columns([3, 1.5, 2])
    with c1: st.write("Honorários")
    with c2: aliq_hon = st.number_input("Aliq Hon", 0.0, step=0.5, label_visibility="collapsed", key="aliq_hon")
    with c3: st.write(format_currency(base_calculo_imposto * (aliq_hon/100)))

    c1, c2, c3 = st.columns([3, 1.5, 2])
    with c1: st.write("Cartório")
    with c2: aliq_cart = st.number_input("Aliq Cart", 0.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
    with c3: st.write(format_currency(base_calculo_imposto * (aliq_cart/100)))

    st.divider()
    custo_total = (base_calculo_imposto * (aliq_itcmd/100)) + (base_calculo_imposto * (aliq_hon/100)) + (base_calculo_imposto * (aliq_cart/100))
    pct_total = (custo_total / base_calculo_imposto * 100) if base_calculo_imposto > 0 else 0

    st.markdown(f"""
        <div style="background-color: #4a1515; padding: 15px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center;">
            <p style="color: white; margin:0;">Custo Inventário</p>
            <h1 style="color: #ff4b4b; margin: 5px 0;">{format_currency(custo_total)}</h1>
            <p style="color: #ddd; margin:0;">Comprometimento: <b>{pct_total:.2f}%</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    aumento_imposto = 0
    # O aviso agora funcionará pois o aliq_itcmd está sendo atualizado corretamente acima
    if usar_pl and (base_calculo_imposto * (aliq_itcmd/100)) > (base_calculo_imposto * 0.04):
        aumento_imposto = (base_calculo_imposto * (aliq_itcmd/100)) - (base_calculo_imposto * 0.04)
        st.error(f"🚨 Aumento de Imposto pela Nova Lei: {format_currency(aumento_imposto)}")

st.write(""); st.subheader("3. Cenário Global")
data_globo = [{"pais": "Japão", "lat": 36.204, "lon": 138.252, "tax": 55}, {"pais": "Coreia do Sul", "lat": 35.907, "lon": 127.766, "tax": 50}, {"pais": "França", "lat": 46.227, "lon": 2.213, "tax": 45}, {"pais": "EUA", "lat": 37.090, "lon": -95.712, "tax": 40}, {"pais": "Reino Unido", "lat": 55.378, "lon": -3.436, "tax": 40}, {"pais": "Brasil (Você)", "lat": -14.235, "lon": -51.925, "tax": aliq_itcmd}, {"pais": "Chile", "lat": -35.675, "lon": -71.543, "tax": 25}, {"pais": "Argentina", "lat": -38.416, "lon": -63.616, "tax": 5}]
df_globo = pd.DataFrame(data_globo).sort_values('tax')
df_globo['color'] = df_globo['tax'].apply(get_color_by_tax)
df_globo['size'] = df_globo['pais'].apply(lambda x: 25 if "Você" in x else 12)

c_chart, c_globe = st.columns(2)
with c_chart:
    fig = px.bar(df_globo, x='tax', y='pais', orientation='h', text='tax', title="Ranking Alíquotas Máximas")
    fig.update_traces(marker_color=df_globo['color'], texttemplate='%{text:.1f}%')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350)
    st.plotly_chart(fig, use_container_width=True)
with c_globe:
    fig_globe = go.Figure(data=go.Scattergeo(
        lon = df_globo['lon'], lat = df_globo['lat'], text = df_globo['pais'] + ": " + df_globo['tax'].astype(str) + "%",
        mode = 'markers', marker = dict(size = df_globo['size'], color = df_globo['color'], line = dict(width=1, color='white'), opacity = 0.9)
    ))
    fig_globe.update_layout(geo = dict(projection_type = "orthographic", showland = True, landcolor = "#f3f4f6", showocean = True, oceancolor = "#a4d4f2", showcountries = True, countrycolor = "#888888", projection_rotation = dict(lon=-50, lat=-15, roll=0)),
        margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', height=350, font=dict(color="black"))
    st.plotly_chart(fig_globe, use_container_width=True)

st.markdown("---")
st.subheader("🛠️ Solução: Liquidez e Multiplicador")
c_s1, c_s2, c_s3 = st.columns(3)
with c_s1: cob_sugerida = st.number_input("Capital Segurado", 0.0, step=50000.0, format="%.2f", key="cobertura_sugerida")
with c_s2: anos_pag = st.slider("Anos Pagamento", 1, 30, key="anos_pagamento")
with c_s3: 
    premio = st.number_input("Prêmio Anual", 0.0, step=1000.0, format="%.2f", key="premio_anual")
    taxa = st.number_input("Reajuste (%)", 0.0, step=0.5, format="%.1f", key="taxa_reajuste")

if premio == 0.0 and cob_sugerida > 0: premio = cob_sugerida * 0.04

st.write("### 📈 Evolução")
data_sim = []
cap_curr = cob_sugerida; prem_curr = premio; acum = 0.0
anos_para_simular = st.session_state.simulacao_anos 

# --- AJUSTE 2: Loop começando em 0 para incluir o ano atual (2026) ---
for i in range(0, anos_para_simular):
    if i < anos_pag: # Menor que anos_pagamento (ex: 0 a 9 = 10 pagamentos)
        aporte_str = format_currency(prem_curr)
        acum += prem_curr
        acum_str = format_currency(acum)
        mult_val = (cap_curr/acum) if acum > 0 else 0
        mult = f"{mult_val:.1f}x"
        prem_next = prem_curr * (1 + (taxa/100))
    else:
        aporte_str = "-"; acum_str = "-"; mult = "-"; prem_next = 0

    data_sim.append({
        "Ano": ano_atual + i, "Idade": idade_cliente + i,
        "Capital Segurado": format_currency(cap_curr), 
        "Aporte": aporte_str, "Total Pago": acum_str, "Multiplicador": mult
    })
    cap_curr *= (1 + (taxa/100))
    prem_curr = prem_next

df_sim = pd.DataFrame(data_sim)

# Estilo Tabela
styler = df_sim.style.set_table_styles([
    {'selector': 'th', 'props': [('background-color', COLOR_HEADER_BG), ('color', 'white'), ('border-bottom', f'2px solid {COLOR_ACCENT}')]}
])
def style_dataframe_rows(row):
    if row.name % 2 == 0: bg_color = '#1E1E1E'
    else: bg_color = '#0E1117'
    row_style = [f'background-color: {bg_color}; color: white; border-bottom: 1px solid #333' for _ in row.index]
    if 'Multiplicador' in row.index:
        idx = row.index.get_loc('Multiplicador')
        row_style[idx] = f'background-color: {bg_color}; color: {COLOR_ACCENT}; font-weight: bold; border-left: 1px solid #333'
    return row_style
styler = styler.apply(style_dataframe_rows, axis=1)
st.dataframe(styler, use_container_width=True, hide_index=True, height=500)

if st.button("Carregar +10 Anos"): st.session_state.simulacao_anos += 10; st.rerun()

st.markdown("### 6. Conclusão")
saudacao = f"{st.session_state.nome_cliente} & {st.session_state.nome_conjuge}" if st.session_state.is_casado and st.session_state.nome_conjuge else st.session_state.nome_cliente

texto_final = f"""
<div class="client-box">
    <p class="client-text">
        Prezado(a) <b>{saudacao}</b>, o custo sucessório estimado é <span class="highlight">{format_currency(custo_total)}</span>.
        A solução de liquidez permite quitar esse custo com um deságio financeiro significativo.
        Observe na tabela acima o <span class="highlight-blue">Multiplicador</span>, que indica quantas vezes o benefício supera o custo.
    </p>
</div>
"""
st.markdown(texto_final, unsafe_allow_html=True)

if st.button("📄 Baixar PDF (Blue Mode)"):
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        pdf.section_title("1. Cliente e Patrimônio")
        pdf.set_font('Arial', '', 11); pdf.set_text_color(220, 220, 220)
        pdf.cell(0, 7, pdf.safe_txt(f"Cliente: {st.session_state.nome_cliente} ({ano_atual - st.session_state.ano_nasc_cliente} anos)"), 0, 1)
        if st.session_state.is_casado: pdf.cell(0, 7, pdf.safe_txt(f"Cônjuge: {st.session_state.nome_conjuge} ({ano_atual - st.session_state.ano_nasc_conjuge} anos)"), 0, 1)
        pdf.ln(5)
        pdf.dark_metric_box("Patrimônio Total", format_currency(total_patrimonio_bruto)); pdf.ln(30)
        
        pdf.section_title("2. Custos de Sucessão")
        pdf.cell(0, 7, pdf.safe_txt(f"Estado: {st.session_state.estado_selecionado}"), 0, 1)
        pdf.ln(5)
        pdf.dark_metric_box("Custo Inventário", format_currency(custo_total), 60, 20, 20, True)
        pdf.dark_metric_box("% Patrimônio", f"{pct_total:.2f}%"); pdf.ln(30)
        
        if aumento_imposto > 0:
            pdf.write_warning_box(f"ATENÇÃO: A PL n.7/2024 elevaria o imposto em + {format_currency(aumento_imposto)}")
        
        pdf.section_title("3. Solução (Liquidez)")
        pdf.cell(0, 7, pdf.safe_txt(f"Capital Segurado: {format_currency(cob_sugerida)}"), 0, 1)
        pdf.cell(0, 7, pdf.safe_txt(f"Prêmio: {format_currency(premio)} ({anos_pag} anos)"), 0, 1)
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 12); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, pdf.safe_txt("Evolução do Multiplicador"), 0, 1)
        
        headers = ["Ano", "Idade", "Capital Segurado", "Aporte", "Total Pago", "Mult (x)"]
        pdf.create_table_row(headers, header=True)
        
        c_p, p_p, a_p = cob_sugerida, premio, 0.0
        # Loop PDF também ajustado para range(0, ...)
        for i in range(0, anos_para_simular):
            if pdf.get_y() > 270: 
                pdf.add_page()
                pdf.create_table_row(headers, header=True)

            zebra = (i % 2 == 0)
            if i < anos_pag:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", f"R$ {p_p:,.0f}", f"R$ {a_p+p_p:,.0f}", f"{(c_p/(a_p+p_p)):.1f}x"]
                a_p += p_p
                p_p *= (1 + taxa/100)
            else:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", "-", "-", "-"]
                p_p = 0
            pdf.create_table_row(row, zebra=zebra)
            c_p *= (1 + taxa/100)
            
        pdf.ln(10)
        pdf.section_title("4. Conclusão")
        pdf.write_colored_conclusion(saudacao, format_currency(custo_total), "Multiplicador")
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("⬇️ Download PDF", f.read(), f"Relatorio_{st.session_state.nome_cliente.split()[0]}.pdf", "application/pdf")
                
    except Exception as e: st.error(f"Erro PDF: {e}")
