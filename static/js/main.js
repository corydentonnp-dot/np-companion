/**
 * CareCompanion — Main JavaScript
 * File location: carecompanion/static/js/main.js
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
    initP1Poll();
    initFlashMessages();
    initAgentStatus();
    initAuthStatus();
    initSetupStatus();
    initZoom();
    initNavKeys();
    initUserPopover();
    initContextMenu();
    initAIPanel();
    initMenuBar();
    initBookmarksBar();
    initCommandPalette();
    initPinSystem();
    initKeyboardShortcuts();
    initWhatsNewBanner();
    initSidebarCollapse();
    initDoubleSubmitGuard();
    initFetchInterceptor();
    initModalAccessibility();
    initSortableHeaders();
    initStatePersistence();
    initCollapsible();
    initQuickActions();
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
    // Don't activate if user has not set a PIN
    if (document.body.getAttribute('data-has-pin') !== 'true') return;

    // Restore lock state from sessionStorage (survives refresh)
    if (sessionStorage.getItem('cc_screen_locked') === '1') {
        showLockScreen();
    }

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
    sessionStorage.setItem('cc_screen_locked', '1');
    var input = document.getElementById('pin-input');
    if (input) { input.value = ''; input.focus(); }
    var err = document.getElementById('pin-error');
    if (err) err.textContent = '';
}

function hideLockScreen() {
    var overlay = document.getElementById('lock-overlay');
    if (overlay) overlay.classList.remove('visible');
    sessionStorage.removeItem('cc_screen_locked');
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
    // No session on login page — skip to avoid HTML redirect being parsed as JSON
    if (document.body.getAttribute('data-user-id') === '0') return;
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
                        /* Phase 12: group into "New" (last hour) and "Earlier Today" */
                        var now = Date.now();
                        var oneHour = 60 * 60 * 1000;
                        var newItems = [];
                        var earlierItems = [];
                        items.forEach(function(n) {
                            /* Parse time from "MM/DD HH:MM AM/PM" — rough heuristic */
                            var ts = n.time ? Date.parse(n.time.replace(/(\d{2})\/(\d{2})/, new Date().getFullYear() + '-$1-$2')) : 0;
                            if (ts && (now - ts) < oneHour) {
                                newItems.push(n);
                            } else {
                                earlierItems.push(n);
                            }
                        });

                        function renderItem(n) {
                            var pClass = n.priority === 1 ? ' notif-dd-item--p1' : (n.priority === 2 ? ' notif-dd-item--p2' : '');
                            return '<div class="notif-dd-item' + pClass + ' notif-dd-unread" data-notif-id="' + (n.id || '') + '">' +
                                '<div style="flex:1;">' +
                                '<span class="notif-dd-text">' + escapeHtml(n.message || n.text || '') + '</span>' +
                                (n.sender ? '<div style="font-size:11px;color:var(--text-muted);">From: ' + escapeHtml(n.sender) + '</div>' : '') +
                                '</div>' +
                                '<span class="notif-dd-time">' + escapeHtml(n.time || '') + '</span>' +
                                '</div>';
                        }

                        if (newItems.length > 0) {
                            html += '<div class="notif-dd-section-label">New</div>';
                            newItems.forEach(function(n) { html += renderItem(n); });
                        }
                        if (earlierItems.length > 0) {
                            html += '<div class="notif-dd-section-label">Earlier Today</div>';
                            earlierItems.forEach(function(n) { html += renderItem(n); });
                        }

                        listEl.innerHTML = html;

                        /* Phase 12: Append P3 morning briefing teaser */
                        fetch('/api/notifications/p3-count')
                            .then(function(r) { return r.json(); })
                            .then(function(d) {
                                if (d.p3_count > 0) {
                                    var teaser = document.createElement('div');
                                    teaser.className = 'notif-dd-section-label';
                                    teaser.innerHTML = '☀️ <a href="/briefing" style="color:inherit;text-decoration:underline;">' +
                                        d.p3_count + ' item' + (d.p3_count !== 1 ? 's' : '') + ' in your morning briefing</a>';
                                    listEl.appendChild(teaser);
                                }
                            }).catch(function() {});

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
   5b. P1 INTERRUPT MODAL — polls every 15 seconds (Phase 12)
   ========================================================== */
var _p1SnoozedIds = {};

function initP1Poll() {
    // No session on login page — skip to avoid HTML redirect being parsed as JSON
    if (document.body.getAttribute('data-user-id') === '0') return;
    function pollP1() {
        fetch('/api/notifications/p1')
            .then(function(res) { return res.json(); })
            .then(function(data) {
                var items = data.notifications || [];
                // Find first unacknowledged P1 not currently snoozed
                for (var i = 0; i < items.length; i++) {
                    var n = items[i];
                    if (_p1SnoozedIds[n.id]) continue;
                    showP1Modal(n);
                    return;
                }
            })
            .catch(function() {});
    }
    pollP1();
    setInterval(pollP1, 15000);
}

function showP1Modal(notif) {
    var overlay = document.getElementById('p1-modal-overlay');
    var msgEl = document.getElementById('p1-modal-message');
    if (!overlay || !msgEl) return;
    msgEl.textContent = notif.message || 'Critical notification requires acknowledgment.';
    overlay.setAttribute('data-notif-id', notif.id);
    overlay.style.display = 'flex';
}

function acknowledgeP1() {
    var overlay = document.getElementById('p1-modal-overlay');
    var nid = overlay ? overlay.getAttribute('data-notif-id') : null;
    if (!nid) return;
    fetch('/api/notifications/' + nid + '/acknowledge', { method: 'POST' })
        .then(function() {
            overlay.style.display = 'none';
            delete _p1SnoozedIds[nid];
            // Refresh bell badge
            var badge = document.getElementById('notification-count');
            if (badge) {
                fetch('/api/notifications').then(function(r) { return r.json(); }).then(function(d) {
                    var c = d.unread_count || 0;
                    badge.textContent = c > 99 ? '99+' : c;
                    badge.style.display = c > 0 ? 'inline-block' : 'none';
                });
            }
        });
}

