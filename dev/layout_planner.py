#!/usr/bin/env python3
"""
Layout Planner - Comic page layout generator
Transforms script into visual page plans for comic artists
"""

from __future__ import annotations
import math
import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ReadingDirection(Enum):
    WESTERN = "left_to_right"
    MANGA = "right_to_left"

class AspectRatio(Enum):
    WIDESCREEN = (16, 9)
    CINEMATIC = (47, 20)  # 2.35:1
    STANDARD = (4, 3)
    SQUARE = (1, 1)
    PORTRAIT = (2, 3)
    VERTICAL = (3, 4)
    EXTREME_VERTICAL = (1, 2)

    @property
    def ratio(self) -> float:
        return self.value[0] / self.value[1]

@dataclass(frozen=True)
class Panel:
    id: int
    x: float  # 0-1 relative position
    y: float  # 0-1 relative position  
    width: float  # 0-1 relative size
    height: float  # 0-1 relative size
    aspect_ratio: AspectRatio
    content: str
    is_bleed: bool = False
    is_climax: bool = False

    @property
    def area(self) -> float:
        return self.width * self.height

@dataclass
class PageLayout:
    panels: List[Panel]
    reading_direction: ReadingDirection
    mood: str
    target_format: str
    total_panels: int
    
    @property
    def dominant_flow(self) -> str:
        return self._calculate_flow_pattern()
    
    @property  
    def composition_type(self) -> str:
        return self._analyze_composition()

