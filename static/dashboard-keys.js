let zeroCounter = 0;

window.addEventListener("keydown", (e) => {
	if (e.key === "Escape") {
		closeModal();
		return;
	}

	if (e.target.matches("input, textarea, select")) {
		return;
	}

	switch (e.key) {
		case "k":
			clickOnClassesDetailsBtn();
			break;
		case "b":
			clickOnUsersDetailsBtn();
			break;
		case "w":
			clickOnWlanCodesDetailsBtn();
			break;
		case "p":
			sendPush();
			break;
		case "n":
			clickOnTutoringDetailsBtn();
			break;
		case "e":
			clickOnParentNotificationDetailsBtn();
			break;
		case "u":
			universalSearch();
			break;
		case "0":
			zeroCounter += 1;
			if (zeroCounter >= 3) {
				activateDevMode();
				zeroCounter = 0;
			}
			break;
	}
});
