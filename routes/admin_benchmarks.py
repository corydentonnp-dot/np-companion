"""
CareCompanion — Admin Benchmarks Route

File location: carecompanion/routes/admin_benchmarks.py

Admin-only pages for running and viewing engine benchmark tests.
"""

import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import require_role  # B1 — moved from routes.auth

admin_benchmarks_bp = Blueprint('admin_benchmarks', __name__)


@admin_benchmarks_bp.route('/admin/benchmarks')
@login_required
@require_role('admin')
def index():
    """Benchmark dashboard with run history."""
    from models import db
    from models.benchmark import BenchmarkRun

    runs = (BenchmarkRun.query
            .filter_by(user_id=current_user.id)
            .order_by(BenchmarkRun.started_at.desc())
            .limit(20)
            .all())

    return render_template('admin_benchmarks.html', runs=runs)


@admin_benchmarks_bp.route('/admin/benchmarks/run', methods=['POST'])
@login_required
@require_role('admin')
def run_benchmark():
    """Execute a benchmark run and return results as JSON."""
    from flask import current_app
    from models import db
    from models.benchmark import BenchmarkRun, BenchmarkResult
    from tests.benchmark_engine import BenchmarkRunner

    engine_filter = request.form.get('engine', 'all')
    patient_filter = request.form.get('patient', 'all')
    include_perf = request.form.get('perf', 'false') == 'true'

    try:
        runner = BenchmarkRunner(current_app._get_current_object())
        run_data = runner.run(engine=engine_filter, patient_id=patient_filter)

        # Add performance checks if requested
        if include_perf:
            import config
            thresholds = {
                'billing': config.BENCHMARK_BILLING_MAX_MS,
                'caregap': config.BENCHMARK_CAREGAP_MAX_MS,
                'monitoring': config.BENCHMARK_MONITORING_MAX_MS,
            }
            perf_results = []
            for r in run_data['results']:
                if r['duration_ms'] > 0:
                    max_ms = thresholds.get(r['engine'], 1000)
                    passed = r['duration_ms'] <= max_ms
                    perf_results.append({
                        'patient_id': r['patient_id'],
                        'engine': r['engine'],
                        'test_name': f'perf_{r["test_name"]}',
                        'passed': passed,
                        'explanation': f'{r["duration_ms"]:.1f}ms {"<=" if passed else ">"} {max_ms}ms',
                        'duration_ms': r['duration_ms'],
                        'actual_summary': r['actual_summary'],
                        'tested_at': datetime.now(timezone.utc).isoformat(),
                    })
            run_data['results'].extend(perf_results)
            run_data['total'] += len(perf_results)
            p = sum(1 for r in perf_results if r['passed'])
            run_data['passed'] += p
            run_data['failed'] += len(perf_results) - p

        # Persist to database
        benchmark_run = BenchmarkRun(
            user_id=current_user.id,
            engine_filter=engine_filter,
            patient_filter=patient_filter,
            total_tests=run_data['total'],
            passed_tests=run_data['passed'],
            failed_tests=run_data['failed'],
            total_duration_ms=run_data['duration_ms'],
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.session.add(benchmark_run)
        db.session.flush()

        for r in run_data['results']:
            result = BenchmarkResult(
                run_id=benchmark_run.id,
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

        return jsonify({
            'success': True,
            'data': {
                'run_id': benchmark_run.id,
                'total': run_data['total'],
                'passed': run_data['passed'],
                'failed': run_data['failed'],
                'duration_ms': run_data['duration_ms'],
                'pass_rate': benchmark_run.pass_rate(),
                'results': run_data['results'],
            },
            'error': None,
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in admin_benchmarks.run_benchmark: {str(e)}")
        return jsonify({'success': False, 'data': None, 'error': 'Benchmark run failed'}), 500


@admin_benchmarks_bp.route('/admin/benchmarks/run/<int:run_id>')
@login_required
@require_role('admin')
def run_detail(run_id):
    """Get details for a specific benchmark run."""
    from models.benchmark import BenchmarkRun, BenchmarkResult

    run = BenchmarkRun.query.filter_by(id=run_id, user_id=current_user.id).first_or_404()
    results = BenchmarkResult.query.filter_by(run_id=run.id).all()

    return jsonify({
        'success': True,
        'data': {
            'run_id': run.id,
            'engine_filter': run.engine_filter,
            'patient_filter': run.patient_filter,
            'total': run.total_tests,
            'passed': run.passed_tests,
            'failed': run.failed_tests,
            'duration_ms': run.total_duration_ms,
            'pass_rate': run.pass_rate(),
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'results': [{
                'patient_id': r.patient_id,
                'engine': r.engine,
                'test_name': r.test_name,
                'passed': r.passed,
                'explanation': r.explanation,
                'duration_ms': r.duration_ms,
                'actual_summary': r.actual_summary,
            } for r in results],
        },
        'error': None,
    })


@admin_benchmarks_bp.route('/admin/benchmarks/patients')
@login_required
@require_role('admin')
def list_patients():
    """Return the list of available benchmark patients."""
    from tests.benchmark_fixtures import PATIENTS

    patients = []
    for pid, pdata in PATIENTS.items():
        patients.append({
            'id': pid,
            'age': pdata.get('patient_age', ''),
            'sex': pdata.get('sex', ''),
            'insurer': pdata.get('insurer_type', ''),
            'conditions': len(pdata.get('diagnoses', [])),
            'medications': len(pdata.get('medications', [])),
        })

    return jsonify({'success': True, 'data': patients, 'error': None})
