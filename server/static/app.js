/**
 * Event Concierge - Tactical Frontend Orchestration
 * Optimized for high-performance rendering and WCAG 2.1 AA+ accessibility.
 */

let map;
let eventData = [];
let lastAlertState = null;
let lastItineraryState = null;

/**
 * State Management & Accessibility Utilities
 */
function isStateSame(oldState, newState) {
    return JSON.stringify(oldState) === JSON.stringify(newState);
}

function announceState(message, priority = 'polite') {
    const announcer = document.getElementById('live-feed');
    if (announcer) {
        const span = document.createElement('span');
        span.textContent = message;
        span.className = 'sr-only'; // Visually hidden but read by SR
        announcer.appendChild(span);
        setTimeout(() => span.remove(), 1000); 
    }
}

function clearErrorSummary() {
    const summary = document.getElementById('error-summary');
    summary.style.display = 'none';
    summary.innerHTML = '';
    
    document.querySelectorAll('[aria-invalid="true"]').forEach(el => {
        el.removeAttribute('aria-invalid');
        el.classList.remove('input-error');
    });
}

function renderErrorSummary(errors) {
    const summary = document.getElementById('error-summary');
    summary.innerHTML = `<h2 id="summary-title">${errors.length} errors found in your plan</h2><ul id="error-list"></ul>`;
    summary.style.display = 'block';
    
    const list = summary.querySelector('ul');
    errors.forEach(err => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `#${err.field}`;
        link.textContent = err.message;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const field = document.getElementById(err.field);
            field.focus();
            field.setAttribute('aria-invalid', 'true');
        });
        li.appendChild(link);
        list.appendChild(li);
        
        // Mark field as invalid
        const field = document.getElementById(err.field);
        if (field) field.setAttribute('aria-invalid', 'true');
    });

    summary.focus();
}

// Securely pull initial event data
try {
    const dataEl = document.getElementById('events-data');
    if (dataEl) {
        eventData = JSON.parse(dataEl.textContent);
    }
} catch (err) {
    console.error("Critical: Initial state synchronization failure.", err);
}

/**
 * Maps Initialization with absolute keyboard isolation.
 */
window.initMap = async function() {
    try {
        const { Map, InfoWindow } = await google.maps.importLibrary("maps");
        const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

        map = new Map(document.getElementById("map"), {
            center: { lat: 37.784, lng: -122.401 },
            zoom: 16,
            mapId: "DEMO_MAP_ID",
            styles: [
                { "featureType": "all", "elementType": "geometry", "stylers": [{"color": "#1e293b"}] },
                { "featureType": "all", "elementType": "labels.text.fill", "stylers": [{"color": "#cbd5e1"}] }
            ]
        });

        // Isolate map from keyboard focus; the Event Registry is the primary interface
        const mapEl = document.getElementById('map');
        mapEl.setAttribute('aria-hidden', 'true');
        mapEl.setAttribute('tabindex', '-1');

        if (Array.isArray(eventData)) {
            const infoWindow = new InfoWindow();
            eventData.forEach(event => {
                const marker = new AdvancedMarkerElement({
                    position: { lat: event.latitude, lng: event.longitude },
                    map: map,
                    title: event.name,
                    zIndex: 1
                });
                marker.addListener("click", () => {
                    const content = document.createElement('div');
                    content.style.color = '#334155';
                    const strong = document.createElement('strong');
                    strong.textContent = event.name;
                    content.appendChild(strong);
                    content.appendChild(document.createElement('br'));
                    content.appendChild(document.createTextNode(event.topic || ""));
                    
                    infoWindow.setContent(content);
                    infoWindow.open(marker.map, marker);
                });
            });
        }
    } catch (err) {
        console.error("Maps link failed.", err);
    }
};

/**
 * Real-time Situational Awareness Stream (WebSocket)
 */
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);

ws.onmessage = (e) => {
    try {
        const data = JSON.parse(e.data);
        if (data.alert_type) {
            if (isStateSame(lastAlertState, data)) return;
            lastAlertState = data;

            const box = document.getElementById('staffAlert');
            box.style.background = 'rgba(239, 68, 68, 0.1)';
            box.style.color = '#fca5a5';
            
            box.textContent = '';
            const title = document.createElement('strong');
            title.textContent = `🚨 ${data.zone_id} ALERT `;
            box.appendChild(title);
            
            if (data.simulated) {
                const badge = document.createElement('span');
                badge.style.cssText = 'background: var(--warning); color: black; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.7rem; font-weight: 800;';
                badge.textContent = 'SIMULATED';
                box.appendChild(badge);
            }
            
            box.appendChild(document.createElement('br'));
            box.appendChild(document.createTextNode(data.protocol));
        } else {
            const feed = document.getElementById('live-feed');
            const item = document.createElement('div');
            item.className = 'live-insight-item';
            
            const zone = document.createElement('span');
            zone.textContent = data.zone;
            
            const level = document.createElement('span');
            level.style.color = data.level > 80 ? 'var(--danger)' : 'var(--success)';
            level.textContent = `${data.level}%`;
            
            item.appendChild(zone);
            item.appendChild(level);
            
            if (feed.firstElementChild && feed.firstElementChild.tagName === 'P') {
                feed.textContent = '';
            }
            feed.insertBefore(item, feed.firstChild);
            
            while (feed.children.length > 5) {
                feed.removeChild(feed.lastChild);
            }
        }
    } catch (err) {
        console.debug("Telemetry bypass:", err);
    }
};

