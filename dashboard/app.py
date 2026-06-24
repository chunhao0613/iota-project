import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# API configuration
API_BASE = "http://127.0.0.1:8000/api/v1"

# Set up page config
st.set_page_config(
    page_title="IOTA IoT Data Integrity Ledger",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    /* Global Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Main Headers */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        padding-top: 1rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }
    
    /* Styled Card Container */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(12px);
        margin-bottom: 1.5rem;
    }
    
    .card-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        border-left: 4px solid #6366f1;
        padding-left: 0.5rem;
    }
    
    /* Metrics grid */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-align: center;
        border: 1px solid transparent;
    }
    .badge-anchored {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.3);
    }
    .badge-pending {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border-color: rgba(245, 158, 11, 0.3);
    }
    .badge-failed {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border-color: rgba(239, 68, 68, 0.3);
    }
    
    /* Table row backgrounds */
    div[data-testid="stExpander"] {
        background: rgba(17, 24, 39, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 8px;
    }
    
    /* Premium Button Customizer */
    div.stButton > button {
        background-color: rgba(99, 102, 241, 0.2) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: rgba(99, 102, 241, 0.8) !important;
        border-color: #6366f1 !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.6) !important;
    }
    div.stButton > button:active {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
    }
    
</style>
""", unsafe_allow_html=True)

# Helper to fetch system status
def get_system_status():
    try:
        response = requests.get(f"{API_BASE}/health", timeout=3)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# Sidebar status panel
status_data = get_system_status()

st.sidebar.markdown("<h2 style='color:white;font-weight:700;'>⚙ 系統設定與狀態</h2>", unsafe_allow_html=True)
if status_data:
    st.sidebar.markdown(f"**API 後端**: 🟢 正常連線")
    st.sidebar.markdown(f"**IOTA 節點**: `{status_data['iota_node']}`")
    if status_data['iota_connected']:
        st.sidebar.markdown(f"**Tangle 網路**: 🟢 已連線")
    else:
        st.sidebar.markdown(f"**Tangle 網路**: 🟡 連線失敗 (已啟用 ignore_node_health 繞過)")
else:
    st.sidebar.error("❌ 無法連線至 FastAPI 後端。請確認後端服務已啟動在 http://127.0.0.1:8000")

# Auto refresh control
auto_refresh = st.sidebar.checkbox("自動更新數據 (每 5 秒)", value=True)

# Gateway connection control
if status_data:
    try:
        gw_status_res = requests.get(f"{API_BASE}/gateway/status", timeout=1)
        if gw_status_res.status_code == 200:
            gw_conn = gw_status_res.json().get("connected", True)
            st.sidebar.markdown("---")
            st.sidebar.markdown("<h3 style='color:white;font-weight:700;'>🔌 模擬閘道連線控制</h3>", unsafe_allow_html=True)
            if gw_conn:
                st.sidebar.success("🟢 閘道接收窗口 (8080/8000): 開啟中")
                if st.sidebar.button("❌ 斷開與模擬閘道的連結 (關閉接收)", use_container_width=True):
                    requests.post(f"{API_BASE}/gateway/toggle")
                    st.toast("⚡ 已關閉閘道數據接收窗口")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.sidebar.error("🔴 閘道接收窗口 (8080/8000): 已關閉")
                if st.sidebar.button("🔌 重新連線與開啟接收窗口", use_container_width=True):
                    requests.post(f"{API_BASE}/gateway/toggle")
                    st.toast("🔌 已重新啟用閘道數據接收窗口")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
    except Exception as e:
        pass

st.markdown("<h1 class='main-title'>🔒 IOTA Tangle IoT 資料完整性驗證系統</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>整合 Thaumio 數位雙生模擬與 IOTA 測試網的生產級高可靠邊緣資料防篡改審計平台</p>", unsafe_allow_html=True)

if not status_data:
    st.warning("⚠️ 系統後端未運行，請在終端機啟動 FastAPI 服務：`uvicorn app.main:app --reload`")
    st.stop()

# Load historical data
@st.cache_data(ttl=2)
def load_data():
    try:
        res = requests.get(f"{API_BASE}/records?limit=50", timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"讀取感測器歷史資料出錯: {e}")
    return []

records = load_data()

# ----------------- TABS LAYOUT -----------------
tab_dashboard, tab_threat_model = st.tabs(["📊 即時監控與校驗 (Dashboard)", "🛡️ 系統安全威脅模型 (Threat Model)"])

with tab_dashboard:
    col_stats, col_graphs = st.columns([1, 2])
    
    with col_stats:
        st.markdown("""
        <div class='glass-card'>
            <div class='card-header'>即時感測器數據</div>
        </div>
        """, unsafe_allow_html=True)
        
        if records:
            latest = records[0]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='metric-label'>🌡️ 溫度</div><div class='metric-value'>{latest['temperature']:.2f} °C</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-label'>💧 濕度</div><div class='metric-value'>{latest['humidity']:.2f} %</div>", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            with c3:
                st.markdown(f"<div class='metric-label'>⚡ 電力消耗</div><div class='metric-value'>{latest['power']:.1f} W</div>", unsafe_allow_html=True)
            with c4:
                # Format time
                try:
                    time_parsed = datetime.fromisoformat(latest['timestamp'].replace("Z", ""))
                    time_str = time_parsed.strftime("%H:%M:%S")
                except:
                    time_str = latest['timestamp'][:19]
                st.markdown(f"<div class='metric-label'>⏰ 更新時間</div><div class='metric-value' style='font-size:1.6rem;'>{time_str}</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**目前裝置**: `{latest['device_id']}` | **韌體版本**: `v{latest['firmware_version']}`")
        else:
            st.info("💡 尚未收到任何感測器資料。請開啟 Thaumio 模擬器：`python sensor/thaumio_sensor.py`")
            
    with col_graphs:
        st.markdown("""
        <div class='glass-card'>
            <div class='card-header'>感測趨勢監控 (最近 15 筆)</div>
        </div>
        """, unsafe_allow_html=True)
        
        if len(records) > 1:
            # Convert to dataframe
            df = pd.DataFrame(records[:15])
            # Parse timestamp to pandas datetime
            df['datetime'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('datetime')
            
            # Tabs for different graphs
            tab_temp, tab_hum, tab_power = st.tabs(["🌡️ 溫度趨勢", "💧 濕度趨勢", "⚡ 電力趨勢"])
            with tab_temp:
                st.line_chart(df, x="datetime", y="temperature", color="#6366f1")
            with tab_hum:
                st.line_chart(df, x="datetime", y="humidity", color="#10b981")
            with tab_power:
                st.line_chart(df, x="datetime", y="power", color="#f59e0b")
        else:
            st.info("📈 當有大於 1 筆的資料時，此處將自動呈現折線圖。")

    # ----------------- AUDIT & VERIFICATION SECTION -----------------
    st.markdown("---")
    st.markdown("## 🔍 區塊鏈資料完整性審計")
    
    # Split screen to show list of records and tamper simulator
    col_records, col_tamper = st.columns([3, 2])
    
    with col_records:
        st.markdown("<h3 style='color:white;'>📋 數據存證帳本 (SQLite + IOTA Tangle)</h3>", unsafe_allow_html=True)
        
        if records:
            pending_count = sum(1 for r in records if r['iota_status'] == "PENDING")
            if pending_count > 0:
                st.warning(f"⏳ 偵測到 **{pending_count}** 筆異常/事件數據處於 `PENDING` (未上鏈) 狀態。")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔗 僅執行 IOTA 聚合上鏈", use_container_width=True):
                        with st.spinner("正在為 PENDING 數據構建 Merkle 樹並發布至 IOTA Testnet..."):
                            try:
                                res = requests.post(f"{API_BASE}/records/anchor-batch")
                                if res.status_code == 200:
                                    data = res.json()
                                    if data.get("status") == "success":
                                        st.success(f"🎉 成功打包 {data['anchored_count']} 筆數據！Merkle Root: `{data['merkle_root'][:16]}...` | Block ID: `{data['iota_block_id']}`")
                                        time.sleep(2.0)
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.info(data.get("message", "無事可做"))
                                else:
                                    st.error(f"上鏈失敗: {res.text}")
                            except Exception as e:
                                st.error(f"連線出錯: {e}")
                with col_btn2:
                    if st.button("📊 執行跨鏈多重公證與對比實驗 (IOTA + Arbitrum + Ethereum + Solana)", use_container_width=True):
                        progress_bar = st.progress(0, text="🚀 初始化跨鏈多重公證任務...")
                        try:
                            # Step 1: IOTA
                            progress_bar.progress(15, text="🔗 [Step 1/4] 正在為異常數據計算 Merkle Root 並發布至 IOTA Tangle 測試網...")
                            res = requests.post(f"{API_BASE}/records/anchor-comparison")
                            if res.status_code == 200:
                                data = res.json()
                                
                                # Step 2: Arbitrum Sepolia
                                progress_bar.progress(45, text="⚡ [Step 2/4] 正在向 Arbitrum Sepolia (EVM L2) 發送交易，測量 RTT 與計算 Gas 開銷...")
                                time.sleep(0.8)
                                
                                # Step 3: Ethereum Sepolia
                                progress_bar.progress(70, text="💎 [Step 3/4] 正在向 Ethereum Sepolia (EVM L1) 發送交易，測量 RTT 與計算 Gas 手續費...")
                                time.sleep(0.8)
                                
                                # Step 4: Solana Devnet
                                progress_bar.progress(90, text="☀️ [Step 4/4] 正在與 Solana Devnet 節點進行通訊，評估網絡時延與交易開銷...")
                                time.sleep(0.8)
                                
                                progress_bar.progress(100, text="✅ 跨鏈多重公證與測量完成！正在載入分析結果...")
                                time.sleep(0.5)
                                
                                st.session_state.comparison_report = data
                                st.toast("🎉 跨鏈公證與對比分析完成！", icon="✅")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"對比上鏈失敗: {res.text}")
                        except Exception as e:
                            st.error(f"連線出錯: {e}")
            else:
                st.success("✅ 所有異常事件皆已完成區塊鏈存證，正常數據僅於本地儲存 (Event Filter 已啟用)")
                st.info("💡 學術實驗提示：目前沒有待上鏈的異常數據。但您可以點擊下方按鈕以「Demo 測試數據 (模擬 5 筆)」執行多鏈公證對比實驗！")
                if st.button("📊 啟動跨鏈多重公證實驗 (測試數據模式)", use_container_width=True):
                    progress_bar = st.progress(0, text="🚀 初始化跨鏈多鏈公證任務...")
                    try:
                        progress_bar.progress(15, text="🔗 [Step 1/4] 正在連接 IOTA Tangle 測試網，測量網絡 RTT 與模擬 Merkle Root 寫入...")
                        res = requests.post(f"{API_BASE}/records/anchor-comparison")
                        if res.status_code == 200:
                            data = res.json()
                            
                            progress_bar.progress(45, text="⚡ [Step 2/4] 正在連接 Arbitrum Sepolia (EVM L2) RPC 節點，測量 RTT 並估算 Gas 費用...")
                            time.sleep(0.8)
                            
                            progress_bar.progress(70, text="💎 [Step 3/4] 正在連接 Ethereum Sepolia (EVM L1) RPC 節點，測量 RTT 並估算 Gas 費用...")
                            time.sleep(0.8)
                            
                            progress_bar.progress(90, text="☀️ [Step 4/4] 正在與 Solana Devnet 節點通訊，測量 RTT 與單次交易開銷...")
                            time.sleep(0.8)
                            
                            progress_bar.progress(100, text="✅ 跨鏈公證實驗完成！正在載入分析結果...")
                            time.sleep(0.5)
                            
                            st.session_state.comparison_report = data
                            st.toast("🎉 跨鏈模擬公證分析完成！", icon="✅")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"對比上鏈失敗: {res.text}")
                    except Exception as e:
                        st.error(f"連線出錯: {e}")

            # Render comparison report if available in session_state
            if "comparison_report" in st.session_state:
                rep = st.session_state.comparison_report
                is_demo_tag = " (測試數據模式)" if rep.get("is_demo", False) else ""
                st.markdown(f"""
                <div class='glass-card' style='border-color: #6366f1; margin-top: 15px;'>
                    <div class='card-header' style='border-left-color: #6366f1;'>📊 邊緣數據公證跨鏈效能對比報告 {is_demo_tag}</div>
                    <p style='font-size:0.9rem; color:#9ca3af; margin-bottom: 1rem;'>
                        本報告對比了基於 DAG 的無手續費 IOTA 測試網與主流 L1/L2 區塊鏈測試網的上鏈表現。
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                c_iota, c_arb, c_eth, c_sol = st.columns(4)
                
                with c_iota:
                    st.markdown(f"""
                    <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 0.8rem; height: 195px;'>
                        <h4 style='color: #10b981; margin-top:0; font-size: 1.05rem;'>🟢 IOTA / Shimmer</h4>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>時延:</b> {rep['iota']['latency_sec']:.4f} 秒</p>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>手續費:</b> <span style='color: #10b981; font-weight: bold;'>$0.00 USD</span></p>
                        <p style='margin: 4px 0; font-size: 0.8rem; color:#9ca3af;'><b>網關載荷:</b> 極低 (免錢包資產)</p>
                        <p style='font-size: 0.75rem; color:#9ca3af; margin: 4px 0; word-break: break-all;'><b>Block ID:</b> {rep['iota']['block_id'][:12] if rep['iota']['block_id'] else 'N/A'}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_arb:
                    st.markdown(f"""
                    <div style='background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 8px; padding: 0.8rem; height: 195px;'>
                        <h4 style='color: #6366f1; margin-top:0; font-size: 1.05rem;'>🟡 Arbitrum Sepolia</h4>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>時延:</b> {rep['arbitrum']['latency_sec']:.4f} 秒</p>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>手續費:</b> <span style='color: #6366f1; font-weight: bold;'>${rep['arbitrum']['fee_usd']:.6f} USD</span></p>
                        <p style='margin: 4px 0; font-size: 0.8rem; color:#9ca3af;'><b>網關載荷:</b> 中 (需簽名與餘額管理)</p>
                        <p style='font-size: 0.75rem; color:#9ca3af; margin: 4px 0; word-break: break-all;'><b>Tx:</b> {rep['arbitrum']['tx_hash'][:12] if rep['arbitrum']['tx_hash'] else 'N/A'}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with c_eth:
                    st.markdown(f"""
                    <div style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 0.8rem; height: 195px;'>
                        <h4 style='color: #ef4444; margin-top:0; font-size: 1.05rem;'>🔴 Ethereum Sepolia</h4>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>時延:</b> {rep['ethereum']['latency_sec']:.4f} 秒</p>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>手續費:</b> <span style='color: #ef4444; font-weight: bold;'>${rep['ethereum']['fee_usd']:.4f} USD</span></p>
                        <p style='margin: 4px 0; font-size: 0.8rem; color:#9ca3af;'><b>網關載荷:</b> 中 (高昂 Gas 管理)</p>
                        <p style='font-size: 0.75rem; color:#9ca3af; margin: 4px 0; word-break: break-all;'><b>Tx:</b> {rep['ethereum']['tx_hash'][:12] if rep['ethereum']['tx_hash'] else 'N/A'}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with c_sol:
                    st.markdown(f"""
                    <div style='background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 0.8rem; height: 195px;'>
                        <h4 style='color: #f59e0b; margin-top:0; font-size: 1.05rem;'>🟡 Solana Devnet</h4>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>時延:</b> {rep['solana']['latency_sec']:.4f} 秒</p>
                        <p style='margin: 4px 0; font-size: 0.85rem;'><b>手續費:</b> <span style='color: #10b981; font-weight: bold;'>${rep['solana']['fee_usd']:.6f} USD</span></p>
                        <p style='margin: 4px 0; font-size: 0.8rem; color:#9ca3af;'><b>網關載荷:</b> 中 (Ed25519 簽名加密)</p>
                        <p style='font-size: 0.75rem; color:#9ca3af; margin: 4px 0; word-break: break-all;'><b>Tx:</b> {rep['solana']['tx_hash'][:12] if rep['solana']['tx_hash'] else 'N/A'}...</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                #### 💡 學術分析結論：為何 IOTA 是 IoT 數據完整性驗證的最優解？
                1. **零手續費（Feeless Architecture）**：IoT 設備通常會產生高頻、長期的遙測數據。即使 EVM L2（如 Arbitrum）的單次交易費用極低（約 $0.001 USD），在海量設備與長期運行下，累積的手續費與 **Gas 錢包的管理維護成本（避免餘額不足而停止公證）**仍是不可承受之重。IOTA 提供完全免手續費的上鏈，從根本上解決了運營成本問題。
                2. **零代幣狀態管理的硬體減載**：EVM/Solana 鏈上鏈需要網關在本地維護私鑰、簽署交易，並追蹤 nonce 值與錢包餘額。這要求 IoT 網關具備較強的本地安全晶片與複雜的軟體狀態機。而 IOTA 支持使用 L1 的 `TaggedData` 負載直接寫入，網關無需託管任何資產，大幅降低了設備被破解時私鑰外洩的風險與硬體成本。
                3. **非同步與平行處理能力**：IOTA 基於 DAG（Directed Acyclic Graph）的 Tangle 拓撲，沒有傳統區塊鏈的「排隊打包」限制，交易可以直接平行掛載，在 IoT 設備並發寫入時具備極佳的擴展性。
                ---
                """)

        # List records
        if records:
            for idx, r in enumerate(records[:15]): # Show latest 15
                # Define status indicator
                status = r['iota_status']
                if status == "ANCHORED":
                    status_header = "🔗 [已上鏈]"
                elif status == "PENDING":
                    status_header = "⏳ [未上鏈]"
                elif status == "NOT_ANCHORED":
                    status_header = "💻 [僅本地]"
                else:
                    status_header = "❌ [上鏈失敗]"
                    
                tamper_header = " ⚠️ [本地遭改!]" if r['is_tampered'] else ""
                
                # Parse record date
                try:
                    dt = datetime.fromisoformat(r['timestamp'].replace("Z", "")).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    dt = r['timestamp'][:19]
                
                expander_title = f"數據 #{r['id'][:8]}... | {dt} | {r['device_id']} | 🌡️ {r['temperature']:.2f}°C | {status_header}{tamper_header}"
                
                with st.expander(expander_title):
                    # HTML Badges
                    if status == "ANCHORED":
                        badge_html = f"<span class='badge badge-anchored'>已上鏈存證 (ANCHORED)</span>"
                    elif status == "PENDING":
                        badge_html = f"<span class='badge badge-pending'>佇列中 (PENDING)</span>"
                    elif status == "NOT_ANCHORED":
                        badge_html = f"<span class='badge' style='background-color: rgba(156, 163, 175, 0.15); color: #9ca3af; border-color: rgba(156, 163, 175, 0.3);'>僅儲存於本地 (NOT_ANCHORED - Event Filtered)</span>"
                    else:
                        badge_html = f"<span class='badge badge-failed'>上鏈失敗 (FAILED)</span>"
                    
                    if r['is_tampered']:
                        badge_html += " <span class='badge badge-failed' style='margin-left: 5px;'>⚠️ 本地已遭改</span>"
                        
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.markdown(f"**完整紀錄 ID**: `{r['id']}`")
                    st.markdown(f"**裝置識別碼 (Device ID)**: `{r['device_id']}` | **韌體版本 (Firmware)**: `v{r['firmware_version']}`")
                    st.markdown(f"**感測時間 (UTC)**: `{r['timestamp']}`")
                    
                    c_details_1, c_details_2, c_details_3 = st.columns(3)
                    c_details_1.metric("溫度 (Temperature)", f"{r['temperature']:.4f} °C")
                    c_details_2.metric("濕度 (Humidity)", f"{r['humidity']:.4f} %")
                    c_details_3.metric("電力 (Power)", f"{r['power']:.4f} W")
                    
                    st.markdown(f"**SQLite 雜湊 (SHA-256 Digest)**: `{r['sha256_hash']}`")
                    
                    # Show Merkle root/proof info if present
                    if r['merkle_root']:
                        st.markdown(f"**Merkle 根雜湊 (Merkle Root)**: `{r['merkle_root']}`")
                        st.markdown(f"**Merkle 證明路徑 (Merkle Proof)**:")
                        st.code(r['merkle_proof'], language="json")
                        
                    if r['iota_block_id']:
                        st.markdown(f"**IOTA 區塊證書 (Block ID)**: `{r['iota_block_id']}`")
                        explorer_url = f"https://explorer.shimmer.network/shimmer/block/{r['iota_block_id']}"
                        st.markdown(f"🔗 [在 Shimmer Explorer 上查看 L1 存證]({explorer_url})")
                    else:
                        st.markdown("**IOTA 區塊證書 (Block ID)**: `無`")
                    
                    # Action buttons in columns
                    c_actions = st.columns(2)
                    with c_actions[0]:
                        run_verification = st.button("🔬 執行三向完整性校驗", key=f"verify_{r['id']}", use_container_width=True)
                    with c_actions[1]:
                        if status in ["PENDING", "NOT_ANCHORED"]:
                            if st.button("🔗 立即將此單筆記錄上鏈", key=f"anchor_single_{r['id']}", use_container_width=True):
                                with st.spinner("正在將此單筆記錄的雜湊公證至 IOTA..."):
                                    try:
                                        res = requests.post(f"{API_BASE}/records/{r['id']}/anchor")
                                        if res.status_code == 200:
                                            st.toast("🎉 單筆記錄成功上鏈公證！", icon="✅")
                                            time.sleep(1.0)
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error(f"上鏈失敗: {res.text}")
                                    except Exception as e:
                                        st.error(f"連線出錯: {e}")
                        else:
                            st.button("🔗 立即將此單筆記錄上鏈", key=f"anchor_single_{r['id']}", disabled=True, use_container_width=True)
                    
                    if run_verification:
                        with st.spinner("正在取得區塊鏈帳本數據並進行雜湊與 Merkle Proof 密碼學核對..."):
                            try:
                                v_res = requests.post(f"{API_BASE}/records/{r['id']}/verify").json()
                                
                                st.markdown("#### ⚖️ 雜湊三向與 Merkle Proof 對比報告")
                                
                                # Matches check
                                local_ok = v_res['local_match']
                                iota_ok = v_res['iota_match']
                                risk = v_res['risk_level']
                                
                                # Show status indicators
                                cc1, cc2 = st.columns(2)
                                with cc1:
                                    if local_ok:
                                        st.success("🟢 1. 本地一致性驗證: 成功\n\n(重新計算的雜湊，與資料庫中儲存的雜湊完全吻合)")
                                    else:
                                        st.error("🔴 1. 本地一致性驗證: 失敗!\n\n(資料庫原始數值已被篡改，與原計算的雜湊不相符)")
                                        
                                with cc2:
                                    if iota_ok:
                                        if r['iota_status'] == "NOT_ANCHORED":
                                            st.info("ℹ️ 2. 區塊鏈錨定驗證: 成功 (免檢驗)\n\n(常態數據符合 Event Filter 免上鏈規則，本地驗證已足夠)")
                                        else:
                                            st.success("🟢 2. 區塊鏈錨定驗證: 成功\n\n(重構的雜湊與 Merkle 證明，經密碼學推演與 IOTA 上錨定的 Merkle Root 完全一致)")
                                    else:
                                        st.error("🔴 2. 區塊鏈錨定驗證: 失敗!\n\n(雜湊經 Merkle 證明重構後，與 IOTA 帳本上不可篡改的 Merkle Root 不吻合！)")
                                
                                # Hash table
                                st.markdown(f"""
                                | 數據節點 | 雜湊值 (SHA-256 Digest) |
                                | :--- | :--- |
                                | 💻 **重新計算雜湊 (Recalculated)** | `{v_res['calculated_hash']}` |
                                | 💾 **資料庫雜湊 (SQLite Stored)** | `{v_res['db_stored_hash']}` |
                                | ⛓️ **Tangle 錨定根 (IOTA Anchor Root)** | `{v_res['iota_stored_hash'] or '無 (未上鏈)'}` |
                                """)
                                
                                # Risk levels cards
                                if risk == "VALID":
                                    st.markdown("<div style='background-color:rgba(16, 185, 129, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #10b981; font-weight:700;'>✅ 數據完整性查核: 通過。無篡改痕跡。 (VALID)</div>", unsafe_allow_html=True)
                                elif risk == "WARNING":
                                    st.markdown("<div style='background-color:rgba(245, 158, 11, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #f59e0b; font-weight:700;'>⚠️ 數據完整性查核: 警告！偵測到 SQLite 本地資料庫數值遭到竄改！ (WARNING)</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown("<div style='background-color:rgba(239, 68, 68, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #ef4444; font-weight:700;'>🚨 數據完整性查核: 嚴重警報！數據雜湊與區塊鏈防篡改帳本不吻合！ (CRITICAL)</div>", unsafe_allow_html=True)
                                    
                            except Exception as ex:
                                st.error(f"校驗失敗: {ex}")
        else:
            st.info("無存證資料。請等待感測器寫入。")
            
    with col_tamper:
        st.markdown("""
        <div class='glass-card'>
            <div class='card-header' style='border-left-color: #ef4444;'>🧪 期末專案篡改展示組 (Tamper Simulation)</div>
            <p style='font-size:0.9rem; color:#9ca3af;'>
            在此區域可以模擬惡意攻擊者入侵 SQLite 資料庫。點擊按鈕後，會直接在資料庫中篡改感測器數值，但不會更改當初計算的雜湊與區塊鏈上的存證紀錄。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if records:
            # 用 session_state 來保留已選取的 record ID，防止自動更新重置選擇
            if "tamper_selected_id" not in st.session_state:
                st.session_state.tamper_selected_id = None

            # Create option mapping
            options_list = []
            mapping = {}
            default_index = 0
            for i, r in enumerate(records[:10]):
                try:
                    dt = datetime.fromisoformat(r['timestamp'].replace("Z", "")).strftime("%H:%M:%S")
                except:
                    dt = r['timestamp'][:19]
                label = f"ID: {r['id'][:8]}... | 時間: {dt} | 原溫度: {r['temperature']:.2f}°C"
                options_list.append(label)
                mapping[label] = r
                if st.session_state.tamper_selected_id == r['id']:
                    default_index = i
                
            selected_label = st.selectbox("選擇要進行篡改的數據 ID", options_list, index=default_index)
            selected_record = mapping[selected_label]
            st.session_state.tamper_selected_id = selected_record['id']
            
            st.markdown(f"**已選擇數據 UUID**: `{selected_record['id']}`")
            
            # Tamper fields
            t_temp = st.number_input("竄改後的溫度值 (°C)", value=float(selected_record['temperature'] + 10.0), step=1.0)
            t_hum = st.number_input("竄改後的濕度值 (%)", value=float(selected_record['humidity'] - 15.0), step=1.0)
            t_power = st.number_input("竄改後的電力值 (W)", value=float(selected_record['power'] + 50.0), step=1.0)
            
            if st.button("🔥 執行惡意資料篡改", use_container_width=True):
                payload = {
                    "temperature": t_temp,
                    "humidity": t_hum,
                    "power": t_power
                }
                try:
                    res = requests.post(f"{API_BASE}/records/{selected_record['id']}/tamper", json=payload)
                    if res.status_code == 200:
                        st.toast("⚡ 資料已直接於資料庫中被強行修改！請於左側對該筆資料重新執行『三向完整性校驗』查看警報成果。", icon="🔥")
                        time.sleep(2)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"篡改失敗: {res.text}")
                except Exception as e:
                    st.error(f"連線出錯: {e}")
        else:
            st.info("等有感測數據寫入後，即可在此展示資料庫篡改警報流程。")

with tab_threat_model:
    st.markdown("""
    <div class='glass-card'>
        <div class='card-header' style='border-left-color: #10b981;'>🛡️ 專案安全威脅模型 (Threat Modeling) 與系統防禦設計</div>
        <p style='font-size:0.95rem; color:#d1d5db; line-height:1.6;'>
        本區塊展示本專案針對物聯網邊緣數據採集、傳輸、儲存等階段所設計的安全防禦體系，並對應六大威脅向量進行緩解說明。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 📂 威脅向量與防禦對策矩陣
    
    | 威脅目標 & 描述 | 潛在後果 | 系統防禦機制與設計機制 | 校驗警報層級 |
    | :--- | :--- | :--- | :--- |
    | **1. 資料庫數值遭竄改 (SQLite Tampering)**<br>惡意系統管理員或外部入侵者，直接連入後端資料庫修改環境讀數 (如調低溫度以規避故障警報)。 | 資料完整性破壞，監控系統失效。 | **本地雜湊校驗**: 每筆寫入的數據在生成時均被計算為 SHA-256 雜湊儲存。由於雜湊的單向特性，重新對數值計算會得出不同雜湊值。 | `WARNING` |
    | **2. 雜湊覆寫攻擊 (Hash Overwriting)**<br>攻擊者在修改數據的同時，亦重新計算雜湊並更新 SQLite Stored Hash 欄位，企圖規避本地雜湊核對。 | 本地雜湊校驗被欺騙，系統誤以為數據完好。 | **IOTA Tangle Ledger 存證**: 異常數據的雜湊 (或打包 Merkle Root) 已被不可篡改地寫入 IOTA 分布式帳本。系統透過 L1 帳本的根比對直接識破雜湊修改。 | `CRITICAL` |
    | **3. 裝置身份偽造 (Device Spoofing)**<br>惡意偽造裝置偽裝成 Greenhouse Sensor Hub 向後端 API 發送偽造數據。 | 系統混入大量垃圾或偽造數據。 | **元數據聯合雜湊**: 雜湊計算中加入了 `device_id` 與 `firmware_version`。若偽造者未遵循精確的韌體格式與裝備雜湊配對，將無法通過鏈上核對。 | `CRITICAL` |
    | **4. 區塊鏈昂貴手續費與交易壅塞 (Blockchain Scalability & Cost)**<br>IoT 裝置高頻發送數據 (如每 3 秒一次)，若直接將每筆數據逐一錨定上鏈，將產生高昂頻寬消耗與交易延遲。 | 交易隊列壅塞，區塊鏈網路效能降低，模擬手續費爆表。 | **Event Filter (事件過濾器)** + **Merkle Tree 樹狀聚合**: <br>1. *Event Filter*: 平時常態數據僅保存在本地，只有在偵測到異常 (Temp > 40°C 等) 時才標記為 `PENDING` 上鏈。<br>2. *Merkle Tree*: 多筆 `PENDING` 事件打包組裝成 Merkle 樹，僅將單一 `Merkle Root` 錨定到 IOTA 上，實現 O(1) 空間複雜度上鏈。 | N/A (架構優化) |
    | **5. 傳輸通道監聽與中間人攻擊 (Man-in-the-Middle)**<br>攻擊者在 Gateway 與後端伺服器傳輸數據時進行竊聽或注入惡意指令。 | Telemetry 數據洩露，控制權遭竊取。 | **企業級安全適配器 (Thaumio)**: 內建 mTLS、JWT 與 SAS Token 加密傳輸管道 (本專案對接 HTTP Gateway 時支援無縫憑證授權)。 | N/A (通訊加密) |
    """)
    
    st.markdown("---")
    st.markdown("### 📊 資料安全流程流向圖 (Data Lifecycle & Trust Flow)")
    
    st.markdown("""
    ```mermaid
    sequenceDiagram
        autonumber
        participant Device as Thaumio Digital Twin (Greenhouse)
        participant API as FastAPI Ingestion Backend
        participant DB as SQLite DB
        participant Tangle as IOTA Testnet (Tangle Ledger)
        
        Device->>API: 1. 發送 Telemetry 數據 (包含裝置 ID、韌體版本)
        API->>API: 2. 計算 SHA-256 Canonical Hash
        API->>API: 3. Event Filter 分流 (判斷是否 >40°C)
        alt 正常數據 (Normal Telemetry)
            API->>DB: 4a. 儲存數據 (標記 iota_status = NOT_ANCHORED)
        else 異常數據 (Anomaly Event)
            API->>DB: 4b. 儲存數據 (標記 iota_status = PENDING)
        end
        
        Note over API, Tangle: 定期或由 Dashboard 點擊觸發 Merkle 樹聚合上鏈
        API->>DB: 5. 檢索所有 PENDING 紀錄
        API->>API: 6. 構建 Merkle 樹，獲取 Merkle Root 與各節點 Proof
        API->>Tangle: 7. 錨定 Merkle Root 到 Tangle 帳本上 (L1 TaggedData)
        Tangle-->>API: 8. 返回 L1 Block ID 證書
        API->>DB: 9. 更新紀錄狀態為 ANCHORED，寫入 Block ID、Merkle Root 與 Proof
    ```
    """, unsafe_allow_html=True)

# Auto rerun handler
if auto_refresh:
    time.sleep(5)
    st.cache_data.clear()
    st.rerun()
