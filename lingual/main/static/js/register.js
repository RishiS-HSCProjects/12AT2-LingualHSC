/**
 * Get CSRF token from hidden form input
 */
function getCSRFToken() {
    const tokenInput = document.getElementById('csrf_token');
    return tokenInput ? tokenInput.value : '';
}

/**
 * Create headers with CSRF token for fetch requests
 */
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    };
}

/**
 * Handles scrolling between registration sections.
 */
function handleSectionScroll(sourceSectionId, targetSectionId, targetId = null) {
    const sourceElement = document.getElementById(sourceSectionId);
    const targetElement = document.getElementById(targetSectionId);

    if (!sourceElement || !targetElement) {
        // Exit early if either element is not found
        console.error("Invalid source or target section ID");
        return;
    }

    // Add active class to make target visible and in document flow
    targetElement.classList.add('active');

    // Use requestAnimationFrame to ensure the element is laid out before scrolling
    requestAnimationFrame(() => {
        if (targetId) {
            const scrollTargetElement = document.getElementById(targetId);
            if (scrollTargetElement) {
                // Scroll to the specific target element within the section, centering it in the viewport
                scrollTargetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                console.error("Invalid target ID for scrolling");
            }
        } else {
            // Check if the target is above or below the current scroll position
            const targetPosition = targetElement.getBoundingClientRect().top;
            const currentPosition = sourceElement.getBoundingClientRect().top;

            if (targetPosition < currentPosition) {
                // Scroll upwards
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // Scroll downwards
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        // Remove active from source after animation completes
        setTimeout(() => {
            sourceElement.classList.remove('active');
            const autofocusInput = targetElement.querySelector('input[autofocus]');
            if (autofocusInput) {
                autofocusInput.focus();
            }
        }, 600);
    });
}

/**
 * Handles language selection and sets welcome text.
 */
function handleLanguageSelect(selectedLanguage) {
    fetch('/register/u/welcome_text', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ language: selectedLanguage }) // Post selected language to the server
    }).then(response => response.json())
        .then(data => {
            // If any error present, flash and exit
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }

            // Update welcome text with the translated version from the server
            const welcomeTextElement = document.getElementById('welcome-text');
            if (welcomeTextElement) {
                welcomeTextElement.textContent = data.text;
            }

            handleSectionScroll('reg-lang', 'reg-name', 'name-input-container'); // Scroll to the name input section
        })
        .catch(error => {
            // Log any errors that occur during the fetch request
            console.error("Error fetching translation (POST /register/u/welcome_text):", error);
            sendFlashMessage("Something went wrong. Please try again later.", 'error');
        }
    );
}

/**
 * Handles first name input validation and submission.
 * @param {boolean} submit - Whether to submit the name to the server for greeting text generation.
 * - If submit is false, it only validates the input and updates styling without making a server request.
 * - If submit is true, it validates the input and sends it to the server to get a personalised greeting text, then scrolls to the next section.
 */
function handleNameInput(submit = false) {
    const fnameElement = document.getElementById('first-name');
    const next = document.querySelector('.active .next');

    if (!fnameElement) {
        console.error("First name input element not found");
        return;
    }

    if (!fnameElement.value) {
        if (submit) {
            // If trying to submit with an empty name field, show error and add styling
            sendFlashMessage("First name is required.", 'error');
            addErrorStyling(fnameElement, submit);
        }
        if (!submit) resetStyling(fnameElement); // If field is empty, remove styling
        next.disabled = true; // Invalid input, disable next button
        return; // Exit early
    }

    next.disabled = false; // Enable next button if there is any input

    // If submitting, send the name to the server to validate and get greeting text, then scroll to the next section
    if (submit) {
        fetch('/register/u/user_hello', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ first_name: fnameElement.value }) // Post first name to the server
        }).then(response => response.json())
            .then(data => {
                // In the case name validation fails or any other error occurs, flash the error message and exit
                const error = data.error; // Returns null if no error
                if (error) {
                    sendFlashMessage(error, 'error');
                    return;
                }

                // Update greeting text with the personalised version from the server
                const helloElement = document.getElementById('hello-text');
                // If the element to display the greeting text is not found, log an error and exit
                if (!helloElement) {
                    console.error("Hello text element not found");
                    return;
                }

                // Request would fetch translated greeting text based on the user's first name and selected language
                // Update helloElement text content with the translated greeting text
                helloElement.textContent = data.text;

                // Scroll to the email input section
                handleSectionScroll('reg-name', 'reg-email', 'email-input-container');
            })
            .catch(error => {
                // In the case of any error, log the error and flash a generic error message to the user
                console.error("Error fetching translation (POST /register/u/user_hello):", error);
                sendFlashMessage("Something went wrong. Please try again later.", 'error');
            }
            );
    } else {
        // If not submitting, just validate the name input by sending it to the server.
        // This provides real-time feedback on the validity of the name input.
        fetch('/register/u/verify_name', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ name: fnameElement.value }) // Post first name to the server for validation
        }).then(response => response.json())
            .then(data => {
                if (data.error) {
                    // if any error is returned from the server, add error styling to the input and flash the error message
                    addErrorStyling(fnameElement, submit);
                    fnameElement.title = data.error; // Set the title attribute to show the error message on hover
                    return;
                }

                // If no error, add success styling to the input and remove any title attribute
                fnameElement.title = ""; // Clear the title attribute to remove any previous error message on hover
                addSuccessStyling(fnameElement);
            });
    }
}

