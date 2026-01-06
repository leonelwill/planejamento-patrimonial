import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(
    page_title="Planejamento Patrimonial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Personalizado ---
st.markdown("""
    <style>
    /* Títulos Brancos e Centralizados */
    h1 { text-align: center; color: #FFFFFF !important; padding-bottom: 20px; }
    h2, h3, h4 { color: #FFFFFF !important; }
    
    /* Métricas */
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF7F; }
    
    /* Box do Cliente */
    .client-box {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #FFD700;
        margin-top: 20px;
    }
    .solution-box {
        background-color: #0e2a18; /* Verde escuro */
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00FF7F;
        margin-top: 10px;
    }
    .client-text { color: #E0E0E0; font-size: 1.1rem; line-height: 1.6; }
    .highlight { color: #FF4B4B; font-weight: bold; }
    .highlight-green { color: #00FF7F; font-weight: bold; }
    
    /* REMOVIDO O ALINHAMENTO À DIREITA QUE CAUSOU ESTRANHEZA */
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

# --- Título e Nome ---
st.title("Calculadora de Planejamento Patrimonial")
col_nome, col_vazia = st.columns([1, 1])
with col_nome:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva")

st.markdown("---")

# --- Colunas Principais ---
col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# ==========================================================
# SEÇÃO 1: PATRIMÔNIO
# ==========================================================
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores (Use Enter para formatar)")
    
    # Steps ajustados para 100.000 conforme pedido
    val_imoveis = st.number_input("Imóveis", min_value=0.0, step=100000.0, format="%.2f", key="v_imoveis")
    val_aplicacoes = st.number_input("Aplicações Financeiras", min_value=0.0, step=100000.0, format="%.2f", key="v_aplicacoes")
    val_veiculos = st.number_input("Veículos", min_value=0.0, step=100000.0, format="%.2f", key="v_veiculos")
    val_empresas = st.number_input("Participação em Empresas", min_value=0.0, step=100000.0, format="%.2f", key="v_empresas")
    val_outros = st.number_input("Outros Bens", min_value=0.0, step=100000.0, format="%.2f", key="v_outros")
    
    st.markdown("### Previdência Privada *")
    col_prev_input, col_prev_check = st.columns([0.7, 0.3])
    with col_prev_input:
        val_previdencia = st.number_input("Saldo em Previdência", min_value=0.0, step=100000.0, format="%.2f", key="v_prev")
    with col_prev_check:
        st.write("") 
        st.write("")
        incluir_prev = st.checkbox("Incluir?", value=False)
    
    st.info("* Obs: Como padrão, a previdência privada não entra no cálculo de inventário, porém depende de cada estado.")

    total_patrimonio = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if incluir_prev:
        total_patrimonio += val_previdencia
        
    st.divider()
    st.metric(label="Total Inventariável", value=format_currency(total_patrimonio))

# ==========================================================
# SEÇÃO 2: CUSTOS DE INVENTÁRIO
# ==========================================================
with col_custos:
    st.subheader("2. Custos de Sucessão")
    
    col_uf, col_pl = st.columns([1, 1])
    with col_uf:
        estados = ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"]
        estado_selecionado = st.selectbox("Estado Base:", estados)
    
    with col_pl:
        st.write("") 
        st.write("") 
        usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    # Lógica de Alíquota
    if 'ultimo_estado_pl' not in st.session_state:
        st.session_state.ultimo_estado_pl = usar_pl
    if 'aliq_itcmd_input' not in st.session_state:
        st.session_state.aliq_itcmd_input = 4.0

    val_sugerido = 4.0
    if usar_pl:
        val_sugerido = obter_aliquota_pl_sp_fixa(total_patrimonio)
    elif estado_selecionado == "Minas Gerais (MG)":
        val_sugerido = 5.0
    
    # Atualiza se mudou o toggle
    if st.session_state.ultimo_estado_pl != usar_pl:
        st.session_state.aliq_itcmd_input = val_sugerido
        st.session_state.ultimo_estado_pl = usar_pl

    # Tabela
    st.markdown("#### Detalhamento de Custos")
    c_head1, c_head2, c_head3 = st.columns([3, 1.5, 2])
    c_head1.markdown("**Item**")
    c_head2.markdown("**Alíquota (%)**")
    c_head3.markdown("**Valor (R$)**")

    # ITCMD
    c_itcmd1, c_itcmd2, c_itcmd3 = st.columns([3, 1.5, 2])
    with c_itcmd1: st.write("ITCMD (Imposto Estadual)")
    with c_itcmd2:
        aliquota_itcmd = st.number_input("Aliq ITCMD", min_value=0.0, max_value=20.0, step=0.5, label_visibility="collapsed", key="aliq_itcmd_input")
    with c_itcmd3:
        val_itcmd = total_patrimonio * (aliquota_itcmd / 100)
        st.write(f"**{format_currency(val_itcmd)}**")

    # Honorários
    c_hon1, c_hon2, c_hon3 = st.columns([3, 1.5, 2])
    with c_hon1: st.write("Honorários Advocatícios")
    with c_hon2: aliquota_hon = st.number_input("Aliq Hon", value=6.0, step=0.5, label_visibility="collapsed", key="aliq_hon")
    with c_hon3:
        val_hon = total_patrimonio * (aliquota_hon / 100)
        st.write(f"{format_currency(val_hon)}")

    # Cartório
    c_cart1, c_cart2, c_cart3 = st.columns([3, 1.5, 2])
    with c_cart1: st.write("Custos Cartório/Outros")
    with c_cart2: aliquota_cart = st.number_input("Aliq Cart", value=2.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
    with c_cart3:
        val_cart = total_patrimonio * (aliquota_cart / 100)
        st.write(f"{format_currency(val_cart)}")

    st.divider()

    custo_total = val_itcmd + val_hon + val_cart
    percentual_total = (custo_total / total_patrimonio * 100) if total_patrimonio > 0 else 0

    st.markdown(
        f"""
        <div style="background-color: #4a1515; padding: 15px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center;">
            <p style="color: white; margin:0; font-size: 1.2rem;">Custo Total Estimado</p>
            <h1 style="color: #ff4b4b; margin: 5px 0; font-size: 2.8rem;">{format_currency(custo_total)}</h1>
            <p style="color: #ddd; margin:0;">Comprometimento Patrimonial: <b>{percentual_total:.2f}%</b></p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    if usar_pl:
        custo_base_itcmd = total_patrimonio * 0.04
        delta = val_itcmd - custo_base_itcmd
        if delta > 0:
            st.error(f"🚨 IMPACTO DA NOVA LEI: + {format_currency(delta)} de Imposto.")

# ==========================================================
# SEÇÃO 3: GRÁFICO GLOBAL
# ==========================================================
st.write("")
st.subheader("3. Onde você está no mundo?")
aliquota_efetiva_imposto = aliquota_itcmd
data_paises = {
    'País': ['Japão', 'Coreia do Sul', 'França', 'EUA', 'Reino Unido', 'Brasil (Sua Simulação)'],
    'Taxa Máxima': [55, 50, 45, 40, 40, aliquota_efetiva_imposto],
    'Tipo': ['Mundo', 'Mundo', 'Mundo', 'Mundo', 'Mundo', 'Voce']
}
df_paises = pd.DataFrame(data_paises).sort_values(by='Taxa Máxima', ascending=False)
fig = px.bar(df_paises, x='País', y='Taxa Máxima', color='Tipo', text_auto='.1f', color_discrete_map={'Mundo': 'gray', 'Voce': '#FF4B4B'}, title=None)
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False, height=300, yaxis=dict(showgrid=False, title=None), xaxis=dict(title=None))
st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# SEÇÃO 5: SOLUÇÃO (NOVA)
# ==========================================================
st.markdown("---")
st.subheader("🛠️ Ferramenta de Solução: Liquidez Fiscal (Seguro)")

col_solucao_inputs, col_solucao_grafico = st.columns([1, 1.5], gap="large")

with col_solucao_inputs:
    st.write("Simule uma apólice (Ex: Whole Life 10 anos) para cobrir o inventário.")
    
    # Inputs do Seguro
    cobertura_sugerida = st.number_input("Capital Segurado (Necessidade)", value=custo_total, step=100000.0, format="%.2f")
    anos_pagamento = st.slider("Tempo de Pagamento (Anos)", min_value=1, max_value=30, value=10)
    premio_anual = st.number_input("Prêmio Anual Estimado (Investimento)", value=(cobertura_sugerida * 0.04), step=1000.0, format="%.2f", help="Quanto o cliente paga por ano pelo seguro.")
    
    custo_total_seguro = premio_anual * anos_pagamento
    
    # Cálculo da Alavancagem
    alavancagem = cobertura_sugerida / custo_total_seguro if custo_total_seguro > 0 else 0
    economia = cobertura_sugerida - custo_total_seguro
    pct_economia = (economia / cobertura_sugerida * 100) if cobertura_sugerida > 0 else 0

    st.markdown(f"""
    <div class="solution-box">
        <h3 style="color:#00FF7F; text-align:center;">Alavancagem Patrimonial</h3>
        <p>Você paga: <b>{format_currency(custo_total_seguro)}</b></p>
        <p>Sua família recebe: <b>{format_currency(cobertura_sugerida)}</b></p>
        <hr style="border-color:#00FF7F;">
        <h2 style="color:white; text-align:center;">{alavancagem:.1f}x</h2>
        <p style="text-align:center; font-size:0.9rem;">Para cada R$ 1 investido, R$ {alavancagem:.1f} retornam para liquidez.</p>
    </div>
    """, unsafe_allow_html=True)

with col_solucao_grafico:
    st.write("### 📉 Comparativo: Custo da Sucessão")
    st.write("Quem paga a conta do inventário? Seu patrimônio ou a Seguradora?")
    
    # Gráfico Waterfall ou Barras Comparativas
    # Vamos fazer duas barras: Custo SEM Seguro (Perda Total) vs Custo COM Seguro (Prêmios Pagos)
    
    fig_comp = go.Figure()
    
    # Barra 1: Sem Planejamento
    fig_comp.add_trace(go.Bar(
        x=['Sem Planejamento'],
        y=[custo_total],
        text=[format_currency(custo_total)],
        textposition='auto',
        marker_color='#FF4B4B',
        name='Custo Inventário'
    ))
    
    # Barra 2: Com Seguro
    fig_comp.add_trace(go.Bar(
        x=['Com Seguro (Whole Life)'],
        y=[custo_total_seguro],
        text=[format_currency(custo_total_seguro)],
        textposition='auto',
        marker_color='#00FF7F',
        name='Custo Apólice'
    ))
    
    fig_comp.update_layout(
        title="Desembolso Efetivo da Família",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        yaxis=dict(showgrid=False, title="Valor a Desembolsar"),
        height=350
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)
    
    st.success(f"💡 **BENEFÍCIO FISCAL:** Ao utilizar o seguro para pagar o inventário, você está essencialmente quitando o imposto com **{pct_economia:.1f}% de desconto**.")


# ==========================================================
# SEÇÃO 4: DIAGNÓSTICO E FECHAMENTO
# ==========================================================
st.markdown("### 6. Diagnóstico Final")

saudacao = f"Prezado(a) <b>{nome_cliente}</b>" if nome_cliente else "Prezado(a)"

texto_diagnostico = f"""
<div class="client-box">
    <p class="client-text">
        {saudacao}, identificamos um risco de liquidez de <span class="highlight">{format_currency(custo_total)}</span> na sua sucessão.
    </p>
    <p class="client-text">
        Sem planejamento, esse valor sairá da venda depreciada de imóveis ou de aplicações financeiras tributadas.
    </p>
    <p class="client-text">
        A solução apresentada via <b>Seguro de Vida (Resgatável/Whole Life)</b> funciona como um instrumento financeiro de alavancagem. 
        Em vez de sua família pagar 100% do imposto no futuro, você parcela esse custo em vida por uma fração do valor (<span class="highlight-green">{format_currency(custo_total_seguro)}</span>).
        Isso garante que seu patrimônio de {format_currency(total_patrimonio)} seja transmitido integralmente.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)
