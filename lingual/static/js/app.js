document.addEventListener('DOMContentLoaded', () => {
    // Store messages in a constant by querying through all elements with a specific ID and class 
    const messages = Array.from(document.querySelectorAll('#flash-container .flash-message'));

    // Duration for each message to be visible (in milliseconds)
    const DURATION = 10000; // todo: change to user preference later

    // Following code handles the display, timing, and interactions of flash messages
    messages.forEach((msg, i) => {
        setTimeout(() => {
            msg.style.display = 'block';
            
            void msg.offsetWidth;  // force style recalculation to avoid transition skipping or snapping
            msg.style.opacity = '0.95';
            msg.style.transform = 'scale(1)';

            // Configure countdown state
            msg.remaining = DURATION;
            msg.lastTick = Date.now();
            msg.timer = requestAnimationFrame(() => tick(msg));

            // hover pause event
            msg.addEventListener('mouseenter', () => {
                if (msg.fadeOutStarted) return; // Avoids visual glitches during removal
                pauseTimer(msg);
                msg.style.opacity = '1';
                msg.style.transform = 'scale(1.05)';
            });

            // hover resume event
            msg.addEventListener('mouseleave', () => {
                if (msg.fadeOutStarted) return; // Avoids visual glitches during removal
                resumeTimer(msg);
                msg.style.opacity = '0.95';
                msg.style.transform = 'scale(1)';
            });

            // click to dismiss event
            msg.addEventListener('click', () => {
                msg.style.cursor = 'pointer';
                pauseTimer(msg);
                fadeOut(msg);
            });

        }, i * 500);
    });

    /**
     * Handles flash countdown.
     * Calls helper functions to handle timing and fading.
     * @param {HTMLElement} msg Flash message element
     * @returns 
     */
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
        msg.fadeOutStarted = true;
        msg.style.opacity = '0';
        msg.style.transition = 'opacity 0.45s ease, transform 0.45s ease';

        setTimeout(() => {
            msg.style.display = 'none';
        }, 450);
    }
});

/**
 * Scrolls to an element by its ID.
 * @param {string} id Id of element
 */
function scrollToId(id) {
    const element = document.getElementById(id);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}