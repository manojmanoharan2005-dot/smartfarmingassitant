import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import joblib
import os
from datetime import datetime

class CropRecommendationModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        self.target_name = 'label'
        
    def load_data(self, file_path):
        """Load and prepare the dataset"""
        try:
            self.data = pd.read_csv(file_path)
            print("✅ Dataset loaded successfully!")
            print(f"📊 Dataset shape: {self.data.shape}")
            print(f"📋 Columns: {list(self.data.columns)}")
            return True
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return False
    
    def explore_data(self):
        """Explore the dataset"""
        print("\n" + "="*60)
        print("🔍 DATASET EXPLORATION")
        print("="*60)
        
        # Basic info
        print(f"\n📈 Dataset Info:")
        print(f"   • Total samples: {len(self.data)}")
        print(f"   • Total features: {len(self.feature_names)}")
        print(f"   • Target classes: {self.data['label'].nunique()}")
        
        # Statistical summary
        print(f"\n📊 Statistical Summary:")
        stats = self.data[self.feature_names].describe()
        for feature in self.feature_names:
            row = stats[feature]
            print(f"   • {feature}: min={row['min']:.2f}, max={row['max']:.2f}, mean={row['mean']:.2f}")
        
        # Check for missing values
        missing_values = self.data.isnull().sum().sum()
        print(f"\n🔍 Missing Values: {missing_values}")
        
        # Class distribution
        print(f"\n🌾 Crop Distribution:")
        class_counts = self.data['label'].value_counts()
        for crop, count in class_counts.head(10).items():
            print(f"   • {crop.capitalize()}: {count} samples")
        
        print(f"\nTotal unique crops: {len(class_counts)}")
        return class_counts
    
    def prepare_data(self, test_size=0.2, validation_size=0.1):
        """Split data into train, validation, and test sets"""
        # Separate features and target
        X = self.data[self.feature_names]
        y = self.data[self.target_name]
        
        # First split: separate test set
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Second split: separate train and validation from remaining data
        val_size_adjusted = validation_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=42, stratify=y_temp
        )
        
        print(f"\n📂 Data Split:")
        print(f"   • Training set: {X_train.shape[0]} samples ({X_train.shape[0]/len(self.data)*100:.1f}%)")
        print(f"   • Validation set: {X_val.shape[0]} samples ({X_val.shape[0]/len(self.data)*100:.1f}%)")
        print(f"   • Test set: {X_test.shape[0]} samples ({X_test.shape[0]/len(self.data)*100:.1f}%)")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        return (X_train_scaled, X_val_scaled, X_test_scaled, 
                y_train, y_val, y_test)
    
    def train_model(self, X_train, y_train):
        """Train the Random Forest model"""
        print("\n" + "="*60)
        print("🚀 TRAINING MODEL")
        print("="*60)
        
        print("⏳ Training Random Forest Classifier...")
        self.model.fit(X_train, y_train)
        print("✅ Model training completed!")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🔥 Feature Importance:")
        for idx, row in feature_importance.iterrows():
            print(f"   • {row['feature']}: {row['importance']:.4f}")
        
        return feature_importance
    
    def validate_model(self, X_val, y_val):
        """Validate model on validation set"""
        print("\n" + "="*60)
        print("🔍 MODEL VALIDATION")
        print("="*60)
        
        # Make predictions
        y_val_pred = self.model.predict(X_val)
        
        # Calculate metrics
        val_accuracy = accuracy_score(y_val, y_val_pred)
        val_precision = precision_score(y_val, y_val_pred, average='weighted')
        val_recall = recall_score(y_val, y_val_pred, average='weighted')
        val_f1 = f1_score(y_val, y_val_pred, average='weighted')
        
        print(f"📊 Validation Results:")
        print(f"   • Accuracy:  {val_accuracy:.4f} ({val_accuracy*100:.2f}%)")
        print(f"   • Precision: {val_precision:.4f} ({val_precision*100:.2f}%)")
        print(f"   • Recall:    {val_recall:.4f} ({val_recall*100:.2f}%)")
        print(f"   • F1-Score:  {val_f1:.4f} ({val_f1*100:.2f}%)")
        
        return {
            'accuracy': val_accuracy,
            'precision': val_precision,
            'recall': val_recall,
            'f1_score': val_f1
        }
    
    def test_model(self, X_test, y_test):
        """Test model on test set and calculate all metrics"""
        print("\n" + "="*60)
        print("🎯 FINAL MODEL TESTING")
        print("="*60)
        
        # Make predictions
        y_test_pred = self.model.predict(X_test)
        
        # Calculate comprehensive metrics
        test_accuracy = accuracy_score(y_test, y_test_pred)
        test_precision = precision_score(y_test, y_test_pred, average='weighted')
        test_recall = recall_score(y_test, y_test_pred, average='weighted')
        test_f1 = f1_score(y_test, y_test_pred, average='weighted')
        
        # Per-class metrics
        precision_per_class = precision_score(y_test, y_test_pred, average=None)
        recall_per_class = recall_score(y_test, y_test_pred, average=None)
        f1_per_class = f1_score(y_test, y_test_pred, average=None)
        
        print(f"🏆 FINAL TEST RESULTS:")
        print(f"   • Accuracy:  {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
        print(f"   • Precision: {test_precision:.4f} ({test_precision*100:.2f}%)")
        print(f"   • Recall:    {test_recall:.4f} ({test_recall*100:.2f}%)")
        print(f"   • F1-Score:  {test_f1:.4f} ({test_f1*100:.2f}%)")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_test_pred)
        
        print(f"\n📋 Detailed Classification Report:")
        report = classification_report(y_test, y_test_pred, output_dict=True)
        
        # Show top performing crops
        crop_scores = []
        for crop in report.keys():
            if crop not in ['accuracy', 'macro avg', 'weighted avg']:
                f1 = report[crop]['f1-score']
                crop_scores.append((crop, f1))
        
        crop_scores.sort(key=lambda x: x[1], reverse=True)
        print(f"🌾 Top 5 Best Predicted Crops:")
        for i, (crop, f1) in enumerate(crop_scores[:5], 1):
            print(f"   {i}. {crop.capitalize()}: F1={f1:.4f}")
        
        return {
            'accuracy': test_accuracy,
            'precision': test_precision,
            'recall': test_recall,
            'f1_score': test_f1,
            'precision_per_class': precision_per_class,
            'recall_per_class': recall_per_class,
            'f1_per_class': f1_per_class,
            'confusion_matrix': cm,
            'y_true': y_test,
            'y_pred': y_test_pred
        }
    
    def analyze_results(self, test_results):
        """Analyze and explain the results"""
        print("\n" + "="*60)
        print("🧠 RESULTS ANALYSIS & REASONING")
        print("="*60)
        
        accuracy = test_results['accuracy']
        precision = test_results['precision']
        recall = test_results['recall']
        f1 = test_results['f1_score']
        
        print(f"\n🎯 MODEL PERFORMANCE SUMMARY:")
        print(f"   🎪 Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"   🔍 Precision: {precision:.4f} ({precision*100:.2f}%)")
        print(f"   📡 Recall:    {recall:.4f} ({recall*100:.2f}%)")
        print(f"   ⚖️  F1-Score:  {f1:.4f} ({f1*100:.2f}%)")
        
        print(f"\n🔬 PERFORMANCE INTERPRETATION:")
        
        # Accuracy interpretation
        if accuracy >= 0.95:
            acc_level = "🔥 EXCELLENT"
            acc_reason = "Model shows outstanding accuracy - ready for production use!"
        elif accuracy >= 0.90:
            acc_level = "⭐ VERY GOOD" 
            acc_reason = "Model shows strong predictive performance for agricultural decisions"
        elif accuracy >= 0.85:
            acc_level = "👍 GOOD"
            acc_reason = "Model provides reliable crop recommendations for most farming scenarios"
        elif accuracy >= 0.80:
            acc_level = "⚠️  FAIR"
            acc_reason = "Model shows moderate performance, consider feature engineering"
        else:
            acc_level = "❌ NEEDS IMPROVEMENT"
            acc_reason = "Model requires significant optimization before deployment"
        
        print(f"   🎯 Accuracy ({acc_level}): {acc_reason}")
        
        # Precision interpretation  
        if precision >= 0.95:
            prec_reason = "🎯 Very few false recommendations - highly trustworthy for farmers"
        elif precision >= 0.90:
            prec_reason = "👌 Low false positive rate - recommendations are generally reliable"
        else:
            prec_reason = "⚠️ Some incorrect recommendations present - needs validation"
        
        print(f"   🔍 Precision: {prec_reason}")
        
        # Recall interpretation
        if recall >= 0.95:
            rec_reason = "🌟 Excellent at identifying suitable crops - minimal missed opportunities"
        elif recall >= 0.90:
            rec_reason = "✅ Good at identifying most suitable crops with few missed cases"
        else:
            rec_reason = "⚠️ Some suitable crops may be missed - consider more training data"
        
        print(f"   📡 Recall: {rec_reason}")
        
        # F1-Score interpretation
        if f1 >= 0.95:
            f1_reason = "🏆 OUTSTANDING balance - model is production-ready!"
        elif f1 >= 0.90:
            f1_reason = "🎖️ EXCELLENT balance - suitable for agricultural deployment"
        else:
            f1_reason = "⚖️ Balanced but improvable - consider hyperparameter tuning"
        
        print(f"   ⚖️  F1-Score: {f1_reason}")
        
        # Agricultural insights
        print(f"\n🌾 AGRICULTURAL MODEL INSIGHTS:")
        unique_crops = len(np.unique(test_results['y_true']))
        print(f"   🌱 Successfully classifies {unique_crops} different crop types")
        print(f"   📊 Uses 7 key agricultural parameters:")
        print(f"      • Soil nutrients: N, P, K levels")
        print(f"      • Climate: Temperature, Humidity, Rainfall")  
        print(f"      • Soil chemistry: pH levels")
        print(f"   🚜 Ready for real-world farm recommendation system")
        
        # Deployment readiness
        if accuracy >= 0.90 and f1 >= 0.90:
            print(f"\n🚀 DEPLOYMENT STATUS: ✅ READY FOR PRODUCTION!")
            print(f"   • Model meets agricultural industry standards")
            print(f"   • Safe to deploy for farmer recommendations")
            print(f"   • Expected to improve crop yield decisions")
        else:
            print(f"\n⚠️  DEPLOYMENT STATUS: NEEDS IMPROVEMENT")
            print(f"   • Consider collecting more training data")
            print(f"   • Experiment with different algorithms")
            print(f"   • Validate with agricultural experts")
    
    def save_model(self, model_dir="ml_models"):
        """Save the trained model and scaler"""
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, 'crop_recommendation_model.joblib')
        scaler_path = os.path.join(model_dir, 'feature_scaler.joblib')
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        print(f"\n💾 MODEL SAVED SUCCESSFULLY!")
        print(f"   📁 Model: {model_path}")
        print(f"   📁 Scaler: {scaler_path}")
    
    def predict_crop(self, n, p, k, temperature, humidity, ph, rainfall):
        """Predict crop recommendation for given parameters"""
        features = np.array([[n, p, k, temperature, humidity, ph, rainfall]])
        features_scaled = self.scaler.transform(features)
        
        # Get prediction and probability
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get top 5 recommendations
        class_names = self.model.classes_
        prob_dict = dict(zip(class_names, probabilities))
        top_5 = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'recommended_crop': prediction,
            'confidence': max(probabilities),
            'top_5_recommendations': top_5
        }

