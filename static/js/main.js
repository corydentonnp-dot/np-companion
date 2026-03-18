/**
 * NP Companion — Main JavaScript
 * File location: np-companion/static/js/main.js
 *
 * Handles all shared client-side behaviour:
 *   1. Dark mode toggle (persists to localStorage + server)
 *   2. Real-time clock in the header
 *   3. Auto-lock screen after 5 minutes of inactivity
 *   4. PIN entry to unlock (3 failures → full logout)
 *   5. Notification bell polling (/api/notifications every 60 s)
 *   6. Mobile sidebar toggle
 *   7. Flash message dismissal
 */

document.addEventListener('DOMContentLoaded', function () {
    initDarkMode();
    initClock();
    initAutoLock();
    initSidebar();
    initNotifications();
    initFlashMessages();
    initAgentStatus();
    initAuthStatus();
    initSetupStatus();
    initZoom();
    initNavKeys();
    initUserPopover();
    initContextMenu();
    initAIPanel();
});


/* ==========================================================
   1.  DARK MODE TOGGLE
   ========================================================== */

function initDarkMode() {
    // Apply saved theme / font / accent immediately (no flash of wrong colors)
    var saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateDarkModeIcon(saved);

    var savedFont = localStorage.getItem('theme_font');
    if (savedFont) document.documentElement.setAttribute('data-font', savedFont);

    var savedAccent = localStorage.getItem('theme_accent');
    if (savedAccent) document.documentElement.setAttribute('data-accent', savedAccent);

    // The header toggle now cycles: current theme → dark → light
    var toggle = document.getElementById('dark-mode-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme');
        // Simple toggle: if already dark, go to light; otherwise go to dark
        var next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateDarkModeIcon(next);

        fetch('/api/settings/theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: next })
        }).catch(function () { });
    });
}

/**
 * Show a sun icon in dark mode (click to go light)
 * and a moon icon in light mode (click to go dark).
 */
function updateDarkModeIcon(theme) {
    var el = document.getElementById('dark-mode-icon');
    if (!el) return;
    if (theme === 'dark') {
        // Sun SVG
        el.innerHTML =
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" ' +
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
            'stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="5"/>' +
            '<line x1="12" y1="1" x2="12" y2="3"/>' +
            '<line x1="12" y1="21" x2="12" y2="23"/>' +
            '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>' +
            '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>' +
            '<line x1="1" y1="12" x2="3" y2="12"/>' +
            '<line x1="21" y1="12" x2="23" y2="12"/>' +
            '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>' +
            '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>' +
            '</svg>';
    } else {
        // Moon SVG
        el.innerHTML =
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" ' +
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
            'stroke-linejoin="round">' +
            '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>' +
            '</svg>';
    }
}


/* ==========================================================
   2.  REAL-TIME CLOCK
   ========================================================== */

function initClock() {
    var clockEl = document.getElementById('header-clock');
    if (!clockEl) return;

    function tick() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        var ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        var display = hours + ':' + (minutes < 10 ? '0' : '') + minutes + ' ' + ampm;
        clockEl.textContent = display;
    }
    tick();                     // show immediately
    setInterval(tick, 30000);   // update every 30 seconds
}


/* ==========================================================
   3.  AUTO-LOCK SCREEN (5-minute inactivity timeout)
   ========================================================== */

var lockTimer = null;
var failedPinAttempts = 0;

// Default 5 minutes; overridable per user via data-lock-timeout on <body>
var LOCK_TIMEOUT_MS = (function () {
    var attr = document.body && document.body.getAttribute('data-lock-timeout');
    var minutes = parseInt(attr, 10);
    return (minutes > 0 ? minutes : 5) * 60 * 1000;
})();

