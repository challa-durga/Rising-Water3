from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os
import json

app = Flask(__name__)

# Load models and scaler
MODELS = {}
SCALER = None
METRICS = {}

# Feature names in the exact training order
FEATURE_COLS = [
    'Temp', 'Humidity', 'Cloud_Visibility', 'ANNUAL',
    'Jan_Feb', 'Mar_May', 'Jun_Sep', 'Oct_Dec', 'avgjune', 'sub'
]

def init_app():
    global SCALER, METRICS
    models_dir = 'models'
    
    # Load Scaler
    scaler_path = os.path.join(models_dir, 'scaler.joblib')
    if os.path.exists(scaler_path):
        SCALER = joblib.load(scaler_path)
        print("StandardScaler loaded.")
    else:
        print("Warning: scaler.joblib not found!")

    # Load all models
    model_names = ['decision_tree', 'random_forest', 'knn', 'xgboost']
    for name in model_names:
        path = os.path.join(models_dir, f'{name}_model.joblib')
        if os.path.exists(path):
            MODELS[name] = joblib.load(path)
            print(f"Model {name} loaded.")
        else:
            print(f"Warning: {name}_model.joblib not found!")

    # Load metrics
    metrics_path = os.path.join(models_dir, 'metrics_summary.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            METRICS = json.load(f)
        print("Metrics summary loaded.")

# Load models on startup
init_app()

@app.route('/')
def index():
    """Scenario 1: Early Flood Warning and Evacuation Planning"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Scenario 2: Disaster Response and Resource Allocation (Multi-Region monitoring)"""
    return render_template('dashboard.html')

@app.route('/validation')
def validation():
    """Scenario 3: Model Validation and Performance Assessment"""
    # Pass metrics to template for display
    return render_template('validation.html', metrics=METRICS)

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # Check model and scaler status
        if not SCALER or not MODELS:
            return jsonify({'error': 'Models and scaler are not initialized. Run training first.'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Parse inputs (with fallback/default values if missing)
        try:
            temp = float(data.get('Temp', 28.0))
            humidity = float(data.get('Humidity', 80.0))
            cloud_vis = float(data.get('Cloud_Visibility', 6.0))
            
            # Rainfalls
            jan_feb = float(data.get('Jan_Feb', 50.0))
            mar_may = float(data.get('Mar_May', 150.0))
            jun_sep = float(data.get('Jun_Sep', 1500.0))
            oct_dec = float(data.get('Oct_Dec', 200.0))
            
            # Annual rainfall is sum of seasonal components if not explicitly provided
            annual = float(data.get('ANNUAL', jan_feb + mar_may + jun_sep + oct_dec))
            
            avgjune = float(data.get('avgjune', jun_sep / 4.0)) # default to quarter of monsoon rainfall
            sub = int(data.get('sub', 3)) # sub-basin index (1 to 5)
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid input values: {str(e)}'}), 400

        # Construct dataframe with exact column names for model
        input_data = pd.DataFrame([[
            temp, humidity, cloud_vis, annual,
            jan_feb, mar_may, jun_sep, oct_dec, avgjune, sub
        ]], columns=FEATURE_COLS)

        # Scale features
        input_scaled = SCALER.transform(input_data)

        # Predict with all models
        results = {}
        for name, model in MODELS.items():
            # Get probability if model supports it
            prob = None
            if hasattr(model, "predict_proba"):
                prob_arr = model.predict_proba(input_scaled)
                # prob of class 1 (flood)
                prob = float(prob_arr[0][1])
            
            prediction = int(model.predict(input_scaled)[0])
            
            # Determine risk level from probability
            if prob is not None:
                if prob < 0.35:
                    risk_level = "Low"
                elif prob < 0.70:
                    risk_level = "Medium"
                else:
                    risk_level = "High"
            else:
                risk_level = "High" if prediction == 1 else "Low"
                prob = 1.0 if prediction == 1 else 0.0
                
            results[name] = {
                'prediction': prediction,
                'probability': prob,
                'risk_level': risk_level
            }

        return jsonify({
            'inputs': data,
            'predictions': results,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify(METRICS)

if __name__ == '__main__':
    # Run server locally
    app.run(debug=True, port=5000)
