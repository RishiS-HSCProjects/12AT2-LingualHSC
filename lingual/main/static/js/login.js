// Refactor enter keydown to only trigger login button click, preventing the default form submission
document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();

        const btn = document.getElementById('login-btn'); // Find btn

        if (btn) {
            // Focus and click the login button
            btn.focus()
            btn.click();
        } // Don't return error if button is not found, should never happen
    }
});

// On page load, focus on the email input field if empty, else focus on the password field
// This is a QOL improvement to allow users to start typing their email/password immediately without having to click on the input field first
window.addEventListener('load', () => {
    const emailInput = document.querySelector('input[name="email"]');
    const passwordInput = document.querySelector('input[name="password"]');
    if (emailInput && emailInput.value === '') {
        emailInput.focus();
    } else if (passwordInput) { // Higher chance of password input being incorrect, on reload, focus here
        passwordInput.focus();
    }
});
