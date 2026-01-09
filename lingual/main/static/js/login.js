document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();

        const btn = document.getElementById('login-btn');

        if (btn) {
            btn.focus()
            btn.click();
        }
    }
});

// On page load, focus on the email input field if empty, else focus on the password field
window.addEventListener('load', () => {
    const emailInput = document.querySelector('input[name="email"]');
    const passwordInput = document.querySelector('input[name="password"]');
    if (emailInput && emailInput.value === '') {
        emailInput.focus();
    } else if (passwordInput) {
        passwordInput.focus();
    }
});
