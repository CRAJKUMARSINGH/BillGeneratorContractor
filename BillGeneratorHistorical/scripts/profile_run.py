"""
Performance profiling script for the Stream Bill Generator
This script profiles the main application to identify performance bottlenecks.
"""
import cProfile
import pstats
import io
import sys
import os

def profile_application():
    """Profile the main application entry point"""
    # Add the parent directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Profile the streamlit app
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        # Import and run the main application
        import streamlit_app
        print("Application imported and executed successfully")
    except Exception as e:
        print(f"Error during profiling: {e}")
    
    profiler.disable()
    
    # Save profiling results
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('tottime')
    ps.print_stats(50)  # Print top 50 functions by total time
    
    # Save to file
    with open('profile_summary.txt', 'w') as f:
        f.write(s.getvalue())
    
    print("Profiling complete. Results saved to profile_summary.txt")
    print("Top functions by total time:")
    print(s.getvalue()[:1000])  # Print first 1000 characters

if __name__ == "__main__":
    profile_application()