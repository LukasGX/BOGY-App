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
						`<div class="element-card mini">
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
				${data.detail[0].users
					.map(
						(user) =>
							`<div class="element-card mini">
								<span>${user.username}</span>
								<span>${user.firstname} ${user.lastname}</span>
							</div>`
					)
					.join("")}
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

btnDetailsClasses.onclick = async () => {
	const response = await fetch("/api/v1/data/get-classes");
	const data = await response.json();

	let classes = "";
	let ids = [];
	data.classes.forEach((cls) => {
		classes += `
			<div class="element-card" id="class-${cls.id}">
				<span>${cls.name}</span>
				<span>Schüler: ${cls.student_count}</span>
			</div>
		`;
		ids.push(`class-${cls.id}`);
	});

	openModal(`
        <h2>Klassen - Details</h2>
		<div id="classes-container">
			${classes}
		</div>
    `);

	document
		.getElementById("classes-container")
		.addEventListener("click", (e) => {
			if (e.target.closest(".element-card")) {
				const id = e.target.closest(".element-card").id;
				clickOnClassCard(id);
			}
		});
};
