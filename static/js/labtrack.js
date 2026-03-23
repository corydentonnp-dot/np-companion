/**
 * CareCompanion — Lab Tracker Autocomplete (UX-14)
 * File: static/js/labtrack.js
 *
 * Fuzzy-match autocomplete for the lab name input field.
 * Loads lab data from /data/lab_cache.json and matches on
 * name, abbreviation, and LOINC code.
 */
(function () {
    'use strict';

    var _labCache = null;
    var _activeIndex = -1;

    /* ---- Load lab cache ---- */
    function loadCache(cb) {
        if (_labCache) return cb(_labCache);
        fetch('/api/lab-cache')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _labCache = data;
                cb(data);
            })
            .catch(function () {
                _labCache = { labs: [], panels: {} };
                cb(_labCache);
            });
    }

    /* ---- Fuzzy match scoring ---- */
    function fuzzyScore(query, text) {
        if (!text) return 0;
        var q = query.toLowerCase();
        var t = text.toLowerCase();
        if (t === q) return 100;
        if (t.startsWith(q)) return 90;
        if (t.indexOf(q) >= 0) return 70;

        // Character-by-character fuzzy
        var qi = 0;
        var score = 0;
        for (var ti = 0; ti < t.length && qi < q.length; ti++) {
            if (t[ti] === q[qi]) {
                score += (ti === 0 || t[ti - 1] === ' ' || t[ti - 1] === '(') ? 3 : 1;
                qi++;
            }
        }
        return qi === q.length ? Math.min(60, score) : 0;
    }

    function searchLabs(query) {
        if (!_labCache || !query || query.length < 1) return [];
        var q = query.trim();
        var results = [];

        _labCache.labs.forEach(function (lab) {
            var score = Math.max(
                fuzzyScore(q, lab.name),
                fuzzyScore(q, lab.abbr) * 1.1,
                fuzzyScore(q, lab.loinc) * 0.9
            );
            if (score > 0) {
                results.push({ lab: lab, score: score });
            }
        });

        results.sort(function (a, b) { return b.score - a.score; });
        return results.slice(0, 12);
    }

    /* ---- Dropdown rendering ---- */
    function renderDropdown(el, results, onSelect) {
        el.innerHTML = '';
        if (results.length === 0) {
            el.style.display = 'none';
            return;
        }
        _activeIndex = -1;
        results.forEach(function (r, idx) {
            var item = document.createElement('div');
            item.className = 'lab-autocomplete-item';
            item.setAttribute('data-index', idx);
            var rangeHint = '';
            if (r.lab.low != null && r.lab.high != null) {
                rangeHint = ' <span style="color:var(--text-muted);font-size:11px;">(' + r.lab.low + '–' + r.lab.high + ' ' + (r.lab.unit || '') + ')</span>';
            }
            var panelHint = r.lab.panels && r.lab.panels.length > 0
                ? ' <span class="badge" style="font-size:9px;background:var(--bg-hover);padding:1px 4px;">' + r.lab.panels.join(', ') + '</span>'
                : '';
            item.innerHTML =
                '<span style="font-weight:500;">' + escHtml(r.lab.name) + '</span>' +
                ' <span style="color:var(--text-secondary);font-size:12px;">' + escHtml(r.lab.abbr) + '</span>' +
                rangeHint + panelHint +
                '<span class="lab-ac-info" data-lab="' + escHtml(r.lab.name) + '" title="View reference" style="margin-left:auto;padding:2px 5px;font-size:12px;color:var(--text-secondary);cursor:pointer;opacity:0.6;flex-shrink:0;">ℹ</span>';
            item.querySelector('.lab-ac-info').addEventListener('mousedown', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var labName = this.getAttribute('data-lab');
                if (window.openLabDetail) window.openLabDetail(labName);
                else if (window.openLabReference) window.openLabReference(labName);
            });
            item.addEventListener('mousedown', function (e) {
                e.preventDefault();
                onSelect(r.lab);
            });
            el.appendChild(item);
        });
        el.style.display = 'block';
    }

    function escHtml(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function highlightItem(dropdown, index) {
        var items = dropdown.querySelectorAll('.lab-autocomplete-item');
        items.forEach(function (el, i) {
            el.classList.toggle('lab-autocomplete-item--active', i === index);
        });
    }

    /* ---- Auto-fill thresholds ---- */
    function fillThresholds(lab) {
        var fields = {
            critical_low: lab.critical_low,
            alert_low: lab.low,
            alert_high: lab.high,
            critical_high: lab.critical_high
        };
        Object.keys(fields).forEach(function (name) {
            var input = document.querySelector('input[name="' + name + '"]');
            if (input && fields[name] != null) {
                input.value = fields[name];
            }
        });
    }

    /* ---- Init ---- */
    function init() {
        var input = document.getElementById('lab-name-input');
        var dropdown = document.getElementById('lab-name-dropdown');
        if (!input || !dropdown) return;

        var debounce = null;

        input.addEventListener('input', function () {
            clearTimeout(debounce);
            debounce = setTimeout(function () {
                loadCache(function () {
                    var results = searchLabs(input.value);
                    renderDropdown(dropdown, results, function (lab) {
                        input.value = lab.name;
                        dropdown.style.display = 'none';
                        fillThresholds(lab);
                    });
                });
            }, 100);
        });

        input.addEventListener('keydown', function (e) {
            var items = dropdown.querySelectorAll('.lab-autocomplete-item');
            if (!items.length || dropdown.style.display === 'none') return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                _activeIndex = Math.min(_activeIndex + 1, items.length - 1);
                highlightItem(dropdown, _activeIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                _activeIndex = Math.max(_activeIndex - 1, 0);
                highlightItem(dropdown, _activeIndex);
            } else if (e.key === 'Enter' && _activeIndex >= 0) {
                e.preventDefault();
                items[_activeIndex].dispatchEvent(new MouseEvent('mousedown'));
            } else if (e.key === 'Escape') {
                dropdown.style.display = 'none';
            }
        });

        input.addEventListener('blur', function () {
            setTimeout(function () { dropdown.style.display = 'none'; }, 150);
        });

        input.addEventListener('focus', function () {
            if (input.value.length >= 1) {
                loadCache(function () {
                    var results = searchLabs(input.value);
                    renderDropdown(dropdown, results, function (lab) {
                        input.value = lab.name;
                        dropdown.style.display = 'none';
                        fillThresholds(lab);
                    });
                });
            }
        });
    }

    /* Clear cached data (called after edits) */
    function clearCache() { _labCache = null; }

    /* Expose for external use */
    window.LabAutocomplete = { init: init, searchLabs: searchLabs, _clearCache: clearCache };

    /* ==================================================================
     * UX-15: Panel Component Badges
     * Adds colored dot badges for each component of a lab panel when the
     * lab name column has a panel_name data attribute.
     * ================================================================ */
    function decoratePanelBadges() {
        loadCache(function (cache) {
            if (!cache || !cache.panels) return;
            var slots = document.querySelectorAll('.panel-badges-slot');
            slots.forEach(function (slot) {
                var td = slot.closest('td');
                if (!td) return;
                var panelName = (td.getAttribute('data-panel-name') || '').trim();
                if (!panelName) return;

                // Find the panel in cache
                var components = cache.panels[panelName];
                if (!components || !components.length) return;

                // Get current lab name so we can highlight it
                var currentLab = (td.getAttribute('data-lab-name') || '').trim().toLowerCase();

                // Build badge HTML
                var html = '<span class="panel-comp-badges" title="' + panelName + ' panel components">';
                components.forEach(function (compName) {
                    var labData = null;
                    for (var i = 0; i < cache.labs.length; i++) {
                        if (cache.labs[i].name.toLowerCase() === compName.toLowerCase() ||
                            (cache.labs[i].abbr && cache.labs[i].abbr.toLowerCase() === compName.toLowerCase())) {
                            labData = cache.labs[i];
                            break;
                        }
                    }
                    var isCurrent = compName.toLowerCase() === currentLab;
                    var abbr = labData ? (labData.abbr || compName.substring(0, 3)) : compName.substring(0, 3);
                    html += '<span class="panel-comp-dot' + (isCurrent ? ' panel-comp-dot--current' : '') + '" title="' + compName + '">' + abbr + '</span>';
                });
                html += '</span>';
                slot.innerHTML = html;
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { init(); decoratePanelBadges(); });
    } else {
        init();
        decoratePanelBadges();
    }
})();
