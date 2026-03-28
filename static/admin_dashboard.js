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

function clickOnClassCard(id) {
	closeModal();
	openModal(`
		<h2>Klasse ${id} - Bearbeiten</h2>
	`);
}

btnDetailsClasses.onclick = async () => {
	const response = await fetch("/api/v1/data/get-classes");
	const data = await response.json();

	let classes = "";
	let ids = [];
	data.classes.forEach((cls) => {
		classes += `
			<div class="class-card" id="class-${cls.id}">
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
			if (e.target.closest(".class-card")) {
				const id = e.target.closest(".class-card").id;
				clickOnClassCard(id);
			}
		});
};
