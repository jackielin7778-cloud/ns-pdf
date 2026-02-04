import streamlit as st
import requests
import json
import time
from datetime import datetime
import re
import base64
import io
import zipfile

# ==========================================
# 1. 基本配置
# ==========================================
VERSION = "v1.1.5-fix"
st.set_page_config(page_title=f"Invoice API Tester {VERSION}", page_icon="🧾", layout="wide")

# ==========================================
# 2. 狀態管理 (確保在最前面執行)
# ==========================================
if 'sent' not in st.session_state: st.session_state.sent = 0
if 'received' not in st.session_state: st.session_state.received = 0
if 'logs' not in st.session_state: st.session_state.logs = []
if 'files' not in st.session_state: st.session_state.files = []
if 'total_time' not in st.session_state: st.session_state.total_time = 0.0

# ==========================================
# 3. 畫面標題與計數看板
# ==========================================
st.title(f"🧾 電子發票 API 測試 - 版本 {VERSION}")

# 建立一個容器來動態更新計數器
stats_container = st.empty()

def update_stats():
    with stats_container.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("已嘗試發送", st.session_state.sent)
        m2.metric("成功接收 PDF", st.session_state.received)
        m3.metric("總耗時 (秒)", f"{st.session_state.total_time:.2f} s")
        success_rate = (st.session_state.received / st.session_state.sent * 100) if st.session_state.sent > 0 else 0
        m4.metric("成功率", f"{success_rate:.1f}%")

update_stats() # 初始化顯示

st.divider()

# ==========================================
# 4. 側邊欄與原始資料
# ==========================================
with st.sidebar:
    st.header("⚙️ 發送設定")
    target_url = st.text_input("API URL", value="https://gw-ns-service.tweinv.com:443/api/v1/pdf/invoice")
    sec_interval = st.number_input("發送間隔 (秒)", min_value=0.0, value=1.0)
    total_rounds = st.number_input("總發送次數", min_value=1, value=5)

    if st.button("🗑️ 歸零計數與紀錄"):
        for key in ['sent', 'received', 'logs', 'files', 'total_time']:
            st.session_state[key] = [] if isinstance(st.session_state[key], list) else 0.0 if isinstance(st.session_state[key], float) else 0
        st.rerun()

