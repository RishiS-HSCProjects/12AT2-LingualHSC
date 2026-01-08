document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();

        btn = document.getElementById('login-btn');

        if (btn) {
            btn.focus()
            btn.click();
        }
    }
});
