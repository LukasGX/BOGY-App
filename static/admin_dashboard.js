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

	PLUS_SHORTCUT_ACTION = () => {};
}

// get detail btns
const btnDetailsClasses = document.getElementById("btn-details-classes");
const btnDetailsUsers = document.getElementById("btn-details-users");
const btnDetailsWlanCodes = document.getElementById("btn-details-wlan-codes");
const btnDetailsTutoring = document.getElementById("btn-details-tutoring");
const btnDetailsParentNotification = document.getElementById(
	"btn-details-parentnotifications"
);

// get import btns
const btnImportClasses = document.getElementById("btn-import-classes");
const btnImportUsers = document.getElementById("btn-import-users");

let PLUS_SHORTCUT_ACTION = () => {};
let DEV_MODE = false;

function showResults(fetch, response, data) {
	closeModal();
	console.log(response);

	openModal(`
	<h2>${fetch}</h2>
	<div class="status-code ${response.ok ? "positive" : "negative"}">
		<h2><span class="indicator"></span> ${response.status} ${response.statusText}</h2>
	</div>
	<pre><code>${data}</code></pre>
	`);
}

async function clickOnClassCard(id) {
	closeModal();

	const classId = id.split("-")[1];

	const response = await fetch(`/api/v1/data/class/${classId}`);
	const data = await response.json();

	openModal(`
		<h2 data-class-id="${classId}" id="modal-h2">Klasse ${response.ok ? data.class.name : classId} - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		${
			response.ok
				? `
		${DEV_MODE ? `<p>ID: ${classId}</p>` : ""}
		<label for="class-name-input">Klassenname:</label>
		<input type="text" id="class-name-input" value="${data.class.name}" ${DEV_MODE ? `placeholder="class-name-input"` : ""} />

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
		<button id="delete-class-btn" class="destructive">Klasse löschen</button>`
				: "Fehler"
		}
	`);

	if (response.ok) {
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

			document.getElementById("confirm-delete-btn").onclick =
				async () => {
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

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				`/api/v1/data/class/${classId}`,
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
}

function addClass() {
	closeModal();

	openModal(`
		<h2>Klasse erstellen</h2>
		<label for="class-name-input">Klassenname:</label>
		<input type="text" id="class-name-input" ${DEV_MODE ? `placeholder="class-name-input"` : ""} />
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

async function clickOnClassesDetailsBtn() {
	const response = await fetch("/api/v1/data/get-classes");
	const data = await response.json();

	let classes = "";

	if (response.ok) {
		PLUS_SHORTCUT_ACTION = () => {
			addClass();
		};
		data.classes.forEach((cls) => {
			classes += `
				<div class="element-card class-card" id="class-${cls.id}">
					<span>${cls.name}</span>
					<span>Schüler: ${cls.student_count}</span>
					<span>Andere Benutzer: ${cls.others_count}</span>
				</div>
			`;
		});
	}

	openModal(`
        <h2>Klassen - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		${
			response.ok
				? `<div id="classes-container">
						${classes}
						<div class="element-card class-card add-element" id="add-class-card">
							<span>+</span>
							<span>Klasse erstellen</span>
						</div>
					</div>`
				: "Fehler"
		}
    `);

	if (response.ok) {
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
	}

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/data/get-classes",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
}

btnDetailsClasses.onclick = async () => {
	clickOnClassesDetailsBtn();
};

btnImportClasses.onclick = async () => {
	const response = await fetch("/api/v1/import/untis/classes");
	const data = await response.json();

	openModal(`
		<h2>Klassen von Untis importieren ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<p>Es wurden ${data.result.length} Klassen von Untis gefunden. Möchten Sie diese importieren?</p>
		<div class="element-card-mini-container">
			${data.result.map((cls) => `<div class="element-card mini-class-card">${cls.name}</div>`).join("<br />")}
		</div>
		<button id="start-import-classes-btn">Ja, Klassen importieren</button>
		<button onclick="closeModal()">Abbrechen</button>
	`);

	document.getElementById("start-import-classes-btn").onclick = async () => {
		closeModal();
		const response = await fetch("/api/v1/import/untis/classes", {
			method: "POST"
		});

		if (!response.ok) {
			openModal(`
			<h2>Fehler beim Importieren der Klassen</h2>
			<p>Bitte versuchen Sie es erneut.</p>
			<button onclick="closeModal()">OK</button>
			`);
		}
		if (response.ok) {
			window.location.reload();
		}
	};

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/import/untis/classes",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
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
		<h2>
			Benutzer ${data.user.username} - Details
			${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}
			${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-2"></span>` : ""}
			${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-3"></span>` : ""}
		</h2>
		${DEV_MODE ? `<p>ID: ${data.user.id}</p>` : ""}
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
		<input type="text" id="username" value="${data.user.username}" ${DEV_MODE ? `placeholder="username"` : ""} />
		<label for="firstname">Vorname:</label>
		<input type="text" id="firstname" value="${data.user.firstname}" ${DEV_MODE ? `placeholder="firstname"` : ""} />
		<label for="lastname">Nachname:</label>
		<input type="text" id="lastname" value="${data.user.lastname}" ${DEV_MODE ? `placeholder="lastname"` : ""} /><br /><br />
		<button id="save-user-btn">Änderungen speichern</button>
		<button id="reset-password-btn">Passwort zurücksetzen</button>
		<button id="delete-user-btn" class="destructive">Benutzer löschen</button>
	`);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				`/api/v1/data/user/${userId}`,
				response,
				JSON.stringify(data, null, 4)
			);
		};

		document.getElementById("fetch-hint-2").onclick = () => {
			showResults(
				"/api/v1/data/roles",
				rolesResponse,
				JSON.stringify(rolesData, null, 4)
			);
		};

		document.getElementById("fetch-hint-3").onclick = () => {
			showResults(
				"/api/v1/data/get-classes",
				classesResponse,
				JSON.stringify(classesData, null, 4)
			);
		};
	}

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
			searchEnabled: true,
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
		<h2>Benutzer erstellen ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""} ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-2"></span>` : ""}</h2>
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
		<input type="text" id="username" ${DEV_MODE ? `placeholder="username"` : ""} />
		<label for="firstname">Vorname:</label>
		<input type="text" id="firstname" ${DEV_MODE ? `placeholder="firstname"` : ""} />
		<label for="lastname">Nachname:</label>
		<input type="text" id="lastname" ${DEV_MODE ? `placeholder="lastname"` : ""} /><br /><br />
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
			searchEnabled: true,
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

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/data/roles",
				rolesResponse,
				JSON.stringify(rolesData)
			);
		};

		document.getElementById("fetch-hint-2").onclick = () => {
			showResults(
				"/api/v1/data/get-classes",
				classesResponse,
				JSON.stringify(classesData, null, 4)
			);
		};
	}
}

