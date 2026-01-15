import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import json
import io
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
    [data-testid="stDataFrame"] thead th {{
        background-color: {COLOR_HEADER_BG} !important; color: white !important;
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

# --- CORREÇÃO DO ERRO: INICIALIZAÇÃO DE ESTADO ---
# Definimos os valores padrão AQUI, antes de criar os widgets.
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

# Lista de chaves para salvar no JSON
keys_to_save = list(defaults.keys())

# --- Gerenciamento de Arquivo ---
def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            for key, value in data.items():
                if key in st.session_state:
                    st.session_state[key] = value
            st.success("Dados carregados! O app será atualizado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")

def limpar_dados():
    for key in keys_to_save:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- Classe PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(14, 17, 23) 
        self.rect(0, 0, 297, 420, 'F') 
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'Relatório de Planejamento Patrimonial', 0, 1, 'C')
        self.ln(5)

    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 212, 255) 
        self.cell(0, 10, title, 0, 1, 'L')
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
        self.cell(80, 5, label, 0, 2)
        self.set_font('Arial', 'B', 14); self.set_text_color(255, 255, 255)
        self.cell(80, 8, value, 0, 0)
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
            self.cell(w[i], 8, str(datum), 1, 0, 'C', True)
        self.ln()
    
    def add_conclusion_text(self, text):
        self.set_font('Arial', '', 11); self.set_text_color(220, 220, 220)
        self.multi_cell(0, 7, text)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📂 Menu")
    # Pega valores atuais do session state para salvar
    current_data = {key: st.session_state[key] for key in keys_to_save if key in st.session_state}
    json_str = json.dumps(current_data)
    st.download_button("💾 Salvar Preenchimento", json_str, "planejamento.json", "application/json")
    
    uploaded_file = st.file_uploader("📂 Carregar", type=["json"])
    if uploaded_file and st.button("Confirmar Carregamento"):
        carregar_dados(uploaded_file)
            
    st.divider()
    if st.button("🗑️ Limpar Tudo", type="primary"):
        limpar_dados()

# --- APP PRINCIPAL ---
st.title("Calculadora de Planejamento Patrimonial")

# Nota: Removemos o argumento 'value=...' de todos os widgets abaixo
# pois o valor agora é controlado 100% pelo st.session_state inicializado acima.

col_d1, col_d2, col_d3 = st.columns([1.5, 0.5, 1.5])
with col_d1: st.text_input("Nome do Cliente", placeholder="Ex: João", key="nome_cliente")
with col_d2: st.write(""); st.write(""); st.toggle("Casado(a)?", key="is_casado")
with col_d3:
    if st.session_state.is_casado: st.text_input("Nome do Cônjuge", placeholder="Ex: Maria", key="nome_conjuge")

col_n1, col_n2, col_n3 = st.columns([1.5, 0.5, 1.5])
ano_atual = datetime.now().year
idade_cliente = 0; idade_conjuge = 0
regime_casamento = "Separação Total de Bens"; percentual_meacao = 0.0

