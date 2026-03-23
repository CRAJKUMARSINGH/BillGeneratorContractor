"""
Frontend optimization script for the Stream Bill Generator
This script optimizes static assets and UI components.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List

def minify_css(css_content: str) -> str:
    """
    Minify CSS content by removing unnecessary whitespace and comments
    
    Args:
        css_content (str): CSS content to minify
        
    Returns:
        str: Minified CSS content
    """
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Remove unnecessary whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
    
    # Remove leading and trailing whitespace
    css_content = css_content.strip()
    
    return css_content

def minify_js(js_content: str) -> str:
    """
    Minify JavaScript content by removing unnecessary whitespace and comments
    
    Args:
        js_content (str): JavaScript content to minify
        
    Returns:
        str: Minified JavaScript content
    """
    # Remove single-line comments
    js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    
    # Remove unnecessary whitespace
    js_content = re.sub(r'\s+', ' ', js_content)
    js_content = re.sub(r'\s*([{}();,:])\s*', r'\1', js_content)
    
    # Remove leading and trailing whitespace
    js_content = js_content.strip()
    
    return js_content

def optimize_static_assets(static_dir: str = "static") -> Dict[str, int]:
    """
    Optimize static assets (CSS, JS) by minifying them
    
    Args:
        static_dir (str): Directory containing static assets
        
    Returns:
        Dict[str, int]: Optimization results
    """
    results = {
        "files_processed": 0,
        "bytes_saved": 0
    }
    
    if not os.path.exists(static_dir):
        print(f"Static directory {static_dir} not found")
        return results
    
    # Process CSS files
    for css_file in Path(static_dir).rglob("*.css"):
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            minified_content = minify_css(original_content)
            
            # Save minified content
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(minified_content)
            
            original_size = len(original_content.encode('utf-8'))
            minified_size = len(minified_content.encode('utf-8'))
            bytes_saved = original_size - minified_size
            
            results["files_processed"] += 1
            results["bytes_saved"] += bytes_saved
            
            print(f"Minified {css_file}: {bytes_saved} bytes saved")
            
        except Exception as e:
            print(f"Error minifying {css_file}: {e}")
    
    # Process JS files
    for js_file in Path(static_dir).rglob("*.js"):
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            minified_content = minify_js(original_content)
            
            # Save minified content
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(minified_content)
            
            original_size = len(original_content.encode('utf-8'))
            minified_size = len(minified_content.encode('utf-8'))
            bytes_saved = original_size - minified_size
            
            results["files_processed"] += 1
            results["bytes_saved"] += bytes_saved
            
            print(f"Minified {js_file}: {bytes_saved} bytes saved")
            
        except Exception as e:
            print(f"Error minifying {js_file}: {e}")
    
    return results

def generate_asset_manifest(static_dir: str = "static", manifest_file: str = "static/manifest.json") -> None:
    """
    Generate a manifest file for static assets with hashes for cache busting
    
    Args:
        static_dir (str): Directory containing static assets
        manifest_file (str): Path where manifest file should be saved
    """
    import hashlib
    
    manifest = {}
    
    if not os.path.exists(static_dir):
        print(f"Static directory {static_dir} not found")
        return
    
    # Process all static files
    for static_file in Path(static_dir).rglob("*"):
        if static_file.is_file() and static_file.name != "manifest.json":
            try:
                # Calculate file hash
                with open(static_file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                
                # Create relative path
                relative_path = str(static_file.relative_to(static_dir))
                manifest[relative_path] = f"{relative_path}?v={file_hash}"
                
            except Exception as e:
                print(f"Error processing {static_file}: {e}")
    
    # Save manifest
    try:
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Asset manifest saved to {manifest_file}")
    except Exception as e:
        print(f"Error saving manifest: {e}")

def optimize_templates(template_dir: str = "templates") -> Dict[str, int]:
    """
    Optimize HTML templates by removing unnecessary whitespace
    
    Args:
        template_dir (str): Directory containing templates
        
    Returns:
        Dict[str, int]: Optimization results
    """
    results = {
        "files_processed": 0,
        "bytes_saved": 0
    }
    
    if not os.path.exists(template_dir):
        print(f"Template directory {template_dir} not found")
        return results
    
    # Process HTML files
    for html_file in Path(template_dir).rglob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Simple whitespace optimization
            optimized_content = re.sub(r'\s+', ' ', original_content)
            optimized_content = optimized_content.strip()
            
            # Save optimized content
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            
            original_size = len(original_content.encode('utf-8'))
            optimized_size = len(optimized_content.encode('utf-8'))
            bytes_saved = original_size - optimized_size
            
            results["files_processed"] += 1
            results["bytes_saved"] += bytes_saved
            
            print(f"Optimized {html_file}: {bytes_saved} bytes saved")
            
        except Exception as e:
            print(f"Error optimizing {html_file}: {e}")
    
    return results

def run_frontend_optimization() -> None:
    """Run all frontend optimization tasks"""
    print("Running frontend optimization...")
    
    # Optimize static assets
    print("\n1. Optimizing static assets...")
    asset_results = optimize_static_assets()
    print(f"   Processed {asset_results['files_processed']} files, saved {asset_results['bytes_saved']} bytes")
    
    # Generate asset manifest
    print("\n2. Generating asset manifest...")
    generate_asset_manifest()
    
    # Optimize templates
    print("\n3. Optimizing templates...")
    template_results = optimize_templates()
    print(f"   Processed {template_results['files_processed']} files, saved {template_results['bytes_saved']} bytes")
    
    print("\nFrontend optimization complete!")

if __name__ == "__main__":
    run_frontend_optimization()