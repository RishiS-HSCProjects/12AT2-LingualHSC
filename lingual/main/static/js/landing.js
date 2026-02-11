function whyUsScroll() {
    scrollToId('why-lingual');
}

function purposeScroll() {
    scrollToId('purpose');
}

document.addEventListener('DOMContentLoaded', () => {
    initLandingNav();
});

function initLandingNav() {
    const nav = document.querySelector('nav');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.getElementById('nav-links');
    const navLogo = document.getElementById('logo');
    const getStarted = document.getElementById('get-started-btn');

    if (!nav || !navMenu || !navLinks || !navLogo || !getStarted) return;

    let toggleBtn = document.getElementById('nav-toggle');
    if (!toggleBtn) {
        toggleBtn = document.createElement('button');
        toggleBtn.id = 'nav-toggle';
        toggleBtn.type = 'button';
        toggleBtn.setAttribute('aria-label', 'Toggle navigation');
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 7L4 7" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                <path d="M20 12L4 12" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
                <path d="M20 17L4 17" stroke="#000000" stroke-width="1.5" stroke-linecap="round"></path>
            </svg>
        `;

        nav.appendChild(toggleBtn);
    }

    const closeMenu = () => {
        nav.classList.remove('nav-open');
        toggleBtn.setAttribute('aria-expanded', 'false');
    };

    toggleBtn.addEventListener('click', () => {
        const isOpen = nav.classList.toggle('nav-open');
        toggleBtn.setAttribute('aria-expanded', String(isOpen));
    });

    navMenu.addEventListener('click', (event) => {
        const target = event.target;
        if (target && target.closest('a, button')) {
            closeMenu();
        }
    });

    const isOverflowing = () => {
        const wasOpen = nav.classList.contains('nav-open');

        nav.classList.remove('nav-collapsed');
        nav.classList.remove('nav-open');
        toggleBtn.setAttribute('aria-expanded', 'false');

        const navWidth = nav.clientWidth;
        const logoWidth = navLogo.getBoundingClientRect().width;
        const linksWidth = navLinks.getBoundingClientRect().width;
        const ctaWidth = getStarted.getBoundingClientRect().width;
        const paddingAllowance = 80;

        const shouldCollapse = logoWidth + linksWidth + ctaWidth + paddingAllowance > navWidth;

        if (wasOpen) {
            nav.classList.add('nav-open');
        }

        return shouldCollapse;
    };

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

    const resizeObserver = new ResizeObserver(() => updateNav());
    resizeObserver.observe(nav);
    resizeObserver.observe(navMenu);

    window.addEventListener('resize', () => updateNav());
    updateNav();

    document.addEventListener('click', (event) => {
        if (!nav.classList.contains('nav-open')) return;

        const navClick = nav.contains(event.target);
        if (!navClick) {
            closeMenu();
        }
    });
}
