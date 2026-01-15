import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
    
    /* Ajuste da tabela para ficar elegante */
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
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

# --- Título e Dados do Cliente (COM DATAS) ---
st.title("Calculadora de Planejamento Patrimonial")

# Linha 1: Nomes
col_dados1, col_dados2, col_dados3 = st.columns([1.5, 0.5, 1.5])
with col_dados1:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva")
with col_dados2:
    st.write("") 
    st.write("") 
    is_casado = st.toggle("Casado(a)?")
with col_dados3:
    if is_casado:
        nome_conjuge = st.text_input("Nome do Cônjuge", placeholder="Ex: Maria da Silva")

# Linha 2: Datas de Nascimento e Regime
col_nasc1, col_nasc2, col_nasc3 = st.columns([1.5, 0.5, 1.5])

# Inicializa variaveis
ano_atual = datetime.now().year
idade_cliente = 0
idade_conjuge = 0
regime_casamento = "Separação Total de Bens"
percentual_meacao = 0.0

with col_nasc1:
    # Optei por Number Input para o Ano para flexibilidade, mas calculando a idade
    ano_nasc_cliente = st.number_input("Ano de Nascimento (Cliente)", min_value=1920, max_value=ano_atual, value=1975, step=1)
    idade_cliente = ano_atual - ano_nasc_cliente

with col_nasc2:
    st.write("") # Espaço

with col_nasc3:
    if is_casado:
        col_c_nasc, col_c_reg = st.columns([1, 1])
        with col_c_nasc:
            ano_nasc_conjuge = st.number_input("Ano Nascimento (Cônjuge)", min_value=1920, max_value=ano_atual, value=1978, step=1)
            idade_conjuge = ano_atual - ano_nasc_conjuge
        with col_c_reg:
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

# Dados Ampliados
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

# ==========================================================
# SEÇÃO 5: SOLUÇÃO (SIMULADOR EVOLUTIVO)
# ==========================================================
st.markdown("---")
st.subheader("🛠️ Solução: Liquidez e Alavancagem Fiscal")

if is_casado and percentual_meacao > 0:
    st.markdown(f"""
    <div class="warning-box">
        <b>⚠️ Atenção ao Casal:</b> Devido ao regime de <b>{regime_casamento}</b>, 
        a simulação abaixo considera a <b>parte individual</b>. O ideal é duplicar a proteção (uma apólice para {nome_cliente} e outra para {nome_conjuge}).
    </div>
    """, unsafe_allow_html=True)

# Inputs da Solução
col_sol_1, col_sol_2, col_sol_3 = st.columns([1, 1, 1])

with col_sol_1:
    cobertura_sugerida = st.number_input("Capital Segurado Necessário (Hoje)", value=custo_total, step=50000.0, format="%.2f")

with col_sol_2:
    anos_pagamento = st.slider("Tempo de Pagamento (Anos)", 1, 30, 10)
    
with col_sol_3:
    premio_anual = st.number_input("Prêmio Anual Inicial (Investimento)", value=(cobertura_sugerida * 0.04), step=1000.0, format="%.2f")
    taxa_reajuste = st.number_input("Taxa de Reajuste Anual (IPCA/IGP-M %)", value=5.0, step=0.5, format="%.1f")

# --- LÓGICA DA TABELA EVOLUTIVA ---
st.write("### 📈 Evolução da Alavancagem Patrimonial")

# Estado para controlar quantas linhas mostramos
if 'simulacao_anos' not in st.session_state:
    st.session_state.simulacao_anos = 16

# Função para gerar os dados
data_simulacao = []
capital_atual = cobertura_sugerida
premio_atual = premio_anual
acumulado = 0.0
idade_atual = idade_cliente

for i in range(1, st.session_state.simulacao_anos + 1):
    ano_calendario = ano_atual + i
    idade_simulada = idade_atual + i
    
    # Lógica de Pagamento: Só paga se estiver dentro do prazo (anos_pagamento)
    if i <= anos_pagamento:
        aporte_do_ano = premio_atual
        # Prepara o prêmio do ano seguinte (reajuste)
        premio_proximo = premio_atual * (1 + (taxa_reajuste/100))
    else:
        aporte_do_ano = 0.0
        premio_proximo = 0.0 # Não tem mais prêmio
    
    acumulado += aporte_do_ano
    
    # Cálculo da Alavancagem (Capital / O que pagou até agora)
    if acumulado > 0:
        alavancagem_x = capital_atual / acumulado
    else:
        alavancagem_x = 0
        
    data_simulacao.append({
        "Ano": ano_calendario,
        "Idade": idade_simulada,
        "Capital Segurado (R$)": capital_atual,
        "Aporte Anual (R$)": aporte_do_ano,
        "Total Pago Acumulado (R$)": acumulado,
        "Alavancagem": f"{alavancagem_x:.1f}x"
    })
    
    # Atualiza variaveis para proxima iteração
    capital_atual = capital_atual * (1 + (taxa_reajuste/100))
    premio_atual = premio_proximo

# Criação do DataFrame
df_simulacao = pd.DataFrame(data_simulacao)

# Configuração de exibição da Tabela (Streamlit Column Config)
st.dataframe(
    df_simulacao,
    column_config={
        "Ano": st.column_config.NumberColumn("Ano", format="%d"),
        "Idade": st.column_config.NumberColumn("Idade", format="%d"),
        "Capital Segurado (R$)": st.column_config.NumberColumn("Capital Segurado", format="R$ %.2f"),
        "Aporte Anual (R$)": st.column_config.NumberColumn("Aporte Anual", format="R$ %.2f"),
        "Total Pago Acumulado (R$)": st.column_config.NumberColumn("Total Pago", format="R$ %.2f"),
        "Alavancagem": st.column_config.TextColumn("Alavancagem", help="Quantas vezes o capital é maior que o valor pago."),
    },
    use_container_width=True,
    hide_index=True
)

# Botão para carregar mais anos
if st.button("Carregar +10 Anos"):
    st.session_state.simulacao_anos += 10
    st.rerun()

# ==========================================================
# SEÇÃO 6: DIAGNÓSTICO
# ==========================================================
st.markdown("### 6. Diagnóstico Final")

saudacao = f"Prezados <b>{nome_cliente}</b> e <b>{nome_conjuge}</b>" if is_casado and nome_conjuge else f"Prezado(a) <b>{nome_cliente}</b>"
texto_meacao = f"Considerando o regime de <b>{regime_casamento}</b>, calculamos o risco individual de cada cônjuge." if is_casado else "Cálculo realizado sobre a totalidade dos bens."

# Pega a alavancagem do último ano pago para o texto
alavancagem_final = cobertura_sugerida / (premio_anual * anos_pagamento) if (premio_anual * anos_pagamento) > 0 else 0

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
    <p class="client-text">
        Como demonstrado na tabela acima, nos primeiros anos a proteção é quase gratuita (alavancagem altíssima). 
        Mesmo ao final do plano, você terá pago apenas uma fração do benefício total, garantindo que o patrimônio fique na família e não fique para o governo.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)
