/* 
   AUTH SLIDING LOGIC 
   Handles the "slide" effect between separate pages.
*/

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.auth-container');

    // Check if we are on Login or Signup page
    const isLoginPage = window.location.pathname.includes('/login') || window.location.pathname === '/' || window.location.pathname === '';
    const isSignupPage = window.location.pathname.includes('/signup');

    /* 
       ANIMATION STRATEGY:
       - Since they are separate html files, we simulate the "slide" by applying classes
         before navigating.
    */

    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');

    if (signUpButton) {
        signUpButton.addEventListener('click', (e) => {
            if (isLoginPage) {
                e.preventDefault();
                // Add class to slide the overlay to the left (covering the form)
                // Actually, standard "Sign Up" slide creates a "right-panel-active" state usually.
                // But here, we just want to transition.

                // Visual effect: Slide overlay to cover screen? 
                // Simple approach: Fade/Slide out
                document.body.style.opacity = '0';
                document.body.style.transform = 'translateX(-20px)';
                document.body.style.transition = 'all 0.4s ease-in-out';

                setTimeout(() => {
                    window.location.href = '/signup';
                }, 400);
            }
        });
    }

    if (signInButton) {
        signInButton.addEventListener('click', (e) => {
            if (isSignupPage) {
                e.preventDefault();
                document.body.style.opacity = '0';
                document.body.style.transform = 'translateX(20px)';
                document.body.style.transition = 'all 0.4s ease-in-out';

                setTimeout(() => {
                    window.location.href = '/login';
                }, 400);
            }
        });
    }

    // Entry Animation
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';

    // Determine entry direction based on page
    if (isLoginPage) {
        // Entering Login: Slide in from Left (as if returning)
        document.body.style.transform = 'translateX(-20px)';
    } else {
        // Entering Signup: Slide in from Right
        document.body.style.transform = 'translateX(20px)';
    }

    requestAnimationFrame(() => {
        document.body.style.opacity = '1';
        document.body.style.transform = 'translateX(0)';
    });
});
