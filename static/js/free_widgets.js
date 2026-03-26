/**
 * CareCompanion — Free-Form Widget Positioning
 * File: static/js/free_widgets.js
 *
 * Provides drag-to-move, resize, snap-to-grid, z-index management,
 * and localStorage persistence for any page that uses the
 * `.fw-container` / `.fw-widget` structure.
 *
 * Usage:
 *   - Wrap widgets in a container with class `fw-container`
 *   - Give each widget class `fw-widget` and a `data-widget-id` attribute
 *   - Include the _free_widgets.html partial for layout toggle buttons
 *   - This script auto-initialises on DOMContentLoaded
 */

(function () {
    'use strict';

    var SNAP_SIZE = 20;
    var _dragState = null;
    var _resizeState = null;
    var _userId = document.body.getAttribute('data-user-id') || '0';
    var _pageKey = document.body.getAttribute('data-page') || 'page';

    /* ---- Storage helpers ---- */
    function _storageKey(suffix) {
        return 'fw_u' + _userId + '_' + _pageKey + '_' + suffix;
    }

    function _loadPositions() {
        var local;
        try { local = JSON.parse(localStorage.getItem(_storageKey('pos')) || 'null'); }
        catch (e) { local = null; }
        if (local && Object.keys(local).length > 0) return local;
        // Server fallback
        if (window._fwServerPositions && typeof window._fwServerPositions === 'object') {
            return window._fwServerPositions;
        }
        return {};
    }

    function _savePositions(container) {
        var widgets = container.querySelectorAll('.fw-widget');
        var pos = {};
        widgets.forEach(function (w, i) {
            var wid = w.getAttribute('data-widget-id') || ('w' + i);
            pos[wid] = {
                x: parseInt(w.style.left) || 0,
                y: parseInt(w.style.top) || 0,
                w: w.offsetWidth,
                h: w.offsetHeight,
                z: parseInt(w.style.zIndex) || 1
            };
        });
        localStorage.setItem(_storageKey('pos'), JSON.stringify(pos));
    }

    function _getMode() {
        // Server-side preference (data attribute) → localStorage → default 'grid'
        var container = document.querySelector('.fw-container');
        var serverMode = container && container.getAttribute('data-server-mode');
        if (serverMode && (serverMode === 'grid' || serverMode === 'free')) return serverMode;
        return localStorage.getItem(_storageKey('mode')) || 'grid';
    }

    function _snap(v) { return Math.round(v / SNAP_SIZE) * SNAP_SIZE; }

    /* ---- Server persistence helpers ---- */
    function _savePreferenceToServer(key, value) {
        fetch('/settings/account/preference', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: key, value: value})
        }).catch(function() {});
    }

    function _savePositionsToServer(container) {
        var widgets = container.querySelectorAll('.fw-widget');
        var pos = {};
        widgets.forEach(function (w, i) {
            var wid = w.getAttribute('data-widget-id') || ('w' + i);
            pos[wid] = {
                x: parseInt(w.style.left) || 0,
                y: parseInt(w.style.top) || 0,
                w: w.offsetWidth,
                h: w.offsetHeight,
                z: parseInt(w.style.zIndex) || 1
            };
        });
        _savePreferenceToServer('chart_free_widget_positions', pos);
    }

    /* ---- Resolve overlaps — push overlapping widgets downward ---- */
    function _resolveOverlaps(container) {
        if (_getMode() !== 'free') return;
        var GAP = 16;
        var widgets = Array.from(container.querySelectorAll('.fw-widget'));
        widgets = widgets.filter(function(w) { return w.style.display !== 'none'; });

        var maxPasses = 3;
        for (var pass = 0; pass < maxPasses; pass++) {
            widgets.sort(function(a, b) {
                return (parseInt(a.style.top) || 0) - (parseInt(b.style.top) || 0);
            });
            var moved = false;
            for (var i = 0; i < widgets.length; i++) {
                var a = widgets[i];
                var aL = parseInt(a.style.left) || 0;
                var aT = parseInt(a.style.top) || 0;
                var aR = aL + a.offsetWidth;
                var aB = aT + a.offsetHeight;
                for (var j = i + 1; j < widgets.length; j++) {
                    var b = widgets[j];
                    var bL = parseInt(b.style.left) || 0;
                    var bT = parseInt(b.style.top) || 0;
                    var bR = bL + b.offsetWidth;
                    if (aL < bR && aR > bL && aT < (bT + b.offsetHeight) && aB > bT) {
                        var newTop = aB + GAP;
                        b.style.transition = 'top 0.2s ease';
                        b.style.top = newTop + 'px';
                        setTimeout((function(el) { return function() { el.style.transition = ''; }; })(b), 250);
                        moved = true;
                    }
                }
            }
            if (!moved) break;
        }
    }

    /* ---- Compact vertical gaps — pull widgets up to fill blank space ---- */
    function _compactGaps(container) {
        if (_getMode() !== 'free') return;
        var GAP = 16;
        var widgets = Array.from(container.querySelectorAll('.fw-widget'));
        widgets = widgets.filter(function(w) { return w.style.display !== 'none'; });

        widgets.sort(function(a, b) {
            return (parseInt(a.style.top) || 0) - (parseInt(b.style.top) || 0);
        });

        for (var i = 0; i < widgets.length; i++) {
            var w = widgets[i];
            var wL = parseInt(w.style.left) || 0;
            var wT = parseInt(w.style.top) || 0;
            var wR = wL + w.offsetWidth;

            // Find the lowest bottom edge of any widget above that horizontally overlaps
            var minTop = 0;
            for (var j = 0; j < i; j++) {
                var above = widgets[j];
                var aL = parseInt(above.style.left) || 0;
                var aR = aL + above.offsetWidth;
                var aB = (parseInt(above.style.top) || 0) + above.offsetHeight;
                if (wL < aR && wR > aL) {
                    var needed = aB + GAP;
                    if (needed > minTop) minTop = needed;
                }
            }

            if (wT > minTop) {
                w.style.transition = 'top 0.2s ease';
                w.style.top = minTop + 'px';
                setTimeout((function(el) { return function() { el.style.transition = ''; }; })(w), 250);
            }
        }
    }

    /* ---- Bring to front ---- */
    function _bringToFront(widget, container) {
        var all = container.querySelectorAll('.fw-widget');
        var maxZ = 1;
        all.forEach(function (w) {
            var z = parseInt(w.style.zIndex) || 1;
            if (z > maxZ) maxZ = z;
        });
        widget.style.zIndex = maxZ + 1;
    }

    /* ---- Send backward ---- */
    function _sendBackward(widget, container) {
        var z = parseInt(widget.style.zIndex) || 1;
        if (z > 1) widget.style.zIndex = z - 1;
    }

    /* ---- Update container min-height to fit content ---- */
    function _updateMinHeight(container) {
        var maxBottom = 0;
        container.querySelectorAll('.fw-widget').forEach(function (w) {
            var b = (parseInt(w.style.top) || 0) + w.offsetHeight;
            if (b > maxBottom) maxBottom = b;
        });
        container.style.minHeight = (maxBottom + 40) + 'px';
    }

    /* ---- Remove free-mode decorations ---- */
    function _cleanWidget(w) {
        w.style.position = '';
        w.style.left = '';
        w.style.top = '';
        w.style.width = '';
        w.style.height = '';
        w.style.zIndex = '';
        w.style.cursor = '';
        w.style.overflow = '';
        var dh = w.querySelector('.fw-drag-handle');
        if (dh) dh.remove();
        var rg = w.querySelector('.fw-resize-grip');
        if (rg) rg.remove();
    }

    /* ---- Drag handlers ---- */
    function _startDrag(e) {
        e.preventDefault();
        var widget = e.target.closest('.fw-widget');
        var container = widget ? widget.closest('.fw-container') : null;
        if (!widget || !container) return;
        if (widget.classList.contains('fw-pinned')) return;
        _bringToFront(widget, container);
        _dragState = {
            el: widget,
            container: container,
            startX: e.clientX,
            startY: e.clientY,
            origLeft: parseInt(widget.style.left) || 0,
            origTop: parseInt(widget.style.top) || 0
        };
        document.addEventListener('mousemove', _onDrag);
        document.addEventListener('mouseup', _endDrag);
    }

    function _onDrag(e) {
        if (!_dragState) return;
        var dx = e.clientX - _dragState.startX;
        var dy = e.clientY - _dragState.startY;
        var x = Math.max(0, _dragState.origLeft + dx);
        var y = Math.max(0, _dragState.origTop + dy);
        if (e.shiftKey) { x = _snap(x); y = _snap(y); }
        _dragState.el.style.left = x + 'px';
        _dragState.el.style.top = y + 'px';

        // Auto-scroll when dragging near container edges
        var container = _dragState.container;
        var main = container.closest('.main-content') || container.parentElement;
        if (main) {
            var rect = main.getBoundingClientRect();
            var scrollSpeed = 12;
            if (e.clientY > rect.bottom - 40) main.scrollTop += scrollSpeed;
            else if (e.clientY < rect.top + 40) main.scrollTop -= scrollSpeed;
        }
    }

    function _endDrag() {
        if (_dragState) {
            var h = _dragState.el.querySelector('.fw-drag-handle');
            if (h) { h.style.opacity = '0.5'; h.style.cursor = 'grab'; }
            _resolveOverlaps(_dragState.container);
            _compactGaps(_dragState.container);
            _savePositions(_dragState.container);
            _savePositionsToServer(_dragState.container);
            _updateMinHeight(_dragState.container);
        }
        _dragState = null;
        document.removeEventListener('mousemove', _onDrag);
        document.removeEventListener('mouseup', _endDrag);
    }

    /* ---- Resize handlers ---- */
    function _startResize(e) {
        e.preventDefault();
        e.stopPropagation();
        var widget = e.target.closest('.fw-widget');
        var container = widget ? widget.closest('.fw-container') : null;
        if (!widget || !container) return;
        if (widget.classList.contains('fw-pinned')) return;
        _bringToFront(widget, container);
        widget.classList.add('fw-resizing');
        _resizeState = {
            el: widget,
            container: container,
            startX: e.clientX,
            startY: e.clientY,
            origW: widget.offsetWidth,
            origH: widget.offsetHeight
        };
        document.addEventListener('mousemove', _onResize);
        document.addEventListener('mouseup', _endResize);
    }

    function _onResize(e) {
        if (!_resizeState) return;
        var dx = e.clientX - _resizeState.startX;
        var dy = e.clientY - _resizeState.startY;
        var w = Math.max(200, _resizeState.origW + dx);
        var h = Math.max(100, _resizeState.origH + dy);
        if (e.shiftKey) { w = _snap(w); h = _snap(h); }
        _resizeState.el.style.width = w + 'px';
        _resizeState.el.style.height = h + 'px';
    }

    function _endResize() {
        if (_resizeState) {
            _resizeState.el.classList.remove('fw-resizing');
            _resolveOverlaps(_resizeState.container);
            _compactGaps(_resizeState.container);
            _savePositions(_resizeState.container);
            _savePositionsToServer(_resizeState.container);
            _updateMinHeight(_resizeState.container);
        }
        _resizeState = null;
        document.removeEventListener('mousemove', _onResize);
        document.removeEventListener('mouseup', _endResize);
    }

    /* ---- Decorate a widget for free mode ---- */
    function _decorateWidget(w) {
        /* Drag handle */
        if (!w.querySelector('.fw-drag-handle')) {
            var handle = document.createElement('div');
            handle.className = 'fw-drag-handle';
            handle.title = 'Drag to move (Shift+drag to snap)';
            handle.innerHTML = '<svg width="20" height="8" viewBox="0 0 20 8" style="pointer-events:none;"><circle cx="4" cy="2" r="1.5" fill="currentColor"/><circle cx="10" cy="2" r="1.5" fill="currentColor"/><circle cx="16" cy="2" r="1.5" fill="currentColor"/><circle cx="4" cy="6" r="1.5" fill="currentColor"/><circle cx="10" cy="6" r="1.5" fill="currentColor"/><circle cx="16" cy="6" r="1.5" fill="currentColor"/></svg>';
            handle.style.cssText = 'position:absolute;top:0;left:0;right:0;height:18px;cursor:grab;' +
                'background:var(--color-teal);opacity:0.5;transition:opacity .15s;z-index:5;' +
                'border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center;' +
                'color:rgba(255,255,255,.8);';
            handle.addEventListener('mouseenter', function () { handle.style.opacity = '1'; });
            handle.addEventListener('mouseleave', function () { if (!_dragState) { handle.style.opacity = '0.5'; } });
            handle.addEventListener('mousedown', _startDrag);
            w.style.overflow = 'visible';
            w.insertBefore(handle, w.firstChild);
        }

        /* Resize grip */
        if (!w.querySelector('.fw-resize-grip')) {
            var grip = document.createElement('div');
            grip.className = 'fw-resize-grip';
            grip.style.cssText = 'position:absolute;bottom:0;right:0;width:16px;height:16px;cursor:nwse-resize;z-index:5;opacity:0.3;';
            grip.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M14 14L8 14M14 14L14 8M14 14L6 6" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>';
            grip.addEventListener('mousedown', _startResize);
            w.appendChild(grip);
        }
    }

    /* ============================================================
       PUBLIC API  (exposed on window.FreeWidgets)
       ============================================================ */

    function setLayout(mode) {
        localStorage.setItem(_storageKey('mode'), mode);
        _savePreferenceToServer('chart_layout_mode', mode);

        var containers = document.querySelectorAll('.fw-container');
        containers.forEach(function (container) {
            var widgets = container.querySelectorAll('.fw-widget');
            var gridBtn = document.getElementById('fw-grid-btn');
            var freeBtn = document.getElementById('fw-free-btn');
            var resetBtn = document.getElementById('fw-reset-btn');

            if (gridBtn) gridBtn.className = 'btn btn-' + (mode === 'grid' ? 'primary' : 'secondary') + ' btn-sm';
            if (freeBtn) freeBtn.className = 'btn btn-' + (mode === 'free' ? 'primary' : 'secondary') + ' btn-sm';
            if (resetBtn) resetBtn.style.display = mode === 'free' ? '' : 'none';

            if (mode === 'grid') {
                container.classList.remove('fw-free-mode');
                container.style.position = '';
                container.style.minHeight = '';
                widgets.forEach(function (w) { _cleanWidget(w); });
            } else {
                /* -- Snapshot grid positions BEFORE switching to absolute -- */
                var snapshot = {};
                widgets.forEach(function(w) {
                    var wid = w.getAttribute('data-widget-id') || '';
                    if (!wid) return;
                    var r = w.getBoundingClientRect();
                    var cr = container.getBoundingClientRect();
                    snapshot[wid] = {
                        x: Math.round(r.left - cr.left),
                        y: Math.round(r.top - cr.top),
                        w: Math.round(r.width),
                        h: Math.round(r.height)
                    };
                });

                /* -- NOW switch to free mode -- */
                container.classList.add('fw-free-mode');
                container.style.position = 'relative';
                container.style.minHeight = '800px';

                var saved = _loadPositions();
                if (window._fwServerPositions && typeof window._fwServerPositions === 'object') {
                    var serverPos = window._fwServerPositions;
                    for (var key in serverPos) {
                        if (!saved[key]) saved[key] = serverPos[key];
                    }
                }

                var hasSaved = Object.keys(saved).length > 0;

                widgets.forEach(function (w, idx) {
                    var wid = w.getAttribute('data-widget-id') || ('w' + idx);
                    var pos = saved[wid];
                    var snap = snapshot[wid];

                    w.style.position = 'absolute';
                    if (pos) {
                        w.style.left = pos.x + 'px';
                        w.style.top = pos.y + 'px';
                        w.style.width = pos.w + 'px';
                        w.style.height = (pos.h || (snap ? snap.h : 300)) + 'px';
                        if (pos.z) w.style.zIndex = pos.z;
                    } else if (snap) {
                        /* Grid snapshot — zero visual change on first Free click */
                        w.style.left = snap.x + 'px';
                        w.style.top = snap.y + 'px';
                        w.style.width = snap.w + 'px';
                        w.style.height = snap.h + 'px';
                    } else {
                        /* Fallback for dynamically added widgets */
                        var cw = container.offsetWidth || 900;
                        w.style.left = '0px';
                        w.style.top = '0px';
                        w.style.width = Math.round((cw - 40) / 3) + 'px';
                        w.style.height = '300px';
                    }
                    w.style.zIndex = w.style.zIndex || '1';
                    _decorateWidget(w);
                });

                /* Save snapshot positions so they persist across refresh */
                if (!hasSaved) {
                    _savePositions(container);
                    _savePositionsToServer(container);
                }

                _updateMinHeight(container);
            }
        });
    }

    function resetLayout() {
        localStorage.removeItem(_storageKey('pos'));
        _savePreferenceToServer('chart_free_widget_positions', '{}');
        /* Switch to grid first so snapshot captures clean layout */
        setLayout('grid');
        setTimeout(function() { setLayout('free'); }, 50);
    }

    function bringForward(widget) {
        var container = widget.closest('.fw-container');
        if (container) {
            _bringToFront(widget, container);
            _savePositions(container);
        }
    }

    function sendBackward(widget) {
        var container = widget.closest('.fw-container');
        if (container) {
            _sendBackward(widget, container);
            _savePositions(container);
        }
    }

    /* ---- Widget Settings ---- */
    var _settingsDD = null;
    var _settingsWidget = null;

    function _loadSettings() {
        try { return JSON.parse(localStorage.getItem(_storageKey('settings')) || '{}'); }
        catch (e) { return {}; }
    }

    function _saveWidgetSettings(s) {
        localStorage.setItem(_storageKey('settings'), JSON.stringify(s));
    }

    function _getWidgetId(w) {
        return w.getAttribute('data-widget-id') || w.getAttribute('data-widget') || '';
    }

    function _applySettings(container) {
        var settings = _loadSettings();
        container.querySelectorAll('.fw-widget').forEach(function (w) {
            var wid = _getWidgetId(w);
            var s = settings[wid];
            if (!s) return;
            if (s.title) {
                var t = w.querySelector('.widget-title');
                if (t) t.textContent = s.title;
            }
            if (s.bgColor) w.style.background = s.bgColor;
            if (s.pinned) w.classList.add('fw-pinned');
            if (s.hidden) w.style.display = 'none';
        });
        _updateHiddenBar(container);
    }

    function _createSettingsDD() {
        var dd = document.createElement('div');
        dd.className = 'fw-settings-dd';
        dd.style.cssText = 'display:none;position:fixed;z-index:6000;';
        dd.innerHTML =
            '<button data-action="rename">&#9998; Rename</button>' +
            '<button data-action="pin">&#128204; Pin / Unpin</button>' +
            '<button data-action="hide">&#128065; Hide</button>' +
            '<hr>' +
            '<label class="fw-color-label">' +
            'Background <input type="color" data-action="color" value="#ffffff">' +
            '</label>' +
            '<hr>' +
            '<button data-action="size-s">Size: Small</button>' +
            '<button data-action="size-m">Size: Medium</button>' +
            '<button data-action="size-l">Size: Large</button>' +
            '<hr>' +
            '<button data-action="reset">&#8634; Reset Widget</button>';
        document.body.appendChild(dd);
        dd.addEventListener('click', function (ev) {
            var btn = ev.target.closest('[data-action]');
            if (btn && btn.tagName !== 'INPUT') _handleSettingsAction(btn.getAttribute('data-action'));
        });
        dd.querySelector('input[data-action="color"]').addEventListener('input', function (ev) {
            _handleSettingsAction('color', ev.target.value);
        });
        document.addEventListener('mousedown', function (ev) {
            if (_settingsDD && _settingsDD.style.display !== 'none' &&
                !_settingsDD.contains(ev.target) && !ev.target.classList.contains('fw-gear-btn')) {
                _settingsDD.style.display = 'none';
                _settingsWidget = null;
            }
        });
        return dd;
    }

    function _openSettings(e, widget) {
        e.stopPropagation();
        if (!_settingsDD) _settingsDD = _createSettingsDD();
        _settingsWidget = widget;
        var rect = e.target.getBoundingClientRect();
        _settingsDD.style.top = (rect.bottom + 4) + 'px';
        _settingsDD.style.left = Math.max(0, rect.right - 200) + 'px';
        _settingsDD.style.display = 'block';
        var pinBtn = _settingsDD.querySelector('[data-action="pin"]');
        if (pinBtn) pinBtn.innerHTML = widget.classList.contains('fw-pinned') ? '&#128204; Unpin' : '&#128204; Pin';
        var ci = _settingsDD.querySelector('input[data-action="color"]');
        if (ci) {
            var ws = _loadSettings()[_getWidgetId(widget)];
            ci.value = (ws && ws.bgColor) || '#ffffff';
        }
    }

    function _handleSettingsAction(action, value) {
        if (!_settingsWidget) return;
        var wid = _getWidgetId(_settingsWidget);
        var settings = _loadSettings();
        if (!settings[wid]) settings[wid] = {};
        var container = _settingsWidget.closest('.fw-container');

        switch (action) {
            case 'rename':
                var te = _settingsWidget.querySelector('.widget-title');
                if (!te) break;
                var nv = prompt('Rename widget:', te.textContent);
                if (nv && nv.trim()) {
                    te.textContent = nv.trim();
                    settings[wid].title = nv.trim();
                    _saveWidgetSettings(settings);
                }
                break;
            case 'pin':
                var p = !_settingsWidget.classList.contains('fw-pinned');
                _settingsWidget.classList.toggle('fw-pinned', p);
                settings[wid].pinned = p;
                _saveWidgetSettings(settings);
                break;
            case 'hide':
                _settingsWidget.style.display = 'none';
                settings[wid].hidden = true;
                _saveWidgetSettings(settings);
                if (container) _updateHiddenBar(container);
                break;
            case 'color':
                _settingsWidget.style.background = value;
                settings[wid].bgColor = value;
                _saveWidgetSettings(settings);
                return; /* keep dropdown open while picking */
            case 'size-s':
                _settingsWidget.style.width = '280px';
                _settingsWidget.style.height = '200px';
                if (container) { _resolveOverlaps(container); _compactGaps(container); _savePositions(container); }
                break;
            case 'size-m':
                _settingsWidget.style.width = '400px';
                _settingsWidget.style.height = '350px';
                if (container) { _resolveOverlaps(container); _compactGaps(container); _savePositions(container); }
                break;
            case 'size-l':
                _settingsWidget.style.width = '600px';
                _settingsWidget.style.height = '500px';
                if (container) { _resolveOverlaps(container); _compactGaps(container); _savePositions(container); }
                break;
            case 'reset':
                delete settings[wid];
                _saveWidgetSettings(settings);
                _settingsWidget.style.background = '';
                _settingsWidget.classList.remove('fw-pinned');
                var ot = _settingsWidget.querySelector('.widget-title');
                if (ot && ot.getAttribute('data-original-title'))
                    ot.textContent = ot.getAttribute('data-original-title');
                break;
        }
        _settingsDD.style.display = 'none';
        _settingsWidget = null;
    }

    function _updateHiddenBar(container) {
        var bar = container.querySelector('.fw-hidden-bar');
        if (!bar) {
            bar = document.createElement('div');
            bar.className = 'fw-hidden-bar';
            container.insertBefore(bar, container.firstChild);
        }
        bar.innerHTML = '<span style="color:var(--text-secondary);font-weight:500;">Hidden:</span>';
        var settings = _loadSettings();
        var any = false;
        container.querySelectorAll('.fw-widget').forEach(function (w) {
            var wid = _getWidgetId(w);
            if (settings[wid] && settings[wid].hidden) {
                any = true;
                var chip = document.createElement('span');
                chip.className = 'fw-hidden-chip';
                var t = w.querySelector('.widget-title');
                chip.textContent = (t ? t.textContent : wid) + ' \u2715';
                chip.onclick = function () {
                    w.style.display = '';
                    settings[wid].hidden = false;
                    _saveWidgetSettings(settings);
                    _updateHiddenBar(container);
                };
                bar.appendChild(chip);
            }
        });
        bar.style.display = any ? '' : 'none';
    }

    function _injectGearIcons(container) {
        container.querySelectorAll('.fw-widget').forEach(function (w) {
            var controls = w.querySelector('.widget-controls');
            if (!controls || controls.querySelector('.fw-gear-btn')) return;
            var t = w.querySelector('.widget-title');
            if (t && !t.getAttribute('data-original-title'))
                t.setAttribute('data-original-title', t.textContent);
            var gear = document.createElement('button');
            gear.className = 'widget-btn fw-gear-btn';
            gear.innerHTML = '&#9881;';
            gear.title = 'Widget settings';
            gear.addEventListener('click', function (ev) { _openSettings(ev, w); });
            controls.insertBefore(gear, controls.firstChild);
        });
    }

    /* ---- Widget Management Panel (UX-18) ---- */
    var _mgmtPanel = null;

    function _createMgmtPanel() {
        var panel = document.createElement('div');
        panel.className = 'fw-mgmt-panel';
        panel.style.cssText = 'display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:7000;' +
            'background:var(--bg-surface,#fff);border-radius:12px;box-shadow:0 8px 40px rgba(0,0,0,0.25);' +
            'width:400px;max-width:95vw;max-height:80vh;display:none;flex-direction:column;overflow:hidden;';
        panel.innerHTML =
            '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border,#e2e8f0);">' +
            '<h3 style="margin:0;font-size:16px;">Manage Widgets</h3>' +
            '<button class="btn btn-outline btn-sm fw-mgmt-close" style="padding:2px 8px;">✕</button></div>' +
            '<div class="fw-mgmt-list" style="flex:1;overflow-y:auto;padding:8px 0;"></div>' +
            '<div style="padding:12px 20px;border-top:1px solid var(--border,#e2e8f0);display:flex;gap:8px;">' +
            '<button class="btn btn-outline btn-sm fw-mgmt-show-all">Show All</button>' +
            '<button class="btn btn-outline btn-sm fw-mgmt-reset-order">Reset Order</button></div>';
        document.body.appendChild(panel);

        panel.querySelector('.fw-mgmt-close').addEventListener('click', function () {
            panel.style.display = 'none';
            _mgmtBackdrop.style.display = 'none';
        });
        panel.querySelector('.fw-mgmt-show-all').addEventListener('click', function () {
            var settings = _loadSettings();
            var container = document.querySelector('.fw-container');
            if (!container) return;
            container.querySelectorAll('.fw-widget').forEach(function (w) {
                var wid = _getWidgetId(w);
                w.style.display = '';
                if (settings[wid]) settings[wid].hidden = false;
            });
            _saveWidgetSettings(settings);
            if (container) _updateHiddenBar(container);
            _populateMgmtList(container);
        });
        panel.querySelector('.fw-mgmt-reset-order').addEventListener('click', function () {
            var container = document.querySelector('.fw-container');
            if (!container) return;
            localStorage.removeItem(_storageKey('widget_order'));
            _populateMgmtList(container);
        });
        return panel;
    }

    var _mgmtBackdrop = null;

    function _ensureBackdrop() {
        if (!_mgmtBackdrop) {
            _mgmtBackdrop = document.createElement('div');
            _mgmtBackdrop.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:6500;';
            document.body.appendChild(_mgmtBackdrop);
            _mgmtBackdrop.addEventListener('click', function () {
                if (_mgmtPanel) _mgmtPanel.style.display = 'none';
                _mgmtBackdrop.style.display = 'none';
            });
        }
        return _mgmtBackdrop;
    }

    function _populateMgmtList(container) {
        if (!_mgmtPanel) return;
        var list = _mgmtPanel.querySelector('.fw-mgmt-list');
        list.innerHTML = '';
        var settings = _loadSettings();
        var widgets = container.querySelectorAll('.fw-widget');
        widgets.forEach(function (w) {
            var wid = _getWidgetId(w);
            var titleEl = w.querySelector('.widget-title');
            var title = (titleEl ? titleEl.textContent : wid) || wid;
            var isHidden = !!(settings[wid] && settings[wid].hidden);
            var row = document.createElement('div');
            row.className = 'fw-mgmt-row';
            row.setAttribute('data-wid', wid);
            row.style.cssText = 'display:flex;align-items:center;gap:10px;padding:8px 20px;border-bottom:1px solid var(--border-color-light,#f1f5f9);cursor:grab;';
            row.draggable = true;
            row.innerHTML =
                '<span style="color:var(--text-secondary);cursor:grab;">⠿</span>' +
                '<label style="flex:1;display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;">' +
                '<input type="checkbox" class="fw-mgmt-vis" ' + (isHidden ? '' : 'checked') + ' style="width:16px;height:16px;">' +
                '<span>' + title + '</span></label>' +
                '<span style="font-size:11px;color:var(--text-secondary);">' + Math.round(w.offsetWidth) + '×' + Math.round(w.offsetHeight) + '</span>';

            // Toggle visibility
            row.querySelector('.fw-mgmt-vis').addEventListener('change', function (ev) {
                var vis = ev.target.checked;
                if (!settings[wid]) settings[wid] = {};
                settings[wid].hidden = !vis;
                w.style.display = vis ? '' : 'none';
                _saveWidgetSettings(settings);
                _updateHiddenBar(container);
            });

            // Drag reorder within list
            row.addEventListener('dragstart', function (ev) {
                ev.dataTransfer.setData('text/plain', wid);
                row.style.opacity = '0.5';
            });
            row.addEventListener('dragend', function () { row.style.opacity = '1'; });
            row.addEventListener('dragover', function (ev) { ev.preventDefault(); });
            row.addEventListener('drop', function (ev) {
                ev.preventDefault();
                var fromWid = ev.dataTransfer.getData('text/plain');
                if (fromWid === wid) return;
                var fromRow = list.querySelector('[data-wid="' + fromWid + '"]');
                if (!fromRow) return;
                list.insertBefore(fromRow, row);
                _saveMgmtOrder(list, container);
            });
            list.appendChild(row);
        });
    }

    function _saveMgmtOrder(list, container) {
        var order = [];
        list.querySelectorAll('.fw-mgmt-row').forEach(function (r) {
            order.push(r.getAttribute('data-wid'));
        });
        localStorage.setItem(_storageKey('widget_order'), JSON.stringify(order));
        // Reorder actual widgets in DOM
        order.forEach(function (wid) {
            var w = container.querySelector('[data-widget-id="' + wid + '"]');
            if (w) container.appendChild(w);
        });
    }

    function _applyWidgetOrder(container) {
        var orderStr = localStorage.getItem(_storageKey('widget_order'));
        if (!orderStr) return;
        try {
            var order = JSON.parse(orderStr);
            order.forEach(function (wid) {
                var w = container.querySelector('[data-widget-id="' + wid + '"]');
                if (w) container.appendChild(w);
            });
        } catch (e) { /* ignore */ }
    }

    function openMgmtPanel() {
        var container = document.querySelector('.fw-container');
        if (!container) return;
        if (!_mgmtPanel) _mgmtPanel = _createMgmtPanel();
        _ensureBackdrop();
        _populateMgmtList(container);
        _mgmtBackdrop.style.display = 'block';
        _mgmtPanel.style.display = 'flex';
    }

    function _injectMgmtButton(container) {
        var existing = container.querySelector('.fw-mgmt-btn');
        if (existing) return;
        /* Skip injection if a static Manage button already exists in page header */
        if (document.querySelector('.page-header__actions .btn[onclick*="openManagePanel"]')) return;
        var btn = document.createElement('button');
        btn.className = 'btn btn-outline btn-sm fw-mgmt-btn';
        btn.innerHTML = '⚙ Manage Widgets';
        btn.style.cssText = 'position:absolute;top:8px;right:8px;z-index:50;font-size:12px;';
        btn.addEventListener('click', openMgmtPanel);
        container.style.position = 'relative';
        container.insertBefore(btn, container.firstChild);
    }

    /* ---- Auto-initialise ---- */
    document.addEventListener('DOMContentLoaded', function () {
        var containers = document.querySelectorAll('.fw-container');
        if (!containers.length) return;
        containers.forEach(function (c) {
            _injectGearIcons(c);
            _applySettings(c);
            _applyWidgetOrder(c);
            _injectMgmtButton(c);
        });
        var mode = _getMode();
        setTimeout(function () { setLayout(mode); }, 0);
    });

    /* Expose */
    window.FreeWidgets = {
        setLayout: setLayout,
        resetLayout: resetLayout,
        bringForward: bringForward,
        sendBackward: sendBackward,
        openManagePanel: openMgmtPanel
    };
})();
