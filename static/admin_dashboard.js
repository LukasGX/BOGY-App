function openModal(content) {
	const modal = document.createElement("div");
	modal.className = "modal";

	const modalContent = document.createElement("div");
	modalContent.className = "modal-content";
	modalContent.innerHTML = content;

	const close = document.createElement("span");
	close.className = "modal-close";
	close.innerHTML = "&#10005;";
	close.onclick = () => {
		document.querySelectorAll(".modal").forEach((el) => {
			el.remove();
		});
	};

	modalContent.appendChild(close);
	modal.appendChild(modalContent);
	document.body.appendChild(modal);
}

function closeModal() {
	document.querySelectorAll(".modal").forEach((el) => {
		el.remove();
	});
}

// get btns
const btnDetailsClasses = document.getElementById("btn-details-classes");
const btnDetailsUsers = document.getElementById("btn-details-users");
const btnDetailsWlanCodes = document.getElementById("btn-details-wlan-codes");
const btnDetailsTutoring = document.getElementById("btn-details-tutoring");
const btnDetailsParentNotification = document.getElementById(
	"btn-details-parentnotifications"
);

async function clickOnClassCard(id) {
	closeModal();

	const classId = id.split("-")[1];

	const result = await fetch(`/api/v1/data/class/${classId}`);
	const data = await result.json();

	openModal(`
		<h2 data-class-id="${classId}" id="modal-h2">Klasse ${data.class.name} - Details</h2>
		<label for="class-name-input">Klassenname:</label>
		<input type="text" id="class-name-input" value="${data.class.name}" />

		<span>Schüler:</span>
			${
				data.class.student_count >= 1
					? `<div class="element-card-mini-container">` +
						data.students
							.map(
								(student) =>
									`<div class="element-card mini mini-user-card">
							<span>${student.username}</span>
							<span>${student.firstname} ${student.lastname}</span>
						</div>`
							)
							.join("") +
						`</div>`
					: "Keine<br />"
			}
		<span>Andere Benutzer:</span>
			${
				data.class.others_count >= 1
					? `<div class="element-card-mini-container">` +
						data.others
							.map(
								(other) =>
									`<div class="element-card mini mini-user-card">
							<span>${other.username}</span>
							<span>${other.firstname} ${other.lastname}</span>
						</div>`
							)
							.join("") +
						`</div>`
					: "Keine<br /><br />"
			}
		<button id="save-class-btn">Änderungen speichern</button>
		<button id="delete-class-btn" class="destructive">Klasse löschen</button>
	`);

	document.getElementById("save-class-btn").onclick = async () => {
		const modalH2 = document.getElementById("modal-h2");
		const classId = modalH2.getAttribute("data-class-id");
		const newName = document.getElementById("class-name-input").value;

		const response = await fetch(`/api/v1/data/class/${classId}`, {
			method: "PATCH",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({ new_name: newName })
		});

		if (response.ok) {
			window.location.reload();
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Ändern des Klassennamens</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="clickOnClassCard('class-${classId}')">OK</button>
			`);
		}
	};

	document.getElementById("delete-class-btn").onclick = async () => {
		const modalH2 = document.getElementById("modal-h2");
		const classId = modalH2.getAttribute("data-class-id");

		closeModal();
		openModal(`
			<h2 data-class-id="${classId}" id="modal-h2">Klasse löschen</h2>
			<p>Sind Sie sicher, dass Sie diese Klasse löschen möchten?</p>
			<button id="confirm-delete-btn" class="destructive">Ja, Klasse löschen</button>
			<button onclick="clickOnClassCard('class-${classId}')">Abbrechen</button>
		`);

		document.getElementById("confirm-delete-btn").onclick = async () => {
			const modalH2 = document.getElementById("modal-h2");
			const classId = modalH2.getAttribute("data-class-id");

			const response = await fetch(
				`/api/v1/administration/class/${classId}`,
				{
					method: "DELETE"
				}
			);

			const data = await response.json();

			if (response.ok) {
				window.location.reload();
			} else if (response.status === 409) {
				closeModal();

				openModal(`
				<h2>Fehler beim Löschen der Klasse</h2>
				<p>Die Klasse kann nicht gelöscht werden, da noch Benutzer der Klasse zugeordnet sind. Bitte entfernen Sie zuerst alle Schüler aus der Klasse.</p>
				<p>Betroffene Nutzer:</p>
				<div class="element-card-mini-container">
					${data.detail[0].users
						.map(
							(user) =>
								`<div class="element-card mini mini-user-card">
									<span>${user.username}</span>
									<span>${user.firstname} ${user.lastname}</span>
								</div>`
						)
						.join("")}
				</div>
			`);
			} else {
				closeModal();
				openModal(`
					<h2>Fehler beim Löschen der Klasse</h2>
					<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
					<button onclick="clickOnClassCard('class-${classId}')">OK</button>
				`);
			}
		};
	};
}

function addClass() {
	closeModal();

	openModal(`
		<h2>Klasse erstellen</h2>
		<label for="class-name-input">Klassenname:</label>
		<input type="text" id="class-name-input" />
		<button id="create-class-btn">Klasse erstellen</button>
	`);

	document.getElementById("create-class-btn").onclick = async () => {
		const className = document.getElementById("class-name-input").value;

		const response = await fetch("/api/v1/administration/class", {
			method: "PUT",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				className: className
			})
		});

		if (response.ok) {
			window.location.reload();
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Erstellen der Klasse</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="addClass()">OK</button>
			`);
		}
	};
}

