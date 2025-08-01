from PIL import Image, ImageDraw, ImageFont
import random
import math
import os

class ImageGenerator:
    def __init__(self):
        self.image_size = (400, 300)
        self.plant_colors = {
            'tomato': {'stem': '#228B22', 'leaf': '#32CD32', 'fruit': '#FF6347'},
            'basil': {'stem': '#228B22', 'leaf': '#90EE90', 'fruit': '#FFFFFF'},
            'mint': {'stem': '#228B22', 'leaf': '#98FB98', 'fruit': '#FFFFFF'},
            'lettuce': {'stem': '#228B22', 'leaf': '#ADFF2F', 'fruit': '#FFFFFF'},
            'rosemary': {'stem': '#8B4513', 'leaf': '#556B2F', 'fruit': '#FFFFFF'},
            'strawberry': {'stem': '#228B22', 'leaf': '#32CD32', 'fruit': '#FF1493'}
        }
        
    def generate_evolution(self, plant_type, parameters, prediction, baseline_path=None):
        """Generate a series of images showing plant evolution"""
        growth_stages = prediction['growth_stages']
        health_score = prediction['health_score']
        
        images = []
        
        # Generate images for key growth stages
        stage_indices = [0, len(growth_stages)//4, len(growth_stages)//2, 
                        3*len(growth_stages)//4, len(growth_stages)-1]
        
        for i, stage_idx in enumerate(stage_indices):
            if stage_idx < len(growth_stages):
                height = growth_stages[stage_idx]
                image = self.generate_plant_image(plant_type, height, health_score, i+1)
                images.append(image)
                
        return images
        
    def generate_plant_image(self, plant_type, height, health_score, stage):
        """Generate a single plant image"""
        img = Image.new('RGB', self.image_size, color='#87CEEB')  # Sky blue background
        draw = ImageDraw.Draw(img)
        
        # Draw ground
        ground_y = self.image_size[1] - 50
        draw.rectangle([0, ground_y, self.image_size[0], self.image_size[1]], 
                      fill='#8B4513')  # Brown ground
        
        # Get plant colors (default to tomato since we removed plant type selection)
        colors = self.plant_colors.get(plant_type, self.plant_colors['tomato'])
        
        # Calculate plant dimensions based on height and health
        if stage == 0:  # Initial/seed stage
            plant_height = 5  # Very small initial plant
            plant_width = 3
        else:
            plant_height = min(height * 2, self.image_size[1] - 100)  # Scale for display
            plant_width = plant_height * 0.6
        
        # Adjust colors based on health
        health_factor = health_score / 100.0
        stem_color = self._adjust_color_health(colors['stem'], health_factor)
        leaf_color = self._adjust_color_health(colors['leaf'], health_factor)
        
        # Plant center position
        center_x = self.image_size[0] // 2
        base_y = ground_y
        
        if stage == 0:
            # Draw seed/initial state
            self._draw_seed(draw, center_x, base_y - 10, health_factor)
        else:
            # Draw stem
            stem_width = max(2, int(plant_height * 0.05))
            stem_top_y = base_y - plant_height
            draw.rectangle([center_x - stem_width//2, int(stem_top_y), 
                           center_x + stem_width//2, base_y], fill=stem_color)
            
            # Draw leaves based on plant type and stage
            self._draw_leaves(draw, plant_type, center_x, stem_top_y, base_y, 
                             plant_width, leaf_color, stage)
            
            # Draw fruits/flowers if applicable
            if stage >= 3 and plant_type in ['tomato', 'strawberry']:
                self._draw_fruits(draw, plant_type, center_x, stem_top_y, base_y, 
                                colors['fruit'], stage)
        
        # Add stage label
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        if stage == 0:
            stage_text = f"Initial State - Seed"
        else:
            stage_text = f"Stage {stage} - Height: {height:.1f}cm"
            
        if font:
            draw.text((10, 10), stage_text, fill='black', font=font)
        else:
            draw.text((10, 10), stage_text, fill='black')
            
        # Add health indicator
        health_text = f"Health: {health_score:.1f}%"
        health_color = 'green' if health_score > 70 else 'orange' if health_score > 40 else 'red'
        if font:
            draw.text((10, 30), health_text, fill=health_color, font=font)
        else:
            draw.text((10, 30), health_text, fill=health_color)
            
        return img
        
    def _draw_seed(self, draw, x, y, health_factor):
        """Draw a seed for the initial state"""
        seed_size = 8
        seed_color = '#8B4513'  # Brown seed
        
        # Adjust seed color based on health
        if health_factor > 0.7:
            seed_color = '#654321'  # Healthy brown
        elif health_factor > 0.4:
            seed_color = '#8B4513'  # Normal brown
        else:
            seed_color = '#A0522D'  # Pale brown
            
        # Draw seed
        draw.ellipse([x - seed_size, y - seed_size//2, 
                     x + seed_size, y + seed_size//2], fill=seed_color)
        
        # Draw small sprout if health is good
        if health_factor > 0.5:
            sprout_color = '#90EE90'
            draw.line([x, y - seed_size//2, x, y - seed_size//2 - 5], 
                     fill=sprout_color, width=2)
        
    def _draw_leaves(self, draw, plant_type, center_x, top_y, base_y, width, color, stage):
        """Draw leaves based on plant type"""
        plant_height = base_y - top_y
        num_leaves = min(stage * 2, 8)  # More leaves as plant grows
        
        for i in range(num_leaves):
            # Calculate leaf position
            y_pos = base_y - (i + 1) * (plant_height / (num_leaves + 1))
            side = 1 if i % 2 == 0 else -1  # Alternate sides
            
            leaf_x = center_x + side * (width * 0.3)
            leaf_size = width * 0.2 * (1 + stage * 0.1)
            
            if plant_type == 'lettuce':
                # Draw broad leaves for lettuce
                self._draw_broad_leaf(draw, leaf_x, y_pos, leaf_size, color)
            elif plant_type == 'rosemary':
                # Draw needle-like leaves for rosemary
                self._draw_needle_leaf(draw, leaf_x, y_pos, leaf_size, color)
            else:
                # Draw regular oval leaves (default for tomato)
                self._draw_oval_leaf(draw, leaf_x, y_pos, leaf_size, color)
                
    def _draw_oval_leaf(self, draw, x, y, size, color):
        """Draw an oval leaf"""
        draw.ellipse([x - size//2, y - size//3, x + size//2, y + size//3], fill=color)
        
    def _draw_broad_leaf(self, draw, x, y, size, color):
        """Draw a broad leaf for lettuce"""
        points = [
            (x, y - size//2),
            (x + size//2, y),
            (x, y + size//2),
            (x - size//2, y)
        ]
        draw.polygon(points, fill=color)
        
    def _draw_needle_leaf(self, draw, x, y, size, color):
        """Draw needle-like leaves for rosemary"""
        for i in range(3):
            offset = (i - 1) * 3
            draw.line([x + offset, y - size//4, x + offset, y + size//4], 
                     fill=color, width=2)
                     
    def _draw_fruits(self, draw, plant_type, center_x, top_y, base_y, color, stage):
        """Draw fruits based on plant type"""
        if plant_type == 'tomato':
            # Draw tomatoes
            num_fruits = min(stage - 2, 4)
            for i in range(num_fruits):
                fruit_x = center_x + random.randint(-20, 20)
                fruit_y = int(top_y + random.randint(10, (base_y - top_y) // 2))
                fruit_size = 8 + stage * 2
                draw.ellipse([fruit_x - fruit_size, fruit_y - fruit_size,
                            fruit_x + fruit_size, fruit_y + fruit_size], fill=color)
                            
        elif plant_type == 'strawberry':
            # Draw strawberries
            num_fruits = min(stage - 2, 3)
            for i in range(num_fruits):
                fruit_x = center_x + random.randint(-15, 15)
                fruit_y = base_y - random.randint(20, 40)
                self._draw_strawberry(draw, fruit_x, fruit_y, color)
                
    def _draw_strawberry(self, draw, x, y, color):
        """Draw a strawberry shape"""
        # Draw strawberry body
        points = [(x, y - 8), (x + 6, y), (x, y + 8), (x - 6, y)]
        draw.polygon(points, fill=color)
        
        # Draw strawberry top (green)
        draw.polygon([(x - 3, y - 8), (x, y - 12), (x + 3, y - 8)], fill='green')
        
    def _adjust_color_health(self, color_hex, health_factor):
        """Adjust color based on plant health"""
        # Convert hex to RGB
        color_hex = color_hex.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        
        # Adjust brightness based on health
        factor = 0.5 + health_factor * 0.5  # Range from 0.5 to 1.0
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        # Ensure values are within valid range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def save_evolution_sequence(self, images, filename):
        """Save evolution images as separate files"""
        if images:
            try:
                base_name = filename.rsplit('.', 1)[0]
                for i, image in enumerate(images):
                    stage_filename = f"{base_name}_stage_{i+1}.png"
                    image.save(stage_filename)
                return True
            except Exception as e:
                print(f"Error saving images: {e}")
                return False
        return False
