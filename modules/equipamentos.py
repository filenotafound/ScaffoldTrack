import streamlit as st
import pandas as pd

def show_equipamentos_page(db, contexto=None):
    st.title("🔧 Gestão de Equipamentos")
    
    # Abas
    tab1, tab2 = st.tabs(["Lista de Equipamentos", "Cadastrar Equipamento"])
    
    with tab1:
        st.subheader("Equipamentos Cadastrados")
        
        equipamentos = db.get_equipamentos()
        
        if equipamentos:
            df = pd.DataFrame(equipamentos)
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                search = st.text_input("Buscar equipamento:", placeholder="Digite a descrição...")
            with col2:
                status_filter = st.selectbox("Filtrar por status:", 
                                           ["Todos", "disponivel", "enviado", "manutencao", "perdido"])
            with col3:
                sort_by = st.selectbox("Ordenar por:", ["Descrição", "Quantidade", "Status"])
            
            # Aplicar filtros
            if search:
                df = df[df['descricao'].str.contains(search, case=False, na=False)]
            
            if status_filter != "Todos":
                df = df[df['status'] == status_filter]
            
            # Ordenação
            if sort_by == "Descrição":
                df = df.sort_values('descricao')
            elif sort_by == "Quantidade":
                df = df.sort_values('quantidade', ascending=False)
            elif sort_by == "Status":
                df = df.sort_values('status')
            
            # Estatísticas rápidas com controle real de estoque
            st.markdown("### 📊 Resumo")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_itens = len(df)
                st.metric("Total de Itens", total_itens)
            with col2:
                total_quantidade = df['quantidade'].sum()
                st.metric("Quantidade Total", total_quantidade)
            with col3:
                # Calcular disponível real baseado em movimentações
                total_disponivel = sum(db.get_quantidade_disponivel(equip['id']) for _, equip in df.iterrows())
                st.metric("Realmente Disponíveis", total_disponivel)
            with col4:
                # Calcular em manutenção
                total_manutencao = sum(db.get_quantidade_em_manutencao(equip['id']) for _, equip in df.iterrows())
                st.metric("Em Manutenção", total_manutencao)
            
            st.markdown("---")
            
            # Mostrar equipamentos
            for idx, equip in df.iterrows():
                status_emoji = {
                    "disponivel": "🟢",
                    "enviado": "🔵", 
                    "manutencao": "🟡",
                    "perdido": "🔴"
                }.get(equip['status'], "⚪")
                
                # Calcular quantidades reais
                disponivel = db.get_quantidade_disponivel(equip['id'])
                em_manutencao = db.get_quantidade_em_manutencao(equip['id'])
                enviado = equip['quantidade'] - disponivel - em_manutencao
                
                with st.expander(f"{status_emoji} {equip['descricao']} (Total: {equip['quantidade']}, Disp: {disponivel}, Manut: {em_manutencao})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {equip['descricao']}")
                        st.write(f"**Código:** {equip['codigo'] or 'N/A'}")
                        st.write(f"**Medida:** {equip['medida'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Quantidade Total:** {equip['quantidade']}")
                        st.write(f"**Disponível:** {disponivel}")
                        st.write(f"**Enviado:** {enviado}")
                        st.write(f"**Em Manutenção:** {em_manutencao}")
                        if equip['observacoes']:
                            st.write(f"**Obs:** {equip['observacoes']}")
                    
                    with col3:
                        if st.button("✏️ Editar", key=f"edit_equip_{equip['id']}"):
                            st.session_state[f"edit_equip_{equip['id']}"] = True
                        
                        if st.button("🗑️ Excluir", key=f"delete_equip_{equip['id']}"):
                            if st.confirm("Tem certeza que deseja excluir este equipamento?"):
                                db.delete_equipamento(equip['id'])
                                st.success("Equipamento excluído com sucesso!")
                                st.rerun()
                    
                    # Formulário de edição
                    if st.session_state.get(f"edit_equip_{equip['id']}", False):
                        st.markdown("---")
                        st.write("**Editar Equipamento:**")
                        
                        with st.form(f"edit_equip_form_{equip['id']}"):
                            descricao_input = st.text_input("Descrição *", value=equip['descricao'],
                                                           help="💡 Será convertido automaticamente para MAIÚSCULAS")
                            # Converter automaticamente para maiúsculas
                            descricao = descricao_input.upper() if descricao_input else ""
                            
                            # Mostrar prévia se há mudança
                            if descricao_input and descricao_input != descricao:
                                st.caption(f"📝 Prévia: **{descricao}**")
                            codigo = st.text_input("Código", value=equip['codigo'] or "")
                            medida = st.text_input("Medida", value=equip['medida'] or "")
                            quantidade = st.number_input("Quantidade *", min_value=1, value=equip['quantidade'])
                            status = st.selectbox("Status", 
                                                ["disponivel", "enviado", "manutencao", "perdido"],
                                                index=["disponivel", "enviado", "manutencao", "perdido"].index(equip['status']))
                            observacoes = st.text_area("Observações", value=equip['observacoes'] or "")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Salvar"):
                                    if descricao and quantidade > 0:
                                        # Verificar se já existe equipamento com essa descrição (excluindo o atual)
                                        if db.equipamento_existe(descricao, equip['id']):
                                            st.error(f"❌ Já existe outro equipamento com a descrição '{descricao}'. Use uma descrição diferente!")
                                        else:
                                            db.update_equipamento(equip['id'], descricao, codigo, medida, 
                                                                quantidade, status, observacoes)
                                            st.success("✅ Equipamento atualizado com sucesso!")
                                            st.session_state[f"edit_equip_{equip['id']}"] = False
                                            st.rerun()
                                    else:
                                        st.error("❌ Descrição e quantidade são obrigatórios!")
                            
                            with col2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"edit_equip_{equip['id']}"] = False
                                    st.rerun()
        else:
            st.info("Nenhum equipamento cadastrado ainda.")
    
    with tab2:
        st.subheader("Cadastrar Novo Equipamento")
        
        with st.form("equipamento_form"):
            st.markdown("#### Informações do Equipamento")
            
            descricao_input = st.text_input("Descrição do Equipamento *", 
                                           placeholder="Ex: tubo de andaime 2m",
                                           help="💡 Será convertido automaticamente para MAIÚSCULAS. Não pode ser duplicada.")
            # Converter automaticamente para maiúsculas
            descricao = descricao_input.upper() if descricao_input else ""
            
            # Mostrar prévia e verificar duplicatas
            if descricao_input and descricao_input != descricao:
                st.caption(f"📝 Prévia: **{descricao}**")
            
            # Verificar se descrição já existe (feedback em tempo real)
            if descricao and db.equipamento_existe(descricao):
                st.warning(f"⚠️ Já existe um equipamento com a descrição '{descricao}'")
            
            col1, col2 = st.columns(2)
            with col1:
                codigo = st.text_input("Código (opcional)", 
                                     placeholder="Ex: TAD-2M-001")
            with col2:
                medida = st.text_input("Medida (opcional)", 
                                     placeholder="Ex: 2m x 48mm")
            
            quantidade = st.number_input("Quantidade *", min_value=1, value=1, step=1)
            
            # Status fixo como "disponível" (não editável)
            st.info("📍 Status inicial fixo: **Disponível**")
            status = "disponivel"
            
            observacoes = st.text_area("Observações", 
                                     placeholder="Informações adicionais sobre o equipamento...")
            
            if st.form_submit_button("💾 Cadastrar Equipamento"):
                if descricao and quantidade > 0:
                    # Verificar se já existe equipamento com essa descrição
                    if db.equipamento_existe(descricao):
                        st.error(f"❌ Já existe um equipamento com a descrição '{descricao}'. Use uma descrição diferente!")
                    else:
                        db.add_equipamento(descricao, codigo if codigo else None, 
                                         medida if medida else None, quantidade, 
                                         observacoes if observacoes else None)
                        st.success("✅ Equipamento cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Descrição e quantidade são obrigatórios!")
        
        st.caption("* Campos obrigatórios")
        
        # Dicas
        with st.expander("💡 Dicas para Cadastro"):
            st.markdown("""
            **Descrição:** Seja específico e claro (ex: "Tubo de andaime 2m", "Braçadeira giratória")
            
            **Código:** Use um padrão consistente para facilitar a identificação
            
            **Medida:** Inclua dimensões importantes (comprimento, diâmetro, peso)
            
            **Quantidade:** Registre a quantidade total disponível no estoque
            
            **Status:** 
            - **Disponível:** Equipamento pronto para uso
            - **Enviado:** Equipamento em uso em obra
            - **Manutenção:** Equipamento em reparo
            - **Perdido:** Equipamento perdido ou danificado irreparavelmente
            """)