function initAutoLock() {
    // Don't activate on the login page (no user to lock)
    if (document.body.getAttribute('data-page') === 'login') return;
    // Don't activate when there is no lock overlay in the DOM
    if (!document.getElementById('lock-overlay')) return;

    resetLockTimer();

    // Any user interaction resets the countdown
    var events = ['mousemove', 'mousedown', 'click', 'keypress', 'touchstart', 'scroll'];
    events.forEach(function (name) {
        document.addEventListener(name, resetLockTimer, { passive: true });
    });

    // Handle PIN form submission
    var pinForm = document.getElementById('pin-form');
    if (pinForm) {
        pinForm.addEventListener('submit', handlePinSubmit);
    }
}

function resetLockTimer() {
    if (lockTimer) clearTimeout(lockTimer);
    lockTimer = setTimeout(showLockScreen, LOCK_TIMEOUT_MS);
}

function showLockScreen() {
    var overlay = document.getElementById('lock-overlay');
    if (!overlay) return;
    overlay.classList.add('visible');
    var input = document.getElementById('pin-input');
    if (input) { input.value = ''; input.focus(); }
    var err = document.getElementById('pin-error');
    if (err) err.textContent = '';
}

function hideLockScreen() {
    var overlay = document.getElementById('lock-overlay');
    if (overlay) overlay.classList.remove('visible');
    failedPinAttempts = 0;
    resetLockTimer();
}

function handlePinSubmit(e) {
    e.preventDefault();
    var input = document.getElementById('pin-input');
    var errEl = document.getElementById('pin-error');
    var pin = input ? input.value : '';

    // Basic validation — must be exactly 4 digits
    if (!/^\d{4}$/.test(pin)) {
        if (errEl) errEl.textContent = 'Enter a 4-digit PIN';
        return;
    }

    fetch('/api/verify-pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin: pin })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.success) {
            hideLockScreen();
        } else {
            failedPinAttempts++;
            if (errEl) {
                errEl.textContent =
                    'Incorrect PIN (' + failedPinAttempts + ' of 3 attempts)';
            }
            if (input) { input.value = ''; input.focus(); }

            // After 3 failures, force a full login
            if (failedPinAttempts >= 3) {
                window.location.href = '/logout';
            }
        }
    })
    .catch(function () {
        // If the endpoint doesn't exist yet, just unlock so
        // development isn't blocked by the lock screen.
        hideLockScreen();
    });
}


/* ==========================================================
   4.  MOBILE SIDEBAR TOGGLE
   ========================================================== */

function initSidebar() {
    var toggleBtn = document.getElementById('sidebar-toggle');
    var sidebar   = document.getElementById('sidebar');
    if (!toggleBtn || !sidebar) return;

    // Create a backdrop element for mobile overlay
    var backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(backdrop);

    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('open');
        backdrop.classList.toggle('visible');
    });

    // Tapping the backdrop closes the sidebar
    backdrop.addEventListener('click', function () {
        sidebar.classList.remove('open');
        backdrop.classList.remove('visible');
    });
}


/* ==========================================================
   5.  NOTIFICATION BELL — polls every 60 seconds
   ========================================================== */

