current_symbol_code = st.session_state.get('last_search_symbol', "2330.TW")
default_symbol_index = 0

for i, display_name in enumerate(current_category_options_display):
    if display_name.startswith(current_symbol_code):
         default_symbol_index = i
         break

st.sidebar.selectbox(
    f"選擇 {selected_category} 標的",
    current_category_options_display,
    index=default_symbol_index,
    key="symbol_select_box",
    on_change=update_search_input,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

st.sidebar.markdown("3. 🔍 **輸入股票代碼或中文名稱**")

text_input_current_value = st.session_state.get('sidebar_search_input', st.session_state.get('last_search_symbol', "2330.TW"))

selected_query = st.sidebar.text_input(
    "🔍 輸入股票代碼或中文名稱", 
    placeholder="例如：AAPL, 台積電, 廣達, BTC-USD", 
    value=text_input_current_value,
    key="sidebar_search_input",
    label_visibility="collapsed"
)

final_symbol_to_analyze = get_symbol_from_query(selected_query)

is_symbol_changed = final_symbol_to_analyze != st.session_state.get('last_search_symbol', "INIT")

if is_symbol_changed:
    if final_symbol_to_analyze and final_symbol_to_analyze != "---": 
        st.session_state['analyze_trigger'] = True
        st.session_state['last_search_symbol'] = final_symbol_to_analyze
        st.session_state['data_ready'] = False


st.sidebar.markdown("---")

st.sidebar.markdown("4. **選擇週期**")

period_keys = list(PERIOD_MAP.keys())
selected_period_key = st.sidebar.selectbox("分析時間週期", period_keys, index=period_keys.index("1 日 (中長線)")) 

selected_period_value = PERIOD_MAP[selected_period_key]

yf_period, yf_interval = selected_period_value

is_long_term = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]

st.sidebar.markdown("---")

st.sidebar.markdown("5. **開始分析**")
analyze_button_clicked = st.sidebar.button("📊 執行AI分析", type="primary", key="main_analyze_button") 

