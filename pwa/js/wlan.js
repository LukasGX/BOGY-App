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

		// date
		const date = new Date(code.expiry);
		const dtString = date.toLocaleString("de-DE", {
			day: "2-digit",
			month: "2-digit",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
			hour12: false
		});

		codeEl.innerHTML = `
        <span class="code">${code.code}</span> <span class="expiry">gültig bis ${dtString}</span>
        `;
		codesEl.appendChild(codeEl);
	});
}

main();
