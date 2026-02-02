// get main elements
const firstOpenMain = document.getElementById("page-firstopen");
const registerStudentMain = document.getElementById("page-register-student");
const registerTeacherMain = document.getElementById("page-register-teacher");

if (firstOpenMain && registerStudentMain && registerTeacherMain) {
	firstOpenMain.style.display = "block";
	registerStudentMain.style.display = "none";
	registerTeacherMain.style.display = "none";
}