async function clickOnUsersDetailsBtn() {
	const loadUsersPage = async (page = 1) => {
		const response = await fetch(`/api/v1/data/get-users?page=${page}`);
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

		// Build pagination controls
		const pagination = data.pagination;
		let paginationHtml = "";
		if (pagination.total_pages > 1) {
			paginationHtml = `
				<div style="display: flex; justify-content: center; gap: 10px; margin-top: 15px;">
					${pagination.page > 1 ? `<button id="prev-page-btn" class="pagination-btn">← Vorherige</button>` : ""}
					<span style="padding: 5px 10px;">Seite ${pagination.page} von ${pagination.total_pages}</span>
					${pagination.page < pagination.total_pages ? `<button id="next-page-btn" class="pagination-btn">Nächste →</button>` : ""}
				</div>
			`;
		}

		closeModal();
		openModal(`
			<h2>Benutzer - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
			<div id="users-container">
				${users}
				<div class="element-card user-card add-element" id="add-user-card">
					<span>+</span>
					<span>Benutzer erstellen</span>
				</div>
			</div>
			${paginationHtml}
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

		// Handle pagination buttons with proper event delegation
		setTimeout(() => {
			const prevBtn = document.getElementById("prev-page-btn");
			const nextBtn = document.getElementById("next-page-btn");

			if (prevBtn) {
				prevBtn.onclick = (e) => {
					e.preventDefault();
					loadUsersPage(page - 1);
				};
			}

			if (nextBtn) {
				nextBtn.onclick = (e) => {
					e.preventDefault();
					loadUsersPage(page + 1);
				};
			}
		}, 0);

		PLUS_SHORTCUT_ACTION = () => {
			addUser();
		};

		if (DEV_MODE) {
			document.getElementById("fetch-hint-1").onclick = () => {
				showResults(
					`/api/v1/data/get-users?page=${page}`,
					response,
					JSON.stringify(data, null, 4)
				);
			};
		}
	};

	loadUsersPage(1);
}

btnDetailsUsers.onclick = async () => {
	clickOnUsersDetailsBtn();
};

btnImportUsers.onclick = async () => {
	const response = await fetch("/api/v1/import/untis/users");
	const data = await response.json();

	openModal(`
		<h2>Benutzer von Untis importieren ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<p>Es wurden ${data.teachers.result.length + data.students.result.length} Benutzer von Untis gefunden. Möchten Sie diese importieren?</p>
		<div class="element-card-mini-container">
			${data.teachers.result.map((user) => `<div class="element-card mmini-user-card">${user.foreName} ${user.longName}</div>`).join("<br />")}
			${data.students.result.map((user) => `<div class="element-card mmini-user-card">${user.foreName} ${user.longName}</div>`).join("<br />")}
		</div>
		<button id="start-import-users-btn">Ja, Benutzer importieren</button>
		<button onclick="closeModal()">Abbrechen</button>
	`);

	document.getElementById("start-import-users-btn").onclick = async () => {
		closeModal();
		const response = await fetch("/api/v1/import/untis/users", {
			method: "POST"
		});

		if (!response.ok) {
			openModal(`
			<h2>Fehler beim Importieren der Benutzer</h2>
			<p>Bitte versuchen Sie es erneut.</p>
			<button onclick="closeModal()">OK</button>
			`);
		}
		if (response.ok) {
			window.location.reload();
		}
	};

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/import/untis/users",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
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

	const responseUsers = await fetch("/api/v1/data/get-users?all=true");
	const dataUsers = await responseUsers.json();

	openModal(`
		<h2>WLAN-Code ${data.code.code} - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""} ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-2"></span>` : ""}</h2>
		${DEV_MODE ? `<p>ID: ${data.code.id}</p>` : ""}
		<p>Code: ${data.code.code}</p>
		<label for="expiry">Ablaufdatum:</label>
		<input type="datetime-local" id="expiry" ${DEV_MODE ? `placeholder="expiry"` : ""} value="${expiryDate
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

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				`/api/v1/data/wlan-code/${codeId}`,
				response,
				JSON.stringify(data, null, 4)
			);
		};

		document.getElementById("fetch-hint-2").onclick = () => {
			showResults(
				"/api/v1/data/get-users?all=true",
				responseUsers,
				JSON.stringify(dataUsers, null, 4)
			);
		};
	}

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

	const response = await fetch("/api/v1/data/get-users?all=true");
	const data = await response.json();

	openModal(`
		<h2>WLAN-Code erstellen ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<label for="code">Code:</label>
		<input type="text" id="code" ${DEV_MODE ? `placeholder="code"` : ""} />
		<label for="expiry">Ablaufdatum:</label>
		<input type="datetime-local" id="expiry" ${DEV_MODE ? `placeholder="expiry"` : ""} />
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

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/data/get-users?all=true",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}

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

async function clickOnWlanCodesDetailsBtn() {
	const response = await fetch("/api/v1/wlan/");
	const data = await response.json();

	PLUS_SHORTCUT_ACTION = () => {
		addWlanCode();
	};

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
		<h2>WLAN-Codes - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<div id="wlan-codes-container">
			${codes}
			<div class="element-card wlan-code-card add-element" id="add-wlancode-card">
				<span>+</span>
				<span>WLAN-Code erstellen</span>
			</div>
		</div>
	`);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/wlan/",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}

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
}

