async function getProfile() {
	const response = await fetch("/api/v1/user/profile", {
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
