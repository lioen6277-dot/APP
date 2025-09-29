import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import warnings
import time
import re 
from datetime import datetime, timedelta
import base64 # 導入 base64 模塊 (新增)

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

# ==============================================================================
# 2. 核心分析功能 (保持不變)
# ==============================================================================

# [原有的輔助函數]

def get_stock_data(symbol, period_tuple):
    """從 Yahoo Finance 下載股票數據"""
    try:
        data = yf.download(
            symbol,
            period=period_tuple[0],
            interval=period_tuple[1],
            # 確保取得盤前/盤後數據 (僅適用於 1h, 30m, 90m, 60m 週期)
            prepost=True if period_tuple[1] in ["1h", "30m", "90m", "60m"] else False
        )
        if data.empty:
            return None
        
        # 移除重複的時間戳記，保留最後一筆
        data = data[~data.index.duplicated(keep='last')]
        
        # 排序並處理時間區間的極端值
        data = data.sort_index(ascending=True)

        return data
    except Exception as e:
        st.error(f"下載數據時發生錯誤：{e}")
        return None

def calculate_indicators(df):
    """計算技術指標"""
    # 複製 DataFrame 以避免 SettingWithCopyWarning
    df = df.copy()

    # 基礎指標
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)

    # 動量指標 (Momentum)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    df['K'] = stoch.stoch()
    df['D'] = stoch.stoch_signal()
    
    # 趨勢指標 (Trend)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()

    # 波動性指標 (Volatility)
    bollinger = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    df['BB_Mavg'] = bollinger.bollinger_mavg()
    
    # 成交量指標 (Volume)
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])

    # 移除 NaN 值，確保計算準確性
    df = df.dropna()
    
    return df

def interpret_rsi(rsi):
    """RSI 分析"""
    if rsi >= 70:
        return {"status": "空頭/削弱信號", "advice": "極度超買，短期回檔風險高", "color": "#008000"}  # 綠色：賣出/高風險
    elif rsi >= 60:
        return {"status": "多頭/強化信號", "advice": "趨勢強勁，但動能可能見頂", "color": "#ff9933"} # 淡橙色：中性/警告
    elif rsi <= 30:
        return {"status": "多頭/強化信號", "advice": "極度超賣，短期反彈機率高", "color": "#ff0000"}  # 紅色：買入/低風險
    elif rsi <= 40:
        return {"status": "空頭/削弱信號", "advice": "趨勢疲弱，動能不足", "color": "#ff9933"} # 淡橙色：中性/警告
    else:
        return {"status": "中性/警告", "advice": "市場保持平衡，無明確信號", "color": "#cccccc"} # 灰色：中性

def interpret_macd(macd_hist):
    """MACD 柱狀圖分析"""
    if macd_hist > 0:
        return {"status": "多頭/強化信號", "advice": "動能偏多，趨勢可能延續", "color": "#ff0000"}
    elif macd_hist < 0:
        return {"status": "空頭/削弱信号", "advice": "動能偏空，趨勢可能轉弱", "color": "#008000"}
    else:
        return {"status": "中性/警告", "advice": "動能持平，趨勢可能盤整", "color": "#cccccc"}

def interpret_stoch(k, d):
    """KDJ (Stochastic) 分析"""
    if k > d and k < 20:
        return {"status": "多頭/強化信號", "advice": "KD低位黃金交叉，可能反彈", "color": "#ff0000"}
    elif k < d and k > 80:
        return {"status": "空頭/削弱信號", "advice": "KD高位死亡交叉，可能回調", "color": "#008000"}
    elif k >= 80:
        return {"status": "空頭/削弱信號", "advice": "超買區，注意回調風險", "color": "#ff9933"}
    elif k <= 20:
        return {"status": "多頭/強化信號", "advice": "超賣區，醞釀反彈機會", "color": "#ff9933"}
    else:
        return {"status": "中性/警告", "advice": "一般波動範圍，趨勢不明確", "color": "#cccccc"}

def interpret_bb(close, bb_high, bb_low, bb_mavg):
    """布林通道分析"""
    if close >= bb_high * 0.999:
        return {"status": "空頭/削弱信號", "advice": "股價觸及上軌，短期超買", "color": "#008000"}
    elif close <= bb_low * 1.001:
        return {"status": "多頭/強化信號", "advice": "股價觸及下軌，短期超賣", "color": "#ff0000"}
    elif close > bb_mavg:
        return {"status": "多頭/強化信號", "advice": "股價運行在中軌之上", "color": "#ff9933"}
    elif close < bb_mavg:
        return {"status": "空頭/削弱信號", "advice": "股價運行在中軌之下", "color": "#ff9933"}
    else:
        return {"status": "中性/警告", "advice": "股價在中軌附近盤整", "color": "#cccccc"}


