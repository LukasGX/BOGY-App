async function main() {
	// logged in
	await getProfile();

	// get main elements
	const noneFoundMain = document.getElementById("page-nonefound");
	const foundSomeMain = document.getElementById("page-foundsome");
	const createMain = document.getElementById("page-create");
	const passwordsEl = document.getElementById("passwords");

	const response = await fetch("/api/v1/pw/list");
	const data = await response.json();

	if (createMain) createMain.style.display = "none";

	if (data.length > 0) {
		if (noneFoundMain) noneFoundMain.style.display = "none";
		if (foundSomeMain) foundSomeMain.style.display = "block";
	} else {
		if (noneFoundMain) noneFoundMain.style.display = "block";
		if (foundSomeMain) foundSomeMain.style.display = "none";
	}

	async function create_pw() {
		const keyResponse = await fetch("/api/v1/pw/key");
		const keyData = await keyResponse.json();

		if (noneFoundMain) noneFoundMain.style.display = "none";
		if (foundSomeMain) foundSomeMain.style.display = "none";
		if (createMain) createMain.style.display = "block";

		const keyNote = document.getElementById("key-note");
		if (!keyData.key_set) {
			keyNote.textContent =
				"Denke dir einen sicheren Key aus. Du wirst diesen brauchen, um deine Passwörter aufzurufen.";
		}

		document
			.getElementById("create-btn")
			.addEventListener("click", async () => {
				const serviceInput = document.getElementById("service");
				const pwInput = document.getElementById("pw");
				const keyInput = document.getElementById("key");

				const service = serviceInput.value.trim();
				const pw = pwInput.value.trim();
				const key = keyInput.value.trim();

				if (!service || !pw || !key) {
					alert("Alle Felder müssen ausgefüllt sein.");
					return;
				}

				try {
					const response = await fetch("/api/v1/pw/create", {
						method: "POST",
						headers: {
							"Content-Type": "application/json"
						},
						body: JSON.stringify({
							name: service,
							value: pw,
							unlock_key: key
						})
					});

					const data = await response.json();

					if (response.ok) {
						alert("Passwort erfolgreich erstellt!");
						location.reload();
					} else {
						alert(
							data.detail ||
								"Fehler beim Erstellen des Passworts."
						);
					}
				} catch (error) {
					alert("Network error: " + error.message);
				}
			});
	}

	document.getElementById("create-pw").onclick = () => {
		create_pw();
	};

	if (data.length > 0) {
		data.forEach(async (pw) => {
			const newEl = document.createElement("div");
			newEl.classList.add("pw-el");
			newEl.id = `el-${pw.name}`;
			newEl.innerHTML = `
			<span id="d-${pw.name}">${pw.name}</span>
			<button id="view-${pw.name}" class="small">Ansehen</button>
			`;

			passwordsEl.appendChild(newEl);

			document.getElementById(`view-${pw.name}`).onclick = async () => {
				const key = prompt("Entschlüsselungs-Key: ");

				if (!key) return; // User cancelled

				try {
					const response = await fetch(
						`/api/v1/pw/read/${pw.name}?unlock_key=${encodeURIComponent(key)}`
					);
					const data = await response.json();

					if (response.ok) {
						alert(`Passwort für ${pw.name}: ${data.value}`);
					} else {
						alert(
							data.detail || "Fehler beim Abrufen des Passworts."
						);
					}
				} catch (error) {
					alert("Netzwerkfehler: " + error.message);
				}
			};
		});
	}
}

main();
