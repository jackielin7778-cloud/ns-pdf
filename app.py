import streamlit as st
import requests
import json
import time
from datetime import datetime

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="Invoice API E2E Tester", 
    page_icon="🧾",
    layout="wide"
)

# 自定義 CSS 讓介面更像專業測試工具
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    code { color: #e83e8c; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧾 電子發票 PDF 產生自動化測試工具")
st.caption("工程師專用 E2E 測試面板 - 支援高頻發送與 PDF 檔案追蹤")

# ==========================================
# 狀態管理 (Session State)
# ==========================================
if 'sent' not in st.session_state: st.session_state.sent = 0
if 'received' not in st.session_state: st.session_state.received = 0
if 'logs' not in st.session_state: st.session_state.logs = []
if 'files' not in st.session_state: st.session_state.files = []
if 'running' not in st.session_state: st.session_state.running = False

# ==========================================
# 側邊欄：配置參數
# ==========================================
with st.sidebar:
    st.header("⚙️ API 配置")
    target_url = st.text_input("API Endpoint", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    auth_token = st.text_input("Authorization (Token)", type="password", help="Bearer token for the API")
    
    st.divider()
    st.header("⏲️ 壓力測試設定")
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.1, value=1.0, step=0.5)
    total_rounds = st.number_input("總發送次數", min_value=1, value=10, step=1)

    if st.button("🗑️ 清除所有紀錄", use_container_width=True):
        st.session_state.sent = 0
        st.session_state.received = 0
        st.session_state.logs = []
        st.session_state.files = []
        st.rerun()

# ==========================================
# 主介面佈局
# ==========================================
# 預設 Payload (根據你提供的 CURL 內容)
default_payload = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8PERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZDAyPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT4yPC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+MzMzPC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjY2NzwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjI8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDM8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjQ8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT40NDU8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MTc4MDwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjM8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgIDwvRGV0YWlscz4KICAgIDxBbW91bnQ+CiAgICAgICAgPFNhbGVzQW1vdW50PjA8L1NhbGVzQW1vdW50PgogICAgICAgIDxGcmVlVGF4U2FsZXNBbW91bnQ+MDwvRnJlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4Mjc0NjwvWmVyb1RheFNhbGVzQW1vdW50PgogICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgPFRheFJhdGU+MDwvVGF4UmF0ZT4KICAgICAgICA8VGF4QW1vdW50PjA8L1RheEFtb3VudD4KICAgICAgICA8VG90YWxBbW91bnQ+Mjc0NjwvVG90YWxBbW91bnQ+CiAgICA8L0Ftb3VudD4KPC9JbnZvaWNlPg==",
        "filename": "C0401-QS26376438-172882.xml",
        "checksum": "",
        "documentStatus": 2,
        "extramemo": ""
    },
    "attribute": {
        "printerName": "Sharp",
        "printerType": "GENERAL",
        "printerKey": "uuid",
        "lineSpacing": 1,
        "printDetail": False,
        "printContact": False,
        "reprint": False,
        "uploadDocument": True
    }
}

st.subheader("📝 JSON Payload (text/plain)")
json_body = st.text_area("編輯要發送的資料：", value=json.dumps(default_payload, indent=2, ensure_ascii=False), height=350)

# 進度顯示區
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("已發送請求 (Sent)", st.session_state.sent)
c2.metric("已收到檔案 (Received)", st.session_state.received)
progress_bar = c3.progress(st.session_state.sent / total_rounds if total_rounds > 0 else 0)

# ==========================================
# 執行按鈕與連線邏輯
# ==========================================
if st.button("🚀 開始測試", use_container_width=True, disabled=st.session_state.running):
    try:
        # JSON 檢查
        parsed_data = json.loads(json_body)
        st.session_state.running = True
        
        # 設定 Header (依據您的 CURL 要求為 text/plain)
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "text/plain"
        }

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            try:
                # 執行發送
                resp = requests.post(target_url, data=json.dumps(parsed_data), headers=headers, timeout=60)
                
                if resp.status_code == 200:
                    st.session_state.received += 1
                    file_name = f"Invoice_{i+1}_{datetime.now().strftime('%M%S')}.pdf"
                    
                    # 暫存 PDF 內容
                    st.session_state.files.append({"name": file_name, "content": resp.content})
                    st.session_state.logs.append(f"[{timestamp}] ✅ #{i+1} 成功: PDF 已接收")
                else:
                    st.session_state.logs.append(f"[{timestamp}] ❌ #{i+1} 失敗: HTTP {resp.status_code}")
            
            except Exception as e:
                st.session_state.logs.append(f"[{timestamp}] ⚠️ #{i+1} 異常: {str(e)}")

            # 即時渲染更新
            if i < total_rounds - 1:
                time.sleep(sec_interval)
            st.rerun()

    except Exception as fatal_e:
        st.error(f"系統錯誤: {fatal_e}")
    finally:
        st.session_state.running = False

# ==========================================
# 結果下載與日誌
# ==========================================
st.divider()
col_dl, col_log = st.columns([1, 1])

with col_dl:
    st.subheader("📂 PDF 下載清單")
    if not st.session_state.files:
        st.info("尚無接收到的檔案。")
    else:
        for f in st.session_state.files:
            st.download_button(label=f"⬇️ 下載 {f['name']}", data=f['content'], file_name=f['name'], mime="application/pdf", key=f['name'])

with col_log:
    st.subheader("📜 執行日誌 (最新)")
    if st.session_state.logs:
        st.text_area("Log", value="\n".join(reversed(st.session_state.logs)), height=250)