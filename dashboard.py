import streamlit as st
import pandas as pd
from datetime import date
import sys
import os
import time

# Adiciona path para importar modulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.supabase_client import get_supabase_client
from src.main import run_market_scan, is_cron_active

# Configuração da Página
st.set_page_config(page_title="Trading Bot B3", page_icon="📈", layout="wide")

# Conexão com Banco
@st.cache_resource
def init_db():
    return get_supabase_client()

supabase = init_db()

# --- SIDEBAR ---
st.sidebar.title("🤖 Bot HiLo")
page = st.sidebar.radio("Navegação", ["Carteira", "Sinais do Dia", "Controle do Robô", "Configurações"])

# --- PÁGINA: CARTEIRA (PORTFOLIO) ---
if page == "Carteira":
    st.title("💰 Minha Carteira de Opções")
    
    # Form de Nova Operação
    with st.expander("➕ Nova Operação", expanded=False):
        with st.form("new_trade_form"):
            col1, col2, col3 = st.columns(3)
            ticker_opt = col1.text_input("CÓDIGO (ex: PETRM333)").upper().strip()
            ticker_asset = col2.text_input("Ativo Base (ex: PETR4)").upper().strip()
            # Nomenclatura ajustada
            structure_opt = col3.selectbox("ESTRUTURA", ["COMPRA DE CALL", "COMPRA DE PUT", "VENDA DE CALL", "VENDA DE PUT"])
            
            col4, col5 = st.columns(2)
            # 'Pago' é o preço unitário de entrada
            price_paid = col4.number_input("PAGO (Unitário R$)", min_value=0.0, format="%.2f")
            qty = col5.number_input("Quantidade", min_value=100, step=100, help="Usado apenas para controle de volume, não afeta o cálculo de %")
            
            start_date = st.date_input("DATA INICIO", date.today(), format="DD/MM/YYYY")
            expiration = st.date_input("Vencimento Opção", format="DD/MM/YYYY")
            
            submitted = st.form_submit_button("💾 Salvar Operação")
            
            if submitted:
                data = {
                    "ticker_asset": ticker_asset,
                    "ticker_option": ticker_opt,
                    "type": structure_opt,
                    "entry_date": str(start_date),
                    "entry_price": price_paid,
                    "quantity": qty,
                    "expiration_date": str(expiration),
                    "status": "Aberta"
                }
                try:
                    supabase.table("portfolio").insert(data).execute()
                    st.success("Operação registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # Tabela de Operações
    st.subheader("Custódia")
    
    try:
        # Carrega dados
        response = supabase.table("portfolio").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # Filtrar operações abertas para uso posterior (Simulador e Encerramento)
            abertas = df[df['status'] == 'Aberta']

            # --- FILTROS ---
            with st.expander("🔍 Filtros", expanded=False):
                col_f1, col_f2, col_f3 = st.columns(3)
                
                # Filtro Ativo
                all_assets = df['ticker_asset'].unique().tolist()
                sel_assets = col_f1.multiselect("Filtrar por Ativo", all_assets)
                
                # Filtro Status
                all_status = df['status'].unique().tolist()
                sel_status = col_f2.multiselect("Filtrar por Status", all_status)
                
                # Filtro Resultado
                filter_profit = col_f3.radio("Filtrar Resultado", ["Todos", "Apenas Lucro 🟢", "Apenas Prejuízo 🔴"], horizontal=True)

            # Aplicar Filtros
            df_filtered = df.copy()
            
            if sel_assets:
                df_filtered = df_filtered[df_filtered['ticker_asset'].isin(sel_assets)]
            
            if sel_status:
                df_filtered = df_filtered[df_filtered['status'].isin(sel_status)]
                
            if filter_profit == "Apenas Lucro 🟢":
                df_filtered = df_filtered[df_filtered['result_percent'] > 0]
            elif filter_profit == "Apenas Prejuízo 🔴":
                df_filtered = df_filtered[df_filtered['result_percent'] < 0]

            # --- PROCESSAMENTO PARA EXIBIÇÃO ---
            display_data = []
            
            # Acumuladores para o Rodapé
            total_investido = 0.0
            total_retornado = 0.0
            total_resultado = 0.0
            
            for index, row in df_filtered.iterrows():
                # Datas
                d_inicio = pd.to_datetime(row['entry_date']).date()
                d_final = pd.to_datetime(row['exit_date']).date() if row['exit_date'] else None
                
                # Calculo Financeiro da Linha
                investido_linha = (row['entry_price'] or 0) * (row['quantity'] or 0)
                retornado_linha = (row['exit_price'] or 0) * (row['quantity'] or 0) # Se estiver aberta, exit_price é None/0
                
                res_val_db = row.get('result_value')
                resultado_linha = float(res_val_db) if res_val_db is not None else 0.0
                
                total_investido += investido_linha
                if row['status'] == 'Encerrada':
                    total_retornado += retornado_linha
                    total_resultado += resultado_linha
                
                # Dias
                dias = (d_final - d_inicio).days if d_final else None
                
                # Resultado %
                pct_res = row.get('result_percent')
                if pct_res is not None:
                     res_str = f"{pct_res:.2f}%"
                else:
                     res_str = "-"

                # Sucesso (Sim/Não)
                sucesso = ""
                if row['status'] == 'Encerrada' and pct_res is not None:
                    sucesso = "Sim" if pct_res > 0 else "Não"

                display_data.append({
                    "CÓDIGO": row['ticker_option'],
                    "ATIVO": row['ticker_asset'],
                    "ESTRUTURA": row['type'],
                    "QUANTIDADE": row['quantity'],
                    "DATA INICIO": d_inicio.strftime('%d/%m/%Y'),
                    "DATA SAÍDA": d_final.strftime('%d/%m/%Y') if d_final else "-",
                    "DIAS": dias if dias is not None else "-",
                    "PREÇO SAÍDA": f"R$ {row['exit_price']:.2f}" if row['exit_price'] else "-",
                    "PREÇO ENTRADA": f"R$ {row['entry_price']:.2f}",
                    "RESULTADO": res_str,
                    "SUCESSO": sucesso,
                    "STATUS": row['status']
                })
            
            df_view = pd.DataFrame(display_data)
            
            # Função de Estilo
            def color_sucesso(val):
                color = '#28a745' if val == 'Sim' else '#dc3545' if val == 'Não' else ''
                font_weight = 'bold' if val in ['Sim', 'Não'] else 'normal'
                return f'color: {color}; font_weight: {font_weight}'

            # Mostra Tabela principal com Estilo
            if not df_view.empty:
                st.dataframe(
                    df_view.style.map(color_sucesso, subset=['SUCESSO']), 
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- RODAPÉ ACUMULADO ---
                st.info(
                    f"💰 **RESUMO DA SELEÇÃO** | "
                    f"Investido: **R$ {total_investido:.2f}** | "
                    f"Retornado (Encerradas): **R$ {total_retornado:.2f}** | "
                    f"Resultado Líquido: **R$ {total_resultado:.2f}**"
                )
            else:
                st.warning("Nenhum registro encontrado com os filtros selecionados.")
            
            st.divider()

            # --- SIMULADOR DE CENÁRIOS ---
            st.subheader("🔮 Simulador de Saída")
            with st.expander("Simular Resultado (Sem salvar)", expanded=True):
                if not abertas.empty:
                    # Seleção para simulação
                    sim_opcoes = abertas.apply(lambda x: f"{x['ticker_option']} (Pago: R$ {x['entry_price']:.2f})", axis=1).tolist()
                    sim_selection = st.selectbox("Selecione para Simular:", options=sim_opcoes)
                    
                    if sim_selection:
                        # Recuperar dados originais
                        sim_ticker = sim_selection.split(" ")[0]
                        sim_data = abertas[abertas['ticker_option'] == sim_ticker].iloc[0]
                        
                        entry_val = float(sim_data['entry_price'])
                        qty_val = int(sim_data['quantity'])
                        
                        target_100 = entry_val * 2
                        
                        col_sim1, col_sim2, col_sim3 = st.columns(3)
                        sim_price = col_sim1.number_input("Preço de Saída Simulado (R$)", value=entry_val, step=0.01, format="%.2f")
                        
                        # Cálculos em tempo real
                        lucro_unit = sim_price - entry_val
                        lucro_total = lucro_unit * qty_val
                        lucro_pct = (lucro_unit / entry_val * 100) if entry_val > 0 else 0
                        
                        # Exibição Visual
                        col_sim2.metric("Resultado Estimado %", f"{lucro_pct:.2f}%", delta=f"{lucro_pct:.2f}%")
                        col_sim3.metric("Lucro/Prejuízo Financeiro", f"R$ {lucro_total:.2f}")
                        
                        st.caption(f"ℹ️ Para dobrar o capital (100%), você precisa vender a **R$ {target_100:.2f}**")
                        
                        if lucro_pct >= 100:
                            st.success("🚀 Cenário de META BATIDA!")
                        elif lucro_pct < 0:
                            st.error("📉 Cenário de Prejuízo.")
                            
                else:
                    st.info("Sem operações abertas para simular.")

            st.write("---")
            
            # --- ÁREA DE GESTÃO DE OPERAÇÕES ---
            st.divider()
            st.subheader("🛠️ Gestão de Operações")
            
            tab_close, tab_edit, tab_del = st.tabs(["📉 Encerrar (Baixar)", "✏️ Editar", "🗑️ Excluir"])
            
            # --- ABA 1: ENCERRAR (Logica Original) ---
            with tab_close:
                if not abertas.empty:
                    map_opts_close = {
                        f"{row['ticker_option']} ({row['type']}) | Início: {pd.to_datetime(row['entry_date']).strftime('%d/%m/%Y')} | Qtd: {row['quantity']}": row['id']
                        for idx, row in abertas.iterrows()
                    }
                    sel_label_close = st.selectbox("Selecione para Baixar:", options=list(map_opts_close.keys()), key="sel_close")
                    
                    if sel_label_close:
                        id_close = map_opts_close[sel_label_close]
                        trade_data_c = df[df['id'] == id_close].iloc[0]
                        
                        with st.form("close_trade_form"):
                            col_c1, col_c2 = st.columns(2)
                            close_date = col_c1.date_input("DATA DE SAÍDA", date.today(), format="DD/MM/YYYY")
                            price_received = col_c2.number_input("PREÇO DE SAÍDA (R$)", min_value=0.0, format="%.2f")
                            
                            if st.form_submit_button("✅ Confirmar Encerramento"):
                                entry_p = float(trade_data_c['entry_price'])
                                res_pct = ((price_received - entry_p) / entry_p * 100) if entry_p > 0 else 0.0
                                res_val = (price_received - entry_p) * trade_data_c['quantity']
                                
                                up_dict = {
                                    "exit_date": str(close_date),
                                    "exit_price": price_received,
                                    "result_percent": res_pct,
                                    "result_value": res_val,
                                    "status": "Encerrada"
                                }
                                supabase.table("portfolio").update(up_dict).eq("id", id_close).execute()
                                st.toast("Encerrado com sucesso!", icon="📉")
                                time.sleep(1.0)
                                st.rerun()
                else:
                    st.info("Nada em aberto para baixar.")

            # --- ABA 2: EDITAR ---
            with tab_edit:
                if not df.empty:
                    # Mapeamento Amigável sem ID exposto
                    map_opts_edit = {
                        f"{row['ticker_option']} ({row['status']}) | Início: {pd.to_datetime(row['entry_date']).strftime('%d/%m/%Y')} | Qtd: {row['quantity']}": row['id']
                        for idx, row in df.iterrows()
                    }
                    sel_label_edit = st.selectbox("Selecione para Corrigir:", options=list(map_opts_edit.keys()), key="sel_edit")
                    
                    if sel_label_edit:
                        id_edit = map_opts_edit[sel_label_edit]
                        curr_data = df[df['id'] == id_edit].iloc[0]
                        
                        with st.form("edit_trade_form"):
                            st.markdown(f"#### 📝 Editando: {curr_data['ticker_option']}")
                            
                            # --- BLOCO 1: IDENTIFICAÇÃO ---
                            st.caption("Identificação da Operação")
                            c1, c2, c3, c4 = st.columns(4)
                            new_asset = c1.text_input("Ativo Base", value=curr_data['ticker_asset'])
                            new_ticker = c2.text_input("Cód. Opção", value=curr_data['ticker_option'])
                            new_type = c3.selectbox("Estrutura", ["COMPRA DE CALL", "COMPRA DE PUT", "VENDA DE CALL", "VENDA DE PUT"], index=["COMPRA DE CALL", "COMPRA DE PUT", "VENDA DE CALL", "VENDA DE PUT"].index(curr_data['type']) if curr_data['type'] in ["COMPRA DE CALL", "COMPRA DE PUT", "VENDA DE CALL", "VENDA DE PUT"] else 0)
                            
                            try:
                                exp_val = pd.to_datetime(curr_data['expiration_date']).date()
                            except:
                                exp_val = date.today()
                            new_exp = c4.date_input("Vencimento", value=exp_val, format="DD/MM/YYYY")

                            st.divider()

                            # --- BLOCO 2: DADOS DE ENTRADA ---
                            st.caption("Dados de Entrada")
                            c5, c6, c7 = st.columns(3)
                            new_date = c5.date_input("Data Início", pd.to_datetime(curr_data['entry_date']).date(), format="DD/MM/YYYY")
                            new_price = c6.number_input("Preço Entrada (R$)", value=float(curr_data['entry_price']), format="%.2f", step=0.01)
                            new_qty = c7.number_input("Quantidade", value=int(curr_data['quantity']), step=100)
                            
                            st.divider()

                            # --- BLOCO 3: DADOS DE SAÍDA (Apenas se já houver ou quiser adicionar) ---
                            st.caption("Dados de Saída (Opcional/Correção)")
                            c8, c9 = st.columns(2)
                            
                            # Tratamento para valores nulos de saída
                            try:
                                out_date_val = pd.to_datetime(curr_data['exit_date']).date() if curr_data['exit_date'] else None
                            except:
                                out_date_val = None
                            
                            new_exit_date = c8.date_input("Data Saída", value=out_date_val, format="DD/MM/YYYY") if out_date_val else c8.date_input("Data Saída", value=None, format="DD/MM/YYYY")
                            
                            curr_exit_price = float(curr_data['exit_price']) if curr_data['exit_price'] else 0.0
                            new_exit_price = c9.number_input("Preço Saída (R$)", value=curr_exit_price, format="%.2f", step=0.01)

                            if st.form_submit_button("💾 Salvar Alterações Completas"):
                                # Lógica de Update Inteligente
                                up_edit = {
                                    "ticker_asset": new_asset.upper(),
                                    "ticker_option": new_ticker.upper(),
                                    "type": new_type,
                                    "expiration_date": str(new_exp),
                                    "entry_date": str(new_date),
                                    "entry_price": new_price,
                                    "quantity": new_qty
                                }
                                
                                # Se houve edição nos dados de saída, vamos recalcular o resultado
                                if new_exit_price > 0:
                                    # Recalcula Resultados
                                    if new_price > 0:
                                        res_pct = ((new_exit_price - new_price) / new_price * 100)
                                    else:
                                        res_pct = 0.0
                                    
                                    res_val = (new_exit_price - new_price) * new_qty
                                    
                                    up_edit.update({
                                        "exit_price": new_exit_price,
                                        "exit_date": str(new_exit_date) if new_exit_date else str(date.today()),
                                        "result_percent": res_pct,
                                        "result_value": res_val,
                                        "status": "Encerrada"
                                    })

                                supabase.table("portfolio").update(up_edit).eq("id", id_edit).execute()
                                
                                st.toast(f"✅ Registro de {new_ticker} atualizado com sucesso!", icon="💾")
                                time.sleep(1.5)
                                st.rerun()
                else:
                    st.info("Carteira vazia.")

            # --- ABA 3: EXCLUIR ---
            with tab_del:
                if not df.empty:
                    sel_label_del = st.selectbox("Selecione para Excluir DEFINITIVAMENTE:", options=list(map_opts_edit.keys()), key="sel_del")
                    
                    if sel_label_del:
                        st.error(f"⚠️ Você tem certeza que deseja apagar **{sel_label_del}**?")
                        st.caption("Essa ação não pode ser desfeita.")
                        
                        if st.button("🗑️ Sim, apagar registro", type="primary"):
                            id_del = map_opts_edit[sel_label_del]
                            supabase.table("portfolio").delete().eq("id", id_del).execute()
                            st.success("Registro apagado.")
                            st.rerun()
                
        else:
            st.info("Nenhuma operação registrada na carteira.")
            
    except Exception as e:
        st.error(f"Erro ao carregar carteira: {e}")


# --- PÁGINA: SINAIS DO DIA ---
elif page == "Sinais do Dia":
    st.title("📡 Sinais do Robô")
    selected_date = st.date_input("Data do Sinal", date.today(), format="DD/MM/YYYY")
    
    response = supabase.table("signals")\
        .select("*, option_opportunities(*) ")\
        .eq("signal_date", str(selected_date))\
        .execute()
    
    data = response.data
    
    if data:
        for s in data:
            # Correção: O campo no banco é 'direction' e não 'signal'
            direction_label = s.get('direction', 'N/A')
            price_val = float(s.get('price_at_signal', 0.0))
            
            with st.expander(f"{s['ticker']} - {direction_label} (R$ {price_val:.2f})"):
                op_raw = s.get('option_opportunities')
                
                # Tratamento robusto: se for lista, pega o primeiro item. Se for dict, usa direto.
                op = None
                if isinstance(op_raw, list) and len(op_raw) > 0:
                    op = op_raw[0]
                elif isinstance(op_raw, dict):
                    op = op_raw
                    
                if op:
                    st.write(f"**Opção Sugerida:** {op.get('ticker_option')}")
                    st.write(f"**Strike:** {op.get('strike')}")
                    st.write(f"**Vencimento:** {op.get('expiration_date')}")
                    
                    # Botão de Reenvio Manual
                    if st.button("📲 Reenviar WhatsApp", key=f"resend_{s['id']}"):
                        from src.services.notification_service import NotificationService
                        svc = NotificationService()
                        
                        # Reconstruir objeto option_data
                        opt_data_resend = {
                            "ticker": op.get('ticker_option'),
                            "strike": op.get('strike'),
                            "last_price": op.get('premium_at_signal', 0.0),
                            "dte": op.get('days_to_expire'),
                            "trades": 0 
                        }
                        
                        # Passamos 'direction_label' como signal
                        svc.send_signal_message(s['ticker'], direction_label, opt_data_resend)
                        st.toast("Mensagem reenviada!")

                else:
                    st.warning("Dados da opção não encontrados.")
    else:
        st.info("Nenhum sinal registrado para esta data.")

# --- PÁGINA: CONTROLE DO ROBÔ ---
elif page == "Controle do Robô":
    st.title("🎛️ Controle e Status")
    
    # Carregar Status Real do JSON
    import json
    CONFIG_FILE = "user_config.json"
    
    def load_config_status():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {"cron_active": True, "hilo_period": 10} 
    
    config_now = load_config_status()
    # Usa o valor do json ou True se não existir
    is_active = config_now.get("cron_active", True)

    # Status e Controle
    st.subheader("Status do Sistema")
    col_status, col_btn = st.columns([1, 3])
    
    status_msg = "ATIVO" if is_active else "PAUSADO"
    status_color = "green" if is_active else "red"
    
    col_status.markdown(f"### :{status_color}[{status_msg}]")
    
    # Toggle de Controle
    new_status = col_btn.toggle("Ativar Agendamento Automático", value=is_active)
    
    if new_status != is_active:
        config_now["cron_active"] = new_status
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_now, f)
        st.toast(f"Status alterado para: {'Ativo' if new_status else 'Pausado'}")
        time.sleep(1)
        st.rerun()
    
    st.divider()
    
    # Execução Manual
    st.subheader("Execução Manual")
    col_exec1, col_exec2 = st.columns(2)
    
    with col_exec1:
        if st.button("🚀 Rodar Análise Completa Agora", type="primary"):
            with st.spinner("Executando scanner de mercado..."):
                try:
                    # Captura logs
                    import io
                    from contextlib import redirect_stdout
                    f = io.StringIO()
                    with redirect_stdout(f):
                        run_market_scan()
                    output = f.getvalue()
                    
                    st.success("Análise concluída!")
                    with st.expander("Ver Logs da Execução"):
                        st.code(output)
                        
                except Exception as e:
                    st.error(f"Erro na execução: {e}")

    with col_exec2:
         # Input para testar ticker específico
         ticker_test = st.text_input("Testar Ticker Específico (ex: PETR4)")
         if st.button("🔎 Analisar Ticker"):
             if ticker_test:
                 with st.spinner(f"Analisando {ticker_test}..."):
                    try:
                        import io
                        from contextlib import redirect_stdout
                        f = io.StringIO()
                        with redirect_stdout(f):
                             # Pequena gambiarra para rodar só um ticker: 
                             # Instancia o scanner e roda analyze_asset direto
                             from src.core.scanner import MarketScanner
                             scanner = MarketScanner()
                             scanner.analyze_asset(ticker_test.upper(), force_notification=True)
                        
                        output = f.getvalue()
                        st.success(f"Análise de {ticker_test} finalizada!")
                        with st.expander("Logs"):
                            st.code(output)
                    except Exception as e:
                        err_msg = str(e)
                        if "404" in err_msg or "Not Found" in err_msg:
                            st.warning(f"⚠️ O ativo **{ticker_test}** não foi encontrado. Verifique se o código está correto (ex: use PETR4, VALE3).")
                        else:
                            st.error(f"❌ Não foi possível analisar o ativo. Erro técnico: {err_msg}")

    st.divider()

    # Gestão de Ativos Monitorados
    st.subheader("📋 Ativos Monitorados")
    try:
        assets_response = supabase.table("assets").select("*").order("ticker").execute()
        assets_df = pd.DataFrame(assets_response.data)
        
        if not assets_df.empty:
            # Formatar Data
            if 'created_at' in assets_df.columns:
                assets_df['created_at'] = pd.to_datetime(assets_df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Selecionar e Renomear Colunas
            display_cols = {
                'ticker': 'Ativo',
                'name': 'Nome',
                'sector': 'Setor',
                'created_at': 'Data Cadastro'
            }
            # Filtra apenas colunas que existem no DF
            cols_to_show = [c for c in display_cols.keys() if c in assets_df.columns]
            
            df_show = assets_df[cols_to_show].rename(columns=display_cols)

            col_list, col_add = st.columns([2, 1])
            
            with col_list:
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                
                # Remover Ativo
                asset_to_remove = st.selectbox("Remover Ativo", assets_df['ticker'].tolist())
                if st.button("🗑️ Remover"):
                    try:
                        # 1. Buscar IDs dos sinais para remover dependências (Netos: option_opportunities)
                        sigs = supabase.table("signals").select("id").eq("ticker", asset_to_remove).execute()
                        sig_ids = [s['id'] for s in sigs.data]
                        
                        if sig_ids:
                            # 2. Remover Oportunidades (Netos)
                            # Supabase-py não suporta .in_ diretamente de forma simples as vezes, vamos iterar ou usar filtro
                            # Tentando delete em massa se possível, senão loop
                            for sid in sig_ids:
                                supabase.table("option_opportunities").delete().eq("signal_id", sid).execute()
                            
                            # 3. Remover Sinais (Filhos)
                            supabase.table("signals").delete().eq("ticker", asset_to_remove).execute()
                        
                        # 4. Remover Ativo (Pai)
                        supabase.table("assets").delete().eq("ticker", asset_to_remove).execute()
                        
                        st.success(f"{asset_to_remove} removido completamente (sinais e histórico limpos).")
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                         st.error(f"Erro ao remover ativo: {e}")

        else:
             st.info("Nenhum ativo monitorado no momento.")
             col_list, col_add = st.columns([2, 1])

        with col_add:
            st.write("**Adicionar Novo**")
            new_ticker = st.text_input("Ticker (ex: VALE3)").upper()
            if st.button("➕ Adicionar"):
                if new_ticker:
                    try:
                        # Busca info extra
                        from src.services.brapi import BrapiClient
                        client = BrapiClient()
                        details = client.get_ticker_details(new_ticker)
                        
                        payload = {
                            "ticker": new_ticker,
                            "name": details.get('longName'),
                            "sector": details.get('sector')
                        }
                        
                        supabase.table("assets").insert(payload).execute()
                        st.success(f"{new_ticker} adicionado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    except Exception as e:
        st.error(f"Erro ao carregar ativos: {e}")

# --- PÁGINA: CONFIGURAÇÕES ---
elif page == "Configurações":
    st.title("⚙️ Configurações")
    
    # Simple Local Config Persistence (JSON)
    import json
    CONFIG_FILE = "user_config.json"
    
    def load_config():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {"hilo_period": 10, "profit_target": 50.0, "phone": ""}

    def save_config(cfg):
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f)

    curr_config = load_config()

    with st.form("settings_form"):
        st.subheader("Parâmetros do Robô")
        
        # HiLo Section
        st.caption("Análise Técnica")
        new_hilo = st.number_input("Período do HiLo (Padrão: 10)", value=int(curr_config.get("hilo_period", 10)), min_value=1)
        
        st.divider()
        
        # Alerts Section
        st.caption("Alertas e Notificações")
        new_target = st.number_input("Meta de Lucro para Aviso (%)", value=float(curr_config.get("profit_target", 50.0)), step=5.0)
        new_phone = st.text_input("Número WhatsApp (com DDD)", value=curr_config.get("phone", ""), placeholder="5511999999999")
        
        st.caption("Esses dados serão usados para filtrar oportunidades e enviar mensagens.")
        
        if st.form_submit_button("💾 Salvar Configurações"):
            new_cfg = {
                "hilo_period": new_hilo,
                "profit_target": new_target,
                "phone": new_phone
            }
            save_config(new_cfg)
            st.toast("✅ Configurações salvas!", icon="⚙️")
            time.sleep(1)
            st.rerun()