/**
 * Handles email input validation and submission.
 * @param {boolean} submit - Whether to submit the email to the server to send a verification code.
 * - If submit is false, it only validates the input and updates styling without making a server request.
 * - If submit is true, it validates the input and sends it to the server to send a verification code, then scrolls to the next section.
 */
function handleEmailInput(submit = false) {
    // Get the email input element and the next button within the active section
    const emailElement = document.getElementById('email');
    const next = document.querySelector('.active .next');

    // If email input element is not found, log an error and exit
    if (!emailElement) {
        console.error("Email input element not found");
        return;
    }

    // If email field is empty, reset styling and disable next button
    if (!emailElement.value) {
        resetStyling(emailElement);
        next.disabled = true;
        return;
    }

    // Enable next button if there is any input (further validation will be done on the server)
    next.disabled = false;

    // If submitting, send the email to the server to validate and send a verification code, then scroll to the next section
    fetch('/register/u/send_verification_code', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ email: emailElement.value, submit: submit }) // Post email to the server to validate and send verification code. Also include whether this is a submit action or just validation for styling purposes
    })
        .then(response => response.json())
        .then(data => {
            const error = data.error; // Assume error is coming from the response
            if (error) {
                // If any error is returned from the server, add error styling to the input and flash the error message
                if (submit) sendFlashMessage(error, 'error'); // Flash error message
                addErrorStyling(emailElement, submit); // Add error styling to email input
                return;
            }

            addSuccessStyling(emailElement); // Add success styling to email input

            // If submitting and no error, scroll to the verification code section
            if (submit) {
                handleSectionScroll('reg-email', 'reg-verify', 'verification-code-container'); // Scroll to the next section
                
                const emailDisplayElement = document.getElementById('email-display');
                if (emailDisplayElement) {
                    emailDisplayElement.textContent = data.email; // Display obfuscated email
                }

                if (!data.allowSendEmails) {
                    /**
                     * If the server indicates that sending emails is not allowed (e.g. in a development environment),
                     * flash a message to the user indicating that the OTP has defaulted to a known value.
                        @see Documentation D-AE03
                    */
                    sendFlashMessage("Mail Service Disabled. OTP defaulted to 123456.", 'error');
                }

                spamPrevention(document.getElementById('resend-code-btn'), 120 * 1000); // Prevent clicking the resend button on page load
            }
        })
        .catch(error => {
            // In the case of any error, log the error and flash a generic error message to the user
            console.error("Error sending verification code:", error);
            sendFlashMessage("Something went wrong. Please try again later.", 'error');
        });
}

/**
 * Scrolls from the OTP verification section to the email input section.
 * Used for when the user clicks "Update Email" in the OTP verification section
 */
function scrollToEmail() {
    handleSectionScroll('reg-verify', 'reg-email', 'email-input-container');
}

/**
 * Helper function to resend the verification code to the user's email.
 * Called when the user clicks the "Resend Code" button in the OTP verification section.
 */
function resendVerificationCode() {
    fetch('/auth/verify_email', {
        method: 'POST',
        headers: getHeaders(),
    }).then(response => response.json())
        .then(data => {
            // Log any errors that occur during the resend request and flash a generic error message to the user
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }

            // Log success and flash a confirmation message to the user
            sendFlashMessage("Verification code resent to your email.", 'info');
        })
        .catch(error => {
            // Log and flash any errors that occur during the resend request
            console.error("Error resending verification code:", error);
            sendFlashMessage("Something went wrong. Please try again later.", 'error');
        }
    );
}

