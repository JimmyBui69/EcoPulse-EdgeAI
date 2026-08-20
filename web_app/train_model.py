import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# 1. Generate Synthetic Microclimate Calibration Dataset
# Based on NOAA Heat Index approximation and temporal dynamic gradients
np.random.seed(42)
n_samples = 500

# Simulate ambient temperature (25 - 38 deg C) and relative humidity (45% - 90%)
temp = np.random.uniform(25.0, 38.0, n_samples)
hum = np.random.uniform(45.0, 90.0, n_samples)

# Simulate rate of change (temporal gradients: Delta T, Delta H)
delta_t = np.random.normal(0.0, 0.5, n_samples)
delta_h = np.random.normal(0.0, 1.2, n_samples)

# Target Future Heat Index calculation
target_hi = (
    1.05 * temp 
    + 0.12 * hum 
    + 2.3 * delta_t 
    + 0.4 * delta_h 
    - 2.1 
    + np.random.normal(0, 0.1, n_samples)
)

# Package into DataFrame
df = pd.DataFrame({
    'temp': temp,
    'hum': hum,
    'delta_t': delta_t,
    'delta_h': delta_h,
    'future_heat_index': target_hi
})

# Export calibration dataset
df.to_csv('sensor_data.csv', index=False)
print("-> [OK] Successfully generated: sensor_data.csv")

# 2. Train Multi-variable Ridge Regression Model
X = df[['temp', 'hum', 'delta_t', 'delta_h']]
y = df['future_heat_index']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = Ridge(alpha=1.0)
model.fit(X_train, y_train)

# Evaluate model performance
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n=== MACHINE LEARNING TRAINING RESULTS ===")
print(f"R2 Score (Variance Explained): {r2:.4f}")
print(f"Mean Squared Error (MSE): {mse:.4f}")
print("\n=== EMBEDDED MODEL WEIGHTS FOR ARDUINO C++ ===")
print(f"const float WEIGHT_TEMP    = {model.coef_[0]:.3f}f;")
print(f"const float WEIGHT_HUM     = {model.coef_[1]:.3f}f;")
print(f"const float WEIGHT_DELTA_T = {model.coef_[2]:.3f}f;")
print(f"const float WEIGHT_DELTA_H = {model.coef_[3]:.3f}f;")
print(f"const float MODEL_BIAS     = {model.intercept_:.3f}f;")