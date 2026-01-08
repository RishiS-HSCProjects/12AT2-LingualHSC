
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
    button.disabled = true;
    button.title = "Button temporarily disabled for " + (timeout / 1000) + " seconds.";

    setTimeout(() => {
        button.disabled = false;
        button.title = "";
    }, timeout);
}
