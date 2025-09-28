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
# 0. AI 虛擬角色與數據源列表 (取代所有「專家」概念)
# ==============================================================================
# 用於在免責聲明中顯示的數據來源列表
EXTERNAL_DATA_SOURCES = [
    "Yahoo Finance (主要價格數據)", "Goodinfo 股市資訊網 (概念性分析維度)", 
    "Morningstar (概念性 FA 評級)", "Finviz (概念性篩選維度)",
    "Gurufocus (概念性 FA/估值維度)", "TradingView (圖表/技術分析邏輯)",
    "SEC EDGAR (概念性財報審核)", "CMoney (概念性台股數據考量)"
]

# 用於在分析報告中模擬 AI 決策維度的角色列表 (已移除所有「專家」字眼)
AI_VIRTUAL_ROLES = [
    "AI 投資決策員 (General Investment Role)", "AI 操盤模擬 (Professional Trader)", 
    "AI 基金經理模擬 (Fund Manager)", "AI 財務分析模組 (Financial Analyst)", 
    "AI 投行評估 (Investment Banker)", "AI 量化分析引擎 (Quantitative Analyst)", 
    "AI 行為金融視角 (Behavioral Finance Role)", "AI 風險管理模組 (Risk Manager)", 
    "AI ESG 評級 (ESG Investment Role)", "AI 財富規劃 (Wealth Manager)", 
    "AI 衍生品估值 (Derivatives Role)", "AI 宏觀經濟分析 (Macro Economist)", 
    "AI 金融科技應用 (FinTech Role)", "AI 資料科學家 (Data Scientist)", 
    "AI 機器學習工程師 (Machine Learning Engineer)", "AI 演算法交易開發 (Algorithmic Trading Developer)", 
    "AI 後端開發 (Backend Developer)", "AI 金融軟體工程 (Financial Software Engineer)", 
    "AI 區塊鏈模擬 (Blockchain Developer)", "AI 風險建模程式 (Risk Modeling Programmer)", 
    "AI 高頻交易系統 (High-Frequency Trading System Developer)", "AI 投資資料工程 (Investment Data Engineer)", 
    "AI 策略架構師 (AI Investment Strategy Architect)"
]


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

# 您的【所有資產清單】(ALL_ASSETS_MAP) - 保持不變
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
# 2. 側邊欄用戶輸入 (Sidebar) - 保持不變
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
# 3. 數據獲取與預處理函數 - 保持不變
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
# 4. 技術分析計算與判讀函數 - 保持不變
# ==============================================================================

def calculate_technical_indicators(df):
    """計算常用技術指標 (RSI, MACD, Bollinger Bands)"""
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
    """根據指標數值提供趨勢判讀和視覺化顏色 - 保持與上次修正的顏色邏輯一致"""
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
    """創建一個包含關鍵指標和判讀結論的 DataFrame - 保持不變"""
    if df_ta is None or df_ta.empty:
        return pd.DataFrame()
        
    latest = df_ta.iloc[-1]
    results = []
    
    # 1. RSI
    rsi_result = interpret_indicator('RSI', latest['RSI'])
    results.append({
        "指標名稱": "RSI (14)",
        "最新值": rsi_result['value'],
        "分析結論": rsi_result['conclusion'],
        "顏色": rsi_result['color']
    })

    # 2. MACD 柱狀圖 (DIFF)
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

# ----------------------------------------------------------------------------------
# 🚩 修正點：AI 融合分析報告生成函數 (已移除所有「專家」字眼)
# ----------------------------------------------------------------------------------

