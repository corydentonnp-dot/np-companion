/**
 * CareCompanion — Schedule Grid View (UX-9)
 * File: static/js/schedule_grid.js
 *
 * Renders a 15-minute time-block grid (7 AM - 6 PM) as an alternative
 * to the flat schedule table. Supports drag-and-drop to move appointments.
 */
(function () {
    'use strict';

    var START_HOUR = 7;
    var END_HOUR = 18; // 6 PM
    var SLOT_MINUTES = 15;
    var SLOT_HEIGHT = 36; // px per 15-min slot
    var TOTAL_SLOTS = (END_HOUR - START_HOUR) * (60 / SLOT_MINUTES); // 44 slots

    /* ---- State ---- */
    var _appointments = [];
    var _dragAppt = null;

    /* ---- Helpers ---- */
    function timeToSlot(timeStr) {
        if (!timeStr) return 0;
        // Handle "9:30 AM", "14:00", "2:15 PM" etc.
        var parts = timeStr.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i);
        if (!parts) return 0;
        var h = parseInt(parts[1], 10);
        var m = parseInt(parts[2], 10);
        if (parts[3]) {
            var ampm = parts[3].toUpperCase();
            if (ampm === 'PM' && h < 12) h += 12;
            if (ampm === 'AM' && h === 12) h = 0;
        }
        return Math.max(0, Math.round(((h - START_HOUR) * 60 + m) / SLOT_MINUTES));
    }

    function slotToTime(slot) {
        var totalMin = slot * SLOT_MINUTES + START_HOUR * 60;
        var h = Math.floor(totalMin / 60);
        var m = totalMin % 60;
        var ampm = h >= 12 ? 'PM' : 'AM';
        var dh = h > 12 ? h - 12 : (h === 0 ? 12 : h);
        return dh + ':' + ('0' + m).slice(-2) + ' ' + ampm;
    }

    function slotTo24(slot) {
        var totalMin = slot * SLOT_MINUTES + START_HOUR * 60;
        var h = Math.floor(totalMin / 60);
        var m = totalMin % 60;
        return ('0' + h).slice(-2) + ':' + ('0' + m).slice(-2);
    }

    function escHtml(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function durationSlots(minutes) {
        return Math.max(1, Math.round(minutes / SLOT_MINUTES));
    }

    /* ---- Build grid ---- */
    function buildGrid(container) {
        container.innerHTML = '';
        container.className = 'sched-grid';

        // Time labels column + appointment column
        for (var s = 0; s < TOTAL_SLOTS; s++) {
            var totalMin = s * SLOT_MINUTES + START_HOUR * 60;
            var isHour = totalMin % 60 === 0;

            // Time label cell
            var label = document.createElement('div');
            label.className = 'sched-grid__label' + (isHour ? ' sched-grid__label--hour' : '');
            label.textContent = isHour ? slotToTime(s) : '';
            label.style.gridRow = (s + 1) + ' / ' + (s + 2);
            label.style.gridColumn = '1';
            container.appendChild(label);

            // Slot cell (droppable)
            var cell = document.createElement('div');
            cell.className = 'sched-grid__slot' + (isHour ? ' sched-grid__slot--hour' : '');
            cell.setAttribute('data-slot', s);
            cell.style.gridRow = (s + 1) + ' / ' + (s + 2);
            cell.style.gridColumn = '2';
            cell.addEventListener('dragover', onDragOver);
            cell.addEventListener('drop', onDrop);
            cell.addEventListener('dragenter', onDragEnter);
            cell.addEventListener('dragleave', onDragLeave);
            container.appendChild(cell);
        }

        // Place appointments
        _appointments.forEach(function (appt) {
            placeAppointment(container, appt);
        });
    }

    function placeAppointment(container, appt) {
        var slot = timeToSlot(appt.time);
        var span = durationSlots(appt.duration_minutes || 15);

        var card = document.createElement('div');
        card.className = 'sched-grid__appt';
        if (appt.is_new_patient) card.classList.add('sched-grid__appt--new');
        card.setAttribute('draggable', 'true');
        card.setAttribute('data-appt-id', appt.id);
        card.style.gridRow = (slot + 1) + ' / ' + (slot + 1 + span);
        card.style.gridColumn = '2';

        var mrnDisplay = appt.patient_mrn ? '••' + appt.patient_mrn.slice(-4) : '';
        card.innerHTML =
            '<div class="sched-grid__appt-time">' + escHtml(appt.time) + '</div>' +
            '<div class="sched-grid__appt-name">' +
                (appt.patient_mrn
                    ? '<a href="/patient/' + encodeURIComponent(appt.patient_mrn) + '" style="color:inherit;text-decoration:none;">' + escHtml(appt.patient_name) + '</a>'
                    : escHtml(appt.patient_name)) +
                (appt.is_new_patient ? ' <span class="badge badge--new-patient" style="font-size:9px;">NEW</span>' : '') +
            '</div>' +
            '<div class="sched-grid__appt-meta">' +
                escHtml(appt.visit_type) +
                (appt.reason ? ' — ' + escHtml(appt.reason) : '') +
            '</div>' +
            '<div class="sched-grid__appt-mrn">' + mrnDisplay + '</div>';

        card.addEventListener('dragstart', onDragStart);
        card.addEventListener('dragend', onDragEnd);
        container.appendChild(card);
    }

    /* ---- Drag and Drop ---- */
    function onDragStart(e) {
        var id = e.target.getAttribute('data-appt-id');
        _dragAppt = _appointments.find(function (a) { return String(a.id) === id; });
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', id);
        e.target.classList.add('sched-grid__appt--dragging');
    }

    function onDragEnd(e) {
        e.target.classList.remove('sched-grid__appt--dragging');
        // Remove all highlight states
        document.querySelectorAll('.sched-grid__slot--hover').forEach(function (el) {
            el.classList.remove('sched-grid__slot--hover');
        });
        _dragAppt = null;
    }

    function onDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function onDragEnter(e) {
        e.preventDefault();
        if (e.currentTarget.classList.contains('sched-grid__slot')) {
            e.currentTarget.classList.add('sched-grid__slot--hover');
        }
    }

    function onDragLeave(e) {
        if (e.currentTarget.classList.contains('sched-grid__slot')) {
            e.currentTarget.classList.remove('sched-grid__slot--hover');
        }
    }

    function onDrop(e) {
        e.preventDefault();
        var slotEl = e.currentTarget;
        slotEl.classList.remove('sched-grid__slot--hover');
        var newSlot = parseInt(slotEl.getAttribute('data-slot'), 10);
        var apptId = e.dataTransfer.getData('text/plain');
        if (!apptId || isNaN(newSlot)) return;

        var newTime = slotTo24(newSlot);

        // Persist to server
        fetch('/api/schedule/' + apptId + '/move', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_time: newTime })
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (d.success) {
                // Update local data and rebuild
                var appt = _appointments.find(function (a) { return String(a.id) === apptId; });
                if (appt) appt.time = slotToTime(newSlot);
                var grid = document.getElementById('schedule-grid-view');
                if (grid) buildGrid(grid);
            } else {
                showError && showError(d.error || 'Could not move appointment');
            }
        })
        .catch(function () {
            showError && showError('Failed to move appointment');
        });
    }

    /* ---- Toggle between table and grid ---- */
    function toggleView(mode) {
        var tableWrap = document.getElementById('schedule-table-view');
        var gridWrap = document.getElementById('schedule-grid-view');
        var tableBtn = document.getElementById('sched-view-table');
        var gridBtn = document.getElementById('sched-view-grid');
        if (!tableWrap || !gridWrap) return;

        localStorage.setItem('cc_sched_view', mode);

        if (mode === 'grid') {
            tableWrap.style.display = 'none';
            gridWrap.style.display = 'grid';
            if (tableBtn) tableBtn.className = 'btn btn-sm btn-secondary';
            if (gridBtn) gridBtn.className = 'btn btn-sm btn-primary';
            buildGrid(gridWrap);
        } else {
            tableWrap.style.display = '';
            gridWrap.style.display = 'none';
            if (tableBtn) tableBtn.className = 'btn btn-sm btn-primary';
            if (gridBtn) gridBtn.className = 'btn btn-sm btn-secondary';
        }
    }

    /* ---- Init ---- */
    function init(appointments) {
        _appointments = appointments || [];
        var saved = localStorage.getItem('cc_sched_view') || 'table';
        toggleView(saved);
    }

    /* Expose */
    window.ScheduleGrid = {
        init: init,
        toggleView: toggleView
    };
})();
