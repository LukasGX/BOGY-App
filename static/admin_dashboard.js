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

// get btns
const btnDetailsClasses = document.getElementById("btn-details-classes");

btnDetailsClasses.onclick = () => {
	openModal(`
        <h2>Klassen - Details</h2>
    `);
};
