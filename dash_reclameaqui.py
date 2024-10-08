import pandas as pd 
import numpy as np 
import plotly.express as px
import plotly.io as pio
import streamlit as st 


# Função auxiliar para filtros com checkbox "Selecionar Todos"
def filter_with_select_all(label, options):
    """
    Cria um filtro com um checkbox para selecionar todas as opções ou selecionar individualmente.

    Args:
        label (str): O rótulo do filtro.
        options (iterable): As opções disponíveis para seleção.

    Returns:
        list: A lista de opções selecionadas.
    """
    # Checkbox para selecionar todas as opções
    select_all = st.sidebar.checkbox(f"Selecionar Todas as {label}", key=f"select_all_{label}")

    if select_all:
        return list(options)
    else:
        return st.sidebar.multiselect(
            label=f"Selecione a(s) {label}(s):",
            options=sorted(options),
            default=[],
            key=f"multiselect_{label}"
        )

# Definir a paleta de cores acessível e global
color_palette = px.colors.qualitative.Safe  # Escolha uma paleta acessível
pio.templates["custom_template"] = pio.templates["plotly"]
pio.templates["custom_template"].layout.colorway = color_palette
pio.templates.default = "custom_template"

# Importando os dados
df_reclameaqui = pd.read_csv('RECLAMEAQUI_UNIFICADO_TRATADO.csv')  # Substitua pelo caminho correto
df_reclameaqui['TEMPO'] = pd.to_datetime(df_reclameaqui['TEMPO'])

# Título do Dashboard
st.title("Dashboard - RECLAME AQUI")

st.header("Painel de Monitoramento de Reclamações", divider="gray")

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro por Empresa (LOJA) com "Selecionar Todas as Empresas"
empresas = df_reclameaqui['LOJA'].unique()
empresa_selecionada = filter_with_select_all("Empresa(s)", empresas)

# Filtro por Estado (ESTADO) com "Selecionar Todos os Estados"
estados = df_reclameaqui['ESTADO'].unique()
estado_selecionado = filter_with_select_all("Estado(s)", estados)

# Filtro por Status (STATUS) com "Selecionar Todos os Status"
status = df_reclameaqui['STATUS'].unique()
status_selecionado = filter_with_select_all("Status(s)", status)

# Filtro por Ano (ANO) com "Selecionar Todos os Anos"
anos = df_reclameaqui['ANO'].unique()
ano_selecionado = filter_with_select_all("Ano(s)", anos)

# Filtro por Tamanho do Texto (DESCRIÇÃO) com Slider
min_size = int(df_reclameaqui['TAMANHO_DESCRICAO'].min())
max_size = int(df_reclameaqui['TAMANHO_DESCRICAO'].max())
size_range = st.sidebar.slider(
    "Selecione o intervalo de tamanho do texto da descrição:",
    min_value=min_size,
    max_value=max_size,
    value=(min_size, max_size)
)

# Criar o mapeamento de cores para LOJAs
lojases_unicas = sorted(df_reclameaqui['LOJA'].unique())
paleta = px.colors.qualitative.Safe

