async function main() {
	// logged in
	let profile = await getProfile();
	if (!profile) profile = { tutoring: false };

	// get main elements
	const noneFoundMain = document.getElementById("page-nonefound");
	const foundSomeMain = document.getElementById("page-foundsome");
	const notificationsEl = document.getElementById("notifications");

	const response = await fetch("/api/v1/parentnotification/");
	const data = await response.json();

	if (data.parent_notifications.length > 0) {
		if (noneFoundMain) noneFoundMain.style.display = "none";
		if (foundSomeMain) foundSomeMain.style.display = "block";
	} else {
		if (noneFoundMain) noneFoundMain.style.display = "block";
		if (foundSomeMain) foundSomeMain.style.display = "none";
	}

	let usedIds = new Set();
	function getUniqueId() {
		let id;
		do {
			id = Math.random().toString(36).substr(2, 8);
		} while (usedIds.has(id));
		usedIds.add(id);
		return id;
	}

	function buildFeedback(f) {
		let output = "";
		if (f.type == "freetext") {
			output += `
            <input type="text" name="input-${f.id}">
            `;
		} else if (f.type == "single-choice") {
			f.choices.forEach((choice) => {
				const id = getUniqueId();
				output += `
                <input type="radio" value="${choice.val}" name="input-${f.id}" id="${id}"> <label for="${id}">${choice.label}</label>
                `;
			});
		}

		return output;
	}

	data.parent_notifications.forEach((notification) => {
		const notificationEl = document.createElement("div");
		notificationEl.classList.add("notification-el");

		// attachments
		const att = JSON.parse(notification.attachments);
		const attachments =
			att.length == 1 ? "1 Anhang" : `${att.length} Anhänge`;
		const attachmentsEl =
			att.length > 0
				? `
                <details class="subject-group">
                    <summary>${attachments}</summary>
                    ${att
						.map(
							(a) => `
                            <a href="/files/${a}" target="_blank">
                                <button class="small">${a}</button>
                            </a>`
						)
						.join("")}
                </details>`
				: `<span class="mini-info">Keine Anhänge</span>`;

		// feedback
		const feedback = JSON.parse(notification.feedback);
		const feedbackEl =
			feedback.length > 0
				? `
                <details class="subject-group">
                    <summary>Rückmeldung</summary>
                    ${feedback
						.map(
							(f) => `
                            <div class="feedback-el">
                                <span>${f.label}</span>
                                ${buildFeedback(f)}
                            </div>
                            `
						)
						.join("")}
					<button class="small">Senden</button>
                </details>`
				: `<span class="mini-info">Keine Rückmeldung</span>`;

		// date
		const date = new Date(notification.created_at);
		const dtString = date.toLocaleString("de-DE", {
			day: "2-digit",
			month: "2-digit",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
			hour12: false
		});
		notificationEl.innerHTML = `
            <div>
                <span class="title">${notification.title}</span>
                <span class="body">${notification.body}</span>
            </div>
            ${attachmentsEl}
            ${feedbackEl}
            <span class="mini-info">erstellt am ${dtString}</span>
        `;
		notificationsEl.appendChild(notificationEl);
	});
}

main();
