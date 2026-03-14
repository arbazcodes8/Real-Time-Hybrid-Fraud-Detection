# Real-Time Framework for Hybrid Fraud Detection

## Project Overview
This repository contains the source code and documentation for a real-time, hybrid stream-processing framework designed for enterprise-grade financial fraud detection. Built to address the latency gaps in traditional batch-processing systems, this architecture evaluates unbounded financial data streams with sub-second latency.

## Architecture Highlights
The framework utilizes a fully decoupled, event-driven architecture:
* **Ingestion Layer:** Apache Kafka buffers high-throughput, simulated transactions.
* **Processing Engine:** Apache Flink consumes the stream, executing a dual-layer defense mechanism.
* **Layer 1 (CEP):** A Complex Event Processing state-machine detects temporal velocity micro-burst attacks (e.g., 5 transactions within 50ms).
* **Layer 2 (ML Inference):** An embedded XGBoost Machine Learning model calculates real-time probabilistic risk scores on PCA-transformed features.
* **Visualization Layer:** An asynchronous Streamlit dashboard routes threats into a 3-tier classification matrix (Safe, Suspicious, Critical).

## Repository Structure
* `src/`: Contains the Python Kafka Producer, Streamlit Dashboard, and Flink processing logic.
* `docs/`: Contains the official capstone project documentation.
* `architecture.png`: Visual diagram of the data pipeline and processing layers.
* `setup_instructions.md`: Detailed execution runbook for deploying the local cluster.

## Academic Context
**Institution:** Alliance University, Bangalore 
**Program:** B.Tech Computer Science & Engineering (Data Analytics)
**Module:** 6th Semester Capstone Project