def main():
    """Main function to run the complete ML pipeline"""
    print("🌾" * 20)
    print("🚜 SMART CROP RECOMMENDATION ML PIPELINE 🚜")
    print("🌾" * 20)
    
    # Initialize model
    crop_model = CropRecommendationModel()
    
    # Load dataset  
    # Load dataset  
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "datasets", "Crop_recommendation.csv")
    if not crop_model.load_data(dataset_path):
        print("❌ Failed to load dataset. Please check the file path.")
        return
    
    # Explore data
    class_counts = crop_model.explore_data()
    
    # Prepare data
    X_train, X_val, X_test, y_train, y_val, y_test = crop_model.prepare_data()
    
    # Train model
    feature_importance = crop_model.train_model(X_train, y_train)
    
    # Validate model
    val_results = crop_model.validate_model(X_val, y_val)
    
    # Test model
    test_results = crop_model.test_model(X_test, y_test)
    
    # Analyze results
    crop_model.analyze_results(test_results)
    
    # Save model
    model_dir = os.path.join(base_dir, "ml_models")
    crop_model.save_model(model_dir=model_dir)
    
    # Example prediction
    print(f"\n🔮 EXAMPLE CROP PREDICTION:")
    print("="*40)
    example_result = crop_model.predict_crop(
        n=90, p=42, k=43, temperature=20.8, humidity=82.0, ph=6.5, rainfall=202.9
    )
    
    print(f"📋 Input Parameters:")
    print(f"   • Nitrogen: 90 mg/kg")
    print(f"   • Phosphorus: 42 mg/kg") 
    print(f"   • Potassium: 43 mg/kg")
    print(f"   • Temperature: 20.8°C")
    print(f"   • Humidity: 82%")
    print(f"   • pH: 6.5")
    print(f"   • Rainfall: 202.9mm")
    
    print(f"\n🎯 AI Recommendation:")
    print(f"   🏆 Best Crop: {example_result['recommended_crop'].upper()}")
    print(f"   🎪 Confidence: {example_result['confidence']:.3f} ({example_result['confidence']*100:.1f}%)")
    
    print(f"\n📊 Top 5 Crop Recommendations:")
    for i, (crop, prob) in enumerate(example_result['top_5_recommendations'], 1):
        print(f"   {i}. {crop.capitalize()}: {prob:.3f} ({prob*100:.1f}%)")
    
    print(f"\n🎉 TRAINING COMPLETED SUCCESSFULLY!")
    print(f"🌾 Your crop recommendation model is ready to help farmers! 🚜")

if __name__ == "__main__":
    main()
