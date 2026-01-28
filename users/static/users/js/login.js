
// Hide the login button in the title bar if present.
document.addEventListener("DOMContentLoaded", function() {
    var loginTitleButton = document.querySelector(".login-title-btn");
    if (loginTitleButton) {
        loginTitleButton.style.display = "none";
    }

    // Autofocus on username field
    var usernameField = document.getElementById("username");
    if (usernameField) {
        usernameField.focus();
    }

    // Handle Enter key press for form submission
    var loginInputs = document.querySelectorAll(".login-input");
    loginInputs.forEach(function(input) {
        input.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                var form = input.closest("form");
                if (form) {
                    form.submit();
                }
            }
        });
    });
});
