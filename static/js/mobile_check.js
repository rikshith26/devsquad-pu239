(function () {
    /**
     * MOBILE ONLY RESTRICTOR
     * Injects a premium overlay if the app is accessed via Tablet or Desktop.
     */
    function checkDevice() {
        // Breakpoint for Mobile (usually < 768px for phones/portrait)
        // We include tablets in the "restricted" group as requested.
        const isMobile = window.innerWidth <= 640; 
        let overlay = document.getElementById('mobile-only-restrictor');

        if (!isMobile) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'mobile-only-restrictor';
                overlay.style.position = 'fixed';
                overlay.style.inset = '0';
                overlay.style.zIndex = '999999';
                overlay.style.backgroundColor = '#fdfbf7'; // Morning Light Theme Bg
                overlay.style.backgroundImage = 'radial-gradient(#e6e6e6 1px, transparent 1px)';
                overlay.style.backgroundSize = '20px 20px';
                overlay.style.display = 'flex';
                overlay.style.alignItems = 'center';
                overlay.style.justifyContent = 'center';
                overlay.style.padding = '2rem';
                overlay.style.textAlign = 'center';
                overlay.style.fontFamily = "'Outfit', sans-serif";

                overlay.innerHTML = `
                    <div style="max-width: 450px; animation: slideUp 0.6s ease-out;">
                        <div style="width: 100px; height: 100px; background: rgba(255, 159, 67, 0.1); border-radius: 30px; display: flex; align-items: center; justify-content: center; margin: 0 auto 2.5rem; transform: rotate(-5deg);">
                            <span class="material-icons" style="font-size: 3.5rem; color: #ff9f43;">smartphone</span>
                        </div>
                        
                        <h1 style="font-size: 2.5rem; font-weight: 800; color: #2d3436; margin-bottom: 1.5rem; letter-spacing: -1px; line-height: 1.1;">
                            Mobile Experience <br/><span style="color: #ff9f43;">Only.</span>
                        </h1>
                        
                        <p style="color: #636e72; font-size: 1.1rem; line-height: 1.6; margin-bottom: 2.5rem;">
                            Foundify is designed exclusively for mobile devices. This allows you to effortlessly use your camera to capture and report items as soon as you find them.
                        </p>
                        
                        <div style="padding: 2rem; background: #fff; border-radius: 32px; box-shadow: 0 20px 50px rgba(0,0,0,0.08); display: inline-block; border: 1px solid rgba(0,0,0,0.03); position: relative; overflow: hidden;">
                            <div style="position: absolute; top:0; left:0; width:100%; height:6px; background: linear-gradient(90deg, #ff9f43, #ff6b6b);"></div>
                            <p style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #2d3436; margin-bottom: 1.5rem;">Scan to switch to mobile</p>
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${window.location.href}" 
                                 style="width: 180px; height: 180px; display: block; margin: 0 auto; border-radius: 12px;" 
                                 alt="QR Code">
                        </div>
                        
                        <div style="margin-top: 3rem; font-size: 0.9rem; color: #a0a0a0;">
                            Tablet & Desktop access is restricted for security and optimal reporting.
                        </div>
                    </div>
                `;

                // Add necessary font and animation
                const style = document.createElement('style');
                style.innerHTML = `
                    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;800&display=swap');
                    @keyframes slideUp {
                        from { opacity: 0; transform: translateY(30px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
                document.head.appendChild(style);

                // Add Material Icons if missing
                if (!document.querySelector('link[href*="Material+Icons"]')) {
                    const link = document.createElement('link');
                    link.href = 'https://fonts.googleapis.com/icon?family=Material+Icons';
                    link.rel = 'stylesheet';
                    document.head.appendChild(link);
                }

                document.body.appendChild(overlay);
                document.body.style.overflow = 'hidden';
            }
        } else {
            if (overlay) {
                overlay.remove();
                document.body.style.overflow = '';
            }
        }
    }

    // Expose for external calls
    window.checkDevice = checkDevice;

    // Run on boot
    checkDevice();
    
    // Listen for resize (e.g. pivoting device or resizing window)
    window.addEventListener('resize', checkDevice);
    
    // Ensure it runs after full DOM loads for safety
    window.addEventListener('load', checkDevice);
})();
