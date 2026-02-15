document.addEventListener("DOMContentLoaded", () => {
  const sections = [
    {
      title: "1. Data Collection",
      content: "We collect only the data necessary to process transactions and improve user experience."
    },
    {
      title: "2. Data Usage",
      content: "Your data is used strictly for service delivery and never shared without consent."
    },
    {
      title: "3. Security Measures",
      content: "We use PCI DSS standards, SSL encryption, and secure servers to protect your information."
    },
    {
      title: "4. User Rights",
      content: "You can request access, correction, or deletion of your personal data at any time."
    },
    {
      title: "5. Contact & Support",
      content: "For privacy concerns, reach out via our support channels listed below."
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

    // Animation avec délai progressif
    setTimeout(() => {
      h3.style.transition = "all 0.6s ease";
      p.style.transition = "all 0.6s ease";
      h3.style.opacity = 1;
      h3.style.transform = "translateY(0)";
      p.style.opacity = 1;
      p.style.transform = "translateY(0)";
    }, index * 800); // chaque bloc apparaît 0.8s après le précédent
  });
});
