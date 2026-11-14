
import { createAuthClient } from "@neon/auth";

const authUrl = import.meta.env.VITE_NEON_AUTH_URL;

if (!authUrl) {
  throw new Error("VITE_NEON_AUTH_URL is missing.");
}

const authClient = createAuthClient(authUrl);

function getCookie(name) {
  const cookies = document.cookie.split(";");

  for (const cookie of cookies) {
    const [key, ...value] = cookie.trim().split("=");

    if (key === name) {
      return decodeURIComponent(value.join("="));
    }
  }

  return null;
}

async function sendTokenToDjango() {
  const response = await authClient.token();

  if (response.error || !response.data?.token) {
    throw new Error("Unable to retrieve authentication token.");
  }

  const djangoResponse = await fetch("/accounts/neon/session/", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      token: response.data.token,
    }),
  });

  const result = await djangoResponse.json();

  if (!djangoResponse.ok) {
    throw new Error(result.error || "Django session verification failed.");
  }

  return result;
}

function showMessage(form, message, isError = false) {
  let element = form.querySelector(".auth-message");

  if (!element) {
    element = document.createElement("p");
    element.className = "auth-message";
    form.appendChild(element);
  }

  element.textContent = message;
  element.style.color = isError ? "red" : "green";
}

document.addEventListener("submit", async (event) => {
  const form = event.target;

  if (!form.matches("[data-auth-form]")) return;

  event.preventDefault();

  const formData = new FormData(form);
  const email = String(formData.get("email") || "").trim();
  const password = String(formData.get("password") || "");
  const action = form.dataset.authForm;
  const button = form.querySelector("button[type='submit']");

  if (button) button.disabled = true;

  try {
    if (action === "signup") {
      const name = String(formData.get("username") || "").trim();
      const confirmPassword = String(
        formData.get("confirm_password") || ""
      );

      if (password !== confirmPassword) {
        throw new Error("Passwords do not match.");
      }

      const result = await authClient.signUp.email({
        name,
        email,
        password,
      });

      if (result.error) {
        throw new Error(result.error.message || "Signup failed.");
      }

      showMessage(
        form,
        "Account registration submitted. Please sign in after completing any required email verification."
      );

      return;
    }

    if (action === "login") {
      const result = await authClient.signIn.email({
        email,
        password,
      });

      if (result.error) {
        throw new Error(result.error.message || "Login failed.");
      }

      await sendTokenToDjango();

      window.location.assign("/");
    }
  } catch (error) {
    showMessage(
      form,
      error.message || "Authentication failed.",
      true
    );
  } finally {
    if (button) button.disabled = false;
  }
});
// Handle customer logout
document.addEventListener("submit", async (event) => {
  const form = event.target;

  if (!form.matches("[data-auth-logout]")) return;

  event.preventDefault();

  const button = form.querySelector("button[type='submit']");

  if (button) button.disabled = true;

  try {
    // First clear the Neon Auth session.
    const result = await authClient.signOut();

    if (result.error) {
      throw new Error("Neon logout failed.");
    }

    // Then clear the Django session.
    const response = await fetch(form.action, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    });

    if (!response.ok) {
      throw new Error("Django logout failed.");
    }

    window.location.assign("/");
  } catch (error) {
    showMessage(form, error.message, true);

    if (button) button.disabled = false;
  }
});