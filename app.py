import streamlit as st
import requests
import json
import time
from datetime import datetime

# ==========================================
# 1. 基礎配置與版本號
# ==========================================
VERSION = "v1.0.4-debug"

st.set_page_config(
    page_title=f"Invoice API Tester {VERSION}", 
    page_icon="🧾", 
    layout="wide"
)

# 顯示版本與標題
st.title(f"🧾 電子發票 API 測試工具")
st.code(f"Current Version: {VERSION}")

# ==========================================
# 2. 狀態管理 (Session State)
# ==========================================
if 'sent' not in st.session_state: st.session_state.sent = 0
if 'received' not in st.session_state: st.session_state.received = 0
if 'logs' not in st.session_state: st.session_state.logs = []
if 'files' not in st.session_state: st.session_state.files = []
if 'running' not in st.session_state: st.session_state.running = False

# ==========================================
# 3. 側邊欄配置
# ==========================================
with st.sidebar:
    st.header("⚙️ 進階配置")
    target_url = st.text_input("API URL", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    
    # 針對 400 錯誤的 Debug 開關
    verify_ssl = st.checkbox("驗證 SSL 憑證 (Verify SSL)", value=False)
    
    st.divider()
    st.header("⏲️ 壓力測試設定")
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.1, value=1.0)
    total_rounds = st.number_input("總發送次數", min_value=1, value=1)

    if st.button("🗑️ 清除所有紀錄與計數"):
        st.session_state.update({"sent": 0, "received": 0, "logs": [], "files": []})
        st.rerun()

# ==========================================
# 4. Payload 資料區
# ==========================================
# CURL 中的原始 Payload 範例
default_payload = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgIC2PEFtb3VudD4zMDA8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8PERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZDAyPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT4yPC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+MzMzPC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjY2NzwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjI8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDM8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjQ8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT40NDU8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MTc4MDwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjM8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgIDwvRGV0YWlscz4KICAgIDxBbW91bnQ+CiAgICAgICAgPFNhbGVzQW1vdW50PjA8L1NhbGVzQW1vdW50PgogICAgICAgIDxGcmVlVGF4U2FsZXNBbW91bnQ+MDwvRnJlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4Mjc0NjwvWmVyb1RheFNhbGVzQW1vdW50PgogICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgPFRheFJhdGU+MDwvVGF4UmF0ZT4KICAgICAgICA8VGF4QW1vdW50PjA8L1RheEFtb3VudD4KICAgICAgICA8VG90YWxBbW91bnQ+Mjc0NjwvVG90YWxBbW91bnQ+CiAgICA8L0Ftb3VudD4KPC9JbnZvaWNlPg==",
        "filename": "C0401-QS26376438-172882.xml",
        "documentStatus": 2,
        "attribute": {
            "printerName": "Sharp",
            "printerType": "GENERAL",
            "uploadDocument": True
        }
    }
}

json_body = st.text_area("JSON 資料編輯：", value=json.dumps(default_payload, indent=2, ensure_ascii=False), height=300)

# ==========================================
# 5. 計數儀表板
# ==========================================
st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("已發送請求 (Sent)", st.session_state.sent)
m2.metric("已成功接收 (Received)", st.session_state.received)
progress_val = st.session_state.sent / total_rounds if total_rounds > 0 else 0
m3.progress(progress_val, text=f"發送進度: {int(progress_val*100)}%")

# ==========================================
# 6. 核心發送邏輯
# ==========================================
if st.button("🚀 執行自動化測試", use_container_width=True, disabled=st.session_state.running):
    try:
        # 強制清理掉輸入字串中的前後空白，確保 text/plain 的純淨性
        clean_raw_text = json_body.strip()
        
        st.session_state.running = True
        # 依照原始 CURL 設定
        headers = {"Content-Type": "text/plain"}

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            log_time = datetime.now().strftime("%H:%M:%S")
            
            try:
                # 模仿 CURL --data 的行為，不使用 json= 參數，直接發送 encode 後的字串
                r = requests.post(
                    target_url, 
                    data=clean_raw_text.encode('utf-8'), 
                    headers=headers, 
                    timeout=30,
                    verify=verify_ssl
                )
                
                if r.status_code == 200:
                    st.session_state.received += 1
                    file_name = f"Invoice_{i+1}_{datetime.now().strftime('%M%S')}.pdf"
                    st.session_state.files.append({"name": file_name, "content": r.content})
                    st.session_state.logs.append(f"[{log_time}] ✅ 第 {i+1} 次發送：200 OK")
                else:
                    # Debug 模式：抓取更多的資訊
                    err_msg = f"[{log_time}] ❌ 第 {i+1} 次失敗 (HTTP {r.status_code})\n"
                    err_msg += f"   > 回傳內容: {r.text if r.text else 'Empty Body'}\n"
                    err_msg += f"   > Server Header: {dict(r.headers).get('Server', 'Unknown')}"
                    st.session_state.logs.append(err_msg)
            
            except Exception as e:
                st.session_state.logs.append(f"[{log_time}] ⚠️ 連線異常: {str(e)}")

            # 每輪結束等待並重繪
            if i < total_rounds - 1:
                time.sleep(sec_interval)
            st.rerun()

    except Exception as e:
        st.error(f"系統崩潰：{e}")
    finally:
        st.session_state.running = False

# ==========================================
# 7. 下載區與日誌
# ==========================================
st.divider()
d_col, l_col = st.columns(2)

with d_col:
    st.subheader("📂 檔案下載清單")
    if st.session_state.files:
        for f in st.session_state.files:
            st.download_button(
                label=f"⬇️ 下載 {f['name']}", 
                data=f['content'], 
                file_name=f['name'], 
                mime="application/pdf",
                key=f"dl_{f['name']}"
            )
    else:
        st.write("目前尚無可下載檔案。")

with l_col:
    st.subheader("📜 詳情日誌 (Debug)")
    # 將日誌反轉，最新的顯示在最上方
    st.text_area("Log Output", "\n".join(reversed(st.session_state.logs)), height=350)
