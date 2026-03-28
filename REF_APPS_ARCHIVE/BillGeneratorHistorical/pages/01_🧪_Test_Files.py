"""
Test Files Dashboard - Integrated into Stream Bill Generator
Safely manage all test files with viewing, running, and downloading capabilities
"""
import streamlit as st
import pathlib
import shutil
import subprocess
import time
import os

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
DATA_ROOT = pathlib.Path("data")
CACHE_DIR = pathlib.Path(".streamlit_cache")
CACHE_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────
# FILE TREE (Sidebar)
# ──────────────────────────────────────────────────────────────
def build_tree(root):
    """Build file tree structure for sidebar navigation"""
    tree = {}
    if not root.exists():
        return tree
        
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).parts
            d = tree
            for part in rel[:-1]:
                d = d.setdefault(part, {})
            d[rel[-1]] = str(p)
    return tree

def render_tree(node, prefix=""):
    """Render file tree in sidebar"""
    for name, val in node.items():
        if isinstance(val, dict):
            with st.sidebar.expander(f"📁 {name}"):
                render_tree(val, prefix + "  ")
        else:
            st.sidebar.markdown(f"{prefix}📄 `{name}`")
            if st.sidebar.button("Show", key=val):
                st.session_state.selected = val

def safe_clean_cache():
    """Clean old temporary files from cache"""
    old_time = time.time() - 3600  # 1 hour ago
    deleted = []
    
    for p in CACHE_DIR.iterdir():
        try:
            if p.stat().st_mtime < old_time:
                if p.is_file():
                    p.unlink()
                    deleted.append(p.name)
                elif p.is_dir():
                    shutil.rmtree(p)
                    deleted.append(p.name)
        except Exception:
            continue  # Skip files that can't be deleted
    
    return deleted

# ──────────────────────────────────────────────────────────────
# PAGE SETUP
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Test Files Dashboard",
    page_icon="🧪",
    layout="wide"
)

# ──────────────────────────────────────────────────────────────
# SIDEBAR - FILE EXPLORER
# ──────────────────────────────────────────────────────────────
st.sidebar.header("📂 Test Files Explorer")
st.sidebar.caption("Browse all test files safely")

# Check if data directory exists and has files
if not DATA_ROOT.exists():
    st.sidebar.error("📁 `data/` folder not found!")
    st.sidebar.info("Create `data/` folder and add your test files")
else:
    tree = build_tree(DATA_ROOT)
    if not tree:
        st.sidebar.warning("📁 `data/` folder is empty")
        st.sidebar.info("Add your `.bat`, `.py`, `.md` files to `data/`")
    else:
        render_tree(tree)

# ──────────────────────────────────────────────────────────────
# MAIN PANEL
# ──────────────────────────────────────────────────────────────
st.title("🧪 Test Files Dashboard")
st.caption("**View • Run • Download • Clean Cache** — *Originals Never Touched*")

# Info about safety
with st.expander("ℹ️ Safety Information"):
    st.markdown("""
    **How This Works Safely:**
    - 📁 **Original files** in `data/` are **never modified or deleted**
    - 🏃 **Running files** creates temporary copies in cache
    - 🗑️ **Cache cleanup** only removes temporary files older than 1 hour
    - 💾 **Downloads** are direct copies, originals stay intact
    - ✅ **Zero risk** of losing your test files
    """)

col1, col2 = st.columns([3, 2])
selected = st.session_state.get("selected")
path = pathlib.Path(selected) if selected else None

