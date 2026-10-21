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

// Parst einen Zeitstempel aus der Datenbank ("2026-10-20 14:00:00.000000")
// als lokale Zeit. new Date("...") ist bei diesem Format nicht verlaesslich
// (Safari liefert Invalid Date) und wuerde UTC/Zeitzonen verschieben.
function parseLocalDate(value) {
	if (!value) return null;
	if (value instanceof Date) return value;

	const str = String(value).trim();
	const m = str.match(
		/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?/
	);
	if (m) {
		return new Date(
			Number(m[1]),
			Number(m[2]) - 1,
			Number(m[3]),
			Number(m[4]),
			Number(m[5]),
			Number(m[6] || 0)
		);
	}

	const parsed = new Date(str);
	return isNaN(parsed.getTime()) ? null : parsed;
}

// Formatiert einen Zeitstempel fuer die Anzeige (de-DE).
function formatLocalDateTime(value) {
	const date = parseLocalDate(value);
	if (!date) return "";
	return date.toLocaleString("de-DE", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
		hour12: false
	});
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
