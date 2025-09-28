import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta # Technical Analysis Library
import warnings
import time
import re 
from datetime import datetime, timedelta

# 警告處理：隱藏 Pandas 或 TA-Lib 可能發出的未來警告
warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

# **頁面標題加入 📈 Emoji**
st.set_page_config(
    page_title="🤖 AI趨勢分析儀表板 📈", 
    page_icon="📈", 
    layout="wide"
)

# YFinance 參數對應表
PERIOD_MAP = { 
    "30 分 (短期)": ("60d", "30m"), 
    "4 小時 (波段)": ("1y", "60m"), 
    "1 日 (中長線)": ("5y", "1d"), 
    "1 週 (長期)": ("max", "1wk")
}

# 您的【所有資產清單】(ALL_ASSETS_MAP)
ALL_ASSETS_MAP = {
    "🎯 蘋果 (AAPL) - 美股": "AAPL",
    "🎯 台灣積體電路 (2330.TW) - 台股": "2330.TW",
    "🎯 比特幣 (BTC-USD) - 加密貨幣": "BTC-USD",
    "🎯 S&P 500 指數 (SPY) - ETF": "SPY",
    "🎯 那斯達克 100 指數 (QQQ) - ETF": "QQQ",
    "🎯 台灣 50 (0050.TW) - ETF": "0050.TW",
    "--- 常見美股 ---": "---",
    "微軟 (MSFT)": "MSFT",
    "Google (GOOGL)": "GOOGL",
    "亞馬遜 (AMZN)": "AMZN",
    "特斯拉 (TSLA)": "TSLA",
    "輝達 (NVDA)": "NVDA",
    "--- 常見台股 ---": "---",
    "鴻海 (2317.TW)": "2317.TW",
    "聯發科 (2454.TW)": "2454.TW",
    "台達電 (2308.TW)": "2308.TW",
    "長榮 (2603.TW)": "2603.TW",
    "--- 常見加密貨幣 ---": "---",
    "以太幣 (ETH-USD)": "ETH-USD",
    "狗狗幣 (DOGE-USD)": "DOGE-USD",
    "--- 全球主要指數 ---": "---",
    "道瓊工業指數 (DIJ)": "^DJI",
    "香港恒生指數 (HSI)": "^HSI",
    "日經 225 (N225)": "^N225",
}

# 狀態初始化
if 'data_ready' not in st.session_state:
    st.session_state.data_ready = False


# ==============================================================================
# 2. 側邊欄用戶輸入 (Sidebar) - 已修正順序與標題
# ==============================================================================

# 側邊欄主標題
st.sidebar.title("🛠️ 分析工具箱")
st.sidebar.markdown("""
歡迎使用 **AI 趨勢分析儀表板**！
請選擇或輸入您想分析的標的。
""")

# --- 1. 快速選擇熱門標的 (Quick Select) - 🚀 順序 1
st.sidebar.subheader("🚀 快速選擇熱門標的") 
selected_asset_name = st.sidebar.selectbox(
    "請選擇標的...",
    options=list(ALL_ASSETS_MAP.keys()),
    index=0,
    key='selected_asset_name_sb'
)

# --- 2. 輸入股票代碼或中文名稱 (Manual Input) - 🔍 順序 2
st.sidebar.subheader("🔍 輸入股票代碼或中文名稱") 
# 過濾出被選中的資產代碼作為預設值
default_symbol = ALL_ASSETS_MAP.get(selected_asset_name, "SPY")
# 創建一個新的、可手動輸入的文本框
custom_symbol_input = st.sidebar.text_input(
    "請輸入股票代碼 (e.g., AAPL, 2330.TW, BTC-USD)：",
    value=default_symbol,
    key='custom_symbol_input_sb'
)


# --- 3. 選擇分析時間週期 (Period Select) - ⏳ 順序 3
st.sidebar.subheader("⏳ 選擇分析時間週期") 
selected_period_key = st.sidebar.radio(
    "選擇圖表和分析的時間跨度：",
    options=list(PERIOD_MAP.keys()),
    index=2, # 預設選擇 '1 日 (中長線)'
    key='selected_period_key_sb'
)

