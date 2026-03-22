/**
 * calculator_charts.js — Phase 35.2
 * SVG-based sparkline chart for score history.
 * No external dependencies. Fetches from /patient/<mrn>/score-history/<key>.
 */

(function () {
    'use strict';

    // Threshold bands per calculator key  { key: [{min, max, color, label}] }
    var THRESHOLDS = {
        bmi: [
            { min: 18.5, max: 24.9, color: 'rgba(39,174,96,0.15)', label: 'Normal' },
            { min: 25,   max: 29.9, color: 'rgba(243,156,18,0.15)', label: 'Overweight' },
            { min: 30,   max: 39.9, color: 'rgba(231,76,60,0.15)',  label: 'Obese I-II' },
            { min: 40,   max: null, color: 'rgba(192,57,43,0.25)',  label: 'Obese III' },
        ],
        prevent: [
            { min: 0,    max: 7.4,  color: 'rgba(39,174,96,0.15)', label: 'Low' },
            { min: 7.5,  max: 19.9, color: 'rgba(243,156,18,0.15)', label: 'Borderline' },
            { min: 20,   max: null, color: 'rgba(231,76,60,0.20)',  label: 'High' },
        ],
        ldl: [
            { min: 0,    max: 129,  color: 'rgba(39,174,96,0.15)', label: 'Normal' },
            { min: 130,  max: 159,  color: 'rgba(243,156,18,0.15)', label: 'Borderline' },
            { min: 160,  max: 189,  color: 'rgba(231,76,60,0.15)',  label: 'High' },
            { min: 190,  max: null, color: 'rgba(192,57,43,0.25)',  label: 'Very High' },
        ],
        pack_years: [
            { min: 0,    max: 19.9, color: 'rgba(39,174,96,0.15)', label: 'Low' },
            { min: 20,   max: null, color: 'rgba(231,76,60,0.20)',  label: 'High (LDCT eligible)' },
        ],
    };

    var UNITS = { bmi: 'kg/m²', prevent: '%', ldl: 'mg/dL', ldl_calculated: 'mg/dL', pack_years: 'pack-yrs' };

    function formatDate(iso) {
        if (!iso) return '';
        var d = new Date(iso);
        return (d.getMonth() + 1) + '/' + d.getDate() + '/' + String(d.getFullYear()).slice(2);
    }

    function buildSVG(records, key) {
        var W = 480, H = 120, PAD_L = 40, PAD_R = 16, PAD_T = 16, PAD_B = 28;
        var plotW = W - PAD_L - PAD_R;
        var plotH = H - PAD_T - PAD_B;

        if (!records || records.length === 0) {
            return '<p style="font-size:12px;color:var(--text-secondary,#888);text-align:center;padding:24px 0;">No history available.</p>';
        }

        var vals = records.map(function (r) { return r.score_value; }).filter(function (v) { return v !== null && v !== undefined; });
        if (vals.length === 0) {
            return '<p style="font-size:12px;color:var(--text-secondary,#888);text-align:center;padding:24px 0;">No numeric scores recorded.</p>';
        }

        var minV = Math.min.apply(null, vals);
        var maxV = Math.max.apply(null, vals);
        var bands = THRESHOLDS[key] || [];

        // Expand range to include threshold boundaries
        bands.forEach(function (b) {
            if (b.min !== null && b.min < minV) minV = b.min;
            if (b.max !== null && b.max > maxV) maxV = b.max;
        });

        // Guarantee a visible range
        if (maxV === minV) { minV -= 1; maxV += 1; }

        var range = maxV - minV;
        minV -= range * 0.05;
        maxV += range * 0.05;
        range = maxV - minV;

        function xPx(i) {
            if (records.length === 1) return PAD_L + plotW / 2;
            return PAD_L + (i / (records.length - 1)) * plotW;
        }
        function yPx(v) {
            return PAD_T + plotH - ((v - minV) / range) * plotH;
        }

        var svgParts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;max-width:' + W + 'px;display:block;">'];

        // Band fills
        bands.forEach(function (b) {
            var bandMin = b.min !== null ? b.min : minV - range;
            var bandMax = b.max !== null ? b.max : maxV + range;
            var y1 = yPx(Math.min(bandMax, maxV));
            var y2 = yPx(Math.max(bandMin, minV));
            if (y2 > y1) {
                svgParts.push('<rect x="' + PAD_L + '" y="' + y1 + '" width="' + plotW + '" height="' + (y2 - y1) + '" fill="' + b.color + '"/>');
            }
        });

        // Axes
        svgParts.push('<line x1="' + PAD_L + '" y1="' + PAD_T + '" x2="' + PAD_L + '" y2="' + (PAD_T + plotH) + '" stroke="#555" stroke-width="1"/>');
        svgParts.push('<line x1="' + PAD_L + '" y1="' + (PAD_T + plotH) + '" x2="' + (PAD_L + plotW) + '" y2="' + (PAD_T + plotH) + '" stroke="#555" stroke-width="1"/>');

        // Y-axis labels (min and max)
        svgParts.push('<text x="' + (PAD_L - 4) + '" y="' + (PAD_T + plotH) + '" text-anchor="end" font-size="9" fill="#888">' + minV.toFixed(1) + '</text>');
        svgParts.push('<text x="' + (PAD_L - 4) + '" y="' + (PAD_T + 6) + '" text-anchor="end" font-size="9" fill="#888">' + maxV.toFixed(1) + '</text>');

        // Polyline
        var points = records.map(function (r, i) {
            return xPx(i) + ',' + yPx(r.score_value);
        }).join(' ');
        svgParts.push('<polyline points="' + points + '" fill="none" stroke="#3498db" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>');

        // Data points + x-axis date labels
        records.forEach(function (r, i) {
            var cx = xPx(i), cy = yPx(r.score_value);
            svgParts.push('<circle cx="' + cx + '" cy="' + cy + '" r="4" fill="#3498db" stroke="var(--bg-secondary,#1e1e1e)" stroke-width="1.5">');
            svgParts.push('<title>' + formatDate(r.computed_at) + ': ' + r.score_value + ' ' + (UNITS[key] || '') + '</title>');
            svgParts.push('</circle>');

            // Date label on x-axis (only first and last if many points)
            if (records.length <= 5 || i === 0 || i === records.length - 1) {
                svgParts.push('<text x="' + cx + '" y="' + (H - 4) + '" text-anchor="middle" font-size="9" fill="#888">' + formatDate(r.computed_at) + '</text>');
            }
        });

        svgParts.push('</svg>');
        return svgParts.join('');
    }

    /**
     * Load and render score history chart into a container element.
     * @param {string} mrn - Patient MRN
     * @param {string} key - Calculator key (e.g. 'bmi')
     * @param {string} containerId - ID of the container div
     */
    window.loadScoreHistory = function (mrn, key, containerId) {
        var container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '<p style="font-size:12px;color:var(--text-secondary,#888);text-align:center;padding:24px 0;">Loading&hellip;</p>';

        fetch('/patient/' + encodeURIComponent(mrn) + '/score-history/' + encodeURIComponent(key))
            .then(function (resp) {
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                return resp.json();
            })
            .then(function (data) {
                var records = Array.isArray(data) ? data : (data.history || []);
                // Reverse to chronological order for chart (API returns newest first)
                records = records.slice().reverse();
                container.innerHTML = buildSVG(records, key);

                // Append unit label
                var unit = UNITS[key];
                if (unit) {
                    var lbl = document.createElement('div');
                    lbl.style.cssText = 'font-size:11px;color:var(--text-secondary,#888);text-align:right;margin-top:2px;';
                    lbl.textContent = unit;
                    container.appendChild(lbl);
                }
            })
            .catch(function () {
                container.innerHTML = '<p style="font-size:12px;color:var(--text-secondary,#888);text-align:center;padding:24px 0;">History unavailable.</p>';
            });
    };
})();