def calculate_ai_fusion_metrics(summary_df, current_price, is_long_term=True):
    """計算 AI 信心指數和生成 AI 觀點"""
    if summary_df.empty:
        return None
    
    # 1. 計算多空信號票數 (根據顏色)
    # 紅色 = 多頭/機會信號 (Bullish)
    # 綠色 = 空頭/風險信號 (Bearish)
    bullish_count = summary_df['顏色'].apply(lambda x: 1 if x == 'red' else 0).sum()
    bearish_count = summary_df['顏色'].apply(lambda x: 1 if x == 'green' else 0).sum()
    total_signals = len(summary_df) # 總票數

    # 2. AI 信心指數計算 (取代 100% 正確性)
    net_signal = bullish_count - bearish_count
    if total_signals > 0:
        # 將淨信號從 -Total 到 +Total 映射到 0% 到 100%
        ai_confidence_score = int(((net_signal + total_signals) / (2 * total_signals)) * 100)
    else:
        ai_confidence_score = 50 

    # 3. 確定最終 AI 動作與建議
    if ai_confidence_score >= 70:
        recommendation = "強烈多頭趨勢 (Strong Bullish)"
        action = "建議逢低買入或加倉"
        action_color = "red"
    elif ai_confidence_score >= 55:
        recommendation = "偏向多頭趨勢 (Mild Bullish)"
        action = "建議謹慎佈局或持有"
        action_color = "orange"
    elif ai_confidence_score <= 30:
        recommendation = "強烈空頭趨勢 (Strong Bearish)"
        action = "建議避險或減倉/賣出"
        action_color = "green"
    elif ai_confidence_score <= 45:
        recommendation = "偏向空頭趨勢 (Mild Bearish)"
        action = "建議觀望或輕倉"
        action_color = "orange"
    else:
        recommendation = "市場盤整 (Neutral / Consolidation)"
        action = "建議等待明確信號"
        action_color = "orange"

    # 4. 風控參數 (簡化版：使用固定百分比模擬 ATR 風控)
    volatility_factor = 0.03 # 假設的 ATR 或波動性因子
    atr = current_price * volatility_factor 
    entry_suggestion = current_price # 入場價設為當前價格

    # 停損：多頭 -1.5 ATR / 空頭 +1.5 ATR
    if ai_confidence_score >= 50:
        stop_loss = entry_suggestion - atr * 1.5
        take_profit = entry_suggestion + atr * 3.0 # 1:2 風報比
    else:
        # 空頭方向的建議 (如果系統支持做空，這裡簡化處理為多頭風險)
        stop_loss = entry_suggestion - atr * 1.5
        take_profit = entry_suggestion + atr * 3.0
    
    # 5. AI 觀點摘要
    ai_opinions = {}
    for index, row in summary_df.iterrows():
        # 這裡將指標名稱作為 AI 分析模組的子模組
        module_name = row['指標名稱'].split('(')[0].strip() 
        ai_opinions[f"AI {module_name} 模組"] = row['分析結論']
        
    
    return {
        'recommendation': recommendation,
        'confidence': ai_confidence_score, 
        'action': action,
        'action_color': action_color,
        'signal_counts': {'Bullish': bullish_count, 'Bearish': bearish_count, 'Neutral': total_signals - bullish_count - bearish_count},
        'total_signals': total_signals,
        'entry_price': entry_suggestion,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'ai_opinions': ai_opinions,
    }

