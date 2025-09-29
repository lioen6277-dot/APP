import streamlit as st
import yfinance as yf
# ... (其他 import 保持不變)
# ... (其他函數定義保持不變)

def main():
    
    # === 新增自定義 CSS 來實現玻璃按鍵效果和橙色文字 ===
    st.markdown("""
        <style>
        /* 1. 側邊欄的主要分析按鈕 - 核心玻璃化設置 (將顏色改為 #ff9933) */
        [data-testid="stSidebar"] .stButton button {
            color: #ff9933 !important; /* 🔥 亮橙色文字 */
            background-color: rgba(255, 255, 255, 0.1) !important; /* 透明背景 */
            border-color: #ff9933 !important; /* 🔥 亮橙色邊框 */
            
            /* 【核心修改 1】 增強邊框厚度 */
            border-width: 2px !important; 
            
            /* 【核心修改 2】 增強靜態陰影 */
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2), 0 2px 4px rgba(0, 0, 0, 0.1); 
            
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        /* 2. 懸停 (Hover) 效果 */
        [data-testid="stSidebar"] .stButton button:hover {
            color: #cc6600 !important; 
            /* 【核心修改 3】 懸停時背景色更飽和 */
            background-color: rgba(255, 153, 51, 0.25) !important; 
            border-color: #cc6600 !important;
            
            /* 【核心修改 4】 懸停時陰影更突出 (上浮效果) */
            box-shadow: 0 8px 15px rgba(255, 153, 51, 0.4), 0 3px 6px rgba(0, 0, 0, 0.15); 
        }
        
        /* 3. 點擊 (Active/Focus) 效果 */
        [data-testid="stSidebar"] .stButton button:active,
        [data-testid="stSidebar"] .stButton button:focus {
            color: #ff9933 !important;
            background-color: rgba(255, 153, 51, 0.4) !important; /* 點擊時背景更深 */
            border-color: #ff9933 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) inset !important; /* 點擊時內凹效果 */
        }
        
        /* 4. 修正主標題顏色 */
        h1 { color: #cc6600; } 
        
        /* 5. 因子分解表格標題顏色 (XAI/Transparency) */
        .factor-score-table th { background-color: rgba(204, 102, 0, 0.3) !important; }
        /* 修正：統一多頭信號顏色 */
        .factor-score-positive { color: #cc6600; font-weight: bold; } 
        .action-buy { color: #cc6600; font-weight: bold; }
        .action-sell { color: #1e8449; font-weight: bold; }
        .action-neutral { color: #0077b6; font-weight: bold; } /* 中性改為藍色 */
        .factor-score-negative { color: #1e8449; font-weight: bold; }
        .factor-score-neutral { color: #0077b6; }
        </style>
        """, unsafe_allow_html=True)

    # ... (後續的 Streamlit 邏輯保持不變)
    # ...
    
    # --- 5. 開始分析 (Button) ---
    st.sidebar.markdown("5. **開始分析**")
    
    # 此按鈕會受益於上述 CSS 調整
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", key="main_analyze_button") 
    
    # ... (後續的分析和結果呈現邏輯保持不變)
    # ...

    # === 未分析時的預設首頁顯示 (維持 #ff9933 顏色) ===
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          
          st.markdown(
              """
              <h1 style='color: #ff9933; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析</h1>
              """, 
              unsafe_allow_html=True
          )
          
          st.markdown(f"請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 <span style='color: #ff9933; font-weight: bold;'>『📊 執行AI分析』</span> 按鈕開始。", unsafe_allow_html=True)
          
          st.markdown("---")
          
          st.subheader("📝 使用步驟：")
          st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
          st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
          st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分 (短期)`、`1 日 (中長線)`）。")
          st.markdown(f"4. **執行分析**：點擊 <span style='color: #ff9933; font-weight: bold;'>『📊 執行AI分析』**</span>，AI將融合基本面與技術面指標提供交易策略。", unsafe_allow_html=True)
          
          st.markdown("---")


if __name__ == '__main__':
# ... (Session State 初始化保持不變)
    main()
    
    # 🚨 綜合免責聲明區塊
    st.markdown("---")
# ... (免責聲明保持不變)