btnDetailsClasses.onclick = async () => {
	const response = await fetch("/api/v1/data/get-classes");
	const data = await response.json();

	let classes = "";
	let ids = [];
	data.classes.forEach((cls) => {
		classes += `
			<div class="element-card class-card" id="class-${cls.id}">
				<span>${cls.name}</span>
				<span>Schüler: ${cls.student_count}</span>
				<span>Andere Benutzer: ${cls.others_count}</span>
			</div>
		`;
		ids.push(`class-${cls.id}`);
	});

	openModal(`
        <h2>Klassen - Details</h2>
		<div id="classes-container">
			${classes}
			<div class="element-card class-card add-element" id="add-class-card">
				<span>+</span>
				<span>Klasse erstellen</span>
			</div>
		</div>
    `);

	document
		.getElementById("classes-container")
		.addEventListener("click", (e) => {
			if (e.target.closest(".element-card")) {
				const id = e.target.closest(".element-card").id;

				if (id == "add-class-card") {
					addClass();
					return;
				}

				clickOnClassCard(id);
			}
		});
};

async function clickOnUserCard(id) {
	closeModal();

	const userId = id.split("-")[1];

	const response = await fetch(`/api/v1/data/user/${userId}`);
	const data = await response.json();

	const rolesResponse = await fetch("/api/v1/data/roles");
	const rolesData = await rolesResponse.json();

	const classesResponse = await fetch("/api/v1/data/get-classes");
	const classesData = await classesResponse.json();

	openModal(`
		<h2>Benutzer ${data.user.username} - Details</h2>
		<label for="role">Rolle:</label>
		<select id="roleSelect">
			${rolesData.roles
				.map(
					(role) =>
						`<option value="${role.id}" ${role.id == data.user.role_id ? "selected" : ""}>
					${role.german_name}
				</option>`
				)
				.join("")}
		</select>
		<label for="class">Klasse:</label>
		<select id="classSelect">
			<option value="0">Keine Klasse</option>
			${classesData.classes.map(
				(cls) =>
					`<option value="${cls.id}" ${
						cls.id == data.user.class_id ? "selected" : ""
					}>
					${cls.name}
				</option>`
			)}
		</select>
		<label for="username">Benutzername:</label>
		<input type="text" id="username" value="${data.user.username}" />
		<label for="firstname">Vorname:</label>
		<input type="text" id="firstname" value="${data.user.firstname}" />
		<label for="lastname">Nachname:</label>
		<input type="text" id="lastname" value="${data.user.lastname}" /><br /><br />
		<button id="save-user-btn">Änderungen speichern</button>
		<button id="reset-password-btn">Passwort zurücksetzen</button>
		<button id="delete-user-btn" class="destructive">Benutzer löschen</button>
	`);

	setTimeout(() => {
		new Choices("#roleSelect", {
			searchEnabled: false,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});

		new Choices("#classSelect", {
			searchEnabled: false,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	document.getElementById("save-user-btn").onclick = async () => {
		const newRole = document.getElementById("roleSelect").value;
		const newClass = document.getElementById("classSelect").value;
		const newUsername = document.getElementById("username").value;
		const newFirstname = document.getElementById("firstname").value;
		const newLastname = document.getElementById("lastname").value;

		const response = await fetch(`/api/v1/data/user/${userId}`, {
			method: "PATCH",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				new_role: newRole,
				new_class: newClass,
				new_username: newUsername,
				new_firstname: newFirstname,
				new_lastname: newLastname
			})
		});

		if (response.ok) {
			window.location.reload();
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Ändern der Benutzerdaten</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="clickOnUserCard('user-${userId}')">OK</button>
			`);
		}
	};

	document.getElementById("reset-password-btn").onclick = async () => {
		const response = await fetch(
			`/api/v1/administration/user/${userId}/reset-pw`,
			{
				method: "POST"
			}
		);

		if (response.ok) {
			const data = await response.json();
			closeModal();
			openModal(`
				<h2>Passwort zurückgesetzt</h2>
				<p>Das Passwort wurde erfolgreich zurückgesetzt.<br />Das neue Passwort lautet: <span class="fat">${data.new_password}</span></p>
				<button onclick="clickOnUserCard('user-${userId}')">OK</button>
			`);
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Zurücksetzen des Passworts</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="clickOnUserCard('user-${userId}')">OK</button>
			`);
		}
	};

	document.getElementById("delete-user-btn").onclick = async () => {
		closeModal();
		openModal(`
			<h2>Benutzer löschen</h2>
			<p>Sind Sie sicher, dass Sie diesen Benutzer löschen möchten?</p>
			<button id="confirm-delete-btn" class="destructive">Ja, Benutzer löschen</button>
			<button onclick="clickOnUserCard('user-${userId}')">Abbrechen</button>
		`);

		document.getElementById("confirm-delete-btn").onclick = async () => {
			const response = await fetch(
				`/api/v1/administration/user/${userId}`,
				{
					method: "DELETE"
				}
			);

			if (response.ok) {
				window.location.reload();
			} else {
				closeModal();
				openModal(`
					<h2>Fehler beim Löschen des Benutzers</h2>
					<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
					<button onclick="clickOnUserCard('user-${userId}')">OK</button>
				`);
			}
		};
	};
}

async function addUser() {
	closeModal();

	const rolesResponse = await fetch("/api/v1/data/roles");
	const rolesData = await rolesResponse.json();

	const classesResponse = await fetch("/api/v1/data/get-classes");
	const classesData = await classesResponse.json();

	openModal(`
		<h2>Benutzer erstellen</h2>
		<label for="role">Rolle:</label>
		<select id="roleSelect">
			${rolesData.roles
				.map(
					(role) =>
						`<option value="${role.id}">
					${role.german_name}
				</option>`
				)
				.join("")}
		</select>
		<label for="class">Klasse:</label>
		<select id="classSelect">
			<option value="0">Keine Klasse</option>
			${classesData.classes.map(
				(cls) =>
					`<option value="${cls.id}">
					${cls.name}
				</option>`
			)}
		</select>
		<label for="username">Benutzername:</label>
		<input type="text" id="username" />
		<label for="firstname">Vorname:</label>
		<input type="text" id="firstname" />
		<label for="lastname">Nachname:</label>
		<input type="text" id="lastname" /><br /><br />
		<button id="create-user-btn">Benutzer erstellen</button>
	`);

	setTimeout(() => {
		new Choices("#roleSelect", {
			searchEnabled: false,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});

		new Choices("#classSelect", {
			searchEnabled: false,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	document.getElementById("create-user-btn").onclick = async () => {
		const newRole = document.getElementById("roleSelect").value;
		const newClass = document.getElementById("classSelect").value;
		const newUsername = document.getElementById("username").value;
		const newFirstname = document.getElementById("firstname").value;
		const newLastname = document.getElementById("lastname").value;

		const response = await fetch("/api/v1/administration/user", {
			method: "PUT",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				role: newRole,
				class_id: newClass,
				username: newUsername,
				firstname: newFirstname,
				lastname: newLastname,
				password: null
			})
		});

		const data = await response.json();

		if (response.ok) {
			closeModal();
			openModal(`
				<h2>Benutzer erstellt</h2>
				<p>Der Benutzer wurde erfolgreich erstellt.<br />Passwort: <span class="fat">${data.password}</span></p>
				<button onclick="window.location.reload()">OK</button>
			`);
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Erstellen des Benutzers</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="addUser()">OK</button>
			`);
		}
	};
}

btnDetailsUsers.onclick = async () => {
	const response = await fetch("/api/v1/data/get-users");
	const data = await response.json();

	let users = "";
	let ids = [];
	data.users.forEach((user) => {
		users += `
			<div class="element-card user-card" id="user-${user.id}">
				<span>${user.username}</span>
				<span>Rolle: ${user.german_role_name}</span>
				<span>Klasse: ${user.class_name ? user.class_name : "Keine Klasse"}</span>
			</div>
		`;
		ids.push(`user-${user.id}`);
	});

	openModal(`
		<h2>Benutzer - Details</h2>
		<div id="users-container">
			${users}
			<div class="element-card user-card add-element" id="add-user-card">
				<span>+</span>
				<span>Benutzer erstellen</span>
			</div>
		</div>
	`);

	document
		.getElementById("users-container")
		.addEventListener("click", (e) => {
			if (e.target.closest(".element-card")) {
				const id = e.target.closest(".element-card").id;

				if (id == "add-user-card") {
					addUser();
					return;
				}

				clickOnUserCard(id);
			}
		});
};

async function clickOnWlanCodeCard(id) {
	closeModal();

	const codeId = id.split("-")[1];

	const response = await fetch(`/api/v1/data/wlan-code/${codeId}`);
	const data = await response.json();

	const expiryDate = new Date(data.code.expiry.replace("Z", "+00:00"));

	const userIds = data.code.user_ids.split(";");
	let users;
	if (userIds.includes("all")) {
		users = "Alle Benutzer";
	} else {
		users = [];
		for (const user_id of userIds) {
			const response = await fetch(`/api/v1/data/user/${user_id}`);
			const userData = await response.json();
			users.push({
				username: userData.user.username,
				firstname: userData.user.firstname,
				lastname: userData.user.lastname
			});
		}
	}

	const responseUsers = await fetch("/api/v1/data/get-users");
	const dataUsers = await responseUsers.json();

	openModal(`
		<h2>WLAN-Code ${data.code.code} - Details</h2>
		<p>Code: ${data.code.code}</p>
		<label for="expiry">Ablaufdatum:</label>
		<input type="datetime-local" id="expiry" value="${expiryDate
			.toISOString()
			.slice(0, 16)}" />
		<select id="userSelect" multiple>
			<option value="all">Alle Benutzer</option>
			${dataUsers.users
				.map(
					(user) =>
						`<option value="${user.id}">
					${user.username} (${user.firstname} ${user.lastname})
				</option>`
				)
				.join("")}
		</select>
		<button id="save-code-btn">Änderungen speichern</button>
		<button id="delete-code-btn" class="destructive">WLAN-Code löschen</button>
	`);

	setTimeout(() => {
		const choices = new Choices("#userSelect", {
			searchEnabled: true,
			itemSelectText: "",
			removeItemButton: true,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});

		if (users === "Alle Benutzer") {
			choices.setChoiceByValue("all");
		} else {
			users.forEach((user) => {
				const option = dataUsers.users.find(
					(u) =>
						u.username === user.username &&
						u.firstname === user.firstname &&
						u.lastname === user.lastname
				);
				if (option) {
					choices.setChoiceByValue(option.id.toString());
				}
			});
		}
	}, 50);

	document.getElementById("save-code-btn").onclick = async () => {
		const newExpiryValue = document.getElementById("expiry").value;
		const newExpiry = newExpiryValue.replace("T", " ") + ":00.000000";
		const selectedUsers = Array.from(
			document.getElementById("userSelect").selectedOptions
		)
			.map((option) => option.value)
			.join(";");

		const response = await fetch(`/api/v1/data/wlan-code/${codeId}`, {
			method: "PATCH",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				new_expiry: newExpiry,
				new_user_ids: selectedUsers
			})
		});

		if (response.ok) {
			window.location.reload();
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Ändern des WLAN-Codes</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="clickOnWlanCodeCard('wlancode-${codeId}')">OK</button>
			`);
		}
	};

	document.getElementById("delete-code-btn").onclick = async () => {
		closeModal();
		openModal(`
			<h2>WLAN-Code löschen</h2>
			<p>Sind Sie sicher, dass Sie diesen WLAN-Code löschen möchten?</p>
			<button id="confirm-delete-btn" class="destructive">Ja, WLAN-Code löschen</button>
			<button onclick="clickOnWlanCodeCard('wlancode-${codeId}')">Abbrechen</button>
		`);

		document.getElementById("confirm-delete-btn").onclick = async () => {
			const response = await fetch(
				`/api/v1/administration/wlan-code/${codeId}`,
				{
					method: "DELETE"
				}
			);

			if (response.ok) {
				window.location.reload();
			} else {
				closeModal();
				openModal(`
					<h2>Fehler beim Löschen des WLAN-Codes</h2>
					<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
					<button onclick="clickOnWlanCodeCard('wlancode-${codeId}')">OK</button>
				`);
			}
		};
	};
}

async function addWlanCode() {
	closeModal();

	const response = await fetch("/api/v1/data/get-users");
	const data = await response.json();

	openModal(`
		<h2>WLAN-Code erstellen</h2>
		<label for="code">Code:</label>
		<input type="text" id="code" />
		<label for="expiry">Ablaufdatum:</label>
		<input type="datetime-local" id="expiry" />
		<select id="userSelect" multiple>
			<option value="all">Alle Benutzer</option>
			${data.users
				.map(
					(user) =>
						`<option value="${user.id}">
					${user.username} (${user.firstname} ${user.lastname})
				</option>`
				)
				.join("")}
		</select>
		<button id="create-code-btn">WLAN-Code erstellen</button>
	`);

	setTimeout(() => {
		new Choices("#userSelect", {
			searchEnabled: true,
			itemSelectText: "",
			removeItemButton: true,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	document.getElementById("create-code-btn").onclick = async () => {
		const code = document.getElementById("code").value;
		const expiryValue = document.getElementById("expiry").value;
		const expiry = expiryValue.replace("T", " ") + ":00.000000";
		const selectedUsers = Array.from(
			document.getElementById("userSelect").selectedOptions
		)
			.map((option) => option.value)
			.join(";");

		const response = await fetch("/api/v1/administration/wlan-code", {
			method: "PUT",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				code: code,
				expiry: expiry,
				user_ids: selectedUsers
			})
		});

		if (response.ok) {
			window.location.reload();
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Erstellen des WLAN-Codes</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="addWlanCode()">OK</button>
			`);
		}
	};
}

btnDetailsWlanCodes.onclick = async () => {
	const response = await fetch("/api/v1/wlan/");
	const data = await response.json();

	let codes = "";
	data.codes.forEach((code) => {
		let expiry_str = code.expiry.replace("Z", "+00:00");
		let dt = new Date(expiry_str);
		let expiry = dt
			.toLocaleString("de-DE", {
				day: "2-digit",
				month: "2-digit",
				year: "numeric",
				hour: "2-digit",
				minute: "2-digit"
			})
			.replace(",", " ");

		codes += `
			<div class="element-card wlan-code-card" id="wlancode-${code.id}">
				<span>${code.code}</span>
				<span>Gültig bis: ${expiry}</span>
			</div>
		`;
	});

	openModal(`
		<h2>WLAN-Codes - Details</h2>
		<div id="wlan-codes-container">
			${codes}
			<div class="element-card wlan-code-card add-element" id="add-wlancode-card">
				<span>+</span>
				<span>WLAN-Code erstellen</span>
			</div>
		</div>
	`);

	document
		.getElementById("wlan-codes-container")
		.addEventListener("click", (e) => {
			if (e.target.closest(".element-card")) {
				const id = e.target.closest(".element-card").id;

				if (id == "add-wlancode-card") {
					addWlanCode();
					return;
				}

				clickOnWlanCodeCard(id);
			}
		});
};

btnDetailsTutoring.onclick = async () => {
	const response = await fetch("/api/v1/tutoring/all-tutors");
	const data = await response.json();

	let offers = "";
	data.results.forEach((offer) => {
		offers += `
			<div class="element-card tutor-card">
				<span>${offer.username}</span>
				<span>Fächer: ${offer.subjects.map((subject) => subject.german_name).join(", ")}</span>
			</div>
		`;
	});

	openModal(`
		<h2>Nachhilfe - Details</h2>
		${offers}
	`);
};

async function viewFeedback(id) {
	closeModal();

	const notificationId = id.split("-")[1];

	const response = await fetch(
		`/api/v1/parentnotification/feedback/${notificationId}`
	);
	const data = await response.json();

	if (!data.data || !data.data.feedbacks) {
		openModal(`
			<h2>Rückmeldungen - ${data.notification_title}</h2>
			<p>Keine Rückmeldungen gefunden.</p>
			<button onclick="closeModal()">OK</button>
		`);
		return;
	}

	// Fetch notification to get feedback labels
	const notificationResponse = await fetch("/api/v1/parentnotification/list");
	const notificationData = await notificationResponse.json();
	const notification = notificationData.parent_notifications.find(
		(pn) => pn.id.toString() === notificationId.toString()
	);

	let feedbackLabels = {};
	let choiceMaps = {};
	if (notification) {
		const feedbackArray = JSON.parse(notification.feedback || "[]");
		feedbackArray.forEach((item, index) => {
			feedbackLabels[index.toString()] = item.label;
			if (
				item.type === "single-choice" ||
				item.type === "multiple-choice"
			) {
				choiceMaps[index.toString()] = {};
				item.choices.forEach((choice) => {
					choiceMaps[index.toString()][choice.val] = choice.label;
				});
			}
		});
	}

	const feedbacks = data.data.feedbacks;
	const feedbackEntries = Object.entries(feedbacks);

	if (feedbackEntries.length === 0) {
		openModal(`
			<h2>Rückmeldungen - ${data.notification_title}</h2>
			<p>Keine Rückmeldungen gefunden.</p>
			<button onclick="closeModal()">OK</button>
		`);
		return;
	}

	// Fetch user data for each feedback
	const userPromises = feedbackEntries.map(async ([userId, feedback]) => {
		try {
			const userResponse = await fetch(`/api/v1/data/user/${userId}`);
			const userData = await userResponse.json();
			return {
				userId,
				username: userData.user.username,
				firstname: userData.user.firstname,
				lastname: userData.user.lastname,
				feedback
			};
		} catch (error) {
			return {
				userId,
				username: `ID ${userId}`,
				firstname: "",
				lastname: "",
				feedback
			};
		}
	});

	const feedbackData = await Promise.all(userPromises);

	let tableRows = "";
	feedbackData.forEach((item) => {
		const feedbackStr = Object.entries(item.feedback)
			.map(([key, value]) => {
				let displayValue = value;
				if (choiceMaps[key] && choiceMaps[key][value]) {
					displayValue = choiceMaps[key][value];
				}
				return `${feedbackLabels[key] || key}: ${displayValue}`;
			})
			.join("\n");

		tableRows += `
			<tr>
				<td>${item.username}</td>
				<td>${item.firstname} ${item.lastname}</td>
				<td><pre>${feedbackStr}</pre></td>
			</tr>
		`;
	});

	openModal(`
		<h2>Rückmeldungen - ${data.notification_title}</h2>
		<p>Rückmeldungen: ${Object.keys(data.data.feedbacks).length}</p>
		<table class="feedback-table">
			<thead>
				<tr>
					<th>Benutzername</th>
					<th>Name</th>
					<th>Rückmeldung</th>
				</tr>
			</thead>
			<tbody>
				${tableRows}
			</tbody>
		</table>
		<button onclick="closeModal()">OK</button>
	`);
}

async function clickOnParentNotificationCard(id) {
	closeModal();

	const notificationId = id.split("-")[1];
	const response = await fetch("/api/v1/parentnotification/list");
	const data = await response.json();

	const notification = data.parent_notifications.find(
		(pn) => pn.id.toString() === notificationId.toString()
	);

	if (!notification) {
		openModal(`
			<h2>Fehler</h2>
			<p>Die Elternbenachrichtigung konnte nicht gefunden werden.</p>
			<button onclick="closeModal()">OK</button>
		`);
		return;
	}

	const attachments = JSON.parse(notification.attachments || "[]");
	const feedback = JSON.parse(notification.feedback || "[]");
	const userIds = notification.user_ids
		? notification.user_ids.split(";").filter((value) => value !== "")
		: [];

	let recipientsHtml = "";
	if (userIds.includes("all")) {
		recipientsHtml = `<span>Alle Benutzer</span>`;
	} else if (userIds.length === 0) {
		recipientsHtml = `<span>Keine Empfänger angegeben</span>`;
	} else {
		const userNames = await Promise.all(
			userIds.map(async (userId) => {
				try {
					const userResponse = await fetch(
						`/api/v1/data/user/${userId}`
					);
					if (!userResponse.ok) throw new Error();
					const userData = await userResponse.json();
					return [
						userData.user.username,
						`${userData.user.firstname} ${userData.user.lastname}`
					];
				} catch (error) {
					return `ID ${userId}`;
				}
			})
		);
		recipientsHtml = userNames
			.map(
				(name) =>
					`<div class="element-card mini mini-user-card">
						<span>${name[0]}</span>
						<span>${name[1]}</span>
					</div>`
			)
			.join("<br />");
	}

	openModal(`
		<h2>Elternbrief - Details</h2>
		<p>
			Titel: ${notification.title}
		</p>
		<p>
			Text: ${notification.body}
		</p>
		<span>Empfänger:</span>
		<div class="element-card-mini-container">${recipientsHtml}</div>
		<span>Anhänge:</span>
		${
			attachments.length > 0
				? `<div class="element-card-mini-container">${attachments
						.map(
							(file) => `
							<a href="/files/${file}" target="_blank">
								<button class="small">${file}</button>
							</a>
						`
						)
						.join("")}</div>`
				: `<span class="mini-info mgb">Keine Anhänge</span>`
		}
		<span>Rückmeldung:</span>
		${
			feedback.length > 0
				? `<div class="element-card-mini-container">${feedback
						.map(
							(item) => `
							<div style="display: flex;">
								<div class="feedback-preview feedback-preview-l">
									<span>${item.label}</span>
								</div>
								<div class="feedback-preview feedback-preview-r">
									<span class="mini-info">${item.type}</span>
								</div>
							</div>
						`
						)
						.join("")}</div>`
				: `<span class="mini-info mgb">Keine Rückmeldung</span>`
		}
		<button onclick="closeModal()">OK</button>
		<button onclick="viewFeedback('${id}')">Rückmeldungen ansehen</button>
	`);
}

async function addParentNotification() {
	closeModal();

	const response = await fetch("/api/v1/data/get-users");
	const data = await response.json();

	const filesResponse = await fetch("/api/v1/data/get-files");
	const filesData = await filesResponse.json();

	openModal(`
	<h2>Elternbrief erstellen</h2>
	<label for="title">Betreff:</label>
	<input type="text" id="title">
	<label for="body">Inhalt:</label>
	<textarea id="body"></textarea>
	<label for="users">Benutzer:</label>
	<select id="users" multiple>
		<option value="all">Alle Benutzer</option>
		${data.users
			.map(
				(user) =>
					`<option value="${user.id}">
						${user.username} (${user.firstname} ${user.lastname})
					</option>`
			)
			.join("")}
	</select>
	<label for="attachments">Anhänge:</label>
	<select id="attachments" multiple>
		<option value="none">Keine Anhänge</option>
		${filesData.files
			.map(
				(file) =>
					`<option value="${file}">
						${file}
					</option>`
			)
			.join("")}
	</select>
	<label>Rückmeldung:</label>
	<div style="display: flex;">
		<div class="feedback-preview" style="cursor: pointer;" id="add-feedback-field">
			<span>+</span>
		</div>
	</div>
	<div id="feedback-fields"></div>
	<button id="create-pn-button">Elternbrief erstellen</button>
	`);

	setTimeout(() => {
		new Choices("#users", {
			searchEnabled: true,
			itemSelectText: "",
			removeItemButton: true,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});

		new Choices("#attachments", {
			searchEnabled: true,
			itemSelectText: "",
			removeItemButton: true,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	/*
	<div style="display: flex;">
		<div class="feedback-preview feedback-preview-l">
			<span>${item.label}</span>
		</div>
		<div class="feedback-preview feedback-preview-r">
			<span class="mini-info">${item.type}</span>
		</div>
	</div>
	*/

	let usedIds = new Set();
	function getUniqueId() {
		let id;
		do {
			id = Math.random().toString(36).substr(2, 8);
		} while (usedIds.has(id));
		usedIds.add(id);
		return id;
	}

	document.getElementById("add-feedback-field").onclick = () => {
		const newFieldID = getUniqueId();

		const container = document.getElementById("feedback-fields");

		const newFieldContainer = document.createElement("div");
		newFieldContainer.style.display = "flex";

		const newFieldL = document.createElement("div");
		newFieldL.classList.add("feedback-preview", "feedback-preview-l");
		newFieldL.innerHTML = `
		<label for="field-${newFieldID}-question">Frage:</label>
		<input type="text" id="field-${newFieldID}-question">
		`;

		const newFieldR = document.createElement("div");
		newFieldR.classList.add("feedback-preview", "feedback-preview-r");
		newFieldR.innerHTML = `
		<label for="field-${newFieldID}-type">Typ:</label>
		<select id="field-${newFieldID}-type">
			<option value="freetext">Freitext</option>
			<option value="single-choice">Einzelauswahl</option>
		</select>
		<label for="field-${newFieldID}-options" id="field-${newFieldID}-options-label">Auswahlmöglichkeiten (mit " " getrennt):</label>
		<input type="text" id="field-${newFieldID}-options">
		`;

		// append
		newFieldContainer.appendChild(newFieldL);
		newFieldContainer.appendChild(newFieldR);
		container.appendChild(newFieldContainer);

		setTimeout(() => {
			const select = new Choices(`#field-${newFieldID}-type`, {
				searchEnabled: false,
				itemSelectText: "",
				removeItemButton: false,
				shouldSort: false,
				placeholderValue: "Auswählen...",
				classNames: {
					containerOuter: "choices"
				}
			});
		}, 50);
	};
}