function snoozeP1(minutes) {
    var overlay = document.getElementById('p1-modal-overlay');
    var nid = overlay ? overlay.getAttribute('data-notif-id') : null;
    if (!nid) return;
    _p1SnoozedIds[nid] = true;
    overlay.style.display = 'none';
    // Remove snooze after specified minutes
    setTimeout(function() { delete _p1SnoozedIds[nid]; }, minutes * 60 * 1000);
}


/* ==========================================================
   6.  FLASH MESSAGE DISMISSAL
   ========================================================== */

function initFlashMessages() {
    document.querySelectorAll('.flash-close').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var flash = btn.closest('.flash');
            if (flash) {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-8px)';
                setTimeout(function () { flash.remove(); }, 300);
            }
        });
    });
    /* Auto-dismiss (Phase 10.4): non-error flashes dismiss after data-auto-dismiss ms */
    document.querySelectorAll('.flash[data-auto-dismiss]').forEach(function (flash) {
        var ms = parseInt(flash.getAttribute('data-auto-dismiss'), 10);
        if (ms > 0) {
            setTimeout(function () {
                if (flash.parentNode) {
                    flash.style.opacity = '0';
                    flash.style.transform = 'translateY(-8px)';
                    setTimeout(function () { flash.remove(); }, 300);
                }
            }, ms);
        }
    });
}


/* ==========================================================
   7.  AGENT HEALTH STATUS DOT — polls every 15 seconds
   ========================================================== */

function initAgentStatus() {
    // No session on login page — skip to avoid HTML redirect being parsed as JSON
    if (document.body.getAttribute('data-user-id') === '0') return;
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
                dot.setAttribute('aria-label', dot.title);
            })
            .catch(function () {
                dot.className = 'status-dot status-dot--unknown';
                dot.title = 'Agent: unable to check status';
                dot.setAttribute('aria-label', dot.title);
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
                dot.setAttribute('aria-label', dot.title);
            })
            .catch(function () {
                dot.className = 'status-dot status-dot--unknown';
                dot.title = 'NetPractice: unable to check status';
                dot.setAttribute('aria-label', dot.title);
            });
    }

    poll();                     // first check immediately
    setInterval(poll, 30000);   // then every 30 seconds
}


/* ==========================================================
   9.  SETUP STATUS — shows/hides setup button in header
   ========================================================== */

function initSetupStatus() {
    // No session on login page — skip to avoid HTML redirect being parsed as JSON
    if (document.body.getAttribute('data-user-id') === '0') return;
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
   10b. SIDEBAR COLLAPSE — Restore state + wire collapse button
   ========================================================== */

function initSidebarCollapse() {
    var sidebar = document.getElementById('sidebar');
    var layout = document.querySelector('.app-layout');
    var btn = document.getElementById('sidebar-collapse-btn');

    if (!sidebar || !layout) return;

    /* Restore persisted collapsed state */
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        sidebar.classList.add('collapsed');
        layout.classList.add('sidebar-collapsed');
    }
    /* Remove the pre-paint helper class now that we've applied the real one */
    document.documentElement.classList.remove('sidebar-will-collapse');

    /* Wire the collapse button at the bottom of the sidebar */
    if (btn) {
        btn.addEventListener('click', function () {
            _menuActions.toggleSidebar();
        });
    }
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

/**
 * Sanitize text before writing to clipboard.
 * Blocks known API key patterns from being copied to prevent secret leakage.
 */
function _safeClipboardWrite(text) {
    if (!text) return Promise.resolve();
    // Detect common API key patterns (Anthropic, OpenAI, xAI, generic)
    var keyPatterns = [
        /sk-ant-api\S+/i,        // Anthropic
        /sk-[a-zA-Z0-9]{20,}/,   // OpenAI
        /xai-[a-zA-Z0-9]{20,}/,  // xAI
        /pk-[a-zA-Z0-9]{20,}/,   // Generic provider key
        /key-[a-zA-Z0-9]{20,}/,  // Generic
    ];
    for (var i = 0; i < keyPatterns.length; i++) {
        if (keyPatterns[i].test(text)) {
            console.warn('[CareCompanion] Blocked clipboard write — text matched API key pattern');
            return Promise.resolve();
        }
    }
    return navigator.clipboard.writeText(text).catch(function(){});
}

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
                if (sel) _safeClipboardWrite(sel);
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
                    openInPreferredBrowser('https://www.uptodate.com/contents/search?search=' + encodeURIComponent(sel));
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
                if (_ctxLinkEl) _safeClipboardWrite(_ctxLinkEl.textContent.trim());
                break;
            case 'copy-link-url':
                if (_ctxLinkEl) _safeClipboardWrite(_ctxLinkEl.href);
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
                    var ltText = _ctxLinkEl.textContent.trim();
                    if (ltText) openInPreferredBrowser('https://www.uptodate.com/contents/search?search=' + encodeURIComponent(ltText));
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
   15.  MENU BAR — VS Code-style open/close/hover-switch (5.1)
   ========================================================== */

function initMenuBar() {
    var menuBar = document.getElementById('app-menu-bar');
    if (!menuBar) return;

    var groups = menuBar.querySelectorAll('.menu-group');
    var _openGroup = null;

    function closeAll() {
        groups.forEach(function (g) { g.classList.remove('open'); });
        _openGroup = null;
    }

    /* Click a menu button → toggle its dropdown */
    groups.forEach(function (group) {
        var btn = group.querySelector('.menu-btn');
        if (!btn) return;

        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (group.classList.contains('open')) {
                closeAll();
            } else {
                closeAll();
                group.classList.add('open');
                _openGroup = group;
            }
        });

        /* Hover-switch: if one menu is already open, entering another opens it instead */
        btn.addEventListener('mouseenter', function () {
            if (_openGroup && _openGroup !== group) {
                closeAll();
                group.classList.add('open');
                _openGroup = group;
            }
        });
    });

    /* Click a dropdown item → navigate or fire action */
    menuBar.addEventListener('click', function (e) {
        var item = e.target.closest('.menu-dd-item');
        if (!item) return;
        e.stopPropagation();

        var action = item.getAttribute('data-action');
        var url = item.getAttribute('data-url');
        var external = item.getAttribute('data-external') === 'true';

        closeAll();

        if (action) {
            _menuActions[action] && _menuActions[action](e);
        } else if (url) {
            if (external) {
                openInPreferredBrowser(url);
            } else {
                window.location.href = url;
            }
        }
    });

    /* Document click → close menus */
    document.addEventListener('click', function () {
        closeAll();
    });

    /* Escape → close menus */
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && _openGroup) {
            closeAll();
        }
    });

    /* Mobile hamburger */
    var hamburger = document.getElementById('menu-hamburger');
    if (hamburger) {
        hamburger.addEventListener('click', function (e) {
            e.stopPropagation();
            menuBar.classList.toggle('mobile-open');
        });
    }
}

