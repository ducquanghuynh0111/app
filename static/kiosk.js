document.querySelector("#punch").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.querySelector("#kiosk-message");
  const button = event.submitter;
  button.disabled = true;
  try {
    const response = await fetch("/api/kiosk/punch", {
      method: "POST", headers: {"Content-Type": "application/json", "X-Kiosk-Key": form.device_key.value},
      body: JSON.stringify({username: form.username.value, pin: form.pin.value, event: button.value})
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Không thể chấm công");
    output.textContent = "Đã ghi " + (button.value === "check-in" ? "giờ vào" : "giờ ra") + " cho ca #" + result.shift_id + ".";
    form.username.value = "";
    form.pin.value = "";
  } catch (error) {
    output.textContent = error.message;
    form.pin.value = "";
  } finally { button.disabled = false; }
});
