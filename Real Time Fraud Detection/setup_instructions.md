# System Setup & Execution Instructions

## Prerequisites
1. Java 11 or higher installed (for Apache Flink).
2. Python 3.9 or higher installed.
3. Docker & Docker Compose (for Kafka/Zookeeper).

## Phase 1: Infrastructure Initialization
1. Start Zookeeper and Kafka via Docker:
   docker-compose up -d

2. Start the local Apache Flink Cluster:
   Navigate to your Flink bin directory and execute:
   start-cluster.bat  (Windows)
   ./start-cluster.sh (Mac/Linux)
   Verify Flink is running at http://localhost:8081

## Phase 2: Engine Deployment
1. Open the Flink Web UI.
2. Navigate to "Submit New Job".
3. Upload the compiled Flink JAR located in the `src/` directory.
4. Set the Entry Class to: `com.fraudproject.FraudDetectorJob`
5. Click "Submit" and ensure the status is "RUNNING".

## Phase 3: Live Stream & Dashboard Execution
1. Open a new terminal and navigate to the project root directory.
2. Install Python dependencies:
   pip install -r requirements.txt

3. Start the Kafka Producer (Synthetic Data Injection):
   python src/producer.py

4. Open a final terminal and launch the SOC Dashboard:
   python -m streamlit run src/dashboard.py

The architecture is now fully operational. The Streamlit UI will automatically open in your default web browser.