def get_indicator_summary(df):
    """生成技術指標總結表格"""
    if df.empty:
        return None
        
    last_row = df.iloc[-1]

    # --- RSI ---
    rsi_val = last_row['RSI']
    rsi_res = interpret_rsi(rsi_val)
    
    # --- MACD ---
    macd_hist_val = last_row['MACD_Hist']
    macd_res = interpret_macd(macd_hist_val)

    # --- KDJ ---
    k_val = last_row['K']
    d_val = last_row['D']
    stoch_res = interpret_stoch(k_val, d_val)

    # --- Bollinger Bands ---
    bb_res = interpret_bb(last_row['Close'], last_row['BB_High'], last_row['BB_Low'], last_row['BB_Mavg'])

    # --- 彙整成 DataFrame ---
    summary_data = {
        "指標名稱": [
            "RSI (相對強弱)", "MACD (動能指標)", "KDJ (隨機指標)", "BB (布林通道)"
        ],
        "最新值": [
            f"{rsi_val:.2f}", 
            f"直方圖: {macd_hist_val:.3f}", 
            f"K: {k_val:.2f}, D: {d_val:.2f}",
            f"收盤價: {last_row['Close']:.2f}"
        ],
        "分析結論": [
            rsi_res["advice"], macd_res["advice"], stoch_res["advice"], bb_res["advice"]
        ],
        "顏色": [
            rsi_res["color"], macd_res["color"], stoch_res["color"], bb_res["color"]
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    
    # 格式化 DataFrame for Streamlit display
    def color_rows(row):
        color = row['顏色']
        # 排除顏色列
        return [f'background-color: {color}' if col != '顏色' else '' for col in row.index]

    styled_df = summary_df.style.apply(color_rows, axis=1).hide(axis='columns', names=['顏色'])

    return styled_df

def create_comprehensive_chart(df, symbol, period):
    """創建綜合分析圖表 (K線圖, 交易量, RSI, MACD)"""
    
    # 創建一個包含4個子圖的圖表
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.5, 0.2, 0.15, 0.15], # K線圖佔比最高
        subplot_titles=(
            f'{symbol} K線圖與趨勢指標 ({period})', 
            '交易量 (Volume)', 
            'RSI (相對強弱指數)', 
            'MACD (平滑異同移動平均線)'
        )
    )

    # 1. K線圖 (Row 1)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        showlegend=False
    ), row=1, col=1)

    # 趨勢線 (SMA_20, EMA_50, BB_Mavg)
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['SMA_20'], 
        line=dict(color='#ff9933', width=1),  # 淡橙色 SMA 20
        name='SMA 20'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['EMA_50'], 
        line=dict(color='blue', width=1, dash='dash'), 
        name='EMA 50'
    ), row=1, col=1)

    # 布林通道
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['BB_High'], 
        line=dict(color='gray', width=0.5), 
        name='BB High', 
        showlegend=False
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['BB_Low'], 
        line=dict(color='gray', width=0.5), 
        fill='tonexty', # 填充上下軌之間的區域
        fillcolor='rgba(192, 192, 192, 0.1)',
        name='BB Low',
        showlegend=False
    ), row=1, col=1)

    # 2. 交易量 (Row 2)
    colors = ['#ff0000' if row['Open'] < row['Close'] else '#008000' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['Volume'], 
        name='交易量',
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)

    # 3. RSI (Row 3)
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['RSI'], 
        line=dict(color='purple', width=1.5), 
        name='RSI',
        showlegend=False
    ), row=3, col=1)
    # RSI 超買/超賣區間線
    fig.add_hline(y=70, line_dash="dash", line_color="green", row=3, col=1, annotation_text="超買 (70)", annotation_position="top left")
    fig.add_hline(y=30, line_dash="dash", line_color="red", row=3, col=1, annotation_text="超賣 (30)", annotation_position="bottom left")

    # 4. MACD (Row 4)
    # MACD 柱狀圖
    hist_colors = ['#ff0000' if h >= 0 else '#008000' for h in df['MACD_Hist']]
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['MACD_Hist'], 
        name='MACD Hist',
        marker_color=hist_colors,
        showlegend=False
    ), row=4, col=1)
    # MACD 線
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['MACD'], 
        line=dict(color='blue', width=1.5), 
        name='MACD Line',
        showlegend=False
    ), row=4, col=1)
    # Signal 線
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['MACD_Signal'], 
        line=dict(color='red', width=1), 
        name='Signal Line',
        showlegend=False
    ), row=4, col=1)
    
    # 更新佈局
    fig.update_layout(
        title_text=f'{symbol} 綜合技術分析 - {period}',
        height=900, 
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        template="plotly_white",
        
        # 調整 RSI/MACD Y軸範圍
        yaxis3=dict(range=[0, 100]),
        yaxis4=dict(title='MACD Value'),
        
        # 調整圖例位置
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 隱藏子圖標題的 X 軸標籤，只保留最底下的
    for i in range(1, 4):
        fig.update_xaxes(showticklabels=False, row=i, col=1)
        
    return fig

# ==============================================================================
# 2. Streamlit 應用程式主體
# ==============================================================================

# ⚙️ 網站配置 (已使用您的 Base64 LOGO 替換)
st.set_page_config(
    page_title="🤖 AI趨勢分析儀表板 📈", 
    page_icon=BASE64_LOGO, # 使用 Base64 LOGO 作為網站圖標
    layout="wide"
)

PERIOD_MAP = { 
    "30 分 (短期)": ("60d", "30m"), 
    "4 小時 (波段)": ("1y", "60m"), 
    "1 日 (中長線)": ("5y", "1d"), 
    "1 週 (長期)": ("max", "1wk")
}

# 🚀 您的【所有資產清單】(FULL_SYMBOLS_MAP)
FULL_SYMBOLS_MAP = {
    # ----------------------------------------------------
    # A. 美股核心 (US Stocks) - 個股
    # ----------------------------------------------------
    "TSLA": {"name": "特斯拉", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "NVDA": {"name": "輝達", "keywords": ["輝達", "英偉達", "AI", "NVDA", "NVIDIA"]},
    "AAPL": {"name": "蘋果", "keywords": ["蘋果", "手機", "AAPL", "Apple"]},
    "MSFT": {"name": "微軟", "keywords": ["微軟", "雲端", "MSFT", "Microsoft"]},
    "GOOGL": {"name": "谷歌", "keywords": ["谷歌", "Google", "Alphabet", "GOOGL"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["亞馬遜", "電商", "AMZN", "Amazon"]},
    # ----------------------------------------------------
    # B. 美股核心 (US Stocks) - ETF/指數
    # ----------------------------------------------------
    "SPY": {"name": "標普500 ETF", "keywords": ["標普500", "SPY", "ETF"]},
    "QQQ": {"name": "那斯達克100 ETF", "keywords": ["那斯達克", "QQQ", "科技"]},
    # ----------------------------------------------------
    # C. 台股核心 (TW Stocks) - 個股
    # ----------------------------------------------------
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "晶圓", "2330"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "IC設計", "2454"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "ETF"]},
    "0056.TW": {"name": "元大高股息", "keywords": ["高股息", "0056", "ETF"]},
    # ----------------------------------------------------
    # D. 加密貨幣 (Crypto)
    # ----------------------------------------------------
    "BTC-USD": {"name": "比特幣", "keywords": ["比特幣", "BTC", "加密貨幣"]},
    "ETH-USD": {"name": "以太幣", "keywords": ["以太幣", "ETH", "加密貨幣"]},
}


def main():
    
    # ==============================================================================
    # 3. 側邊欄配置
    # ==============================================================================
    st.sidebar.title("🛠️ 分析參數設定")

    # --- 選擇資產類別 ---
    asset_types = ["美股", "台股", "加密貨幣"]
    selected_asset = st.sidebar.selectbox("請選擇資產類別：", asset_types)

    # --- 根據類別篩選標的 ---
    if selected_asset == "美股":
        current_symbols = {k: v for k, v in FULL_SYMBOLS_MAP.items() if k not in ["2330.TW", "2454.TW", "0050.TW", "0056.TW", "BTC-USD", "ETH-USD"]}
    elif selected_asset == "台股":
        current_symbols = {k: v for k, v in FULL_SYMBOLS_MAP.items() if ".TW" in k}
    elif selected_asset == "加密貨幣":
        current_symbols = {k: v for k, v in FULL_SYMBOLS_MAP.items() if "-USD" in k}
    else:
        current_symbols = FULL_SYMBOLS_MAP

    # --- 標的選擇/輸入 ---
    # 創建一個包含 (名稱 - 代碼) 的列表
    symbol_options = [f"{v['name']} ({k})" for k, v in current_symbols.items()]
    
    # 預設值處理
    default_symbol_key = st.session_state.get('last_search_symbol', "2330.TW")
    default_index = next((i for i, opt in enumerate(symbol_options) if default_symbol_key in opt), 0)
    
    selected_option = st.sidebar.selectbox(
        "選擇熱門標的：",
        options=symbol_options,
        index=default_index,
        key='sidebar_select_symbol'
    )
    
    # 解析選中的代碼
    match = re.search(r'\(([^)]+)\)$', selected_option)
    selected_symbol_code = match.group(1) if match else selected_option.split(' ')[-1] # 提取括號內的代碼

    # 手動輸入框
    manual_input = st.sidebar.text_input(
        "或手動輸入標的代碼/名稱 (如 2330.TW, TSLA):",
        value=st.session_state.get('sidebar_search_input', selected_symbol_code),
        key='sidebar_text_input'
    )

    # 確定最終要分析的標的
    # 如果手動輸入框有值且與下拉選單的值不同，則使用手動輸入的值
    if manual_input and manual_input.upper() != selected_symbol_code and manual_input.upper() != selected_option:
        final_symbol_to_analyze = manual_input.upper()
    else:
        final_symbol_to_analyze = selected_symbol_code

    # --- 選擇分析週期 ---
    selected_period_key = st.sidebar.selectbox(
        "選擇分析週期：", 
        options=list(PERIOD_MAP.keys()),
        index=2 # 預設為 1 日 (中長線)
    )
    period_tuple = PERIOD_MAP[selected_period_key]

    # --- 執行按鈕 ---
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", type="primary")

    # ==============================================================================
    # 4. 資料處理與顯示
    # ==============================================================================

    # 初始化 session state 變數
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
        
    if 'analyzed_data' not in st.session_state:
        st.session_state['analyzed_data'] = None
        
    if 'last_analyzed_symbol' not in st.session_state:
        st.session_state['last_analyzed_symbol'] = None

    # 執行分析的邏輯
    if analyze_button_clicked or (st.session_state.get('last_analyzed_symbol') and st.session_state['last_analyzed_symbol'] != final_symbol_to_analyze):
        
        st.session_state['data_ready'] = False # 重置狀態
        st.session_state['last_search_symbol'] = final_symbol_to_analyze # 儲存最後搜尋的標的
        st.session_state['sidebar_search_input'] = final_symbol_to_analyze # 更新輸入框的值
        
        with st.spinner(f"正在為 {final_symbol_to_analyze} 下載數據並執行AI技術分析..."):
            
            # 1. 下載數據
            df_raw = get_stock_data(final_symbol_to_analyze, period_tuple)
            
            if df_raw is None or df_raw.empty:
                st.error(f"無法獲取 {final_symbol_to_analyze} 的數據。請檢查標的代碼是否正確。")
                st.session_state['data_ready'] = False
            else:
                # 2. 計算指標
                df_analyzed = calculate_indicators(df_raw)
                
                # 3. 儲存結果
                st.session_state['analyzed_data'] = df_analyzed
                st.session_state['last_analyzed_symbol'] = final_symbol_to_analyze
                st.session_state['last_analyzed_period'] = selected_period_key
                st.session_state['data_ready'] = True
                
                st.balloons() # 成功提示

    # === 結果呈現區塊 ===
    if st.session_state.get('data_ready', False):
        
        df = st.session_state['analyzed_data']
        final_symbol_to_analyze = st.session_state['last_analyzed_symbol']
        selected_period_key = st.session_state['last_analyzed_period']
        last_price = df['Close'].iloc[-1]
        
        st.title(f"🤖 {final_symbol_to_analyze} AI 趨勢分析報告")
        st.subheader(f"📈 週期: {selected_period_key} | 最新收盤價: **${last_price:,.2f}**")
        st.markdown("---")
        
        # --- 關鍵技術指標總結 ---
        st.subheader(f"🧠 AI關鍵指標判讀 ({selected_period_key})")
        summary_df_styled = get_indicator_summary(df)

        if summary_df_styled is not None:
            # 應用 Streamlit 的數據表格顯示風格
            st.dataframe(
                summary_df_styled,
                use_container_width=True,
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

    # === 修正部分：未分析時的預設首頁顯示 (已使用 LOGO 和淡橙色標題) ===
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 將 LOGO 圖片顯示在主頁面
          st.markdown(f"""
              <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
                  <img src="{BASE64_LOGO}" alt="AI Trend Analysis Logo" style="width: 180px; height: auto; border-radius: 15px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
              </div>
              <h1 style='color: #ff9933; font-size: 36px; font-weight: bold; text-align: center;'>🚀 歡迎使用 AI 趨勢分析儀表板</h1>
              """, 
              unsafe_allow_html=True
          )
          
          st.info("請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 **『📊 執行AI分析』** 按鈕開始。")
          
          st.markdown("---")
          
          st.subheader("📝 使用步驟：")
          st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
          st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
          st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分 (短期)`、`1 日 (中長線)`）。")
          st.markdown("4. **執行分析**：點擊 **『📊 執行AI分析』**，AI將融合基本面與技術面指標提供交易策略。")


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'sidebar_search_input' not in st.session_state:
        st.session_state['sidebar_search_input'] = "2330.TW"
        
    main()
    
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")

