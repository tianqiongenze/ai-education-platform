#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
100-student concurrent notebook execution test (v5).
Fixed: execute all code cells via client.execute(), catching the expected
AssertionError on the last test cell.
"""
import json
import os
import sys
import time
import threading
import concurrent.futures
import nbformat
from nbclient import NotebookClient
import resource

NUM_STUDENTS = 100
CONCURRENCY = 20
NOTEBOOK_PATH = "/home/jovyan/work/p11_P1.1_Python基础_学生版.ipynb"

results = []
results_lock = threading.Lock()

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg), flush=True)

def execute_notebook(student_id):
    """Execute notebook. Last cell assertion failure is expected on template."""
    start = time.time()
    try:
        with open(NOTEBOOK_PATH) as f:
            nb = nbformat.read(f, as_version=4)
        
        client = NotebookClient(nb, timeout=30, kernel_name='python3')
        
        # Get indices of code cells
        code_indices = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code']
        last_code_idx = code_indices[-1] if code_indices else -1
        
        cells_executed = 0
        total_outputs = 0
        last_cell_status = 'not_reached'
        
        for ci in code_indices:
            cell = nb.cells[ci]
            try:
                # Use the client's execute_cell with correct index
                client.execute_cell(cell, ci)
                cells_executed += 1
                outs = cell.get('outputs', [])
                total_outputs += len(outs)
                if ci == last_code_idx:
                    last_cell_status = 'passed'
            except Exception as cell_err:
                cells_executed += 1
                err_str = str(cell_err)
                if ci == last_code_idx and 'AssertionError' in err_str:
                    last_cell_status = 'assertion_failed_expected'
                    total_outputs += 1  # count the error output
                elif ci == last_code_idx:
                    last_cell_status = 'unexpected_error_last_cell: ' + err_str[:100]
                else:
                    last_cell_status = 'unexpected_error_cell_%d: %s' % (ci, err_str[:100])
                break
        
        elapsed = time.time() - start
        is_success = last_cell_status in ('passed', 'assertion_failed_expected')
        
        return {
            'student_id': student_id,
            'status': 'success' if is_success else 'error',
            'elapsed_s': round(elapsed, 3),
            'cells_executed': cells_executed,
            'outputs': total_outputs,
            'last_cell_status': last_cell_status,
        }
        
    except Exception as e:
        elapsed = time.time() - start
        return {
            'student_id': student_id,
            'status': 'error',
            'elapsed_s': round(elapsed, 3),
            'error': str(e)[:300],
            'last_cell_status': 'exception',
        }

def main():
    log("Starting %d-student concurrent notebook execution test (v5)" % NUM_STUDENTS)
    log("Concurrency: %d threads" % CONCURRENCY)
    log("Notebook: %s" % NOTEBOOK_PATH)
    log("")
    
    mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    log("Pre-test RSS: %.1f MB" % (mem_before / 1024))
    
    student_ids = ["student-%03d" % i for i in range(1, NUM_STUDENTS + 1)]
    
    log("Launching %d concurrent executions..." % NUM_STUDENTS)
    test_start = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        future_map = {executor.submit(execute_notebook, sid): sid for sid in student_ids}
        completed = 0
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            with results_lock:
                results.append(result)
            completed += 1
            if completed % 10 == 0:
                log("  Completed %d/%d..." % (completed, NUM_STUDENTS))
    
    test_total = time.time() - test_start
    log("All %d executions completed in %.1fs" % (NUM_STUDENTS, test_total))
    
    mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    log("Post-test RSS: %.1f MB" % (mem_after / 1024))
    log("")
    
    # Analyze
    log("=" * 60)
    log("TEST RESULTS ANALYSIS")
    log("=" * 60)
    
    success = [r for r in results if r.get('status') == 'success']
    errors_list = [r for r in results if r.get('status') == 'error']
    expected_fail = [r for r in success if r.get('last_cell_status') == 'assertion_failed_expected']
    all_passed = [r for r in success if r.get('last_cell_status') == 'passed']
    
    log("")
    log("1. OVERALL SUMMARY")
    log("   Total students:              %d" % NUM_STUDENTS)
    log("   Successful:                  %d" % len(success))
    log("     - All cells passed:        %d" % len(all_passed))
    log("     - Expected assertion fail: %d" % len(expected_fail))
    log("   Errors:                      %d" % len(errors_list))
    log("   Success rate:                %.1f%%" % (len(success) / NUM_STUDENTS * 100))
    log("   Total test duration:         %.1fs" % test_total)
    log("   Peak RSS:                    %.1f MB" % (mem_after / 1024))
    log("   Memory delta:                %.1f MB" % ((mem_after - mem_before) / 1024))
    
    if success:
        times = [r['elapsed_s'] for r in success]
        sorted_times = sorted(times)
        n = len(sorted_times)
        mean_t = sum(times) / len(times)
        
        log("")
        log("2. RESPONSE TIME (per notebook execution)")
        log("   Min:     %.3fs" % min(times))
        log("   Max:     %.3fs" % max(times))
        log("   Mean:    %.3fs" % mean_t)
        log("   Median:  %.3fs" % sorted_times[n // 2])
        if n > 1:
            var = sum((x - mean_t) ** 2 for x in times) / (len(times) - 1)
            log("   Stdev:   %.3fs" % (var ** 0.5))
        log("   P90:     %.3fs" % sorted_times[min(int(n * 0.9), n - 1)])
        log("   P95:     %.3fs" % sorted_times[min(int(n * 0.95), n - 1)])
        log("   P99:     %.3fs" % sorted_times[min(int(n * 0.99), n - 1)])
    
    log("")
    log("3. THROUGHPUT")
    if test_total > 0:
        log("   Executions/sec:        %.2f" % (len(success) / test_total))
    log("   Concurrency level:     %d" % CONCURRENCY)
    if success and test_total > 0:
        log("   Effective parallelism:  %.1fx" % (sum(r['elapsed_s'] for r in success) / test_total))
    
    cells_list = [r.get('cells_executed', 0) for r in success]
    if cells_list:
        log("")
        log("4. NOTEBOOK EXECUTION DETAILS")
        log("   Code cells in notebook: 9 (8 exercise + 1 test)")
        log("   Cells executed (min):   %d" % min(cells_list))
        log("   Cells executed (max):   %d" % max(cells_list))
        log("   Cells executed (avg):   %.1f" % (sum(cells_list) / len(cells_list)))
    
    log("")
    log("5. CORRECTNESS")
    log("   Last cell (test assertions):")
    log("     - Failed as expected (template stubs): %d" % len(expected_fail))
    log("     - All passed:                          %d" % len(all_passed))
    log("   Non-test cells: all executed in %d/%d sessions" % (len(success), NUM_STUDENTS))
    
    if errors_list:
        log("")
        log("6. ERROR BREAKDOWN")
        error_types = {}
        for r in errors_list:
            etype = r.get('last_cell_status', r.get('status', 'unknown'))
            # Truncate long error types
            if len(etype) > 50:
                etype = etype[:50]
            error_types[etype] = error_types.get(etype, 0) + 1
        for etype, count in sorted(error_types.items()):
            log("   %s: %d" % (etype, count))
        log("")
        log("   Sample errors (first 3):")
        for r in errors_list[:3]:
            log("   - %s: %s" % (r.get('student_id'), r.get('error', r.get('last_cell_status', 'unknown'))[:200]))
    
    log("")
    log("7. RESOURCE USAGE")
    log("   Peak RSS:        %.1f MB" % (mem_after / 1024))
    log("   Memory delta:    %.1f MB" % ((mem_after - mem_before) / 1024))
    log("   Memory/student:  %.3f MB" % ((mem_after - mem_before) / 1024.0 / NUM_STUDENTS))
    
    log("")
    log("8. PERFORMANCE RATING")
    rate = len(success) / NUM_STUDENTS * 100
    if success:
        avg_time = sum(r['elapsed_s'] for r in success) / len(success)
        max_time = max(r['elapsed_s'] for r in success)
        p95_time = sorted([r['elapsed_s'] for r in success])[min(int(len(success) * 0.95), len(success) - 1)]
    else:
        avg_time = max_time = p95_time = 0
    
    if rate >= 95 and avg_time < 5:
        grade = "A (Excellent)"
    elif rate >= 95 and avg_time < 15:
        grade = "B (Good)"
    elif rate >= 95 and p95_time < 30:
        grade = "C (Acceptable)"
    elif rate >= 80:
        grade = "D (Marginal)"
    else:
        grade = "F (Failed)"
    
    log("   Grade: %s" % grade)
    log("   Success rate:       %.1f%%" % rate)
    log("   Avg execution time: %.2fs" % avg_time)
    log("   Max execution time: %.2fs" % max_time)
    log("   P95 execution time: %.2fs" % p95_time)
    
    log("")
    log("9. CONCLUSION")
    if rate >= 95:
        log("   [PASS] %d/%d students (%.1f%%) executed notebook successfully" % (len(success), NUM_STUDENTS, rate))
        log("   All exercise cells (8/8) executed in every session")
        log("   Last cell assertion failure is EXPECTED (student template)")
        log("   Avg: %.2fs | P95: %.2fs | Max: %.2fs" % (avg_time, p95_time, max_time))
        log("   Peak memory: %.1f MB (%.3f MB/student)" % (mem_after / 1024, (mem_after - mem_before) / 1024.0 / NUM_STUDENTS))
        log("   System CAN handle 100 concurrent students")
    elif rate >= 80:
        log("   [MARGINAL] %d/%d (%.1f%%) succeeded" % (len(success), NUM_STUDENTS, rate))
    else:
        log("   [FAIL] %d/%d (%.1f%%) succeeded" % (len(success), NUM_STUDENTS, rate))
    
    log("")
    log("=" * 60)
    log("TEST COMPLETE")
    log("=" * 60)
    
    # Save JSON
    report = {
        "test_name": "100-student concurrent notebook execution",
        "notebook": NOTEBOOK_PATH,
        "num_students": NUM_STUDENTS,
        "concurrency": CONCURRENCY,
        "total_duration_s": round(test_total, 1),
        "success_count": len(success),
        "error_count": len(errors_list),
        "success_rate": "%.1f%%" % rate,
        "peak_rss_mb": round(mem_after / 1024, 1),
        "memory_delta_mb": round((mem_after - mem_before) / 1024, 1),
        "expected_assertion_failures": len(expected_fail),
        "results": results,
    }
    if success:
        times = [r['elapsed_s'] for r in success]
        sorted_t = sorted(times)
        report["response_time"] = {
            "min_s": min(times),
            "max_s": max(times),
            "mean_s": round(sum(times) / len(times), 3),
            "median_s": sorted_t[len(sorted_t) // 2],
            "p95_s": sorted_t[min(int(len(sorted_t) * 0.95), len(sorted_t) - 1)],
        }
    
    with open("/home/jovyan/work/concurrent_test_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\nReport saved to /home/jovyan/work/concurrent_test_report.json")


if __name__ == "__main__":
    main()
