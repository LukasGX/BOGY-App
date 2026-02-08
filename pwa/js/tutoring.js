async function main() {
	// logged in
	let profile = await getProfile();
	if (!profile) profile = { tutoring: false };

	// get main elements
	const firstOpenMain = document.getElementById("page-firstopen");
	const registerMain = document.getElementById("page-register");
	const standardMain = document.getElementById("page-standard");

	const RGCS = document.getElementById("section-register-callout");
	const EPC = document.getElementById("section-edit-profile-callout");

	if (profile.tutoring == true) {
		if (RGCS) RGCS.style.display = "none";
		if (EPC) EPC.style.display = "block";
	} else {
		if (RGCS) RGCS.style.display = "block";
		if (EPC) EPC.style.display = "none";
	}

	if (firstOpenMain) firstOpenMain.style.display = "block";
	if (registerMain) registerMain.style.display = "none";
	if (standardMain) standardMain.style.display = "none";

	// get btns
	const btnRegister = document.getElementById("btn-register");

	if (btnRegister) {
		btnRegister.addEventListener("click", () => {
			if (firstOpenMain) firstOpenMain.style.display = "none";
			if (registerMain) registerMain.style.display = "block";
			if (standardMain) standardMain.style.display = "none";
		});
	}

	// search form handling: submit via fetch and render results
	const searchForm = document.querySelector(".search-form");
	const resultsEl = document.getElementById("search-results");

	function escapeHtml(str) {
		if (!str && str !== 0) return "";
		return String(str)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#39;");
	}

	if (searchForm && resultsEl) {
		searchForm.addEventListener("submit", async (ev) => {
			ev.preventDefault();
			const fd = new FormData(searchForm);
			const subjects = fd.getAll("subject");
			if (!subjects || subjects.length === 0) {
				resultsEl.innerHTML =
					'<p class="muted">Bitte mindestens ein Fach wählen.</p>';
				return;
			}

			const params = new URLSearchParams();
			subjects.forEach((s) => params.append("subject", s));
			resultsEl.innerHTML = '<p class="muted">Suche läuft…</p>';
			try {
				const resp = await fetch(
					"/search-tutors?" + params.toString(),
					{ credentials: "same-origin" }
				);
				if (!resp.ok) throw new Error("Netzwerkfehler");
				const data = await resp.json();
				if (!data.results || data.results.length === 0) {
					resultsEl.innerHTML = '<p class="muted">Keine Treffer.</p>';
					return;
				}

				const wrapper = document.createElement("div");
				wrapper.className = "tutor-list";
				data.results.forEach((t) => {
					const item = document.createElement("div");
					item.className = "search-result";

					const name = (t.firstname || "") + " " + (t.lastname || "");
					const pName = escapeHtml(name.trim() || t.username);
					const pUsername = escapeHtml(t.username);
					const pClass = escapeHtml(t.class || "");
					const pSubjects = t.subjects.map(escapeHtml).join(", ");

					item.innerHTML = `<span class="name">${pName}</span>
						<span class="infos">${pUsername} &middot; ${pClass}</span>
						<div class="subjects">
							Fächer: ${pSubjects}
						</div>
						<!-- <button class="contact"><img src="/app/resources/contact-icon.svg" alt="Kontakt" /></button> -->
					`;
					wrapper.appendChild(item);
				});
				resultsEl.innerHTML = "";
				resultsEl.appendChild(wrapper);
			} catch (err) {
				console.error(err);
				resultsEl.innerHTML =
					'<p class="muted">Fehler bei der Suche.</p>';
			}
		});
	}
}

main();
