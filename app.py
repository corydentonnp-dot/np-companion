"""
CareCompanion — app.py runner

This file is intentionally a thin wrapper so that all imports use the
package-based app factory at app/__init__.py.
"""

from app import create_app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False),
    )