function initNotifications() {
    var badge = document.getElementById('notification-count');
    var bell = document.getElementById('notification-bell');
    var dropdown = document.getElementById('notification-dropdown');
    var listEl = document.getElementById('notification-list');
    if (!badge) return;

    function poll() {
        fetch('/api/notifications')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var count = data.unread_count || 0;
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(function () {
                badge.style.display = 'none';
            });
    }

    poll();
    setInterval(poll, 60000);

    if (bell && dropdown && listEl) {
        bell.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = dropdown.style.display !== 'none';
            if (isOpen) {
                dropdown.style.display = 'none';
                return;
            }
            dropdown.style.display = 'block';
            fetch('/api/notifications')
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    var items = data.notifications || [];
                    if (items.length === 0) {
                        listEl.innerHTML = '<p class="notif-dd-empty">No new notifications</p>';
                    } else {
                        var html = '<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 14px;border-bottom:1px solid var(--border-color,#eee);">' +
                            '<strong style="font-size:13px;">Notifications</strong>' +
                            '<button class="btn btn-sm btn-outline" onclick="markAllNotificationsRead()" style="font-size:11px;padding:2px 8px;">Mark all read</button></div>';
                        items.forEach(function (n) {
                            html += '<div class="notif-dd-item' + (n.is_read ? '' : ' notif-dd-unread') + '" data-notif-id="' + (n.id || '') + '">' +
                                '<div style="flex:1;">' +
                                '<span class="notif-dd-text">' + escapeHtml(n.message || n.text || '') + '</span>' +
                                (n.sender ? '<div style="font-size:11px;color:var(--text-muted);">From: ' + escapeHtml(n.sender) + '</div>' : '') +
                                '</div>' +
                                '<span class="notif-dd-time">' + escapeHtml(n.time || '') + '</span>' +
                                '</div>';
                        });
                        listEl.innerHTML = html;
                        // Click on an unread notification to mark it read
                        listEl.querySelectorAll('.notif-dd-item[data-notif-id]').forEach(function(item) {
                            item.addEventListener('click', function() {
                                var nid = item.getAttribute('data-notif-id');
                                if (nid) {
                                    fetch('/api/notifications/' + nid + '/read', { method: 'POST' })
                                        .then(function() {
                                            item.classList.remove('notif-dd-unread');
                                            poll();
                                        });
                                }
                            });
                        });
                    }
                })
                .catch(function () {
                    listEl.innerHTML = '<p class="notif-dd-empty">Unable to load notifications</p>';
                });
        });

        document.addEventListener('click', function () {
            dropdown.style.display = 'none';
        });
    }
}

function markAllNotificationsRead() {
    fetch('/api/notifications/read-all', { method: 'POST' })
        .then(function() {
            var badge = document.getElementById('notification-count');
            if (badge) badge.style.display = 'none';
            var items = document.querySelectorAll('.notif-dd-unread');
            items.forEach(function(i) { i.classList.remove('notif-dd-unread'); });
        });
}

function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}


/* ==========================================================
   6.  FLASH MESSAGE DISMISSAL
   ========================================================== */

function initFlashMessages() {
    document.querySelectorAll('.flash-close').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var flash = btn.closest('.flash');
            if (flash) flash.remove();
        });
    });
}


/* ==========================================================
   7.  AGENT HEALTH STATUS DOT — polls every 15 seconds
   ========================================================== */

function initAgentStatus() {
    var dot = document.getElementById('agent-status');
    if (!dot) return;

    function poll() {
        fetch('/api/agent-status')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Remove all status classes
                dot.className = 'status-dot';

                if (data.status === 'green') {
                    dot.classList.add('status-dot--green');
                    dot.title = 'Agent: running (heartbeat ' + data.age_seconds + 's ago)';
                } else if (data.status === 'yellow') {
                    dot.classList.add('status-dot--yellow');
                    dot.title = 'Agent: stale (heartbeat ' + data.age_seconds + 's ago)';
                } else if (data.status === 'red') {
                    dot.classList.add('status-dot--red');
                    dot.title = 'Agent: not responding (heartbeat ' + data.age_seconds + 's ago)';
                } else {
                    dot.classList.add('status-dot--unknown');
                    dot.title = 'Agent: offline (no heartbeat found)';
                }
            })
            .catch(function () {
                dot.className = 'status-dot status-dot--unknown';
                dot.title = 'Agent: unable to check status';
            });
    }

    poll();                     // first check immediately
    setInterval(poll, 15000);   // then every 15 seconds
}


/* ==========================================================
   8.  NETPRACTICE AUTH STATUS DOT — polls every 30 seconds
   ========================================================== */

