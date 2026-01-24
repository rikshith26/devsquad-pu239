
// Foundify Offline Handler
// Injects a "Connection Lost" overlay when internet is disconnected.

document.addEventListener("DOMContentLoaded", () => {
    // 1. Create Overlay HTML
    const offlineOverlay = document.createElement("div");
    offlineOverlay.id = "foundify-offline-overlay";
    offlineOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #FDFBF7 0%, #FFF7ED 100%);
        z-index: 999999;
        display: none; /* Hidden by default */
        align-items: center;
        justify-content: center;
        flex-direction: column;
        text-align: center;
        padding: 2rem;
        font-family: 'Outfit', sans-serif;
    `;

    // Branding Colors (from style.css)
    const primaryColor = "#F6AD55"; // Orange
    const textColor = "#2D3748";

    offlineOverlay.innerHTML = `
        <div style="background: rgba(255,255,255,0.7); backdrop-filter: blur(20px); 
                    padding: 3rem; border-radius: 30px; box-shadow: 0 20px 50px rgba(0,0,0,0.05);
                    max-width: 500px; width: 100%;">
            
            <!-- Animated Icon -->
            <div style="width: 120px; height: 120px; margin: 0 auto 2rem; position: relative;">
                <div style="position: absolute; inset: 0; border: 4px solid ${primaryColor}; border-radius: 50%; opacity: 0.2; animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
                <div style="width: 100%; height: 100%; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; z-index: 2; box-shadow: 0 10px 30px rgba(246, 173, 85, 0.2);">
                    <span class="material-icons" style="font-size: 64px; color: ${primaryColor};">wifi_off</span>
                </div>
            </div>

            <h2 style="font-size: 2rem; margin-bottom: 1rem; color: ${textColor}; font-weight: 700;">
                Connection Lost
            </h2>
            
            <p style="color: #718096; margin-bottom: 2.5rem; font-size: 1.1rem; line-height: 1.6;">
                We can't find a signal. Just like a lost item, we are searching for your connection...
            </p>

            <button onclick="window.location.reload()" 
                    style="background: linear-gradient(135deg, #F6AD55 0%, #EC4899 100%); 
                           color: white; border: none; padding: 1rem 2.5rem; 
                           border-radius: 12px; font-size: 1rem; font-weight: 600; 
                           cursor: pointer; box-shadow: 0 10px 20px rgba(246, 173, 85, 0.3);
                           transition: transform 0.2s;">
                Try Again
            </button>
        </div>

        <style>
            @keyframes ping {
                75%, 100% {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        </style>
    `;

    document.body.appendChild(offlineOverlay);

    // 2. Logic to Show/Hide
    function updateOnlineStatus() {
        const status = navigator.onLine;
        if (status) {
            // Online
            offlineOverlay.style.display = "none";
            document.body.style.overflow = "auto"; // Restore scroll
        } else {
            // Offline
            offlineOverlay.style.display = "flex";
            document.body.style.overflow = "hidden"; // Lock scroll
        }
    }

    // 3. Event Listeners
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Initial Check
    if (!navigator.onLine) {
        updateOnlineStatus();
    }
});
