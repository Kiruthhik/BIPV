import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load your dataset
dataset = pd.read_csv(r'C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\BIPV\BIPV_Panel_Recommendations_Ahmedabad.csv')

# Prepare features (X) and multiple targets (y)
X = dataset[["Building Type", "Facade Material", "Solar Irradiance", "Surface Area (m²)"]]
y_high = dataset["Highly Recommended"]
y_medium = dataset["Medium Recommended"]
y_low = dataset["Least Recommended"]

# Encode categorical features
X = pd.get_dummies(X, columns=["Building Type", "Facade Material", "Solar Irradiance"], drop_first=True)

# Log the expected feature names (columns after encoding)
print("Model's Expected Feature Names (Columns):", X.columns)

# Train-test split for each target
X_train, X_test, y_train_high, y_test_high = train_test_split(X, y_high, test_size=0.2, random_state=42)
_, _, y_train_medium, y_test_medium = train_test_split(X, y_medium, test_size=0.2, random_state=42)
_, _, y_train_low, y_test_low = train_test_split(X, y_low, test_size=0.2, random_state=42)

# Train Random Forest models for each target
rf_model_high = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model_high.fit(X_train, y_train_high)

rf_model_medium = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model_medium.fit(X_train, y_train_medium)

rf_model_low = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model_low.fit(X_train, y_train_low)

# Evaluate accuracy for each model
accuracy_high = accuracy_score(y_test_high, rf_model_high.predict(X_test))
accuracy_medium = accuracy_score(y_test_medium, rf_model_medium.predict(X_test))
accuracy_low = accuracy_score(y_test_low, rf_model_low.predict(X_test))

print(f"Accuracy (High Recommendation): {accuracy_high * 100:.2f}%")
print(f"Accuracy (Medium Recommendation): {accuracy_medium * 100:.2f}%")
print(f"Accuracy (Low Recommendation): {accuracy_low * 100:.2f}%")

# Predict for a sample input
new_data = pd.DataFrame({
    "Building Type": ["industrial"],
    "Facade Material": ["concrete"],
    "Solar Irradiance": ["medium"],
    "Surface Area (m²)": [3000]
})

# Encode the sample input
new_data_encoded = pd.get_dummies(new_data, columns=["Building Type", "Facade Material", "Solar Irradiance"], drop_first=True)
new_data_encoded = new_data_encoded.reindex(columns=X.columns, fill_value=0)  # Align with training data

# Make predictions for each recommendation level
pred_high = rf_model_high.predict(new_data_encoded)
pred_medium = rf_model_medium.predict(new_data_encoded)
pred_low = rf_model_low.predict(new_data_encoded)

print("Predicted Highly Recommended Panel:", pred_high[0])
print("Predicted Medium Recommended Panel:", pred_medium[0])
print("Predicted Least Recommended Panel:", pred_low[0])

# Example to access feature importances
print("Feature Importances:", rf_model_high.feature_importances_)