/* Map of action names → handler functions for menu items with data-action */
var _menuActions = {
    toggleSidebar: function () {
        var sidebar = document.getElementById('sidebar');
        var layout = document.querySelector('.app-layout');
        if (sidebar) {
            var isCollapsed = sidebar.classList.toggle('collapsed');
            if (layout) layout.classList.toggle('sidebar-collapsed', isCollapsed);
            /* Remove pre-paint class once user has interacted */
            document.documentElement.classList.remove('sidebar-will-collapse');
            /* Persist state */
            localStorage.setItem('sidebar-collapsed', isCollapsed ? 'true' : 'false');
        }
    },
    toggleBookmarks: function () {
        var bar = document.getElementById('bookmarks-bar');
        if (bar) bar.classList.toggle('collapsed');
    },
    toggleCompactMode: function () {
        document.body.classList.toggle('compact-mode');
    },
    openManageReferences: function () {
        var modal = document.getElementById('manage-refs-modal');
        if (modal) modal.style.display = 'flex';
    },
    openKeyboardShortcuts: function () {
        var modal = document.getElementById('keyboard-shortcuts-modal');
        if (modal) modal.style.display = 'flex';
    },
    openWhatsNew: function () {
        var modal = document.getElementById('whats-new-modal');
        if (!modal) return;
        modal.style.display = 'flex';
        var body = document.getElementById('whats-new-body');
        if (body && !body.dataset.loaded) {
            fetch('/static/changelog.json?' + Date.now())
                .then(function (r) { return r.ok ? r.json() : []; })
                .then(function (entries) {
                    if (!entries || !entries.length) {
                        body.innerHTML = '<p style="color:var(--text-secondary);">No changelog data available.</p>';
                        return;
                    }
                    var html = '';
                    entries.forEach(function (e) {
                        html += '<div style="margin-bottom:16px;">';
                        html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
                        html += '<strong style="font-size:15px;">v' + (e.version || '?') + '</strong>';
                        if (e.date) html += '<span style="font-size:12px;color:var(--text-secondary);">' + e.date + '</span>';
                        html += '</div>';
                        if (e.highlights && e.highlights.length) {
                            html += '<ul style="margin:0;padding-left:20px;font-size:13px;line-height:1.7;">';
                            e.highlights.forEach(function (h) { html += '<li>' + h + '</li>'; });
                            html += '</ul>';
                        }
                        html += '</div>';
                    });
                    body.innerHTML = html;
                    body.dataset.loaded = '1';
                })
                .catch(function () {
                    body.innerHTML = '<p style="color:var(--text-secondary);">Could not load changelog.</p>';
                });
        }
        /* Also dismiss the banner */
        var banner = document.getElementById('whats-new-banner');
        if (banner) banner.style.display = 'none';
        fetch('/api/settings/dismiss-whats-new', { method: 'POST' }).catch(function () {});
    },
    openAbout: function () {
        var modal = document.getElementById('about-modal');
        if (modal) modal.style.display = 'flex';
    }
};


/* ==========================================================
   16.  BOOKMARKS BAR — load, render chips, add/remove (5.2)
   ========================================================== */

