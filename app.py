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
    /* Títulos e Textos */
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
    
    /* Inputs numéricos alinhados */
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

# Função para definir cor baseada na taxa (Semáforo)
def get_color_by_tax(tax):
    if tax > 30:
        return '#FF4B4B' # Vermelho (Perigo)
    elif tax > 10:
        return '#FFD700' # Amarelo (Atenção)
    else:
        return '#00FF7F' # Verde (Seguro)

# --- Título e Dados do Cliente ---
st.title("Calculadora de Planejamento Patrimonial")

col_dados1, col_dados2, col_dados3 = st.columns([1.5, 0.5, 1.5])
with col_dados1:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva")

with col_dados2:
    st.write("") 
    st.write("") 
    is_casado = st.toggle("Casado(a)?")

nome_conjuge = ""
regime_casamento = "Separação Total de Bens"
percentual_meacao = 0.0

with col_dados3:
    if is_casado:
        nome_conjuge = st.text_input("Nome do Cônjuge", placeholder="Ex: Maria da Silva")
        regime_casamento = st.selectbox("Regime de Bens", 
            ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Separação Total de Bens", "Participação Final nos Aquestos"])
        
        if regime_casamento in ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Participação Final nos Aquestos"]:
            percentual_meacao = 0.50
        else:
            percentual_meacao = 0.0

st.markdown("---")

# --- Colunas Principais ---
col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# ==========================================================
# SEÇÃO 1: PATRIMÔNIO
# ==========================================================
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores totais do casal/indivíduo")
    
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
        incluir_prev = st.checkbox("Incluir?", value=False)
    
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

    # Tabela de Custos
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

# ==========================================================
# SEÇÃO 3: CENÁRIO GLOBAL (ATUALIZADA)
# ==========================================================
st.write("")
st.subheader("3. Cenário Global de Sucessão")
st.caption("Verde: ≤10% | Amarelo: 11-30% | Vermelho: >30%")

# Dados Ampliados (Mundo + América do Sul)
# Importante: O Brasil do Cliente é adicionado dinamicamente
aliquota_efetiva = aliquota_itcmd
data_globo = [
    # Grandes Economias (High Tax)
    {"pais": "Japão", "lat": 36.204, "lon": 138.252, "tax": 55},
    {"pais": "Coreia do Sul", "lat": 35.907, "lon": 127.766, "tax": 50},
    {"pais": "França", "lat": 46.227, "lon": 2.213, "tax": 45},
    {"pais": "EUA", "lat": 37.090, "lon": -95.712, "tax": 40},
    {"pais": "Reino Unido", "lat": 55.378, "lon": -3.436, "tax": 40},
    {"pais": "Alemanha", "lat": 51.165, "lon": 10.451, "tax": 30},
    
    # América do Sul
    {"pais": "Brasil (Você)", "lat": -14.235, "lon": -51.925, "tax": aliquota_efetiva},
    {"pais": "Chile", "lat": -35.675, "lon": -71.543, "tax": 25},
    {"pais": "Equador", "lat": -1.831, "lon": -78.183, "tax": 35},
    {"pais": "Peru", "lat": -9.190, "lon": -75.015, "tax": 4}, # Variável, mas baixo para herdeiros diretos
    {"pais": "Argentina", "lat": -38.416, "lon": -63.616, "tax": 5}, # Imposto de transmissão gratuita varia, mas geralmente baixo
    {"pais": "Uruguai", "lat": -32.522, "lon": -55.765, "tax": 4},
]

df_globo = pd.DataFrame(data_globo)

# Aplica as cores baseadas na taxa
df_globo['color'] = df_globo['tax'].apply(get_color_by_tax)
# Define tamanho (Você fica maior)
df_globo['size'] = df_globo['pais'].apply(lambda x: 25 if "Você" in x else 12)

# Ordena para o gráfico de barras
df_chart = df_globo.sort_values(by='tax', ascending=True) # Ascendente para barra horizontal ficar melhor ou vertical

col_chart, col_globo = st.columns([1, 1], gap="medium")

# --- Lado Esquerdo: Gráfico de Barras ---
with col_chart:
    fig_bar = px.bar(
        df_chart, 
        x='tax', 
        y='pais', 
        orientation='h',
        text='tax',
        title="Ranking de Alíquotas Máximas",
    )
    # Atualiza as cores individualmente para corresponder à logica do semáforo
    fig_bar.update_traces(
        marker_color=df_chart['color'],
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis=dict(showgrid=False, title="Alíquota (%)", range=[0, 60]),
        yaxis=dict(title=None),
        margin=dict(l=0, r=0, t=40, b=0),
        height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Lado Direito: Globo Interativo ---
with col_globo:
    fig_globe = go.Figure(data=go.Scattergeo(
        lon = df_globo['lon'],
        lat = df_globo['lat'],
        text = df_globo['pais'] + ": " + df_globo['tax'].astype(str) + "%",
        mode = 'markers+text', # Tirei o texto do mapa para não poluir, se quiser voltar use 'markers+text'
        marker = dict(
            size = df_globo['size'],
            color = df_globo['color'],
            line = dict(width=1, color='white'),
            opacity = 0.9
        ),
        textposition="top center"
    ))

    fig_globe.update_layout(
        geo = dict(
            projection_type = "orthographic",
            showland = True,
            landcolor = "#f3f4f6", # Cor clara/terra padrão
            showocean = True,
            oceancolor = "#a4d4f2", # Azul claro oceano padrão
            showcountries = True,
            countrycolor = "#888888",
            projection_rotation = dict(lon=-50, lat=-15, roll=0)
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        font=dict(color="black") # Texto no mapa fica melhor preto com fundo claro
    )
    st.plotly_chart(fig_globe, use_container_width=True)

# ==========================================================
# SEÇÃO 5: SOLUÇÃO
# ==========================================================
st.markdown("---")
st.subheader("🛠️ Ferramenta de Solução: Liquidez Fiscal")

if is_casado and percentual_meacao > 0:
    st.markdown(f"""
    <div class="warning-box">
        <b>⚠️ Atenção ao Casal:</b> Devido ao regime de <b>{regime_casamento}</b>, 
        ambos os cônjuges possuem risco sucessório. A solução abaixo deve ser duplicada.
    </div>
    """, unsafe_allow_html=True)

col_solucao_inputs, col_solucao_grafico = st.columns([1, 1.5], gap="large")

with col_solucao_inputs:
    st.write(f"Simulação para: **{nome_cliente if nome_cliente else 'Cliente Principal'}**")
    
    cobertura_sugerida = st.number_input("Capital Segurado Necessário", value=custo_total, step=50000.0, format="%.2f")
    anos_pagamento = st.slider("Tempo de Pagamento (Anos)", 1, 30, 10)
    premio_anual = st.number_input("Prêmio Anual (Investimento)", value=(cobertura_sugerida * 0.04), step=1000.0, format="%.2f")
    
    custo_total_seguro = premio_anual * anos_pagamento
    alavancagem = cobertura_sugerida / custo_total_seguro if custo_total_seguro > 0 else 0
    
    st.markdown(f"""
    <div class="solution-box">
        <h3 style="color:#00FF7F; text-align:center;">Alavancagem: {alavancagem:.1f}x</h3>
        <p>Custo Total Apólice: <b>{format_currency(custo_total_seguro)}</b></p>
        <p>Liquidez Gerada: <b>{format_currency(cobertura_sugerida)}</b></p>
    </div>
    """, unsafe_allow_html=True)

with col_solucao_grafico:
    st.write("### 📉 Desconto no Imposto (Via Seguro)")
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        x=['Sem Planejamento'], y=[custo_total],
        text=[format_currency(custo_total)], textposition='auto',
        marker_color='#FF4B4B', name='Custo Inventário'
    ))
    fig_comp.add_trace(go.Bar(
        x=['Com Seguro'], y=[custo_total_seguro],
        text=[format_currency(custo_total_seguro)], textposition='auto',
        marker_color='#00FF7F', name='Custo Apólice'
    ))
    fig_comp.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white',
        yaxis=dict(showgrid=False, title=None), height=300, showlegend=False
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ==========================================================
# SEÇÃO 6: DIAGNÓSTICO
# ==========================================================
st.markdown("### 6. Diagnóstico Final")

saudacao = f"Prezados <b>{nome_cliente}</b> e <b>{nome_conjuge}</b>" if is_casado and nome_conjuge else f"Prezado(a) <b>{nome_cliente}</b>"
texto_meacao = f"Considerando o regime de <b>{regime_casamento}</b>, calculamos o risco individual de cada cônjuge." if is_casado else "Cálculo realizado sobre a totalidade dos bens."

texto_diagnostico = f"""
<div class="client-box">
    <p class="client-text">
        {saudacao}, o patrimônio total da família é de <span class="highlight">{format_currency(total_patrimonio_bruto)}</span>.
        {texto_meacao}
    </p>
    <p class="client-text">
        Identificamos um custo sucessório estimado de <span class="highlight">{format_currency(custo_total)}</span> para a sucessão do titular.
        {f"Vale ressaltar que o cônjuge possui uma exposição idêntica, totalizando um risco familiar de <b>{format_currency(custo_total*2)}</b>." if is_casado and percentual_meacao > 0 else ""}
    </p>
    <p class="client-text">
        A utilização do Seguro de Vida permite quitar esse custo pagando apenas <span class="highlight-green">{format_currency(custo_total_seguro)}</span> 
        ao longo dos anos, garantindo a integridade do legado familiar.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)
