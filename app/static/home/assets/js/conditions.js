document.addEventListener("DOMContentLoaded", () => {
  const sections = [
    {
      title: "1. Acceptance of Terms",
      content: "By accessing or using our services, you agree to be bound by these Terms & Conditions."
    },
    {
      title: "2. User Responsibilities",
      content: "Users must provide accurate information and comply with all applicable laws when using our services."
    },
    {
      title: "3. Service Limitations",
      content: "We reserve the right to modify, suspend, or discontinue any part of the service at any time."
    },
    {
      title: "4. Liability Disclaimer",
      content: "We are not liable for indirect damages or losses arising from the use of our services."
    },
    {
      title: "5. Governing Law",
      content: "These Terms & Conditions are governed by applicable laws in your jurisdiction."
    }
  ];

  const container = document.getElementById("policy-content");

  sections.forEach((section, index) => {
    const h3 = document.createElement("h3");
    h3.textContent = section.title;
    h3.style.opacity = 0;
    h3.style.transform = "translateY(20px)";

    const p = document.createElement("p");
    p.textContent = section.content;
    p.style.opacity = 0;
    p.style.transform = "translateY(20px)";

    container.appendChild(h3);
    container.appendChild(p);

    // Animation progressive
    setTimeout(() => {
      h3.style.transition = "all 0.6s ease";
      p.style.transition = "all 0.6s ease";
      h3.style.opacity = 1;
      h3.style.transform = "translateY(0)";
      p.style.opacity = 1;
      p.style.transform = "translateY(0)";
    }, index * 800);
  });
});
