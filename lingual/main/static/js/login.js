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
