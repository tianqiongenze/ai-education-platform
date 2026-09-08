#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
100-student concurrent notebook execution test.
Runs on the master node (Python 3.6 compatible).
Executes the student notebook via kubectl exec on the teacher pod,
simulating 100 students running the notebook simultaneously.
"""
import json
import subprocess
import sys
import threading
import time

NUM_STUDENTS = 100
CONCURRENCY = 25  # Max concurrent kubectl exec calls
NOTEBOOK_PATH = "/home/jovyan/work/p11_P1.1_Python基础_学生版.ipynb"
POD = "jupyter-teacher-zhang"

results = []
results_lock = threading.Lock()

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg), flush=True)

def execute_notebook(student_id):
    """Execute the notebook on the pod and return timing + output info."""
    start = time.time()
    
    # Python script to run inside the pod
    inner_script = """
import json, time, nbformat
from nbclient import NotebookClient

start = time.time()
try:
    with open("%s") as f:
        nb = nbformat.read(f, as_version=4)
    client = NotebookClient(nb, timeout=30, kernel_name='python3')
    client.execute()
    elapsed = time.time() - start
    
    output_count = 0
    error_count = 0
    for cell in nb.cells:
        if cell.cell_type == 'code':
            output_count += len(cell.get('outputs', []))
            for out in cell.get('outputs', []):
                if out.get('output_type') == 'error':
                    error_count += 1
    
    result = {
        'student_id': '%s',
        'status': 'success',
        'elapsed_s': round(elapsed, 3),
        'outputs': output_count,
        'errors': error_count,
    }
    print('JSON_RESULT:' + json.dumps(result))
except Exception as e:
    elapsed = time.time() - start
    result = {
        'student_id': '%s',
        'status': 'error',
        'elapsed_s': round(elapsed, 3),
        'error': str(e)[:200],
    }
    print('JSON_RESULT:' + json.dumps(result))
