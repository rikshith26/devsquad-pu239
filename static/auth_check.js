// Polling interval in milliseconds (e.g., 10000 = 10 seconds)
const POLL_INTERVAL = 10000;

function checkUserStatus() {
    fetch('/auth/check-status') // We will create this endpoint in app.py
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                // Unauthorized or Forbidden implies session invalid or user blocked
                window.location.href = "/account-blocked";
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.status === 'inactive') {
                // User is explicitly inactive
                window.location.href = "/account-blocked";
            } else if (data && data.status === 'invalid_session') {
                // Session version mismatch or other invalidation
                 window.location.href = "/login";
            }
        })
        .catch(error => {
            console.error('Error checking user status:', error);
        });
}

// Start polling
setInterval(checkUserStatus, POLL_INTERVAL);
