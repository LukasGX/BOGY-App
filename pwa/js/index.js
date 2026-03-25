// add click event listeners to the links
const tutoringLink = document.getElementById("app-tutoring");
const pwLink = document.getElementById("app-pw");
const wlanLink = document.getElementById("app-wlan");

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

if (wlanLink) {
	wlanLink.addEventListener("click", () => {
		window.location.href = "/app/wlan.html";
	});
}

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
