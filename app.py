import streamlit as st
import requests
import json
import time
from datetime import datetime
import base64

# ==========================================
# 1. 配置與版本
# ==========================================
VERSION = "v1.0.6-debug"
st.set_page_config(page_title=f"Invoice API Tester {VERSION}", page_icon="🧾", layout="wide")

st.title(f"🧾 電子發票 API 測試 - 版本 {VERSION}")
st.info("偵測到請求經過 Google 負載均衡器。若持續 400，建議檢查發票號碼是否重複。")

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
    st.header("⚙️ 進階配置")
    target_url = st.text_input("API URL", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    
    # 模擬瀏覽器，減少被攔截機率
    ua = st.text_input("User-Agent", value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
    
    st.divider()
    auto_date = st.checkbox("自動更新發票日期至今日", value=True)
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.1, value=1.0)
    total_rounds = st.number_input("總發送次數", min_value=1, value=1)

    if st.button("🗑️ 清除數據"):
        st.session_state.update({"sent": 0, "received": 0, "logs": [], "files": []})
        st.rerun()

# ==========================================
# 4. Payload 資料處理區
# ==========================================
# 原始 CURL 的 JSON 結構
base_payload = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgIC2PEFtb3VudD4zMDA8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8PERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZDAyPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT4yPC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+MzMzPC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjY2NzwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjI8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDM8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjQ8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT40NDU8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MTc4MDwvQW1vdW50PgogICAgICAgICAgICAgICAgPFNlcXVlbmNlTnVtYmVyPjM8L1NlcXVlbmNlTnVtYmVyPgogICAgICAgICAgICAgICAgPFRheFR5cGU+MjwvVGF4VHlwZT4KICAgICAgICAgICAgPC9Qcm9kdWN0SXRlbT4KICAgIDwvRGV0YWlscz4KICAgIDxBbW91bnQ+CiAgICAgICAgPFNhbGVzQW1vdW50PjA8L1NhbGVzQW1vdW50PgogICAgICAgIDxGcmVlVGF4U2FsZXNBbW91bnQ+MDwvRnJlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4Mjc0NjwvWmVyb1RheFNhbGVzQW1vdW50PgogICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgPFRheFJhdGU+MDwvVGF4UmF0ZT4KICAgICAgICA8VGF4QW1vdW50PjA8L1RheEFtb3VudD4KICAgICAgICA8VG90YWxBbW91bnQ+Mjc0NjwvVG90YWxBbW91bnQ+CiAgICA8L0Ftb3VudD4KPC9JbnZvaWNlPg==",
        "filename": "C0401-QS26376438-172882.xml",
        "documentStatus": 2,
        "attribute": {
            "printerName": "Sharp",
            "printerType": "GENERAL",
            "uploadDocument": True
        }
    }
}

json_input = st.text_area("JSON 模板 (可手動修改):", value=json.dumps(base_payload, indent=2), height=250)

# ==========================================
# 5. 發送邏輯
# ==========================================
if st.button("🚀 執行自動測試", use_container_width=True, disabled=st.session_state.running):
    try:
        st.session_state.running = True
        payload_data = json.loads(json_input)
        
        # 自動處理日期 (若勾選)
        if auto_date:
            try:
                # 解碼 XML -> 修改日期 -> 編碼回 Base64
                xml_content = base64.b64decode(payload_data["payload"]["xml"]).decode('utf-8')
                today_str = datetime.now().strftime("%Y%m%d")
                # 簡單替換日期標籤內容
                import re
                xml_content = re.sub(r'<InvoiceDate>.*?</InvoiceDate>', f'<InvoiceDate>{today_str}</InvoiceDate>', xml_content)
                payload_data["payload"]["xml"] = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
                st.toast(f"已自動更新發票日期為: {today_str}")
            except:
                st.warning("XML 日期更新失敗，將使用原始資料發送。")

        # 最終發送字串 (移除所有多餘空格)
        final_body = json.dumps(payload_data, separators=(',', ':'))
        
        headers = {
            "Content-Type": "text/plain",
            "User-Agent": ua,
            "Accept": "*/*"
        }

        for i in range(total_rounds):
            st.session_state.sent = i + 1
            log_time = datetime.now().strftime("%H:%M:%S")
            
            try:
                r = requests.post(target_url, data=final_body.encode('utf-8'), headers=headers, timeout=20)
                
                if r.status_code == 200:
                    st.session_state.received += 1
                    st.session_state.logs.append(f"[{log_time}] ✅ 第 {i+1} 次成功")
                    st.session_state.files.append({"name": f"Invoice_{i+1}.pdf", "content": r.content})
                else:
                    st.session_state.logs.append(f"[{log_time}] ❌ 第 {i+1} 次失敗 (HTTP {r.status_code}): {r.text}")
            except Exception as e:
                st.session_state.logs.append(f"[{log_time}] ⚠️ 連線異常: {str(e)}")

            if i < total_rounds - 1: time.sleep(sec_interval)
            st.rerun()

    finally:
        st.session_state.running = False

# ==========================================
# 6. 展示與下載
# ==========================================
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("📂 成功獲取的 PDF")
    for f in st.session_state.files:
        st.download_button(f"⬇️ {f['name']}", f['content'], f['name'], "application/pdf", key=f['name'])
with c2:
    st.subheader(f"📜 日誌 ({VERSION})")
    st.text_area("Debug Log", "\n".join(reversed(st.session_state.logs)), height=400)
