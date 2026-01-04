const FLASH_DURATION = 10000; // Flash alive duration in ms
const FLASH_STAGGER = 500;    // Stagger in ms

document.addEventListener('DOMContentLoaded', () => {
    const messages = Array.from(
        document.querySelectorAll('#flash-container .flash-message')
    );

    messages.forEach((msg, index) => initFlashMessage(msg, index)); // Initialises each message
});

function initFlashMessage(msg, index = 0) {
    setTimeout(() => {
        msg.style.display = 'block';

        // force reflow so transitions don't skip
        void msg.offsetWidth;

        msg.style.opacity = '0.95';
        msg.style.transform = 'scale(1)';

        // internal state
        msg.remaining = FLASH_DURATION;
        msg.lastTick = Date.now();
        msg.fadeOutStarted = false;

        msg.timer = requestAnimationFrame(() => tick(msg));

        /* hover pause */
        msg.addEventListener('mouseenter', () => {
            if (msg.fadeOutStarted) return;
            pauseTimer(msg);
            msg.style.opacity = '1';
            msg.style.transform = 'scale(1.05)';
        });

        /* hover resume */
        msg.addEventListener('mouseleave', () => {
            if (msg.fadeOutStarted) return;
            resumeTimer(msg);
            msg.style.opacity = '0.95';
            msg.style.transform = 'scale(1)';
        });

        /* click dismiss */
        msg.addEventListener('click', () => {
            pauseTimer(msg);
            fadeOut(msg);
        });

    }, index * FLASH_STAGGER);
}

function tick(msg) {
    const now = Date.now();
    const elapsed = now - msg.lastTick;
    msg.lastTick = now;

    msg.remaining -= elapsed;

    if (msg.remaining <= 0) {
        fadeOut(msg);
        return;
    }

    msg.timer = requestAnimationFrame(() => tick(msg));
}

function pauseTimer(msg) {
    if (msg.timer) {
        cancelAnimationFrame(msg.timer);
        msg.timer = null;
    }
}

function resumeTimer(msg) {
    if (!msg.timer) {
        msg.lastTick = Date.now();
        msg.timer = requestAnimationFrame(() => tick(msg));
    }
}

function fadeOut(msg) {
    if (msg.fadeOutStarted) return;

    msg.fadeOutStarted = true;
    msg.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
    msg.style.opacity = '0';
    msg.style.transform = 'scale(0.95)';

    setTimeout(() => {
        msg.remove();
    }, 450);
}

function sendFlashMessage(message, category = 'info') {
    const container = document.getElementById('flash-container');
    if (!container) {
        console.error('Flash container not found.');
        return;
    }

    const msg = document.createElement('div');
    msg.className = `flash-message ${category}`;
    msg.textContent = message;

    container.appendChild(msg);

    // initialise immediately (no stagger for dynamic)
    initFlashMessage(msg);
}

function scrollToId(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with id "${id}" not found.`);
        return;
    }

    element.scrollIntoView({ behavior: 'smooth' });
}