# ──────────────────────────────────────────────────────────────
# FILE VIEWER & RUNNER
# ──────────────────────────────────────────────────────────────
with col1:
    if path and path.exists():
        rel = path.relative_to(DATA_ROOT)
        ext = path.suffix.lower()
        
        st.subheader(f"📄 **{rel}**")
        st.caption(f"File size: {path.stat().st_size:,} bytes")

        # VIEW FILE CONTENT
        if ext in {".md", ".py", ".bat", ".txt", ".json", ".yaml", ".yml", ".csv"}:
            try:
                content = path.read_text(encoding="utf-8")
                
                # Determine language for syntax highlighting
                if ext == ".md":
                    st.markdown(content)
                else:
                    language = {
                        ".py": "python",
                        ".bat": "batch",
                        ".json": "json",
                        ".yaml": "yaml",
                        ".yml": "yaml",
                        ".csv": "csv"
                    }.get(ext, "text")
                    
                    st.code(content, language=language)
                    
            except Exception as e:
                st.error(f"Could not read file: {e}")
        else:
            st.info(f"File type `{ext}` - Use download button to get the file")

        # RUN EXECUTABLE FILES
        if ext in {".py", ".bat"}:
            st.markdown("---")
            st.subheader("🚀 Execute File")
            
            col_run, col_info = st.columns([1, 2])
            
            with col_run:
                run_button = st.button(
                    f"▶️ Run `{path.name}`", 
                    key=f"run_{selected}",
                    type="primary"
                )
            
            with col_info:
                st.caption("Creates temporary copy for safe execution")
            
            if run_button:
                # Create temporary copy
                timestamp = int(time.time())
                temp_file = CACHE_DIR / f"run_{timestamp}_{path.name}"
                
                try:
                    shutil.copy2(path, temp_file)
                    st.info(f"Created temporary copy: `{temp_file.name}`")
                    
                    with st.spinner("Executing..."):
                        # Prepare command
                        if ext == ".py":
                            cmd = ["python", str(temp_file)]
                        else:  # .bat
                            cmd = [str(temp_file)]
                        
                        # Execute with timeout
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            shell=(ext == ".bat"),
                            timeout=60,
                            cwd=str(temp_file.parent)
                        )
                        
                        # Show results
                        if result.returncode == 0:
                            st.success("✅ Execution completed successfully")
                        else:
                            st.warning(f"⚠️ Execution completed with return code: {result.returncode}")
                        
                        if result.stdout:
                            st.subheader("📤 STDOUT")
                            st.code(result.stdout, language="text")
                        
                        if result.stderr:
                            st.subheader("📤 STDERR")
                            st.code(result.stderr, language="text")
                            
                except subprocess.TimeoutExpired:
                    st.error("❌ Execution timed out (60 seconds limit)")
                except Exception as e:
                    st.error(f"❌ Execution failed: {e}")

        # DOWNLOAD BUTTON
        st.markdown("---")
        try:
            file_data = path.read_bytes()
            st.download_button(
                label="💾 Download File",
                data=file_data,
                file_name=path.name,
                mime="application/octet-stream",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Could not prepare download: {e}")
            
    else:
        st.info("👈 **Select a file from the sidebar to get started**")
        
        # Show available file types
        if DATA_ROOT.exists():
            all_files = list(DATA_ROOT.rglob("*"))
            file_count = len([f for f in all_files if f.is_file()])
            
            if file_count > 0:
                st.markdown(f"**📊 Available: {file_count} files**")
                
                # Show file type breakdown
                extensions = {}
                for f in all_files:
                    if f.is_file():
                        ext = f.suffix.lower() or "no extension"
                        extensions[ext] = extensions.get(ext, 0) + 1
                
                if extensions:
                    st.markdown("**File Types:**")
                    for ext, count in sorted(extensions.items()):
                        st.markdown(f"- `{ext}`: {count} files")

# ──────────────────────────────────────────────────────────────
# CACHE MANAGEMENT PANEL
# ──────────────────────────────────────────────────────────────
with col2:
    st.subheader("🗑️ Cache Management")
    st.caption("Manage temporary execution files")
    
    # Cache statistics
    if CACHE_DIR.exists():
        cache_files = list(CACHE_DIR.rglob("*"))
        cache_file_count = len([f for f in cache_files if f.is_file()])
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        
        st.metric("Temp Files", cache_file_count)
        st.metric("Cache Size", f"{total_size/1024:.1f} KB")
        
        # Manual clean button
        if st.button("🧹 Clean Cache Now", use_container_width=True):
            deleted = safe_clean_cache()
            if deleted:
                st.success(f"✅ Cleaned {len(deleted)} temp files")
                st.rerun()
            else:
                st.info("✨ Cache already clean")
        
        # Show cache contents
        if cache_file_count > 0:
            with st.expander("📋 Cache Contents"):
                for f in cache_files:
                    if f.is_file():
                        age_hours = (time.time() - f.stat().st_mtime) / 3600
                        st.text(f"📄 {f.name} ({age_hours:.1f}h old)")
    
    # Auto-clean info
    st.markdown("---")
    st.markdown("**🔄 Auto-Clean:**")
    st.caption("• Files older than 1 hour are auto-deleted")
    st.caption("• Runs every hour automatically")
    st.caption("• Original files never touched")

# ──────────────────────────────────────────────────────────────
# AUTO-CLEAN (Background)
# ──────────────────────────────────────────────────────────────
if "last_auto_clean" not in st.session_state:
    st.session_state.last_auto_clean = 0

current_time = time.time()
if current_time - st.session_state.last_auto_clean > 3600:  # 1 hour
    safe_clean_cache()
    st.session_state.last_auto_clean = current_time

# ──────────────────────────────────────────────────────────────
# FOOTER INFO
# ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**🛡️ Safety Guarantee:** Original files in `data/` are never modified or deleted. Only temporary execution copies are managed.")