/* ==========================================================
   error-handler.js — Centralized toast notification system
   Phase 10.1 — replaces alert() calls across the app
   ========================================================== */
(function () {
    'use strict';

    /* ---- Error map: known patterns → plain-language messages ---- */
    var ERROR_MAP = {
        'Failed to fetch':       'Could not reach the server. Check your connection and try again.',
        'NetworkError':          'Network error — the server may be restarting. Try again in a moment.',
        'Internal Server Error': 'Something went wrong on the server. Try again or contact support.',
        '500':                   'Server error — please try again.',
        '401':                   'Your session may have expired. Please log in again.',
        '403':                   'You don\'t have permission for that action.',
        '404':                   'The requested resource was not found.',
        'PDMP connection':       'Could not connect to PDMP. Check your credentials in Settings.',
        'timeout':               'The request timed out. Try again.'
    };

    function mapError(technicalMsg) {
        if (!technicalMsg) return 'Something went wrong. Please try again.';
        var msg = String(technicalMsg);
        var keys = Object.keys(ERROR_MAP);
        for (var i = 0; i < keys.length; i++) {
            if (msg.indexOf(keys[i]) !== -1) return ERROR_MAP[keys[i]];
        }
        return msg;
    }

    /* ---- Toast container (created once) ---- */
    var container;
    function getContainer() {
        if (container) return container;
        container = document.createElement('div');
        container.id = 'toast-container';
        container.setAttribute('role', 'status');
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
        return container;
    }

    /* ---- Icon SVGs ---- */
    var ICONS = {
        success: '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
        error:   '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
        warning: '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
        info:    '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
    };

    /**
     * Show a toast notification.
     * @param {string} message  - Plain-language message to display
     * @param {string} type     - 'success' | 'error' | 'warning' | 'info' (default: 'info')
     * @param {object} opts     - { duration: ms (default 6000, 0=sticky), action: {label, fn} }
     */
    function showToast(message, type, opts) {
        type = type || 'info';
        opts = opts || {};
        var duration = opts.duration !== undefined ? opts.duration : (type === 'error' ? 8000 : 6000);

        var toast = document.createElement('div');
        toast.className = 'toast toast--' + type;

        var icon = ICONS[type] || ICONS.info;
        toast.innerHTML =
            '<span class="toast-icon">' + icon + '</span>' +
            '<span class="toast-msg"></span>' +
            '<button class="toast-close" aria-label="Dismiss">&times;</button>';

        toast.querySelector('.toast-msg').textContent = message;

        /* Close button */
        toast.querySelector('.toast-close').addEventListener('click', function () {
            dismiss(toast);
        });

        /* Optional action button (e.g. "Try again") */
        if (opts.action && opts.action.label) {
            var btn = document.createElement('button');
            btn.className = 'toast-action';
            btn.textContent = opts.action.label;
            btn.addEventListener('click', function () {
                if (typeof opts.action.fn === 'function') opts.action.fn();
                dismiss(toast);
            });
            toast.querySelector('.toast-msg').after(btn);
        }

        getContainer().appendChild(toast);

        /* Trigger entrance animation */
        requestAnimationFrame(function () { toast.classList.add('toast--visible'); });

        /* Auto-dismiss */
        if (duration > 0) {
            setTimeout(function () { dismiss(toast); }, duration);
        }

        return toast;
    }

    function dismiss(toast) {
        if (!toast || !toast.parentNode) return;
        toast.classList.remove('toast--visible');
        toast.classList.add('toast--exit');
        setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }

    /**
     * Show an error toast. Maps technical messages to plain-language via ERROR_MAP.
     */
    function showError(technicalMsg, opts) {
        return showToast(mapError(technicalMsg), 'error', opts);
    }

    function showSuccess(message, opts) {
        return showToast(message, 'success', opts);
    }

    function showWarning(message, opts) {
        return showToast(message, 'warning', opts);
    }

    function showInfo(message, opts) {
        return showToast(message, 'info', opts);
    }

    /* Expose globally */
    window.showToast   = showToast;
    window.showError   = showError;
    window.showSuccess = showSuccess;
    window.showWarning = showWarning;
    window.showInfo    = showInfo;
})();

/**
 * fetchWithLoading — wraps fetch() with a loading state on a button or element.
 * Adds .btn--loading class and disables the trigger, then restores on completion.
 *
 * Usage:
 *   fetchWithLoading('/api/endpoint', {method:'POST', body:...}, myButton)
 *     .then(function(data) { ... })
 *     .catch(function(err) { showError(err.message); });
 *
 * @param {string} url - The fetch URL
 * @param {object} opts - Fetch options (method, headers, body, etc.)
 * @param {HTMLElement} [trigger] - Button or element to show loading state on
 * @returns {Promise} - Resolves with parsed JSON, rejects on error
 */
window.fetchWithLoading = function (url, opts, trigger) {
    if (trigger) {
        trigger.classList.add('btn--loading');
        trigger.disabled = true;
    }
    return fetch(url, opts)
        .then(function (res) {
            if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
            return res.json();
        })
        .finally(function () {
            if (trigger) {
                trigger.classList.remove('btn--loading');
                trigger.disabled = false;
            }
        });
};
