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

function handleLanguageSelect(selectedLanguage) {
    /** Handles language selection and sets welcome text */
    fetch('/register/u/welcome_text', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ language: selectedLanguage })
    }).then(response => response.json())
        .then(data => {
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }

            const welcomeTextElement = document.getElementById('welcome-text');
            if (welcomeTextElement) {
                welcomeTextElement.textContent = data.text;
            }

            handleSectionScroll('reg-lang', 'reg-name', 'name-input-container');
        })
        .catch(error => {
            console.error("Error fetching translation:", error);
        }
        );
}

function handleNameInput(submit = false) {
    /** Handles first name input and validation */
    const fnameElement = document.getElementById('first-name');
    const next = document.querySelector('.active .next');

    if (submit) {
        if (!fnameElement.value) {
            sendFlashMessage("First name is required.", 'error');
            addErrorStyling(fnameElement, submit);
            next.disabled = true;
            return;
        }
    } else if (!fnameElement.value) {
        resetStyling(fnameElement);
        return;
    }

    next.disabled = false;

    if (submit) {
        fetch('/register/u/user_hello', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ first_name: fnameElement.value })
        }).then(response => response.json())
            .then(data => {
                const error = data.error;
                if (error) {
                    sendFlashMessage(error, 'error');
                    return;
                }

                const helloElement = document.getElementById('hello-text');

                if (!helloElement) {
                    console.error("Hello text element not found");
                    return;
                }

                helloElement.textContent = data.text;

                handleSectionScroll('reg-name', 'reg-email', 'email-input-container');
            })
            .catch(error => {
                console.error("Error fetching translation:", error);
            }
            );
    } else {
        fetch('/register/u/verify_name', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ name: fnameElement.value })
        }).then(response => response.json())
            .then(data => {
                if (data.error) {
                    addErrorStyling(fnameElement, submit);
                    return;
                }

                addSuccessStyling(fnameElement);
            });
    }
}

function handleEmailInput(submit = false) {
    /** Handles email input and validation */
    const emailElement = document.getElementById('email');
    const next = document.querySelector('.active .next');

    if (!emailElement.value) {
        resetStyling(emailElement);
        next.disabled = true;
        return;
    }

    next.disabled = false;

    fetch('/register/u/send_verification_code', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ email: emailElement.value, submit: submit })
    })
        .then(response => response.json())
        .then(data => {
            const error = data.error; // Assume error is coming from the response
            if (error) {
                if (submit) sendFlashMessage(error, 'error'); // Flash error message
                addErrorStyling(emailElement, submit); // Add error styling to email input
                return;
            }

            addSuccessStyling(emailElement); // Add success styling to email input

            if (submit) {
                handleSectionScroll('reg-email', 'reg-verify', 'verification-code-container'); // Scroll to the next section
                const emailDisplayElement = document.getElementById('email-display');

                if (emailDisplayElement) {
                    emailDisplayElement.textContent = data.email; // Display email
                }

                spamPrevention(document.getElementById('resend-code-btn'), 120 * 1000); // Prevent clicking the resend button on page load
            }
        })
        .catch(error => {
            console.error("Error sending verification code:", error);
        });
}

function scrollToEmail() {
    handleSectionScroll('reg-verify', 'reg-email', 'email-input-container');
}

function resendVerificationCode() {
    fetch('/auth/verify_email', {
        method: 'POST',
        headers: getHeaders(),
    }).then(response => response.json())
        .then(data => {
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }
            sendFlashMessage("Verification code resent to your email.", 'info');
        })
        .catch(error => {
            console.error("Error resending verification code:", error);
        }
        );
}

function handleVerificationCodeInput(submit = false) {
    /** Handles verification code input and validation */
    const codeElement = document.getElementById('verification-code');
    const code = codeElement.value.trim();
    const next = document.querySelector('.active .next');

    if (!code) {
        resetStyling(codeElement)
        next.disabled = true;
        return;
    } else if (!/^\d{6}$/.test(code)) {
        addErrorStyling(codeElement);
        next.disabled = true;
        return;
    }

    addSuccessStyling(codeElement)
    next.disabled = false;

    if (submit) fetch('/register/u/verify_otp', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ code: code })
    })
        .then(response => response.json())
        .then(data => {
            const error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                codeElement.classList.add('error');
                setTimeout(() => {
                    codeElement.classList.remove('error');
                }, 1000);
                return;
            }

            const txt = document.getElementById('secret-text');
            txt.textContent = data.secret_text;
            handleSectionScroll('reg-verify', 'reg-pwd', 'password-input-container');
        })
        .catch(error => {
            console.error("Error verifying code:", error);
        });
}

function submitRegistrationForm() {
    /** Submits the registration form to create a new account */
    fetch('/auth/create', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            password: document.getElementById('password').value,
            confirm_password: document.getElementById('confirm-password').value
        })
    }).then(response => response.json())
        .then(data => {
            if (!data.error) {
                window.location.href = '/login';
            } else {
                sendFlashMessage(data.error, 'error');
            }
        }
        ).catch(error => {
            console.error("Error creating account:", error);
        }
        );
}

/**
 * Influenced by:
 *  - https://medium.com/@kyleducharme/developing-custom-dropdowns-with-vanilla-js-css-in-under-5-minutes-e94a953cee75
 *  - https://developers.knowivate.com/old/@kheersagar/designing-a-custom-select-dropdown-with-html-css-and-javascript
 * 
 * My adaptation was refined by AI to fix visual issues and meet my requirements. Refer to AI declaration.
 */ // TODO: Add to AI Declaration

document.addEventListener("DOMContentLoaded", () => {
    const dropdown = document.getElementById("language-dropdown");
    if (!dropdown) return; // Exit if dropdown not found
    const toggle = dropdown.querySelector(".dropdown-toggle");
    const label = dropdown.querySelector(".dropdown-label");
    const hiddenInput = document.getElementById("language-hidden");
    const options = dropdown.querySelectorAll(".dropdown-option");

    toggle.addEventListener("click", () => {
        dropdown.classList.toggle("open");
    });

    options.forEach(option => {
        option.addEventListener("click", () => {
            const value = option.dataset.value;
            const text = option.textContent;

            label.textContent = text;
            hiddenInput.value = value;

            options.forEach(o => o.classList.remove("selected"));
            option.classList.add("selected");

            dropdown.classList.remove("open");

            handleLanguageSelect(value);
        });
    });

    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open");
        }
    });
});

document.getElementById('form').addEventListener('submit', e => {
    e.preventDefault();
    submitRegistrationForm();
});

document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();

        const btn = document.querySelector('.active .next');
        if (btn) {
            btn.focus()
            btn.click();
        }
    }
});
