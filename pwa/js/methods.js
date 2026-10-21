// Hilfsfunktionen, die auf allen Seiten der PWA zur Verfuegung stehen.

// Escaping fuer Werte, die in innerHTML landen (verhindert XSS).
function escapeHtml(str) {
	if (!str && str !== 0) return "";
	return String(str)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

async function getProfile() {
	const response = await fetch("/api/v1/user/profile", {
		method: "GET",
		credentials: "include"
	});

	if (response.status === 200) {
		const data = await response.json();
		console.log("User is logged in:", data);
		return data;
	} else {
		window.location.href = "/app/login.html";
	}
}
