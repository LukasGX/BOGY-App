// add click event listeners to the links
const tutoringLink = document.getElementById("app-tutoring");
const pwLink = document.getElementById("app-pw");

if (tutoringLink) {
	tutoringLink.addEventListener("click", () => {
		window.location.href = "/app/tutoring.html";
	});
}

if (pwLink) {
	pwLink.addEventListener("click", () => {
		window.location.href = "/app/pw.html";
	});
}

// check login
getProfile();