function initAuthStatus() {
    var dot = document.getElementById('auth-status');
    if (!dot) return;

    function poll() {
        fetch('/api/auth-status')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Remove all status classes
                dot.className = 'status-dot';

                if (!data.netpractice_configured) {
                    dot.classList.add('status-dot--unknown');
                    dot.title = 'NetPractice: not configured';
                } else if (data.status === 'green') {
                    dot.classList.add('status-dot--green');
                    dot.title = 'NetPractice: session valid';
                } else if (data.status === 'red' || data.needs_reauth) {
                    dot.classList.add('status-dot--red');
                    dot.title = 'NetPractice: session expired — re-auth needed';
                } else {
                    dot.classList.add('status-dot--unknown');
                    dot.title = 'NetPractice: status unknown';
                }
            })
            .catch(function () {
                dot.className = 'status-dot status-dot--unknown';
                dot.title = 'NetPractice: unable to check status';
            });
    }

    poll();                     // first check immediately
    setInterval(poll, 30000);   // then every 30 seconds
}


/* ==========================================================
   9.  SETUP STATUS — shows/hides setup button in header
   ========================================================== */

function initSetupStatus() {
    var btn = document.getElementById('setup-btn');
    var badge = document.getElementById('setup-count');
    if (!btn || !badge) return;

    function poll() {
        fetch('/api/setup-status')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var count = data.incomplete_count || 0;
                if (count > 0) {
                    badge.textContent = count;
                    btn.style.display = 'inline-flex';
                    btn.title = count + ' setup task' + (count !== 1 ? 's' : '') + ' remaining';
                } else {
                    btn.style.display = 'none';
                }
            })
            .catch(function () {
                // Endpoint may not exist yet — hide button quietly
                btn.style.display = 'none';
            });
    }

    poll();                     // first check immediately
    setInterval(poll, 60000);   // then every 60 seconds
}


/* ==========================================================
   10.  ZOOM — Ctrl+Plus / Ctrl+Minus / Ctrl+0
   ========================================================== */

function initZoom() {
    var zoomLevel = parseFloat(localStorage.getItem('zoomLevel') || '1');
    applyZoom(zoomLevel);

    document.addEventListener('keydown', function (e) {
        if (!e.ctrlKey) return;

        // Ctrl + = / Ctrl + +  (zoom in)
        if (e.key === '=' || e.key === '+') {
            e.preventDefault();
            zoomLevel = Math.min(zoomLevel + 0.1, 2.0);
            applyZoom(zoomLevel);
            localStorage.setItem('zoomLevel', String(zoomLevel));
        }
        // Ctrl + -  (zoom out)
        else if (e.key === '-') {
            e.preventDefault();
            zoomLevel = Math.max(zoomLevel - 0.1, 0.5);
            applyZoom(zoomLevel);
            localStorage.setItem('zoomLevel', String(zoomLevel));
        }
        // Ctrl + 0  (reset)
        else if (e.key === '0') {
            e.preventDefault();
            zoomLevel = 1.0;
            applyZoom(zoomLevel);
            localStorage.setItem('zoomLevel', String(zoomLevel));
        }
    });
}

function applyZoom(level) {
    document.documentElement.style.zoom = level;
}


/* ==========================================================
   11.  NAV KEYS — Alt+Left / Alt+Right
   ========================================================== */

function initNavKeys() {
    document.addEventListener('keydown', function (e) {
        if (!e.altKey) return;
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            history.back();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            history.forward();
        }
    });
}


/* ==========================================================
   12.  USER POPOVER — hover username to see info
   ========================================================== */

function initUserPopover() {
    var wrapper = document.getElementById('user-wrapper');
    var popover = document.getElementById('user-popover');
    if (!wrapper || !popover) return;

    var hideTimer = null;

    wrapper.addEventListener('mouseenter', function () {
        if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
        popover.style.display = 'block';
    });

    wrapper.addEventListener('mouseleave', function () {
        hideTimer = setTimeout(function () {
            popover.style.display = 'none';
        }, 200);
    });
}


