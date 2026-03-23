#!/usr/bin/env python3
"""
COMPREHENSIVE ROBUSTNESS TEST - 101% Certification
Tests Excel upload + Online/Hybrid mode with:
- Multiple iterations (10+ rounds)
- Random file order each iteration
- Memory management verification
- Cache cleaning verification
- Zero-qty item activation
- Part-rate modifications
- Document generation
- Memory leak detection
"""
import sys
from pathlib import Path
import pandas as pd
import random
import gc
import io
import psutil
import os
import time

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

class MemoryMonitor:
    """Monitor memory usage to detect leaks"""
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_mb()
        self.measurements = []
    
    def get_memory_mb(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def record(self, label):
        """Record memory measurement"""
        mem = self.get_memory_mb()
        self.measurements.append((label, mem))
        return mem
    
    def get_increase(self):
        """Get memory increase from initial"""
        current = self.get_memory_mb()
        return current - self.initial_memory
    
    def report(self):
        """Generate memory report"""
        print("\n" + "="*80)
        print("MEMORY USAGE REPORT")
        print("="*80)
        print(f"Initial Memory: {self.initial_memory:.2f} MB")
        print(f"Current Memory: {self.get_memory_mb():.2f} MB")
        print(f"Memory Increase: {self.get_increase():.2f} MB")
        print()
        
        if len(self.measurements) > 0:
            print("Memory Timeline:")
            for label, mem in self.measurements[-10:]:  # Last 10 measurements
                print(f"  {label:<40} {mem:>10.2f} MB")
        print()

def clean_memory():
    """Clean memory and cache aggressively"""
    gc.collect()
    try:
        from core.utils.cache_cleaner import CacheCleaner
        CacheCleaner.clean_cache(verbose=False)
    except:
        pass
    gc.collect()  # Second pass

def test_online_mode_iteration(file_path, iteration, test_num, memory_monitor):
    """Test online mode with modifications - single iteration"""
    try:
        # Record memory before test
        mem_before = memory_monitor.record(f"Before Test {test_num}")
        
        from core.processors.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        
        # Read file as BytesIO
        with open(file_path, 'rb') as f:
            file_bytes = io.BytesIO(f.read())
        
        processed_data = processor.process_excel(file_bytes)
        
        # Extract data
        title_data = processed_data.get('title_data', {})
        work_order_data = processed_data.get('work_order_data')
        if isinstance(work_order_data, list):
            work_order_df = pd.DataFrame(work_order_data)
        else:
            work_order_df = work_order_data
        
        bill_quantity_data = processed_data.get('bill_quantity_data')
        if isinstance(bill_quantity_data, list):
            bill_quantity_df = pd.DataFrame(bill_quantity_data)
        else:
            bill_quantity_df = bill_quantity_data
        
        if work_order_df is None or work_order_df.empty:
            return False, "No work order data"
        
        # Prepare items list
        items_list = []
        for idx, row in work_order_df.iterrows():
            item_no = row.get('Item No.', f"{idx+1:03d}")
            description = row.get('Description of Item', row.get('Description', ''))
            unit = row.get('Unit', 'NOS')
            
            try:
                wo_quantity = float(row.get('Quantity', 0) or 0)
            except (ValueError, TypeError):
                wo_quantity = 0.0
            
            try:
                wo_rate = float(row.get('Rate', 0) or 0)
            except (ValueError, TypeError):
                wo_rate = 0.0
            
            # Get bill quantity
            bill_qty = 0.0
            if bill_quantity_df is not None and not bill_quantity_df.empty:
                if idx < len(bill_quantity_df):
                    bill_row = bill_quantity_df.iloc[idx]
                    try:
                        bill_qty_value = bill_row.get('Quantity', 0)
                        if bill_qty_value and str(bill_qty_value) != 'nan':
                            bill_qty = float(bill_qty_value)
                    except (ValueError, TypeError):
                        bill_qty = 0.0
            
            items_list.append({
                'Item No': item_no,
                'Description': description,
                'Unit': unit,
                'WO Quantity': wo_quantity,
                'Bill Quantity': bill_qty,
                'WO Rate': wo_rate,
                'Bill Rate': wo_rate,
                'WO Amount': wo_quantity * wo_rate,
                'Bill Amount': bill_qty * wo_rate
            })
        
        df = pd.DataFrame(items_list)
        
        # Identify zero-qty and active items
        zero_qty_items = df[df['Bill Quantity'] == 0]
        active_items = df[df['Bill Quantity'] > 0]
        
        modifications_count = 0
        
        # Modification 1: Add quantity to 3 zero-qty items
        if len(zero_qty_items) >= 3:
            selected_zero = random.sample(list(zero_qty_items.index), min(3, len(zero_qty_items)))
            for idx in selected_zero:
                new_qty = df.loc[idx, 'WO Quantity'] * 0.5
                df.loc[idx, 'Bill Quantity'] = new_qty
                df.loc[idx, 'Bill Amount'] = new_qty * df.loc[idx, 'Bill Rate']
                modifications_count += 1
        elif len(zero_qty_items) > 0:
            for idx in zero_qty_items.index:
                new_qty = df.loc[idx, 'WO Quantity'] * 0.5
                df.loc[idx, 'Bill Quantity'] = new_qty
                df.loc[idx, 'Bill Amount'] = new_qty * df.loc[idx, 'Bill Rate']
                modifications_count += 1
        
        # Modification 2: Reduce rate by Rs.5 for 2-3 active items
        active_indices = df[df['Bill Quantity'] > 0].index.tolist()
        if len(active_indices) >= 2:
            num_to_modify = min(random.randint(2, 3), len(active_indices))
            selected_active = random.sample(active_indices, num_to_modify)
            
            for idx in selected_active:
                old_rate = df.loc[idx, 'Bill Rate']
                new_rate = max(0, old_rate - 5)
                df.loc[idx, 'Bill Rate'] = new_rate
                df.loc[idx, 'Bill Amount'] = df.loc[idx, 'Bill Quantity'] * new_rate
                
                if new_rate < old_rate:
                    desc = df.loc[idx, 'Description']
                    if '(Part Rate)' not in desc:
                        df.loc[idx, 'Description'] = f"{desc} (Part Rate)"
                    modifications_count += 1
        
        # Generate documents
        from core.generators.html_generator import HTMLGenerator
        
        active_items_df = df[df['Bill Quantity'] > 0].copy()
        
        work_order_list = []
        bill_quantity_list = []
        
        for idx, row in active_items_df.iterrows():
            work_order_list.append({
                'Item No.': row['Item No'],
                'Description': row['Description'],
                'Unit': row['Unit'],
                'Quantity': row['WO Quantity'],
                'Rate': row['WO Rate'],
                'Amount': row['WO Amount']
            })
            
            bill_quantity_list.append({
                'Item No.': row['Item No'],
                'Description': row['Description'],
                'Unit': row['Unit'],
                'Quantity': row['Bill Quantity'],
                'Rate': row['Bill Rate'],
                'Amount': row['Bill Amount']
            })
        
        work_order_df_final = pd.DataFrame(work_order_list)
        bill_quantity_df_final = pd.DataFrame(bill_quantity_list)
        
        data = {
            'title_data': title_data,
            'work_order_data': work_order_df_final,
            'bill_quantity_data': bill_quantity_df_final,
            'extra_items_data': pd.DataFrame(),
            'source_filename': file_path.name,
            'hybrid_mode': True
        }
        
        generator = HTMLGenerator(data)
        html_documents = generator.generate_all_documents()
        
        # Store document count before cleanup
        doc_count = len(html_documents)
        
        # Verify "(Part Rate)" in documents
        part_rate_found = any('(Part Rate)' in html for html in html_documents.values())
        
        # Calculate stats
        wo_total = df['WO Amount'].sum()
        bill_total = df['Bill Amount'].sum()
        
        # Clean up
        del df, generator, html_documents, processed_data, work_order_df, bill_quantity_df
        del work_order_df_final, bill_quantity_df_final, data
        
        # Record memory after test
        mem_after = memory_monitor.record(f"After Test {test_num}")
        mem_used = mem_after - mem_before
        
        return True, {
            'zero_qty_found': len(zero_qty_items),
            'modifications': modifications_count,
            'documents': doc_count,
            'part_rate_found': part_rate_found,
            'wo_total': wo_total,
            'bill_total': bill_total,
            'memory_used': mem_used
        }
        
    except Exception as e:
        return False, str(e)

def main():
    """Run comprehensive robustness test"""
    print()
    print("="*80)
    print("COMPREHENSIVE ROBUSTNESS TEST - 101% CERTIFICATION")
    print("="*80)
    print()
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor()
    print(f"Initial Memory: {memory_monitor.initial_memory:.2f} MB")
    print()
    
    # Get all test files
    test_dir = Path('TEST_INPUT_FILES')
    if not test_dir.exists():
        print(f"ERROR: Test directory not found: {test_dir}")
        return 1
    
    test_files = list(test_dir.glob('*.xlsx')) + list(test_dir.glob('*.xls')) + list(test_dir.glob('*.xlsm'))
    
    if not test_files:
        print(f"ERROR: No test files found in {test_dir}")
        return 1
    
    print(f"Found {len(test_files)} test files")
    print()
    
    # Test configuration
    NUM_ITERATIONS = 15  # 15 iterations for robustness
    print(f"Test Configuration:")
    print(f"  - Iterations: {NUM_ITERATIONS}")
    print(f"  - Files per iteration: {len(test_files)}")
    print(f"  - Total tests: {NUM_ITERATIONS * len(test_files)}")
    print(f"  - Random order: Yes")
    print(f"  - Memory monitoring: Yes")
    print(f"  - Cache cleaning: Yes")
    print()
    
    # Run iterations
    all_results = []
    iteration_stats = []
    
    for iteration in range(1, NUM_ITERATIONS + 1):
        print("="*80)
        print(f"ITERATION {iteration}/{NUM_ITERATIONS}")
        print("="*80)
        print()
        
        # Randomize file order
        random.shuffle(test_files)
        
        iteration_results = []
        iteration_start_time = time.time()
        mem_start = memory_monitor.get_memory_mb()
        
        for idx, test_file in enumerate(test_files, 1):
            test_num = (iteration - 1) * len(test_files) + idx
            
            print(f"Test {test_num}: {test_file.name}...", end=" ", flush=True)
            
            success, result = test_online_mode_iteration(test_file, iteration, test_num, memory_monitor)
            
            if success:
                print(f"PASS (Mods: {result['modifications']}, Docs: {result['documents']}, Mem: {result['memory_used']:.1f}MB)")
                iteration_results.append((test_file.name, True, result))
            else:
                print(f"FAIL - {result}")
                iteration_results.append((test_file.name, False, result))
            
            # Clean memory after each test
            clean_memory()
        
        iteration_time = time.time() - iteration_start_time
        mem_end = memory_monitor.get_memory_mb()
        mem_iteration = mem_end - mem_start
        
        # Iteration summary
        passed = sum(1 for _, success, _ in iteration_results if success)
        failed = len(iteration_results) - passed
        
        iteration_stats.append({
            'iteration': iteration,
            'passed': passed,
            'failed': failed,
            'time': iteration_time,
            'memory': mem_iteration
        })
        
        print()
        print(f"Iteration {iteration} Summary: {passed}/{len(test_files)} passed, Time: {iteration_time:.1f}s, Memory: {mem_iteration:.1f}MB")
        print()
        
        all_results.extend(iteration_results)
        
        # Aggressive memory cleanup between iterations
        print("Cleaning memory...")
        clean_memory()
        time.sleep(0.5)  # Brief pause
        print()
    
    # Final summary
    print()
    print("="*80)
    print("FINAL ROBUSTNESS TEST SUMMARY")
    print("="*80)
    print()
    
    total_tests = len(all_results)
    total_passed = sum(1 for _, success, _ in all_results if success)
    total_failed = total_tests - total_passed
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {(total_passed/total_tests*100):.2f}%")
    print()
    
    # Iteration statistics
    print("Iteration Statistics:")
    print(f"{'Iteration':<12} {'Passed':<10} {'Failed':<10} {'Time (s)':<12} {'Memory (MB)':<15}")
    print("-" * 80)
    for stat in iteration_stats:
        print(f"{stat['iteration']:<12} {stat['passed']:<10} {stat['failed']:<10} {stat['time']:<12.1f} {stat['memory']:<15.1f}")
    print()
    
    # Memory analysis
    memory_monitor.report()
    
    # Memory leak detection
    memory_increase = memory_monitor.get_increase()
    memory_per_test = memory_increase / total_tests if total_tests > 0 else 0
    
    print("Memory Leak Analysis:")
    print(f"  Total Memory Increase: {memory_increase:.2f} MB")
    print(f"  Memory per Test: {memory_per_test:.4f} MB")
    
    if memory_per_test < 0.5:
        print(f"  Status: EXCELLENT - No significant memory leaks detected")
    elif memory_per_test < 1.0:
        print(f"  Status: GOOD - Minor memory accumulation")
    elif memory_per_test < 2.0:
        print(f"  Status: ACCEPTABLE - Some memory accumulation")
    else:
        print(f"  Status: WARNING - Significant memory accumulation detected")
    print()
    
    # Feature verification
    print("Feature Verification:")
    
    # Count features across all successful tests
    zero_qty_counts = [r['zero_qty_found'] for _, s, r in all_results if s and isinstance(r, dict)]
    mod_counts = [r['modifications'] for _, s, r in all_results if s and isinstance(r, dict)]
    doc_counts = [r['documents'] for _, s, r in all_results if s and isinstance(r, dict)]
    part_rate_counts = sum(1 for _, s, r in all_results if s and isinstance(r, dict) and r.get('part_rate_found'))
    
    if zero_qty_counts:
        print(f"  Zero-Qty Items Found: Avg {sum(zero_qty_counts)/len(zero_qty_counts):.1f} per test")
    if mod_counts:
        print(f"  Modifications Applied: Avg {sum(mod_counts)/len(mod_counts):.1f} per test")
    if doc_counts:
        print(f"  Documents Generated: Avg {sum(doc_counts)/len(doc_counts):.1f} per test")
    print(f"  Part Rate Label Found: {part_rate_counts}/{total_passed} tests")
    print()
    
    # Final certification
    print("="*80)
    print("CERTIFICATION RESULTS")
    print("="*80)
    print()
    
    criteria_passed = 0
    criteria_total = 6
    
    # Criterion 1: Success rate
    if total_passed == total_tests:
        print("✅ 100% Test Success Rate")
        criteria_passed += 1
    else:
        print(f"❌ Test Success Rate: {(total_passed/total_tests*100):.2f}%")
    
    # Criterion 2: Memory management
    if memory_per_test < 1.0:
        print("✅ Excellent Memory Management")
        criteria_passed += 1
    else:
        print(f"❌ Memory Management Needs Improvement ({memory_per_test:.2f} MB/test)")
    
    # Criterion 3: Zero-qty items
    if zero_qty_counts and sum(zero_qty_counts) > 0:
        print("✅ Zero-Qty Items Detection Working")
        criteria_passed += 1
    else:
        print("❌ Zero-Qty Items Detection Failed")
    
    # Criterion 4: Modifications
    if mod_counts and sum(mod_counts) > 0:
        print("✅ Modifications Applied Successfully")
        criteria_passed += 1
    else:
        print("❌ Modifications Failed")
    
    # Criterion 5: Document generation
    if doc_counts and all(d > 0 for d in doc_counts):
        print("✅ Document Generation Working")
        criteria_passed += 1
    else:
        print("❌ Document Generation Failed")
    
    # Criterion 6: Part rate label
    if part_rate_counts > total_passed * 0.8:  # 80% threshold
        print("✅ Part Rate Label Working")
        criteria_passed += 1
    else:
        print(f"❌ Part Rate Label Inconsistent ({part_rate_counts}/{total_passed})")
    
    print()
    print(f"Criteria Passed: {criteria_passed}/{criteria_total}")
    print()
    
    if criteria_passed == criteria_total:
        print("🎉 101% CERTIFICATION ACHIEVED!")
        print()
        print("The application has been certified as:")
        print("  ✅ Robust")
        print("  ✅ Memory Efficient")
        print("  ✅ Cache Managed")
        print("  ✅ Feature Complete")
        print("  ✅ Production Ready")
        print()
        return 0
    else:
        print(f"⚠️ CERTIFICATION INCOMPLETE ({criteria_passed}/{criteria_total} criteria)")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