function initBookmarksBar() {
    var bar = document.getElementById('bookmarks-bar');
    if (!bar) return;

    var practiceContainer = document.getElementById('bm-practice-chips');
    var personalContainer = document.getElementById('bm-personal-chips');
    var addBtn = document.getElementById('bm-add-btn');
    var addPopover = document.getElementById('bm-add-popover');
    var addLabel = document.getElementById('bm-add-label');
    var addUrl = document.getElementById('bm-add-url');
    var addSave = document.getElementById('bm-add-save');
    var addCancel = document.getElementById('bm-add-cancel');

    function renderChips(items, container, type) {
        container.innerHTML = '';
        if (!items || !items.length) return;
        items.forEach(function (bm, idx) {
            var chip = document.createElement('button');
            chip.className = 'bm-chip';
            chip.title = bm.url;
            chip.textContent = (type === 'practice' ? '🌐 ' : '📌 ') + bm.label;
            chip.addEventListener('click', function () {
                openInPreferredBrowser(bm.url);
            });
            chip.addEventListener('contextmenu', function (e) {
                e.preventDefault();
                if (type === 'personal') {
                    if (confirm('Remove bookmark "' + bm.label + '"?')) {
                        removePersonalBookmark(idx);
                    }
                }
            });
            container.appendChild(chip);
        });
    }

    function loadBookmarks() {
        fetch('/api/bookmarks')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                renderChips(data.practice || [], practiceContainer, 'practice');
                renderChips(data.personal || [], personalContainer, 'personal');
                // Also populate the Bookmarks menu dropdown
                renderBookmarkMenu(data.practice || [], data.personal || []);
            })
            .catch(function () { /* silently fail — bookmarks not critical */ });
    }

    function renderBookmarkMenu(practice, personal) {
        var practiceWrap = document.getElementById('bm-menu-practice');
        var practiceList = document.getElementById('bm-menu-practice-list');
        var personalWrap = document.getElementById('bm-menu-personal');
        var personalList = document.getElementById('bm-menu-personal-list');
        if (!practiceList || !personalList) return;

        practiceList.innerHTML = '';
        personalList.innerHTML = '';

        if (practice.length) {
            practiceWrap.style.display = '';
            practice.forEach(function (bm) {
                var btn = document.createElement('button');
                btn.className = 'menu-dd-item';
                btn.innerHTML = '<span class="menu-dd-icon">🌐</span>' + escapeHtml(bm.label);
                btn.addEventListener('click', function () { openInPreferredBrowser(bm.url); });
                practiceList.appendChild(btn);
            });
        } else {
            practiceWrap.style.display = 'none';
        }

        if (personal.length) {
            personalWrap.style.display = '';
            personal.forEach(function (bm) {
                var btn = document.createElement('button');
                btn.className = 'menu-dd-item';
                btn.innerHTML = '<span class="menu-dd-icon">📌</span>' + escapeHtml(bm.label);
                btn.addEventListener('click', function () { openInPreferredBrowser(bm.url); });
                personalList.appendChild(btn);
            });
        } else {
            personalWrap.style.display = 'none';
        }
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function removePersonalBookmark(index) {
        if (!confirm('Remove this bookmark?')) return;
        fetch('/api/bookmarks/personal/' + index, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function () { loadBookmarks(); })
            .catch(function () {});
    }

    if (addBtn && addPopover) {
        addBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            addPopover.style.display = addPopover.style.display === 'none' ? 'block' : 'none';
            if (addPopover.style.display === 'block' && addLabel) addLabel.focus();
        });
    }

    if (addCancel) {
        addCancel.addEventListener('click', function () {
            addPopover.style.display = 'none';
            if (addLabel) addLabel.value = '';
            if (addUrl) addUrl.value = '';
        });
    }

    if (addSave) {
        addSave.addEventListener('click', function () {
            var label = (addLabel.value || '').trim();
            var url = (addUrl.value || '').trim();
            if (!label || !url) return;
            fetch('/api/bookmarks/personal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: label, url: url })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    addPopover.style.display = 'none';
                    addLabel.value = '';
                    addUrl.value = '';
                    loadBookmarks();
                }
            })
            .catch(function () {});
        });
    }

    /* Close popover on outside click */
    document.addEventListener('click', function (e) {
        if (addPopover && !addPopover.contains(e.target) && e.target !== addBtn) {
            addPopover.style.display = 'none';
        }
    });

    loadBookmarks();
}


/* ==========================================================
   17.  COMMAND PALETTE — Ctrl+K fuzzy nav (5.3)
   ========================================================== */

function initCommandPalette() {
    var backdrop = document.getElementById('command-palette');
    if (!backdrop) return;

    var input = document.getElementById('cmd-palette-input');
    var list = document.getElementById('cmd-result-list');
    var routes = window.__npRoutes || [];
    var _activeIdx = -1;

    function open() {
        backdrop.style.display = 'flex';
        input.value = '';
        renderResults('');
        setTimeout(function () { input.focus(); }, 50);
    }

    function close() {
        backdrop.style.display = 'none';
        input.value = '';
        _activeIdx = -1;
    }

    function renderResults(query) {
        list.innerHTML = '';
        var q = (query || '').toLowerCase();
        var filtered = routes.filter(function (r) {
            return !q || r.label.toLowerCase().indexOf(q) !== -1 || (r.category && r.category.toLowerCase().indexOf(q) !== -1);
        });

        /* Limit to top 12 */
        filtered = filtered.slice(0, 12);

        /* Group by category */
        var groups = {};
        filtered.forEach(function (r) {
            var cat = r.category || 'Other';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(r);
        });

        var idx = 0;
        Object.keys(groups).forEach(function (cat) {
            var header = document.createElement('li');
            header.className = 'cmd-result-cat';
            header.textContent = cat;
            list.appendChild(header);

            groups[cat].forEach(function (r) {
                var li = document.createElement('li');
                li.className = 'cmd-result-item';
                li.textContent = r.label;
                li.setAttribute('data-url', r.url);
                li.setAttribute('data-idx', idx);
                li.addEventListener('click', function () {
                    navigate(r.url);
                });
                li.addEventListener('mouseenter', function () {
                    setActive(parseInt(li.getAttribute('data-idx'), 10));
                });
                list.appendChild(li);
                idx++;
            });
        });

        _activeIdx = -1;
        if (idx > 0) setActive(0);
    }

    function setActive(idx) {
        var items = list.querySelectorAll('.cmd-result-item');
        items.forEach(function (el) { el.classList.remove('active'); });
        if (items[idx]) {
            items[idx].classList.add('active');
            items[idx].scrollIntoView({ block: 'nearest' });
        }
        _activeIdx = idx;
    }

    function navigate(url) {
        close();
        /* Save to recent in sessionStorage */
        try {
            var recent = JSON.parse(sessionStorage.getItem('cmd_recent') || '[]');
            recent = recent.filter(function (r) { return r !== url; });
            recent.unshift(url);
            if (recent.length > 5) recent = recent.slice(0, 5);
            sessionStorage.setItem('cmd_recent', JSON.stringify(recent));
        } catch (_) {}
        window.location.href = url;
    }

    input.addEventListener('input', function () {
        renderResults(input.value);
    });

    input.addEventListener('keydown', function (e) {
        var items = list.querySelectorAll('.cmd-result-item');
        var count = items.length;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActive((_activeIdx + 1) % count);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActive((_activeIdx - 1 + count) % count);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (items[_activeIdx]) {
                navigate(items[_activeIdx].getAttribute('data-url'));
            }
        } else if (e.key === 'Escape') {
            close();
        }
    });

    /* Click backdrop to close */
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) close();
    });

    /* Ctrl+K to open */
    document.addEventListener('keydown', function (e) {
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            if (backdrop.style.display === 'flex') { close(); } else { open(); }
        }
    });
}