btnDetailsWlanCodes.onclick = async () => {
	clickOnWlanCodesDetailsBtn();
};

async function clickOnTutoringDetailsBtn() {
	const response = await fetch("/api/v1/tutoring/all-tutors");
	const data = await response.json();

	PLUS_SHORTCUT_ACTION = () => {};

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
		<h2>Nachhilfe - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		${offers}
	`);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/tutoring/all-tutors",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
}

btnDetailsTutoring.onclick = async () => {
	clickOnTutoringDetailsBtn();
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
		<h2>Rückmeldungen - ${data.notification_title} ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
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

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				`/api/v1/parentnotification/feedback/${notificationId}`,
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
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
		<h2>Elternbrief - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		${DEV_MODE ? `<p>ID: ${notification.id}</p>` : ""}
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
		<button onclick="viewFeedback('${id}')" id="feedbackBtn">
			Rückmeldungen ansehen
			<span class="shortcut">R</span>
		</button>
	`);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/parentnotification/list",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}
}

async function addParentNotification() {
	closeModal();

	const response = await fetch("/api/v1/data/get-users?all=true");
	const data = await response.json();

	const filesResponse = await fetch("/api/v1/data/get-files");
	const filesData = await filesResponse.json();

	openModal(`
	<h2>Elternbrief erstellen ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""} ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-2"></span>` : ""}</h2>
	<label for="title">Betreff:</label>
	<input type="text" id="title" ${DEV_MODE ? `placeholder="title"` : ""} />
	<label for="body">Inhalt:</label>
	<textarea id="body" ${DEV_MODE ? `placeholder="body"` : ""}></textarea>
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
	<div style="display: flex;" id="feedbacks">
		<div class="feedback-preview" style="cursor: pointer;" id="add-feedback-field">
			<span>+</span>
		</div>
	</div>
	<div id="feedback-fields"></div>
	<button id="create-pn-button">Elternbrief erstellen</button>
	`);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/data/get-users?all=true",
				response,
				JSON.stringify(data, null, 4)
			);
		};

		document.getElementById("fetch-hint-2").onclick = () => {
			showResults(
				"/api/v1/data/get-files",
				filesResponse,
				JSON.stringify(filesData, null, 4)
			);
		};
	}

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
		newFieldContainer.id = `${newFieldID}`;

		const newFieldL = document.createElement("div");
		newFieldL.classList.add("feedback-preview", "feedback-preview-l");
		newFieldL.innerHTML = `
		<label for="field-${newFieldID}-question">Frage:</label>
		<input type="text" id="field-${newFieldID}-question" ${DEV_MODE ? `placeholder="field-${newFieldID}-question"` : ""} />
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
		<input type="text" id="field-${newFieldID}-options" ${DEV_MODE ? `placeholder="field-${newFieldID}-options"` : ""} />
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

	document.getElementById("create-pn-button").onclick = async () => {
		const title = document.getElementById("title").value;
		const body = document.getElementById("body").value;
		const users = Array.from(
			document.getElementById("users").selectedOptions
		)
			.map((opt) => opt.value)
			.join(";");
		const attachments = JSON.stringify(
			Array.from(
				document.getElementById("attachments").selectedOptions,
				(opt) => opt.value
			)
		);
		const feedbacksEl = document.getElementById("feedback-fields");

		let feedbacks = [];
		let lastID = 0;

		Array.from(feedbacksEl.children).forEach((el) => {
			if (el.id === "add-feedback-field") return;

			const id = el.id;
			const questionEl = document.getElementById(`field-${id}-question`);
			const typeEl = document.getElementById(`field-${id}-type`);
			const optionsEl = document.getElementById(`field-${id}-options`);

			if (!questionEl || !typeEl || !optionsEl) return;

			const question = questionEl.value;
			const type = typeEl.value;
			const options = optionsEl.value;

			let choices = [];
			if (type === "single-choice") {
				const oSplit = options.split(" ");
				oSplit.forEach((option) => {
					choices.push({
						val: getUniqueId(),
						label: option
					});
				});
			}

			feedbacks.push({
				id: lastID,
				label: question,
				type: type,
				choices: choices
			});
			lastID += 1;
		});

		const sendBody = {
			title: title,
			body: body,
			user_ids: users,
			attachments: attachments,
			feedback: JSON.stringify(feedbacks)
		};

		const response = await fetch("/api/v1/parentnotification/", {
			method: "PUT",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify(sendBody)
		});

		const data = await response.json();

		if (response.ok) {
			closeModal();
			openModal(`
				<h2>Elternbrief erstellt</h2>
				<p>Der Elternbrief wurde erfolgreich erstellt.</p>
				<button onclick="window.location.reload()">OK</button>
			`);
		} else {
			closeModal();
			openModal(`
				<h2>Fehler beim Erstellen des Elternbriefes</h2>
				<p>Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.</p>
				<button onclick="addParentNotification()">OK</button>
			`);
		}
	};
}

