import streamlit as st
import requests
import json
import time
from datetime import datetime

# ==========================================
# 1. 配置與版本
# ==========================================
VERSION = "v1.0.7-debug"
st.set_page_config(page_title=f"Invoice API Tester {VERSION}", page_icon="🧾", layout="wide")

st.title(f"🧾 電子發票 API 測試 - 版本 {VERSION}")
st.success("已更新為正確的 Payload 結構")

# ==========================================
# 2. 狀態管理
# ==========================================
for key in ['sent', 'received', 'logs', 'files', 'running']:
    if key not in st.session_state:
        st.session_state[key] = 0 if key in ['sent', 'received'] else ([] if key in ['logs', 'files'] else False)

# ==========================================
# 3. 側邊欄配置
# ==========================================
with st.sidebar:
    st.header("⚙️ 配置")
    target_url = st.text_input("API URL", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    ua = st.text_input("User-Agent", value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
    
    st.divider()
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.1, value=1.0)
    total_rounds = st.number_input("總發送次數", min_value=1, value=1)

    if st.button("🗑️ 清除所有紀錄"):
        st.session_state.update({"sent": 0, "received": 0, "logs": [], "files": []})
        st.rerun()

# ==========================================
# 4. 正確的 Payload 資料 (由你提供)
# ==========================================
# 這裡使用了你提供的正確 JSON 字串
correct_data = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8RGVzY3JpcHRpb24+MjAyNU5FVy3mnI3li5kwMjwvRGVzY3JpcHRpb24+CiAgICAgICAgICAgICAgICA8UXVhbnRpdHk+MjwvUXVhbnRpdHk+CiAgICAgICAgICAgICAgICA8VW5pdFByaWNlPjMzMzwvVW5pdFByaWNlPgogICAgICAgICAgICAgICAgPEFtb3VudD42NjY8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZWx1ZW5jZU51bWJlcj4yPC9TZXF1ZW5jZU51bWJlcj4KICAgICAgICAgICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgICAgIDwvUHJvZHVjdEl0ZW0+CiAgICAgICAgICAgIDxQcm9kdWN0SXRlbT4KICAgICAgICAgICAgICAgIDxEZXNjcmlwdGlvbj4yMDI1TkVXLeacjeWLmTAzPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT40PC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+NDQ1PC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjE3ODA8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZWx1ZW5jZU51bWJlcj4zPC9TZXF1ZW5jZU51bWJlcj4KICAgICAgICAgICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgICAgIDwvUHJvZHVjdEl0ZW0+CiAgICA8L0RldGFpbHM+CiAgICA8QW1vdW50PgogICAgICAgIDxTYWxlc0Ftb3VudD4wPC9TYWxlc0Ftb3VudD4KICAgICAgICA8RnJlVGF4U2FsZXNBbW91bnQ+0PC9GcmVlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4yNzQ2PC9WZXJvVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFRheFR5cGU+MzwvVGF4VHlwZT4KICAgICAgICA8VGF4UmF0ZT4wPC9UYXhSYXRlPgogICAgICAgIDxUYXhBbW91bnQ+MDwvVGF4QW1vdW50PgogICAgICAgIDxUb3RhbEFtb3VudD4yNzQ2PC9Ub3RhbEFtb3VudD4KICAgIDwvQW1vdW50Pgo8L0ludm9pY2U+",
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

json_input = st.text_area("正確 Payload (JSON):", value=json.dumps(correct_data, indent=2), height=400)

# ==========================================
# 5. 發送邏輯
# ==========================================
if st.button("🚀 開始測試 (v1.0.7)", use_container_width=True, disabled=st.session_state.running):
    try:
        st.session_state.running = True
        # 完全解析輸入，確保沒有格式損毀
        final_payload = json.loads(json_input)
        # 轉回最純粹的緊湊字串 (移除空格)
        compact_body = json.dumps(final_payload, separators=(',', ':'))
        
        headers = {
            "Content-Type": "text/plain",
            "User-Agent": ua
        }

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            log_time = datetime.now().strftime("%H:%M:%S")
            
            try:
                # 執行 POST
                r = requests.post(target_url, data=compact_body.encode('utf-8'), headers=headers, timeout=25)
                
                if r.status_code == 200:
                    st.session_state.received += 1
                    st.session_state.logs.append(f"[{log_time}] ✅ 成功接收 PDF")
                    st.session_state.files.append({"name": f"Invoice_{i+1}.pdf", "content": r.content})
                else:
                    st.session_state.logs.append(f"[{log_time}] ❌ 失敗 ({r.status_code}): {r.text}")
            except Exception as e:
                st.session_state.logs.append(f"[{log_time}] ⚠️ 連線錯誤: {str(e)}")

            if i < total_rounds - 1: time.sleep(sec_interval)
            st.rerun()

    finally:
        st.session_state.running = False

# ==========================================
# 6. 下載與日誌
# ==========================================
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("📂 下載區")
    for f in st.session_state.files:
        st.download_button(f"⬇️ 下載 {f['name']}", f['content'], f['name'], "application/pdf", key=f['name'])
with c2:
    st.subheader("📜 執行日誌")
    st.text_area("Log", "\n".join(reversed(st.session_state.logs)), height=350)