/* ==========================================================
   18.  PIN SYSTEM — right-click menu item → pin to sidebar (5.4)
   ========================================================== */

function initPinSystem() {
    var ctxMenu = document.getElementById('pin-ctx-menu');
    if (!ctxMenu) return;

    var _targetItem = null;

    /* Listen for right-click on any .menu-dd-item that has a data-url */
    document.addEventListener('contextmenu', function (e) {
        var item = e.target.closest('.menu-dd-item[data-url]');
        if (!item || item.getAttribute('data-external') === 'true') return;
        e.preventDefault();
        _targetItem = item;

        /* Position the context menu */
        ctxMenu.style.left = e.clientX + 'px';
        ctxMenu.style.top = e.clientY + 'px';
        ctxMenu.style.display = 'block';

        /* Show pin or unpin based on current state */
        var url = item.getAttribute('data-url');
        var pinBtn = ctxMenu.querySelector('[data-action="pin-item"]');
        var unpinBtn = ctxMenu.querySelector('[data-action="unpin-item"]');
        var isPinned = document.querySelector('.pinned-item[data-pin-url="' + url + '"]');
        if (pinBtn) pinBtn.style.display = isPinned ? 'none' : '';
        if (unpinBtn) unpinBtn.style.display = isPinned ? '' : 'none';
    });

    /* Pin action */
    ctxMenu.querySelector('[data-action="pin-item"]').addEventListener('click', function () {
        if (!_targetItem) return;
        var url = _targetItem.getAttribute('data-url');
        var iconSpan = _targetItem.querySelector('.menu-dd-icon');
        var label = _targetItem.textContent.replace(/[\s]+/g, ' ').trim();
        /* Remove icon text and shortcut from label */
        if (iconSpan) label = label.replace(iconSpan.textContent, '').trim();
        var shortcutSpan = _targetItem.querySelector('.menu-dd-shortcut');
        if (shortcutSpan && shortcutSpan.textContent) label = label.replace(shortcutSpan.textContent, '').trim();
        var icon = iconSpan ? iconSpan.textContent.trim() : '📌';

        fetch('/api/prefs/pin-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ label: label, url: url, icon: icon })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                _addPinnedItemToDOM(label, url, icon);
            }
        })
        .catch(function () {});
        ctxMenu.style.display = 'none';
    });

    /* Unpin action */
    ctxMenu.querySelector('[data-action="unpin-item"]').addEventListener('click', function () {
        if (!_targetItem) return;
        var url = _targetItem.getAttribute('data-url');

        fetch('/api/prefs/unpin-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                _removePinnedItemFromDOM(url);
            }
        })
        .catch(function () {});
        ctxMenu.style.display = 'none';
    });

    /* Close pin context on outside click */
    document.addEventListener('click', function () {
        ctxMenu.style.display = 'none';
    });
}

/* Helper: inject a pinned item into the sidebar DOM */
function _addPinnedItemToDOM(label, url, icon) {
    var section = document.getElementById('pinned-section');
    if (!section) {
        /* Create the pinned section dynamically */
        var sidebar = document.getElementById('sidebar');
        var footer = sidebar ? sidebar.querySelector('.sidebar-footer') : null;
        if (!sidebar || !footer) return;
        section = document.createElement('nav');
        section.className = 'sidebar-nav pinned-section';
        section.id = 'pinned-section';
        section.style.marginTop = '0';
        section.innerHTML = '<div style="padding:4px 16px 4px;font-size:10px;text-transform:uppercase;letter-spacing:.1em;opacity:.55;">Pinned</div><ul class="nav-list"></ul>';
        sidebar.insertBefore(section, footer);
    }
    var list = section.querySelector('.nav-list');
    if (!list) return;

    var li = document.createElement('li');
    li.className = 'nav-item pinned-item';
    li.setAttribute('data-pin-url', url);
    li.innerHTML = '<a href="' + url + '" class="nav-link" title="' + label + '"><span class="nav-icon" style="font-size:14px;width:20px;text-align:center;">' + icon + '</span><span class="nav-label">' + label + '</span></a>';
    list.appendChild(li);
}

/* Helper: remove a pinned item from sidebar DOM */
function _removePinnedItemFromDOM(url) {
    var item = document.querySelector('.pinned-item[data-pin-url="' + url + '"]');
    if (item) item.remove();

    /* If no pinned items left, remove the section */
    var section = document.getElementById('pinned-section');
    if (section) {
        var remaining = section.querySelectorAll('.pinned-item');
        if (remaining.length === 0) section.remove();
    }
}


/* ==========================================================
   19.  KEYBOARD SHORTCUTS — Ctrl+B, Ctrl+Shift+B, ? (5.5)
   ========================================================== */

function initKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        /* Skip if user is typing in a text field */
        var tag = (e.target.tagName || '').toLowerCase();
        var isInput = (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable);

        /* Ctrl+B → toggle sidebar */
        if (e.ctrlKey && !e.shiftKey && e.key === 'b') {
            e.preventDefault();
            _menuActions.toggleSidebar();
            return;
        }

        /* Ctrl+Shift+B → toggle bookmarks bar */
        if (e.ctrlKey && e.shiftKey && (e.key === 'B' || e.key === 'b')) {
            e.preventDefault();
            _menuActions.toggleBookmarks();
            return;
        }

        /* Ctrl+Shift+K → Clinical Calculators */
        if (e.ctrlKey && e.shiftKey && (e.key === 'K' || e.key === 'k')) {
            e.preventDefault();
            window.location.href = '/calculators';
            return;
        }

        /* ? → keyboard shortcuts (only when not in an input field) */
        if (!isInput && e.key === '?' && !e.ctrlKey && !e.altKey) {
            e.preventDefault();
            _menuActions.openKeyboardShortcuts();
            return;
        }

        /* Escape → close modals */
        if (e.key === 'Escape') {
            var modals = document.querySelectorAll('.modal-backdrop[style*="flex"]');
            modals.forEach(function (m) { m.style.display = 'none'; });
        }
    });

    /* Wire up modal close buttons (data-dismiss attribute) */
    document.querySelectorAll('.modal-close[data-dismiss]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modalId = btn.getAttribute('data-dismiss');
            var modal = document.getElementById(modalId);
            if (modal) modal.style.display = 'none';
        });
    });

    /* Click modal backdrop to close */
    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
        backdrop.addEventListener('click', function (e) {
            if (e.target === backdrop) backdrop.style.display = 'none';
        });
    });

    /* Tab switching inside modals */
    document.querySelectorAll('.cc-tabs').forEach(function (group) {
        group.querySelectorAll('.cc-tab').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var tabId = btn.getAttribute('data-tab');
                if (!tabId) return; /* skip tabs wired with their own onclick */
                /* Deactivate siblings */
                group.querySelectorAll('.cc-tab').forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                /* Show matching panel, hide others */
                var parent = group.parentElement;
                parent.querySelectorAll('.tab-panel').forEach(function (p) { p.classList.remove('active'); });
                var panel = document.getElementById(tabId);
                if (panel) panel.classList.add('active');
            });
        });
    });
}


/* ==========================================================
   20.  WHAT'S NEW BANNER — dismiss + persist (5.6)
   ========================================================== */

function initWhatsNewBanner() {
    var banner = document.getElementById('whats-new-banner');
    if (!banner) return;

    var dismissBtn = document.getElementById('whats-new-dismiss');
    var detailsLink = document.getElementById('whats-new-details');

    if (dismissBtn) {
        dismissBtn.addEventListener('click', function () {
            banner.style.display = 'none';
            fetch('/api/settings/dismiss-whats-new', { method: 'POST' })
                .catch(function () {});
        });
    }

    if (detailsLink) {
        detailsLink.addEventListener('click', function (e) {
            e.preventDefault();
            banner.style.display = 'none';
            fetch('/api/settings/dismiss-whats-new', { method: 'POST' })
                .catch(function () {});
            /* Open the What's New modal */
            if (_menuActions.openWhatsNew) _menuActions.openWhatsNew();
        });
    }
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

/* ================================================================
   Phase 14 — WhyLink popover toggle + dismiss dialog
   ================================================================ */
function whyBadge(reason, source) {
    return '<span class="why-link" tabindex="0" role="button">Why?<span class="why-popover"><span class="why-popover-reason">' +
        escHtml(reason) + '</span><span class="why-popover-source">Source: ' + escHtml(source) + '</span></span></span>';
}

(function initWhyLinks() {
    document.addEventListener('click', function (e) {
        var link = e.target.closest('.why-link');
        /* Close all open popovers first */
        document.querySelectorAll('.why-link.why-open').forEach(function (el) {
            if (el !== link) el.classList.remove('why-open');
        });
        if (link) {
            e.preventDefault();
            link.classList.toggle('why-open');
        }
    });
})();

/* Global dismiss dialog helper */
var _dismissPending = null;

function showDismissDialog(itemType, itemId, endpoint) {
    _dismissPending = { type: itemType, id: itemId, endpoint: endpoint };
    var overlay = document.getElementById('dismiss-overlay');
    if (!overlay) return;
    overlay.classList.add('dismiss-open');
    /* Reset form */
    var radios = overlay.querySelectorAll('input[name="dismiss_reason"]');
    radios.forEach(function (r) { r.checked = false; });
    var custom = overlay.querySelector('.dismiss-custom-reason');
    if (custom) custom.value = '';
    radios[0].checked = true;
}

function closeDismissDialog() {
    var overlay = document.getElementById('dismiss-overlay');
    if (overlay) overlay.classList.remove('dismiss-open');
    _dismissPending = null;
}

function submitDismiss() {
    if (!_dismissPending) return;
    var overlay = document.getElementById('dismiss-overlay');
    var checked = overlay.querySelector('input[name="dismiss_reason"]:checked');
    var reason = checked ? checked.value : '';
    if (reason === '__custom') {
        reason = (overlay.querySelector('.dismiss-custom-reason').value || '').trim();
        if (!reason) { alert('Please enter a reason.'); return; }
    }
    fetch(_dismissPending.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason })
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
        if (d.success) location.reload();
    });
    closeDismissDialog();
}


/* ==========================================================
   22.  DOUBLE-SUBMIT GUARD — prevents re-submitting POST forms
   ========================================================== */
