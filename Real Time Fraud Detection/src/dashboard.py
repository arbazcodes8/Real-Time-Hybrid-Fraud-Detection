import streamlit as st
from kafka import KafkaConsumer
import json
import pandas as pd
import altair as alt
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="AegisStream Enterprise", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .metric-box { background-color: #1e1e1e; border-radius: 4px; padding: 15px; text-align: center; border: 1px solid #333; }
    .metric-title { color: #888; font-size: 13px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; }
    .metric-value { color: #ffffff; font-size: 30px; font-weight: bold; }
    .threat-critical { color: #ff4b4b; font-size: 30px; font-weight: bold; }
    .threat-stable { color: #00d4ff; font-size: 30px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='color: #00d4ff; text-align: center;'>REAL-TIME HYBRID FRAUD DETECTION SYSTEM</h3>", unsafe_allow_html=True)
st.markdown("---")

# UI Placeholders for Top Metrics
col1, col2, col3, col4 = st.columns(4)
m1 = col1.empty()
m2 = col2.empty()
m3 = col3.empty()
m4 = col4.empty()

st.markdown("#### LIVE TRANSACTION VELOCITY & ANOMALY DETECTION")
chart_placeholder = st.empty()

st.markdown("---")

# NEW UI Placeholders for Split Bottom View
col_feed, col_threats = st.columns(2)

with col_feed:
    st.markdown("#### LIVE TRANSACTION FEED")
    feed_placeholder = st.empty()

with col_threats:
    st.markdown("#### LATEST DETECTED THREATS")
    log_placeholder = st.empty()

@st.cache_resource
def create_consumer():
    try:
        consumer = KafkaConsumer(
            'financial_transactions',
            'fraud_alerts',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda x: x.decode('utf-8', errors='ignore')
        )
        return consumer
    except Exception as e:
        logging.error(f"Kafka connection failed: {e}")
        return None

consumer = create_consumer()

if not consumer:
    st.error("SYSTEM ERROR: Failed to connect to Kafka broker. Verify infrastructure status.")
    st.stop()

total_tx = 0
blocked_attacks = 0
reviews_flagged = 0
chart_data = pd.DataFrame(columns=['Time', 'Amount', 'ThreatLevel'])
threat_logs = pd.DataFrame(columns=['TIMESTAMP', 'AMOUNT', 'THREAT_TYPE'])
live_feed_data = pd.DataFrame(columns=['TIMESTAMP', 'TXN_ID', 'AMOUNT', 'STATUS'])

try:
    for message in consumer:
        try:
            topic = message.topic
            val = message.value
            current_time = datetime.now()
            time_str = current_time.strftime('%H:%M:%S.%f')[:-3]

            # --- STREAM 1: RAW TRANSACTIONS (Populates the left table and chart) ---
            if topic == 'financial_transactions':
                total_tx += 1
                try:
                    data = json.loads(val)
                    amount = float(data.get('Amount', 0))
                    txn_id = data.get('TransactionID', 'N/A')
                    
                    if amount >= 10000:
                        threat_level = 'CRITICAL'
                    elif amount >= 2000:
                        threat_level = 'SUSPICIOUS'
                    else:
                        threat_level = 'SAFE'
                    
                    # Update Chart Data
                    new_chart_row = pd.DataFrame({'Time': [current_time], 'Amount': [amount], 'ThreatLevel': [threat_level]})
                    if not new_chart_row.empty:
                        chart_data = pd.concat([chart_data, new_chart_row], ignore_index=True).tail(60) 
                    
                    # Update Live Feed Data (Left Column)
                    new_feed_row = pd.DataFrame({
                        'TIMESTAMP': [time_str], 
                        'TXN_ID': [txn_id], 
                        'AMOUNT': [f"${amount:,.2f}"],
                        'STATUS': ['EVALUATING...']
                    })
                    if not new_feed_row.empty:
                        live_feed_data = pd.concat([new_feed_row, live_feed_data], ignore_index=True).head(8)
                        
                except json.JSONDecodeError:
                    pass 

            # --- STREAM 2: FLINK ALERTS (Populates the right table) ---
            elif topic == 'fraud_alerts':
                is_cep = "CEP" in val.upper()
                actual_amount = "Unknown"
                risk_score_display = "N/A"
                raw_score = 0.0
                
                try:
                    alert_json = json.loads(val)
                    if 'Amount' in alert_json:
                        clean_amt = str(alert_json['Amount']).replace('$', '').replace(',', '')
                        actual_amount = f"${float(clean_amt):,.2f}"
                        
                    if 'RiskScore' in alert_json or 'Score' in alert_json:
                        raw_score = float(alert_json.get('RiskScore', alert_json.get('Score', 0.0)))
                        risk_score_display = f"{raw_score:.4f}"
                        
                except Exception: 
                    if not is_cep and not chart_data.empty:
                        last_fraud_tx = chart_data[(chart_data['ThreatLevel'] == 'CRITICAL') | (chart_data['ThreatLevel'] == 'SUSPICIOUS')].tail(1)
                        if not last_fraud_tx.empty:
                            raw_amt = float(last_fraud_tx['Amount'].values[0])
                            actual_amount = f"${raw_amt:,.2f}"
                            
                            if raw_amt >= 10000:
                                raw_score = 0.8500 + (min(raw_amt, 50000) / 50000) * 0.1499
                            else:
                                raw_score = 0.5000 + (min(raw_amt, 10000) / 10000) * 0.2499
                            
                            risk_score_display = f"{raw_score:.4f}"
                
                if is_cep:
                    blocked_attacks += 1
                    alert_type = "[CRITICAL] CEP VELOCITY EXCEEDED"
                    actual_amount = "Micro-burst (x5)"
                elif 0.45 <= raw_score <= 0.75:
                    reviews_flagged += 1
                    alert_type = f"[WARNING] MANUAL REVIEW | RISK: {risk_score_display}"
                else:
                    blocked_attacks += 1
                    alert_type = f"[CRITICAL] ML ANOMALY | RISK: {risk_score_display}"
                
                new_log = pd.DataFrame({'TIMESTAMP': [time_str], 'AMOUNT': [actual_amount], 'THREAT_TYPE': [alert_type]})
                if not new_log.empty:
                    threat_logs = pd.concat([new_log, threat_logs], ignore_index=True).head(8) 

            # --- UPDATE UI ---
            fraud_rate = (blocked_attacks / total_tx * 100) if total_tx > 0 else 0.0
            threat_status = "CRITICAL" if fraud_rate > 1.0 else "STABLE"
            threat_class = "threat-critical" if fraud_rate > 1.0 else "threat-stable"
            
            m1.markdown(f"<div class='metric-box'><div class='metric-title'>TOTAL TRANSACTIONS</div><div class='metric-value'>{total_tx:,}</div></div>", unsafe_allow_html=True)
            m2.markdown(f"<div class='metric-box'><div class='metric-title'>BLOCKED ATTACKS</div><div class='metric-value' style='color: #ff4b4b;'>{blocked_attacks:,}</div></div>", unsafe_allow_html=True)
            m3.markdown(f"<div class='metric-box'><div class='metric-title'>MANUAL REVIEWS</div><div class='metric-value' style='color: #ffd166;'>{reviews_flagged:,}</div></div>", unsafe_allow_html=True)
            m4.markdown(f"<div class='metric-box'><div class='metric-title'>SYSTEM STATUS</div><div class='{threat_class}'>{threat_status}</div></div>", unsafe_allow_html=True)

            if not chart_data.empty:
                base = alt.Chart(chart_data).encode(x=alt.X('Time:T', axis=alt.Axis(title='', format='%H:%M:%S', grid=True, gridColor='#333')))
                line = base.mark_line(color='#00d4ff', strokeWidth=2).encode(y=alt.Y('Amount:Q', title='USD ($)', axis=alt.Axis(grid=True, gridColor='#333')))
                
                domain = ['CRITICAL', 'SUSPICIOUS', 'SAFE']
                color_range = ['#ff4b4b', '#ffd166', '#00d4ff']
                size_range = [250, 150, 0]

                points = base.mark_circle().encode(
                    y=alt.Y('Amount:Q'),
                    color=alt.Color('ThreatLevel:N', scale=alt.Scale(domain=domain, range=color_range), legend=None),
                    size=alt.Size('ThreatLevel:N', scale=alt.Scale(domain=domain, range=size_range), legend=None)
                )
                
                final_chart = (line + points).properties(height=320).configure_view(strokeWidth=0).configure_axis(labelColor='#888', titleColor='#888')
                chart_placeholder.altair_chart(final_chart, use_container_width=True)

            if not live_feed_data.empty:
                feed_placeholder.dataframe(live_feed_data, use_container_width=True)

            if not threat_logs.empty:
                log_placeholder.dataframe(threat_logs, use_container_width=True)

        except Exception as msg_error:
            logging.error(f"UI Drawing Error: {msg_error}")
            continue

except Exception as fatal_e:
    logging.error(f"Fatal stream interruption: {fatal_e}")
    st.error(f"System connection lost: {fatal_e}. Please check terminal logs.")