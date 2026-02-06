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
}

main();