function initDoubleSubmitGuard() {
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (!form || form.method.toUpperCase() !== 'POST') return;
        var btn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (!btn) return;
        if (btn.dataset.submitting === 'true') {
            e.preventDefault();
            return;
        }
        btn.dataset.submitting = 'true';
        btn.disabled = true;
        btn.style.opacity = '0.6';
        /* Re-enable after 5s as safety net (for failed submissions) */
        setTimeout(function () {
            btn.disabled = false;
            btn.style.opacity = '';
            btn.dataset.submitting = '';
        }, 5000);
    });
}


/* ==========================================================
   23.  GLOBAL FETCH INTERCEPTOR — detects 401 session expiry
   ========================================================== */
function initFetchInterceptor() {
    var _origFetch = window.fetch;
    window.fetch = function (url, opts) {
        return _origFetch.apply(this, arguments).then(function (response) {
            if (response.status === 401) {
                /* Session expired — show toast and redirect */
                if (typeof showError === 'function') {
                    showError('Your session has expired. Redirecting to login...');
                }
                setTimeout(function () { window.location.href = '/login'; }, 2000);
            }
            return response;
        });
    };
}


/* ==========================================================
   24.  MODAL ACCESSIBILITY — focus trap + Escape to close
   ========================================================== */
function initModalAccessibility() {
    /* Trap focus inside any visible element with [data-modal] or .modal-overlay */
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            /* Close the topmost open modal/overlay */
            var modals = document.querySelectorAll('.modal-overlay, [data-modal]');
            for (var i = modals.length - 1; i >= 0; i--) {
                var m = modals[i];
                if (m.offsetParent !== null || m.style.display === 'flex' || m.style.display === 'block' || m.classList.contains('dismiss-open')) {
                    /* Try clicking a close button inside it */
                    var closeBtn = m.querySelector('.modal-close, .btn-close, [data-dismiss], button[aria-label="Close"], button[aria-label="Dismiss"]');
                    if (closeBtn) { closeBtn.click(); return; }
                    /* Otherwise hide it */
                    m.style.display = 'none';
                    return;
                }
            }
        }

        if (e.key !== 'Tab') return;

        /* Find the active modal */
        var activeModal = null;
        var modals = document.querySelectorAll('.modal-overlay, [data-modal]');
        for (var i = 0; i < modals.length; i++) {
            var m = modals[i];
            if (m.offsetParent !== null || m.style.display === 'flex' || m.style.display === 'block' || m.classList.contains('dismiss-open')) {
                activeModal = m;
                break;
            }
        }
        if (!activeModal) return;

        /* Focus trap */
        var focusable = activeModal.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
        if (focusable.length === 0) return;
        var first = focusable[0];
        var last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    });
}


/* ==========================================================
   25.  SORTABLE TABLE HEADERS — click <th data-sort> to sort
   ========================================================== */
function initSortableHeaders() {
    document.addEventListener('click', function (e) {
        var th = e.target.closest('.data-table th[data-sort]');
        if (!th) return;

        var table = th.closest('table');
        var tbody = table.querySelector('tbody');
        if (!tbody) return;

        var colIndex = Array.from(th.parentNode.children).indexOf(th);
        var currentDir = th.getAttribute('data-sort');
        var newDir = (currentDir === 'asc') ? 'desc' : 'asc';

        /* Reset sibling sort indicators */
        th.parentNode.querySelectorAll('th[data-sort]').forEach(function (s) {
            if (s !== th) s.setAttribute('data-sort', '');
        });
        th.setAttribute('data-sort', newDir);

        var rows = Array.from(tbody.querySelectorAll('tr'));
        var sortType = th.dataset.sortType || 'text'; /* text | number | date */

        rows.sort(function (a, b) {
            var aCell = a.cells[colIndex];
            var bCell = b.cells[colIndex];
            if (!aCell || !bCell) return 0;
            var aVal = (aCell.dataset.sortValue !== undefined ? aCell.dataset.sortValue : aCell.textContent).trim();
            var bVal = (bCell.dataset.sortValue !== undefined ? bCell.dataset.sortValue : bCell.textContent).trim();

            if (sortType === 'number') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
                return (newDir === 'asc' ? 1 : -1) * (aVal - bVal);
            }
            if (sortType === 'date') {
                aVal = new Date(aVal).getTime() || 0;
                bVal = new Date(bVal).getTime() || 0;
                return (newDir === 'asc' ? 1 : -1) * (aVal - bVal);
            }
            return (newDir === 'asc' ? 1 : -1) * aVal.localeCompare(bVal);
        });

        rows.forEach(function (row) { tbody.appendChild(row); });

        /* Persist sort state per table */
        var tableId = table.id;
        if (tableId) {
            sessionStorage.setItem('cc_sort_' + tableId, colIndex + ':' + newDir);
        }
    });

    /* Restore saved sort state on page load */
    document.querySelectorAll('.data-table[id]').forEach(function (table) {
        var saved = sessionStorage.getItem('cc_sort_' + table.id);
        if (!saved) return;
        var parts = saved.split(':');
        var colIndex = parseInt(parts[0], 10);
        var dir = parts[1];
        var th = table.querySelector('thead tr').children[colIndex];
        if (th && th.hasAttribute('data-sort')) {
            th.setAttribute('data-sort', dir === 'asc' ? 'desc' : 'asc');  /* pre-set opposite so click toggles to saved */
            th.click();
        }
    });
}


/* ==========================================================
   26.  STATE PERSISTENCE — restore filter/tab state per page
   ========================================================== */
