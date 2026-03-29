"""
Test suite for optimization features of the Stream Bill Generator
"""
import sys
import os
import unittest
import tempfile
import json

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestOptimizations(unittest.TestCase):
    
    def test_redis_cache_import(self):
        """Test that the Redis cache module can be imported"""
        try:
            from data.redis_cache import RedisCache, HybridCache
            self.assertIsNotNone(RedisCache)
            self.assertIsNotNone(HybridCache)
        except ImportError as e:
            # This is expected if Redis is not installed
            print(f"Redis cache module import test skipped: {e}")
    
    def test_advanced_formats_import(self):
        """Test that the advanced formats module can be imported"""
        try:
            from exports.advanced_formats import generate_json, generate_xml, export_to_csv
            self.assertIsNotNone(generate_json)
            self.assertIsNotNone(generate_xml)
            self.assertIsNotNone(export_to_csv)
        except ImportError as e:
            self.fail(f"Failed to import advanced formats module: {e}")
    
    def test_batch_processor_import(self):
        """Test that the batch processor module can be imported"""
        try:
            from scripts.batch_processor import process_single_file, process_batch
            self.assertIsNotNone(process_single_file)
            self.assertIsNotNone(process_batch)
        except ImportError as e:
            self.fail(f"Failed to import batch processor module: {e}")
    
    def test_frontend_optimizer_import(self):
        """Test that the frontend optimizer module can be imported"""
        try:
            from scripts.frontend_optimizer import minify_css, minify_js
            self.assertIsNotNone(minify_css)
            self.assertIsNotNone(minify_js)
        except ImportError as e:
            self.fail(f"Failed to import frontend optimizer module: {e}")
    
    def test_json_generation(self):
        """Test JSON generation functionality"""
        from exports.advanced_formats import generate_json
        
        # Test data
        test_data = {
            "test": "data",
            "number": 123,
            "list": [1, 2, 3]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Test JSON generation
            result = generate_json(test_data, tmp_path)
            self.assertTrue(result)
            
            # Verify file was created
            self.assertTrue(os.path.exists(tmp_path))
            
            # Verify content
            with open(tmp_path, 'r') as f:
                loaded_data = json.load(f)
            self.assertEqual(loaded_data, test_data)
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_xml_generation(self):
        """Test XML generation functionality"""
        from exports.advanced_formats import generate_xml
        
        # Test data
        test_data = {
            "root": {
                "child": "value",
                "number": 123
            }
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Test XML generation
            result = generate_xml(test_data, tmp_path)
            self.assertTrue(result)
            
            # Verify file was created
            self.assertTrue(os.path.exists(tmp_path))
            
            # Verify content (basic check)
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertIn("<?xml", content)
            self.assertIn("root", content)
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_css_minification(self):
        """Test CSS minification functionality"""
        from scripts.frontend_optimizer import minify_css
        
        # Test CSS
        original_css = """
        /* This is a comment */
        .test {
            color: red;
            font-size: 16px;
        }
        """
        
        minified_css = minify_css(original_css)
        
        # Check that minification occurred
        self.assertLess(len(minified_css), len(original_css))
        self.assertNotIn("/*", minified_css)  # Comments should be removed
        self.assertIn(".test{color:red;", minified_css)  # Properties should be condensed
    
    def test_js_minification(self):
        """Test JavaScript minification functionality"""
        from scripts.frontend_optimizer import minify_js
        
        # Test JavaScript
        original_js = """
        // This is a comment
        var test = {
            value: "hello",
            number: 123
        };
        """
        
        minified_js = minify_js(original_js)
        
        # Check that minification occurred
        self.assertLess(len(minified_js), len(original_js))
        self.assertNotIn("//", minified_js)  # Single-line comments should be removed
        self.assertIn("var test", minified_js)  # Properties should be condensed

if __name__ == "__main__":
    unittest.main()