import streamlit as st
import pandas as pd
from datetime import datetime

def show_movimentacao_page(db, contexto=None):
    st.title("📦 Movimentação de Equipamentos")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["📋 Histórico", "➕ Nova Movimentação", "📦 Movimentação em Lote"])
    
    with tab1:
        st.subheader("Histórico de Movimentações")
        
        movimentacoes = db.get_movimentacoes()
        
        if movimentacoes:
            df = pd.DataFrame(movimentacoes)
            df['data_movimentacao'] = pd.to_datetime(df['data_movimentacao'])
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_filter = st.selectbox("Tipo:", ["Todos", "envio", "retorno", "manutencao", "retorno_manutencao", "perda", "retorno_perda"])
            with col2:
                data_inicio = st.date_input("Data Início:", format="DD/MM/YYYY")
            with col3:
                data_fim = st.date_input("Data Fim:", format="DD/MM/YYYY")
            
            # Aplicar filtros
            if tipo_filter != "Todos":
                df = df[df['tipo'] == tipo_filter]
            
            if data_inicio:
                df = df[df['data_movimentacao'].dt.date >= data_inicio]
            
            if data_fim:
                df = df[df['data_movimentacao'].dt.date <= data_fim]
            
            # Mostrar movimentações
            df_sorted = df.sort_values('data_movimentacao', ascending=False)
            
            for idx, mov in df_sorted.iterrows():
                tipo_emoji = {
                    "envio": "📤",
                    "retorno": "📥", 
                    "manutencao": "🔧",
                    "retorno_manutencao": "🔧✅",
                    "perda": "❌",
                    "retorno_perda": "🔄"
                }.get(mov['tipo'], "📦")
                
                data_formatada = mov['data_movimentacao'].strftime("%d/%m/%Y")
                
                with st.expander(f"{tipo_emoji} {mov['tipo'].title()} - {mov['equipamento_descricao']} - {data_formatada}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Equipamento:** {mov['equipamento_descricao']}")
                        st.write(f"**Obra:** {mov['obra_nome'] or 'N/A'}")
                        st.write(f"**Quantidade:** {mov['quantidade']}")
                    
                    with col2:
                        st.write(f"**Tipo:** {mov['tipo'].title()}")
                        st.write(f"**Responsável:** {mov['responsavel'] or 'N/A'}")
                        st.write(f"**Data:** {data_formatada}")
                    
                    if mov['observacoes']:
                        st.write(f"**Observações:** {mov['observacoes']}")
        else:
            st.info("Nenhuma movimentação registrada ainda.")
    
    with tab2:
        st.subheader("Registrar Nova Movimentação")
        
        equipamentos = db.get_equipamentos()
        obras = db.get_obras()
        
        if not equipamentos:
            st.warning("⚠️ É necessário cadastrar equipamentos antes de registrar movimentações.")
        else:
            # Tipo de movimentação (fora do form para permitir atualizações dinâmicas)
            tipo = st.selectbox("Tipo de Movimentação *", 
                              ["envio", "retorno", "manutencao", "retorno_manutencao", "perda", "retorno_perda"])
            
            # Obra (para retornos, precisa ser selecionada antes dos equipamentos)
            obra_id = None
            if tipo in ["envio", "retorno"]:
                if obras:
                    obra_options = {f"{o['nome']} - {o['cliente_nome'] or 'Cliente N/A'}": o['id'] for o in obras}
                    obra_key = st.selectbox("Obra *", options=list(obra_options.keys()))
                    obra_id = obra_options[obra_key] if obra_key else None
                else:
                    st.warning("⚠️ É necessário cadastrar obras para registrar envios/retornos.")
            elif tipo in ["manutencao", "retorno_manutencao", "perda", "retorno_perda"]:
                st.info("ℹ️ Movimentações de manutenção e perda não precisam de obra específica.")

            with st.form("movimentacao_form"):
                # Equipamento (filtrado por tipo e obra se necessário)
                equip_options = {}
                equipamentos_disponiveis = []
                
                for e in equipamentos:
                    disponivel = db.get_quantidade_disponivel(e['id'])
                    em_manutencao = db.get_quantidade_em_manutencao(e['id'])
                    
                    # Filtrar equipamentos baseado no tipo de movimentação
                    incluir = False
                    if tipo in ["envio", "manutencao"] and disponivel > 0:
                        incluir = True
                        label = f"{e['descricao']} (Disponível: {disponivel})"
                    elif tipo == "retorno_manutencao" and em_manutencao > 0:
                        incluir = True
                        label = f"{e['descricao']} (Em Manutenção: {em_manutencao})"
                    elif tipo == "perda" and e['quantidade'] > 0:
                        incluir = True
                        label = f"{e['descricao']} (Total: {e['quantidade']})"
                    elif tipo == "retorno_perda":
                        # Para retorno de perda, calcular quantas foram perdidas
                        qtd_perdida = db.get_quantidade_perdida(e['id'])
                        if qtd_perdida > 0:
                            incluir = True
                            label = f"{e['descricao']} (Perdidas: {qtd_perdida})"
                    elif tipo == "retorno" and obra_id:
                        # Para retorno, só mostrar equipamentos que foram enviados para esta obra
                        qtd_enviada = db.get_quantidade_enviada_obra(e['id'], obra_id)
                        if qtd_enviada > 0:
                            incluir = True
                            label = f"{e['descricao']} (Enviado: {qtd_enviada})"
                    
                    if incluir:
                        equip_options[label] = e['id']
                        equipamentos_disponiveis.append(e)
                
                if not equip_options:
                    if tipo == "retorno" and obra_id:
                        st.warning(f"⚠️ Nenhum equipamento foi enviado para esta obra.")
                    else:
                        st.warning(f"⚠️ Nenhum equipamento disponível para {tipo.replace('_', ' ')}.")
                    equipamento_id = None
                    equip_key = None
                else:
                    equip_key = st.selectbox("Equipamento *", options=list(equip_options.keys()))
                    equipamento_id = equip_options[equip_key] if equip_key else None
                
                # Quantidade com validação
                if equipamento_id:
                    if tipo == "envio":
                        max_qtd = db.get_quantidade_disponivel(equipamento_id)
                        if max_qtd <= 0:
                            st.error("⚠️ Nenhuma unidade disponível para envio deste equipamento!")
                            quantidade = 0
                        else:
                            quantidade = st.number_input(f"Quantidade * (Máximo disponível: {max_qtd})", 
                                                       min_value=1, max_value=max_qtd, value=1)
                    elif tipo == "retorno" and obra_id:
                        max_qtd = db.get_quantidade_enviada_obra(equipamento_id, obra_id)
                        if max_qtd <= 0:
                            st.error("⚠️ Nenhuma unidade enviada deste equipamento para esta obra!")
                            quantidade = 0
                        else:
                            quantidade = st.number_input(f"Quantidade * (Máximo enviado: {max_qtd})", 
                                                       min_value=1, max_value=max_qtd, value=1)
                    elif tipo == "manutencao":
                        max_qtd = db.get_quantidade_disponivel(equipamento_id)
                        if max_qtd <= 0:
                            st.error("⚠️ Nenhuma unidade disponível para enviar à manutenção!")
                            quantidade = 0
                        else:
                            quantidade = st.number_input(f"Quantidade * (Máximo disponível: {max_qtd})", 
                                                       min_value=1, max_value=max_qtd, value=1)
                    elif tipo == "retorno_manutencao":
                        max_qtd = db.get_quantidade_em_manutencao(equipamento_id)
                        if max_qtd <= 0:
                            st.error("⚠️ Nenhuma unidade em manutenção para retornar!")
                            quantidade = 0
                        else:
                            quantidade = st.number_input(f"Quantidade * (Máximo em manutenção: {max_qtd})", 
                                                       min_value=1, max_value=max_qtd, value=1)
                    elif tipo == "retorno_perda":
                        max_qtd = db.get_quantidade_perdida(equipamento_id)
                        if max_qtd <= 0:
                            st.error("⚠️ Nenhuma unidade perdida para retornar!")
                            quantidade = 0
                        else:
                            quantidade = st.number_input(f"Quantidade * (Máximo perdido: {max_qtd})", 
                                                       min_value=1, max_value=max_qtd, value=1)
                    else:
                        equip_selecionado = next(e for e in equipamentos if e['id'] == equipamento_id)
                        quantidade = st.number_input("Quantidade *", min_value=1, 
                                                   max_value=equip_selecionado['quantidade'], value=1)
                else:
                    quantidade = st.number_input("Quantidade *", min_value=1, value=1)
                
                # Campo de data com data atual preenchida
                data_movimentacao = st.date_input("Data da Movimentação *", 
                                                 value=datetime.now().date(),
                                                 format="DD/MM/YYYY",
                                                 help="Data em que a movimentação foi realizada")
                
                responsavel = st.text_input("Responsável", placeholder="Nome do responsável pela movimentação")
                observacoes = st.text_area("Observações", placeholder="Informações adicionais...")
                
                if st.form_submit_button("📦 Registrar Movimentação"):
                    if equipamento_id and quantidade > 0:
                        if tipo in ["envio", "retorno"] and not obra_id:
                            st.error("Obra é obrigatória para envios e retornos!")
                        else:
                            # Validar movimentação antes de registrar
                            valido, mensagem = db.validar_movimentacao(tipo, equipamento_id, obra_id, quantidade)
                            
                            if not valido:
                                st.error(f"❌ {mensagem}")
                            else:
                                db.add_movimentacao(tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes, data_movimentacao)
                                st.success("✅ Movimentação registrada com sucesso!")
                                st.rerun()
                    else:
                        st.error("Selecione um equipamento e informe a quantidade!")
            
            st.caption("* Campos obrigatórios")
    
    with tab3:
        st.subheader("📦 Movimentação em Lote")
        st.info("💡 Selecione múltiplos equipamentos para movimentar de uma só vez!")
        
        equipamentos = db.get_equipamentos()
        obras = db.get_obras()
        
        if not equipamentos:
            st.warning("⚠️ É necessário cadastrar equipamentos antes de registrar movimentações.")
        else:
            # Tipo de movimentação
            tipo = st.selectbox("Tipo de Movimentação *", 
                              ["envio", "retorno", "manutencao", "retorno_manutencao", "perda", "retorno_perda"],
                              key="lote_tipo")
            
            # Obra (para retornos, precisa ser selecionada antes dos equipamentos)
            obra_id = None
            if tipo in ["envio", "retorno"]:
                if obras:
                    obra_options = {f"{o['nome']} - {o['cliente_nome'] or 'Cliente N/A'}": o['id'] for o in obras}
                    obra_key = st.selectbox("Obra *", options=list(obra_options.keys()), key="lote_obra")
                    obra_id = obra_options[obra_key] if obra_key else None
                else:
                    st.warning("⚠️ É necessário cadastrar obras para registrar envios/retornos.")
            elif tipo in ["manutencao", "retorno_manutencao", "perda", "retorno_perda"]:
                st.info("ℹ️ Movimentações de manutenção e perda não precisam de obra específica.")

            # Equipamentos disponíveis para seleção múltipla
            equipamentos_disponiveis = []
            
            for e in equipamentos:
                disponivel = db.get_quantidade_disponivel(e['id'])
                em_manutencao = db.get_quantidade_em_manutencao(e['id'])
                
                # Filtrar equipamentos baseado no tipo de movimentação
                incluir = False
                max_qtd = 0
                if tipo in ["envio", "manutencao"] and disponivel > 0:
                    incluir = True
                    max_qtd = disponivel
                    label = f"{e['descricao']} (Disponível: {disponivel})"
                elif tipo == "retorno_manutencao" and em_manutencao > 0:
                    incluir = True
                    max_qtd = em_manutencao
                    label = f"{e['descricao']} (Em Manutenção: {em_manutencao})"
                elif tipo == "perda" and e['quantidade'] > 0:
                    incluir = True
                    max_qtd = e['quantidade']
                    label = f"{e['descricao']} (Total: {e['quantidade']})"
                elif tipo == "retorno_perda":
                    qtd_perdida = db.get_quantidade_perdida(e['id'])
                    if qtd_perdida > 0:
                        incluir = True
                        max_qtd = qtd_perdida
                        label = f"{e['descricao']} (Perdidas: {qtd_perdida})"
                elif tipo == "retorno" and obra_id:
                    qtd_enviada = db.get_quantidade_enviada_obra(e['id'], obra_id)
                    if qtd_enviada > 0:
                        incluir = True
                        max_qtd = qtd_enviada
                        label = f"{e['descricao']} (Enviado: {qtd_enviada})"
                
                if incluir:
                    equipamentos_disponiveis.append({
                        'id': e['id'],
                        'label': label,
                        'descricao': e['descricao'],
                        'max_qtd': max_qtd
                    })
            
            if not equipamentos_disponiveis:
                if tipo == "retorno" and obra_id:
                    st.warning(f"⚠️ Nenhum equipamento foi enviado para esta obra.")
                else:
                    st.warning(f"⚠️ Nenhum equipamento disponível para {tipo.replace('_', ' ')}.")
            else:
                st.markdown("### Selecione os equipamentos e quantidades:")
                
                # Mostrar todos os equipamentos com checkboxes e campos de quantidade
                equipamentos_selecionados = {}
                
                for i, equip in enumerate(equipamentos_disponiveis):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selecionado = st.checkbox(equip['label'], key=f"lote_check_{equip['id']}")
                    
                    with col2:
                        # Sempre mostrar o campo de quantidade, mas desabilitar se não selecionado
                        quantidade = st.number_input(
                            f"Qtd (máx: {equip['max_qtd']})",
                            min_value=1,
                            max_value=equip['max_qtd'],
                            value=1,
                            disabled=not selecionado,
                            key=f"lote_qtd_{equip['id']}"
                        )
                        
                        if selecionado:
                            equipamentos_selecionados[equip['id']] = {
                                'id': equip['id'],
                                'descricao': equip['descricao'],
                                'quantidade': quantidade,
                                'max_qtd': equip['max_qtd']
                            }

                with st.form("movimentacao_lote_form"):
                    # Mostrar resumo dos selecionados
                    if equipamentos_selecionados:
                        st.markdown("### Resumo da seleção:")
                        total_itens = 0
                        for equip_data in equipamentos_selecionados.values():
                            st.write(f"• {equip_data['descricao']}: {equip_data['quantidade']} unidades")
                            total_itens += equip_data['quantidade']
                        st.info(f"📊 Total: {len(equipamentos_selecionados)} equipamentos, {total_itens} itens")
                    else:
                        st.info("👆 Selecione os equipamentos acima")
                    
                    # Converter dict para lista para compatibilidade
                    equipamentos_para_processar = list(equipamentos_selecionados.values())
                    
                    # Campos comuns
                    st.markdown("### Informações da movimentação:")
                    # Campo de data com data atual preenchida
                    data_movimentacao = st.date_input("Data da Movimentação *", 
                                                     value=datetime.now().date(),
                                                     format="DD/MM/YYYY",
                                                     help="Data em que a movimentação foi realizada",
                                                     key="lote_data")
                    
                    responsavel = st.text_input("Responsável", placeholder="Nome do responsável pela movimentação", key="lote_responsavel")
                    observacoes = st.text_area("Observações", placeholder="Informações adicionais...", key="lote_observacoes")
                    
                    if st.form_submit_button("📦 Registrar Movimentações em Lote"):
                        if not equipamentos_para_processar:
                            st.error("⚠️ Selecione pelo menos um equipamento!")
                        elif tipo in ["envio", "retorno"] and not obra_id:
                            st.error("⚠️ Obra é obrigatória para envios e retornos!")
                        else:
                            # Validar e registrar todas as movimentações
                            erros = []
                            sucessos = 0
                            
                            for equip in equipamentos_para_processar:
                                valido, mensagem = db.validar_movimentacao(tipo, equip['id'], obra_id, equip['quantidade'])
                                
                                if not valido:
                                    erros.append(f"{equip['descricao']}: {mensagem}")
                                else:
                                    db.add_movimentacao(tipo, equip['id'], obra_id, equip['quantidade'], responsavel, observacoes, data_movimentacao)
                                    sucessos += 1
                            
                            # Mostrar resultados
                            if sucessos > 0:
                                st.success(f"✅ {sucessos} movimentação(ões) registrada(s) com sucesso!")
                            
                            if erros:
                                st.error("❌ Erros encontrados:")
                                for erro in erros:
                                    st.write(f"- {erro}")
                            
                            if sucessos > 0:
                                st.rerun()
                
                st.caption("* Campos obrigatórios")
