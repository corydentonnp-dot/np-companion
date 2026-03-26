"""
CareCompanion — Benchmark Test Suite (CLI)

Runs the full benchmark suite or a subset via command-line flags.

Usage:
    venv\\Scripts\\python.exe tests/test_benchmarks.py
    venv\\Scripts\\python.exe tests/test_benchmarks.py --engine billing
    venv\\Scripts\\python.exe tests/test_benchmarks.py --patient BM_MEDICARE_68F
    venv\\Scripts\\python.exe tests/test_benchmarks.py --save
    venv\\Scripts\\python.exe tests/test_benchmarks.py --engine caregap --patient BM_TOBACCO_55M --save

Flags:
    --engine   billing | caregap | monitoring | all (default: all)
    --patient  patient_id from benchmark_fixtures or 'all' (default: all)
    --save     Persist results to BenchmarkRun/BenchmarkResult tables
    --perf     Include performance threshold checks
"""

import argparse
import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


def _parse_args():
    parser = argparse.ArgumentParser(description='CareCompanion Benchmark Suite')
    parser.add_argument('--engine', default='all',
                        choices=['all', 'billing', 'caregap', 'monitoring'],
                        help='Engine to benchmark (default: all)')
    parser.add_argument('--patient', default='all',
                        help='Patient ID from fixtures or "all" (default: all)')
    parser.add_argument('--save', action='store_true',
                        help='Persist results to database')
    parser.add_argument('--perf', action='store_true',
                        help='Include performance threshold checks')
    return parser.parse_args()


def _check_performance(run_data, perf_results):
    """Add performance threshold test results."""
    import config

    thresholds = {
        'billing': config.BENCHMARK_BILLING_MAX_MS,
        'caregap': config.BENCHMARK_CAREGAP_MAX_MS,
        'monitoring': config.BENCHMARK_MONITORING_MAX_MS,
    }

    # Check per-engine timing on individual tests
    for r in run_data['results']:
        if r['duration_ms'] > 0:
            engine = r['engine']
            max_ms = thresholds.get(engine, 1000)
            passed = r['duration_ms'] <= max_ms
            perf_results.append({
                'patient_id': r['patient_id'],
                'engine': engine,
                'test_name': f'perf_{r["test_name"]}',
                'passed': passed,
                'explanation': (
                    f'{r["duration_ms"]:.1f}ms '
                    f'{"<=" if passed else ">"} {max_ms}ms threshold'
                ),
                'duration_ms': r['duration_ms'],
                'actual_summary': r['actual_summary'],
                'tested_at': datetime.now(timezone.utc).isoformat(),
            })

    # Check full suite timing
    suite_max = config.BENCHMARK_FULL_SUITE_MAX_MS
    suite_passed = run_data['duration_ms'] <= suite_max
    perf_results.append({
        'patient_id': 'SUITE',
        'engine': 'all',
        'test_name': 'perf_full_suite_duration',
        'passed': suite_passed,
        'explanation': (
            f'{run_data["duration_ms"]:.1f}ms '
            f'{"<=" if suite_passed else ">"} {suite_max}ms threshold'
        ),
        'duration_ms': run_data['duration_ms'],
        'actual_summary': '{}',
        'tested_at': datetime.now(timezone.utc).isoformat(),
    })


def _save_results(app, run_data, user_id=1):
    """Persist run + results to the database."""
    with app.app_context():
        from models import db
        from models.benchmark import BenchmarkRun, BenchmarkResult

        run = BenchmarkRun(
            user_id=user_id,
            engine_filter=run_data['engine_filter'],
            patient_filter=run_data['patient_filter'],
            total_tests=run_data['total'],
            passed_tests=run_data['passed'],
            failed_tests=run_data['failed'],
            total_duration_ms=run_data['duration_ms'],
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.session.add(run)
        db.session.flush()  # Get run.id

        for r in run_data['results']:
            result = BenchmarkResult(
                run_id=run.id,
                patient_id=r['patient_id'],
                engine=r['engine'],
                test_name=r['test_name'],
                passed=r['passed'],
                explanation=r['explanation'],
                duration_ms=r['duration_ms'],
                actual_summary=r['actual_summary'],
            )
            db.session.add(result)

        db.session.commit()
        print(f"\n  Results saved to database (run_id={run.id})")


def _print_results(run_data):
    """Print formatted results to terminal."""
    print("\n" + "=" * 70)
    print("  CARECOMPANION ENGINE BENCHMARK RESULTS")
    print("=" * 70)
    print(f"  Engine:   {run_data['engine_filter']}")
    print(f"  Patients: {run_data['patient_filter']}")
    print(f"  Duration: {run_data['duration_ms']:.1f}ms")
    print("-" * 70)

    # Group results by patient
    by_patient = {}
    for r in run_data['results']:
        key = r['patient_id']
        if key not in by_patient:
            by_patient[key] = []
        by_patient[key].append(r)

    for pid, tests in sorted(by_patient.items()):
        p_passed = sum(1 for t in tests if t['passed'])
        p_total = len(tests)
        status = 'PASS' if p_passed == p_total else 'FAIL'
        print(f"\n  [{status}] {pid} ({p_passed}/{p_total})")
        for t in tests:
            icon = '  +' if t['passed'] else '  X'
            timing = f" ({t['duration_ms']:.1f}ms)" if t['duration_ms'] > 0 else ""
            print(f"    {icon} {t['engine']}/{t['test_name']}{timing}")
            if not t['passed']:
                print(f"        {t['explanation']}")

    print("\n" + "-" * 70)
    print(f"  TOTAL: {run_data['passed']}/{run_data['total']} passed "
          f"({run_data['failed']} failed) in {run_data['duration_ms']:.1f}ms")
    print("=" * 70 + "\n")


def main():
    args = _parse_args()
    app = _get_app()

    from tests.benchmark_engine import BenchmarkRunner
    runner = BenchmarkRunner(app)

    print(f"\nRunning benchmarks: engine={args.engine}, patient={args.patient}")
    run_data = runner.run(engine=args.engine, patient_id=args.patient)

    # Add performance checks if requested
    if args.perf:
        perf_results = []
        _check_performance(run_data, perf_results)
        run_data['results'].extend(perf_results)
        run_data['total'] += len(perf_results)
        p = sum(1 for r in perf_results if r['passed'])
        run_data['passed'] += p
        run_data['failed'] += len(perf_results) - p

    _print_results(run_data)

    if args.save:
        _save_results(app, run_data)

    return 0 if run_data['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
