document.addEventListener('DOMContentLoaded', () => {
    const navLinks = Array.from(document.querySelectorAll('aside > #nav > a[href^="#"]'));

    const setActiveByHash = () => {
        const hash = window.location.hash || '#your-account';
        navLinks.forEach((link) => {
            link.classList.toggle('active', link.getAttribute('href') === hash);
        });
    };

    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            navLinks.forEach((other) => other.classList.remove('active'));
            link.classList.add('active');
        });
    });

    window.addEventListener('hashchange', setActiveByHash);
    setActiveByHash();
});