/**
 * Itinerary Computation Orchestration with Grouped Registry List
 */
document.getElementById('itineraryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrorSummary();
    
    const errors = [];
    const start = document.getElementById('startTime').value;
    const end = document.getElementById('endTime').value;
    const topics = Array.from(document.getElementById('interests').selectedOptions).map(o => o.value);
    
    if (!start) errors.push({ field: 'startTime', message: 'Start time is required for pathfinding.' });
    if (!end) errors.push({ field: 'endTime', message: 'End time is required for pathfinding.' });
    if (topics.length === 0) errors.push({ field: 'interests', message: 'Select at least one interest for semantic matching.' });
    
    if (errors.length > 0) {
        renderErrorSummary(errors);
        return;
    }

    const btn = document.getElementById('submitBtn');
    btn.setAttribute('aria-busy', 'true');
    btn.setAttribute('aria-disabled', 'true');
    btn.disabled = true;
    btn.textContent = 'Computing Optimal Path...';
    announceState('Computing optimal itinerary results...', 'assertive');

    try {
        const payload = {
            user_location: { latitude: 37.7749, longitude: -122.4194 },
            start_time: start,
            end_time: end,
            preferred_topics: topics
        };

        const res = await fetch('/api/itinerary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (res.ok && data.itinerary) {
            if (isStateSame(lastItineraryState, data.itinerary)) {
                announceState('Itinerary results loaded (No changes since last compute).');
                return;
            }
            lastItineraryState = data.itinerary;

            document.getElementById('itineraryBadge').style.display = data.simulated ? 'block' : 'none';
            const container = document.getElementById('itineraryContent');
            container.textContent = '';
            
            // Grouping by "Topic" for semantic scalability
            const groups = data.itinerary.reduce((acc, item) => {
                const topic = item.topic || "General";
                if (!acc[topic]) acc[topic] = [];
                acc[topic].push(item);
                return acc;
            }, {});

            const fragment = document.createDocumentFragment();
            Object.keys(groups).forEach(topic => {
                const section = document.createElement('section');
                section.className = 'registry-group';
                
                const h2 = document.createElement('h2');
                h2.textContent = `${topic} Focused Sessions`;
                h2.className = 'registry-group-title';
                section.appendChild(h2);
                
                const ul = document.createElement('ul');
                ul.className = 'registry-list';
                
                groups[topic].forEach(item => {
                    const li = document.createElement('li');
                    li.className = 'itinerary-item';
                    
                    const h3 = document.createElement('h3');
                    h3.textContent = item.event_name;
                    
                    const time = document.createElement('p');
                    time.textContent = `${item.start_time} - ${item.end_time}`;
                    
                    const directions = document.createElement('p');
                    directions.style.cssText = 'font-size: 0.85rem; opacity: 0.9; color: var(--text-muted);';
                    directions.textContent = item.walking_directions;
                    
                    const selectBtn = document.createElement('button');
                    selectBtn.type = 'button';
                    selectBtn.className = 'list-action-btn';
                    selectBtn.setAttribute('aria-label', `Select Event: ${item.event_name}`);
                    selectBtn.textContent = 'Join Session';
                    selectBtn.style.cssText = 'background: transparent; border: 1px solid var(--primary); color: var(--primary); margin-top: 0.5rem; width: auto; padding: 6px 16px;';
                    
                    li.appendChild(h3);
                    li.appendChild(time);
                    li.appendChild(directions);
                    li.appendChild(selectBtn);
                    ul.appendChild(li);
                });
                section.appendChild(ul);
                fragment.appendChild(section);
            });
            
            container.appendChild(fragment);
            document.getElementById('itinerarySection').style.display = 'block';
            announceState('Optimal itinerary results loaded and rendered.');
        } else {
            renderErrorSummary([{ field: 'submitBtn', message: data.message || data.error || "Pathfinding link error." }]);
        }
    } catch (err) { 
        renderErrorSummary([{ field: 'submitBtn', message: "Network synchronization failure. Verify tactical link." }]);
    } finally { 
        btn.disabled = false; 
        btn.removeAttribute('aria-busy');
        btn.removeAttribute('aria-disabled');
        btn.textContent = 'Compute Itinerary';
    }
});

/**
 * Tactical Protocol Call
 */
document.getElementById('trigger-staff-btn').addEventListener('click', async () => {
    const btn = document.getElementById('trigger-staff-btn');
    const token = document.getElementById('staffToken').value;
    if (!token) {
        renderErrorSummary([{ field: 'staffToken', message: 'Authorization token required for zone deployment.' }]);
        return;
    }
    
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    btn.textContent = 'Orchestrating...';
    
    try {
        const res = await fetch('/api/staff/zone-action', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'Authorization': 'Bearer ' + token 
            },
            body: JSON.stringify({ zone_id: "Main Entrance", alert_type: "Emergency" })
        });
        const data = await res.json();
        if (!res.ok) {
             renderErrorSummary([{ field: 'staffToken', message: data.message || data.error || 'Tactical rejection.' }]);
        } else {
            announceState('Tactical protocol initiated successfully.');
        }
    } catch (err) {
        console.error("Link disruption.");
    } finally {
        btn.disabled = false;
        btn.removeAttribute('aria-busy');
        btn.textContent = 'Initiate Tactical Protocol';
    }
});
