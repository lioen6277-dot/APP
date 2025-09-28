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

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

st.set_page_config(
    page_title="🤖 AI趨勢分析儀表板 📈", 
    page_icon="📈", 
    layout="wide"
)

PERIOD_MAP = { 
    "30 分 (短期)": ("60d", "30m"), 
    "4 小時 (波段)": ("1y", "60m"), 
    "1 日 (中長線)": ("5y", "1d"), 
    "1 週 (長期)": ("max", "1wk")
}

ALL_ASSETS_MAP = {
    "2330.TW": {"name": "台積電", "category": "台灣股票", "currency": "TWD"},
    "2303.TW": {"name": "聯電", "category": "台灣股票", "currency": "TWD"},
    "2454.TW": {"name": "聯發科", "category": "台灣股票", "currency": "TWD"},
    "2317.TW": {"name": "鴻海", "category": "台灣股票", "currency": "TWD"},
    "2382.TW": {"name": "廣達", "category": "台灣股票", "currency": "TWD"},
    "2881.TW": {"name": "富邦金", "category": "台灣股票", "currency": "TWD"},
    "0050.TW": {"name": "元大台灣50", "category": "台灣ETF", "currency": "TWD"},
    "0056.TW": {"name": "元大高股息", "category": "台灣ETF", "currency": "TWD"},
    "TSE": {"name": "台灣加權指數", "category": "指數", "currency": "TWD"},

    "AAPL": {"name": "蘋果", "category": "美國股票", "currency": "USD"},
    "MSFT": {"name": "微軟", "category": "美國股票", "currency": "USD"},
    "GOOGL": {"name": "Alphabet (Google)", "category": "美國股票", "currency": "USD"},
    "AMZN": {"name": "亞馬遜", "category": "美國股票", "currency": "USD"},
    "NVDA": {"name": "輝達", "category": "美國股票", "currency": "USD"},
    "META": {"name": "Meta Platforms", "category": "美國股票", "currency": "USD"},
    "TSLA": {"name": "特斯拉", "category": "美國股票", "currency": "USD"},
    "JPM": {"name": "摩根大通", "category": "美國股票", "currency": "USD"},
    
    "BTC-USD": {"name": "比特幣/USD", "category": "加密貨幣", "currency": "USD"},
    "ETH-USD": {"name": "以太幣/USD", "category": "加密貨幣", "currency": "USD"},
    "ADA-USD": {"name": "Cardano/USD", "category": "加密貨幣", "currency": "USD"},
    
    "^GSPC": {"name": "S&P 500", "category": "指數", "currency": "USD"},
    "^DJI": {"name": "道瓊指數", "category": "指數", "currency": "USD"},
    "^IXIC": {"name": "納斯達克指數", "category": "USD"},
    "^HSI": {"name": "香港恒生指數", "category": "指數", "currency": "HKD"},

    "SPY": {"name": "標普500 ETF", "category": "美國ETF", "currency": "USD"},
    "QQQ": {"name": "那斯達克100 ETF", "category": "美國ETF", "currency": "USD"},
}

# ==============================================================================
# 2. 輔助函式定義
# ==============================================================================

def get_symbol_from_query(query):
    query = query.strip()
    if not query:
        return st.session_state.get('last_search_symbol', "2330.TW")

    if query.upper() in ALL_ASSETS_MAP:
        return query.upper()

    for symbol, data in ALL_ASSETS_MAP.items():
        if data['name'] == query:
            return symbol

    for symbol, data in ALL_ASSETS_MAP.items():
        if query in data['name']:
            return symbol

    if re.match(r'^\d{4,5}$', query) and f"{query}.TW" in ALL_ASSETS_MAP:
        return f"{query}.TW"

    try:
        if yf.Ticker(query).info.get('regularMarketPrice'):
            return query.upper()
    except:
        pass
        
    return query

@st.cache_data(ttl=3600, show_spinner="正在從 Yahoo Finance 獲取數據...")
def get_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return pd.DataFrame()
        
        df.columns = [col.capitalize() for col in df.columns] 
        df.index.name = 'Date'
        
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return df.iloc[:-1]
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    if symbol in ALL_ASSETS_MAP:
        return ALL_ASSETS_MAP[symbol]
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get('longName') or info.get('shortName') or symbol
        currency = info.get('currency') or "USD"
        return {"name": name, "category": "未分類", "currency": currency}
    except:
        return {"name": symbol, "category": "未分類", "currency": "USD"}
    
