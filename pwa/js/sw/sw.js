self.addEventListener("push", (event) => {
	let data = {};
	try {
		data = event.data ? event.data.json() : {};
	} catch (e) {
		data = { title: "BOGY-App", body: event.data ? event.data.text() : "" };
	}

	const options = {
		body: data.body,
		icon: data.icon || "/app/resources/logo.png",
		badge: data.badge || "/app/resources/logo.png",
		vibrate: [100, 50, 100],
		data: { url: "/app/index.html" }
	};

	event.waitUntil(self.registration.showNotification(data.title || "BOGY-App", options));
});

self.addEventListener("notificationclick", (event) => {
	event.notification.close();
	event.waitUntil(
		clients.openWindow(event.notification.data?.url || "/app/index.html")
	);
});
