// Notification System
const NOTIFY_POLL_INTERVAL = 10000; // 10 seconds

document.addEventListener('DOMContentLoaded', () => {
    // Inject Bell Icon if not present (helper for existing templates)
    // In a real scenario, we might edit templates directly, but this ensures it exists
    const bellContainer = document.getElementById('notification-bell-container');
    if (bellContainer) {
        startNotificationPolling();
    }
});

function startNotificationPolling() {
    checkNotifications();
    setInterval(checkNotifications, NOTIFY_POLL_INTERVAL);
}

function checkNotifications() {
    fetch('/api/notifications')
        .then(res => {
            if (res.status === 401) return; // User not logged in
            return res.json();
        })
        .then(data => {
            if (data) {
                updateNotificationUI(data.notifications, data.unread_count);
            }
        })
        .catch(err => console.error('Notification Poll Error:', err));
}

function updateNotificationUI(notifications, unreadCount) {
    const badge = document.getElementById('notification-badge');
    const list = document.getElementById('notification-list');
    const bellIcon = document.getElementById('bell-icon');

    // Update Badge
    if (unreadCount > 0) {
        badge.style.display = 'flex';
        badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
    } else {
        badge.style.display = 'none';
    }

    // Update List
    if (notifications.length === 0) {
        list.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: var(--text-muted);">
                <span class="material-icons" style="font-size: 32px; color: #CBD5E1;">notifications_off</span>
                <p style="margin-top: 0.5rem; font-size: 0.9rem;">No new alerts.</p>
            </div>
        `;
    } else {
        list.innerHTML = notifications.map(n => `
            <div class="notification-item ${n.is_read ? 'read' : 'unread'}" style="padding: 1rem; border-bottom: 1px solid #F1F5F9; display: flex; gap: 1rem; align-items: start; transition: background 0.2s;">
                <img src="/${n.found_img}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover; border: 1px solid #E2E8F0;">
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                        <h4 style="margin: 0; font-size: 0.9rem; font-weight: 600; color: var(--text-main);">Potential Match!</h4>
                        <span style="font-size: 0.75rem; color: var(--text-muted);">${n.time_ago}</span>
                    </div>
                    <p style="margin: 0 0 0.5rem; font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">
                        Confidence: <strong style="color: #10B981;">${n.score}%</strong>. Found in ${n.location}.
                    </p>
                    <div style="display: flex; gap: 0.5rem;">
                        <a href="/user/history" class="btn-xs-primary" style="text-decoration: none; font-size: 0.75rem; padding: 0.2rem 0.6rem; background: var(--primary-gradient); color: white; border-radius: 6px;">
                            View
                        </a>
                        <button onclick="markRead('${n.id}')" style="background: none; border: none; font-size: 0.75rem; color: var(--text-muted); cursor: pointer; text-decoration: underline;">
                            Dismiss
                        </button>
                    </div>
                </div>
                ${!n.is_read ? '<div style="width: 8px; height: 8px; background: #EF4444; border-radius: 50%; margin-top: 6px;"></div>' : ''}
            </div>
        `).join('');
    }
}

function toggleNotifications() {
    const dropdown = document.getElementById('notification-dropdown');
    if (dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
        // Remove click listener when closed
        document.removeEventListener('click', closeNotificationOnClickOutside);
    } else {
        dropdown.style.display = 'block';
        // Add click listener when opened
        setTimeout(() => {
            document.addEventListener('click', closeNotificationOnClickOutside);
        }, 0);
    }
}

function closeNotificationOnClickOutside(e) {
    const container = document.querySelector('.notification-container');
    const dropdown = document.getElementById('notification-dropdown');

    if (container && !container.contains(e.target)) {
        dropdown.style.display = 'none';
        document.removeEventListener('click', closeNotificationOnClickOutside);
    }
}

function markRead(id) {
    const btn = event.target;
    btn.innerHTML = 'Dismissing...';
    fetch(`/api/notifications/mark-read/${id}`, { method: 'POST' })
        .then(() => checkNotifications());
}