with col_n1:
    # Widgets sem 'value', usando apenas 'key'
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
            else: percentual_meacao = 0.0

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
    with c_chk: st.write(""); st.write(""); st.checkbox("Incluir?", key="incluir_prev")

    total_patrimonio_bruto = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if st.session_state.incluir_prev: total_patrimonio_bruto += val_prev
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
    with c_uf: estado_sel = st.selectbox("Estado", ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"], key="estado_selecionado")
    with c_pl: st.write(""); st.write(""); usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    # Lógica de Atualização Automática
    val_sugerido = 4.0
    if usar_pl: val_sugerido = obter_aliquota_pl_sp_fixa(base_calculo_imposto)
    elif estado_sel == "Minas Gerais (MG)": val_sugerido = 5.0
    
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
    if usar_pl and (base_calculo_imposto * (aliq_itcmd/100)) > (base_calculo_imposto * 0.04):
        st.error(f"🚨 Aumento de Imposto pela Nova Lei: {format_currency((base_calculo_imposto * (aliq_itcmd/100)) - (base_calculo_imposto * 0.04))}")

# SEÇÃO 3: CENÁRIO GLOBAL
st.write(""); st.subheader("3. Cenário Global")
data_globo = [{"pais": "Japão", "tax": 55}, {"pais": "Coreia do Sul", "tax": 50}, {"pais": "França", "tax": 45}, {"pais": "EUA", "tax": 40}, {"pais": "Reino Unido", "tax": 40}, {"pais": "Brasil (Você)", "tax": aliq_itcmd}, {"pais": "Chile", "tax": 25}, {"pais": "Argentina", "tax": 5}]
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
# Atenção: Se custo_total mudou, precisamos atualizar cobertura_sugerida se o usuário não tiver editado
# Mas para não complicar a lógica, deixamos o usuário ajustar ou resetar.
with c_s1: cob_sugerida = st.number_input("Capital Segurado", 0.0, step=50000.0, format="%.2f", key="cobertura_sugerida")
with c_s2: anos_pag = st.slider("Anos Pagamento", 1, 30, key="anos_pagamento")
with c_s3: 
    premio = st.number_input("Prêmio Anual", 0.0, step=1000.0, format="%.2f", key="premio_anual")
    taxa = st.number_input("Reajuste (%)", 0.0, step=0.5, format="%.1f", key="taxa_reajuste")

# Se premio vier zerado do default, sugerimos valor
if premio == 0.0 and cob_sugerida > 0:
    premio = cob_sugerida * 0.04
    # Não podemos atualizar widget renderizado sem rerun, mas o calculo abaixo usa a variavel premio

st.write("### 📈 Evolução")
data_sim = []
cap_curr = cob_sugerida; prem_curr = premio; acum = 0.0
for i in range(1, st.session_state.simulacao_anos + 1):
    if i <= anos_pag:
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

def style_dataframe_rows(row):
    if row.name % 2 == 0: bg_color = '#1E1E1E'
    else: bg_color = '#0E1117'
    row_style = [f'background-color: {bg_color}; color: white; border-bottom: 1px solid #333' for _ in row.index]
    if 'Multiplicador' in row.index:
        idx = row.index.get_loc('Multiplicador')
        row_style[idx] = f'background-color: {bg_color}; color: {COLOR_ACCENT}; font-weight: bold; border-left: 1px solid #333'
    return row_style

st.dataframe(df_sim.style.apply(style_dataframe_rows, axis=1), use_container_width=True, hide_index=True, height=500)
if st.button("Carregar +10 Anos"): st.session_state.simulacao_anos += 10; st.rerun()

# DIAGNÓSTICO
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
        
        pdf.section_title("1. Cliente e Patrimonio")
        pdf.set_font('Arial', '', 11); pdf.set_text_color(220, 220, 220)
        pdf.cell(0, 7, f"Cliente: {st.session_state.nome_cliente} ({ano_atual - st.session_state.ano_nasc_cliente} anos)", 0, 1)
        if st.session_state.is_casado: pdf.cell(0, 7, f"Conjuge: {st.session_state.nome_conjuge} ({ano_atual - st.session_state.ano_nasc_conjuge} anos)", 0, 1)
        pdf.ln(5)
        pdf.dark_metric_box("Patrimonio Total", format_currency(total_patrimonio_bruto)); pdf.ln(30)
        
        pdf.section_title("2. Custos Sucessao")
        pdf.cell(0, 7, f"Estado: {st.session_state.estado_selecionado}", 0, 1)
        pdf.ln(5)
        pdf.dark_metric_box("Custo Inventario", format_currency(custo_total), 60, 20, 20, True)
        pdf.dark_metric_box("% Patrimonio", f"{pct_total:.2f}%"); pdf.ln(30)
        
        pdf.section_title("3. Solucao (Liquidez)")
        pdf.cell(0, 7, f"Capital Segurado: {format_currency(cob_sugerida)}", 0, 1)
        pdf.cell(0, 7, f"Premio: {format_currency(premio)} ({anos_pag} anos)", 0, 1)
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 12); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "Evolucao do Multiplicador", 0, 1)
        
        headers = ["Ano", "Idade", "Capital Segurado", "Aporte", "Total Pago", "Mult (x)"]
        pdf.create_table_row(headers, header=True)
        
        c_p, p_p, a_p = cob_sugerida, premio, 0.0
        for i in range(1, 16):
            zebra = (i % 2 == 0)
            if i <= anos_pag:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", f"R$ {p_p:,.0f}", f"R$ {a_p+p_p:,.0f}", f"{(c_p/(a_p+p_p)):.1f}x"]
                a_p += p_p
                p_p *= (1 + taxa/100)
            else:
                row = [ano_atual+i, idade_cliente+i, f"R$ {c_p:,.0f}", "-", "-", "-"]
                p_p = 0
            pdf.create_table_row(row, zebra=zebra)
            c_p *= (1 + taxa/100)
            
        pdf.ln(10)
        pdf.section_title("4. Conclusao")
        texto_limpo = f"Prezado(a) {saudacao}, o custo sucessorio estimado e {format_currency(custo_total)}. A solucao de liquidez permite quitar esse custo com um desagio financeiro significativo. Observe na tabela acima o Multiplicador, que indica quantas vezes o beneficio supera o custo."
        pdf.add_conclusion_text(texto_limpo)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("⬇️ Download PDF", f.read(), f"Relatorio_{st.session_state.nome_cliente.split()[0]}.pdf", "application/pdf")
                
    except Exception as e: st.error(f"Erro PDF: {e}")
