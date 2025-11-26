<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 趨勢分析與專業操盤計算器</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'Noto Sans TC', 'sans-serif'],
                    },
                    colors: {
                        'primary-dark': '#1e293b',
                        'secondary-light': '#f8fafc',
                        'accent-green': '#10b981', // Emerald green for reward
                        'accent-red': '#ef4444',   // Red for risk
                        'accent-blue': '#3b82f6',  // Blue for AI
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', 'Noto Sans TC', sans-serif; }
    </style>
</head>
<body class="bg-gray-900 text-secondary-light min-h-screen p-4 sm:p-8">

    <div class="max-w-6xl mx-auto">
        <header class="mb-8 text-center">
            <h1 class="text-3xl sm:text-4xl font-extrabold text-white mb-2">AI 趨勢分析與專業策略驗證</h1>
            <p class="text-gray-400">宏觀趨勢定性 (AI) 結合微觀結構風控 (計算器)</p>
        </header>

        <main class="grid grid-cols-1 lg:grid-cols-5 gap-8">

            <!-- 左側區塊：AI 趨勢分析器 (佔 3/5 寬度) -->
            <div class="lg:col-span-3 bg-primary-dark p-6 sm:p-8 rounded-xl shadow-2xl space-y-6">
                <h2 class="text-2xl font-bold border-b border-gray-700 pb-3 text-accent-blue flex items-center">
                    <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-4-4m5-4a5 5 0 11-10 0 5 5 0 0110 0zm0 0l-1.5-1.5m1.5 1.5l1.5-1.5M10.5 13.5l1.5-1.5m-1.5 1.5l1.5 1.5"></path></svg>
                    區塊一：AI 趨勢判斷與市場定性 (RSI / MACD 輔助)
                </h2>

                <div>
                    <label for="aiPrompt" class="block text-sm font-medium mb-1">輸入您想分析的標的物或市場問題（例如：TSLA, BTC, 黃金的最新季度表現）</label>
                    <textarea id="aiPrompt" rows="3" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-blue focus:border-accent-blue transition duration-150 resize-y" placeholder="請輸入分析指令..."></textarea>
                </div>

                <button id="analyzeButton" class="w-full py-3 bg-accent-blue hover:bg-blue-600 text-white font-bold rounded-lg transition duration-200 flex items-center justify-center">
                    <svg class="w-5 h-5 mr-2 animate-spin hidden" id="loadingSpinner" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m15.356-2A8.001 8.001 0 004.582 15m15.356-2H12"></path></svg>
                    開始 AI 趨勢分析
                </button>

                <div id="aiResults" class="mt-6 p-4 bg-gray-800 rounded-lg min-h-[150px]">
                    <h3 class="text-xl font-semibold mb-3 text-yellow-300">分析結果</h3>
                    <p id="analysisText" class="text-gray-300">AI 分析結果將顯示在此處。請務必結合您的 RSI/MACD 分析進行趨勢定性。</p>
                    <div id="citations" class="mt-4 border-t border-gray-700 pt-3">
                        <p class="text-sm text-gray-500 font-medium">資料來源 (Grounding Sources):</p>
                        <ul id="sourceList" class="list-disc list-inside text-xs text-gray-400 mt-1 space-y-1">
                            <!-- 來源將在此處顯示 -->
                        </ul>
                    </div>
                </div>
            </div>

            <!-- 右側區塊：策略計算器 (佔 2/5 寬度) -->
            <div class="lg:col-span-2 bg-primary-dark p-6 sm:p-8 rounded-xl shadow-2xl space-y-6">
                <h2 class="text-2xl font-bold border-b border-gray-700 pb-3 text-yellow-400 flex items-center">
                    <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c1.657 0 3 .895 3 2s-1.343 2-3 2v2m0 0V8m0 4v2m0 0V8m0 4c-1.657 0-3-.895-3-2s1.343-2 3-2V8"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h.01M17 7h.01M7 7h.01M7 17h.01M12 7h.01M12 17h.01M17 12h.01M7 12h.01M12 12h.01"></path></svg>
                    區塊二：風控與目標設定驗證
                </h2>

                <!-- 輸入區 Input Section -->
                <div class="space-y-4">
                    <!-- 開單價位 Entry Price -->
                    <div>
                        <label for="entryPrice" class="block text-sm font-medium mb-1">1. 開單價位 (Entry)</label>
                        <input type="number" id="entryPrice" value="100.00" step="0.01" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-green focus:border-accent-green">
                    </div>

                    <!-- 結構止損錨定 Structural Anchor for SL -->
                    <div>
                        <label for="swingAnchor" class="block text-sm font-medium mb-1">2. 止損結構錨點 (前一個有效震盪低點)</label>
                        <input type="number" id="swingAnchor" value="95.00" step="0.01" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-green focus:border-accent-green">
                    </div>

                    <!-- ATR 緩衝設定 ATR Buffer -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label for="atrValue" class="block text-sm font-medium mb-1">3. ATR 波動值</label>
                            <input type="number" id="atrValue" value="0.50" step="0.01" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-green focus:border-accent-green">
                        </div>
                        <div>
                            <label for="atrMultiplier" class="block text-sm font-medium mb-1">4. ATR 緩衝倍數 (例如 1.5)</label>
                            <input type="number" id="atrMultiplier" value="1.50" step="0.1" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-green focus:border-accent-green">
                        </div>
                    </div>

                    <!-- 止盈目標 Take Profit Target -->
                    <div>
                        <label for="tpTarget" class="block text-sm font-medium mb-1">5. 主要止盈目標 (TP2, 例如 1.618 擴展)</label>
                        <input type="number" id="tpTarget" value="125.00" step="0.01" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-lg focus:ring-accent-green focus:border-accent-green">
                    </div>
                </div>

                <!-- 結果區 Result Section -->
                <div id="results" class="bg-gray-800 p-5 rounded-lg shadow-inner space-y-4">
                    <!-- 計算結果將在這裡顯示 -->
                </div>

                <div id="rrValidation" class="p-3 rounded-lg text-center font-extrabold text-xl shadow-md">
                    <!-- R:R 驗證結果 -->
                </div>
            </div>

        </main>
    </div>

    <script>
        const apiKey = ""; // API Key 設置為空字串，將由運行環境提供
        const modelUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent";
        
        // --- 區塊一：AI 分析邏輯 ---
        const analyzeButton = document.getElementById('analyzeButton');
        const aiPrompt = document.getElementById('aiPrompt');
        const analysisText = document.getElementById('analysisText');
        const sourceList = document.getElementById('sourceList');
        const loadingSpinner = document.getElementById('loadingSpinner');

        // Helper for Exponential Backoff
        const MAX_RETRIES = 5;

        // Helper function for fetching with retry logic
        async function fetchWithRetry(url, options, retries = 0) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                if (retries < MAX_RETRIES) {
                    const delay = Math.pow(2, retries) * 1000;
                    // console.log(`Retrying after ${delay}ms... (Attempt ${retries + 1})`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return fetchWithRetry(url, options, retries + 1);
                }
                throw error;
            }
        }

        async function analyzeTrend() {
            const userQuery = aiPrompt.value.trim();
            if (!userQuery) {
                analysisText.textContent = "請輸入有效的查詢內容。";
                return;
            }

            // UI feedback
            analyzeButton.disabled = true;
            loadingSpinner.classList.remove('hidden');
            analysisText.textContent = "正在進行市場分析，請稍候...";
            sourceList.innerHTML = '';

            const systemPrompt = "您是一位專門且中立的金融市場趨勢分析師。請基於最新的市場資訊和數據，提供關於使用者查詢標的物的趨勢分析，重點關注近期動能和結構性變化，並以一個精簡、專業的單一自然段落中文總結。";
            
            // Construct the payload
            const payload = {
                contents: [{ parts: [{ text: userQuery }] }],
                tools: [{ "google_search": {} }], // 啟用 Google 搜尋接地
                systemInstruction: {
                    parts: [{ text: systemPrompt }]
                },
            };

            const options = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            };

            try {
                const result = await fetchWithRetry(`${modelUrl}?key=${apiKey}`, options);
                const candidate = result.candidates?.[0];

                if (candidate && candidate.content?.parts?.[0]?.text) {
                    const text = candidate.content.parts[0].text;
                    analysisText.textContent = text;

                    // Extract grounding sources
                    let sources = [];
                    const groundingMetadata = candidate.groundingMetadata;
                    if (groundingMetadata && groundingMetadata.groundingAttributions) {
                        sources = groundingMetadata.groundingAttributions
                            .map(attribution => ({
                                uri: attribution.web?.uri,
                                title: attribution.web?.title,
                            }))
                            .filter(source => source.uri && source.title); // Ensure sources are valid
                    }

                    // Display sources
                    if (sources.length > 0) {
                        sourceList.innerHTML = sources.map((s, index) => `
                            <li>
                                <a href="${s.uri}" target="_blank" class="text-blue-400 hover:text-blue-300 transition duration-150 truncate block">${index + 1}. ${s.title}</a>
                            </li>
                        `).join('');
                    } else {
                        sourceList.innerHTML = '<li>無外部資料來源引用。</li>';
                    }

                } else {
                    analysisText.textContent = "未能生成有效的分析結果。請嘗試調整查詢內容。";
                }

            } catch (error) {
                console.error("API 呼叫失敗:", error);
                analysisText.textContent = `API 呼叫失敗，請檢查網路或稍後重試。錯誤: ${error.message}`;
            } finally {
                // Reset UI state
                analyzeButton.disabled = false;
                loadingSpinner.classList.add('hidden');
            }
        }

        analyzeButton.addEventListener('click', analyzeTrend);


        // --- 區塊二：專業操盤計算器邏輯 ---
        const inputs = ['entryPrice', 'swingAnchor', 'atrValue', 'atrMultiplier', 'tpTarget'];
        const resultsDiv = document.getElementById('results');
        const rrValidationDiv = document.getElementById('rrValidation');
        const tradingDirection = 'LONG'; // 固定為多單 LONG 範例

        // Helper function to format numbers to 2 decimal places
        const formatCurrency = (num) => parseFloat(num).toFixed(2);

        function calculateStrategy() {
            const entryPrice = parseFloat(document.getElementById('entryPrice').value);
            const swingAnchor = parseFloat(document.getElementById('swingAnchor').value);
            const atrValue = parseFloat(document.getElementById('atrValue').value);
            const atrMultiplier = parseFloat(document.getElementById('atrMultiplier').value);
            const tpTarget = parseFloat(document.getElementById('tpTarget').value);

            if (isNaN(entryPrice) || isNaN(swingAnchor) || isNaN(atrValue) || isNaN(atrMultiplier) || isNaN(tpTarget)) {
                resultsDiv.innerHTML = '<p class="text-red-500">請輸入所有有效的數值。</p>';
                rrValidationDiv.className = 'p-3 rounded-lg text-center font-extrabold text-xl shadow-md';
                rrValidationDiv.textContent = '等待輸入...';
                return;
            }

            let structuralSL, atrBuffer, finalSL, risk, reward, rrRatio;

            // 1. 計算 ATR 緩衝區
            atrBuffer = atrValue * atrMultiplier;

            if (tradingDirection === 'LONG') {
                // 多單 (買入) 止損應在結構錨點下方
                structuralSL = swingAnchor;
                finalSL = structuralSL - atrBuffer;
                
                // 計算風險與回報
                risk = entryPrice - finalSL;
                reward = tpTarget - entryPrice;

            } else { 
                // 為了簡化，這裡僅提供 LONG 的計算邏輯。若需 SHORT，請參考註釋。
                structuralSL = swingAnchor;
                finalSL = structuralSL + atrBuffer;
                risk = finalSL - entryPrice;
                reward = entryPrice - tpTarget;
            }
            
            // 計算風險報酬比 (R:R)
            rrRatio = risk > 0 ? reward / risk : 0; // 避免除以零


            // --- 輸出結果 ---
            let riskClass = risk > 0 ? 'text-accent-red' : 'text-gray-500';
            let rewardClass = reward > 0 ? 'text-accent-green' : 'text-gray-500';
            let rrClass = rrRatio >= 2.0 ? 'bg-accent-green text-white' : (rrRatio >= 1.0 ? 'bg-yellow-500 text-gray-900' : 'bg-accent-red text-white');

            resultsDiv.innerHTML = `
                <div class="flex justify-between border-b border-gray-700 py-2">
                    <span class="font-semibold text-gray-300">ATR 緩衝值 (${atrMultiplier}x)</span>
                    <span class="font-mono text-lg">${formatCurrency(atrBuffer)}</span>
                </div>
                <div class="flex justify-between border-b border-gray-700 py-2">
                    <span class="font-semibold text-gray-300">結構止損錨點 (Swing Low)</span>
                    <span class="font-mono text-lg">${formatCurrency(structuralSL)}</span>
                </div>
                <div class="flex justify-between border-b border-gray-700 py-2">
                    <span class="font-semibold text-gray-300">最終止損價位 (Final SL)</span>
                    <span class="font-extrabold text-lg text-accent-red">${formatCurrency(finalSL)}</span>
                </div>
                <div class="flex justify-between border-b border-gray-700 py-2">
                    <span class="font-semibold text-gray-300">單次交易風險 (Risk)</span>
                    <span class="font-extrabold text-lg ${riskClass}">-${formatCurrency(risk)}</span>
                </div>
                <div class="flex justify-between py-2">
                    <span class="font-semibold text-gray-300">潛在回報 (Reward to TP2)</span>
                    <span class="font-extrabold text-lg ${rewardClass}">+${formatCurrency(reward)}</span>
                </div>
            `;
            
            // --- R:R 驗證區 ---
            rrValidationDiv.className = `p-4 rounded-lg text-center font-extrabold text-xl shadow-lg mt-6 ${rrClass}`;
            rrValidationDiv.innerHTML = `
                <span class="block text-sm font-medium mb-1">風險報酬比 (R:R Ratio)</span>
                <span class="block text-3xl">${formatCurrency(rrRatio)} : 1</span>
                <span class="block text-sm mt-2">${rrRatio >= 2.0 ? '✅ 符合專業高於 1:2 的標準' : (rrRatio >= 1.0 ? '⚠️ R:R 低於 2，需審慎評估' : '❌ 風險大於回報，不建議開單')}</span>
            `;
        }

        // Add event listeners to all calculator input fields
        inputs.forEach(id => {
            document.getElementById(id).addEventListener('input', calculateStrategy);
        });

        // Initial calculation on load
        window.onload = calculateStrategy;

    </script>
</body>
</html>