function initStatePersistence() {
    var pageKey = 'cc_state_' + location.pathname;

    /* Restore form inputs marked [data-persist] */
    document.querySelectorAll('[data-persist]').forEach(function (el) {
        var key = pageKey + '_' + el.getAttribute('data-persist');
        var saved = sessionStorage.getItem(key);
        if (saved === null) return;

        if (el.tagName === 'SELECT') {
            el.value = saved;
        } else if (el.type === 'checkbox' || el.type === 'radio') {
            el.checked = (saved === 'true');
        } else {
            el.value = saved;
        }
        /* Trigger change so any dependent JS runs */
        el.dispatchEvent(new Event('change', { bubbles: true }));
    });

    /* Save on change */
    document.addEventListener('change', function (e) {
        var el = e.target.closest('[data-persist]');
        if (!el) return;
        var key = pageKey + '_' + el.getAttribute('data-persist');
        var val = (el.type === 'checkbox' || el.type === 'radio') ? String(el.checked) : el.value;
        sessionStorage.setItem(key, val);
    });

    /* Restore active tab marked [data-persist-tab] */
    document.querySelectorAll('[data-persist-tab]').forEach(function (tabGroup) {
        var groupKey = pageKey + '_tab_' + tabGroup.getAttribute('data-persist-tab');
        var saved = sessionStorage.getItem(groupKey);
        if (!saved) return;

        var target = tabGroup.querySelector('[data-tab="' + saved + '"]');
        if (target) target.click();
    });

    /* Save active tab on click */
    document.addEventListener('click', function (e) {
        var tab = e.target.closest('[data-tab]');
        if (!tab) return;
        var group = tab.closest('[data-persist-tab]');
        if (!group) return;
        var groupKey = pageKey + '_tab_' + group.getAttribute('data-persist-tab');
        sessionStorage.setItem(groupKey, tab.getAttribute('data-tab'));
    });

    /* Restore scroll position */
    var scrollKey = pageKey + '_scrollY';
    var savedScroll = sessionStorage.getItem(scrollKey);
    if (savedScroll) {
        requestAnimationFrame(function () {
            window.scrollTo(0, parseInt(savedScroll, 10));
        });
    }

    /* Save scroll position on beforeunload */
    window.addEventListener('beforeunload', function () {
        sessionStorage.setItem(scrollKey, String(window.scrollY));
    });
}


/* ==========================================================
   27.  COLLAPSIBLE SECTIONS — unified collapse/expand
   ========================================================== */
function initCollapsible() {
    /* Restore saved collapse states */
    document.querySelectorAll('[data-collapsible]').forEach(function (trigger) {
        var key = trigger.getAttribute('data-collapsible');
        var targetSel = trigger.getAttribute('data-collapsible-target');
        var target = targetSel ? document.querySelector(targetSel) : trigger.nextElementSibling;
        if (!target) return;

        var saved = localStorage.getItem('cc_collapse_' + key);
        if (saved === 'collapsed') {
            target.classList.add('cc-collapsed');
            trigger.classList.add('cc-collapsed');
            trigger.setAttribute('aria-expanded', 'false');
        } else {
            trigger.setAttribute('aria-expanded', 'true');
        }
    });

    /* Toggle on click */
    document.addEventListener('click', function (e) {
        var trigger = e.target.closest('[data-collapsible]');
        if (!trigger) return;

        var key = trigger.getAttribute('data-collapsible');
        var targetSel = trigger.getAttribute('data-collapsible-target');
        var target = targetSel ? document.querySelector(targetSel) : trigger.nextElementSibling;
        if (!target) return;

        var isCollapsed = target.classList.toggle('cc-collapsed');
        trigger.classList.toggle('cc-collapsed', isCollapsed);
        trigger.setAttribute('aria-expanded', String(!isCollapsed));
        localStorage.setItem('cc_collapse_' + key, isCollapsed ? 'collapsed' : 'expanded');
    });
}


/* ==========================================================
   28.  QUICK ACTIONS — inline status toggle via fetch
   ========================================================== */
function initQuickActions() {
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-quick-action]');
        if (!btn || btn.disabled) return;
        e.preventDefault();

        var url = btn.getAttribute('data-quick-action');
        var method = btn.getAttribute('data-method') || 'POST';
        var confirmMsg = btn.getAttribute('data-confirm');
        if (confirmMsg && !confirm(confirmMsg)) return;

        /* Show loading state */
        var origHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner loading-spinner--sm"></span>';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            btn.disabled = false;
            if (data.success || data.ok) {
                /* Update badge text if data-status-target is set */
                var targetSel = btn.getAttribute('data-status-target');
                if (targetSel && data.data && data.data.status) {
                    var badge = document.querySelector(targetSel);
                    if (badge) badge.textContent = data.data.status;
                }
                /* Update button text if data-success-text is set */
                var successText = btn.getAttribute('data-success-text');
                if (successText) {
                    btn.innerHTML = successText;
                    setTimeout(function () { btn.innerHTML = origHtml; }, 2000);
                } else {
                    btn.innerHTML = origHtml;
                }
                /* Optionally reload */
                if (btn.hasAttribute('data-reload')) location.reload();
            } else {
                btn.innerHTML = origHtml;
                if (typeof showError === 'function') {
                    showError(data.error || 'Action failed');
                }
            }
        })
        .catch(function () {
            btn.disabled = false;
            btn.innerHTML = origHtml;
            if (typeof showError === 'function') {
                showError('Network error');
            }
        });
    });
}


/* ==========================================================
   26.  _withSpinner — Global button loading state helper
   ========================================================== */
/**
 * Disable a button, show a spinner, and restore when the promise settles.
 * Usage:  _withSpinner(btn, fetch('/url', opts).then(...))
 * Safe to call with btn=null (returns promise unchanged).
 */
function _withSpinner(btn, promise) {
    if (!btn) return promise;
    var orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner loading-spinner--sm"></span>';
    return promise.finally(function () {
        btn.disabled = false;
        btn.innerHTML = orig;
    });
}
