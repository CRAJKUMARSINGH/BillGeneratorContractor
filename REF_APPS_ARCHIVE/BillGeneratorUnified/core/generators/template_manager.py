"""
Template Manager - Manage Jinja2 templates and caching
"""
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from functools import lru_cache
import os

class TemplateManager:
    """Manages Jinja2 templates and caching for document generation"""
    
    def __init__(self, template_dir: Optional[str] = None):
        # Set up Jinja2 environment for templates
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self._template_cache = {}
    
    @lru_cache(maxsize=128)
    def get_template_cached(self, template_name: str):
        """Cache loaded templates with LRU cache"""
        return self.jinja_env.get_template(template_name)
    
    def get_template(self, template_name: str):
        """Get template with instance-based caching"""
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.jinja_env.get_template(template_name)
        return self._template_cache[template_name]
    
    def render_template(self, template_name: str, template_data: Dict[str, Any]) -> str:
        """Render a template with provided data"""
        try:
            # Use cached template
            template = self.get_template(template_name)
            # Pass both the template data and the original data to the template
            render_data = {'data': template_data}
            render_data.update(template_data)
            return template.render(**render_data)
        except Exception as e:
            print(f"Failed to render template {template_name}: {e}")
            raise
    
    def clear_cache(self):
        """Clear the template cache"""
        self._template_cache.clear()
        # Note: LRU cache clearing would require accessing the method directly
        # self.get_template_cached.cache_clear()
    
    def preload_templates(self, template_names: list):
        """Preload templates into cache"""
        for template_name in template_names:
            try:
                self.get_template(template_name)
            except Exception as e:
                print(f"Failed to preload template {template_name}: {e}")