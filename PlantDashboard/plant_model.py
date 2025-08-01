import numpy as np
import joblib
import pickle
from datetime import datetime, timedelta
import random

class PlantGrowthModel:
    def __init__(self):
        self.plant_characteristics = {
            'tomato': {
                'max_height': 150,
                'growth_rate_base': 2.5,
                'optimal_temp': (20, 25),
                'optimal_humidity': (60, 70),
                'optimal_ph': (6.0, 6.8),
                'phases': [
                    {'name': 'Germination', 'duration': 7, 'growth_factor': 0.1},
                    {'name': 'Seedling', 'duration': 14, 'growth_factor': 0.3},
                    {'name': 'Vegetative', 'duration': 30, 'growth_factor': 1.0},
                    {'name': 'Flowering', 'duration': 21, 'growth_factor': 0.7},
                    {'name': 'Fruiting', 'duration': 28, 'growth_factor': 0.4}
                ]
            },
            'basil': {
                'max_height': 60,
                'growth_rate_base': 1.8,
                'optimal_temp': (18, 24),
                'optimal_humidity': (50, 65),
                'optimal_ph': (6.0, 7.0),
                'phases': [
                    {'name': 'Germination', 'duration': 5, 'growth_factor': 0.1},
                    {'name': 'Seedling', 'duration': 10, 'growth_factor': 0.4},
                    {'name': 'Vegetative', 'duration': 25, 'growth_factor': 1.0},
                    {'name': 'Mature', 'duration': 30, 'growth_factor': 0.6}
                ]
            },
            'mint': {
                'max_height': 40,
                'growth_rate_base': 2.0,
                'optimal_temp': (15, 22),
                'optimal_humidity': (65, 75),
                'optimal_ph': (6.0, 7.0),
                'phases': [
                    {'name': 'Germination', 'duration': 7, 'growth_factor': 0.1},
                    {'name': 'Seedling', 'duration': 12, 'growth_factor': 0.3},
                    {'name': 'Vegetative', 'duration': 20, 'growth_factor': 1.0},
                    {'name': 'Mature', 'duration': 35, 'growth_factor': 0.5}
                ]
            },
            'lettuce': {
                'max_height': 25,
                'growth_rate_base': 1.2,
                'optimal_temp': (16, 20),
                'optimal_humidity': (70, 80),
                'optimal_ph': (6.0, 7.0),
                'phases': [
                    {'name': 'Germination', 'duration': 4, 'growth_factor': 0.1},
                    {'name': 'Seedling', 'duration': 8, 'growth_factor': 0.4},
                    {'name': 'Vegetative', 'duration': 20, 'growth_factor': 1.0},
                    {'name': 'Mature', 'duration': 18, 'growth_factor': 0.3}
                ]
            },
            'rosemary': {
                'max_height': 120,
                'growth_rate_base': 0.8,
                'optimal_temp': (18, 25),
                'optimal_humidity': (40, 55),
                'optimal_ph': (6.0, 7.5),
                'phases': [
                    {'name': 'Germination', 'duration': 14, 'growth_factor': 0.05},
                    {'name': 'Seedling', 'duration': 21, 'growth_factor': 0.2},
                    {'name': 'Vegetative', 'duration': 60, 'growth_factor': 1.0},
                    {'name': 'Mature', 'duration': 90, 'growth_factor': 0.4}
                ]
            },
            'strawberry': {
                'max_height': 30,
                'growth_rate_base': 1.5,
                'optimal_temp': (18, 24),
                'optimal_humidity': (60, 70),
                'optimal_ph': (5.5, 6.5),
                'phases': [
                    {'name': 'Germination', 'duration': 10, 'growth_factor': 0.1},
                    {'name': 'Seedling', 'duration': 15, 'growth_factor': 0.3},
                    {'name': 'Vegetative', 'duration': 25, 'growth_factor': 1.0},
                    {'name': 'Flowering', 'duration': 20, 'growth_factor': 0.6},
                    {'name': 'Fruiting', 'duration': 30, 'growth_factor': 0.4}
                ]
            }
        }
        
    def predict_growth(self, parameters):
        """Predict plant growth based on environmental parameters"""
        plant_type = parameters.get('plant_type', 'tomato')
        ambient_mode = parameters.get('ambient_mode', 'controlled')
        
        if plant_type not in self.plant_characteristics:
            plant_type = 'tomato'
            
        plant_info = self.plant_characteristics[plant_type]
        
        # Calculate environmental stress factors
        stress_factors = self._calculate_stress_factors(parameters, plant_info)
        
        # Apply ambient mode effects
        if ambient_mode == 'open':
            # Add random variations for open environment
            for factor in stress_factors:
                stress_factors[factor] *= (0.8 + random.random() * 0.4)
        elif ambient_mode == 'semi-controlled':
            # Moderate variations
            for factor in stress_factors:
                stress_factors[factor] *= (0.9 + random.random() * 0.2)
                
        # Calculate overall health score
        health_score = np.mean(list(stress_factors.values())) * 100
        
        # Generate growth stages
        growth_stages = self._simulate_growth_stages(plant_info, stress_factors)
        
        # Calculate final metrics
        final_height = growth_stages[-1] if growth_stages else 0
        growth_rate = final_height / len(growth_stages) if growth_stages else 0
        
        # Calculate optimal conditions percentage
        optimal_conditions = self._calculate_optimal_conditions(parameters, plant_info)
        
        # Estimate yield
        yield_estimate = self._estimate_yield(plant_type, health_score, final_height)
        
        # Generate phase information
        phases = self._generate_phase_info(plant_info)
        
        return {
            'growth_stages': growth_stages,
            'final_height': final_height,
            'growth_rate': growth_rate,
            'health_score': health_score,
            'optimal_conditions': optimal_conditions,
            'yield': yield_estimate,
            'phases': phases,
            'stress_factors': stress_factors
        }
        
    def _calculate_stress_factors(self, params, plant_info):
        """Calculate stress factors for each environmental parameter"""
        factors = {}
        
        # Temperature stress
        temp = params.get('temperature', 20)
        opt_temp = plant_info['optimal_temp']
        if opt_temp[0] <= temp <= opt_temp[1]:
            factors['temperature'] = 1.0
        else:
            deviation = min(abs(temp - opt_temp[0]), abs(temp - opt_temp[1]))
            factors['temperature'] = max(0.1, 1.0 - deviation / 20.0)
            
        # Humidity stress
        humidity = params.get('humidity', 60)
        opt_humidity = plant_info['optimal_humidity']
        if opt_humidity[0] <= humidity <= opt_humidity[1]:
            factors['humidity'] = 1.0
        else:
            deviation = min(abs(humidity - opt_humidity[0]), abs(humidity - opt_humidity[1]))
            factors['humidity'] = max(0.1, 1.0 - deviation / 40.0)
            
        # pH stress
        ph = params.get('soil_acidity', 6.5)
        opt_ph = plant_info['optimal_ph']
        if opt_ph[0] <= ph <= opt_ph[1]:
            factors['ph'] = 1.0
        else:
            deviation = min(abs(ph - opt_ph[0]), abs(ph - opt_ph[1]))
            factors['ph'] = max(0.1, 1.0 - deviation / 2.0)
            
        # Water stress
        water = params.get('water', 70) / 100.0
        factors['water'] = min(1.0, max(0.1, water))
        
        # Nutrient stress
        nutrients = params.get('nutrients', 70) / 100.0
        factors['nutrients'] = min(1.0, max(0.1, nutrients))
        
        # Light stress
        brightness = params.get('brightness', 30000)
        optimal_light = 40000  # Optimal light in lux
        light_factor = min(1.0, brightness / optimal_light)
        factors['light'] = max(0.1, light_factor)
        
        # CO2 stress
        co2 = params.get('co2', 400)
        optimal_co2 = 600  # Optimal CO2 in ppm
        co2_factor = min(1.0, co2 / optimal_co2)
        factors['co2'] = max(0.3, co2_factor)
        
        return factors
        
    def _simulate_growth_stages(self, plant_info, stress_factors):
        """Simulate daily growth stages"""
        base_rate = plant_info['growth_rate_base']
        max_height = plant_info['max_height']
        phases = plant_info['phases']
        
        overall_stress = np.mean(list(stress_factors.values()))
        adjusted_rate = base_rate * overall_stress
        
        growth_stages = []
        current_height = 0
        day = 0
        
        for phase in phases:
            phase_duration = phase['duration']
            growth_factor = phase['growth_factor']
            
            for _ in range(phase_duration):
                daily_growth = adjusted_rate * growth_factor
                # Add some randomness
                daily_growth *= (0.8 + random.random() * 0.4)
                
                current_height += daily_growth
                current_height = min(current_height, max_height)
                growth_stages.append(current_height)
                day += 1
                
        return growth_stages
        
    def _calculate_optimal_conditions(self, params, plant_info):
        """Calculate percentage of optimal conditions met"""
        optimal_count = 0
        total_conditions = 3  # temp, humidity, pH
        
        temp = params.get('temperature', 20)
        if plant_info['optimal_temp'][0] <= temp <= plant_info['optimal_temp'][1]:
            optimal_count += 1
            
        humidity = params.get('humidity', 60)
        if plant_info['optimal_humidity'][0] <= humidity <= plant_info['optimal_humidity'][1]:
            optimal_count += 1
            
        ph = params.get('soil_acidity', 6.5)
        if plant_info['optimal_ph'][0] <= ph <= plant_info['optimal_ph'][1]:
            optimal_count += 1
            
        return (optimal_count / total_conditions) * 100
        
    def _estimate_yield(self, plant_type, health_score, final_height):
        """Estimate plant yield based on health and growth"""
        yield_factors = {
            'tomato': {'base': 2.0, 'unit': 'kg'},
            'basil': {'base': 0.3, 'unit': 'kg'},
            'mint': {'base': 0.2, 'unit': 'kg'},
            'lettuce': {'base': 0.5, 'unit': 'kg'},
            'rosemary': {'base': 0.1, 'unit': 'kg'},
            'strawberry': {'base': 0.8, 'unit': 'kg'}
        }
        
        if plant_type in yield_factors:
            base_yield = yield_factors[plant_type]['base']
            unit = yield_factors[plant_type]['unit']
            
            # Adjust yield based on health and height
            health_factor = health_score / 100.0
            height_factor = min(1.0, final_height / 50.0)  # Normalize height
            
            estimated_yield = base_yield * health_factor * height_factor
            return f"{estimated_yield:.2f} {unit}"
        
        return "N/A"
        
    def _generate_phase_info(self, plant_info):
        """Generate phase information with start/end days"""
        phases = []
        current_day = 0
        
        for phase in plant_info['phases']:
            phases.append({
                'name': phase['name'],
                'start': current_day,
                'end': current_day + phase['duration'] - 1
            })
            current_day += phase['duration']
            
        return phases
        
    def save_model(self, filename):
        """Save the model to a file"""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self.plant_characteristics, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
            
    def load_model(self, filename):
        """Load the model from a file"""
        try:
            with open(filename, 'rb') as f:
                self.plant_characteristics = pickle.load(f)
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
