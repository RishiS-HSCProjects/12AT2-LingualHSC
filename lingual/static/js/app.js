const FLASH_DURATION = 10000; // Flash alive duration in ms
const FLASH_STAGGER = 500;    // Stagger in ms

document.addEventListener('DOMContentLoaded', () => {
    const messages = Array.from( // Get all flash messages
        document.querySelectorAll('#flash-container .flash-message')
    );

    messages.forEach((msg, index) => initFlashMessage(msg, index)); // Initialize each message
});

function initFlashMessage(msg, index = 0) {
    // Set initial display and styling
    setTimeout(() => {
        msg.style.display = 'block'; // Make message visible

        // Force reflow so transitions don't skip
        void msg.offsetWidth;

        msg.style.opacity = '0.95';
        msg.style.transform = 'scale(1)';

        // Initialize internal state
        msg.remaining = FLASH_DURATION;
        msg.lastTick = Date.now();
        msg.fadeOutStarted = false;

        msg.timer = requestAnimationFrame(() => tick(msg));

        /**
         * The below logic handles user interactions with the flash message.
         * The intention is to allow users to focus on a message by hovering over it,
         * which pauses the auto-dismiss timer. When the user moves the mouse away,
         * the timer resumes with an additional 2 seconds added to the remaining time,
         * up to a maximum of 10 seconds total. Clicking the message immediately dismisses it.
         * 
         * This approach improves user experience by giving users more control over
         * how long they want to view important messages, while still ensuring that
         * messages do not linger indefinitely.
         */

        // Hover to pause
        msg.addEventListener('mouseenter', () => {
            if (msg.fadeOutStarted) return;
            pauseTimer(msg);
            msg.style.opacity = '1';
            msg.style.transform = 'scale(1.05)';
        });

        // Hover to resume
        msg.addEventListener('mouseleave', () => {
            if (msg.fadeOutStarted) return;
            // Increase the remaining time by 2 seconds, but ensure it doesn't exceed 10 seconds
            msg.remaining = Math.min(msg.remaining + 2000, 10000); // Max 10 seconds
            resumeTimer(msg);
            msg.style.opacity = '0.95';
            msg.style.transform = 'scale(1)';
        });

        // Click to dismiss
        msg.addEventListener('click', () => {
            pauseTimer(msg);
            fadeOut(msg);
        });

    }, index * FLASH_STAGGER); // Staggered display
}

/**
 * Handles the ticking of the flash message timer.
 * Handles the countdown and triggers fade-out when time is up.
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

function pauseTimer(msg) { // Don't think I need to explain this one
    if (msg.timer) {
        cancelAnimationFrame(msg.timer);
        msg.timer = null;
    }
}

function resumeTimer(msg) { // Or this
    if (!msg.timer) {
        msg.lastTick = Date.now();
        msg.timer = requestAnimationFrame(() => tick(msg));
    }
}

function fadeOut(msg) {
    if (msg.fadeOutStarted) return;

    // Mark fade-out as started to prevent multiple triggers (this was a pain to watch when it didn't exist haha)
    msg.fadeOutStarted = true;
    msg.style.transition = 'opacity 0.45s ease, transform 0.45s ease'; // Add animations
    msg.style.opacity = '0'; // Fade out destination.
    msg.style.transform = 'scale(0.95)'; // Slight shrink effect

    setTimeout(() => {
        msg.remove();
    }, 450); // Ensure message removal after fade-out
}

/**
 * Sends a flash message to be displayed.
 * Used to dynamically create flash messages from JS without reloading the page. (AJAX)
 * 
 * @param {string} message - The message text to display.
 * @param {string} category - The category of the message ('info', 'success', 'error', 'warning').
 */
function sendFlashMessage(message, category = 'info') {
    const container = document.getElementById('flash-container');
    if (!container) {
        console.error('Flash container not found.');
        return;
    }

    /* This solution of creating a new element and appending
       it to the existing flash-container was suggested by AI. */
    // Refer to AI declaration.
    const msg = document.createElement('div');
    msg.className = `flash-message ${category}`;
    msg.textContent = message;

    container.appendChild(msg);

    // Initialize immediately to handle display and timing
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

function redirectTo(url) {
    window.location.href = url;
}