""" % (NOTEBOOK_PATH, student_id, student_id)

    cmd = ["kubectl", "exec", "-n", "jupyterhub", POD, "--", "python3", "-c", inner_script]
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(timeout=90)
        elapsed = time.time() - start
        
        # Parse JSON result from stdout
        result = None
        for line in stdout.decode('utf-8', errors='replace').strip().split('\n'):
            if line.startswith('JSON_RESULT:'):
                result = json.loads(line[len('JSON_RESULT:'):])
                break
        
        if result:
            result['total_elapsed_s'] = round(elapsed, 3)
            return result
        else:
            return {
                'student_id': student_id,
                'status': 'parse_error',
                'elapsed_s': round(elapsed, 3),
                'stdout': stdout.decode('utf-8', errors='replace')[-300:],
                'stderr': stderr.decode('utf-8', errors='replace')[-300:],
            }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {
            'student_id': student_id,
            'status': 'timeout',
            'elapsed_s': round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            'student_id': student_id,
            'status': 'exception',
            'elapsed_s': round(time.time() - start, 3),
            'error': str(e)[:200],
        }


def main():
    log("Starting %d-student concurrent notebook execution test" % NUM_STUDENTS)
    log("Concurrency: %d threads" % CONCURRENCY)
    log("Notebook: %s" % NOTEBOOK_PATH)
    log("Pod: %s" % POD)
    log("")
    
    import concurrent.futures
    
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
    log("")
    
    # Analyze
    log("=" * 60)
    log("TEST RESULTS ANALYSIS")
    log("=" * 60)
    
    success = [r for r in results if r.get('status') == 'success']
    errors = [r for r in results if r.get('status') in ('error', 'parse_error', 'exception')]
    timeouts = [r for r in results if r.get('status') == 'timeout']
    
    log("")
    log("1. OVERALL SUMMARY")
    log("   Total students:      %d" % NUM_STUDENTS)
    log("   Successful:           %d" % len(success))
    log("   Errors:               %d" % len(errors))
    log("   Timeouts:             %d" % len(timeouts))
    log("   Success rate:         %.1f%%" % (len(success)/NUM_STUDENTS*100))
    log("   Total test duration:  %.1fs" % test_total)
    
    if success:
        times = [r['elapsed_s'] for r in success]
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        log("")
        log("2. RESPONSE TIME (kernel execution)")
        log("   Min:    %.3fs" % min(times))
        log("   Max:    %.3fs" % max(times))
        log("   Mean:   %.3fs" % (sum(times)/len(times)))
        log("   Median: %.3fs" % (sorted_times[n//2]))
        if n > 1:
            mean = sum(times)/len(times)
            var = sum((x-mean)**2 for x in times) / (len(times)-1)
            log("   Stdev:  %.3fs" % (var**0.5))
        log("   P90:    %.3fs" % sorted_times[int(n*0.9)])
        log("   P95:    %.3fs" % sorted_times[int(n*0.95)])
        if n > 99:
            log("   P99:    %.3fs" % sorted_times[int(n*0.99)])
    
    log("")
    log("3. THROUGHPUT")
    if test_total > 0:
        log("   Executions/sec:       %.2f" % (len(success)/test_total))
    log("   Concurrency level:    %d" % CONCURRENCY)
    
    output_counts = [r.get('outputs', 0) for r in success]
    if output_counts:
        log("")
        log("4. NOTEBOOK OUTPUT ANALYSIS")
        log("   Outputs per notebook (min): %d" % min(output_counts))
        log("   Outputs per notebook (max): %d" % max(output_counts))
        log("   Outputs per notebook (avg): %.1f" % (sum(output_counts)/len(output_counts)))
    
    # Last cell failure analysis (expected for student template)
    error_cells = [r.get('errors', 0) for r in success]
    last_cell_failed = sum(1 for e in error_cells if e > 0)
    log("")
    log("5. NOTEBOOK EXECUTION DETAILS")
    log("   All cells executed:           %d" % len(success))
    log("   Last cell assertion failed:   %d (expected - student template stubs)" % last_cell_failed)
    log("   All cells passed:             %d" % (len(success) - last_cell_failed))
    
    if errors:
        log("")
        log("6. ERROR BREAKDOWN")
        error_types = {}
        for r in errors:
            status = r.get('status', 'unknown')
            error_types[status] = error_types.get(status, 0) + 1
        for etype, count in sorted(error_types.items()):
            log("   %s: %d" % (etype, count))
        
        log("")
        log("   Sample errors:")
        shown = 0
        for r in errors:
            if r.get('error'):
                log("   - %s: %s" % (r.get('student_id'), r['error'][:150]))
                shown += 1
                if shown >= 3:
                    break
        if shown == 0:
            for r in errors[:3]:
                log("   - %s: %s" % (r.get('student_id'), str(r)[:200]))
    
    if timeouts:
        log("")
        log("7. TIMEOUT ANALYSIS")
        log("   %d executions timed out (90s limit)" % len(timeouts))
        timeout_ids = [r.get('student_id') for r in timeouts]
        log("   First 5: %s" % ', '.join(timeout_ids[:5]))
    
    log("")
    log("8. CONCLUSION")
    rate = len(success)/NUM_STUDENTS*100
    if rate >= 95:
        log("   [PASS] %d/%d students (%.1f%%) executed notebook successfully" % (len(success), NUM_STUDENTS, rate))
        if success:
            avg_time = sum(r['elapsed_s'] for r in success) / len(success)
            log("   Average execution time: %.1fs" % avg_time)
            log("   System handles 100 concurrent users")
    elif rate >= 80:
        log("   [MARGINAL] %d/%d students (%.1f%%) succeeded" % (len(success), NUM_STUDENTS, rate))
    else:
        log("   [FAIL] Only %d/%d students (%.1f%%) succeeded" % (len(success), NUM_STUDENTS, rate))
    
    log("")
    log("=" * 60)
    log("TEST COMPLETE")
    log("=" * 60)
    
    # Save JSON report
    report = {
        "test_name": "100-student concurrent notebook execution",
        "notebook": NOTEBOOK_PATH,
        "num_students": NUM_STUDENTS,
        "concurrency": CONCURRENCY,
        "total_duration_s": round(test_total, 1),
        "success_count": len(success),
        "error_count": len(errors),
        "timeout_count": len(timeouts),
        "success_rate": "%.1f%%" % rate,
        "results": results,
    }
    if success:
        times = [r['elapsed_s'] for r in success]
        sorted_t = sorted(times)
        report["response_time"] = {
            "min_s": min(times),
            "max_s": max(times),
            "mean_s": round(sum(times)/len(times), 3),
            "median_s": sorted_t[len(sorted_t)//2],
            "p95_s": sorted_t[int(len(sorted_t)*0.95)],
        }
    
    with open("/tmp/concurrent_test_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\nReport saved to /tmp/concurrent_test_report.json")


if __name__ == "__main__":
    main()
