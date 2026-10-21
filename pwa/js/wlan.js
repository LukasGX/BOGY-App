async function main() {
	// logged in
	let profile = await getProfile();
	if (!profile) profile = { tutoring: false };

	// get main elements
	const noneFoundMain = document.getElementById("page-nonefound");
	const foundSomeMain = document.getElementById("foundsome");
	const codesEl = document.getElementById("codes");

	const response = await fetch("/api/v1/wlan/");
	const data = await response.json();

	if (data.codes.length > 0) {
		if (noneFoundMain) noneFoundMain.style.display = "none";
		if (foundSomeMain) foundSomeMain.style.display = "block";
	} else {
		if (noneFoundMain) noneFoundMain.style.display = "block";
		if (foundSomeMain) foundSomeMain.style.display = "none";
	}

	data.codes.forEach((code) => {
		const codeEl = document.createElement("div");
		codeEl.classList.add("code-el");

		// date (lokale Zeit, Format aus der DB ist nicht ISO-kompatibel)
		const dtString = formatLocalDateTime(code.expiry);

		codeEl.innerHTML = `
        <span class="code">${escapeHtml(code.code)}</span> <span class="expiry">gültig bis ${escapeHtml(dtString)}</span>
        `;
		codesEl.appendChild(codeEl);
	});
}

main();
