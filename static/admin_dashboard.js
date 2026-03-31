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
		<div class="element-card-mini-container">
			${data.students
				.map(
					(student) =>
						`<div class="element-card mini mini-user-card">
							<span>${student.username}</span>
							<span>${student.firstname} ${student.lastname}</span>
						</div>`
				)
				.join("")}
		</div>
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
