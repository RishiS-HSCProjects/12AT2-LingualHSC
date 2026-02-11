document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.home-item.disabled').forEach(item => {
        item.addEventListener('click', event => {
            event.preventDefault();
        });
    });
});