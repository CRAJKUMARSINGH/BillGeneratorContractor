"""
Cache Cleaner - Automatic cache cleaning utility
Cleans Python cache files after each run
"""
import shutil
from pathlib import Path
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

class CacheCleaner:
    """Automatic cache cleaner"""
    
    # Cache patterns to clean
    CACHE_PATTERNS = [
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/*.pyd',
        '.pytest_cache',
        '.mypy_cache',
        '.ruff_cache',
    ]
    
    @staticmethod
    def clean_cache(root_dir: str = '.', verbose: bool = False) -> Tuple[int, int]:
        """
        Clean all cache files and directories
        
        Args:
            root_dir: Root directory to clean from
            verbose: Print cleaning progress
            
        Returns:
            Tuple of (directories_removed, files_removed)
        """
        root_path = Path(root_dir)
        dirs_removed = 0
        files_removed = 0
        
        # Clean cache directories
        for pattern in CacheCleaner.CACHE_PATTERNS:
            if '**' in pattern:
                # Recursive pattern
                for path in root_path.glob(pattern):
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                            dirs_removed += 1
                            if verbose:
                                logger.info(f"Removed directory: {path}")
                        elif path.is_file():
                            path.unlink()
                            files_removed += 1
                            if verbose:
                                logger.info(f"Removed file: {path}")
                    except Exception as e:
                        if verbose:
                            logger.warning(f"Failed to remove {path}: {e}")
            else:
                # Non-recursive pattern
                path = root_path / pattern
                if path.exists():
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                            dirs_removed += 1
                            if verbose:
                                logger.info(f"Removed directory: {path}")
                        elif path.is_file():
                            path.unlink()
                            files_removed += 1
                            if verbose:
                                logger.info(f"Removed file: {path}")
                    except Exception as e:
                        if verbose:
                            logger.warning(f"Failed to remove {path}: {e}")
        
        return dirs_removed, files_removed
    
    @staticmethod
    def clean_on_exit():
        """Clean cache on application exit"""
        try:
            dirs, files = CacheCleaner.clean_cache(verbose=False)
            if dirs > 0 or files > 0:
                logger.info(f"Cache cleaned: {dirs} directories, {files} files")
        except Exception as e:
            logger.warning(f"Cache cleaning failed: {e}")
    
    @staticmethod
    def register_exit_handler():
        """Register automatic cache cleaning on exit"""
        import atexit
        atexit.register(CacheCleaner.clean_on_exit)


# Auto-register exit handler
CacheCleaner.register_exit_handler()
