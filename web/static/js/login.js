const passwordField = document.getElementsByClassName("password-input")[0];
const loginButton = document.getElementsByClassName("login-button")[0];

function getCookie(cookieName) {
  let name = cookieName + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let cookies = decodedCookie.split(";");

  for (let index = 0; index < cookies.length; index++) {
    let cookie = cookies[index];
    while (cookie.charAt(0) == " ") {
      cookie = cookie.substring(1);
    }
    if (cookie.indexOf(name) == 0) {
      return cookie.substring(name.length, cookie.length);
    }
  }

  return "";
}

loginButton.addEventListener("click", () => {
  fetch("/dev/login", {
    method: "POST",
    headers: {
      password: passwordField.value,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      let bearerToken = data["bearer_token"];

      if (bearerToken) {
        document.cookie = "bearer_token=" + bearerToken + "; path=/";
        location.href = "/dev/dashboard";
      }
    });
});

let foundLogin = getCookie("access_code");
if (foundLogin) {
  location.href = "/dev/dashboard";
}
