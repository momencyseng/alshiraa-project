// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }

    // Language Switcher Logic
    const langBtn = document.getElementById('lang-toggle');
    const htmlElement = document.documentElement;

    // Check saved language
    const currentLang = localStorage.getItem('language') || 'en';
    setLanguage(currentLang);

    if (langBtn) {
        langBtn.addEventListener('click', () => {
            const newLang = htmlElement.getAttribute('dir') === 'rtl' ? 'en' : 'ar';
            setLanguage(newLang);
        });
    }

    function setLanguage(lang) {
        if (lang === 'ar') {
            htmlElement.setAttribute('dir', 'rtl');
            htmlElement.setAttribute('lang', 'ar');
            if (langBtn) langBtn.textContent = 'English';
        } else {
            htmlElement.setAttribute('dir', 'ltr');
            htmlElement.setAttribute('lang', 'en');
            if (langBtn) langBtn.textContent = 'العربية';
        }
        localStorage.setItem('language', lang);
    }

    // Theme Switcher Logic
    const themeBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    setTheme(currentTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const newTheme = htmlElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Icon update
        if (themeBtn) {
            themeBtn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
    }

    // Smooth Scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});

// --- Calculator Functions ---

function calculatePower() {
    const volts = parseFloat(document.getElementById('calc-volts').value);
    const amps = parseFloat(document.getElementById('calc-amps').value);
    const resultDiv = document.getElementById('result-power');
    const isArabic = document.documentElement.getAttribute('dir') === 'rtl';

    if (isNaN(volts) || isNaN(amps)) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = isArabic ? "يرجى إدخال قيم صحيحة" : "Please enter valid numbers.";
        return;
    }

    const watts = volts * amps;
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = isArabic
        ? `القدرة الناتجة: <span style="color:var(--accent-color); font-size:1.2rem;">${watts.toFixed(2)} واط</span>`
        : `Power Output: <span style="color:var(--accent-color); font-size:1.2rem;">${watts.toFixed(2)} Watts</span>`;
}

function calculatePanels() {
    const usage = parseFloat(document.getElementById('calc-usage').value); // kWh
    const panelWatt = parseFloat(document.getElementById('calc-panel-watt').value); // Watts
    const resultDiv = document.getElementById('result-panels');
    const isArabic = document.documentElement.getAttribute('dir') === 'rtl';
    const sunHours = 5; // Average approximation for Iraq/Nineveh

    if (isNaN(usage) || isNaN(panelWatt)) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = isArabic ? "يرجى إدخال قيم صحيحة" : "Please enter valid numbers.";
        return;
    }

    // Daily Usage (Wh) = usage * 1000
    // Total Generating Capacity needed = Daily Usage / Sun Hours
    // Number of Panels = Capacity / Panel Wattage
    // Adding 20% buffer for system losses
    const dailyWh = usage * 1000;
    const requiredCapacity = (dailyWh / sunHours) * 1.2;
    const numberOfPanels = Math.ceil(requiredCapacity / panelWatt);

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = isArabic
        ? `تحتاج تقريباً إلى <span style="color:var(--accent-color); font-size:1.2rem;">${numberOfPanels}</span> لوح شمسي.`
        : `You need approximately <span style="color:var(--accent-color); font-size:1.2rem;">${numberOfPanels}</span> solar panels.`;
}

function calculateBattery() {
    const load = parseFloat(document.getElementById('calc-load').value); // Watts
    const hours = parseFloat(document.getElementById('calc-hours').value); // Hours
    const voltage = parseFloat(document.getElementById('calc-sys-volts').value); // Volts
    const resultDiv = document.getElementById('result-battery');
    const isArabic = document.documentElement.getAttribute('dir') === 'rtl';

    if (isNaN(load) || isNaN(hours)) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = isArabic ? "يرجى إدخال قيم صحيحة" : "Please enter valid numbers.";
        return;
    }

    // Total Energy required (Wh) = Load * Hours
    // Battery Capacity (Ah) = Total Energy / Voltage
    // Lead Acid Depth of Discharge (DoD) ~ 50% => multiply by 2 to save battery life
    // Lithium DoD ~ 80% => multiply by 1.25. Let's assume standard calculation with 50% buffer (Lead Acid safe)
    const energyNeeded = load * hours;
    const capacityAh = (energyNeeded / voltage) / 0.5; // 50% DoD

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = isArabic
        ? `سعة البطارية المقترحة (لضمان تشغيل آمن): <span style="color:var(--accent-color); font-size:1.2rem;">${Math.ceil(capacityAh)} أمبير/ساعة</span>`
        : `Recommended Battery Capacity (for safe DoD): <span style="color:var(--accent-color); font-size:1.2rem;">${Math.ceil(capacityAh)} Ah</span>`;
}
