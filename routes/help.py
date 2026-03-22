"""
CareCompanion — Help & Feature Guide Routes
File: routes/help.py

User-facing help system with categorized feature documentation:
  GET /help                      — Feature guide (categorized list)
  GET /help/<feature_id>         — Individual feature help article
  GET /api/help/search           — Search help content (JSON)
"""

import json
import logging
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

help_bp = Blueprint('help', __name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def _load_help_data():
    """Load and return the help guide JSON data."""
    path = _DATA_DIR / 'help_guide.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@help_bp.route('/help')
@login_required
def help_index():
    """Feature guide — categorized list of all features with descriptions."""
    data = _load_help_data()
    categories = data.get('categories', [])
    features = data.get('features', [])

    # Group features by category
    grouped = {}
    for cat in categories:
        grouped[cat['id']] = {
            'info': cat,
            'features': []
        }

    for feat in features:
        cat_id = feat.get('category', '')
        if cat_id in grouped:
            # Filter admin-only features for non-admin users
            if feat.get('admin_only') and current_user.role != 'admin':
                continue
            grouped[cat_id]['features'].append(feat)

    return render_template(
        'help_guide.html',
        categories=categories,
        grouped=grouped,
        selected_feature=None
    )


@help_bp.route('/help/<feature_id>')
@login_required
def help_feature(feature_id):
    """Individual feature help article."""
    data = _load_help_data()
    categories = data.get('categories', [])
    features = data.get('features', [])

    # Find the requested feature
    feature = None
    for f in features:
        if f['id'] == feature_id:
            feature = f
            break

    if not feature:
        abort(404)

    # Check admin-only access
    if feature.get('admin_only') and current_user.role != 'admin':
        abort(404)

    # Build grouped data for sidebar navigation
    grouped = {}
    for cat in categories:
        grouped[cat['id']] = {
            'info': cat,
            'features': []
        }
    for feat in features:
        cat_id = feat.get('category', '')
        if cat_id in grouped:
            if feat.get('admin_only') and current_user.role != 'admin':
                continue
            grouped[cat_id]['features'].append(feat)

    return render_template(
        'help_guide.html',
        categories=categories,
        grouped=grouped,
        selected_feature=feature
    )


@help_bp.route('/api/help/search')
@login_required
def help_search():
    """Search help content — returns matching features as JSON."""
    q = request.args.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return jsonify([])

    data = _load_help_data()
    results = []

    for feat in data.get('features', []):
        if feat.get('admin_only') and current_user.role != 'admin':
            continue

        # Search across name, description, steps, and tips
        searchable = ' '.join([
            feat.get('name', ''),
            feat.get('description', ''),
            feat.get('how_it_works', ''),
            ' '.join(feat.get('steps', [])),
            ' '.join(feat.get('tips', []))
        ]).lower()

        if q in searchable:
            results.append({
                'id': feat['id'],
                'name': feat['name'],
                'category': feat.get('category', ''),
                'description': feat.get('description', '')[:150],
                'url': f"/help/{feat['id']}"
            })

    return jsonify(results[:20])


@help_bp.route('/api/help/items')
@login_required
def help_items():
    """Return a lightweight list of all help features for popover use.
    Returns: [{ id, name, description, category, url }]
    """
    data = _load_help_data()
    items = []
    for feat in data.get('features', []):
        if feat.get('admin_only') and current_user.role != 'admin':
            continue
        items.append({
            'id': feat['id'],
            'name': feat.get('name', feat['id']),
            'description': (feat.get('description') or '')[:200],
            'category': feat.get('category', ''),
            'url': f"/help/{feat['id']}"
        })
    return jsonify(items)
