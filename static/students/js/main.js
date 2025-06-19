let seconds = parseInt(localStorage.getItem("timeSpent")) || 0;
let lastRenderedTime = "";

// Reset timer if cookie indicates a reset
if (document.cookie.includes("resetTimer=true")) {
    localStorage.removeItem("timeSpent");
    seconds = 0;
    document.cookie = "resetTimer=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

document.addEventListener("DOMContentLoaded", () => {
    initTimerDisplay();
    showSection('home'); // Load home section by default
});

// Start and update timer
function initTimerDisplay() {
    setInterval(() => {
        seconds++;
        localStorage.setItem("timeSpent", seconds);

        const currentFormatted = formatTime(seconds);
        const timeDisplay = document.getElementById("time-spent");

        if (timeDisplay && currentFormatted !== lastRenderedTime) {
            timeDisplay.textContent = currentFormatted;
            lastRenderedTime = currentFormatted;
        }
    }, 1000);
}

function formatTime(s) {
    const m = String(Math.floor(s / 60)).padStart(2, '0');
    const sec = String(s % 60).padStart(2, '0');
    return `${m}:${sec}`;
}

// Logout and save time
function logoutAndSaveTime() {
    const formattedTime = formatTime(seconds);

    fetch("/students/save-time/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ time_spent: formattedTime, logout: true }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "logged out") {
            localStorage.removeItem("timeSpent");
            window.location.href = "/";
        }
    })
    .catch(error => {
        console.error("Logout failed:", error);
        window.location.href = "/";
    });
}

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Token display logic
function fetchTokens() {
    fetch("/students/get-tokens/")
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch tokens");
            return response.json();
        })
        .then(data => {
            const { text_to_text, voice_to_voice, face_to_face } = data.tokens || {};
            const tokenMap = {
                "text-token": text_to_text,
                "voice-token": voice_to_voice,
                "face-token": face_to_face
            };

            Object.entries(tokenMap).forEach(([id, value]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value ?? "0";
            });
        })
        .catch(error => console.error("Token fetch error:", error));
}

// Sidebar toggles
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

function toggleModulesDropdown() {
    const modLinks = document.getElementById('module-links');
    modLinks.style.display = modLinks.style.display === 'none' ? 'block' : 'none';
}

// Section renderer
function showSection(sectionId) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = ''; // Clear section

    let sectionContent = '';
    const timeNow = formatTime(seconds);

    switch (sectionId) {
        case 'home':
            sectionContent = `
                <section id="home" class="section">
                    <div class="dashboard-container">
                        <h2>🌟 Welcome back, <span class="highlight-username"></span>!</h2>
                        <p>Monitor progress, enhance skills, achieve goals with AetherBoard.</p>
                        <div class="token-cards animated-grid">
                            <div class="token-card neon-frame">
                                <h4>Text Module Tokens</h4>
                                <p id="text-token">Loading...</p>
                            </div>
                            <div class="token-card neon-frame">
                                <h4>Voice Module Tokens</h4>
                                <p id="voice-token">Loading...</p>
                            </div>
                            <div class="token-card neon-frame">
                                <h4>Face Module Tokens</h4>
                                <p id="face-token">Loading...</p>
                            </div>
                            <div class="token-card neon-frame">
                                <h4>Time Spent</h4>
                                <p id="time-spent">${timeNow}</p>
                            </div>
                        </div>
                    </div>
                </section>`;
            break;

        case 'text':
            sectionContent = `
                <section id="text" class="section">
                    <div class="dashboard-container">
                        <h3>📝 Text-to-Text Module</h3>
                        <div class="module-cards">
                            <div class="module-card neon-frame">
                                <img src="https://img.freepik.com/premium-vector/creative-illustrator-editable-text-effect_179567-292.jpg?semt=ais_hybrid&w=740" alt="Text Module">
                                <h4>Text-to-Text</h4>
                                <p>Test your skills with MCQs, blanks, and coding tasks.</p>
                                <button class="neon-btn open-modal" data-target="text-modal">Launch</button>
                            </div>
                        </div>
                    </div>
                </section>`;
            break;

        case 'voice':
            sectionContent = `
                <section id="voice" class="section">
                    <div class="dashboard-container">
                        <h3>🎙 Voice-to-Voice Module</h3>
                        <div class="module-cards">
                            <div class="module-card neon-frame">
                                <img src="https://via.placeholder.com/200x120?text=Voice+Module" alt="Voice Module">
                                <h4>Voice-to-Voice</h4>
                                <p>Respond to AI questions using your voice or code answers.</p>
                                <button class="neon-btn open-modal" data-target="voice-modal">Launch</button>
                            </div>
                        </div>
                    </div>
                </section>`;
            break;

        case 'face':
            sectionContent = `
                <section id="face" class="section">
                    <div class="dashboard-container">
                        <h3>🧑‍💻 Face-to-Face Module</h3>
                        <div class="module-cards">
                            <div class="module-card neon-frame">
                                <img src="https://via.placeholder.com/200x120?text=Face+Module" alt="Face Module">
                                <h4>Face-to-Face</h4>
                                <p>Interactive assessments (Coming Soon).</p>
                                <button class="neon-btn disabled" disabled>Coming Soon</button>
                            </div>
                        </div>
                    </div>
                </section>`;
            break;

        case 'resume':
            sectionContent = `
                <section id="resume" class="section">
                    <div class="dashboard-container">
                        <h3>📄 Resume Upload</h3>
                        <p>Upload your resume to personalize learning and assessments.</p>
                    </div>
                </section>`;
            break;

        case 'assessment':
            sectionContent = `
                <section id="assessment" class="section">
                    <div class="dashboard-container">
                        <h3>🧪 Assessment Dashboard</h3>
                        <p>Manage ongoing and completed assessments.</p>
                    </div>
                </section>`;
            break;

        case 'interview':
            sectionContent = `
                <section id="interview" class="section">
                    <div class="dashboard-container">
                        <h3>🎯 Interview Simulator</h3>
                        <p>Practice mock interviews powered by AI.</p>
                    </div>
                </section>`;
            break;

        case 'results':
            sectionContent = `
                <section id="results" class="section">
                    <div class="dashboard-container">
                        <h3>📊 Results</h3>
                        <p>Track progress, view scores, and analyze growth.</p>
                    </div>
                </section>`;
            break;

        case 'contact':
            sectionContent = `
                <section id="contact" class="section">
                    <div class="dashboard-container">
                        <h3>📬 Contact Us</h3>
                        <p>Need help? Our support team is here for you.</p>
                    </div>
                </section>`;
            break;
    }

    mainContent.innerHTML = sectionContent;
    document.getElementById('sidebar').classList.remove('active');

    if (sectionId === 'home') {
        fetchTokens();
        const timeDisplay = document.getElementById("time-spent");
        if (timeDisplay) {
            lastRenderedTime = formatTime(seconds);
            timeDisplay.textContent = lastRenderedTime;
        }
    }

    attachModalListeners(); // Ensure modal clicks are reattached
}

// Modal listeners
function attachModalListeners() {
    document.querySelectorAll(".open-modal").forEach(btn => {
        btn.addEventListener("click", () => {
            const modalId = btn.dataset.target;
            document.getElementById(modalId).classList.add("active");
        });
    });

    document.querySelectorAll(".close-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            btn.closest(".modal-overlay").classList.remove("active");
        });
    });
}

// Optional helpers
function openModal(id) {
    document.getElementById(id).classList.add("active");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}