btnDetailsParentNotification.onclick = async () => {
	const response = await fetch("/api/v1/parentnotification/list");
	const data = await response.json();

	if (!data.parent_notifications || data.parent_notifications.length === 0) {
		openModal(`
			<h2>Elternbriefe - Details</h2>
			<p>Keine Elternbriefe gefunden.</p>
			<button onclick="closeModal()">OK</button>
		`);
		return;
	}

	let notificationsHtml = "";
	data.parent_notifications.forEach((notification) => {
		const attachmentCount = JSON.parse(
			notification.attachments || "[]"
		).length;
		const attachmentsLabel = attachmentCount === 1 ? "Anhang" : "Anhänge";
		const createdAt = new Date(
			notification.created_at.replace("Z", "+00:00")
		);
		const formattedDate = createdAt
			.toLocaleString("de-DE", {
				day: "2-digit",
				month: "2-digit",
				year: "numeric",
				hour: "2-digit",
				minute: "2-digit"
			})
			.replace(",", " ");

		notificationsHtml += `
			<div class="element-card pn-card" id="pn-${notification.id}">
				<span>${notification.title}</span>
				<span>${attachmentCount} ${attachmentsLabel}</span>
				<span class="mono">${formattedDate}</span>
			</div>
		`;
	});

	openModal(`
		<h2>Elternbriefe - Details</h2>
		<div id="parentnotifications-container">
			${notificationsHtml}
			<div class="element-card pn-card add-element" id="add-pn-card">
				<span>+</span>
				<span>Elternbrief erstellen</span>
			</div>
		</div>
	`);

	document
		.getElementById("parentnotifications-container")
		.addEventListener("click", (e) => {
			if (e.target.closest(".element-card")) {
				const id = e.target.closest(".element-card").id;

				if (id === "add-pn-card") {
					addParentNotification();
					return;
				}

				clickOnParentNotificationCard(id);
			}
		});
};