async function clickOnParentNotificationDetailsBtn() {
	const response = await fetch("/api/v1/parentnotification/list");
	const data = await response.json();

	PLUS_SHORTCUT_ACTION = () => {
		addParentNotification();
	};

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
		<h2>Elternbriefe - Details ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<div id="parentnotifications-container">
			${notificationsHtml}
			<div class="element-card pn-card add-element" id="add-pn-card">
				<span>+</span>
				<span>Elternbrief erstellen</span>
			</div>
		</div>
	`);

	const fetchHint1 = document.getElementById("fetch-hint-1");
	if (fetchHint1)
		fetchHint1.onclick = () => {
			showResults(
				"/api/v1/parentnotification/list",
				response,
				JSON.stringify(data, null, 4)
			);
		};

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
}

btnDetailsParentNotification.onclick = async () => {
	clickOnParentNotificationDetailsBtn();
};

// push
async function sendPush() {
	const response = await fetch("/api/v1/data/get-users?all=true");
	const data = await response.json();

	openModal(`
		<h2>Push-Benachrichtigung senden ${DEV_MODE ? `<span class="fetch-hint" id="fetch-hint-1"></span>` : ""}</h2>
		<label for="push-title">Betreff:</label>
		<input type="text" id="push-title" ${DEV_MODE ? `placeholder="push-title"` : ""} />
		<label for="push-message">Nachricht:</label>
		<textarea id="push-message" ${DEV_MODE ? `placeholder="push-message"` : ""}></textarea>
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
			searchEnabled: true,
			itemSelectText: "",
			removeItemButton: false,
			shouldSort: false,
			placeholderValue: "Auswählen...",
			classNames: {
				containerOuter: "choices"
			}
		});
	}, 50);

	if (DEV_MODE) {
		document.getElementById("fetch-hint-1").onclick = () => {
			showResults(
				"/api/v1/data/get-users?all=true",
				response,
				JSON.stringify(data, null, 4)
			);
		};
	}

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
}

