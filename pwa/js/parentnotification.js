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
            <input type="text" name="input-${escapeHtml(f.id)}">
            `;
		} else if (f.type == "single-choice") {
			f.choices.forEach((choice) => {
				const id = getUniqueId();
				output += `
                <input type="radio" value="${escapeHtml(choice.val)}" name="input-${escapeHtml(f.id)}" id="${id}"> <label for="${id}">${escapeHtml(choice.label)}</label>
                `;
			});
		}

		return output;
	}

	// Sammelt die Antworten des Feedback-Formulars
	function collectFeedback(notificationEl, fields) {
		const result = {};
		fields.forEach((f) => {
			const inputName = `input-${f.id}`;
			if (f.type === "single-choice") {
				const checked = notificationEl.querySelector(
					`input[name="${inputName}"]:checked`
				);
				result[String(f.id)] = checked ? checked.value : "";
			} else {
				const input = notificationEl.querySelector(
					`input[name="${inputName}"]`
				);
				result[String(f.id)] = input ? input.value : "";
			}
		});
		return result;
	}

	data.parent_notifications.forEach((notification) => {
		const notificationEl = document.createElement("div");
		notificationEl.classList.add("notification-el");

		// attachments
		let att = [];
		try {
			att = JSON.parse(notification.attachments || "[]");
		} catch (e) {
			att = [];
		}
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
                            <a href="/files/${encodeURIComponent(a)}" target="_blank">
                                <button class="small">${escapeHtml(a)}</button>
                            </a>`
						)
						.join("")}
                </details>`
				: `<span class="mini-info">Keine Anhänge</span>`;

		// feedback
		let feedback = [];
		try {
			feedback = JSON.parse(notification.feedback || "[]");
		} catch (e) {
			feedback = [];
		}
		const feedbackEl =
			feedback.length > 0
				? `
                <details class="subject-group">
                    <summary>Rückmeldung</summary>
                    ${feedback
						.map(
							(f) => `
                            <div class="feedback-el">
                                <span>${escapeHtml(f.label)}</span>
                                ${buildFeedback(f)}
                            </div>
                            `
						)
						.join("")}
					<button class="small send-feedback-btn">Senden</button>
                </details>`
				: `<span class="mini-info">Keine Rückmeldung</span>`;

		// date
		const dtString = formatLocalDateTime(notification.created_at);

		notificationEl.innerHTML = `
            <div>
                <span class="title">${escapeHtml(notification.title)}</span>
                <span class="body">${escapeHtml(notification.body)}</span>
            </div>
            ${attachmentsEl}
            ${feedbackEl}
            <span class="mini-info">erstellt am ${escapeHtml(dtString)}</span>
        `;
		notificationsEl.appendChild(notificationEl);

		// Feedback absenden
		const sendBtn = notificationEl.querySelector(".send-feedback-btn");
		if (sendBtn) {
			sendBtn.onclick = async () => {
				const payload = collectFeedback(notificationEl, feedback);
				sendBtn.disabled = true;
				try {
					const res = await fetch("/api/v1/parentnotification/feedback", {
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify({
							notification_id: notification.id,
							feedback: payload
						})
					});
					if (!res.ok) {
						const err = await res.json().catch(() => ({}));
						alert(
							err.detail || "Fehler beim Senden der Rückmeldung."
						);
						return;
					}
					alert("Rückmeldung gesendet.");
					sendBtn.textContent = "Gesendet";
				} catch (err) {
					console.error(err);
					alert("Netzwerkfehler: " + err.message);
				} finally {
					sendBtn.disabled = false;
				}
			};
		}
	});
}

main();