/**
 * Handles verification code input and validation.
 * @param {boolean} submit - Whether to submit the code for verification.
 * - If submit is false, it only validates the input and updates styling without making a server request.
 * - If submit is true, it validates the input and sends it to the server to verify the code, then scrolls to the next section if successful.
 */
function handleVerificationCodeInput(submit = false) {
    const codeElement = document.getElementById('verification-code');
    const code = codeElement.value.trim();
    const next = document.querySelector('.active .next');

    if (!code) { // If code field is empty, reset styling and disable next button
        resetStyling(codeElement)
        next.disabled = true;
        return;
    } else if (!/^\d{6}$/.test(code)) { // If code is not a 6-digit number, add error styling and disable next button
        addErrorStyling(codeElement);
        next.disabled = true;
        return;
    }

    addSuccessStyling(codeElement)
    next.disabled = false;

    if (submit) fetch('/register/u/verify_otp', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ code: code }) // Post the verification code to the server for validation
    })
        .then(response => response.json())
        .then(data => {
            // Flash and log any errors during validation
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                addErrorStyling(codeElement, submit);
                return;
            }

            // Scroll to the password input section if verification is successful
            const txt = document.getElementById('secret-text');
            txt.textContent = data.secret_text; // Update translated pwd secret text
            handleSectionScroll('reg-verify', 'reg-pwd', 'password-input-container');
        })
        .catch(error => {
            // Log and flash any errors that occur during the verification request
            console.error("Error verifying code:", error);
            sendFlashMessage("Something went wrong. Please try again later.", 'error');
        });
}

/**
 * Handles submission of the registration form by sending the password and confirmation to the server to create the account.
 * If successful, redirects the user to the login page. If there is an error, flashes the error message to the user.
 */
function submitRegistrationForm() {
    fetch('/auth/create', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            // Post pwd and confirm_pwd to the server for validation and account creation
            password: document.getElementById('password').value,
            confirm_password: document.getElementById('confirm-password').value
        })
    }).then(response => response.json())
        .then(data => {
            if (!data.error) {
                // If no errors, redirect to the login page
                window.location.href = '/login';
            } else {
                // If there is an error, flash the error message to the user
                sendFlashMessage(data.error, 'error');
            }
        }
        // Log and flash any errors that occur during the account creation request
        ).catch(error => {
            console.error("Error creating account:", error);
            sendFlashMessage("Something went wrong. Please try again later.", 'error');
        }
    );
}

document.addEventListener("DOMContentLoaded", () => {
    // On page load, set up event listeners for the language dropdown and options

    const dropdown = document.getElementById("language-dropdown");
    if (!dropdown) return; // Exit if dropdown not found
    const toggle = dropdown.querySelector(".dropdown-toggle");
    const label = dropdown.querySelector(".dropdown-label");
    const hiddenInput = document.getElementById("language-hidden");
    const options = dropdown.querySelectorAll(".dropdown-option");

    toggle.addEventListener("click", () => {
        // Add event listener to the dropdown toggle to open/close the dropdown menu when clicked
        dropdown.classList.toggle("open");
    });

    options.forEach(option => {
        // Add event listeners to each dropdown option to handle selection
        option.addEventListener("click", () => {
            const value = option.dataset.value;
            const text = option.textContent;

            // Update the dropdown label and hidden input value based on the selected option
            label.textContent = text;
            hiddenInput.value = value;

            // Remove 'selected' class and add to currently selected option for styling
            // This is not necessary since the dropdown hides almost immediately after selection,
            // but ensures that styling is applied correctly in the brief moment before the section changes.
            options.forEach(o => o.classList.remove("selected"));
            option.classList.add("selected"); // Add selected class to the currently selected option

            // Close dropdown
            dropdown.classList.remove("open");

            // Handle language selection
            handleLanguageSelect(value);
        });
    });

    // Add event listener to the document to close the dropdown if clicking outside of it
    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open");
        }
    });
});

// Add event listener for form submission to handle registration form submission when the user clicks the final "Submit" button
document.getElementById('form').addEventListener('submit', e => {
    e.preventDefault();
    submitRegistrationForm();
});

// Add event listener to handle "Enter" key presses for accessibility and convenience,
// allowing users to navigate through the registration sections and submit the form using the keyboard
document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();

        const btn = document.querySelector('.active .next');
        if (btn) {
            // Click the next button in the active section
            btn.focus()
            btn.click();
        }
    }
});