@st.cache_data
def get_currency_symbol(symbol):
    currency_code = get_company_info(symbol).get('currency', 'USD')
    if currency_code == 'TWD':
        return 'NT$'
    elif currency_code == 'USD':
        return '$'
    elif currency_code == 'HKD':
        return 'HK$'
    else:
        return currency_code + ' '

def calculate_technical_indicators(df):
    
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['MACD'] = ta.trend.macd_diff(df['Close'])
    df['RSI'] = ta.momentum.rsi(df['Close'])
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['Stoch_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    
    return df

def get_technical_data_df(df):
    
    if df.empty or len(df) < 50: 
        return pd.DataFrame()

    last_row = df.iloc[-1]
    
    indicators = {}
    
    indicators['收盤價 vs SMA-20'] = last_row['Close']
    indicators['收盤價 vs EMA-50'] = last_row['Close']
    
    indicators['RSI (14)'] = last_row['RSI']
    indicators['Stochastics (%K)'] = last_row['Stoch_K']
    indicators['MACD 柱狀圖 (Signal)'] = last_row['MACD']
    
    indicators['ATR (14)'] = last_row['ATR']
    indicators['布林通道 (BB)'] = last_row['Close']
    
    data = []
    
    for name, value in indicators.items():
        conclusion = ""
        color = "grey"
        
        if name == '收盤價 vs SMA-20':
            ma = last_row['SMA_20']
            if value > ma * 1.01:
                conclusion = "多頭：價格強勢站上均線"
                color = "red"
            elif value < ma * 0.99:
                conclusion = "空頭：價格跌破均線"
                color = "green"
            else:
                conclusion = "中性：盤整或趨勢發展中"
                color = "orange"
        
        elif name == '收盤價 vs EMA-50':
            ma = last_row['EMA_50']
            if value > ma * 1.02:
                conclusion = "多頭：中長線趨勢強勁"
                color = "red"
            elif value < ma * 0.98:
                conclusion = "空頭：中長線趨勢疲軟"
                color = "green"
            else:
                conclusion = "中性：中長線盤整"
                color = "orange"

        elif name == 'RSI (14)':
            if value > 70:
                conclusion = "警告：超買區域，潛在回調"
                color = "green" 
            elif value < 30:
                conclusion = "強化：超賣區域，潛在反彈"
                color = "red"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'Stochastics (%K)':
            if value > 80:
                conclusion = "警告：接近超買區域"
                color = "green"
            elif value < 20:
                conclusion = "強化：接近超賣區域"
                color = "red"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'MACD 柱狀圖 (Signal)':
            if value > 0 and last_row['MACD'] > df.iloc[-2]['MACD']:
                conclusion = "強化：多頭動能增強 (金叉趨勢)"
                color = "red"
            elif value < 0 and last_row['MACD'] < df.iloc[-2]['MACD']:
                conclusion = "削弱：空頭動能增強 (死叉趨勢)"
                color = "green"
            else:
                conclusion = "中性：動能盤整"
                color = "orange"
        
        elif name == 'ATR (14)':
            avg_atr = df['ATR'].mean()
            if value > avg_atr * 1.5:
                conclusion = "警告：極高波動性"
                color = "green"
            elif value < avg_atr * 0.5:
                conclusion = "中性：低波動性"
                color = "orange"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == '布林通道 (BB)':
            high = last_row['BB_High']
            low = last_row['BB_Low']
            range_pct = (high - low) / low
            
            if value > high:
                conclusion = "警告：價格位於上軌外側 (超強勢)"
                color = "red"
            elif value < low:
                conclusion = "強化：價格位於下軌外側 (超弱勢)"
                color = "green"
            else:
                conclusion = f"中性：在上下軌間 ({range_pct*100:.2f}% 寬度)"
                color = "blue"
        
        data.append([name, value, conclusion, color])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    technical_df = technical_df.set_index('指標名稱')
    return technical_df

def calculate_fundamental_rating(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        roe = info.get('returnOnEquity', 0)
        payoutRatio = info.get('payoutRatio', 0) 
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)
        marketCap = info.get('marketCap', 1) 
        pe = info.get('trailingPE', 99)
        
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt else 100
        
        roe_score = 0
        if roe > 0.15: roe_score = 3 
        elif roe > 0.08: roe_score = 2
        elif roe > 0: roe_score = 1
        
        pe_score = 0
        if pe < 15: pe_score = 3
        elif pe < 25: pe_score = 2
        elif pe < 35: pe_score = 1
        
        cf_score = 0
        if freeCashFlow > 0.05 * marketCap and cash_debt_ratio > 1.5: cf_score = 3
        elif freeCashFlow > 0 and cash_debt_ratio > 1: cf_score = 2
        elif freeCashFlow > 0: cf_score = 1

        combined_rating = roe_score + pe_score + cf_score
        
        if combined_rating >= 7:
            message = "頂級優異：基本面健康，成長與估值均強勁，適合長期持有。"
        elif combined_rating >= 5:
            message = "良好穩健：財務結構穩固，但可能在成長性或估值方面有所不足。"
        elif combined_rating >= 3:
            message = "中性警示：存在財務壓力或估值過高，需警惕風險。"
        else:
            message = "基本面較弱：財務指標不佳，或數據缺失，不建議盲目進場。"
            
        return {
            "Combined_Rating": combined_rating,
            "Message": message,
            "Details": info
        }

    except Exception as e:
        return {
            "Combined_Rating": 1.0, 
            "Message": f"基本面數據獲取失敗或不適用 (例如指數/加密貨幣)。",
            "Details": None
        }

def generate_expert_fusion_signal(df, fa_rating, is_long_term=True):
    
    if df.empty:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}}

    last_row = df.iloc[-1]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    
    expert_opinions = {}
    
    # 1. 趨勢專家 (均線)
    trend_score = 0
    if last_row['Close'] > last_row['SMA_20'] and last_row['SMA_20'] > last_row['EMA_50']:
        trend_score = 3
        expert_opinions['趨勢分析 (均線)'] = "多頭：短線(SMA)與中長線(EMA)均線呈多頭排列。"
    elif last_row['Close'] < last_row['SMA_20'] and last_row['SMA_20'] < last_row['EMA_50']:
        trend_score = -3
        expert_opinions['趨勢分析 (均線)'] = "空頭：短線與中長線均線呈空頭排列。"
    elif last_row['Close'] > last_row['SMA_20'] or last_row['Close'] > last_row['EMA_50']:
        trend_score = 1
        expert_opinions['趨勢分析 (均線)'] = "中性偏多：價格位於部分均線之上。"
    else:
        trend_score = -1
        expert_opinions['趨勢分析 (均線)'] = "中性偏空：價格位於部分均線之下。"

    # 2. 動能專家 (RSI & Stoch)
    momentum_score = 0
    rsi = last_row['RSI']
    stoch_k = last_row['Stoch_K']
    
    if rsi < 40 and stoch_k < 40:
        momentum_score = 2
        expert_opinions['動能分析 (RSI/Stoch)'] = "強化：動能指標低位，潛在反彈空間大。"
    elif rsi > 60 and stoch_k > 60:
        momentum_score = -2
        expert_opinions['動能分析 (RSI/Stoch)'] = "削弱：動能指標高位，潛在回調壓力大。"
    else:
        momentum_score = 0
        expert_opinions['動能分析 (RSI/Stoch)'] = "中性：指標位於中間區域，趨勢發展中。"

    # 3. 波動性專家 (MACD)
    volatility_score = 0
    macd_diff = last_row['MACD']
    
    if macd_diff > 0 and macd_diff > df.iloc[-2]['MACD']:
        volatility_score = 2
        expert_opinions['波動分析 (MACD)'] = "多頭：MACD柱狀圖擴大，多頭動能強勁。"
    elif macd_diff < 0 and macd_diff < df.iloc[-2]['MACD']:
        volatility_score = -2
        expert_opinions['波動分析 (MACD)'] = "空頭：MACD柱狀圖擴大，空頭動能強勁。"
    else:
        volatility_score = 0
        expert_opinions['波動分析 (MACD)'] = "中性：MACD柱狀圖收縮，動能盤整。"

    # 4. K線形態專家 (簡單判斷)
    kline_score = 0
    is_up_bar = last_row['Close'] > last_row['Open']
    is_strong_up = is_up_bar and (last_row['Close'] - last_row['Open']) > atr_value * 0.5
    is_strong_down = not is_up_bar and (last_row['Open'] - last_row['Close']) > atr_value * 0.5

    if is_strong_up:
        kline_score = 1.5
        expert_opinions['K線形態分析'] = "強化：實體大陽線，買盤積極。"
    elif is_strong_down:
        kline_score = -1.5
        expert_opinions['K線形態分析'] = "削弱：實體大陰線，賣壓沉重。"
    else:
        kline_score = 0
        expert_opinions['K線形態分析'] = "中性：K線實體小，觀望。"

    fusion_score = trend_score + momentum_score + volatility_score + kline_score + (fa_rating / 9) * 3
    
    action = "觀望 (Neutral)"
    
    if fusion_score >= 4.5:
        action = "買進 (Buy)"
    elif fusion_score >= 1.5:
        action = "中性偏買 (Hold/Buy)"
    elif fusion_score <= -4.5:
        action = "賣出 (Sell/Short)"
    elif fusion_score <= -1.5:
        action = "中性偏賣 (Hold/Sell)"
        
    confidence = min(100, max(0, 50 + fusion_score * 5))
    
    risk_multiple = 2.0 if is_long_term else 1.5
    reward_multiple = 2.0
    
    if action in ["買進 (Buy)", "中性偏買 (Hold/Buy)"]:
        entry = current_price * 0.99 
        stop_loss = entry - (atr_value * risk_multiple)
        take_profit = entry + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，考慮在{atr_value:.4f}波動範圍內尋找進場點。"
    elif action in ["賣出 (Sell/Short)", "中性偏賣 (Hold/Sell)"]:
        entry = current_price * 1.01
        stop_loss = entry + (atr_value * risk_multiple)
        take_profit = entry - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，考慮在{atr_value:.4f}波動範圍內尋找進場點。"
    else:
        entry = current_price
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value
        strategy_desc = "市場信號混亂，建議等待趨勢明朗或在區間內操作。"

    return {
        'action': action,
        'score': round(fusion_score, 2),
        'confidence': round(confidence, 0),
        'strategy': strategy_desc,
        'entry_price': entry,
        'take_profit': take_profit,
        'stop_loss': stop_loss,
        'current_price': current_price,
        'expert_opinions': expert_opinions,
        'atr': atr_value
    }

