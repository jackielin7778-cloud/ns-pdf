import streamlit as st
import requests
import json
import time
from datetime import datetime

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(page_title="Invoice API Tester", page_icon="🧾", layout="wide")

st.title("🧾 電子發票 PDF 自動化測試 (無 Token 版)")

# ==========================================
# 狀態管理
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
    target_url = st.text_input("API 網址", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    
    # 註：根據你的 CURL，這裡暫時不需要 Token，我們將其設為隱藏或備用
    use_auth = st.checkbox("開啟 Token 驗證", value=False)
    auth_token = ""
    if use_auth:
        auth_token = st.text_input("Authorization Token", type="password")
    
    st.divider()
    st.header("⏲️ 發送設定")
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.1, value=1.0)
    total_rounds = st.number_input("發送總次數", min_value=1, value=5)

    if st.button("🗑️ 清除數據"):
        st.session_state.update({"sent": 0, "received": 0, "logs": [], "files": []})
        st.rerun()

# ==========================================
# 主介面：Payload 編輯
# ==========================================
# 這是你 CURL 裡的原始 JSON 內容
default_payload = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8PERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZDAyPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT4yPC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+MzMzPC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjY2NzwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjI8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDM8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjQ8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT40NDU8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MTc4MDwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjM8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgIDwvRGV0YWlscz4KICAgIDxBbW91bnQ+CiAgICAgICAgPFNhbGVzQW1vdW50PjA8L1NhbGVzQW1vdW50PgogICAgICAgIDxGcmVlVGF4U2FsZXNBbW91bnQ+MDwvRnJlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4Mjc0NjwvWmVyb1RheFNhbGVzQW1vdW50PgogICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgPFRheFJhdGU+MDwvVGF4UmF0ZT4KICAgICAgICA8VGF4QW1vdW50PjA8L1RheEFtb3VudD4KICAgICAgICA8VG90YWxBbW91bnQ+Mjc0NjwvVG90YWxBbW91bnQ+CiAgICA8L0Ftb3VudD4KPC9JbnZvaWNlPg==",
        "filename": "C0401-QS26376438-172882.xml",
        "documentStatus": 2,
        "attribute": {
            "printerName": "Sharp",
            "printerType": "GENERAL",
            "uploadDocument": True
        }
    }
}

json_body = st.text_area("請求資料 (JSON):", value=json.dumps(default_payload, indent=2, ensure_ascii=False), height=350)

# 顯示計數
st.divider()
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("已發送", st.session_state.sent)
col_m2.metric("已接收", st.session_state.received)
col_m3.progress(st.session_state.sent / total_rounds if total_rounds > 0 else 0)

# ==========================================
# 發送邏輯
# ==========================================
if st.button("🚀 開始執行測試", use_container_width=True, disabled=st.session_state.running):
    try:
        parsed_payload = json.loads(json_body)
        st.session_state.running = True
        
        # 建立 Header：根據你的 CURL，只有 Content-Type
        headers = {"Content-Type": "text/plain"}
        if use_auth and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            log_time = datetime.now().strftime("%H:%M:%S")
            
            try:
                # 執行發送
                r = requests.post(target_url, data=json.dumps(parsed_payload), headers=headers, timeout=60)
                
                if r.status_code == 200:
                    st.session_state.received += 1
                    f_name = f"Invoice_{i+1}_{datetime.now().strftime('%M%S')}.pdf"
                    st.session_state.files.append({"name": f_name, "content": r.content})
                    st.session_state.logs.append(f"[{log_time}] ✅ 第 {i+1} 次成功")
                else:
                    st.session_state.logs.append(f"[{log_time}] ❌ 第 {i+1} 次失敗: {r.status_code}")
            except Exception as e:
                st.session_state.logs.append(f"[{log_time}] ⚠️ 異常: {str(e)}")

            if i < total_rounds - 1: time.sleep(sec_interval)
            st.rerun()

    except Exception as e:
        st.error(f"錯誤: {e}")
    finally:
        st.session_state.running = False

# ==========================================
# 下載與日誌
# ==========================================
st.divider()
d_col, l_col = st.columns(2)
with d_col:
    st.subheader("📂 下載區")
    for f in st.session_state.files:
        st.download_button(f"⬇️ {f['name']}", f['content'], f['name'], "application/pdf", key=f['name'])
with l_col:
    st.subheader("📜 日誌")
    st.text_area("Log", "\n".join(reversed(st.session_state.logs)), height=200)
