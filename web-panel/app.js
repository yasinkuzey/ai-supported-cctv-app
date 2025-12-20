// app.js - CCTV Web Panel

const API_BASE = "https://ai-supported-cctv-app.onrender.com";

let auth = { username: "", password: "" };
let currentPage = 1;
let chart = null;

// ============ AUTH ============
document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch(`${API_BASE}/auth/login?username=${username}&password=${password}`, {
            method: "POST"
        });

        if (res.ok) {
            auth = { username, password };
            showDashboard();
        } else {
            document.getElementById("login-error").textContent = "Hatalı kullanıcı adı veya şifre";
        }
    } catch (err) {
        document.getElementById("login-error").textContent = "Bağlantı hatası";
    }
});

function showDashboard() {
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("dashboard").classList.remove("hidden");
    loadStats();
    loadLogs();
}

function logout() {
    auth = { username: "", password: "" };
    document.getElementById("dashboard").classList.add("hidden");
    document.getElementById("login-screen").classList.remove("hidden");
}

// ============ API CALLS ============
async function api(endpoint) {
    const separator = endpoint.includes("?") ? "&" : "?";
    const res = await fetch(`${API_BASE}${endpoint}${separator}username=${auth.username}&password=${auth.password}`);
    return res.json();
}

async function apiPost(endpoint, params = "") {
    const res = await fetch(`${API_BASE}${endpoint}?username=${auth.username}&password=${auth.password}${params}`, {
        method: "POST"
    });
    return res.json();
}

async function apiPut(endpoint, params = "") {
    const res = await fetch(`${API_BASE}${endpoint}?username=${auth.username}&password=${auth.password}${params}`, {
        method: "PUT"
    });
    return res.json();
}

async function apiDelete(endpoint) {
    await fetch(`${API_BASE}${endpoint}?username=${auth.username}&password=${auth.password}`, {
        method: "DELETE"
    });
}

// ============ STATS ============
async function loadStats() {
    const stats = await api("/stats");

    document.getElementById("stat-total").textContent = stats.total_logs || 0;
    document.getElementById("stat-anomaly").textContent = stats.total_anomalies || 0;

    const rate = stats.total_logs > 0
        ? ((stats.total_anomalies / stats.total_logs) * 100).toFixed(1) + "%"
        : "0%";
    document.getElementById("stat-rate").textContent = rate;
    document.getElementById("stat-24h").textContent = stats.last_24h_anomalies || "-";

    updateChart(stats);
}

function updateChart(stats) {
    const ctx = document.getElementById("anomaly-chart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Temiz", "Anomali"],
            datasets: [{
                data: [
                    stats.total_logs - stats.total_anomalies,
                    stats.total_anomalies
                ],
                backgroundColor: ["#22c55e", "#ef4444"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#e5e7eb" }
                }
            }
        }
    });
}

// ============ LOGS ============
async function loadLogs() {
    const filter = document.getElementById("filter-anomaly").value;
    let endpoint = `/logs?page=${currentPage}`;
    if (filter) endpoint += `&is_anomaly=${filter}`;

    const data = await api(endpoint);

    const tbody = document.querySelector("#logs-table tbody");
    tbody.innerHTML = "";

    if (data.logs) {
        data.logs.forEach(log => {
            const date = new Date(log.created_at).toLocaleString("tr-TR");
            const status = log.is_anomaly
                ? '<span class="badge danger">Anomali</span>'
                : '<span class="badge success">Temiz</span>';

            // AI Response (reason) zaten log.reason içinde geliyor.
            // Previous URL ve Reason'ı modal'a gönderiyoruz.
            const reasonEscaped = (log.reason || "").replace(/'/g, "\\'");
            const viewBtn = log.image_url
                ? `<button class="view-btn" onclick="openModal('${log.image_url}', '${log.previous_image_url || ""}', '${reasonEscaped}')">İncele</button>`
                : "-";

            tbody.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td>${status}</td>
                    <td>${log.reason}</td>
                    <td>${log.diff_percentage.toFixed(2)}%</td>
                    <td>${viewBtn}</td>
                </tr>
            `;
        });
    }

    document.getElementById("page-info").textContent = `Sayfa ${currentPage}`;
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadLogs();
    }
}

function nextPage() {
    currentPage++;
    loadLogs();
}

// ============ PHOTOS ============
async function loadPhotos() {
    const data = await api("/logs?per_page=50");
    const grid = document.getElementById("photos-grid");
    grid.innerHTML = "";

    if (data.logs) {
        data.logs.filter(l => l.image_url).forEach(log => {
            const date = new Date(log.created_at).toLocaleString("tr-TR");
            const reasonEscaped = (log.reason || "").replace(/'/g, "\\'");

            grid.innerHTML += `
                <div class="photo-card" onclick="openModal('${log.image_url}', '${log.previous_image_url || ""}', '${reasonEscaped}')">
                    <img src="${log.image_url}" alt="Capture">
                    <div class="photo-info">${date}</div>
                </div>
            `;
        });
    }
}

// ============ SETTINGS ============
async function loadSettings() {
    const settings = await api("/settings");
    document.getElementById("anomalies-input").value = settings.anomalies_to_watch || "";

    const emails = await api("/email-list");
    const list = document.getElementById("email-list");
    list.innerHTML = "";

    if (emails && emails.length) {
        emails.forEach(e => {
            list.innerHTML += `
                <div class="email-item">
                    <span>${e.email} ${e.name ? `(${e.name})` : ""}</span>
                    <button onclick="deleteEmail(${e.id})">Sil</button>
                </div>
            `;
        });
    }
}

async function saveSettings() {
    const anomalies = encodeURIComponent(document.getElementById("anomalies-input").value);
    await apiPut("/settings", `&anomalies_to_watch=${anomalies}`);
    alert("Ayarlar kaydedildi");
}

async function addEmail() {
    const email = document.getElementById("new-email").value;
    const name = document.getElementById("new-name").value;

    if (!email) return;

    await apiPost("/email-list", `&email=${email}&name=${name}`);
    document.getElementById("new-email").value = "";
    document.getElementById("new-name").value = "";
    loadSettings();
}

async function deleteEmail(id) {
    await apiDelete(`/email-list/${id}`);
    loadSettings();
}

// ============ MODAL ============
function openModal(currentUrl, prevUrl, reason) {
    document.getElementById("modal-image-curr").src = currentUrl;

    const prevImg = document.getElementById("modal-image-prev");
    if (prevUrl && prevUrl !== "null" && prevUrl !== "undefined" && prevUrl !== "") {
        prevImg.src = prevUrl;
        prevImg.parentElement.style.display = "block";
    } else {
        prevImg.parentElement.style.display = "none";
    }

    document.getElementById("modal-desc").textContent = reason || "";
    document.getElementById("image-modal").classList.remove("hidden");
}

function closeModal() {
    document.getElementById("image-modal").classList.add("hidden");
    document.getElementById("modal-image-curr").src = "";
    document.getElementById("modal-image-prev").src = "";
}

// ============ NAVIGATION ============
document.querySelectorAll(".sidebar li").forEach(item => {
    item.addEventListener("click", () => {
        document.querySelectorAll(".sidebar li").forEach(i => i.classList.remove("active"));
        item.classList.add("active");

        const page = item.dataset.page;
        document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));
        document.getElementById(`page-${page}`).classList.remove("hidden");

        if (page === "photos") loadPhotos();
        if (page === "settings") loadSettings();
        if (page === "overview") loadStats();
        if (page === "logs") loadLogs();
    });
});