// push
document.getElementById("send-push").onclick = async () => {
	const response = await fetch("/api/v1/data/get-users");
	const data = await response.json();

	openModal(`
		<h2>Push-Benachrichtigung senden</h2>
		<label for="push-title">Betreff:</label>
		<input type="text" id="push-title" />
		<label for="push-message">Nachricht:</label>
		<textarea id="push-message"></textarea>
		<div class="push-users-container">
			<input type="checkbox" id="push-send-all" />
			<label for="push-send-all">An alle Benutzer senden</label>
			<div id="push-users-container">
				<label for="push-users">Empfänger:</label>
				<select id="push-users">
					${data.users
						.map(
							(user) =>
								`<option value="${user.id}">
							${user.username} (${user.firstname} ${user.lastname})
						</option>`
						)
						.join("")}
				</select>
			</div>
		</div>
		<button id="send-push-btn">Push-Benachrichtigung senden</button>
	`);

	setTimeout(() => {
		new Choices("#push-users", {
			searchEnabled: false,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	document.getElementById("push-send-all").onchange = (e) => {
		const pushUsersSelectContainer = document.getElementById(
			"push-users-container"
		);
		if (e.target.checked) {
			pushUsersSelectContainer.style.display = "none";
		} else {
			pushUsersSelectContainer.style.display = "block";
		}
	};

	document.getElementById("send-push-btn").onclick = async () => {
		const title = document.getElementById("push-title").value;
		const message = document.getElementById("push-message").value;
		const sendToAll = document.getElementById("push-send-all").checked;
		const selectedUser = document.getElementById("push-users").value;

		const response = await fetch(
			sendToAll
				? "/api/v1/administration/send-all"
				: "/api/v1/administration/send-user",
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					title: title,
					body: message,
					user_id: selectedUser
				})
			}
		);

		if (response.ok) {
			closeModal();
			openModal(`
				<h2>Push-Benachrichtigung gesendet</h2>
				<p>Die Push-Benachrichtigung wurde erfolgreich gesendet.</p>
				<button onclick="closeModal()">OK</button>
			`);
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Senden der Push-Benachrichtigung</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="closeModal()">OK</button>
			`);
		}
	};
};