# Tratar caso o número de LOJAs exceda a paleta
if len(lojases_unicas) > len(paleta):
    # Combina várias paletas ou adiciona mais cores
    # Exemplo: combinando 'Safe' com 'Set2'
    paleta = paleta + px.colors.qualitative.Set2
    # Se ainda assim for insuficiente, repetir as cores
    if len(lojases_unicas) > len(paleta):
        paleta = paleta * (len(lojases_unicas) // len(paleta) + 1)

color_discrete_map = {loja: paleta[i] for i, loja in enumerate(lojases_unicas)}

# Aplicar filtros
filtro = (
    df_reclameaqui['LOJA'].isin(empresa_selecionada) &
    df_reclameaqui['ESTADO'].isin(estado_selecionado) &
    df_reclameaqui['STATUS'].isin(status_selecionado) &
    df_reclameaqui['TAMANHO_DESCRICAO'].between(size_range[0], size_range[1]) &
    df_reclameaqui['ANO'].isin(ano_selecionado)  # Filtro para Ano
)

df_filtrado = df_reclameaqui[filtro]

# ### Substituição do Resumo Estático por Métricas Dinâmicas ###
st.markdown("### Resumo dos Filtros Aplicados")

# Obter as contagens de reclamações por LOJA
contagens_lojas = df_filtrado['LOJA'].value_counts()

# Número de empresas selecionadas
num_empresas = len(empresa_selecionada)

if num_empresas > 0:
    # Criar as colunas dinamicamente
    cols = st.columns(num_empresas)
    
    # Iterar sobre cada empresa selecionada e sua respectiva coluna
    for col, empresa in zip(cols, empresa_selecionada):
        # Obter a contagem de reclamações para a empresa atual
        count = contagens_lojas.get(empresa, 0)
        
        # Exibir a métrica na coluna correspondente
        col.metric(
            label=empresa,
            value=count
        )
else:
    # Caso nenhuma empresa seja selecionada (opcional)
    st.metric(label="Total de Reclamações", value=0)

# Verificar se o dataframe filtrado não está vazio
if df_filtrado.empty:
    st.warning("Nenhuma reclamação encontrada com os filtros selecionados.")
else:
    # 1. Série Temporal do Número de Reclamações
    st.markdown("### 1. Série Temporal do Número de Reclamações")
    df_time = df_filtrado.groupby(['TEMPO', 'LOJA']).size().reset_index(name='Reclamações')
    df_time['TEMPO'] = df_time['TEMPO'].dt.to_period("M").dt.to_timestamp()

    fig_time = px.line(
        df_time, 
        x='TEMPO', 
        y='Reclamações', 
        color='LOJA',
        color_discrete_map=color_discrete_map,  # Aplicando o mapeamento de cores
        title='Número de Reclamações ao Longo do Tempo por LOJA',
        labels={'Reclamações': 'Número de Reclamações', 'TEMPO': 'Tempo'}
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # 2. Frequência de Reclamações por Estado
    st.markdown("### 2. Frequência de Reclamações por Estado")
    df_estado = df_filtrado.groupby(['ESTADO', 'LOJA']).size().reset_index(name='Reclamações')

    fig_estado = px.bar(
        df_estado, 
        x='ESTADO', 
        y='Reclamações', 
        color='LOJA',
        color_discrete_map=color_discrete_map,  # Aplicando o mapeamento de cores
        barmode='group',
        title='Reclamações por Estado e LOJA',
        labels={'Reclamações': 'Número de Reclamações', 'ESTADO': 'Estado'}
    )
    st.plotly_chart(fig_estado, use_container_width=True)

    # 3. Frequência de Cada Tipo de STATUS
    st.markdown("### 3. Frequência de Cada Tipo de STATUS")
    df_status = df_filtrado.groupby(['STATUS', 'LOJA']).size().reset_index(name='Reclamações')

    fig_status = px.bar(
        df_status, 
        x='STATUS', 
        y='Reclamações', 
        color='LOJA',
        color_discrete_map=color_discrete_map,  # Aplicando o mapeamento de cores
        barmode='group',
        title='Distribuição de Status das Reclamações por LOJA',
        labels={'Reclamações': 'Número de Reclamações', 'STATUS': 'Status'}
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # 4. Distribuição do Tamanho do Texto (DESCRIÇÃO)
    st.markdown("### 4. Distribuição do Tamanho do Texto (DESCRIÇÃO)")
    fig_size = px.histogram(
        df_filtrado, 
        x='TAMANHO_DESCRICAO', 
        color='LOJA',
        color_discrete_map=color_discrete_map,  # Aplicando o mapeamento de cores
        nbins=50, 
        title='Distribuição do Tamanho da Descrição por LOJA',
        labels={'TAMANHO_DESCRICAO': 'Tamanho da Descrição'},
        opacity=0.75
    )
    st.plotly_chart(fig_size, use_container_width=True)

