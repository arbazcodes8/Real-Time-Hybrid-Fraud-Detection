import json
import time
import random
import logging
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
TOPIC = 'financial_transactions'

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

logging.info("AegisStream DEMO Simulator initialized (3-Tier Logic).")
transaction_id = 50000
counter = 0

def generate_transaction(override_id=None, fraud_type="SAFE"):
    global transaction_id
    
    if override_id is None:
        transaction_id += 1
        current_id = transaction_id
    else:
        current_id = override_id
        
    if fraud_type == "CRITICAL":
        amount = round(random.uniform(15000.0, 45000.0), 2) 
        v_features = [random.gauss(5, 2) for _ in range(28)] 
    elif fraud_type == "SUSPICIOUS":
        amount = round(random.uniform(3000.0, 6000.0), 2)
        v_features = [random.gauss(1.5, 1) for _ in range(28)] 
    else: # SAFE
        amount = round(random.uniform(5.0, 150.0), 2)
        v_features = [random.gauss(0, 1) for _ in range(28)]
        
    data = {
        "TransactionID": current_id, 
        "Amount": amount
    }
    for i in range(1, 29):
        data[f"V{i}"] = v_features[i-1]
        
    return data

try:
    while True:
        counter += 1
        
        # --- 1. INJECT CEP VELOCITY ATTACK ---
        if counter % 45 == 0:
            cep_id = transaction_id + 1
            logging.warning(f"[CEP INJECTION] Velocity fraud sequence for ID: {cep_id}")
            for _ in range(5): 
                txn = generate_transaction(override_id=cep_id, fraud_type="SAFE") 
                producer.send(TOPIC, txn)
                time.sleep(0.01) 
            transaction_id += 1 
                
        # --- 2. INJECT CRITICAL ML ATTACK (> 0.85 Score) ---
        elif counter % 20 == 0:
            logging.warning("[ML INJECTION] Critical statistical anomaly generated")
            txn = generate_transaction(fraud_type="CRITICAL")
            producer.send(TOPIC, txn)

        # --- 3. INJECT SUSPICIOUS ML ATTACK (~ 0.60 Score) ---
        elif counter % 12 == 0:
            logging.warning("[ML INJECTION] Borderline suspicious transaction generated")
            txn = generate_transaction(fraud_type="SUSPICIOUS")
            producer.send(TOPIC, txn)
            
        # --- 4. NORMAL SAFE TRANSACTIONS (< 0.40 Score) ---
        else:
            txn = generate_transaction(fraud_type="SAFE")
            producer.send(TOPIC, txn)
            logging.info(f"Transaction Processed | ID: {txn['TransactionID']} | Amount: ${txn['Amount']}")
            
        producer.flush()
        time.sleep(0.1) 

except KeyboardInterrupt:
    logging.info("Stream interrupted by user.")
    producer.close()