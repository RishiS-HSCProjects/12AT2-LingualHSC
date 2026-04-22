/**
 * Account page JavaScript to handle navigation and active link highlighting.
 * This script listens for clicks on navigation links and updates the active state accordingly.
 * It also listens for hash changes in the URL to ensure the correct link is highlighted when navigating directly to a section.
 */
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = Array.from(document.querySelectorAll('aside > #nav > a[href^="#"]')); // Select all navigation links that are direct children of the #nav element and have a hash href

    /**
     * Sets the active navigation link based on the current URL hash.
     */
    const setActiveByHash = () => {
        const hash = window.location.hash || '#your-account'; // Default to '#your-account' if no hash is present
        navLinks.forEach((link) => {
            link.classList.toggle('active', link.getAttribute('href') === hash); // Add 'active' class if the link's href matches the current hash, otherwise remove it
        });
    };

    // Add event listeners to each navigation link to handle click events and update the active state
    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            navLinks.forEach((other) => other.classList.remove('active'));
            link.classList.add('active');
        });
    });

    window.addEventListener('hashchange', setActiveByHash); // Listen for hash changes in the URL to update the active link accordingly
    setActiveByHash(); // Set the active link on initial page load based on the current URL hash
});
