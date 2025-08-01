import pandas as pd
import json
import csv
import os
from datetime import datetime

class DataHandler:
    def __init__(self):
        self.data_directory = "plant_data"
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)
            
    def save_prediction_data(self, parameters, prediction, filename=None):
        """Save prediction data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prediction_{timestamp}.csv"
            
        filepath = os.path.join(self.data_directory, filename)
        
        # Combine parameters and prediction results
        data = {**parameters}
        data.update({
            'final_height': prediction['final_height'],
            'growth_rate': prediction['growth_rate'],
            'health_score': prediction['health_score'],
            'optimal_conditions': prediction['optimal_conditions'],
            'yield': prediction['yield'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Convert to DataFrame
        df = pd.DataFrame([data])
        
        try:
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            print(f"Error saving data: {e}")
            return None
            
    def load_historical_data(self):
        """Load all historical prediction data"""
        data_files = [f for f in os.listdir(self.data_directory) if f.endswith('.csv')]
        
        if not data_files:
            return pd.DataFrame()
            
        all_data = []
        for file in data_files:
            filepath = os.path.join(self.data_directory, file)
            try:
                df = pd.read_csv(filepath)
                all_data.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")
                
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
            
    def export_to_json(self, data, filename):
        """Export data to JSON format"""
        filepath = os.path.join(self.data_directory, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return filepath
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return None
            
    def import_from_json(self, filename):
        """Import data from JSON format"""
        filepath = os.path.join(self.data_directory, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return None
            
    def get_plant_statistics(self, plant_type=None):
        """Get statistics for plant predictions"""
        df = self.load_historical_data()
        
        if df.empty:
            return {}
            
        if plant_type:
            df = df[df['plant_type'] == plant_type]
            
        if df.empty:
            return {}
            
        stats = {
            'total_predictions': len(df),
            'avg_final_height': df['final_height'].mean(),
            'avg_health_score': df['health_score'].mean(),
            'avg_growth_rate': df['growth_rate'].mean(),
            'best_conditions': df['optimal_conditions'].max(),
            'worst_conditions': df['optimal_conditions'].min()
        }
        
        return stats
        
    def create_comparison_report(self, plant_types):
        """Create a comparison report for different plant types"""
        df = self.load_historical_data()
        
        if df.empty:
            return {}
            
        report = {}
        for plant_type in plant_types:
            plant_data = df[df['plant_type'] == plant_type]
            if not plant_data.empty:
                report[plant_type] = {
                    'count': len(plant_data),
                    'avg_height': plant_data['final_height'].mean(),
                    'avg_health': plant_data['health_score'].mean(),
                    'success_rate': len(plant_data[plant_data['health_score'] > 70]) / len(plant_data) * 100
                }
                
        return report
