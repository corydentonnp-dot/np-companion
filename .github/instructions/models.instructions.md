---
applyTo: "models/**/*.py"
---

# Model File Rules

## Required Patterns
- All models inherit from `db.Model` via SQLAlchemy.
- Every model with patient data MUST include `user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)` for tenant scoping.
- Clinical records use soft-delete: add `is_archived = db.Column(db.Boolean, default=False)` — never use `db.session.delete()`.
- All timestamps use `datetime.now(timezone.utc)` — never `datetime.utcnow()`.
- Export every new model from `models/__init__.py`.

## Naming
- Model class: PascalCase singular (e.g., `PatientRecord`, `BillingRule`).
- Table name: auto-generated snake_case (or explicit `__tablename__`).
- Foreign keys: `{related_table}_id` pattern.

## Relationships
- Use `db.relationship()` with `lazy='select'` (default) unless bulk loading is proven necessary.
- Always set `cascade='all, delete-orphan'` on parent side when children should not exist without parent.

## Validation
- Required fields use `nullable=False`.
- String fields with business constraints use `db.CheckConstraint` or validate in the route.
- Every new model needs at least one test in `tests/test_{model}.py`.

## SaaS Readiness
- Include `user_id` or `practice_id` (when added) on every model that stores user-specific data.
- Never create a model that assumes single-user operation without scoping.
- Avoid SQLite-specific column types or constraints.