class LayoutEngine:
    """Core layout generation engine"""
    
    # Layout templates for different panel counts
    LAYOUT_TEMPLATES = {
        4: [
            [(0.0, 0.0, 0.5, 0.5), (0.5, 0.0, 0.5, 0.5),
             (0.0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)]
        ],
        5: [
            [(0.0, 0.0, 0.6, 0.4), (0.6, 0.0, 0.4, 0.4),
             (0.0, 0.4, 1.0, 0.3), 
             (0.0, 0.7, 0.5, 0.3), (0.5, 0.7, 0.5, 0.3)]
        ],
        6: [
            [(0.0, 0.0, 0.6, 0.3), (0.6, 0.0, 0.4, 0.3),
             (0.0, 0.3, 0.45, 0.25), (0.45, 0.3, 0.55, 0.25),
             (0.0, 0.55, 0.3, 0.45), (0.3, 0.55, 0.7, 0.45)]
        ]
    }
    
    # Mood to layout style mapping
    MOOD_STYLES = {
        "эпичный боевик": "dynamic",
        "лирическая драма": "balanced", 
        "напряженный триллер": "tight",
        "комедийный скетч": "varied"
    }
    
    # Content to aspect ratio mapping
    CONTENT_RATIOS = {
        "установочный": AspectRatio.WIDESCREEN,
        "пейзаж": AspectRatio.WIDESCREEN,
        "город": AspectRatio.WIDESCREEN,
        "бежит": AspectRatio.CINEMATIC,
        "движение": AspectRatio.CINEMATIC, 
        "погоня": AspectRatio.CINEMATIC,
        "крупный план": AspectRatio.PORTRAIT,
        "лицо": AspectRatio.PORTRAIT,
        "эмоция": AspectRatio.PORTRAIT,
        "высота": AspectRatio.EXTREME_VERTICAL,
        "падение": AspectRatio.EXTREME_VERTICAL
    }
    
    def __init__(self, page_width: int = 1200, page_height: int = 1800):
        self.page_width = page_width
        self.page_height = page_height
        
    def generate_layout(
        self,
        scenes: List[str],
        key_elements: List[str],
        mood: str,
        target_format: str,
        reading_direction: ReadingDirection = ReadingDirection.WESTERN
    ) -> PageLayout:
        """
        Generate page layout from script data
        """
        # Validate input
        if not scenes:
            raise ValueError("At least one scene required")
        
        # Determine optimal panel count
        panel_count = self._calculate_panel_count(scenes, mood, target_format)
        
        # Identify climax scene
        climax_index = self._find_climax(scenes, key_elements)
        
        # Select layout template
        layout_template = self._select_layout_template(panel_count, mood)
        
        # Adjust for climax
        adjusted_template = self._adjust_for_climax(layout_template, climax_index)
        
        # Create panels
        panels = self._create_panels(adjusted_template, scenes, climax_index)
        
        return PageLayout(
            panels=panels,
            reading_direction=reading_direction,
            mood=mood,
            target_format=target_format,
            total_panels=panel_count
        )
    
    def _calculate_panel_count(
        self, 
        scenes: List[str], 
        mood: str, 
        target_format: str
    ) -> int:
        """
        Calculate optimal number of panels based on content and constraints
        """
        base_count = len(scenes)
        
        # Mood-based adjustments
        mood_factors = {
            "эпичный боевик": 0.8,
            "лирическая драма": 1.2, 
            "напряженный триллер": 1.0,
            "комедийный скетч": 1.4
        }
        
        # Format-based constraints  
        format_limits = {
            "веб-комикс": 9,
            "печатная манга": 7,
            "европейский альбом": 6,
            "сториз для соцсетей": 4
        }
        
        mood_factor = mood_factors.get(mood, 1.0)
        format_limit = format_limits.get(target_format, 8)
        
        calculated = int(base_count * mood_factor)
        return max(3, min(format_limit, calculated))
    
    def _find_climax(self, scenes: List[str], key_elements: List[str]) -> int:
        """
        Identify the most important scene for emphasis
        """
        climax_indicators = {
            "взрыв": 10,
            "кульминация": 9,
            "решающий": 8, 
            "ключевой": 7,
            "шокирующий": 8,
            "неожиданный": 7,
            "битва": 6
        }
        
        scores = []
        for i, scene in enumerate(scenes):
            score = 0
            scene_lower = scene.lower()
            
            # Score based on keywords
            for keyword, weight in climax_indicators.items():
                if keyword in scene_lower:
                    score += weight
            
            # Bonus for key elements
            for element in key_elements:
                if element.lower() in scene_lower:
                    score += 3
            
            scores.append(score)
        
        return scores.index(max(scores)) if scores else len(scenes) // 2
    
    def _select_layout_template(
        self, 
        panel_count: int, 
        mood: str
    ) -> List[Tuple[float, float, float, float]]:
        """
        Select appropriate layout template
        """
        # Get base template
        if panel_count in self.LAYOUT_TEMPLATES:
            templates = self.LAYOUT_TEMPLATES[panel_count]
        else:
            # Fallback: generate grid
            templates = [self._generate_grid_layout(panel_count)]
        
        # Select based on mood
        style = self.MOOD_STYLES.get(mood, "balanced")
        
        if style == "dynamic" and len(templates) > 1:
            return templates[1]  # More dynamic variant
        else:
            return templates[0]  # Default variant
    
    def _generate_grid_layout(self, panel_count: int) -> List[Tuple[float, float, float, float]]:
        """
        Generate fallback grid layout
        """
        cols = math.ceil(math.sqrt(panel_count))
        rows = math.ceil(panel_count / cols)
        
        cell_width = 1.0 / cols
        cell_height = 1.0 / rows
        
        layout = []
        for i in range(panel_count):
            row = i // cols
            col = i % cols
            layout.append((
                col * cell_width,
                row * cell_height, 
                cell_width,
                cell_height
            ))
        
        return layout
    
    def _adjust_for_climax(
        self, 
        template: List[Tuple[float, float, float, float]], 
        climax_index: int
    ) -> List[Tuple[float, float, float, float]]:
        """
        Adjust layout to emphasize climax panel
        """
        if climax_index >= len(template):
            return template
        
        adjusted = template.copy()
        climax_panel = list(adjusted[climax_index])
        
        # Make climax panel larger
        climax_panel[2] *= 1.3  # width
        climax_panel[3] *= 1.3  # height
        
        # Normalize to keep within page bounds
        adjusted[climax_index] = tuple(climax_panel)
        return self._normalize_layout(adjusted)
    
    def _normalize_layout(
        self, 
        layout: List[Tuple[float, float, float, float]]
    ) -> List[Tuple[float, float, float, float]]:
        """
        Ensure all panels fit within page boundaries
        """
        normalized = []
        for x, y, w, h in layout:
            # Clamp values to [0,1] range
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))
            w = max(0.1, min(1.0, w))
            h = max(0.1, min(1.0, h))
            
            # Ensure panels don't extend beyond page
            if x + w > 1.0:
                w = 1.0 - x
            if y + h > 1.0:
                h = 1.0 - y
                
            normalized.append((x, y, w, h))
        
        return normalized
    
    def _create_panels(
        self,
        template: List[Tuple[float, float, float, float]],
        scenes: List[str],
        climax_index: int
    ) -> List[Panel]:
        """
        Create Panel objects from layout template
        """
        panels = []
        
        for i, (x, y, w, h) in enumerate(template):
            if i >= len(scenes):
                break
                
            content = scenes[i]
            aspect_ratio = self._determine_aspect_ratio(content)
            is_climax = (i == climax_index)
            is_bleed = is_climax and random.random() > 0.7  # 30% chance for climax
            
            panel = Panel(
                id=i + 1,
                x=x,
                y=y, 
                width=w,
                height=h,
                aspect_ratio=aspect_ratio,
                content=content,
                is_bleed=is_bleed,
                is_climax=is_climax
            )
            panels.append(panel)
        
        return panels
    
    def _determine_aspect_ratio(self, content: str) -> AspectRatio:
        """
        Determine best aspect ratio for scene content
        """
        content_lower = content.lower()
        
        for keyword, ratio in self.CONTENT_RATIOS.items():
            if keyword in content_lower:
                return ratio
        
        # Default based on content characteristics
        if any(word in content_lower for word in ["эмоция", "лицо", "реакция"]):
            return AspectRatio.PORTRAIT
        elif any(word in content_lower for word in ["действие", "движение"]):
            return AspectRatio.CINEMATIC
        else:
            return AspectRatio.STANDARD

