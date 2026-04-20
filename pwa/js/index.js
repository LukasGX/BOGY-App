// apps
const tutoringLink = document.getElementById("app-tutoring");
const wlanLink = document.getElementById("app-wlan");
const parentNotificationLink = document.getElementById(
	"app-parentnotification"
);
const pwLink = document.getElementById("app-pw");

if (tutoringLink) {
	tutoringLink.addEventListener("click", () => {
		window.location.href = "/app/tutoring.html";
	});
}

if (wlanLink) {
	wlanLink.addEventListener("click", () => {
		window.location.href = "/app/wlan.html";
	});
}

if (parentNotificationLink) {
	parentNotificationLink.addEventListener("click", () => {
		window.location.href = "/app/parentnotification.html";
	});
}

if (pwLink) {
	pwLink.addEventListener("click", () => {
		window.location.href = "/app/pw.html";
	});
}

// links
const linkUntis = document.getElementById("link-untis");
const linkMathegym = document.getElementById("link-mathegym");
const linkBycs = document.getElementById("link-bycs");
const linkMS = document.getElementById("link-ms");

if (linkUntis) {
	linkUntis.addEventListener("click", () => {
		window.open("https://bogy.webuntis.com", "_blank");
	});
}

if (linkMathegym) {
	linkMathegym.addEventListener("click", () => {
		window.open("https://mathegym.de", "_blank");
	});
}

if (linkBycs) {
	linkBycs.addEventListener("click", () => {
		window.open("https://bycs.de", "_blank");
	});
}

if (linkMS) {
	linkMS.addEventListener("click", () => {
		window.open("https://www.office.com", "_blank");
	});
}

// urgent push btn
const btnActivatePush = document.getElementById("btn-activatepush");
async function checkPushStatus() {
	if (!btnActivatePush) return;

	try {
		const res = await fetch("/api/v1/push/status");
		const data = await res.json();

		if (data.has_push) {
			btnActivatePush.style.display = "none";
		} else {
			btnActivatePush.style.display = "block";
		}
	} catch (err) {
		btnActivatePush.style.display = "block";
	}
}

checkPushStatus();

// check login
getProfile();

// check for wlan codes
async function wlanCodesCheck() {
	const response = await fetch("/api/v1/wlan/");
	const data = await response.json();
	const appWlanBox = document.getElementById("app-wlan-box");

	if (data.codes.length > 0) {
		const badge = document.createElement("div");
		badge.classList.add("badge");
		badge.textContent = data.codes.length;
		appWlanBox.appendChild(badge);
	}
}
wlanCodesCheck();

// check for pns
async function pnCheck() {
	const response = await fetch("/api/v1/parentnotification/");
	const data = await response.json();
	const appPNBox = document.getElementById("app-parentnotification-box");

	if (data.parent_notifications.length > 0) {
		const badge = document.createElement("div");
		badge.classList.add("badge");
		badge.textContent = data.parent_notifications.length;
		appPNBox.appendChild(badge);
	}
}
pnCheck();
