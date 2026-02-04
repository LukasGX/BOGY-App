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
async function checkLogin() {
	const response = await fetch("/profile", {
		method: "GET",
		credentials: "include"
	});

	if (response.status === 200) {
		const data = await response.json();
		console.log("User is logged in:", data);
	} else {
		console.log("User is not logged in, redirecting to login page.");
		window.location.href = "/app/login.html";
	}
}

checkLogin();
