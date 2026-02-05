async function main() {
	// logged in
	let profile = await getProfile();
	if (!profile) profile = { tutoring: false };

	// get main elements
	const firstOpenMain = document.getElementById("page-firstopen");
	const registerStudentMain = document.getElementById(
		"page-register-student"
	);
	const registerTeacherMain = document.getElementById(
		"page-register-teacher"
	);
	const standardMain = document.getElementById("page-standard");

	if (firstOpenMain && profile.tutoring == true)
		firstOpenMain.style.display = "none";
	if (firstOpenMain && profile.tutoring == false)
		firstOpenMain.style.display = "block";
	if (registerStudentMain) registerStudentMain.style.display = "none";
	if (registerTeacherMain) registerTeacherMain.style.display = "none";
	if (standardMain && profile.tutoring == true)
		standardMain.style.display = "block";
	if (standardMain && profile.tutoring == false)
		standardMain.style.display = "block";

	// get btns
	const btnRegisterStudent = document.getElementById("btn-register-student");
	const btnRegisterTeacher = document.getElementById("btn-register-teacher");

	if (btnRegisterStudent) {
		btnRegisterStudent.addEventListener("click", () => {
			if (firstOpenMain) firstOpenMain.style.display = "none";
			if (registerStudentMain)
				registerStudentMain.style.display = "block";
			if (registerTeacherMain) registerTeacherMain.style.display = "none";
		});
	}

	if (btnRegisterTeacher) {
		btnRegisterTeacher.addEventListener("click", () => {
			if (firstOpenMain) firstOpenMain.style.display = "none";
			if (registerStudentMain) registerStudentMain.style.display = "none";
			if (registerTeacherMain)
				registerTeacherMain.style.display = "block";
		});
	}
}

main();
