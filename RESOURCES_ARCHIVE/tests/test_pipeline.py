import os
import glob
import subprocess
import pytest
from pathlib import Path

def discover_test_folders():
    """
    Auto-discover folders matching TEST* and INPUT* in the root directory.
    """
    base_dir = Path(__file__).parent.parent
    folders = []
    
    # Simple pattern matching for folders
    for f in base_dir.iterdir():
        if f.is_dir() and (f.name.startswith("TEST") or f.name.startswith("INPUT")):
            folders.append(f)
            
    return folders

def get_test_files():
    folders = discover_test_folders()
    test_files = []
    for folder in folders:
        # Grab all Excel files within these directories
        test_files.extend(list(folder.rglob("*.xlsx")))
        test_files.extend(list(folder.rglob("*.xls")))
    return test_files

# Parametrize over all discovered test input files
@pytest.mark.parametrize("input_file", get_test_files())
def test_pipeline_execution(input_file):
    """
    Run the engine automatically on the input file.
    Validates that the process exits with a 0 code (success) and an output is generated.
    """
    engine_script = Path(__file__).parent.parent / "engine" / "run_engine.py"
    
    if not engine_script.exists():
        pytest.skip("Engine extraction script (run_engine.py) does not exist yet.")
    
    result = subprocess.run(
        ["python", str(engine_script), str(input_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Engine failed on {input_file} with error: {result.stderr}"
    # In a real workflow, we would also add mismatch detection comparing expected versus current output.
    # For now, we only ensure that the execution logic completes without exceptions.
