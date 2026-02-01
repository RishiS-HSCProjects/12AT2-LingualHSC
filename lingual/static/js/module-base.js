document.addEventListener('DOMContentLoaded', () => {
    initResponsiveNav(); // Initialize responsive navigation (check if the nav needs collapsing)
});

function initResponsiveNav() {
    const nav = document.querySelector('nav');
    const navWrapper = document.getElementById('nav-wrapper');
    const navOpt = document.getElementById('nav-opt');
    const navLogo = document.getElementById('nav-logo');

    if (!nav || !navWrapper || !navOpt || !navLogo) return; // Required elements not found

    let toggleBtn = document.getElementById('nav-toggle'); // Check for existing toggle button
    if (!toggleBtn) { // Create toggle button if not found
        toggleBtn = document.createElement('button');
        toggleBtn.id = 'nav-toggle';
        toggleBtn.type = 'button';
        toggleBtn.setAttribute('aria-label', 'Toggle navigation');
        toggleBtn.setAttribute('aria-expanded', 'false');

        // SVG icon for hamburger menu
        // Editted based on https://www.svgrepo.com/svg/524617/hamburger-menu
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.8160000000000001"></g>
                <g id="SVGRepo_iconCarrier">
                    <path d="M20 7L4 7" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                    <path d="M20 12L4 12" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                    <path d="M20 17L4 17" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                </g>
            </svg>
        `;

        navOpt.prepend(toggleBtn); // Insert toggle button before "nav options".
    }

    const closeMenu = () => { // Close menu anonymous function
        nav.classList.remove('nav-open');
        toggleBtn.setAttribute('aria-expanded', 'false'); // Accessibility (I'm very inconsistent with this. todo: add accessibility everywhere)
    };

    toggleBtn.addEventListener('click', () => {
        const isOpen = nav.classList.toggle('nav-open'); // Toggle nav-open class
        toggleBtn.setAttribute('aria-expanded', String(isOpen));
    });

    navOpt.addEventListener('click', (event) => {
        const target = event.target;
        if (target && target.closest('a, button')) { // Check if a link or button was clicked (option click logic is handled by the browser)
            closeMenu(); // Close nav menu on option click
        }
    });

    /**
     * Anonymous function to check if the navigation bar is overflowing its container.
     * Temporarily removes nav state classes to get accurate measurements.
     * 
     * @returns {boolean} - True if the navigation should be collapsed, false otherwise.
     */
    const isOverflowing = () => {
        const wasOpen = nav.classList.contains('nav-open');

        // Expand and collapse temporarily to measure overflow. 
        // This makes it stutter slightly on resize, but it's "good enough" for now.
        // todo: fix attitude.
        nav.classList.remove('nav-collapsed');
        nav.classList.remove('nav-open');
        toggleBtn.setAttribute('aria-expanded', 'false'); // Reset toggle button state for accurate measurement

        const wrapperWidth = navWrapper.clientWidth;
        const logoWidth = navLogo.getBoundingClientRect().width;
        const optWidth = navOpt.scrollWidth;
        const paddingAllowance = 75; // This was tested to be a good amount of extra space to prevent wrapping.

        const shouldCollapse = logoWidth + optWidth + paddingAllowance > wrapperWidth;

        if (wasOpen) { // Restore previous open state if it was open
            nav.classList.add('nav-open');
        }

        return shouldCollapse;
    };

    const updateNav = () => {
        const wasOpen = nav.classList.contains('nav-open');
        const shouldCollapse = isOverflowing();

        if (shouldCollapse) {
            nav.classList.add('nav-collapsed'); // Add collapsed class
            if (wasOpen) { // Restore previous open state if it was open
                nav.classList.add('nav-open'); // Keep it open
                toggleBtn.setAttribute('aria-expanded', 'true'); // Update toggle button state
            }
        } else {
            nav.classList.remove('nav-collapsed'); // Remove collapsed class
            nav.classList.remove('nav-open'); // Ensure nav is closed
            toggleBtn.setAttribute('aria-expanded', 'false'); // Update toggle button state
        }
    };

    const resizeObserver = new ResizeObserver(() => updateNav()); // Add 'observer' for DOM elements' resize events.
    // If any of these elements resize, we need to recheck nav state.
    resizeObserver.observe(navWrapper); // add listener to nav wrapper
    resizeObserver.observe(navOpt); // add listener to nav options

    window.addEventListener('resize', () => updateNav()); // Fallback for window resize
    updateNav(); // Initial check on load

    // Close nav menu when clicking outside of it
    document.addEventListener('click', (event) => {
        if (!nav.classList.contains('nav-open')) return;

        const navClick = nav.contains(event.target);
        if (!navClick) { // If the click was outside the nav, close the menu
            closeMenu();
        }
    });
}