class LayoutFormatter:
    """Format layout data for output"""
    
    @staticmethod
    def format_layout(layout: PageLayout) -> str:
        """Generate formatted layout description"""
        
        lines = []
        lines.append(f"МАКЕТ СТРАНИЦЫ: {layout.mood.upper()}")
        lines.append("=" * 50)
        lines.append(f"Панелей: {layout.total_panels} | Настроение: {layout.mood}")
        lines.append(f"Формат: {layout.target_format} | Поток: {layout.dominant_flow}")
        lines.append(f"Композиция: {layout.composition_type}")
        lines.append("")
        
        # Sort panels by reading order
        sorted_panels = LayoutFormatter._sort_panels_by_reading_order(
            layout.panels, layout.reading_direction
        )
        
        for panel in sorted_panels:
            bleed = " [BLEED]" if panel.is_bleed else ""
            climax = " [CLIMAX]" if panel.is_climax else ""
            
            lines.append(f"ПАНЕЛЬ {panel.id}:")
            lines.append(f"  Позиция: ({panel.x:.1f}, {panel.y:.1f})")
            lines.append(f"  Размер: {panel.width:.1f} x {panel.height:.1f}")
            lines.append(f"  Соотношение: {panel.aspect_ratio.name} ({panel.aspect_ratio.value[0]}:{panel.aspect_ratio.value[1]})")
            lines.append(f"  Содержание: {panel.content}{bleed}{climax}")
            lines.append(f"  Площадь: {panel.area:.2f}")
            lines.append("")
        
        lines.append("АНАЛИЗ КОМПОЗИЦИИ:")
        lines.append(f"- {layout.composition_type}")
        lines.append(f"- Доминирующий поток: {layout.dominant_flow}")
        lines.append(f"- Акцент на панели {sorted_panels[0].id if sorted_panels else 'N/A'}")
        lines.append("- Готов для художника")
        
        return "\n".join(lines)
    
    @staticmethod
    def _sort_panels_by_reading_order(
        panels: List[Panel], 
        direction: ReadingDirection
    ) -> List[Panel]:
        """Sort panels in reading order"""
        if direction == ReadingDirection.MANGA:
            # Right to left, top to bottom
            return sorted(panels, key=lambda p: (-p.y, -p.x))
        else:
            # Left to right, top to bottom (Western)
            return sorted(panels, key=lambda p: (p.y, p.x))

# Extension for PageLayout
def _calculate_flow_pattern(self) -> str:
    """Calculate dominant visual flow pattern"""
    if self.reading_direction == ReadingDirection.MANGA:
        return "vertical_right_left"
    
    # Analyze panel positions for Western layouts
    if len(self.panels) <= 4:
        return "z_pattern"
    elif self.mood in ["эпичный боевик", "напряженный триллер"]:
        return "diagonal_dynamic"
    else:
        return "modified_z"

def _analyze_composition(self) -> str:
    """Analyze overall composition type"""
    areas = [p.area for p in self.panels]
    avg_area = sum(areas) / len(areas)
    max_area = max(areas)
    
    if max_area / avg_area > 2.0:
        return "pyramidal_focus"
    elif len(self.panels) <= 5:
        return "balanced_grid"
    else:
        return "rhythmic_mosaic"

# Add methods to PageLayout class
PageLayout._calculate_flow_pattern = _calculate_flow_pattern
PageLayout._analyze_composition = _analyze_composition

# Usage example
def main():
    """Example usage"""
    scenes = [
        "Ночной город, установочный план",
        "Протагонист бежит по крыше",
        "Крупный план: испуганное лицо",
        "Взрыв за спиной", 
        "Падение обломков",
        "Уворот от падающей балки"
    ]
    
    key_elements = [
        "персонаж смотрит на часы",
        "эмоция: паника", 
        "динамика взрыва"
    ]
    
    engine = LayoutEngine()
    layout = engine.generate_layout(
        scenes=scenes,
        key_elements=key_elements,
        mood="эпичный боевик",
        target_format="веб-комикс",
        reading_direction=ReadingDirection.WESTERN
    )
    
    formatter = LayoutFormatter()
    print(formatter.format_layout(layout))

if __name__ == "__main__":
    main()