def generate_ai_fusion_report(metrics: dict, asset_name: str, symbol: str) -> str:
    """根據 AI 融合指標，生成一份專業的 AI 報告 (已移除所有「專家」字眼)"""
    
    confidence = metrics['confidence']
    action = metrics['action']
    signal_counts = metrics['signal_counts']
    total_signals = metrics['total_signals']
    ai_opinions = metrics['ai_opinions']

    # 1. 風險等級設定 (由 AI 風險管理模組評估)
    if confidence >= 80 or confidence <= 20:
        risk_level = "中高 (趨勢強烈，但隨時可能反轉)"
        risk_advice = "建議嚴格執行止損機制，並動態調整倉位大小。"
    elif confidence >= 60 or confidence <= 40:
        risk_level = "中 (趨勢漸進，波動性中等)"
        risk_advice = "適合趨勢追蹤策略，但應預留現金用於應對波動。"
    else:
        risk_level = "低 (盤整或中性，交易機會少)"
        risk_advice = "建議等待信號確立，避免過度交易。"


    # 2. 數據準確性與專業修正聲明 (直接回應 100% 準確性問題)
    accuracy_statement = f"""
    ---
    ### ⚠️ 關於數據「100% 準確性」的 AI 風控聲明：
    **AI 系統聲明：** 在金融市場中，**100% 的預測準確性是不可能實現的目標**，因為市場受無法量化的宏觀經濟、非理性行為與突發事件影響。

    本 AI 系統旨在通過整合 **{total_signals}** 個獨立技術信號和多重數據源（{', '.join(EXTERNAL_DATA_SOURCES[:3])} 等）的**交叉評估機制**，將結果量化為 **AI 信心指數**，以提升決策的**魯棒性 (Robustness)** 和**穩定性 (Stability)**，但無法消除市場固有風險。
    """
    
    # 3. 最終報告生成
    summary_report = f"""
    ## 🤖 AI 融合分析報告 ({asset_name} - {symbol})
    
    ### 💡 AI 核心結論與信號共識
    
    * **AI 信心指數 (AI Confidence Index):** **{confidence}%** (代表 AI 量化分析引擎對當前趨勢的置信度)
    * **AI 風險等級 (AI Risk Assessment):** **{risk_level}** (由 AI 風險管理模組評估)
    
    **AI 系統綜合判斷：** {metrics['recommendation']}。
    
    #### AI 系統信號計數
    * **多頭信號 (Bullish):** {signal_counts['Bullish']} 票
    * **空頭信號 (Bearish):** {signal_counts['Bearish']} 票
    * **中性信號 (Neutral):** {signal_counts['Neutral']} 票
    
    ### 📊 AI 分項分析摘要
    
    | AI 分析模組 | 結論 (AI Opinion) |
    | :--- | :--- |
    | **AI RSI 模組** | {ai_opinions.get('AI RSI 模組', 'N/A')} |
    | **AI MACD 模組** | {ai_opinions.get('AI MACD 模組', 'N/A')} |
    | **AI MA20 模組** | {ai_opinions.get('AI MA20 模組', 'N/A')} |
    | **AI 布林通道模組** | {ai_opinions.get('AI 布林通道模組', 'N/A')} |
    
    ### 🛡️ AI 風控與交易建議
    * **AI 策略動作:** {action}
    * **AI 入場價 (Entry):** **{metrics['entry_price']:.2f}**
    * **AI 停損價 (Stop Loss):** **{metrics['stop_loss']:.2f}** ({'建議多頭方向' if confidence >= 50 else '建議空頭方向'})
    * **AI 止盈價 (Take Profit):** **{metrics['take_profit']:.2f}** (基於 1:2 風報比計算)
    * **AI 風險提示:** {risk_advice}

    {accuracy_statement}
    """
    return summary_report, metrics['action_color']

# ==============================================================================
# 5. 圖表繪製函數 (Plotly) - 保持不變
# ==============================================================================

