import streamlit as st
import requests
import json
import time
from datetime import datetime

# 頁面配置
st.set_page_config(page_title="Invoice API Tester V3", page_icon="🧾", layout="wide")

st.title("🧾 電子發票 API 測試 (排除 400 錯誤版)")

# 狀態初始化
if 'sent' not in st.session_state: st.session_state.sent = 0
if 'received' not in st.session_state: st.session_state.received = 0
if 'logs' not in st.session_state: st.session_state.logs = []
if 'files' not in st.session_state: st.session_state.files = []
if 'running' not in st.session_state: st.session_state.running = False

# 側邊欄
with st.sidebar:
    st.header("⚙️ 進階配置")
    target_url = st.text_input("API URL", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    
    # 新增：跳過 SSL 驗證 (針對某些伺服器憑證問題)
    verify_ssl = st.checkbox("驗證 SSL 憑證", value=True)
    
    # 保持 Token 選項，但預設關閉
    use_auth = st.checkbox("開啟 Token 驗證", value=False)
    auth_token = st.text_input("Token", type="password") if use_auth else ""
    
    st.divider()
    sec_interval = st.number_input("間隔秒數", min_value=0.1, value=1.0)
    total_rounds = st.number_input("次數", min_value=1, value=1)

    if st.button("🗑️ 清除所有紀錄"):
        st.session_state.update({"sent": 0, "received": 0, "logs": [], "files": []})
        st.rerun()

# 預設 Payload
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

json_body = st.text_area("JSON Payload:", value=json.dumps(default_payload, indent=2, ensure_ascii=False), height=300)

# 進度儀表
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("已發送", st.session_state.sent)
c2.metric("已接收", st.session_state.received)
c3.progress(st.session_state.sent / total_rounds if total_rounds > 0 else 0)

# 發送邏輯
if st.button("🚀 開始測試", use_container_width=True, disabled=st.session_state.running):
    try:
        # 重要：模仿 CURL 的方式處理內容
        raw_text = json_body.strip() 
        
        st.session_state.running = True
        headers = {"Content-Type": "text/plain"}
        if use_auth and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            t = datetime.now().strftime("%H:%M:%S")
            
            try:
                # 這裡改用 data=raw_text (不經過 JSON 轉換，直接發送文字內容)
                r = requests.post(
                    target_url, 
                    data=raw_text.encode('utf-8'), 
                    headers=headers, 
                    timeout=30,
                    verify=verify_ssl
                )
                
                if r.status_code == 200:
                    st.session_state.received += 1
                    f_name = f"Invoice_{i+1}.pdf"
                    st.session_state.files.append({"name": f_name, "content": r.content})
                    st.session_state.logs.append(f"[{t}] ✅ 第 {i+1} 次成功")
                else:
                    # 顯示完整的回傳內容，不擷取
                    st.session_state.logs.append(f"[{t}] ❌ 第 {i+1} 次失敗 (HTTP {r.status_code}): {r.text}")
            except Exception as e:
                st.session_state.logs.append(f"[{t}] ⚠️ 請求異常: {str(e)}")

            if i < total_rounds - 1: time.sleep(sec_interval)
            st.rerun()

    except Exception as e:
        st.error(f"系統錯誤: {e}")
    finally:
        st.session_state.running = False

# 下載與日誌
st.divider()
d_col, l_col = st.columns(2)
with d_col:
    st.subheader("📂 下載區")
    for f in st.session_state.files:
        st.download_button(f"⬇️ 下載 {f['name']}", f['content'], f['name'], "application/pdf", key=f['name'])
with l_col:
    st.subheader("📜 執行日誌")
    st.text_area("Log", "\n".join(reversed(st.session_state.logs)), height=300)