/* ==========================================================
   13.  CUSTOM RIGHT-CLICK CONTEXT MENU
   ========================================================== */

function initContextMenu() {
    var menu = document.getElementById('ctx-menu');
    if (!menu) return;

    // Track the link / widget element that was right-clicked
    var _ctxLinkEl = null;
    var _ctxWidgetEl = null;

    // Suppress default context menu and show ours
    document.addEventListener('contextmenu', function (e) {
        // Allow default on actual input/textarea for browser spell-check
        var tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;

        e.preventDefault();
        var sel = (window.getSelection().toString() || '').trim();

        // Detect if right-clicked on a link
        _ctxLinkEl = e.target.closest('a[href]');

        // Detect if right-clicked on a free-form widget
        _ctxWidgetEl = e.target.closest('.fw-widget, .dash-widget');
        var inFreeMode = _ctxWidgetEl && _ctxWidgetEl.closest('.fw-free-mode');
        var widgetItems = menu.querySelectorAll('.ctx-widget-item');
        var widgetSep = menu.querySelector('.ctx-widget-sep');
        for (var wi = 0; wi < widgetItems.length; wi++) {
            widgetItems[wi].style.display = inFreeMode ? '' : 'none';
        }
        if (widgetSep) widgetSep.style.display = inFreeMode ? '' : 'none';

        // Show/hide link-specific items
        var linkItems = menu.querySelectorAll('.ctx-link-item');
        var linkSep = menu.querySelector('.ctx-link-sep');
        for (var li = 0; li < linkItems.length; li++) {
            linkItems[li].style.display = _ctxLinkEl ? '' : 'none';
        }
        if (linkSep) linkSep.style.display = _ctxLinkEl ? '' : 'none';

        // Update "Go to [site]" label
        if (_ctxLinkEl) {
            var gotoLabel = document.getElementById('ctx-goto-label');
            if (gotoLabel) {
                try {
                    var hostname = new URL(_ctxLinkEl.href).hostname.replace('www.', '');
                    gotoLabel.textContent = 'Go to ' + hostname;
                } catch (ex) {
                    gotoLabel.textContent = 'Open link';
                }
            }
        }

        // Show/hide Cut and Copy only when there's a selection
        var selItems = menu.querySelectorAll('.ctx-has-selection');
        for (var si = 0; si < selItems.length; si++) {
            selItems[si].style.display = sel ? '' : 'none';
        }

        // Show/hide selection-dependent search items (Google, UpToDate, AI)
        var items = menu.querySelectorAll('.ctx-needs-selection');
        for (var i = 0; i < items.length; i++) {
            items[i].style.display = sel ? '' : 'none';
        }
        // Show/hide search separator
        var sepSearch = menu.querySelector('.ctx-sep-search');
        if (sepSearch) sepSearch.style.display = sel ? '' : 'none';

        // Position the menu
        var x = e.clientX, y = e.clientY;
        menu.style.display = 'block';
        var mw = menu.offsetWidth, mh = menu.offsetHeight;
        if (x + mw > window.innerWidth) x = window.innerWidth - mw - 4;
        if (y + mh > window.innerHeight) y = window.innerHeight - mh - 4;
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
    });

    // Hide on click outside or Escape
    document.addEventListener('click', function () { menu.style.display = 'none'; });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') menu.style.display = 'none';
    });

    // Handle menu actions
    menu.addEventListener('click', function (e) {
        var btn = e.target.closest('.ctx-menu-item');
        if (!btn) return;
        var action = btn.getAttribute('data-action');
        var sel = (window.getSelection().toString() || '').trim();

        switch (action) {
            case 'cut':
                document.execCommand('cut');
                break;
            case 'copy':
                if (sel) navigator.clipboard.writeText(sel).catch(function(){});
                else document.execCommand('copy');
                break;
            case 'paste':
                navigator.clipboard.readText().then(function (text) {
                    document.execCommand('insertText', false, text);
                }).catch(function () {
                    document.execCommand('paste');
                });
                break;
            case 'select-all':
                document.execCommand('selectAll');
                break;
            case 'google':
                if (sel) openInPreferredBrowser('https://www.google.com/search?q=' + encodeURIComponent(sel));
                break;
            case 'uptodate':
                if (sel) {
                    // Extract first word for drug lookup
                    var drugWord = sel.split(/[\s,]+/)[0].toLowerCase();
                    openInPreferredBrowser('https://www.uptodate.com/contents/' + encodeURIComponent(drugWord) + '-drug-information');
                }
                break;
            case 'ai-assist':
                if (sel) openAIPanel(sel);
                break;
            // Widget z-index actions (free-form mode)
            case 'widget-forward':
                if (_ctxWidgetEl && window.FreeWidgets) window.FreeWidgets.bringForward(_ctxWidgetEl);
                break;
            case 'widget-backward':
                if (_ctxWidgetEl && window.FreeWidgets) window.FreeWidgets.sendBackward(_ctxWidgetEl);
                break;
            // Link-specific actions
            case 'copy-link-text':
                if (_ctxLinkEl) navigator.clipboard.writeText(_ctxLinkEl.textContent.trim()).catch(function(){});
                break;
            case 'copy-link-url':
                if (_ctxLinkEl) navigator.clipboard.writeText(_ctxLinkEl.href).catch(function(){});
                break;
            case 'goto-link':
                if (_ctxLinkEl) openInPreferredBrowser(_ctxLinkEl.href);
                break;
            case 'google-link':
                if (_ctxLinkEl) {
                    var linkText = _ctxLinkEl.textContent.trim();
                    if (linkText) openInPreferredBrowser('https://www.google.com/search?q=' + encodeURIComponent(linkText));
                }
                break;
            case 'uptodate-link':
                if (_ctxLinkEl) {
                    var ltWord = _ctxLinkEl.textContent.trim().split(/[\s,]+/)[0].toLowerCase();
                    if (ltWord) openInPreferredBrowser('https://www.uptodate.com/contents/' + encodeURIComponent(ltWord) + '-drug-information');
                }
                break;
            case 'ai-link':
                if (_ctxLinkEl && typeof openAIPanel === 'function') openAIPanel(_ctxLinkEl.textContent.trim());
                break;
            case 'refresh':
                location.reload();
                break;
        }
        menu.style.display = 'none';
    });
}

