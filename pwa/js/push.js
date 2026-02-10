const VAPID_PUBLIC_KEY =
	"BOzTsLFXHSxIDtzgBVWzRGP8UmdYGbd3-0IF3I-dQF30gwSpG_AfHRrS8LV4Qb-U2linj7K0xlDxzRNe04AqqHA";

const urlBase64ToUint8Array = (base64String) => {
	const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
	const base64 = (base64String + padding)
		.replace(/\-/g, "+")
		.replace(/_/g, "/");
	const rawData = window.atob(base64);
	return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
};

const activatePushBtn = document.getElementById("btn-activatepush");

if (activatePushBtn)
	activatePushBtn.onclick = async () => {
		if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
			alert("Push nicht unterstützt");
			return;
		}

		// SW registrieren
		const reg = await navigator.serviceWorker.register("/app/js/sw/sw.js");

		// Permission
		const permission = await Notification.requestPermission();
		if (permission !== "granted") return alert("Permission verweigert");

		// Subscription erstellen
		const subscription = await reg.pushManager.subscribe({
			userVisibleOnly: true,
			applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
		});

		// An Backend senden
		await fetch("/api/push/subscribe", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(subscription)
		});

		alert("Push aktiviert!");
	};
