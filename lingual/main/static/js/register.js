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

function handleLanguageSelect(selectedLanguage) {
    fetch('/register/u/welcome_text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ language: selectedLanguage })
    }).then(response => response.json())
        .then(data => {
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

/**
 * @param {HTMLElement} element
 */
function verifyName(element) {
    const name = element.value.trim();
    const nameRegex = /^[A-Za-z'\- ]{0,50}$/;
    if (name.length === 0) {
        element.style.borderColor = "";
        element.style.boxShadow = "";
        return false;
    } if (nameRegex.test(name)) {
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true;
    } else {
        element.style.borderColor = "red";
        element.style.boxShadow = "0 0 5px red";
        return false;
    }
}

/**
 * Tests is email includes "@" and "." to confirm basic validity.
 * 
 * @param {HTMLElement} element
 */
function verifyEmail(element) {
    const email = element.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email.length === 0) {
        element.style.borderColor = "";
        element.style.boxShadow = "";
        return false;
    } else if (emailRegex.test(email)) {
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true;
    } else {
        element.style.borderColor = "red";
        element.style.boxShadow = "0 0 5px red";
        return false;
    }
}

function handleNameInput() {
    const fnameElement = document.getElementById('first-name');
    const lnameElement = document.getElementById('last-name');

    if (!verifyName(fnameElement) || !verifyName(lnameElement)) {
        alert("Names can only include letters and spaces.");
        return;
    }

    fetch('/register/u/user_hello', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ first_name: fnameElement.value, last_name: lnameElement.value })
    }).then(response => response.json())
        .then(data => {
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

function handleEmailInput() {
    const emailElement = document.getElementById('email');
    if (!verifyEmail(emailElement)) {
        return;
    }
    fetch('/register/u/send_verification_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: emailElement.value })
    }).then(response => response.json())
        .then(data => {
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
    fetch('/auth/verify_email/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    }).then(response => response.json())
        .then(data => {
            // TODO: Implement spam prevention
            alert("Verification code resent to your email.");
        })
        .catch(error => {
            console.error("Error resending verification code:", error);
        }
        );
}

function handleVerificationCodeInput() {
    const codeElement = document.getElementById('verification-code');
    const code = codeElement.value.trim();

    fetch('/register/u/verify_otp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: code })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {

                document.getElementById('secret-text').textContent = data.secret_text;

                handleSectionScroll('reg-verify', 'reg-pwd', 'secret-text');
            } else {
                alert("Invalid verification code. Please try again.");
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

    document.getElementById('pwd-match').className = ((password === confirmPassword) && password.length > 0)  ? 'valid' : 'invalid';

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
    const password = document.getElementById('password').value;
    const confirm_password = document.getElementById('confirm-password').value;

    if (validatePassword(document.getElementById('password')) && validatePasswordMatch(document.getElementById('confirm-password'))) {
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
                window.location.href = '/app';
            } else {
                alert("Error creating account: " + data.error);
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