/**
 * 
 * @param {HTMLElement} sourceSection 
 * @param {*} targetSection 
 * @param {*} targetId 
 * @returns 
 */
function handleSectionScroll(sourceSectionId, targetSectionId, targetId = null) {
    const sourceElement = document.getElementById(sourceSectionId);
    const targetElement = document.getElementById(targetSectionId);

    if (!sourceElement || !targetElement) {
        console.error("Invalid source or target section ID");
        return;
    }

    document.body.style.overflowY = 'hidden';

    targetElement.classList.add('active');

    if (targetId) {
        const scrollTargetElement = document.getElementById(targetId);
        if (scrollTargetElement) {
            scrollTargetElement.scrollIntoView({ behavior: 'smooth' });
        } else {
            console.warn(`Element with id "${targetId}" not found for scrolling.`);
        }
    } else {
        targetElement.scrollIntoView({ behavior: 'smooth' });
    }

    setTimeout(() => {
        sourceElement.classList.remove('active');
        document.body.style.overflowY = 'auto';
    }, 500);

}

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

function handleLanguageSelect(selectedLanguage) {
    fetch('/register/u/welcome_text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ language: selectedLanguage })
    }).then(response => response.json())
        .then(data => {
            error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }

            const welcomeTextElement = document.getElementById('welcome-text');
            if (welcomeTextElement) {
                welcomeTextElement.textContent = data.text;
            }

            handleSectionScroll('reg-lang', 'reg-name', 'welcome-text');
        })
        .catch(error => {
            console.error("Error fetching translation:", error);
        }
        );
}

function handleNameInput(element = null) {
    const fnameElement = document.getElementById('first-name');
    const lnameElement = document.getElementById('last-name');
    if (!element) {
        if (!fnameElement.value || !lnameElement.value) {
            if (!element) sendFlashMessage("First name or last name input element not found.", 'error');
            return;
        }
    } else if (!element.value) {
        resetStyling(element);
        return;
    }

    if (element) {
        fetch('register/u/verify_name', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: element.value, type: element.id })
        }).then(response => response.json())
            .then(data => {
                if (data.error) {
                    if (!element) sendFlashMessage(data.error, 'error');
                    addErrorStyling(fnameElement, !element);
                    addErrorStyling(lnameElement, !element);
                    return;
                } else if (data.f_error) {
                    if (!element) sendFlashMessage(data.f_error, 'error');
                    addErrorStyling(fnameElement, !element);
                    return;
                } else if (data.l_error) {
                    if (!element) sendFlashMessage(data.l_error, 'error');
                    addErrorStyling(lnameElement, !element);
                    return;
                }

                addSuccessStyling(element)
            });
    }

    if (!element) fetch('/register/u/user_hello', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ first_name: fnameElement.value, last_name: lnameElement.value })
    }).then(response => response.json())
        .then(data => {
            error = data.error;
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

            handleSectionScroll('reg-name', 'reg-email', 'hello-text');
        })
        .catch(error => {
            console.error("Error fetching translation:", error);
        }
        );
}

function handleEmailInput(submit = false) {
    const emailElement = document.getElementById('email');

    fetch('/register/u/send_verification_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: emailElement.value })
    }).then(response => response.json())
        .then(data => {
            error = data.error;
            if (error) {
                if (submit) sendFlashMessage(error, 'error');
                addErrorStyling(emailElement, submit);
                return;
            }

            const emailDisplayElement = document.getElementById('email-display');
            if (emailDisplayElement) {
                emailDisplayElement.textContent = data.email;
            }

            handleSectionScroll('reg-email', 'reg-verify', 'verify-text');
        })
        .catch(error => {
            console.error("Error sending verification code:", error);
        }
        );
}

function scrollToEmail() {
    emailElement = document.getElementById('reg-email');

    handleSectionScroll('reg-verify', 'reg-email');

    document.getElementById('reg-email').focus({ preventScroll: true });
}

function resendVerificationCode() {
    fetch('/auth/verify_email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    }).then(response => response.json())
        .then(data => {
            error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }
            // TODO: Implement spam prevention
            sendFlashMessage("Verification code resent to your email.", 'info');
        })
        .catch(error => {
            console.error("Error resending verification code:", error);
        }
        );
}

function handleVerificationCodeInput() {

    const codeElement = document.getElementById('verification-code');
    const code = codeElement.value.trim();

    if (code.length === 0) {
        codeElement.style.borderColor = "red";
        codeElement.style.boxShadow = "0 0 5px red";
        sendFlashMessage("Please enter the verification code sent to your email.", 'error');
        return;
    }

    fetch('/register/u/verify_otp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: code })
    })
        .then(response => response.json())
        .then(data => {

            error = data.error;
            if (error) {
                sendFlashMessage(error, 'error');
                return;
            }

            const txt = document.getElementById('secret-text');
            if (data.error === null) {

                txt.textContent = data.secret_text;

                handleSectionScroll('reg-verify', 'reg-pwd', 'secret-text');
            } else {
                codeElement.classList.add('error');
                setTimeout(() => {
                    codeElement.classList.remove('error');
                }, 1000);
            }
        })
        .catch(error => {
            console.error("Error verifying code:", error);
        });
}

function validatePassword(element) {
    const password = element.value;
    const confirmPasswordElement = document.getElementById('confirm-password');

    const lengthRequirement = password.length >= 8;
    const specialRequirement = /[!@#$%^&*(),.?":{}|<>]/.test(password); // Checks for ! @ # $ % ^ & * ( ) , . ? " : { } | < >
    const numberRequirement = /[0-9]/.test(password);
    const upperRequirement = /[A-Z]/.test(password);
    const lowerRequirement = /[a-z]/.test(password);

    document.getElementById('pwd-char').className = lengthRequirement ? 'valid' : 'invalid';
    document.getElementById('pwd-special').className = specialRequirement ? 'valid' : 'invalid';
    document.getElementById('pwd-num').className = numberRequirement ? 'valid' : 'invalid';
    document.getElementById('pwd-upper').className = upperRequirement ? 'valid' : 'invalid';
    document.getElementById('pwd-lower').className = lowerRequirement ? 'valid' : 'invalid';
    validatePasswordMatch(confirmPasswordElement);

    if (password.length === 0) {
        element.style.borderColor = "";
        element.style.boxShadow = "";
    }
    else if (lengthRequirement && specialRequirement && numberRequirement && upperRequirement && lowerRequirement) {
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true;
    } else {
        element.style.borderColor = "red";
        element.style.boxShadow = "0 0 5px red";
    }
    return false;
}

function validatePasswordMatch(element) {
    const password = document.getElementById('password').value;
    const confirmPassword = element.value;

    document.getElementById('pwd-match').className = ((password === confirmPassword) && password.length > 0) ? 'valid' : 'invalid';

    if (confirmPassword.length === 0) {
        element.style.borderColor = "";
        element.style.boxShadow = "";
    } else if (password === confirmPassword) {
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true;
    } else {
        element.style.borderColor = "red";
        element.style.boxShadow = " 0 0 5px red"
    }
    return false;
}

function checkSubmit() {
    const password = document.getElementById('password');
    const confirm_password = document.getElementById('confirm-password');

    if (validatePassword(password) && validatePasswordMatch(confirm_password)) {
        const submit = document.getElementById('pwd-submit');
        submit.disabled = false;
    }
}

function submitRegistrationForm() {
    fetch('auth/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            password: document.getElementById('password').value
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
