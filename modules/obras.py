import streamlit as st
import pandas as pd
from datetime import date

def show_obras_page(db, contexto=None):
    st.title("🏗️ Gestão de Obras")
    
    # Abas
    tab1, tab2 = st.tabs(["Lista de Obras", "Cadastrar Obra"])
    
    with tab1:
        st.subheader("Obras Cadastradas")
        
        obras = db.get_obras()
        
        if obras:
            df = pd.DataFrame(obras)
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("Buscar obra:", placeholder="Digite o nome da obra...")
            with col2:
                status_filter = st.selectbox("Filtrar por status:", ["Todos", "ativa", "concluida", "pausada"])
            
            # Aplicar filtros
            if search:
                df = df[df['nome'].str.contains(search, case=False, na=False)]
            
            if status_filter != "Todos":
                df = df[df['status'] == status_filter]
            
            # Mostrar obras
            for idx, obra in df.iterrows():
                status_color = {"ativa": "🟢", "concluida": "🔵", "pausada": "🟡"}.get(obra['status'], "⚪")
                
                with st.expander(f"{status_color} {obra['nome']} - {obra['cliente_nome'] or 'Cliente não informado'}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Cliente:** {obra['cliente_nome'] or 'N/A'}")
                        st.write(f"**Responsável:** {obra['responsavel'] or 'N/A'}")
                        st.write(f"**Telefone:** {obra['telefone'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Status:** {obra['status']}")
                        st.write(f"**Data Início:** {obra['data_inicio'] or 'N/A'}")
                        st.write(f"**Data Fim:** {obra['data_fim'] or 'N/A'}")
                        st.write(f"**Endereço:** {obra['endereco'] or 'N/A'}")
                    
                    with col3:
                        if st.button("✏️ Editar", key=f"edit_obra_{obra['id']}"):
                            st.session_state[f"edit_obra_{obra['id']}"] = True
                        
                        if st.button("🗑️ Excluir", key=f"delete_obra_{obra['id']}"):
                            if st.confirm("Tem certeza que deseja excluir esta obra?"):
                                db.delete_obra(obra['id'])
                                st.success("Obra excluída com sucesso!")
                                st.rerun()
                    
                    # Formulário de edição
                    if st.session_state.get(f"edit_obra_{obra['id']}", False):
                        st.markdown("---")
                        st.write("**Editar Obra:**")
                        
                        clientes = db.get_clientes()
                        cliente_options = {f"{c['nome']} (ID: {c['id']})": c['id'] for c in clientes}
                        
                        with st.form(f"edit_obra_form_{obra['id']}"):
                            nome = st.text_input("Nome da Obra *", value=obra['nome'])
                            
                            # Cliente
                            current_cliente = next((f"{c['nome']} (ID: {c['id']})" for c in clientes if c['id'] == obra['cliente_id']), None)
                            cliente_key = st.selectbox("Cliente", options=list(cliente_options.keys()), 
                                                     index=list(cliente_options.keys()).index(current_cliente) if current_cliente else 0)
                            cliente_id = cliente_options[cliente_key] if cliente_key else None
                            
                            endereco = st.text_area("Endereço", value=obra['endereco'] or "")
                            responsavel = st.text_input("Responsável", value=obra['responsavel'] or "")
                            telefone = st.text_input("Telefone", value=obra['telefone'] or "")
                            
                            col_date1, col_date2 = st.columns(2)
                            with col_date1:
                                data_inicio = st.date_input("Data Início", 
                                                          value=pd.to_datetime(obra['data_inicio']).date() if obra['data_inicio'] else None)
                            with col_date2:
                                data_fim = st.date_input("Data Fim", 
                                                       value=pd.to_datetime(obra['data_fim']).date() if obra['data_fim'] else None)
                            
                            status = st.selectbox("Status", ["ativa", "concluida", "pausada"], 
                                                index=["ativa", "concluida", "pausada"].index(obra['status']))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Salvar"):
                                    if nome:
                                        db.update_obra(obra['id'], nome, cliente_id, endereco, responsavel, 
                                                     telefone, data_inicio, data_fim, status)
                                        st.success("Obra atualizada com sucesso!")
                                        st.session_state[f"edit_obra_{obra['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Nome da obra é obrigatório!")
                            
                            with col2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"edit_obra_{obra['id']}"] = False
                                    st.rerun()
        else:
            st.info("Nenhuma obra cadastrada ainda.")
    
    with tab2:
        st.subheader("Cadastrar Nova Obra")
        
        clientes = db.get_clientes()
        
        if not clientes:
            st.warning("⚠️ É necessário cadastrar pelo menos um cliente antes de criar uma obra.")
            st.markdown("[Ir para Cadastro de Clientes](./clientes)")
        else:
            with st.form("obra_form"):
                nome = st.text_input("Nome da Obra *")
                
                # Seleção de cliente
                cliente_options = {f"{c['nome']} (ID: {c['id']})": c['id'] for c in clientes}
                cliente_key = st.selectbox("Cliente *", options=list(cliente_options.keys()))
                cliente_id = cliente_options[cliente_key] if cliente_key else None
                
                endereco = st.text_area("Endereço da Obra")
                responsavel = st.text_input("Responsável pela Obra")
                telefone = st.text_input("Telefone de Contato")
                
                col1, col2 = st.columns(2)
                with col1:
                    data_inicio = st.date_input("Data de Início", value=date.today())
                with col2:
                    data_fim = st.date_input("Data Prevista de Fim", value=None)
                
                if st.form_submit_button("💾 Cadastrar Obra"):
                    if nome and cliente_id:
                        db.add_obra(nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim)
                        st.success("Obra cadastrada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Nome da obra e cliente são obrigatórios!")
            
            st.caption("* Campos obrigatórios")
