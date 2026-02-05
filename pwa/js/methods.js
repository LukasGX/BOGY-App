async function getProfile() {
	const response = await fetch("/profile", {
		method: "GET",
		credentials: "include"
	});

	if (response.status === 200) {
		const data = await response.json();
		console.log("User is logged in:", data);
		return data;
	} else {
		window.location.href = "/app/login.html";
	}
}