raw_json_data = {
    "url": "",
    "payload": {
        "xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEludm9pY2UgeG1sbnM9InVybjpHRUlOVjplSW52b2ljZU1lc3NhZ2U6QzA0MDE6NC4xIj4KICAgIDxNYWluPgogICAgICAgIDxJbnZvaWNlTnVtYmVyPkRNMTAwOTc3MzE8L0ludm9pY2VOdW1iZXI+CiAgICAgICAgPEludm9pY2VEYXRlPjIwMjUxMTEyPC9JbnZvaWNlRGF0ZT4KICAgICAgICA8SW52b2ljZVRpbWU+MTE6NDU6Mzk8L0ludm9pY2VUaW1lPgogICAgICAgIDxTZWxsZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjI0NTQ5MjEwPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7pl5zntrLos4foqIrogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7lj7DljJfluILmnb7lsbHljYDlvqnoiIjljJfot68xNjfomZ8xMuaok+S5i+S4gDwvQWRkcmVzcz4KICAgICAgICA8L1NlbGxlcj4KICAgICAgICA8QnV5ZXI+CiAgICAgICAgICAgIDxJZGVudGlmaWVyPjIwNTYxNTYyPC9JZGVudGlmaWVyPgogICAgICAgICAgICA8TmFtZT7msY7ogqHku73mnInpmZDlhazlj7g8L05hbWU+CiAgICAgICAgICAgICAgICA8QWRkcmVzcz7oh7rljJfluILlhafmuZbljYDooYzmhJvot68xMDDomZ835qiTPC9BZGRyZXNzPgogICAgICAgICAgICAgICAgPEVtYWlsQWRkcmVzcz5uYWRpYUBpbnphZ2hpLWNvcnAuY29tPC9FbWFpbEFkZHJlc3M+CiAgICAgICAgPC9CdXllcj4KICAgICAgICAgICAgPEN1c3RvbXNDbGVhcmFuY2VNYXJrPjE8L0N1c3RvbXNDbGVhcmFuY2VNYXJrPgogICAgICAgIDxJbnZvaWNlVHlwZT4wNzwvSW52b2ljZVR5cGU+CiAgICAgICAgICAgIDxEb25hdGVNYXJrPjA8L0RvbmF0ZU1hcms+CiAgICAgICAgPFByaW50TWFyaz5ZPC9QcmludE1hcms+CiAgICAgICAgPFJhbmRvbU51bWJlcj45MTY5PC9SYW5kb21OdW1iZXI+CiAgICA8L01haW4+CiAgICA8RGV0YWlscz4KICAgICAgICAgICAgPFByb2R1Y3RJdGVtPgogICAgICAgICAgICAgICAgPERlc2NyaXB0aW9uPjIwMjVORVct5pyN5YuZMDE8L0Rlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgPFF1YW50aXR5PjE8L1F1YW50aXR5PgogICAgICAgICAgICAgICAgPFVuaXRQcmljZT4zMDA8L1VuaXRQcmljZT4KICAgICAgICAgICAgICAgIDxBbW91bnQ+MzAwPC9BbW91bnQ+CiAgICAgICAgICAgICAgICA8U2VxdWVuY2VOdW1iZXI+MTwvU2VxdWVuY2VOdW1iZXI+CiAgICAgICAgICAgICAgICA8VGF4VHlwZT4yPC9UYXhUeXBlPgogICAgICAgICAgICA8L1Byb2R1Y3RJdGVtPgogICAgICAgICAgICA8UHJvZHVjdEl0ZW0+CiAgICAgICAgICAgICAgICA8RGVzY3JpcHRpb24+MjAyNU5FVy3mnI3li5kwMjwvRGVzY3JpcHRpb24+CiAgICAgICAgICAgICAgICA8UXVhbnRpdHk+MjwvUXVhbnRpdHk+CiAgICAgICAgICAgICAgICA8VW5pdFByaWNlPjMzMzwvVW5pdFByaWNlPgogICAgICAgICAgICAgICAgPEFtb3VudD42NjY8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZXF1ZW5jZU51bWJlcj4yPC9TZXF1ZW5jZU51bWJlcj4KICAgICAgICAgICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgICAgIDwvUHJvZHVjdEl0ZW0+CiAgICAgICAgICAgIDxQcm9kdWN0SXRlbT4KICAgICAgICAgICAgICAgIDxEZXNjcmlwdGlvbj4yMDI1TkVXLeacjeWLmTAzPC9EZXNjcmlwdGlvbj4KICAgICAgICAgICAgICAgIDxRdWFudGl0eT40PC9RdWFudGl0eT4KICAgICAgICAgICAgICAgIDxVbml0UHJpY2U+NDQ1PC9Vbml0UHJpY2U+CiAgICAgICAgICAgICAgICA8QW1vdW50PjE3ODA8L0Ftb3VudD4KICAgICAgICAgICAgICAgIDxTZXF1ZW5jZU51bWJlcj4zPC9TZXF1ZW5jZU51bWJlcj4KICAgICAgICAgICAgICAgIDxUYXhUeXBlPjI8L1RheFR5cGU+CiAgICAgICAgICAgIDwvUHJvZHVjdEl0ZW0+CiAgICA8L0RldGFpbHM+CiAgICA8QW1vdW50PgogICAgICAgIDxTYWxlc0Ftb3VudD4wPC9TYWxlc0Ftb3VudD4KICAgICAgICA8RnJlVGF4U2FsZXNBbW91bnQ+MDwvRnJlVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFplcm9UYXhTYWxlc0Ftb3VudD4yNzQ2PC9WZXJvVGF4U2FsZXNBbW91bnQ+CiAgICAgICAgPFRheFR5cGU+MzwvVGF4VHlwZT4KICAgICAgICA8VGF4UmF0ZT4wPC9UYXhSYXRlPgogICAgICAgIDxUYXhBbW91bnQ+MDwvVGF4QW1vdW50PgogICAgICAgIDxUb3RhbEFtb3VudD4yNzQ2PC9Ub3RhbEFtb3VudD4KICAgIDwvQW1vdW50Pgo8L0ludm9pY2U+",
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

json_input = st.text_area("🔧 JSON Payload 編輯區：", value=json.dumps(raw_json_data, indent=2), height=350)

# ==========================================
# 5. 發送邏輯 (核心修正)
# ==========================================
if st.button("🚀 開始測試 (計數器即時更新)", use_container_width=True, type="primary"):
    try:
        payload_to_send = json.loads(json_input)
        
        # 抓取發票號碼
        try:
            xml_str = base64.b64decode(payload_to_send["payload"]["xml"]).decode('utf-8')
            inv_no = re.search(r'<InvoiceNumber>(.*?)</InvoiceNumber>', xml_str).group(1)
        except:
            inv_no = "Invoice"

        compact_body = json.dumps(payload_to_send, separators=(',', ':'))
        headers = {"Content-Type": "text/plain"}

        start_time = time.time()
        
        # 使用 Status 顯示當前進度
        with st.status("正在發送請求...", expanded=True) as status:
            for i in range(int(total_rounds)):
                st.session_state.sent += 1
                
                try:
                    r = requests.post(target_url, data=compact_body.encode('utf-8'), headers=headers, timeout=25)
                    if r.status_code == 200:
                        st.session_state.received += 1
                        fname = f"{inv_no}_{st.session_state.received}_{datetime.now().strftime('%H%M%S')}.pdf"
                        st.session_state.files.append({"name": fname, "content": r.content})
                        st.session_state.logs.append(f"✅ {fname} 成功")
                    else:
                        st.session_state.logs.append(f"❌ 第 {i+1} 次失敗: {r.status_code}")
                except Exception as e:
                    st.session_state.logs.append(f"⚠️ 錯誤: {str(e)}")
                
                # 每跑一圈就更新看板
                st.session_state.total_time = time.time() - start_time
                update_stats()
                
                if i < total_rounds - 1:
                    time.sleep(sec_interval)
            
            status.update(label="測試完成！", state="complete")
        
        st.rerun() # 最後刷新一次確保下載區出現
    except Exception as e:
        st.error(f"執行發生錯誤: {e}")

# ==========================================
# 6. 下載區與日誌 (佈局優化)
# ==========================================
st.divider()
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader(f"📂 下載區 ({len(st.session_state.files)})")
    if st.session_state.files:
        # ZIP 打包
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
            for f in st.session_state.files:
                zf.writestr(f["name"], f["content"])
        
        st.download_button("📦 打包下載所有 PDF (ZIP)", data=buf.getvalue(), 
                           file_name=f"Invoices_{datetime.now().strftime('%m%d%H%M')}.zip", 
                           mime="application/zip", type="primary", use_container_width=True)
        
        # 列表顯示
        for idx, f in enumerate(reversed(st.session_state.files)):
            st.download_button(f"⬇️ {f['name']}", f['content'], f['name'], key=f"d_{idx}")

with col_right:
    st.subheader("📜 執行日誌 (最新在最上)")
    st.text_area("Logs", "\n".join(reversed(st.session_state.logs)), height=400)