/**
 * Opens a URL in the user's preferred browser via the server endpoint.
 * Falls back to window.open if the API call fails.
 */
function openInPreferredBrowser(url) {
    fetch('/api/open-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    }).catch(function () {
        window.open(url, '_blank');
    });
}


/* ==========================================================
   14.  AI ASSISTANT PANEL
   ========================================================== */

var _aiContext = '';
var _aiMessages = [];
var _aiHipaaAcknowledged = false;

function initAIPanel() {
    var panel = document.getElementById('ai-panel');
    if (!panel) return;

    var closeBtn = document.getElementById('ai-panel-close');
    var form = document.getElementById('ai-form');
    var input = document.getElementById('ai-input');
    var clearCtx = document.getElementById('ai-context-clear');

    closeBtn.addEventListener('click', function () {
        panel.style.display = 'none';
        panel.classList.remove('minimized');
    });

    var minimizeBtn = document.getElementById('ai-panel-minimize');
    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', function () {
            var isMin = panel.classList.toggle('minimized');
            minimizeBtn.innerHTML = isMin ? '&#9634;' : '&#8722;';
            minimizeBtn.title = isMin ? 'Restore' : 'Minimize';
        });
    }

    if (clearCtx) {
        clearCtx.addEventListener('click', function () {
            _aiContext = '';
            document.getElementById('ai-context-bar').style.display = 'none';
            document.getElementById('ai-context-text').textContent = '';
        });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        sendAIMessage(msg);
    });

    // HIPAA modal wiring
    var hipaaModal = document.getElementById('hipaa-modal');
    if (hipaaModal) {
        var agreeCheck = document.getElementById('hipaa-agree-check');
        var agreeBtn = document.getElementById('hipaa-agree-btn');
        var cancelBtn = document.getElementById('hipaa-cancel-btn');

        agreeCheck.addEventListener('change', function () {
            agreeBtn.disabled = !agreeCheck.checked;
        });
        cancelBtn.addEventListener('click', function () {
            hipaaModal.style.display = 'none';
        });
        agreeBtn.addEventListener('click', function () {
            hipaaModal.style.display = 'none';
            _aiHipaaAcknowledged = true;
            // Persist to server
            fetch('/api/ai/acknowledge-hipaa', { method: 'POST' }).catch(function(){});
            // Now show the panel
            _showAIPanelUI();
        });
    }
}

