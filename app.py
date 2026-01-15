import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import json
import io
import tempfile # ADICIONADO PARA CORRIGIR O ERRO

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
    
    /* Botões */
    .stButton button { width: 100%; }
    
    /* Tabelas e Inputs */
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

# --- Classe PDF Avançada (Estilo Dark + Tabela Colorida) ---
class PDFReport(FPDF):
    def header(self):
        # Fundo Preto da Página
        self.set_fill_color(14, 17, 23) 
        self.rect(0, 0, 297, 420, 'F') 
        
        # Título Principal
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
            self.set_draw_color(255, 75, 75)
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
        self.set_xy(x + 95, y) 

    def create_table_row(self, data, header=False, zebra=False):
        # Configuração de Cores da Tabela
        if header:
            self.set_fill_color(0, 100, 50) # Verde Escuro para o Cabeçalho
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 9)
            self.set_draw_color(0, 255, 127) # Linha verde neon
        else:
            # Efeito Zebra (Alternar cinza escuro e cinza médio)
            if zebra:
                self.set_fill_color(40, 44, 52) 
            else:
                self.set_fill_color(30, 33, 39)
            
            self.set_text_color(220, 220, 220) # Texto padrão cinza claro
            self.set_font('Arial', '', 9)
            self.set_draw_color(60, 60, 60) # Bordas sutis

        # Larguras das colunas
        w = [20, 20, 40, 40, 40, 30] 
        
        # Desenhar Células
        for i, datum in enumerate(data):
            # Lógica Especial para a coluna "Multiplicador" (Índice 5)
            if not header and i == 5:
                self.set_text_color(0, 255, 127) # Verde Neon
                self.set_font('Arial', 'B', 9)   # Negrito
            elif not header:
                self.set_text_color(220, 220, 220) # Reset cor normal
                self.set_font('Arial', '', 9)      # Reset fonte normal
            
            self.cell(w[i], 8, str(datum), 1, 0, 'C', True)
        self.ln()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📂 Menu")
    current_data = {key: st.session_state.get(key) for key in keys_to_save}
    json_str = json.dumps(current_data)
    st.download_button("💾 Salvar Preenchimento", json_str, "planejamento.json", "application/json")
    
    uploaded_file = st.file_uploader("📂 Carregar", type=["json"])
    if uploaded_file and st.button("Confirmar Carregamento"):
        carregar_dados(uploaded_file)
            
    st.divider()
    if st.button("🗑️ Limpar Tudo", type="primary"):
        limpar_dados()

# --- INPUTS PRINCIPAIS ---
st.title("Calculadora de Planejamento Patrimonial")

col_d1, col_d2, col_d3 = st.columns([1.5, 0.5, 1.5])
with col_d1: nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João", key="nome_cliente")
with col_d2: 
    st.write("")
    st.write("")
    is_casado = st.toggle("Casado(a)?", key="is_casado")
with col_d3:
    if is_casado: nome_conjuge = st.text_input("Nome do Cônjuge", placeholder="Ex: Maria", key="nome_conjuge")

col_n1, col_n2, col_n3 = st.columns([1.5, 0.5, 1.5])
ano_atual = datetime.now().year
idade_cliente = 0
idade_conjuge = 0
regime_casamento = "Separação Total de Bens"
percentual_meacao = 0.0

with col_n1:
    ano_nasc_cliente = st.number_input("Ano Nasc. (Cliente)", 1920, ano_atual, 1975, key="ano_nasc_cliente")
    idade_cliente = ano_atual - ano_nasc_cliente

