#!/usr/bin/env python3
"""
Project Cleanup Script
Removes redundant, duplicate, unwanted, legacy, and cache files
Keeps only production-ready, essential files
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

class ProjectCleaner:
    """Clean up project by removing unnecessary files."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.deleted_files: List[Path] = []
        self.deleted_dirs: List[Path] = []
        self.freed_space = 0
        
    def get_size(self, path: Path) -> int:
        """Get size of file or directory."""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def delete_file(self, path: Path, reason: str):
        """Delete a file."""
        if not path.exists():
            return
        
        size = self.get_size(path)
        
        if self.dry_run:
            print(f"[DRY RUN] Would delete: {path} ({size:,} bytes) - {reason}")
        else:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                print(f"✅ Deleted: {path} ({size:,} bytes) - {reason}")
                self.deleted_files.append(path)
                self.freed_space += size
            except Exception as e:
                print(f"❌ Failed to delete {path}: {e}")
    
    def clean_cache_files(self):
        """Remove all cache files."""
        print("\n" + "="*60)
        print("🧹 Cleaning Cache Files")
        print("="*60)
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/.pytest_cache",
            "**/.mypy_cache",
            "**/.ruff_cache",
            "**/*.egg-info",
            ".coverage",
            "htmlcov",
        ]
        
        for pattern in cache_patterns:
            for path in Path(".").glob(pattern):
                self.delete_file(path, "Cache file")
    
    def clean_legacy_files(self):
        """Remove legacy/old files."""
        print("\n" + "="*60)
        print("🗑️ Cleaning Legacy Files")
        print("="*60)
        
        legacy_files = [
            # Old batch processing scripts
            "batch_process_all_files.py",
            "run_interactive_bill_generation.py",
            "generate_word_files.py",
            "test_chrome_pdf.py",
            "test_streamlit.py",
            
            # Old app versions
            "dash_app.py",
            "app/main.py",  # Keep only root app.py
            
            # Old deployment files
            "DEPLOY_NOW.md",
            "NO_SHRINKING_VERIFIED.md",
            "STREAMLIT_DEPLOYMENT.md",
            "maintain-billgen-historical.bat",
            "RUN_BATCH_ALL.bat",
            "INSTALL.sh",
            "START_HERE.txt",
            
            # Old test files
            "test_chrome_output.pdf",
            
            # Duplicate documentation
            "CREDITS.md",  # Info is in README
        ]
        
        for file in legacy_files:
            path = Path(file)
            if path.exists():
                self.delete_file(path, "Legacy file")
    
    def clean_duplicate_docs(self):
        """Remove duplicate documentation."""
        print("\n" + "="*60)
        print("📄 Cleaning Duplicate Documentation")
        print("="*60)
        
        # Keep only essential docs, remove duplicates
        docs_to_remove = [
            # Keep: README.md, STREAMLIT_CLOUD_DEPLOYMENT.md, DEPLOYMENT_READY.md
            # Keep: ENTERPRISE_DEPLOYMENT_COMPLETE.md, TEST_RESULTS.md
            # Remove others that are redundant
        ]
        
        for doc in docs_to_remove:
            path = Path(doc)
            if path.exists():
                self.delete_file(path, "Duplicate documentation")
    
    def clean_test_outputs(self):
        """Clean test output directories."""
        print("\n" + "="*60)
        print("🧪 Cleaning Test Outputs")
        print("="*60)
        
        output_dirs = [
            "test_outputs",
            "uploaded_outputs",
            "batch_outputs",
            "All_Outputs",
            "PERFECT_PDFS",
        ]
        
        for dir_name in output_dirs:
            path = Path(dir_name)
            if path.exists() and path.is_dir():
                # Check if directory has files
                files = list(path.rglob("*"))
                if files:
                    self.delete_file(path, "Test output directory")
    
    def clean_data_folder(self):
        """Clean data folder with old test files."""
        print("\n" + "="*60)
        print("📦 Cleaning Data Folder")
        print("="*60)
        
        data_path = Path("data")
        if data_path.exists():
            # Keep only essential files, remove test files
            files_to_remove = [
                "data/🚀_LAUNCH_APP.bat",
                "data/comprehensive_test.py",
                "data/comprehensive_workflow_test.py",
                "data/final_deployment_test.py",
                "data/final_integration_test.py",
                "data/final_validation.py",
                "data/test_consolidated_app.py",
                "data/ultimate_validation_test.py",
                "data/validate_web_ready.py",
                "data/DEPLOYMENT_READY.md",
            ]
            
            for file in files_to_remove:
                path = Path(file)
                if path.exists():
                    self.delete_file(path, "Old test file")
    
    def clean_scripts_folder(self):
        """Clean scripts folder."""
        print("\n" + "="*60)
        print("📜 Cleaning Scripts Folder")
        print("="*60)
        
        scripts_to_remove = [
            "scripts/test_all_apps_comprehensive.py",
            "scripts/test_pdf_generation_comprehensive.py",
            "scripts/verify_all_apps.py",
            "scripts/update_all_apps.py",
            "scripts/consolidate_apps.py",
            "scripts/compare_html_pdf.py",
            "scripts/diagnose_pdf_issues.py",
            "scripts/fix_pdf_generation.py",
        ]
        
        for script in scripts_to_remove:
            path = Path(script)
            if path.exists():
                self.delete_file(path, "Old script")
    
    def clean_docs_folder(self):
        """Clean docs folder."""
        print("\n" + "="*60)
        print("📚 Cleaning Docs Folder")
        print("="*60)
        
        docs_to_remove = [
            "docs/MIGRATION_GUIDE.md",
            "docs/README_PDF_OPTIMIZATION.md",
            "docs/STREAMLIT_DEPLOYMENT_FIX.md",
        ]
        
        for doc in docs_to_remove:
            path = Path(doc)
            if path.exists():
                self.delete_file(path, "Old documentation")
    
    def clean_vscode_settings(self):
        """Clean VS Code settings."""
        print("\n" + "="*60)
        print("⚙️ Cleaning IDE Settings")
        print("="*60)
        
        # Keep .vscode but clean unnecessary files
        vscode_path = Path(".vscode")
        if vscode_path.exists():
            print(f"ℹ️ Keeping .vscode folder (IDE settings)")
    
    def clean_git_artifacts(self):
        """Clean git artifacts (keep .git folder)."""
        print("\n" + "="*60)
        print("🔧 Checking Git Artifacts")
        print("="*60)
        
        print("ℹ️ Keeping .git folder (version control)")
    
    def clean_docker_files(self):
        """Check Docker files."""
        print("\n" + "="*60)
        print("🐳 Checking Docker Files")
        print("="*60)
        
        docker_files = ["Dockerfile", "docker-compose.yml"]
        for file in docker_files:
            if Path(file).exists():
                print(f"ℹ️ Keeping {file} (deployment)")
    
    def clean_pages_folder(self):
        """Clean pages folder."""
        print("\n" + "="*60)
        print("📑 Checking Pages Folder")
        print("="*60)
        
        pages_path = Path("pages")
        if pages_path.exists():
            print(f"ℹ️ Keeping pages/ folder (Streamlit multi-page)")
    
    def clean_assets_folder(self):
        """Clean assets folder."""
        print("\n" + "="*60)
        print("🎨 Checking Assets Folder")
        print("="*60)
        
        assets_path = Path("assets")
        if assets_path.exists():
            print(f"ℹ️ Keeping assets/ folder (UI resources)")
    
    def show_summary(self):
        """Show cleanup summary."""
        print("\n" + "="*60)
        print("📊 Cleanup Summary")
        print("="*60)
        
        if self.dry_run:
            print("\n⚠️ DRY RUN MODE - No files were actually deleted")
        
        print(f"\n✅ Files/Directories deleted: {len(self.deleted_files)}")
        print(f"💾 Space freed: {self.freed_space:,} bytes ({self.freed_space / (1024*1024):.2f} MB)")
        
        if self.deleted_files:
            print("\n📋 Deleted items:")
            for path in self.deleted_files[:20]:  # Show first 20
                print(f"   - {path}")
            if len(self.deleted_files) > 20:
                print(f"   ... and {len(self.deleted_files) - 20} more")
    
    def run_cleanup(self):
        """Run all cleanup operations."""
        print("="*60)
        print("🧹 PROJECT CLEANUP SCRIPT")
        print("="*60)
        
        if self.dry_run:
            print("\n⚠️ RUNNING IN DRY RUN MODE")
            print("No files will be deleted. Review the output first.")
        else:
            print("\n⚠️ RUNNING IN LIVE MODE")
            print("Files will be permanently deleted!")
        
        # Run all cleanup operations
        self.clean_cache_files()
        self.clean_legacy_files()
        self.clean_duplicate_docs()
        self.clean_test_outputs()
        self.clean_data_folder()
        self.clean_scripts_folder()
        self.clean_docs_folder()
        self.clean_vscode_settings()
        self.clean_git_artifacts()
        self.clean_docker_files()
        self.clean_pages_folder()
        self.clean_assets_folder()
        
        # Show summary
        self.show_summary()
        
        print("\n" + "="*60)
        print("✅ CLEANUP COMPLETE")
        print("="*60)


def main():
    """Main function."""
    import sys
    
    # Check for dry run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if not dry_run:
        print("\n⚠️ WARNING: This will permanently delete files!")
        print("Run with --dry-run flag first to preview changes.")
        response = input("\nContinue? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Cleanup cancelled")
            return
    
    # Run cleanup
    cleaner = ProjectCleaner(dry_run=dry_run)
    cleaner.run_cleanup()
    
    if dry_run:
        print("\n💡 To actually delete files, run without --dry-run flag:")
        print("   python cleanup_project.py")


if __name__ == "__main__":
    main()
