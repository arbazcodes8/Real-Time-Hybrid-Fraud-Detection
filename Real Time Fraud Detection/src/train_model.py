import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os

# ==========================================
# 1. GENERATE SYNTHETIC DATA (Simulating Credit Card Data)
# ==========================================
print(" Generating synthetic data...")
np.random.seed(42)
n_samples = 10000

# Generate 28 anonymized features (V1 to V28)
X_features = np.random.normal(0, 1, size=(n_samples, 28))

# Generate 'Amount' column
amounts = np.random.exponential(scale=100, size=n_samples).reshape(-1, 1)

# Combine all 29 features (V1...V28 + Amount)
X = np.hstack((X_features, amounts))

# Generate Target 'Class' (0 = Safe, 1 = Fraud)
# We make fraud rare (approx 2%)
y = np.random.choice([0, 1], size=n_samples, p=[0.98, 0.02])

# Create DataFrame for better handling
feature_names = [f"V{i}" for i in range(1, 29)] + ["Amount"]
df = pd.DataFrame(X, columns=feature_names)
df['Class'] = y

print(f" Data Created: {df.shape}")

# ==========================================
# 2. TRAIN XGBOOST MODEL
# ==========================================
print(" Training XGBoost Model...")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configure XGBoost
# We use 'hist' tree method for compatibility and speed
model = xgb.XGBClassifier(
    objective='binary:logistic',
    eval_metric='logloss',
    use_label_encoder=False,
    max_depth=6,
    learning_rate=0.1,
    n_estimators=100,
    tree_method='hist' 
)

model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"Model Accuracy: {acc * 100:.2f}%")

# ==========================================
# 3. SAVE MODEL FOR JAVA (FLINK)
# ==========================================
model_path = "src/model/fraud_model_java.json"

# Ensure directory exists
os.makedirs(os.path.dirname(model_path), exist_ok=True)

# Save in JSON format (Required for Flink XGBoost library)
model.save_model(model_path)

print(f" Model saved to: {model_path}")
print(" READY! You can now copy this file to your Docker container.")