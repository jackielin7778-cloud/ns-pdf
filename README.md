# ns-pdf
# Invoice API E2E 自動化測試工具 (Streamlit)

🚀 **專為發票服務設計的高效能 E2E 測試工具。**

## 🎯 功能特色
- **純 Python 實作**：使用 Streamlit 快速構建 UI，無需撰寫前端 HTML/JS。
- **即時計數**：同步追蹤「發送請求數」與「收到 PDF 檔案數」。
- **自動間隔發送**：可自定義間隔秒數，模擬真實使用場景或壓力測試。
- **檔案自動收集**：所有 API 回傳之 PDF 內容皆暫存於 Session，可一鍵下載。

## 🛠️ 安裝與啟動
1. 確保已安裝 Python 3.8+
2. 安裝依賴項：
   ```bash
   pip install -r requirements.txt
   