function openAIPanel(selectedText) {
    var panel = document.getElementById('ai-panel');
    if (!panel) return;

    _aiContext = selectedText || '';

    // Check HIPAA acknowledgment — show modal if not yet acknowledged
    if (!_aiHipaaAcknowledged) {
        // Check server-side
        fetch('/api/ai/hipaa-status')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.acknowledged) {
                    _aiHipaaAcknowledged = true;
                    _showAIPanelUI();
                } else {
                    var modal = document.getElementById('hipaa-modal');
                    if (modal) modal.style.display = '';
                }
            })
            .catch(function () {
                // If check fails, show the modal as a safety measure
                var modal = document.getElementById('hipaa-modal');
                if (modal) modal.style.display = '';
            });
    } else {
        _showAIPanelUI();
    }
}

function _showAIPanelUI() {
    var panel = document.getElementById('ai-panel');
    panel.classList.remove('minimized');
    var minBtn = document.getElementById('ai-panel-minimize');
    if (minBtn) { minBtn.innerHTML = '&#8722;'; minBtn.title = 'Minimize'; }
    panel.style.display = 'flex';
    document.getElementById('ai-input').focus();

    if (_aiContext) {
        document.getElementById('ai-context-bar').style.display = '';
        document.getElementById('ai-context-text').textContent =
            _aiContext.length > 120 ? _aiContext.substring(0, 120) + '…' : _aiContext;
    } else {
        document.getElementById('ai-context-bar').style.display = 'none';
    }
}

function sendAIMessage(userMsg) {
    var msgBox = document.getElementById('ai-messages');
    var sendBtn = document.getElementById('ai-send-btn');

    // Render user message
    _aiMessages.push({ role: 'user', content: userMsg });
    _renderAIMessage(msgBox, 'user', userMsg);

    // Show loading
    var loadingEl = document.createElement('div');
    loadingEl.className = 'ai-msg ai-msg--loading';
    loadingEl.textContent = 'Thinking…';
    msgBox.appendChild(loadingEl);
    msgBox.scrollTop = msgBox.scrollHeight;
    sendBtn.disabled = true;

    fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: userMsg,
            context: _aiContext,
            history: _aiMessages.slice(-20)  // last 20 messages for context
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        loadingEl.remove();
        sendBtn.disabled = false;
        if (data.error) {
            _renderAIMessage(msgBox, 'error', data.error);
        } else {
            _aiMessages.push({ role: 'assistant', content: data.reply });
            _renderAIMessage(msgBox, 'assistant', data.reply);
        }
    })
    .catch(function (err) {
        loadingEl.remove();
        sendBtn.disabled = false;
        _renderAIMessage(msgBox, 'error', 'Failed to reach AI service.');
    });
}

function _renderAIMessage(container, role, text) {
    var div = document.createElement('div');
    div.className = 'ai-msg ai-msg--' + role;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
