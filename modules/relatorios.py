import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date

def show_relatorios_page(db, contexto=None):
    st.title("📊 Relatórios e Análises")
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Executivo", "Relatório de Equipamentos", 
                                      "Relatório de Movimentações", "Perdas e Manutenções"])
    
    with tab1:
        st.subheader("📈 Dashboard Executivo")
        
        # Período de análise
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início:", value=date.today() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data Fim:", value=date.today())
        
        # KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_equipamentos = db.get_total_equipamentos()
            st.metric("Total de Equipamentos", total_equipamentos)
        
        with col2:
            total_clientes = db.get_total_clientes()
            st.metric("Clientes Ativos", total_clientes)
        
        with col3:
            obras_ativas = len([o for o in db.get_obras() if o['status'] == 'ativa'])
            st.metric("Obras Ativas", obras_ativas)
        
        with col4:
            movimentacoes = db.get_movimentacoes()
            movimentacoes_periodo = [m for m in movimentacoes 
                                   if data_inicio <= pd.to_datetime(m['data_movimentacao']).date() <= data_fim]
            st.metric("Movimentações (Período)", len(movimentacoes_periodo))
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status dos Equipamentos")
            status_data = db.get_equipamentos_status_summary()
            if status_data:
                df_status = pd.DataFrame(status_data)
                fig = px.pie(df_status, values='quantidade', names='status', 
                           title="Distribuição por Status",
                           color_discrete_map={
                               'disponivel': '#28a745',
                               'enviado': '#007bff', 
                               'manutencao': '#ffc107',
                               'perdido': '#dc3545'
                           })
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados para exibir")
        
        with col2:
            st.subheader("Movimentações por Tipo")
            if movimentacoes_periodo:
                df_mov = pd.DataFrame(movimentacoes_periodo)
                mov_por_tipo = df_mov.groupby('tipo').size().reset_index(name='quantidade')
                fig = px.bar(mov_por_tipo, x='tipo', y='quantidade', 
                           title="Movimentações por Tipo (Período)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem movimentações no período")
        
        # Timeline de movimentações
        st.subheader("Timeline de Movimentações")
        if movimentacoes_periodo:
            df_timeline = pd.DataFrame(movimentacoes_periodo)
            df_timeline['data'] = pd.to_datetime(df_timeline['data_movimentacao']).dt.date
            timeline_data = df_timeline.groupby(['data', 'tipo']).size().reset_index(name='quantidade')
            
            fig = px.line(timeline_data, x='data', y='quantidade', color='tipo',
                         title="Movimentações ao Longo do Tempo")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para timeline")
    
    with tab2:
        st.subheader("📦 Relatório de Equipamentos")
        
        equipamentos = db.get_equipamentos()
        
        if equipamentos:
            df_equipamentos = pd.DataFrame(equipamentos)
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.multiselect("Status:", 
                                             ["disponivel", "enviado", "manutencao", "perdido"],
                                             default=["disponivel", "enviado", "manutencao", "perdido"])
            with col2:
                search_equip = st.text_input("Buscar equipamento:")
            with col3:
                ordenar_por = st.selectbox("Ordenar por:", ["Descrição", "Quantidade", "Status"])
            
            # Aplicar filtros
            df_filtered = df_equipamentos[df_equipamentos['status'].isin(status_filter)]
            
            if search_equip:
                df_filtered = df_filtered[df_filtered['descricao'].str.contains(search_equip, case=False, na=False)]
            
            # Ordenação
            if ordenar_por == "Descrição":
                df_filtered = df_filtered.sort_values('descricao')
            elif ordenar_por == "Quantidade":
                df_filtered = df_filtered.sort_values('quantidade', ascending=False)
            else:
                df_filtered = df_filtered.sort_values('status')
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tipos de Equipamentos", len(df_filtered))
            with col2:
                st.metric("Quantidade Total", df_filtered['quantidade'].sum())
            with col3:
                valor_total = len(df_filtered) * 1000  # Estimativa
                st.metric("Valor Estimado (R$)", f"{valor_total:,.2f}")
            
            # Tabela detalhada
            st.subheader("Equipamentos Detalhados")
            
            # Preparar dados para exibição
            df_display = df_filtered.copy()
            df_display['Status'] = df_display['status'].map({
                'disponivel': '🟢 Disponível',
                'enviado': '🔵 Enviado',
                'manutencao': '🟡 Manutenção',
                'perdido': '🔴 Perdido'
            })
            
            # Seleção de colunas para exibir
            colunas_exibir = st.multiselect("Colunas:", 
                                          ['descricao', 'codigo', 'medida', 'quantidade', 'Status', 'observacoes'],
                                          default=['descricao', 'quantidade', 'Status'])
            
            if colunas_exibir:
                st.dataframe(df_display[colunas_exibir], use_container_width=True)
            
            # Download CSV
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Baixar Relatório CSV",
                data=csv,
                file_name=f"relatorio_equipamentos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("Nenhum equipamento cadastrado.")
    
    with tab3:
        st.subheader("📋 Relatório de Movimentações")
        
        movimentacoes = db.get_movimentacoes()
        
        if movimentacoes:
            df_mov = pd.DataFrame(movimentacoes)
            df_mov['data_movimentacao'] = pd.to_datetime(df_mov['data_movimentacao'])
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                tipos_mov = st.multiselect("Tipos:", 
                                         ["envio", "retorno", "manutencao", "retorno_manutencao", "perda", "retorno_perda"],
                                         default=["envio", "retorno", "manutencao", "retorno_manutencao", "perda", "retorno_perda"])
            with col2:
                data_inicio_mov = st.date_input("Data Início:", 
                                              value=date.today() - timedelta(days=30),
                                              key="mov_inicio")
            with col3:
                data_fim_mov = st.date_input("Data Fim:", value=date.today(), key="mov_fim")
            
            # Aplicar filtros
            df_mov_filtered = df_mov[
                (df_mov['tipo'].isin(tipos_mov)) &
                (df_mov['data_movimentacao'].dt.date >= data_inicio_mov) &
                (df_mov['data_movimentacao'].dt.date <= data_fim_mov)
            ]
            
            # Estatísticas do período
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                envios = len(df_mov_filtered[df_mov_filtered['tipo'] == 'envio'])
                st.metric("Envios", envios)
            with col2:
                retornos = len(df_mov_filtered[df_mov_filtered['tipo'] == 'retorno'])
                st.metric("Retornos", retornos)
            with col3:
                manutencoes = len(df_mov_filtered[df_mov_filtered['tipo'] == 'manutencao'])
                st.metric("Manutenções", manutencoes)
            with col4:
                perdas = len(df_mov_filtered[df_mov_filtered['tipo'] == 'perda'])
                st.metric("Perdas", perdas)
            
            # Gráfico de movimentações por dia
            st.subheader("Movimentações Diárias")
            df_mov_filtered['data'] = df_mov_filtered['data_movimentacao'].dt.date
            mov_diarias = df_mov_filtered.groupby(['data', 'tipo']).size().reset_index(name='quantidade')
            
            fig = px.bar(mov_diarias, x='data', y='quantidade', color='tipo',
                        title="Movimentações por Dia e Tipo")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de movimentações
            st.subheader("Movimentações Detalhadas")
            df_display_mov = df_mov_filtered.copy()
            df_display_mov['Data'] = df_display_mov['data_movimentacao'].dt.strftime('%d/%m/%Y %H:%M')
            df_display_mov['Tipo'] = df_display_mov['tipo'].map({
                'envio': '📤 Envio',
                'retorno': '📥 Retorno',
                'manutencao': '🔧 Manutenção',
                'retorno_manutencao': '🔧✅ Retorno Manutenção',
                'perda': '❌ Perda',
                'retorno_perda': '🔄 Retorno Perda'
            })
            
            colunas_mov = ['Data', 'Tipo', 'equipamento_descricao', 'obra_nome', 'quantidade', 'responsavel']
            st.dataframe(df_display_mov[colunas_mov], use_container_width=True)
            
            # Download
            csv_mov = df_mov_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Baixar Relatório de Movimentações CSV",
                data=csv_mov,
                file_name=f"relatorio_movimentacoes_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("Nenhuma movimentação registrada.")
    
    with tab4:
        st.subheader("⚠️ Perdas e Manutenções")
        
        # Equipamentos em manutenção
        equipamentos_manutencao = db.get_equipamentos_by_status("manutencao")
        equipamentos_perdidos = db.get_equipamentos_by_status("perdido")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🔧 Equipamentos em Manutenção")
            if equipamentos_manutencao:
                for equip in equipamentos_manutencao:
                    st.write(f"- **{equip['descricao']}** (Qtd: {equip['quantidade']})")
                    if equip['observacoes']:
                        st.caption(f"  Obs: {equip['observacoes']}")
            else:
                st.info("Nenhum equipamento em manutenção")
        
        with col2:
            st.write("### ❌ Equipamentos Perdidos")
            if equipamentos_perdidos:
                for equip in equipamentos_perdidos:
                    st.write(f"- **{equip['descricao']}** (Qtd: {equip['quantidade']})")
                    if equip['observacoes']:
                        st.caption(f"  Obs: {equip['observacoes']}")
            else:
                st.info("Nenhum equipamento perdido")
        
        # Histórico de manutenções
        st.write("### 📋 Histórico de Manutenções")
        manutencoes = db.get_manutencoes()
        
        if manutencoes:
            df_manut = pd.DataFrame(manutencoes)
            df_manut['data_manutencao'] = pd.to_datetime(df_manut['data_manutencao'])
            
            # Filtro por período
            col1, col2 = st.columns(2)
            with col1:
                data_inicio_manut = st.date_input("Data Início:", 
                                                value=date.today() - timedelta(days=90),
                                                key="manut_inicio")
            with col2:
                data_fim_manut = st.date_input("Data Fim:", value=date.today(), key="manut_fim")
            
            # Filtrar por período
            df_manut_filtered = df_manut[
                (df_manut['data_manutencao'].dt.date >= data_inicio_manut) &
                (df_manut['data_manutencao'].dt.date <= data_fim_manut)
            ]
            
            # Estatísticas de manutenção
            col1, col2, col3 = st.columns(3)
            with col1:
                total_manut = len(df_manut_filtered)
                st.metric("Total de Manutenções", total_manut)
            with col2:
                custo_total = df_manut_filtered['custo'].sum() if 'custo' in df_manut_filtered.columns else 0
                st.metric("Custo Total (R$)", f"{custo_total:,.2f}")
            with col3:
                manut_pendentes = len(df_manut_filtered[df_manut_filtered['status'] == 'pendente'])
                st.metric("Pendentes", manut_pendentes)
            
            # Tabela de manutenções
            if not df_manut_filtered.empty:
                df_display_manut = df_manut_filtered.copy()
                df_display_manut['Data'] = df_display_manut['data_manutencao'].dt.strftime('%d/%m/%Y')
                df_display_manut['Status'] = df_display_manut['status'].map({
                    'pendente': '🟡 Pendente',
                    'em_andamento': '🔵 Em Andamento',
                    'concluida': '🟢 Concluída'
                })
                
                colunas_manut = ['Data', 'equipamento_descricao', 'tipo', 'Status', 'responsavel', 'custo']
                st.dataframe(df_display_manut[colunas_manut], use_container_width=True)
            
        else:
            st.info("Nenhuma manutenção registrada.")
        
        # Análise de perdas por período
        st.write("### 📊 Análise de Perdas")
        movimentacoes_perda = [m for m in db.get_movimentacoes() if m['tipo'] == 'perda']
        
        if movimentacoes_perda:
            df_perdas = pd.DataFrame(movimentacoes_perda)
            df_perdas['data_movimentacao'] = pd.to_datetime(df_perdas['data_movimentacao'])
            df_perdas['mes'] = df_perdas['data_movimentacao'].dt.to_period('M')
            
            perdas_por_mes = df_perdas.groupby('mes')['quantidade'].sum().reset_index()
            perdas_por_mes['mes'] = perdas_por_mes['mes'].astype(str)
            
            fig = px.bar(perdas_por_mes, x='mes', y='quantidade',
                        title="Perdas por Mês")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Nenhuma perda registrada.")
