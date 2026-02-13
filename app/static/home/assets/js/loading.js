const statusText = document.querySelector(".status-text");

const steps = [
  "Initializing dashboard creation...",
  "Loading product data...",
  "Analyzing revenue sources...",
  "Processing expenses...",
  "Generating financial forecast...",
  "Finalizing dashboard layout...",
  "Almost done..."
];

let index = 0;

const interval = setInterval(() => {
  statusText.textContent = steps[index];
  index++;
  if (index === steps.length) {
    clearInterval(interval);
  }
}, 8000); // 8s per step × 7 steps = ~56s

// Redirect after 60 seconds
setTimeout(() => {
  window.location.href = "/admin/admin"; // change to your actual dashboard route
}, 60000);
