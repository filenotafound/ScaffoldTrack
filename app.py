import streamlit as st
import pandas as pd
from database import DatabaseManager
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# Configuração da página
st.set_page_config(
    page_title="CMMS - Sistema de Controle de Andaimes",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar banco de dados
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# Sidebar para navegação
st.sidebar.title("🏗️ CMMS Andaimes")
st.sidebar.markdown("---")

# Seção de seleção de Cliente e Obra
st.sidebar.subheader("🏢 Contexto Atual")

# Obter listas de clientes e obras
clientes = db.get_clientes()
obras = db.get_obras()

# Seleção de Cliente
if 'cliente_selecionado_id' not in st.session_state:
    st.session_state.cliente_selecionado_id = None

if clientes:
    cliente_options = {f"{c['nome']} - {c.get('empresa', 'Pessoa Física') or 'Pessoa Física'}": c['id'] for c in clientes}
    cliente_options["Nenhum cliente selecionado"] = None
    
    cliente_key = st.sidebar.selectbox(
        "👤 Cliente:",
        options=list(cliente_options.keys()),
        index=list(cliente_options.keys()).index("Nenhum cliente selecionado") if st.session_state.cliente_selecionado_id is None else 
              [i for i, (k, v) in enumerate(cliente_options.items()) if v == st.session_state.cliente_selecionado_id][0] if st.session_state.cliente_selecionado_id in cliente_options.values() else 0,
        key="cliente_selector"
    )
    st.session_state.cliente_selecionado_id = cliente_options[cliente_key]
else:
    st.sidebar.info("📝 Cadastre clientes primeiro")
    st.session_state.cliente_selecionado_id = None

# Seleção de Obra
if 'obra_selecionada_id' not in st.session_state:
    st.session_state.obra_selecionada_id = None

if obras:
    # Filtrar obras por cliente se um cliente estiver selecionado
    if st.session_state.cliente_selecionado_id:
        obras_filtradas = [o for o in obras if o['cliente_id'] == st.session_state.cliente_selecionado_id]
    else:
        obras_filtradas = obras
    
    if obras_filtradas:
        obra_options = {f"{o['nome']} - {o['cliente_nome'] or 'Cliente não definido'}": o['id'] for o in obras_filtradas}
        obra_options["Nenhuma obra selecionada"] = None
        
        obra_key = st.sidebar.selectbox(
            "🏗️ Obra:",
            options=list(obra_options.keys()),
            index=list(obra_options.keys()).index("Nenhuma obra selecionada") if st.session_state.obra_selecionada_id is None else 
                  [i for i, (k, v) in enumerate(obra_options.items()) if v == st.session_state.obra_selecionada_id][0] if st.session_state.obra_selecionada_id in obra_options.values() else 0,
            key="obra_selector"
        )
        st.session_state.obra_selecionada_id = obra_options[obra_key]
    else:
        st.sidebar.info("🏗️ Nenhuma obra para este cliente")
        st.session_state.obra_selecionada_id = None
else:
    st.sidebar.info("📝 Cadastre obras primeiro")
    st.session_state.obra_selecionada_id = None

# Mostrar contexto atual
if st.session_state.cliente_selecionado_id and st.session_state.obra_selecionada_id:
    cliente_atual = next(c for c in clientes if c['id'] == st.session_state.cliente_selecionado_id)
    obra_atual = next(o for o in obras if o['id'] == st.session_state.obra_selecionada_id)
    st.sidebar.success(f"✅ {cliente_atual['nome'][:15]}...\n🏗️ {obra_atual['nome'][:15]}...")
elif st.session_state.cliente_selecionado_id:
    cliente_atual = next(c for c in clientes if c['id'] == st.session_state.cliente_selecionado_id)
    st.sidebar.info(f"👤 {cliente_atual['nome'][:20]}...")
elif st.session_state.obra_selecionada_id:
    obra_atual = next(o for o in obras if o['id'] == st.session_state.obra_selecionada_id)
    st.sidebar.info(f"🏗️ {obra_atual['nome'][:20]}...")

st.sidebar.markdown("---")

pages = {
    "Dashboard": "dashboard",
    "Clientes": "clientes", 
    "Obras": "obras",
    "Equipamentos": "equipamentos",
    "Movimentação": "movimentacao",
    "Checklists": "checklists",
    "Relatórios": "relatorios"
}

selected_page = st.sidebar.selectbox("📍 Navegação", list(pages.keys()))

# Criar contexto para passar aos módulos
contexto = {
    'cliente_id': st.session_state.cliente_selecionado_id,
    'obra_id': st.session_state.obra_selecionada_id,
    'cliente_nome': next((c['nome'] for c in clientes if c['id'] == st.session_state.cliente_selecionado_id), None) if st.session_state.cliente_selecionado_id else None,
    'obra_nome': next((o['nome'] for o in obras if o['id'] == st.session_state.obra_selecionada_id), None) if st.session_state.obra_selecionada_id else None
}

# Dashboard principal
if selected_page == "Dashboard":
    st.title("📊 Dashboard - Sistema CMMS")
    
    # Mostrar contexto se selecionado
    if st.session_state.obra_selecionada_id:
        obra_atual = next(o for o in obras if o['id'] == st.session_state.obra_selecionada_id)
        cliente_atual = next(c for c in clientes if c['id'] == obra_atual['cliente_id']) if obra_atual['cliente_id'] else None
        
        cliente_info = f"- {cliente_atual['nome']}" if cliente_atual else ""
        st.info(f"📊 Dashboard para: **{obra_atual['nome']}** {cliente_info}")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.obra_selecionada_id:
            # Contar equipamentos enviados para esta obra específica
            equipamentos_obra = db.get_equipamentos_enviados_obra(st.session_state.obra_selecionada_id)
            total_equipamentos_obra = sum(eq.get('quantidade_enviada', 0) for eq in equipamentos_obra)
            st.metric("Equipamentos na Obra", total_equipamentos_obra)
        else:
            total_equipamentos = db.get_total_equipamentos()
            st.metric("Total de Equipamentos", total_equipamentos)
    
    with col2:
        if st.session_state.obra_selecionada_id:
            # Tipos de equipamentos na obra
            tipos_obra = len(db.get_equipamentos_enviados_obra(st.session_state.obra_selecionada_id))
            st.metric("Tipos de Equipamentos", tipos_obra)
        else:
            equipamentos_enviados = db.get_equipamentos_by_status("enviado")
            st.metric("Equipamentos Enviados", len(equipamentos_enviados))
    
    with col3:
        equipamentos_manutencao = db.get_equipamentos_by_status("manutencao")
        st.metric("Em Manutenção", len(equipamentos_manutencao))
    
    with col4:
        total_clientes = db.get_total_clientes()
        st.metric("Total de Clientes", total_clientes)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status dos Equipamentos")
        status_data = db.get_equipamentos_status_summary()
        if status_data:
            df_status = pd.DataFrame(status_data)
            fig = px.pie(df_status, values='quantidade', names='status', 
                        title="Distribuição por Status")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum equipamento cadastrado ainda")
    
    with col2:
        st.subheader("Movimentações Recentes")
        movimentacoes = db.get_recent_movimentacoes(10)
        if movimentacoes:
            df_mov = pd.DataFrame(movimentacoes)
            st.dataframe(df_mov, use_container_width=True)
        else:
            st.info("Nenhuma movimentação registrada ainda")

# Importar módulos
elif selected_page == "Clientes":
    from modules.clientes import show_clientes_page
    show_clientes_page(db, contexto)

elif selected_page == "Obras":
    from modules.obras import show_obras_page
    show_obras_page(db, contexto)

elif selected_page == "Equipamentos":
    from modules.equipamentos import show_equipamentos_page
    show_equipamentos_page(db, contexto)

elif selected_page == "Movimentação":
    from modules.movimentacao import show_movimentacao_page
    show_movimentacao_page(db, contexto)

elif selected_page == "Checklists":
    from modules.checklists import show_checklists_page
    show_checklists_page(db, contexto)

elif selected_page == "Relatórios":
    from modules.relatorios import show_relatorios_page
    show_relatorios_page(db, contexto)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**CMMS Andaimes v1.0**")
st.sidebar.markdown("Sistema de Controle de Andaimes")
