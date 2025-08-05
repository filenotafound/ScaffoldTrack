import streamlit as st
import pandas as pd

def show_clientes_page(db, contexto=None):
    st.title("👥 Gestão de Clientes")
    
    # Abas
    tab1, tab2 = st.tabs(["Lista de Clientes", "Cadastrar Cliente"])
    
    with tab1:
        st.subheader("Clientes Cadastrados")
        
        clientes = db.get_clientes()
        
        if clientes:
            df = pd.DataFrame(clientes)
            
            # Busca
            search = st.text_input("Buscar cliente:", placeholder="Digite o nome do cliente...")
            if search:
                df = df[df['nome'].str.contains(search, case=False, na=False)]
            
            # Mostrar tabela
            for idx, cliente in df.iterrows():
                with st.expander(f"📋 {cliente['nome']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Contato:** {cliente['contato'] or 'N/A'}")
                        st.write(f"**Telefone:** {cliente['telefone'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Email:** {cliente['email'] or 'N/A'}")
                        st.write(f"**Endereço:** {cliente['endereco'] or 'N/A'}")
                    
                    with col3:
                        if st.button("✏️ Editar", key=f"edit_{cliente['id']}"):
                            st.session_state[f"edit_cliente_{cliente['id']}"] = True
                        
                        if st.button("🗑️ Excluir", key=f"delete_{cliente['id']}"):
                            if st.confirm("Tem certeza que deseja excluir este cliente?"):
                                db.delete_cliente(cliente['id'])
                                st.success("Cliente excluído com sucesso!")
                                st.rerun()
                    
                    # Formulário de edição
                    if st.session_state.get(f"edit_cliente_{cliente['id']}", False):
                        st.markdown("---")
                        st.write("**Editar Cliente:**")
                        
                        with st.form(f"edit_form_{cliente['id']}"):
                            nome = st.text_input("Nome *", value=cliente['nome'])
                            contato = st.text_input("Contato", value=cliente['contato'] or "")
                            telefone = st.text_input("Telefone", value=cliente['telefone'] or "")
                            email = st.text_input("Email", value=cliente['email'] or "")
                            endereco = st.text_area("Endereço", value=cliente['endereco'] or "")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Salvar"):
                                    if nome:
                                        db.update_cliente(cliente['id'], nome, contato, telefone, email, endereco)
                                        st.success("Cliente atualizado com sucesso!")
                                        st.session_state[f"edit_cliente_{cliente['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Nome é obrigatório!")
                            
                            with col2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"edit_cliente_{cliente['id']}"] = False
                                    st.rerun()
        else:
            st.info("Nenhum cliente cadastrado ainda.")
    
    with tab2:
        st.subheader("Cadastrar Novo Cliente")
        
        with st.form("cliente_form"):
            nome = st.text_input("Nome do Cliente *")
            contato = st.text_input("Pessoa de Contato")
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            endereco = st.text_area("Endereço")
            
            if st.form_submit_button("💾 Cadastrar Cliente"):
                if nome:
                    db.add_cliente(nome, contato, telefone, email, endereco)
                    st.success("Cliente cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Nome é obrigatório!")
        
        st.caption("* Campos obrigatórios")
