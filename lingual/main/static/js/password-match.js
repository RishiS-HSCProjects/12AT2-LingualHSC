/**
 * Password validation script for registration form.
 * - Validates password strength and checks if password and confirm password match
 * - Update element styles and validity indicators based on validation results
 * - Enable submit button only when all validations pass
 */
function validatePassword(element) {
    // Get required elements
    const password = element.value;
    const confirmPasswordElement = document.getElementById('confirm-password');

    const lengthRequirement = password.length >= 8;
    const specialRequirement = /[!@#$%^&*(),.?":{}|<>]/.test(password); // Checks for ! @ # $ % ^ & * ( ) , . ? " : { } | < >
    const numberRequirement = /[0-9]/.test(password);
    const upperRequirement = /[A-Z]/.test(password);
    const lowerRequirement = /[a-z]/.test(password);

    // Update validity indicators
    const valid = 'valid';
    const invalid = 'invalid';
    document.getElementById('pwd-char').className = lengthRequirement ? valid : invalid;
    document.getElementById('pwd-special').className = specialRequirement ? valid : invalid;
    document.getElementById('pwd-num').className = numberRequirement ? valid : invalid;
    document.getElementById('pwd-upper').className = upperRequirement ? valid : invalid;
    document.getElementById('pwd-lower').className = lowerRequirement ? valid : invalid;
    validatePasswordMatch(confirmPasswordElement); // Re-validate confirm password to update match status if password changes

    if (password.length === 0) {
        // Reset styles if password field is empty
        element.style.borderColor = "";
        element.style.boxShadow = "";
    }
    else if (lengthRequirement && specialRequirement && numberRequirement && upperRequirement && lowerRequirement) {
        // If all requirements are met, set styles to indicate success
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true; // Return true if password is valid
    } else {
        // If any requirement is not met, set styles to indicate error
        element.style.borderColor = "red";
        element.style.boxShadow = "0 0 5px red";
    }

    return false; // Return false for any invalid password
}

/**
 * Validates if the confirm password matches the original password and updates styles accordingly.
 */
function validatePasswordMatch(element) {
    const password = document.getElementById('password').value; // Get the current value of the password field
    const confirmPassword = element.value; // Get the current value of the confirm password field

    // Update validity indicator for password match
    const valid = 'valid';
    const invalid = 'invalid';
    document.getElementById('pwd-match').className = ((password === confirmPassword) && password.length > 0) ? valid : invalid;

    if (confirmPassword.length === 0) {
        // Ignore empty confirm password field and reset styles
        element.style.borderColor = "";
        element.style.boxShadow = "";
    } else if (password === confirmPassword) {
        // If passwords match, set styles to indicate success
        element.style.borderColor = "green";
        element.style.boxShadow = "0 0 5px green";
        return true;
    } else {
        // If passwords do not match, set styles to indicate error
        element.style.borderColor = "red";
        element.style.boxShadow = "0 0 5px red";
    }

    return false; // Return false for invalid password match
}

/**
 * Checks if the submit button should be enabled based on the validity of the password and confirm password fields.
 */
function checkSubmit() {
    // Get the password and confirm password elements
    const password = document.getElementById('password');
    const confirm_password = document.getElementById('confirm-password');
    const submit = document.getElementById('pwd-submit');
    
    if (submit) { // Ensure the submit button exists to avoid null error
        // submit.disabled is set to the opposite of the combined validation results of password and confirm password
        submit.disabled = !(validatePassword(password) && validatePasswordMatch(confirm_password));
    }
}