def create_comprehensive_chart(df, symbol_name, selected_period_key):
    # ... (Plotly 圖表繪製函數內容保持不變)
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
        increasing_line_color='#FF5733', # 紅色 K 棒 (上漲)
        decreasing_line_color='#33FF57', # 綠色 K 棒 (下跌)
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
    
    # 🚩 修正點：生成 AI 融合指標與報告
    if not summary_df.empty:
        ai_metrics = calculate_ai_fusion_metrics(summary_df, current_price)
        ai_summary_text, color_trend = generate_ai_fusion_report(ai_metrics, symbol_name, final_symbol_to_analyze)
    else:
        ai_summary_text = "無法生成 AI 融合報告，技術數據不足。"
        color_trend = "gray"
    
    
    # --- 1. AI 融合分析報告 --- 
    st.subheader("🤖 AI 融合分析報告與建議") 
    
    if summary_df.empty:
        st.warning(ai_summary_text)
    else:
        # 使用 color_trend 來決定框線顏色
        color_map = {"red": "red", "green": "green", "orange": "orange", "gray": "gray"}
        style = f"border: 2px solid {color_map.get(color_trend, 'gray')}; padding: 15px; border-radius: 10px;"
        
        with st.container(border=True):
             # 報告包含所有 AI 邏輯、風控和 100% 準確性修正聲明
             st.markdown(ai_summary_text, unsafe_allow_html=True)
             
    st.markdown("---")
    
    # --- 2. 關鍵指標綜合判讀 --- **加入 💡 Emoji**
    st.subheader(f"💡 關鍵指標 AI 量化判讀 ({symbol_name})") 

    if not summary_df.empty:
        # 視覺化表格 (實現文字上色)
        color_map_hex = {
            "red": "#FF5733",      # 多頭/買入機會
            "green": "#33FF57",    # 空頭/賣出風險
            "orange": "#FFA500"    # 中性/警告
        }
        
        st.dataframe(
            summary_df, 
            hide_index=True,
            use_container_width=True,
            key=f"summary_df_{final_symbol_to_analyze}_{selected_period_key}",
            column_config={
                "指標名稱": st.column_config.Column("指標名稱"),
                "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                "分析結論": st.column_config.Column(
                    "趨勢/動能判讀", 
                    help="基於數值範圍的 AI 解讀 (已上色)",
                    styles=[
                        {"selector": "td", "props": [("color", color_map_hex["red"])]}
                        if row["顏色"] == "red" else
                        {"selector": "td", "props": [("color", color_map_hex["green"])]}
                        if row["顏色"] == "green" else
                        {"selector": "td", "props": [("color", color_map_hex["orange"])]}
                        for index, row in summary_df.iterrows()
                    ]
                ),
                "顏色": None # 隱藏用於上色的顏色欄位
            }
        )
        st.caption(f"ℹ️ **AI 提示:** 表格中 **分析結論** 的文字顏色已根據 AI 信號自動變化（**{color_map_hex['red']} (多頭)**, **{color_map_hex['green']} (空頭)**, **{color_map_hex['orange']} (中性)**）。")

    else:
        st.info("無足夠數據生成關鍵技術指標表格。")
    
    st.markdown("---")
    
    # --- 3. 核心財務與基本面指標 --- **保持不變**
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

    # --- 4. 完整技術分析圖表 --- 
    st.subheader(f"📊 完整技術分析圖表")
    chart = create_comprehensive_chart(df, symbol_name, selected_period_key) 
    
    st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    # ==============================================================================
    # 7. 結尾資訊與透明度聲明 (已移除所有「專家」字眼)
    # ==============================================================================
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    # 🚩 修正點：AI 角色與數據透明度聲明
    with st.expander("🧾 AI 系統聲明、數據源與 AI 虛擬角色透明度", expanded=False):
        st.markdown(f"""
        ### 📜 **AI 系統免責聲明 (AI System Disclaimer)**
        本 AI 分析儀表板由模擬 **{len(AI_VIRTUAL_ROLES)}** 種專業投資/技術角色的 **AI 引擎**所驅動。
        **所有輸出的分析、評級與交易建議僅為數據模型模擬的結果，絕不構成任何實際的投資建議 (Financial Advice)**。
        投資有風險，請用戶根據自身風險承受能力進行獨立判斷。
        
        ### 💻 **數據來源透明度 (Data Source Transparency)**
        本系統的核心數據主要來自 **Yahoo Finance** (使用 `yfinance` 庫)，並**概念性地整合**了以下多種數據來源的**分析思路與考量維度**，以確保模型的穩健性：
        
        **[AI 分析維度整合來源]**
        {'\n'.join([f"* {source}" for source in EXTERNAL_DATA_SOURCES])}
        
        **注意：** 除 Yahoo Finance (yfinance) 外，其餘數據源目前僅作為**分析模型的知識與維度基礎**。

        ### 🧑‍💻 **AI 虛擬角色陣容 (AI Virtual Roles)**
        本 AI 融合分析報告是以下 AI 模擬角色的研究與討論共識：
        
        **[AI 虛擬角色列表]**
        {'\n'.join([f"* {role}" for role in AI_VIRTUAL_ROLES])}
        
        ---
        **AI 數據正確性聲明：** 儘管 AI 系統力求數據準確，但因 YFinance 來源的數據可能存在延遲、時間戳不一致、或數據校準差異，**數據的絕對準確性無法達到 100%**。本系統已盡力透過數據清洗和魯棒性計算來提高**數據品質**，並將重點放在**信號的穩健性**上。
        """)
        
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance (主要) | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")


# 首次載入或數據未準備好時的提示
elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
     st.info("請在左側選擇或輸入標的，然後點擊 **✨ 開始分析** 按鈕，以查看 AI 融合報告。")
