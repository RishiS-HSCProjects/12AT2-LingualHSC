/**
 * Adds standard error styling to an element, with an optional animation for submit actions.
 */
function addErrorStyling(element, submit = false) {
    element.style.borderColor = "red";
    element.style.boxShadow = "0 0 5px red";
    if (submit) {
        // Shake on submit
        element.classList.add('error');
        setTimeout(() => {
            element.classList.remove('error');
        }, 1000); // Stop shaking after 1 second
    }
}

/**
 * Adds standard success styling to an element.
 */
function addSuccessStyling(element) {
    element.style.borderColor = "green";
    element.style.boxShadow = "0 0 5px green";
}

/**
 * Resets state styling of an element.
 */
function resetStyling(element) {
    element.style.borderColor = "";
    element.style.boxShadow = "";
}

/**
 * Utility function to prevent spamming of a button by disabling it for a specified timeout period,
 * and providing user feedback through the button's title attribute to indicate how long it will remain disabled.
 */
function spamPrevention(button, timeout = 3000) {
    button.disabled = true; // Disable the button
    let secsRemaining = timeout / 1000; // Convert to seconds
    button.title = `Button temporarily disabled for ${secsRemaining} seconds.`; // Add tooltip

    if (button.disabledInterval) {
        // Clear any existing interval to avoid overlaps
        clearInterval(button.disabledInterval);
    }

    // Start a new interval to countdown the time
    button.disabledInterval = setInterval(() => {
        secsRemaining--; // Decrement remaining seconds
        button.title = `Button temporarily disabled for ${secsRemaining} seconds.`; // Update tooltip with remaining time
        
        if (secsRemaining <= 0) {
            // Time is up, re-enable the button
            clearInterval(button.disabledInterval); // Clear interval when time is up
            button.disabled = false; // Enable button
            button.title = ""; // Remove tooltip text
            button.disabledInterval = null; // Clean up the reference
        }
    }, 1000); // Run every 1000 milliseconds (1 second)
}
