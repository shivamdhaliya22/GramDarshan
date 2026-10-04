const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const navLinks = document.getElementById("navLinks");

if (mobileMenuBtn && navLinks) {

    mobileMenuBtn.addEventListener("click", function () {
        navLinks.classList.toggle("active");

        if (navLinks.classList.contains("active")) {
            mobileMenuBtn.innerHTML = "✕";
        } else {
            mobileMenuBtn.innerHTML = "☰";
        }
    });

}