if analyze_button_clicked or st.session_state.get('analyze_trigger', False):
    
    st.session_state['data_ready'] = False
    st.session_state['analyze_trigger'] = False 
    
    try:
        with st.spinner(f"🔍 正在啟動AI模型，獲取並分析 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
            
            df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
            
            if df.empty:
                display_symbol = final_symbol_to_analyze
                # 假設 FULL_SYMBOLS_MAP 已經在程式碼其他部分定義
                # for code, data in FULL_SYMBOLS_MAP.items():
                #     if data["name"] == final_symbol_to_analyze:
                #         display_symbol = code
                #         break
                    
                st.error(f"❌ **數據不足或代碼無效。** 請確認代碼 **{display_symbol}** 是否正確。")
                st.info(f"💡 **提醒：** 台灣股票需要以 **代碼.TW** 格式輸入 (例如：**2330.TW**)。")
                st.session_state['data_ready'] = False 
            else:
                company_info = get_company_info(final_symbol_to_analyze) 
                currency_symbol = get_currency_symbol(final_symbol_to_analyze) 
                
                df = calculate_technical_indicators(df) 
                fa_result = calculate_fundamental_rating(final_symbol_to_analyze)
                analysis = generate_expert_fusion_signal(
                    df, 
                    fa_rating=fa_result['Combined_Rating'], 
                    is_long_term=is_long_term
                )
                
                st.session_state['analysis_results'] = {
                    'df': df,
                    'company_info': company_info,
                    'currency_symbol': currency_symbol,
                    'fa_result': fa_result,
                    'analysis': analysis,
                    'selected_period_key': selected_period_key,
                    'final_symbol_to_analyze': final_symbol_to_analyze
                }
                
                st.session_state['data_ready'] = True

    except Exception as e:
        st.error(f"❌ 分析 {final_symbol_to_analyze} 時發生未預期的錯誤: {str(e)}")
        st.info("💡 請檢查代碼格式或嘗試其他分析週期。")
        st.session_state['data_ready'] = False 

if st.session_state.get('data_ready', False):
    
    results = st.session_state['analysis_results']
    df = results['df']
    company_info = results['company_info']
    currency_symbol = results['currency_symbol']
    fa_result = results['fa_result']
    analysis = results['analysis']
    selected_period_key = results['selected_period_key']
    final_symbol_to_analyze = results['final_symbol_to_analyze']
    
    st.header(f"📈 **{company_info['name']}** ({final_symbol_to_analyze}) AI趨勢分析")
    
    current_price = analysis['current_price']
    prev_close = df['Close'].iloc[-2] if len(df) >= 2 else current_price
    change = current_price - prev_close
    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
    
    price_delta_color = 'inverse' if change < 0 else 'normal'

    st.markdown(f"**分析週期:** **{selected_period_key}** | **FA 評級:** **{fa_result['Combined_Rating']:.2f}**")
    st.markdown(f"**基本面診斷:** {fa_result['Message']}")
    st.markdown("---")
    
    st.subheader("💡 核心行動與量化評分")
    
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] { font-size: 20px; }
        [data-testid="stMetricLabel"] { font-size: 13px; }
        [data-testid="stMetricDelta"] { font-size: 12px; }
        .action-buy { color: #cc0000; font-weight: bold; }
        .action-sell { color: #1e8449; font-weight: bold; }
        .action-neutral { color: #cc6600; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True
    )
    
    col_core_1, col_core_2, col_core_3, col_core_4 = st.columns(4)
    
    with col_core_1: 
        st.metric("💰 當前價格", f"{currency_symbol}{current_price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)", delta_color=price_delta_color)
    
    with col_core_2: 
        st.markdown("**🎯 最終行動建議**")
        action_class = "action-buy" if analysis['action'] == "買進 (Buy)" else ("action-sell" if analysis['action'] == "賣出 (Sell/Short)" else "action-neutral")
        st.markdown(f"<p class='{action_class}' style='font-size: 20px;'>{analysis['action']}</p>", unsafe_allow_html=True)
    
    with col_core_3: 
        st.metric("🔥 總量化評分", f"{analysis['score']}", help="FA/TA 融合策略總分 (正數看漲)")
    with col_core_4: 
        st.metric("🛡️ 信心指數", f"{analysis['confidence']:.0f}%", help="AI對此建議的信心度")
    
    st.markdown("---")

    st.subheader("🛡️ 精確交易策略與風險控制")
    col_strat_1, col_strat_2, col_strat_3, col_strat_4 = st.columns(4)

    risk = abs(analysis['entry_price'] - analysis['stop_loss'])
    reward = abs(analysis['take_profit'] - analysis['entry_price'])
    risk_reward = reward / risk if risk > 0 else float('inf')

    with col_strat_1:
        st.markdown(f"**建議操作:** <span class='{action_class}' style='font-size: 18px;'>**{analysis['action']}**</span>", unsafe_allow_html=True)
    with col_strat_2:
        st.markdown(f"**建議進場價:** <span style='color:#cc6600;'>**{currency_symbol}{analysis['entry_price']:.2f}**</span>", unsafe_allow_html=True)
    with col_strat_3:
        st.markdown(f"**🚀 止盈價 (TP):** <span style='color:red;'>**{currency_symbol}{analysis['take_profit']:.2f}**</span>", unsafe_allow_html=True)
    with col_strat_4:
        st.markdown(f"**🛑 止損價 (SL):** <span style='color:green;'>**{currency_symbol}{analysis['stop_loss']:.2f}**</span>", unsafe_allow_html=True)
        
    st.info(f"**💡 策略總結:** **{analysis['strategy']}** | **⚖️ 風險/回報比 (R:R):** **{risk_reward:.2f}** | **波動單位 (ATR):** {analysis.get('atr', 0):.4f}")
    
    st.markdown("---")
    
    st.subheader("📊 關鍵技術指標數據與AI判讀 (交叉驗證細節)")
    
    ai_df = pd.DataFrame(analysis['expert_opinions'].items(), columns=['AI領域', '判斷結果']) 
    
    if isinstance(fa_result, dict) and 'Message' in fa_result:
        ai_df.loc[len(ai_df)] = ['基本面 FCF/ROE/PE 診斷', fa_result['Message']]
    
    def style_expert_opinion(s):
        is_positive = s.str.contains('牛市|買進|多頭|強化|利多|增長|頂級|良好|潛在反彈|K線向上|正常波動性', case=False)
        is_negative = s.str.contains('熊市|賣出|空頭|削弱|利空|下跌|不足|潛在回調|K線向下|極高波動性', case=False)
        is_neutral = s.str.contains('盤整|警告|中性|觀望|趨勢發展中|不適用|不完整', case=False) 
        
        colors = np.select(
            [is_negative, is_positive, is_neutral],
            ['color: #1e8449; font-weight: bold;', 'color: #cc0000; font-weight: bold;', 'color: #cc6600;'],
            default='color: #888888;'
        )
        return [f'{c}' for c in colors]

    styled_ai_df = ai_df.style.apply(style_expert_opinion, subset=['判斷結果'], axis=0)

    st.dataframe(
        styled_ai_df,
        use_container_width=True,
        key=f"ai_df_{final_symbol_to_analyze}_{selected_period_key}",
        column_config={
            "AI領域": st.column_config.Column("AI領域", help="FA/TA 分析範疇"),
            "判斷結果": st.column_config.Column("判斷結果", help="AI對該領域的量化判讀與結論"),
        }
    )
    
    st.caption("ℹ️ **設計師提示:** 判讀結果顏色：**紅色=多頭/強化信號** (類似低風險買入)，**綠色=空頭/削弱信號** (類似高風險賣出)，**橙色=中性/警告**。")

    st.markdown("---")
    
    st.subheader("🛠️ 技術指標狀態表")
    technical_df = get_technical_data_df(df)
    
    if not technical_df.empty:
        def style_indicator(s):
            df_color = technical_df['顏色']
            color_map = {'red': 'color: #cc0000; font-weight: bold;', 
                         'green': 'color: #1e8449; font-weight: bold;', 
                         'orange': 'color: #cc6600;',
                         'blue': 'color: #004d99;',
                         'grey': 'color: #888888;'}
            
            return [color_map.get(df_color.loc[index], '') for index in s.index]
            
        styled_df = technical_df[['最新值', '分析結論']].style.apply(style_indicator, subset=['最新值', '分析結論'], axis=0)

        st.dataframe(
            styled_df, 
            use_container_width=True,
            key=f"technical_df_{final_symbol_to_analyze}_{selected_period_key}",
            column_config={
                "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
            }
        )
        st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**（類似低風險買入），**綠色=空頭/削弱信號**（類似高風險賣出），**橙色=中性/警告**）。")

    else:
        st.info("無足夠數據生成關鍵技術指標表格。")
    
    st.markdown("---")
    
    st.subheader(f"📊 完整技術分析圖表")
    chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
    
    st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
      st.info("請在左側選擇或輸入標的，然後點擊 **『執行AI分析』** 開始。")


if __name__ == '__main__':
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
        
    main()
    
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
