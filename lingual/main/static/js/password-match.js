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
        element.style.boxShadow = "0 0 5px red";
    }
    return false;
}

function checkSubmit() {
    const password = document.getElementById('password');
    const confirm_password = document.getElementById('confirm-password');
    const submit = document.getElementById('pwd-submit');
    
    submit.disabled = !(validatePassword(password) && validatePasswordMatch(confirm_password));
}
