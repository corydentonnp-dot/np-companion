"""
CareCompanion — Benchmark Models

File location: carecompanion/models/benchmark.py

Stores benchmark run history and per-patient results so the admin
can track correctness and performance trends over time.
"""

from datetime import datetime, timezone
from models import db


class BenchmarkRun(db.Model):
    """A single execution of the benchmark suite (or a subset)."""
    __tablename__ = 'benchmark_run'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Which engines were tested: 'all', 'billing', 'caregap', 'monitoring'
    engine_filter = db.Column(db.String(50), nullable=False, default='all')

    # Which patient was tested: 'all' or a specific patient_id
    patient_filter = db.Column(db.String(100), nullable=False, default='all')

    # Aggregate results
    total_tests = db.Column(db.Integer, nullable=False, default=0)
    passed_tests = db.Column(db.Integer, nullable=False, default=0)
    failed_tests = db.Column(db.Integer, nullable=False, default=0)

    # Timing (milliseconds)
    total_duration_ms = db.Column(db.Float, nullable=False, default=0.0)

    started_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    finished_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    results = db.relationship('BenchmarkResult', backref='run', lazy='dynamic',
                              cascade='all, delete-orphan')
    user = db.relationship('User', backref='benchmark_runs', lazy=True)

    def pass_rate(self):
        if self.total_tests == 0:
            return 0.0
        return round(self.passed_tests / self.total_tests * 100, 1)

    def __repr__(self):
        return (
            f'<BenchmarkRun {self.id} {self.engine_filter} '
            f'{self.passed_tests}/{self.total_tests}>'
        )


class BenchmarkResult(db.Model):
    """Individual test result within a benchmark run."""
    __tablename__ = 'benchmark_result'

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('benchmark_run.id'), nullable=False, index=True)

    # Test identification
    patient_id = db.Column(db.String(100), nullable=False)
    engine = db.Column(db.String(50), nullable=False)  # billing | caregap | monitoring
    test_name = db.Column(db.String(200), nullable=False)

    # Result
    passed = db.Column(db.Boolean, nullable=False)
    explanation = db.Column(db.Text, default='')

    # Performance (milliseconds)
    duration_ms = db.Column(db.Float, nullable=False, default=0.0)

    # What the engine actually returned (JSON summary for debugging)
    actual_summary = db.Column(db.Text, default='{}')

    tested_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.Index('ix_benchmark_result_patient_engine', 'patient_id', 'engine'),
    )

    def __repr__(self):
        result = 'PASS' if self.passed else 'FAIL'
        return (
            f'<BenchmarkResult {self.id} {self.patient_id}/{self.engine} '
            f'{self.test_name} {result}>'
        )
