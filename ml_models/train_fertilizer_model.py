import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os

def load_and_preprocess_data(filepath):
    """Load and preprocess the fertilizer dataset"""
    print("Loading dataset...")
    df = pd.read_csv(filepath)
    
    print(f"Dataset shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Check for missing values
    print(f"\nMissing values:\n{df.isnull().sum()}")
    
    # Handle missing values if any
    df = df.dropna()
    
    return df

def encode_features(df):
    """Encode categorical features"""
    print("\nEncoding categorical features...")
    
    # Separate features and target
    X = df.drop(['Fertilizer', 'Remark'], axis=1)
    y = df['Fertilizer']
    
    # Encode categorical features
    label_encoders = {}
    categorical_columns = ['Soil', 'Crop']
    
    for col in categorical_columns:
        if col in X.columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le
            print(f"  {col}: {len(le.classes_)} unique values")
    
    # Encode target variable
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y)
    
    print(f"\nTarget variable: {len(target_encoder.classes_)} fertilizer types")
    print(f"Fertilizer types: {target_encoder.classes_}")
    
    return X, y_encoded, label_encoders, target_encoder

def train_model(X_train, y_train):
    """Train Random Forest Classifier"""
    print("\nTraining Random Forest model...")
    
    # Initialize model with optimized parameters for better variety
    model = RandomForestClassifier(
        n_estimators=200,  # Increased from 100
        max_depth=25,      # Increased from 20
        min_samples_split=3,  # Decreased from 5
        min_samples_leaf=1,   # Decreased from 2
        max_features='sqrt',  # Added for better feature selection
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle class imbalance
    )
    
    # Train the model
    model.fit(X_train, y_train)
    
    print("Training completed!")
    return model

def evaluate_model(model, X_test, y_test, target_encoder):
    """Evaluate model performance"""
    print("\n" + "="*60)
    print("MODEL EVALUATION")
    print("="*60)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=target_encoder.classes_,
                                zero_division=0))
    
    # Confusion matrix
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Feature importance
    feature_names = ['Temperature', 'Moisture', 'Rainfall', 'PH', 
                     'Nitrogen', 'Phosphorous', 'Potassium', 'Carbon', 
                     'Soil', 'Crop']
    feature_importance = pd.DataFrame({
        'Feature': feature_names,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("\nTop 5 Feature Importances:")
    print(feature_importance.head())
    
    return accuracy, y_pred

def test_sample_predictions(model, X_test, y_test, target_encoder, n_samples=5):
    """Test model with sample predictions"""
    print("\n" + "="*60)
    print("SAMPLE PREDICTIONS")
    print("="*60)
    
    # Get random samples
    indices = np.random.choice(len(X_test), n_samples, replace=False)
    
    correct = 0
    for i, idx in enumerate(indices, 1):
        X_sample = X_test.iloc[idx:idx+1]
        # Fix: y_test is a numpy array, use direct indexing
        y_true = target_encoder.inverse_transform([y_test[idx]])[0]
        y_pred = target_encoder.inverse_transform(model.predict(X_sample))[0]
        
        if y_true == y_pred:
            correct += 1
        
        print(f"\nSample {i}:")
        print(f"  Input: {X_sample.values[0]}")
        print(f"  True Fertilizer: {y_true}")
        print(f"  Predicted Fertilizer: {y_pred}")
        print(f"  Match: {'✓' if y_true == y_pred else '✗'}")
    
    print(f"\nSample Accuracy: {correct}/{n_samples} ({correct/n_samples*100:.1f}%)")

def save_model(model, label_encoders, target_encoder, scaler, output_dir):
    """Save trained model and encoders"""
    print(f"\nSaving model to {output_dir}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model
    joblib.dump(model, os.path.join(output_dir, 'fertilizer_model.pkl'))
    
    # Save encoders
    joblib.dump(label_encoders, os.path.join(output_dir, 'label_encoders.pkl'))
    joblib.dump(target_encoder, os.path.join(output_dir, 'target_encoder.pkl'))
    joblib.dump(scaler, os.path.join(output_dir, 'scaler.pkl'))
    
    print("Model and encoders saved successfully!")

def main():
    # Configuration
    # Use absolute paths relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, 'datasets', 'fertilizer_recommendation_dataset.csv')
    model_output_dir = os.path.join(base_dir, 'models')
    
    print("="*60)
    print("FERTILIZER RECOMMENDATION MODEL TRAINING")
    print("="*60)
    
    # Load and preprocess data
    df = load_and_preprocess_data(dataset_path)
    
    # Check class distribution
    print("\nClass Distribution:")
    print(df['Fertilizer'].value_counts())
    print(f"\nTotal unique fertilizers: {df['Fertilizer'].nunique()}")
    
    # Encode features
    X, y, label_encoders, target_encoder = encode_features(df)
    
    # Scale numerical features
    print("\nScaling numerical features...")
    scaler = StandardScaler()
    numerical_cols = ['Temperature', 'Moisture', 'Rainfall', 'PH', 
                      'Nitrogen', 'Phosphorous', 'Potassium', 'Carbon']
    X[numerical_cols] = scaler.fit_transform(X[numerical_cols])
    
    # Split data
    print("\nSplitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set size: {len(X_train)}")
    print(f"Testing set size: {len(X_test)}")
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Evaluate model
    accuracy, y_pred = evaluate_model(model, X_test, y_test, target_encoder)
    
    # Test sample predictions
    test_sample_predictions(model, X_test, y_test, target_encoder)
    
    # Verify model variety
    print("\n" + "="*60)
    print("VERIFYING MODEL VARIETY")
    print("="*60)
    unique_predictions = len(set(target_encoder.inverse_transform(y_pred)))
    print(f"Unique predictions in test set: {unique_predictions}/{len(target_encoder.classes_)}")
    
    if unique_predictions < len(target_encoder.classes_) * 0.3:
        print("⚠️  WARNING: Model may not be diverse enough!")
    else:
        print("✓ Model shows good prediction diversity")
    
    # Save model
    save_model(model, label_encoders, target_encoder, scaler, model_output_dir)
    
    print("\n" + "="*60)
    print(f"TRAINING COMPLETED! Final Accuracy: {accuracy*100:.2f}%")
    print("="*60)

if __name__ == "__main__":
    main()
