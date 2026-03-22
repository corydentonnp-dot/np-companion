"""
CareCompanion — AI Assistant API Routes

File location: carecompanion/routes/ai_api.py

Provides:
  POST /api/ai/chat              — Proxy user message to their configured AI provider
  GET  /api/ai/hipaa-status      — Check if user has acknowledged HIPAA warning
  POST /api/ai/acknowledge-hipaa — Record HIPAA acknowledgment
"""

import json
import urllib.request
import urllib.error
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db

ai_api_bp = Blueprint('ai_api', __name__)


# ======================================================================
# POST /api/ai/chat — Send a message to the user's configured AI
# ======================================================================
@ai_api_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """Proxy a chat message to the user's chosen AI provider."""
    if not current_user.can_use_ai():
        return jsonify({'error': 'AI assistant not configured or not enabled.'}), 403

    if not current_user.ai_hipaa_acknowledged:
        return jsonify({'error': 'HIPAA acknowledgment required.'}), 403

    data = request.get_json(silent=True) or {}
    user_msg = (data.get('message') or '').strip()
    context = (data.get('context') or '').strip()
    history = data.get('history') or []

    if not user_msg:
        return jsonify({'error': 'Message is required.'}), 400

    api_key = current_user.get_ai_api_key()
    provider = current_user.ai_provider

    if not api_key or not provider:
        return jsonify({'error': 'AI provider or API key not configured.'}), 400

    # Build the messages array for the API call
    messages = _build_messages(context, history, user_msg)

    try:
        reply = _call_provider(provider, api_key, messages)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 502


# ======================================================================
# GET /api/ai/hipaa-status — Check HIPAA acknowledgment
# ======================================================================
@ai_api_bp.route('/api/ai/hipaa-status')
@login_required
def hipaa_status():
    return jsonify({'acknowledged': bool(current_user.ai_hipaa_acknowledged)})


# ======================================================================
# POST /api/ai/acknowledge-hipaa — Record acknowledgment
# ======================================================================
@ai_api_bp.route('/api/ai/acknowledge-hipaa', methods=['POST'])
@login_required
def acknowledge_hipaa():
    current_user.ai_hipaa_acknowledged = True
    db.session.commit()
    return jsonify({'ok': True})


# ======================================================================
# Internal helpers
# ======================================================================

def _build_messages(context, history, user_msg):
    """Build a standard messages array for the AI API call."""
    system_prompt = (
        "You are a helpful clinical reference assistant for a medical office. "
        "Answer questions clearly and concisely. If the user provides clinical "
        "context, use it to inform your answers. Do not fabricate medical "
        "information — if you are unsure, say so."
    )

    messages = [{'role': 'system', 'content': system_prompt}]

    if context:
        messages.append({
            'role': 'system',
            'content': f'Reference context from the patient chart:\n\n{context}'
        })

    # Add conversation history (already validated as list of dicts)
    for msg in history:
        role = msg.get('role', '')
        content = msg.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})

    # The current user message (append even if it's in history — ensures it's present)
    if not messages or messages[-1].get('content') != user_msg:
        messages.append({'role': 'user', 'content': user_msg})

    return messages


def _call_provider(provider, api_key, messages):
    """
    Call the appropriate AI provider API using urllib (no extra deps).
    Returns the assistant reply text.
    """
    if provider == 'openai':
        return _call_openai(api_key, messages)
    elif provider == 'anthropic':
        return _call_anthropic(api_key, messages)
    elif provider == 'xai':
        return _call_xai(api_key, messages)
    else:
        raise ValueError(f'Unsupported AI provider: {provider}')


def _call_openai(api_key, messages):
    """Call OpenAI Chat Completions API (gpt-4o-mini)."""
    url = 'https://api.openai.com/v1/chat/completions'
    payload = json.dumps({
        'model': 'gpt-4o-mini',
        'messages': messages,
        'max_tokens': 2048,
        'temperature': 0.3,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data['choices'][0]['message']['content'].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get('error', {}).get('message', body)
        except Exception:
            msg = body
        raise RuntimeError(f'OpenAI error ({e.code}): {msg}')


def _call_anthropic(api_key, messages):
    """Call Anthropic Messages API (claude-3-5-haiku)."""
    url = 'https://api.anthropic.com/v1/messages'

    # Anthropic uses a separate system param, not in messages
    system_parts = []
    chat_msgs = []
    for m in messages:
        if m['role'] == 'system':
            system_parts.append(m['content'])
        else:
            chat_msgs.append(m)

    # Anthropic requires alternating user/assistant; merge consecutive same-role
    merged = []
    for m in chat_msgs:
        if merged and merged[-1]['role'] == m['role']:
            merged[-1]['content'] += '\n\n' + m['content']
        else:
            merged.append(dict(m))

    payload = json.dumps({
        'model': 'claude-3-5-haiku-latest',
        'max_tokens': 2048,
        'system': '\n\n'.join(system_parts) if system_parts else '',
        'messages': merged,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data['content'][0]['text'].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get('error', {}).get('message', body)
        except Exception:
            msg = body
        raise RuntimeError(f'Anthropic error ({e.code}): {msg}')


def _call_xai(api_key, messages):
    """Call xAI (Grok) API — uses OpenAI-compatible endpoint."""
    url = 'https://api.x.ai/v1/chat/completions'
    payload = json.dumps({
        'model': 'grok-3-mini-fast',
        'messages': messages,
        'max_tokens': 2048,
        'temperature': 0.3,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data['choices'][0]['message']['content'].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get('error', {}).get('message', body)
        except Exception:
            msg = body
        raise RuntimeError(f'xAI error ({e.code}): {msg}')