document.getElementById("send-push").onclick = async () => {
	sendPush();
};

// universal search
async function universalSearch() {
	closeModal();

	openModal(`
	<h2>Universal-Suche</h2>
	<p>Suchen Sie nach Klassen, Benutzern, WLAN-Codes, Nachhilfe-Einträgen und Elternbriefen.</p>
	<label for="search">Suchbegriff:</label>
	<input type="text" id="search" autocomplete="off" ${DEV_MODE ? `placeholder="search"` : ""} />
	<div id="search-results" class="search-results"></div>
	`);

	const searchInput = document.getElementById("search");
	setTimeout(() => {
		searchInput.focus();
	}, 1);
	const resultsContainer = document.getElementById("search-results");

	resultsContainer.innerHTML = `<p>Starten Sie die Eingabe, um Ergebnisse zu sehen.</p>`;

	let searchItems = [];

	try {
		const [
			classesResponse,
			usersResponse,
			wlanResponse,
			tutoringResponse,
			pnResponse
		] = await Promise.all([
			fetch("/api/v1/data/get-classes"),
			fetch("/api/v1/data/get-users?all=true"),
			fetch("/api/v1/wlan/"),
			fetch("/api/v1/tutoring/all-tutors"),
			fetch("/api/v1/parentnotification/list")
		]);

		if (
			!classesResponse.ok ||
			!usersResponse.ok ||
			!wlanResponse.ok ||
			!tutoringResponse.ok ||
			!pnResponse.ok
		) {
			resultsContainer.innerHTML = `<p>Fehler beim Laden der Suchdaten.</p>`;
			return;
		}

		const [classesData, usersData, wlanData, tutoringData, pnData] =
			await Promise.all([
				classesResponse.json(),
				usersResponse.json(),
				wlanResponse.json(),
				tutoringResponse.json(),
				pnResponse.json()
			]);

		searchItems = [
			...(classesData.classes || []).map((cls) => ({
				id: `class-${cls.id}`,
				type: "class",
				title: cls.name,
				subtitle: `Schüler: ${cls.student_count} · Andere: ${cls.others_count}`,
				searchText: `${cls.name}`.toLowerCase()
			})),
			...(usersData.users || []).map((user) => ({
				id: `user-${user.id}`,
				type: "user",
				title: user.username,
				subtitle: `${user.firstname} ${user.lastname} · ${user.german_role_name || ""} · ${user.class_name || "Keine Klasse"}`,
				searchText:
					`${user.username} ${user.firstname} ${user.lastname} ${user.german_role_name || ""} ${user.class_name || ""}`.toLowerCase()
			})),
			...(wlanData.codes || []).map((code) => ({
				id: `wlancode-${code.id}`,
				type: "wlan-code",
				title: code.code,
				subtitle: `Gültig bis: ${new Date(
					code.expiry.replace("Z", "+00:00")
				).toLocaleString("de-DE", {
					day: "2-digit",
					month: "2-digit",
					year: "numeric",
					hour: "2-digit",
					minute: "2-digit"
				})} `,
				searchText: `${code.code} ${code.user_ids || ""}`.toLowerCase()
			})),
			...(tutoringData.results || []).map((offer, index) => ({
				id: `tutoring-${offer.id || offer.user_id || offer.tutor_id || index}`,
				type: "tutoring",
				title: offer.username,
				subtitle: `Fächer: ${(offer.subjects || []).map((subject) => subject.german_name).join(", ") || "Keine Fächer"}`,
				searchText:
					`${offer.username} ${(offer.subjects || []).map((subject) => subject.german_name).join(" ")}`.toLowerCase()
			})),
			...(pnData.parent_notifications || []).map((notification) => ({
				id: `pn-${notification.id}`,
				type: "parentnotification",
				title: notification.title,
				subtitle: notification.body,
				searchText:
					`${notification.title} ${notification.body}`.toLowerCase()
			}))
		];
	} catch (error) {
		resultsContainer.innerHTML = `<p>Fehler beim Laden der Suchdaten.</p>`;
		return;
	}

	function getTypeLabel(type) {
		switch (type) {
			case "class":
				return "Klasse";
			case "user":
				return "Benutzer";
			case "wlan-code":
				return "WLAN-Code";
			case "tutoring":
				return "Nachhilfe";
			case "parentnotification":
				return "Elternbrief";
			default:
				return "Unbekannt";
		}
	}

	function renderResults(results) {
		if (!results.length) {
			return `<p>Keine Ergebnisse gefunden.</p>`;
		}

		return results
			.map(
				(item) => `
					<div class="element-card ${item.type}-card search-result-card" id="${item.id}">
						<div class="search-result-main">
							<strong>${item.title}</strong>
							<small>${getTypeLabel(item.type)}</small>
						</div>
						<div class="search-result-subtitle">${item.subtitle}</div>
					</div>
				`
			)
			.join("");
	}

	function updateResults() {
		const query = searchInput.value.trim().toLowerCase();
		if (!query) {
			resultsContainer.innerHTML = `<p>Starten Sie die Eingabe, um Ergebnisse zu sehen.</p>`;
			return;
		}

		const filtered = searchItems.filter((item) =>
			item.searchText.includes(query)
		);
		resultsContainer.innerHTML = renderResults(filtered);
	}

	function openTutoringCard(item) {
		closeModal();
		openModal(`
			<h2>Nachhilfe - ${item.title}</h2>
			<p>${item.subtitle}</p>
			<button onclick="closeModal()">OK</button>
		`);
	}

	resultsContainer.addEventListener("click", (e) => {
		const card = e.target.closest(".search-result-card");
		if (!card) return;

		const id = card.id;
		const item = searchItems.find((entry) => entry.id === id);
		if (!item) return;

		switch (item.type) {
			case "class":
				clickOnClassCard(id);
				break;
			case "user":
				clickOnUserCard(id);
				break;
			case "wlan-code":
				clickOnWlanCodeCard(id);
				break;
			case "parentnotification":
				clickOnParentNotificationCard(id);
				break;
			case "tutoring":
				openTutoringCard(item);
				break;
			default:
				break;
		}
	});

	searchInput.addEventListener("input", updateResults);
}
document.getElementById("universal-search-btn").onclick = async () => {
	universalSearch();
};

// dev mode
function enableCSSDevMode() {
	const devModeStylesheet = document.createElement("link");
	devModeStylesheet.rel = "stylesheet";
	devModeStylesheet.href = "/static/dev-mode.css";
	document.head.appendChild(devModeStylesheet);
}

function devModeChanges() {
	const subtitle = document.getElementById("subtitle");
	subtitle.innerHTML = `ADMIN DASHBOARD <span class="dm-badge">DEV-MODE</span>`;
}

function activateDevMode() {
	console.log("%cWELCOME TO DEV MODE", "color: red; font-size: 1.2rem;");

	DEV_MODE = true;

	devModeChanges();
	enableCSSDevMode();
}

// + Shortcut
function plusKey() {
	PLUS_SHORTCUT_ACTION();
}
