function addErrorStyling(element, submit = false) {
    element.style.borderColor = "red";
    element.style.boxShadow = "0 0 5px red";
    if (submit) {
        element.classList.add('error');
        setTimeout(() => {
            element.classList.remove('error');
        }, 1000);
    }
}

function addSuccessStyling(element) {
    element.style.borderColor = "green";
    element.style.boxShadow = "0 0 5px green";
}

function resetStyling(element) {
    element.style.borderColor = "";
    element.style.boxShadow = "";
}

function spamPrevention(button, timeout = 3000) {
    button.disabled = true; // Disable the button
    let timeRemaining = timeout / 1000; // Convert to seconds
    button.title = `Button temporarily disabled for ${timeRemaining} seconds.`;

    if (button.disabledInterval) {
        // Clear any existing interval to avoid overlaps
        clearInterval(button.disabledInterval);
    }

    // Start a new interval to countdown the time
    button.disabledInterval = setInterval(() => {
        timeRemaining--;
        button.title = `Button temporarily disabled for ${timeRemaining} seconds.`;
        
        if (timeRemaining <= 0) {
            clearInterval(button.disabledInterval); // Clear interval when time is up
            button.disabled = false; // Enable button
            button.title = ""; // Remove tooltip text
            button.disabledInterval = null; // Clean up the reference
        }
    }, 1000); // Run every second
}

