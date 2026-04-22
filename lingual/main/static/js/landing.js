document.addEventListener('DOMContentLoaded', () => { // Wait for the DOM to be fully loaded before executing the script
    initLandingNav();

    if (window.matchMedia("(any-pointer:coarse)").matches) {
        // Show alert if user is on a mobile device, as the service is not yet optimised for mobile use
        alert("Welcome to Lingual HSC! This service is yet to be optimised for mobile devices. For the best experience, please log on using a computer.")
    }
});

/**
 * Initializes the landing page navigation functionality, setting up event listeners for the navigation toggle button, handling window
 * resizing to adjust the navigation layout, and ensuring that clicking outside the navigation menu will close it if it's open.
 */
function initLandingNav() {
    // Get references to navigation elements
    const nav = document.querySelector('nav');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.getElementById('nav-links');
    const navLogo = document.getElementById('logo');
    const getStarted = document.getElementById('get-started-btn');

    if (!nav || !navMenu || !navLinks || !navLogo || !getStarted) return; // Exit early if any of the required elements are missing

    let toggleBtn = document.getElementById('nav-toggle'); // Check if the toggle button already exists in the DOM
    if (!toggleBtn) { // If toggle button not found, create it dynamically
        toggleBtn = document.createElement('button');
        toggleBtn.id = 'nav-toggle';
        toggleBtn.type = 'button';
        toggleBtn.setAttribute('aria-label', 'Toggle navigation'); // Accessibility label for screen readers
        toggleBtn.setAttribute('aria-expanded', 'false'); // Accessibility attribute for menu state

        // SVG icon for the hamburger menu
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 7L4 7" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                <path d="M20 12L4 12" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                <path d="M20 17L4 17" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
            </svg>
        `;

        nav.appendChild(toggleBtn); // Add toggle button to the nav bar
    }

    /** Closes the open navigation menu */
    const closeMenu = () => {
        nav.classList.remove('nav-open'); // Remove class attribute
        toggleBtn.setAttribute('aria-expanded', 'false'); // Update state for accessibility
    };

    // Event listener for toggle button to open/close the navigation menu
    toggleBtn.addEventListener('click', () => {
        const isOpen = nav.classList.toggle('nav-open');
        toggleBtn.setAttribute('aria-expanded', String(isOpen)); // Update state for accessibility
    });

    navMenu.addEventListener('click', (event) => {
        const target = event.target;
        if (target && target.closest('a, button')) {
            closeMenu(); // Close the menu when a link or button inside the nav menu is clicked
        }
    });

    /**
     * Determines if the navigation bar content is overflowing its container, which would require collapsing the menu into a hamburger style.
     * @returns {boolean} True if the content is overflowing, false otherwise.

     */
    const isOverflowing = () => {
        const wasOpen = nav.classList.contains('nav-open'); // Check open state before measuring

        nav.classList.remove('nav-collapsed'); // Temporarily remove collapsed state to get accurate measurements
        nav.classList.remove('nav-open'); // Ensure menu is closed for measurement
        toggleBtn.setAttribute('aria-expanded', 'false'); // Set toggle button state to closed for measurement

        // Get widths of navigation elements to determine if they fit within the nav container
        const navWidth = nav.clientWidth;
        const logoWidth = navLogo.getBoundingClientRect().width;
        const linksWidth = navLinks.getBoundingClientRect().width;
        const ctaWidth = getStarted.getBoundingClientRect().width;
        const paddingAllowance = 80; // Additional space to account for padding/margins and ensure the menu doesn't feel cramped

        // Determine if nav bar should collapse
        const shouldCollapse = logoWidth + linksWidth + ctaWidth + paddingAllowance > navWidth;

        if (wasOpen) { // If the menu was open before measurement, restore its open state after determining if it should collapse
            nav.classList.add('nav-open');
        }

        return shouldCollapse; // Return whether the menu should collapse based on the measurement
    };

    /** Update navigation bar state based on overflow */
    const updateNav = () => {
        const wasOpen = nav.classList.contains('nav-open');
        const shouldCollapse = isOverflowing();

        if (shouldCollapse) {
            nav.classList.add('nav-collapsed');
            if (wasOpen) {
                nav.classList.add('nav-open');
                toggleBtn.setAttribute('aria-expanded', 'true');
            }
        } else {
            nav.classList.remove('nav-collapsed');
            nav.classList.remove('nav-open');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    };

    /**
     * ResizeObserver to monitor changes in the size of the navigation bar and its menu, allowing the layout to adjust
     * dynamically when the window is resized or when content changes.
     * This ensures that the navigation remains responsive and appropriately collapses or expands based on available space.
     */
    const resizeObserver = new ResizeObserver(() => updateNav()); // Call updateNav on resize event
    resizeObserver.observe(nav); // Add nav to observer
    resizeObserver.observe(navMenu); // Add nav menu to observer

    window.addEventListener('resize', () => updateNav()); // Add resize event listener
    updateNav(); // Initial update on DOM load

    // Add event listener to close the navigation menu when clicking outside of it
    document.addEventListener('click', (event) => {
        if (!nav.classList.contains('nav-open')) return;

        const navClick = nav.contains(event.target);
        if (!navClick) {
            closeMenu();
        }
    });
}
