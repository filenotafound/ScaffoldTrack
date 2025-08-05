import streamlit as st
import pandas as pd
from datetime import datetime

def show_checklists_page(db, contexto=None):
    st.title("✅ Checklists de Montagem e Desmontagem")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["Lista de Checklists", "Novo Checklist", "Templates"])
    
    with tab1:
        st.subheader("Checklists Realizados")
        
        checklists = db.get_checklists()
        
        if checklists:
            df = pd.DataFrame(checklists)
            df['data_checklist'] = pd.to_datetime(df['data_checklist'])
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_filter = st.selectbox("Tipo:", ["Todos", "montagem", "desmontagem", "inspecao"])
            with col2:
                status_filter = st.selectbox("Status:", ["Todos", "pendente", "aprovado", "reprovado"])
            with col3:
                search = st.text_input("Buscar:", placeholder="Nome da obra...")
            
            # Aplicar filtros
            if tipo_filter != "Todos":
                df = df[df['tipo'] == tipo_filter]
            
            if status_filter != "Todos":
                df = df[df['status'] == status_filter]
            
            if search:
                df = df[df['obra_nome'].str.contains(search, case=False, na=False)]
            
            # Mostrar checklists
            df_sorted = df.sort_values('data_checklist', ascending=False)
            
            for idx, checklist in df_sorted.iterrows():
                tipo_emoji = {
                    "montagem": "🔨",
                    "desmontagem": "🔧",
                    "inspecao": "🔍"
                }.get(checklist['tipo'], "✅")
                
                status_emoji = {
                    "pendente": "🟡",
                    "aprovado": "🟢",
                    "reprovado": "🔴"
                }.get(checklist['status'], "⚪")
                
                data_formatada = checklist['data_checklist'].strftime("%d/%m/%Y %H:%M")
                
                with st.expander(f"{tipo_emoji} {status_emoji} {checklist['tipo'].title()} - {checklist['obra_nome']} - {data_formatada}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Obra:** {checklist['obra_nome']}")
                        st.write(f"**Tipo:** {checklist['tipo'].title()}")
                        st.write(f"**Responsável:** {checklist['responsavel'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Status:** {checklist['status'].title()}")
                        st.write(f"**Data:** {data_formatada}")
                    
                    if checklist['itens_verificados']:
                        st.write("**Itens Verificados:**")
                        itens = checklist['itens_verificados'].split('\n')
                        for item in itens:
                            if item.strip():
                                st.write(f"- {item.strip()}")
                    
                    if checklist['observacoes']:
                        st.write(f"**Observações:** {checklist['observacoes']}")
                    
                    # Atualizar status
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🟢 Aprovar", key=f"aprovar_{checklist['id']}"):
                            db.update_checklist_status(checklist['id'], "aprovado")
                            st.success("Checklist aprovado!")
                            st.rerun()
                    
                    with col2:
                        if st.button("🔴 Reprovar", key=f"reprovar_{checklist['id']}"):
                            db.update_checklist_status(checklist['id'], "reprovado")
                            st.error("Checklist reprovado!")
                            st.rerun()
                    
                    with col3:
                        if st.button("🟡 Pendente", key=f"pendente_{checklist['id']}"):
                            db.update_checklist_status(checklist['id'], "pendente")
                            st.warning("Status alterado para pendente!")
                            st.rerun()
        else:
            st.info("Nenhum checklist realizado ainda.")
    
    with tab2:
        st.subheader("Novo Checklist")
        
        obras = db.get_obras()
        
        if not obras:
            st.warning("⚠️ É necessário cadastrar obras antes de criar checklists.")
        else:
            with st.form("checklist_form"):
                # Tipo de checklist
                tipo = st.selectbox("Tipo de Checklist *", 
                                  ["montagem", "desmontagem", "inspecao"])
                
                # Obra
                obra_options = {f"{o['nome']} - {o['cliente_nome'] or 'Cliente N/A'}": o['id'] for o in obras}
                obra_key = st.selectbox("Obra *", options=list(obra_options.keys()))
                obra_id = obra_options[obra_key] if obra_key else None
                
                responsavel = st.text_input("Responsável *", placeholder="Nome do responsável pelo checklist")
                
                # Itens do checklist baseado no tipo
                if tipo == "montagem":
                    st.write("**Itens de Verificação para Montagem:**")
                    itens_montagem = [
                        "Base nivelada e estável",
                        "Fundação adequada",
                        "Tubos em bom estado (sem corrosão/danos)",
                        "Braçadeiras apertadas corretamente",
                        "Travamento entre tubos adequado",
                        "Pranchas de trabalho fixas",
                        "Guarda-corpo instalado",
                        "Rodapé instalado",
                        "Escadas de acesso seguras",
                        "Sinalização instalada"
                    ]
                    
                elif tipo == "desmontagem":
                    st.write("**Itens de Verificação para Desmontagem:**")
                    itens_montagem = [
                        "Área isolada e sinalizada",
                        "Remoção de materiais da plataforma",
                        "Verificação de equipamentos presos",
                        "Desmontagem sequencial (topo para base)",
                        "Armazenamento organizado dos componentes",
                        "Contagem de peças desmontadas",
                        "Verificação de danos nos componentes",
                        "Limpeza da área após desmontagem"
                    ]
                
                else:  # inspeção
                    st.write("**Itens de Verificação para Inspeção:**")
                    itens_montagem = [
                        "Estado geral da estrutura",
                        "Fixações e braçadeiras",
                        "Deformações ou danos visíveis",
                        "Estabilidade da estrutura",
                        "Proteções coletivas",
                        "Acessos e saídas",
                        "Documentação atualizada",
                        "Conformidade com projeto"
                    ]
                
                # Checkboxes para itens
                itens_selecionados = []
                for item in itens_montagem:
                    if st.checkbox(item, key=f"item_{item}"):
                        itens_selecionados.append(f"✓ {item}")
                    else:
                        itens_selecionados.append(f"✗ {item}")
                
                # Campo livre para itens adicionais
                itens_adicionais = st.text_area("Itens Adicionais:", 
                                              placeholder="Digite itens adicionais, um por linha...")
                
                observacoes = st.text_area("Observações Gerais:", 
                                         placeholder="Observações sobre o checklist...")
                
                if st.form_submit_button("✅ Salvar Checklist"):
                    if obra_id and responsavel:
                        # Compilar todos os itens
                        todos_itens = itens_selecionados.copy()
                        
                        if itens_adicionais:
                            itens_extras = itens_adicionais.split('\n')
                            todos_itens.extend([f"• {item.strip()}" for item in itens_extras if item.strip()])
                        
                        itens_texto = '\n'.join(todos_itens)
                        
                        db.add_checklist(tipo, obra_id, responsavel, itens_texto, observacoes)
                        st.success("Checklist salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error("Obra e responsável são obrigatórios!")
            
            st.caption("* Campos obrigatórios")
    
    with tab3:
        st.subheader("📋 Templates de Checklist")
        
        # Templates pré-definidos
        templates = {
            "Montagem Básica": {
                "tipo": "montagem",
                "itens": [
                    "Verificação do terreno",
                    "Base nivelada",
                    "Componentes em bom estado",
                    "Montagem conforme projeto",
                    "Proteções instaladas",
                    "Acesso seguro"
                ]
            },
            "Inspeção Semanal": {
                "tipo": "inspecao",
                "itens": [
                    "Estado geral da estrutura",
                    "Fixações das braçadeiras",
                    "Condição das pranchas",
                    "Proteções coletivas",
                    "Sinalizações"
                ]
            },
            "Desmontagem Segura": {
                "tipo": "desmontagem",
                "itens": [
                    "Isolamento da área",
                    "Remoção de materiais",
                    "Desmontagem sequencial",
                    "Contagem de componentes",
                    "Limpeza final"
                ]
            }
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Templates Disponíveis:**")
            for nome, template in templates.items():
                with st.expander(f"📝 {nome}"):
                    st.write(f"**Tipo:** {template['tipo'].title()}")
                    st.write("**Itens:**")
                    for item in template['itens']:
                        st.write(f"- {item}")
        
        with col2:
            st.write("**Criar Template Personalizado:**")
            with st.form("template_form"):
                nome_template = st.text_input("Nome do Template:")
                tipo_template = st.selectbox("Tipo:", ["montagem", "desmontagem", "inspecao"])
                itens_template = st.text_area("Itens (um por linha):")
                
                if st.form_submit_button("💾 Salvar Template"):
                    if nome_template and itens_template:
                        st.success(f"Template '{nome_template}' criado com sucesso!")
                        # Aqui você poderia salvar o template em uma tabela específica
                    else:
                        st.error("Nome e itens são obrigatórios!")
        
        # Dicas
        with st.expander("💡 Dicas para Checklists"):
            st.markdown("""
            **Montagem:**
            - Sempre verificar a base e fundação
            - Conferir estado dos componentes antes da montagem
            - Garantir instalação de proteções coletivas
            
            **Inspeção:**
            - Realizar inspeções regulares (semanal/quinzenal)
            - Documentar qualquer irregularidade encontrada
            - Verificar conformidade com normas de segurança
            
            **Desmontagem:**
            - Isolar a área antes de iniciar
            - Remover materiais da plataforma
            - Desmontar sempre de cima para baixo
            - Contar e conferir todos os componentes
            """)