# --- 4. 分析按鈕
st.sidebar.markdown("---")
analyze_button_clicked = st.sidebar.button("✨ 開始分析", key='analyze_button_sb', use_container_width=True)

# ==============================================================================
# 3. 數據獲取與預處理函數
# ==============================================================================

@st.cache_data(ttl=3600) # 緩存數據，提高性能
def get_data_and_info(symbol, period, interval):
    """從 YFinance 獲取歷史價格和資產資訊"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 獲取資訊 (如果可用)
        info = ticker.info
        
        # 獲取歷史數據
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            return None, None, f"⚠️ **數據獲取失敗:** 無法取得 {symbol} 在 {interval} 週期內的數據。請檢查代碼或週期設定。"

        # 重新命名欄位以保持一致性
        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
        data = data.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')
        
        return data, info, None
    
    except Exception as e:
        return None, None, f"⚠️ **數據獲取錯誤:** {e}"

# ==============================================================================
# 4. 技術分析計算與判讀函數
# ==============================================================================

def calculate_technical_indicators(df):
    """計算常用技術指標 (RSI, MACD, Bollinger Bands)"""
    # 確保輸入數據的 Close 欄位存在
    if df is None or 'Close' not in df.columns:
        return None

    df_ta = df.copy()

    # RSI (相對強弱指數) - 14 週期
    df_ta['RSI'] = ta.momentum.RSIIndicator(df_ta['Close'], window=14).rsi()

    # MACD (移動平均收斂/發散指標) - 12, 26, 9 週期
    macd = ta.trend.MACD(df_ta['Close'], window_fast=12, window_slow=26, window_sign=9)
    df_ta['MACD'] = macd.macd()
    df_ta['MACD_Signal'] = macd.macd_signal()
    df_ta['MACD_Diff'] = macd.macd_diff() # 柱狀圖

    # Bollinger Bands (布林通道) - 20 週期, 2 倍標準差
    bollinger = ta.volatility.BollingerBands(df_ta['Close'], window=20, window_dev=2)
    df_ta['BB_High'] = bollinger.bollinger_hband()
    df_ta['BB_Low'] = bollinger.bollinger_lband()
    df_ta['BB_Mid'] = bollinger.bollinger_mavg()
    df_ta['BB_Width'] = bollinger.bollinger_wband()

    # MA (簡單移動平均) - 5日, 20日, 60日
    df_ta['MA5'] = ta.trend.sma_indicator(df_ta['Close'], window=5)
    df_ta['MA20'] = ta.trend.sma_indicator(df_ta['Close'], window=20)
    df_ta['MA60'] = ta.trend.sma_indicator(df_ta['Close'], window=60)
    
    # 移除 NaN 值
    df_ta = df_ta.dropna()

    return df_ta

def interpret_indicator(name, value, df_ta=None):
    """根據指標數值提供趨勢判讀和視覺化顏色"""
    if pd.isna(value):
        return {"value": "-", "conclusion": "數據不足", "color": "orange"}
        
    value = round(value, 2)
    
    if name == 'RSI':
        if value > 70:
            return {"value": f"{value}", "conclusion": "超買區 (動能過強)", "color": "green"} # 綠色代表潛在賣出信號/風險
        elif value < 30:
            return {"value": f"{value}", "conclusion": "超賣區 (動能過弱)", "color": "red"} # 紅色代表潛在買入信號/機會
        else:
            return {"value": f"{value}", "conclusion": "中性 (趨勢延續)", "color": "orange"}
    
    elif name == 'MACD':
        if df_ta is not None and len(df_ta) >= 2:
            current_diff = df_ta['MACD_Diff'].iloc[-1]
            prev_diff = df_ta['MACD_Diff'].iloc[-2] if len(df_ta) >= 2 else 0

            if current_diff > 0 and current_diff > prev_diff:
                return {"value": f"{value}", "conclusion": "多頭動能增強 (DIFF > 0, 柱體放大)", "color": "red"}
            elif current_diff < 0 and current_diff < prev_diff:
                 return {"value": f"{value}", "conclusion": "空頭動能增強 (DIFF < 0, 柱體放大)", "color": "green"}
            elif current_diff > 0:
                 return {"value": f"{value}", "conclusion": "多頭動能減弱 (DIFF > 0, 柱體縮小)", "color": "orange"}
            elif current_diff < 0:
                 return {"value": f"{value}", "conclusion": "空頭動能減弱 (DIFF < 0, 柱體縮小)", "color": "orange"}
            else:
                 return {"value": f"{value}", "conclusion": "中性/等待信號", "color": "orange"}
        
        # 僅用 MACD 值判斷
        if value > 0:
            return {"value": f"{value}", "conclusion": "多頭趨勢 (MACD > 0)", "color": "red"}
        elif value < 0:
            return {"value": f"{value}", "conclusion": "空頭趨勢 (MACD < 0)", "color": "green"}
        else:
            return {"value": f"{value}", "conclusion": "中性/盤整", "color": "orange"}
            
    elif name.startswith('MA'):
        current_close = df_ta['Close'].iloc[-1]
        if current_close > value:
            return {"value": f"{value}", "conclusion": f"多頭支撐 (收盤價 > MA{name.replace('MA', '')})", "color": "red"}
        elif current_close < value:
            return {"value": f"{value}", "conclusion": f"空頭壓力 (收盤價 < MA{name.replace('MA', '')})", "color": "green"}
        else:
            return {"value": f"{value}", "conclusion": "中性/糾結", "color": "orange"}
            
    return {"value": f"{value}", "conclusion": "中性", "color": "orange"}


def create_analysis_summary_df(df_ta, final_symbol_to_analyze):
    """創建一個包含關鍵指標和判讀結論的 DataFrame"""
    if df_ta is None or df_ta.empty:
        return pd.DataFrame()
        
    latest = df_ta.iloc[-1]
    
    # 判讀結果字典列表
    results = []
    
    # 1. RSI
    rsi_result = interpret_indicator('RSI', latest['RSI'])
    results.append({
        "指標名稱": "RSI (14)",
        "最新值": rsi_result['value'],
        "分析結論": rsi_result['conclusion'],
        "顏色": rsi_result['color']
    })

    # 2. MACD (使用 MACD_Diff 作為判斷基礎)
    macd_result = interpret_indicator('MACD', latest['MACD_Diff'], df_ta)
    results.append({
        "指標名稱": "MACD 柱狀圖 (DIFF)",
        "最新值": macd_result['value'],
        "分析結論": macd_result['conclusion'],
        "顏色": macd_result['color']
    })

    # 3. 5 日均線
    ma5_result = interpret_indicator('MA5', latest['MA5'], df_ta)
    results.append({
        "指標名稱": "5 日均線 (MA5)",
        "最新值": ma5_result['value'],
        "分析結論": ma5_result['conclusion'],
        "顏色": ma5_result['color']
    })
    
    # 4. 20 日均線
    ma20_result = interpret_indicator('MA20', latest['MA20'], df_ta)
    results.append({
        "指標名稱": "20 日均線 (MA20)",
        "最新值": ma20_result['value'],
        "分析結論": ma20_result['conclusion'],
        "顏色": ma20_result['color']
    })
    
    # 5. Bollinger Bands (布林通道)
    close_price = df_ta['Close'].iloc[-1]
    bb_high = latest['BB_High']
    bb_low = latest['BB_Low']
    
    bb_conclusion = "中性 (通道內)"
    bb_color = "orange"
    if close_price > bb_high:
        bb_conclusion = "觸及/突破上軌 (強勢/超買)"
        bb_color = "green" # 高位風險
    elif close_price < bb_low:
        bb_conclusion = "觸及/跌破下軌 (弱勢/超賣)"
        bb_color = "red" # 低位機會

    results.append({
        "指標名稱": "布林通道 (20)",
        "最新值": f"H:{round(bb_high, 2)} L:{round(bb_low, 2)}",
        "分析結論": bb_conclusion,
        "顏色": bb_color
    })

    summary_df = pd.DataFrame(results)
    return summary_df

def generate_ai_summary(summary_df, asset_name, current_price, symbol):
    """基於分析表格的結論，生成一個模擬的 AI 總結"""
    if summary_df.empty:
        return f"無法為 {asset_name} ({symbol}) 生成總結，因為技術數據不足。"
        
    bullish_count = summary_df['顏色'].apply(lambda x: 1 if x == 'red' else 0).sum()
    bearish_count = summary_df['顏色'].apply(lambda x: 1 if x == 'green' else 0).sum()
    total_indicators = len(summary_df)
    
    # 總結趨勢
    if bullish_count >= 3 and bullish_count > bearish_count:
        trend = "整體多頭趨勢**極強**" if bullish_count >= 4 else "**偏向多頭趨勢**"
        recommendation = "建議積極關注或逢低布局。"
        color_trend = "red"
    elif bearish_count >= 3 and bearish_count > bullish_count:
        trend = "整體空頭趨勢**極強**" if bearish_count >= 4 else "**偏向空頭趨勢**"
        recommendation = "建議謹慎觀望或考慮減倉/避險。"
        color_trend = "green"
    elif bullish_count > bearish_count:
        trend = "**多空拉鋸**，但略微偏多"
        recommendation = "建議在關鍵支撐位附近觀察，保持中性偏多態度。"
        color_trend = "orange"
    elif bearish_count > bullish_count:
        trend = "**多空拉鋸**，但略微偏空"
        recommendation = "建議在關鍵壓力位附近觀察，保持中性偏空態度。"
        color_trend = "orange"
    else:
        trend = "**市場處於盤整或觀望階段**"
        recommendation = "建議等待明確信號，或縮小操作區間。"
        color_trend = "orange"

    # 詳細指標描述
    rsi_row = summary_df[summary_df['指標名稱'] == "RSI (14)"].iloc[0]
    macd_row = summary_df[summary_df['指標名稱'] == "MACD 柱狀圖 (DIFF)"].iloc[0]
    
    rsi_status = f"RSI 處於 **{rsi_row['分析結論'].split('(')[0].strip()}**"
    macd_status = f"MACD 柱狀圖顯示 **{macd_row['分析結論'].split('(')[0].strip()}**"

    
    # 最終建議
    summary_text = f"""
    ### 🎯 {asset_name} ({symbol}) **AI 趨勢分析總結**
    ---
    **當前價格:** ${current_price:.2f}
    
    **💡 綜合趨勢判讀:** 根據 **{total_indicators}** 個主要技術指標的分析，當前市場訊號顯示為 **{trend}**。
    
    **📢 動能與超買超賣:**
    - {rsi_status}，反映市場動能**{'過熱' if '超買' in rsi_row['分析結論'] else '偏弱' if '超賣' in rsi_row['分析結論'] else '中性'}**。
    - {macd_status}，代表近期趨勢的動能**{'正在增加' if '增強' in macd_row['分析結論'] else '正在減弱' if '減弱' in macd_row['分析結論'] else '趨勢明確'}**。
    
    **✅ 我們的建議:**
    - **整體建議:** {recommendation}
    - **風險提示:** 請密切關注價格對 **20日均線** 和 **布林通道上下軌** 的反應，以確認趨勢是否持續。
    """
    
    return summary_text, color_trend

# ==============================================================================
# 5. 圖表繪製函數 (Plotly)
# ==============================================================================

def create_comprehensive_chart(df, symbol_name, selected_period_key):
    """繪製綜合 K 線圖、均線、布林通道、RSI、MACD"""
    if df is None or df.empty:
        return go.Figure()
        
    df_ta = calculate_technical_indicators(df)
    
    # 創建子圖：1. K線+BB+MA (高度 3) 2. RSI (高度 1) 3. MACD (高度 1)
    fig = make_subplots(
        rows=3, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.6, 0.2, 0.2]
    )

    # --- 1. K線主圖 (第 1 行) ---
    fig.add_trace(go.Candlestick(
        x=df_ta.index,
        open=df_ta['Open'],
        high=df_ta['High'],
        low=df_ta['Low'],
        close=df_ta['Close'],
        name=f'{symbol_name} K線',
        increasing_line_color='#FF5733', # 紅色 K 棒
        decreasing_line_color='#33FF57', # 綠色 K 棒
        showlegend=False
    ), row=1, col=1)

    # 均線 (MA)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA5'], name='MA5', line=dict(color='#00ffff', width=1), opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA20'], name='MA20', line=dict(color='#ff00ff', width=1), opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA60'], name='MA60', line=dict(color='#ffff00', width=1.5), opacity=0.8), row=1, col=1)

    # 布林通道 (BB) - 上軌、下軌
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['BB_High'], name='BB 上軌', line=dict(color='gray', width=1, dash='dot'), opacity=0.6), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['BB_Low'], name='BB 下軌', line=dict(color='gray', width=1, dash='dot'), opacity=0.6, fill='tonexty', fillcolor='rgba(100, 100, 100, 0.1)'), row=1, col=1)


    # --- 2. RSI 副圖 (第 2 行) ---
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['RSI'], name='RSI', line=dict(color='blue', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="gray", row=2, col=1, annotation_text="超買 (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="gray", row=2, col=1, annotation_text="超賣 (30)")
    fig.update_yaxes(range=[0, 100], title_text="RSI", row=2, col=1)

    # --- 3. MACD 副圖 (第 3 行) ---
    # MACD 柱狀圖 (Diff)
    macd_colors = np.where(df_ta['MACD_Diff'] > 0, '#FF5733', '#33FF57')
    fig.add_trace(go.Bar(
        x=df_ta.index, 
        y=df_ta['MACD_Diff'], 
        name='MACD 柱狀圖', 
        marker_color=macd_colors,
        showlegend=False
    ), row=3, col=1)
    
    # MACD 線 (MACD & Signal)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MACD'], name='MACD', line=dict(color='yellow', width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MACD_Signal'], name='Signal', line=dict(color='red', width=1, dash='dot')), row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    # --- 整體佈局設定 ---
    fig.update_layout(
        title={
            'text': f'{symbol_name} - {selected_period_key} 綜合技術分析圖表',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_rangeslider_visible=False, # 隱藏底部的滑動條
        height=800, # 調整圖表高度
        template="plotly_dark", # 深色主題
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    # 移除底部兩圖的 X 軸標籤 (因為已經 shared_xaxes=True)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(title_text="時間軸", row=3, col=1) # 讓最底下的圖顯示 X 軸標籤

    return fig

# ==============================================================================
# 6. 主程式邏輯
# ==============================================================================

# 主內容區標題
st.title("🤖 AI 趨勢分析儀表板 📈") 

# 執行分析邏輯
if analyze_button_clicked:
    
    # 確定最終要分析的代碼：優先使用手動輸入，如果手動輸入為空，則使用選單選擇的代碼
    symbol_from_select = ALL_ASSETS_MAP.get(selected_asset_name)
    final_symbol_to_analyze = custom_symbol_input.strip().upper() if custom_symbol_input.strip() and custom_symbol_input.strip() != "---" else (symbol_from_select.upper() if symbol_from_select and symbol_from_select != "---" else "SPY")
    
    # 獲取時間參數
    yf_period, yf_interval = PERIOD_MAP[selected_period_key]
    
    # 顯示進度條
    with st.spinner(f'正在從伺服器獲取 **{final_symbol_to_analyze}** ({selected_period_key}) 的數據...'):
        df, info, error_message = get_data_and_info(final_symbol_to_analyze, yf_period, yf_interval)
    
    # 處理錯誤訊息
    if error_message:
        st.error(error_message)
        st.session_state.data_ready = False
        st.stop()
        
    if df is None or df.empty:
        st.error(f"⚠️ **分析失敗:** 無法取得 {final_symbol_to_analyze} 的數據。請檢查代碼是否正確。")
        st.session_state.data_ready = False
        st.stop()

    # 數據準備完成
    st.session_state.data_ready = True
    
    # 獲取資產名稱
    symbol_name = info.get('longName', final_symbol_to_analyze)
    current_price = df['Close'].iloc[-1]
    
    st.success(f"✅ **{symbol_name} ({final_symbol_to_analyze})** 數據成功載入！當前收盤價：**${current_price:.2f}**")
    st.markdown("---")

    # --- 關鍵指標計算與總結 ---
    df_ta = calculate_technical_indicators(df)
    summary_df = create_analysis_summary_df(df_ta, final_symbol_to_analyze)
    
    # 生成 AI 總結
    ai_summary_text, color_trend = generate_ai_summary(summary_df, symbol_name, current_price, final_symbol_to_analyze)
    
    
    # --- 1. AI 趨勢總結與建議 --- 
    st.subheader("🤖 AI 趨勢總結與建議") 
    
    if summary_df.empty:
        st.warning("⚠️ 數據不足，無法生成 AI 趨勢總結。")
    else:
        # 使用 color_trend 來決定框線顏色 (已修正為安全的 st.container 樣式)
        color_map = {"red": "red", "green": "green", "orange": "orange"}
        # 使用 HTML 語法設定外框顏色
        style = f"border: 2px solid {color_map.get(color_trend, 'gray')}; padding: 15px; border-radius: 10px;"
        
        with st.container(border=True):
             st.markdown(ai_summary_text, unsafe_allow_html=True)
             
    st.markdown("---")
    
    # --- 2. 關鍵指標綜合判讀 --- **加入 💡 Emoji**
    st.subheader(f"💡 關鍵指標綜合判讀 ({symbol_name})") 

    if not summary_df.empty:
        # 視覺化表格
        st.dataframe(
            summary_df[['指標名稱', '最新值', '分析結論']],
            hide_index=True,
            use_container_width=True,
            key=f"summary_df_{final_symbol_to_analyze}_{selected_period_key}",
            column_config={
                "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
            }
        )
        st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**（類似低風險買入），**綠色=空頭/削弱信號**（類似高風險賣出），**橙色=中性/警告**）。")

    else:
        st.info("無足夠數據生成關鍵技術指標表格。")
    
    st.markdown("---")
    
    # --- 3. 核心財務與基本面指標 --- **加入 💰 Emoji**
    st.subheader(f"💰 核心財務與基本面指標") 
    
    if info:
        # 提取常用指標
        market_cap = info.get('marketCap')
        trailing_pe = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        dividend_yield = info.get('dividendYield')
        beta = info.get('beta')
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        def format_value(value, is_percentage=False):
            if value is None:
                return "N/A"
            if is_percentage:
                return f"{value * 100:.2f}%"
            if value >= 1_000_000_000:
                return f"${value/1_000_000_000:.2f} B"
            if value >= 1_000_000:
                return f"${value/1_000_000:.2f} M"
            return f"{value:,.2f}"

        col1.metric("市值 (Market Cap)", format_value(market_cap))
        col2.metric("本益比 (Trailing P/E)", format_value(trailing_pe, is_percentage=False))
        col3.metric("預估本益比 (Forward P/E)", format_value(forward_pe, is_percentage=False))
        col4.metric("股息殖利率 (Yield)", format_value(dividend_yield, is_percentage=True))
        col5.metric("Beta (市場波動性)", format_value(beta, is_percentage=False))

    else:
         st.warning("⚠️ 無法獲取資產的基本面/財務資訊。")
         
    st.markdown("---")

    # --- 4. 完整技術分析圖表 --- **加入 📊 Emoji**
    st.subheader(f"📊 完整技術分析圖表")
    chart = create_comprehensive_chart(df, symbol_name, selected_period_key) 
    
    st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    # ==============================================================================
    # 7. 結尾資訊 (免責聲明與數據歸屬)
    # ==============================================================================
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")

# 首次載入或數據未準備好時的提示
elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
     st.info("請在左側選擇或輸入標的，然後點擊 **✨ 開始分析** 按鈕，以查看結果。")