def create_comprehensive_chart(df, symbol, period_key):
    
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.08,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=(f"{symbol} 價格走勢 (週期: {period_key})", "MACD 指標", "RSI 指標"))

    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name='K線',
                                 increasing_line_color='#cc0000', decreasing_line_color='#1e8449'), 
                  row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='blue', width=1), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='grey', width=1, dash='dot'), name='BB 上軌'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='grey', width=1, dash='dot'), name='BB 下軌'), row=1, col=1)
    
    colors = np.where(df['MACD'] > 0, '#cc0000', '#1e8449') 
    fig.add_trace(go.Bar(x=df.index, y=df['MACD'], name='MACD 柱狀圖', marker_color=colors), row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

# Streamlit 側邊欄函數
def update_search_input():
    selected_display = st.session_state.symbol_select_box
    symbol = selected_display.split(' ')[0] 
    st.session_state['sidebar_search_input'] = symbol
    st.session_state['analyze_trigger'] = True

# ==============================================================================
# 3. Streamlit 主邏輯 (Main Function)
# ==============================================================================

def main():
    # --- 0. 靜態側邊欄選擇器 (Category Selectbox) 移入 main() ---
    category_options = list(set(data['category'] for data in ALL_ASSETS_MAP.values()))
    category_options.sort(key=lambda x: ("台灣" not in x, x)) 
    
    selected_category = st.sidebar.selectbox("1. 選擇資產類別", category_options)

    current_category_options_display = []
    for symbol, data in ALL_ASSETS_MAP.items():
        if data['category'] == selected_category:
            current_category_options_display.append(f"{symbol} ({data['name']})")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("2. **選擇標的**")
    
    # --- 1. 找出當前 symbol 是否在列表中的預設值 ---
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

    # --- 3. 輸入股票代碼或中文名稱 (Text Input) ---
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

    # --- 4. 選擇週期 (Period Selectbox) ---
    st.sidebar.markdown("4. **選擇週期**")

    period_keys = list(PERIOD_MAP.keys())
    selected_period_key = st.sidebar.selectbox("分析時間週期", period_keys, index=period_keys.index("1 日 (中長線)")) 

    selected_period_value = PERIOD_MAP[selected_period_key]

    yf_period, yf_interval = selected_period_value

    is_long_term = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]

    st.sidebar.markdown("---")

    # --- 5. 開始分析 (Button) ---
    st.sidebar.markdown("5. **開始分析**")
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", type="primary", key="main_analyze_button") 

    # === 主要分析邏輯 (Main Analysis Logic) ===
    if analyze_button_clicked or st.session_state.get('analyze_trigger', False):
        
        st.session_state['data_ready'] = False
        st.session_state['analyze_trigger'] = False 
        
        try:
            with st.spinner(f"🔍 正在啟動AI模型，獲取並分析 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
                
                df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
                
                if df.empty:
                    display_symbol = final_symbol_to_analyze
                    
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

    # === 結果呈現區塊 ===
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