with col_n3:
    if is_casado:
        c1, c2 = st.columns(2)
        with c1:
            ano_nasc_conjuge = st.number_input("Ano Nasc. (Cônjuge)", 1920, ano_atual, 1978, key="ano_nasc_conjuge")
            idade_conjuge = ano_atual - ano_nasc_conjuge
        with c2:
            regime_casamento = st.selectbox("Regime", ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Separação Total de Bens", "Participação Final nos Aquestos"], key="regime_casamento")
            if regime_casamento in ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Participação Final nos Aquestos"]:
                percentual_meacao = 0.50
            else:
                percentual_meacao = 0.0

st.markdown("---")

col_pat, col_cus = st.columns([1, 1.2], gap="large")

# SEÇÃO 1: PATRIMÔNIO
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
    with c_chk: 
        st.write(""); st.write("")
        incluir_prev = st.checkbox("Incluir?", False, key="incluir_prev")

    total_patrimonio_bruto = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if incluir_prev: total_patrimonio_bruto += val_prev

    valor_meacao = total_patrimonio_bruto * percentual_meacao
    base_calculo_imposto = total_patrimonio_bruto - valor_meacao

    st.divider()
    c_t1, c_t2 = st.columns(2)
    with c_t1: st.metric("Patrimônio Total", format_currency(total_patrimonio_bruto))
    with c_t2: st.metric("Base Tributável", format_currency(base_calculo_imposto), delta="- Meação" if percentual_meacao > 0 else None)

# SEÇÃO 2: CUSTOS
with col_cus:
    st.subheader("2. Custos de Sucessão")
    c_uf, c_pl = st.columns(2)
    with c_uf: estado_selecionado = st.selectbox("Estado", ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"], key="estado_selecionado")
    with c_pl: 
        st.write(""); st.write("")
        usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    if 'ultimo_estado_pl' not in st.session_state: st.session_state.ultimo_estado_pl = usar_pl
    if 'aliq_itcmd_input' not in st.session_state: st.session_state.aliq_itcmd_input = 4.0

    val_sugerido = 4.0
    if usar_pl: val_sugerido = obter_aliquota_pl_sp_fixa(base_calculo_imposto)
    elif estado_selecionado == "Minas Gerais (MG)": val_sugerido = 5.0
    
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
    with c2: aliq_hon = st.number_input("Aliq Hon", value=6.0, step=0.5, label_visibility="collapsed", key="aliq_hon")
    with c3: st.write(format_currency(base_calculo_imposto * (aliq_hon/100)))

    c1, c2, c3 = st.columns([3, 1.5, 2])
    with c1: st.write("Cartório")
    with c2: aliq_cart = st.number_input("Aliq Cart", value=2.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
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
    
    if usar_pl and (base_calculo_imposto * (aliq_itcmd/100)) > (base_calculo_imposto * 0.04):
        st.error(f"🚨 Aumento de Imposto pela Nova Lei: {format_currency((base_calculo_imposto * (aliq_itcmd/100)) - (base_calculo_imposto * 0.04))}")

# SEÇÃO 3: CENÁRIO GLOBAL
st.write(""); st.subheader("3. Cenário Global")
data_globo = [
    {"pais": "Japão", "tax": 55}, {"pais": "Coreia do Sul", "tax": 50}, {"pais": "França", "tax": 45},
    {"pais": "EUA", "tax": 40}, {"pais": "Reino Unido", "tax": 40}, {"pais": "Brasil (Você)", "tax": aliq_itcmd},
    {"pais": "Chile", "tax": 25}, {"pais": "Argentina", "tax": 5}
]
df_globo = pd.DataFrame(data_globo).sort_values('tax')
df_globo['color'] = df_globo['tax'].apply(get_color_by_tax)
fig = px.bar(df_globo, x='tax', y='pais', orientation='h', text='tax', title="Ranking Alíquotas Máximas")
fig.update_traces(marker_color=df_globo['color'], texttemplate='%{text:.1f}%')
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350)
st.plotly_chart(fig, use_container_width=True)

# SEÇÃO 5: SOLUÇÃO
st.markdown("---")
st.subheader("🛠️ Solução: Liquidez e Multiplicador")

c_s1, c_s2, c_s3 = st.columns(3)
with c_s1: cob_sugerida = st.number_input("Capital Segurado", value=custo_total, step=50000.0, format="%.2f", key="cobertura_sugerida")
with c_s2: anos_pag = st.slider("Anos Pagamento", 1, 30, 10, key="anos_pagamento")
with c_s3: 
    premio = st.number_input("Prêmio Anual", value=(cob_sugerida * 0.04), step=1000.0, format="%.2f", key="premio_anual")
    taxa = st.number_input("Reajuste (%)", 5.0, step=0.5, format="%.1f", key="taxa_reajuste")

st.write("### 📈 Evolução")
if 'simulacao_anos' not in st.session_state: st.session_state.simulacao_anos = 16

data_sim = []
cap_curr = cob_sugerida
prem_curr = premio
acum = 0.0
for i in range(1, st.session_state.simulacao_anos + 1):
    if i <= anos_pag:
        aporte_str = format_currency(prem_curr)
        acum += prem_curr
        acum_str = format_currency(acum)
        mult = f"{(cap_curr/acum):.1f}x" if acum > 0 else "0x"
        prem_next = prem_curr * (1 + (taxa/100))
    else:
        aporte_str = "-"; acum_str = "-"; mult = "-"; prem_next = 0

    data_sim.append({
        "Ano": ano_atual + i, "Idade": idade_cliente + i,
        "Capital": format_currency(cap_curr), "Aporte": aporte_str,
        "Total Pago": acum_str, "Multiplicador": mult
    })
    cap_curr *= (1 + (taxa/100))
    prem_curr = prem_next

df_sim = pd.DataFrame(data_sim)
def style_fn(s): return ['color: #00FF7F; font-weight: bold' if col == 'Multiplicador' else '' for col in s.index]
st.dataframe(df_sim.style.apply(style_fn, axis=1).set_properties(**{'background-color': '#262730', 'color': 'white'}), use_container_width=True, hide_index=True)

if st.button("Carregar +10 Anos"): 
    st.session_state.simulacao_anos += 10
    st.rerun()

# DIAGNÓSTICO E PDF
st.markdown("### 6. Relatório")
saudacao = f"{nome_cliente} & {nome_conjuge}" if is_casado and nome_conjuge else nome_cliente
st.markdown(f"""<div class="client-box"><p class="client-text">Prezado(a) <b>{saudacao}</b>, o custo sucessório estimado é <span class="highlight">{format_currency(custo_total)}</span>. A solução de seguro quita este custo com alto deságio.</p></div>""", unsafe_allow_html=True)

if st.button("📄 Baixar PDF (Dark Mode)"):
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        pdf.section_title("1. Cliente e Patrimonio")
        pdf.set_font('Arial', '', 11); pdf.set_text_color(220, 220, 220)
        pdf.cell(0, 7, f"Cliente: {nome_cliente} ({ano_atual - ano_nasc_cliente} anos)", 0, 1)
        if is_casado: pdf.cell(0, 7, f"Conjuge: {nome_conjuge} ({ano_atual - ano_nasc_conjuge} anos)", 0, 1)
        pdf.ln(5)
        
        pdf.dark_metric_box("Patrimonio Total", format_currency(total_patrimonio_bruto)); pdf.ln(30)
        
        pdf.section_title("2. Custos Sucessao")
        pdf.cell(0, 7, f"Estado: {estado_selecionado}", 0, 1)
        pdf.ln(5)
        pdf.dark_metric_box("Custo Inventario", format_currency(custo_total), 60, 20, 20, True)
        pdf.dark_metric_box("% Patrimonio", f"{pct_total:.2f}%"); pdf.ln(30)
        
        pdf.section_title("3. Solucao (Liquidez)")
        pdf.cell(0, 7, f"Capital: {format_currency(cob_sugerida)}", 0, 1)
        pdf.cell(0, 7, f"Premio: {format_currency(premio)} ({anos_pag} anos)", 0, 1)
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 12); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "Evolucao do Multiplicador", 0, 1)
        
        headers = ["Ano", "Idade", "Capital", "Aporte", "Total Pago", "Mult (x)"]
        pdf.create_table_row(headers, header=True)
        
        # Recalcula para PDF (15 linhas)
        c_p, p_p, a_p = cob_sugerida, premio, 0.0
        for i in range(1, 16):
            zebra = (i % 2 == 0) # Zebra striping
            if i <= anos_pag:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", f"R$ {p_p:,.0f}", f"R$ {a_p+p_p:,.0f}", f"{(c_p/(a_p+p_p)):.1f}x"]
                a_p += p_p
                p_p *= (1 + taxa/100)
            else:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", "-", "-", "-"]
                p_p = 0
            pdf.create_table_row(row, zebra=zebra)
            c_p *= (1 + taxa/100)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("⬇️ Download PDF", f.read(), f"Relatorio_{nome_cliente.split()[0]}.pdf", "application/pdf")
                
    except Exception as e: st.error(f"Erro PDF: {e}")
