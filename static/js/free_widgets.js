/**
 * NP Companion — Free-Form Widget Positioning
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
        try { return JSON.parse(localStorage.getItem(_storageKey('pos')) || '{}'); }
        catch (e) { return {}; }
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
        return localStorage.getItem(_storageKey('mode')) || 'free';
    }

    function _snap(v) { return Math.round(v / SNAP_SIZE) * SNAP_SIZE; }

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
    }

    function _endDrag() {
        if (_dragState) {
            var h = _dragState.el.querySelector('.fw-drag-handle');
            if (h) { h.style.opacity = '0'; h.style.height = '6px'; }
            _savePositions(_dragState.container);
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
            _savePositions(_resizeState.container);
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
            handle.title = 'Drag to move';
            handle.innerHTML = '&#9776;';
            handle.style.cssText = 'position:absolute;top:0;left:0;right:0;height:6px;cursor:move;' +
                'background:var(--color-teal);opacity:0;transition:opacity .15s,height .15s;z-index:5;' +
                'border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center;' +
                'font-size:10px;color:#fff;';
            handle.addEventListener('mouseenter', function () { handle.style.opacity = '0.7'; handle.style.height = '14px'; });
            handle.addEventListener('mouseleave', function () { if (!_dragState) { handle.style.opacity = '0'; handle.style.height = '6px'; } });
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
                container.classList.add('fw-free-mode');
                container.style.position = 'relative';
                container.style.minHeight = '800px';

                var saved = _loadPositions();

                widgets.forEach(function (w, idx) {
                    var wid = w.getAttribute('data-widget-id') || ('w' + idx);
                    var pos = saved[wid];

                    w.style.position = 'absolute';
                    if (pos) {
                        w.style.left = pos.x + 'px';
                        w.style.top = pos.y + 'px';
                        w.style.width = pos.w + 'px';
                        if (pos.h) w.style.height = pos.h + 'px';
                        if (pos.z) w.style.zIndex = pos.z;
                    } else {
                        var col = idx % 3;
                        var row = Math.floor(idx / 3);
                        var cw = container.offsetWidth || 900;
                        var defW = Math.round((cw - 40) / 3);
                        w.style.left = (col * (defW + 16)) + 'px';
                        w.style.top = (row * 300) + 'px';
                        w.style.width = defW + 'px';
                    }
                    w.style.zIndex = w.style.zIndex || 1;
                    _decorateWidget(w);
                });
                _updateMinHeight(container);
            }
        });
    }

    function resetLayout() {
        localStorage.removeItem(_storageKey('pos'));
        setLayout('free');
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
                if (container) _savePositions(container);
                break;
            case 'size-m':
                _settingsWidget.style.width = '400px';
                _settingsWidget.style.height = '350px';
                if (container) _savePositions(container);
                break;
            case 'size-l':
                _settingsWidget.style.width = '600px';
                _settingsWidget.style.height = '500px';
                if (container) _savePositions(container);
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

    /* ---- Auto-initialise ---- */
    document.addEventListener('DOMContentLoaded', function () {
        var containers = document.querySelectorAll('.fw-container');
        if (!containers.length) return;
        containers.forEach(function (c) {
            _injectGearIcons(c);
            _applySettings(c);
        });
        var mode = _getMode();
        setTimeout(function () { setLayout(mode); }, 0);
    });

    /* Expose */
    window.FreeWidgets = {
        setLayout: setLayout,
        resetLayout: resetLayout,
        bringForward: bringForward,
        sendBackward: sendBackward
    };
})();
