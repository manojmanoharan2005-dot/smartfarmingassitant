import os

class CropPredictor:
    def __init__(self, model_dir="ml_models"):
        self.model = None
        self.scaler = None
        self.use_sklearn = False
        self.load_model()
    
    def load_model(self):
        """Load the trained model or fallback to simple model"""
        try:
            # Try to load sklearn model first
            import joblib
            # Use absolute path relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, 'crop_recommendation_model.joblib')
            scaler_path = os.path.join(base_dir, 'feature_scaler.joblib')
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.use_sklearn = True
                print("✅ Sklearn model loaded successfully!")
                return True
        except ImportError:
            print("⚠️ Sklearn not available, using simple model")
        except Exception as e:
            print(f"⚠️ Error loading sklearn model: {e}")
        
        # Fallback to simple rule-based model
        try:
            from ml_models.crop_model_simple import simple_crop_predictor
            self.simple_model = simple_crop_predictor
            print("✅ Simple rule-based model loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Error loading simple model: {e}")
            return False
    
    def predict_crop_recommendation(self, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
        """Predict crop recommendation using available model"""
        try:
            if self.use_sklearn and self.model and self.scaler:
                # Use sklearn model
                import numpy as np
                features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])
                features_scaled = self.scaler.transform(features)
                
                prediction = self.model.predict(features_scaled)[0]
                probabilities = self.model.predict_proba(features_scaled)[0]
                
                class_names = self.model.classes_
                crop_probabilities = []
                
                for crop, prob in zip(class_names, probabilities):
                    crop_probabilities.append({
                        'name': crop.capitalize(),
                        'probability': float(prob),
                        'confidence_percentage': float(prob * 100),
                        'priority': 'High' if prob > 0.7 else 'Medium' if prob > 0.4 else 'Low'
                    })
                
                crop_probabilities.sort(key=lambda x: x['probability'], reverse=True)
                
                return {
                    'recommended_crop': prediction.capitalize(),
                    'top_recommendations': crop_probabilities[:6],
                    'input_parameters': {
                        'nitrogen': nitrogen,
                        'phosphorus': phosphorus,
                        'potassium': potassium,
                        'temperature': temperature,
                        'humidity': humidity,
                        'ph': ph,
                        'rainfall': rainfall
                    }
                }
            else:
                # Use simple rule-based model
                return self.simple_model.predict_crop_recommendation(
                    nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall
                )
                
        except Exception as e:
            print(f"Error in prediction: {e}")
            # Return fallback recommendation
            return {
                'recommended_crop': 'Rice',
                'top_recommendations': [
                    {'name': 'Rice', 'probability': 0.85, 'confidence_percentage': 85, 'priority': 'High'},
                    {'name': 'Wheat', 'probability': 0.70, 'confidence_percentage': 70, 'priority': 'Medium'},
                    {'name': 'Maize', 'probability': 0.60, 'confidence_percentage': 60, 'priority': 'Medium'},
                ],
                'input_parameters': {
                    'nitrogen': nitrogen, 'phosphorus': phosphorus, 'potassium': potassium,
                    'temperature': temperature, 'humidity': humidity, 'ph': ph, 'rainfall': rainfall
                }
            }

# Global predictor instance
crop_predictor = CropPredictor()
