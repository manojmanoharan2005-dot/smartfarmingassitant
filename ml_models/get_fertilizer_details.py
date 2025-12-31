import pandas as pd
import os

class FertilizerDetails:
    def __init__(self, dataset_path=None):
        """Load fertilizer details from dataset"""
        if dataset_path is None:
            # Use absolute path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, 'datasets', 'fertilizer_recommendation_dataset.csv')
        self.df = pd.read_csv(dataset_path)
        self.fertilizer_info = self._build_fertilizer_database()
    
    def _build_fertilizer_database(self):
        """Build a database of fertilizer information"""
        fertilizer_db = {}
        
        for fertilizer in self.df['Fertilizer'].unique():
            fert_data = self.df[self.df['Fertilizer'] == fertilizer]
            
            # Get common remark for this fertilizer
            remarks = fert_data['Remark'].mode()
            remark = remarks[0] if len(remarks) > 0 else "General purpose fertilizer"
            
            # Calculate average nutrient requirements
            avg_nitrogen = fert_data['Nitrogen'].mean()
            avg_phos = fert_data['Phosphorous'].mean()
            avg_pot = fert_data['Potassium'].mean()
            
            # Determine effectiveness based on nutrient balance
            effectiveness = self._calculate_effectiveness(avg_nitrogen, avg_phos, avg_pot)
            
            fertilizer_db[fertilizer] = {
                'name': fertilizer,
                'remark': remark,
                'effectiveness': effectiveness,
                'avg_nitrogen': avg_nitrogen,
                'avg_phosphorous': avg_phos,
                'avg_potassium': avg_pot,
                'dosage': self._calculate_dosage(fertilizer),
                'use_case': self._determine_use_case(fert_data)
            }
        
        return fertilizer_db
    
    def _calculate_effectiveness(self, n, p, k):
        """Calculate effectiveness percentage"""
        total = n + p + k
        if total > 200:
            return "High"
        elif total > 120:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_dosage(self, fertilizer):
        """Calculate recommended dosage"""
        dosage_map = {
            'Urea': '20-30 kg/acre',
            'DAP': '15-25 kg/acre',
            'NPK': '40-60 kg/acre',
            'Balanced NPK Fertilizer': '40-60 kg/acre',
            'MOP': '15-30 kg/acre',
            'Muriate of Potash': '15-30 kg/acre',
            'Compost': '2-3 ton/acre',
            'Organic Fertilizer': '1-2 ton/acre',
            'Lime': '0.5-1 ton/acre',
            'Gypsum': '0.3-0.5 ton/acre',
            'Water Retaining Fertilizer': '10-20 kg/acre'
        }
        return dosage_map.get(fertilizer, '20-40 kg/acre')
    
    def _determine_use_case(self, fert_data):
        """Determine best use case"""
        avg_temp = fert_data['Temperature'].mean()
        avg_ph = fert_data['PH'].mean()
        
        if avg_ph < 5.5:
            return "Best for acidic soils"
        elif avg_ph > 7.5:
            return "Best for alkaline soils"
        elif avg_temp > 30:
            return "Suitable for warm climate"
        else:
            return "General purpose application"
    
    def get_details(self, fertilizer_name):
        """Get details for a specific fertilizer"""
        return self.fertilizer_info.get(fertilizer_name, {
            'name': fertilizer_name,
            'remark': 'General purpose fertilizer',
            'effectiveness': 'Medium',
            'dosage': '20-40 kg/acre',
            'use_case': 'General use'
        })

# Global instance
_fertilizer_details = None

def get_fertilizer_details():
    """Get or create FertilizerDetails instance"""
    global _fertilizer_details
    if _fertilizer_details is None:
        _fertilizer_details = FertilizerDetails()
    return _fertilizer_details
