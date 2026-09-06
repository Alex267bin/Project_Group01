const app = document.getElementById("app");

let selectedRole = "student";
let currentUser = null;
let qrScanner = null;
let qrRefreshTimer = null;
let activeSession = null;
let lecturerRows = [];
let attendanceRows = [];
let users = [];

const icons = {
  building: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V6l8-3 8 3v15"/><path d="M8 9h1M8 13h1M8 17h1M15 9h1M15 13h1M15 17h1"/><path d="M10 21v-4h4v4"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-6"/></svg>`,
  eye: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/></svg>`,
  qr: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z"/><path d="M14 14h2v2h-2zM18 14h2v2h-2zM14 18h2v2h-2zM18 18h2v2h-2z"/></svg>`,
  check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 4.8 2.8 18a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3l-7.5-13.2a2 2 0 0 0-3.4 0Z"/></svg>`,
  search: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 5 5"/></svg>`,
  sync: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M18.2 12A7 7 0 0 0 6.5 7.2L4 9"/><path d="M5.8 12A7 7 0 0 0 17.5 16.8L20 15"/></svg>`,
  user: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5"/><path d="M5 21a7 7 0 0 1 14 0"/></svg>`,
  users: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 21a6 6 0 0 1 12 0"/><path d="M16 5.5a3 3 0 0 1 0 5.8"/><path d="M18 14a5 5 0 0 1 3 4.5"/></svg>`,
  pulse: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h4l2-7 4 14 2-7h6"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 4-.8L19 8.2a2.1 2.1 0 0 0-3-3L5 16.2 4 20Z"/><path d="m14.5 6.5 3 3"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString([], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function statusBadge(status) {
  const s = String(status || "").toLowerCase();
  const label = status || "—";
  if (s === "present") return `<span class="status-badge present">${escapeHtml(label)}</span>`;
  if (s === "late") return `<span class="status-badge late">${escapeHtml(label)}</span>`;
  if (s === "absent") return `<span class="status-badge absent">${escapeHtml(label)}</span>`;
  return `<span class="status-badge">${escapeHtml(label)}</span>`;
}

function initials(name) {
  const parts = String(name || "User").trim().split(/\s+/).slice(0, 2);
  return parts.map(p => p[0]).join("").toUpperCase() || "U";
}

function showToast(type, message) {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 200);
  }, 3200);
}

function showInline(id, type, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `inline-alert ${type}`;
  el.innerHTML = `${type === "success" ? icons.check : icons.alert}<span>${escapeHtml(message)}</span>`;
  el.hidden = false;
}

function clearInline(id) {
  const el = document.getElementById(id);
  if (el) el.hidden = true;
}

function userFromToken() {
  const payload = decodeTokenPayload();
  const role = String(payload?.role || localStorage.getItem("selected_role") || "").toLowerCase();
  return {
    name: payload?.full_name || payload?.name || (role === "lecturer" ? "Dr. James Mitchell" : role === "admin" ? "Reg. Chief Clerk" : "Sarah Chen"),
    code: payload?.student_code || payload?.username || (role === "student" ? "STU-2024-0847" : ""),
    role
  };
}

function header(user, kind) {
  const title = kind === "lecturer" ? "UTH University Faculty" : kind === "admin" ? "UTH University Admin" : "UTH University";
  const subtitle = kind === "lecturer" ? "Computer Science Department" : kind === "admin" ? "Master Registry & Portal" : (user.code || "STU-2024-0847");
  const roleLabel = kind.charAt(0).toUpperCase() + kind.slice(1);

  return `
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">${icons.building}</div>
        <div>
          <div class="brand-title">${escapeHtml(title)}</div>
          <div class="brand-subtitle">${escapeHtml(subtitle)}</div>
        </div>
      </div>
      <div class="top-actions">
        ${kind === "student" ? `<button class="notification" aria-label="Notifications">${icons.bell}<span></span></button>` : ""}
        <div class="account">
          ${kind === "student" ? `<div class="account-copy"><strong>${escapeHtml(user.name)}</strong><span class="role-label ${kind}">${roleLabel}</span></div><div class="avatar">${initials(user.name)}</div>` : `<div class="account-copy"><strong>${escapeHtml(user.name)}</strong><span class="role-label ${kind}">${roleLabel}</span></div>`}
        </div>
        <button class="logout-btn" id="logout-btn">${icons.logout}<span>Logout</span></button>
      </div>
    </header>`;
}

function bindLogout() {
  document.getElementById("logout-btn")?.addEventListener("click", () => {
    clearQrRefresh();
    if (qrScanner) stopQrScanner();
    logout();
    loginView();
  });
}

function loginView(errorMessage = "") {
  clearQrRefresh();
  app.innerHTML = `
    <main class="login-page">
      <section class="login-card">
        <div class="login-logo">${icons.building}</div>
        <h1>Student Attendance System</h1>
        <p class="login-subtitle">Please sign in to access your portal</p>

        <div id="login-alert" class="login-alert" ${errorMessage ? "" : "hidden"}>
          ${icons.alert}<span>${escapeHtml(errorMessage)}</span>
        </div>

        <form id="login-form" novalidate>
          <label class="section-label">Sign In As</label>
          <div class="role-tabs" role="tablist">
            ${["student","lecturer","admin"].map(role => `
              <button type="button" class="role-tab ${selectedRole === role ? "active" : ""}" data-role="${role}">
                ${role.charAt(0).toUpperCase() + role.slice(1)}
              </button>`).join("")}
          </div>

          <label class="field-label" for="username">Username or Academic Email</label>
          <input id="username" class="text-input" autocomplete="username" placeholder="sarah.chen@uth.edu">

          <label class="field-label" for="password">Password</label>
          <div class="password-input">
            <input id="password" class="text-input" type="password" autocomplete="current-password" placeholder="••••••••">
            <button type="button" id="toggle-password" aria-label="Show password">${icons.eye}</button>
          </div>

          <div class="login-options">
            <label class="remember"><input id="remember" type="checkbox" checked><span>Remember me</span></label>
            <button type="button" class="text-link" id="forgot-password">Forgot Password?</button>
          </div>

          <button class="primary-btn login-btn" type="submit">Sign In</button>
        </form>
      </section>
    </main>`;

  document.querySelectorAll(".role-tab").forEach(button => {
    button.addEventListener("click", () => {
      selectedRole = button.dataset.role;
      localStorage.setItem("selected_role", selectedRole);
      document.querySelectorAll(".role-tab").forEach(b => b.classList.toggle("active", b === button));
    });
  });

  document.getElementById("toggle-password")?.addEventListener("click", () => {
    const input = document.getElementById("password");
    input.type = input.type === "password" ? "text" : "password";
  });

  document.getElementById("forgot-password")?.addEventListener("click", () => {
    showToast("info", "Password recovery is handled by the authentication service.");
  });

  document.getElementById("login-form")?.addEventListener("submit", async event => {
    event.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const button = event.currentTarget.querySelector("button[type=submit]");

    if (!username || !password) {
      showInline("login-alert", "error", "Please enter your username/email and password.");
      return;
    }

    button.disabled = true;
    button.textContent = "Signing In…";

    try {
      await login(username, password);
      const actual = userFromToken();
      if (actual.role && actual.role !== selectedRole) {
        throw new Error(`The account is assigned to ${actual.role}, not ${selectedRole}.`);
      }
      currentUser = actual;
      showDashboard(actual.role || selectedRole);
    } catch (error) {
      showInline("login-alert", "error", error.message);
    } finally {
      button.disabled = false;
      button.textContent = "Sign In";
    }
  });
}

function studentView() {
  currentUser = currentUser || userFromToken();

  app.innerHTML = `
    <div class="app-shell">
      ${header(currentUser, "student")}
      <main class="content">
        <section class="card attendance-card">
          <h2>Submit Live Attendance</h2>
          <p class="card-description">Enter the 6-digit code displayed by your lecturer or scan their QR code to register your check-in.</p>
          <div id="student-alert" class="inline-alert" hidden></div>

          <div class="attendance-entry">
            <div class="code-inputs">
              ${[0,1,2,3,4,5].map(i => `<input class="code-input" maxlength="1" inputmode="numeric" aria-label="Attendance code digit ${i+1}" data-index="${i}">`).join("")}
            </div>
            <button class="primary-btn submit-code-btn" id="submit-code">${icons.check}<span>Submit Code</span></button>
            <button class="secondary-btn" id="scan-qr">${icons.qr}<span>Scan QR Code</span></button>
          </div>
        </section>

        <section class="card history-card">
          <div class="section-head">
            <h2>Attendance History</h2>
            <div class="filters">
              <select id="course-filter" class="select-input"><option value="">Course: All Courses</option></select>
              <select id="semester-filter" class="select-input">
                <option value="">Semester: All Semesters</option>
                <option value="Fall 2024">Semester: Fall 2024</option>
                <option value="Spring 2025">Semester: Spring 2025</option>
              </select>
            </div>
          </div>
          <div class="table-scroll">
            <table class="data-table">
              <thead><tr><th>Date &amp; Time</th><th>Course Name</th><th>Lecturer</th><th>Session Code</th><th>Status</th></tr></thead>
              <tbody id="student-history"><tr><td colspan="5" class="empty-row">Loading attendance history…</td></tr></tbody>
            </table>
          </div>
        </section>
      </main>
    </div>`;

  bindLogout();

  const digits = [...document.querySelectorAll(".code-input")];
  digits.forEach((input, index) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "").slice(0, 1);
      if (input.value && digits[index + 1]) digits[index + 1].focus();
    });
    input.addEventListener("keydown", event => {
      if (event.key === "Backspace" && !input.value && digits[index - 1]) digits[index - 1].focus();
    });
    input.addEventListener("paste", event => {
      const value = (event.clipboardData?.getData("text") || "").replace(/\D/g, "").slice(0, 6);
      if (!value) return;
      event.preventDefault();
      value.split("").forEach((digit, i) => { if (digits[i]) digits[i].value = digit; });
      digits[Math.min(value.length, 6) - 1]?.focus();
    });
  });

  document.getElementById("submit-code")?.addEventListener("click", submitCode);
  document.getElementById("scan-qr")?.addEventListener("click", openQrScanner);
  document.getElementById("course-filter")?.addEventListener("change", renderStudentHistory);
  document.getElementById("semester-filter")?.addEventListener("change", renderStudentHistory);

  loadStudentHistory();
}

async function loadStudentHistory() {
  try {
    attendanceRows = await getAttendanceHistory();
    renderStudentHistory();
    populateCourseFilter();
  } catch (error) {
    attendanceRows = [];
    renderStudentHistory();
    showToast("error", `Attendance history could not be loaded: ${error.message}`);
  }
}

function populateCourseFilter() {
  const select = document.getElementById("course-filter");
  if (!select) return;
  const courses = [...new Set(attendanceRows.map(row => row.course_name).filter(Boolean))];
  select.innerHTML = `<option value="">Course: All Courses</option>` +
    courses.map(course => `<option value="${escapeHtml(course)}">${escapeHtml(course)}</option>`).join("");
}

function renderStudentHistory() {
  const tbody = document.getElementById("student-history");
  if (!tbody) return;

  const course = document.getElementById("course-filter")?.value || "";
  const semester = document.getElementById("semester-filter")?.value || "";

  const filtered = attendanceRows.filter(row => {
    const courseMatch = !course || row.course_name === course;
    // The current attendance history response does not expose semester.
    // Keep the filter in the UI as specified; it is applied when the backend
    // provides semester metadata in a future compatible response.
    const semesterMatch = !semester || !row.semester || row.semester === semester;
    return courseMatch && semesterMatch;
  });

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No attendance records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(row => `
    <tr>
      <td>${escapeHtml(formatTime(row.timestamp))}</td>
      <td class="strong">${escapeHtml(row.course_name || "—")}</td>
      <td>${escapeHtml(row.lecturer_name || "—")}</td>
      <td>${escapeHtml(row.session_code || "—")}</td>
      <td>${statusBadge(row.status)}</td>
    </tr>`).join("");
}

async function submitCode() {
  const code = [...document.querySelectorAll(".code-input")].map(input => input.value).join("");
  if (code.length !== 6) {
    showInline("student-alert", "error", "Please enter the complete 6-digit attendance code.");
    return;
  }

  // The supplied backend contract exposes QR submission at /attendance/scan,
  // but does not expose a code-only attendance endpoint. Do not fake a success.
  showInline(
    "student-alert",
    "info",
    "The 6-digit code UI is ready, but the supplied backend contract does not expose a code-only attendance endpoint. Use Scan QR Code for the currently supported attendance API."
  );
}

function openQrScanner() {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.id = "qr-modal";
  backdrop.innerHTML = `
    <div class="modal-card qr-modal">
      <button class="modal-close" id="close-qr" aria-label="Close">×</button>
      <div class="modal-icon">${icons.qr}</div>
      <h3>Scan Attendance QR Code</h3>
      <p class="modal-description">Allow camera access and position the lecturer's QR code inside the frame.</p>
      <div id="qr-reader" class="qr-reader"></div>
      <div id="qr-status" class="scanner-status">Starting camera…</div>
      <button class="secondary-btn modal-cancel" id="cancel-qr">Cancel</button>
    </div>`;
  document.body.appendChild(backdrop);

  document.getElementById("close-qr").addEventListener("click", stopQrScanner);
  document.getElementById("cancel-qr").addEventListener("click", stopQrScanner);

  if (typeof Html5Qrcode === "undefined") {
    document.getElementById("qr-status").textContent = "QR scanner library is unavailable.";
    return;
  }

  qrScanner = new Html5Qrcode("qr-reader");
  qrScanner.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: { width: 230, height: 230 } },
    decodedText => handleQrPayload(decodedText),
    () => {}
  ).then(() => {
    const status = document.getElementById("qr-status");
    if (status) status.textContent = "Camera active — point it at the attendance QR code.";
  }).catch(error => {
    const status = document.getElementById("qr-status");
    if (status) status.textContent = `Camera could not be started: ${error}`;
  });
}

async function handleQrPayload(decodedText) {
  const status = document.getElementById("qr-status");
  if (status) status.textContent = "QR detected. Validating…";

  let payload;
  try {
    payload = JSON.parse(decodedText);
  } catch (_) {
    if (status) status.textContent = "Invalid QR format.";
    return;
  }

  if (!payload.session_id || !payload.session_code || !payload.token || payload.timestamp_bucket === undefined) {
    if (status) status.textContent = "This QR code is not a valid attendance QR.";
    return;
  }

  try {
    await scanAttendance({
      session_id: String(payload.session_id),
      session_code: String(payload.session_code),
      token: String(payload.token),
      timestamp_bucket: Number(payload.timestamp_bucket)
    });
    stopQrScanner();
    showInline("student-alert", "success", "Attendance submitted successfully.");
    await loadStudentHistory();
  } catch (error) {
    if (status) status.textContent = error.message;
  }
}

function stopQrScanner() {
  if (qrScanner) {
    qrScanner.stop().catch(() => {}).finally(() => {
      qrScanner.clear();
      qrScanner = null;
    });
  }
  document.getElementById("qr-modal")?.remove();
}

function lecturerView() {
  currentUser = currentUser || userFromToken();

  app.innerHTML = `
    <div class="app-shell">
      ${header(currentUser, "lecturer")}
      <main class="content lecturer-content">
        <div class="lecturer-grid">
          <aside class="card session-card">
            <h2>Session Control</h2>
            <p class="card-description">Deploy a code and QR code for real-time tracking.</p>

            <label class="field-label" for="course-name">Active Course</label>
            <input id="course-name" class="text-input" value="CS301 - Database Systems">

            <label class="field-label" for="class-location">Class ID / Location</label>
            <input id="class-location" class="text-input" value="Room 402 - Lab A">

            <button class="primary-btn full-btn" id="generate-session">${icons.sync}<span>Generate New Session Code</span></button>

            <div class="divider"></div>

            <div class="active-code">
              <span>ACTIVE ATTENDANCE CODE</span>
              <strong id="session-code">—</strong>
            </div>

            <div class="qr-display">
              <div class="qr-placeholder" id="qr-placeholder">${icons.qr}</div>
              <img id="qr-image" alt="Active attendance QR code" hidden>
              <p>Students can scan this to check in instantly</p>
            </div>

            <div id="lecturer-alert" class="inline-alert" hidden></div>
          </aside>

          <section class="lecturer-main">
            <div class="stat-grid">
              <div class="card stat-card"><span>Total Students</span><strong id="total-students">—</strong></div>
              <div class="card stat-card"><span>Present Today</span><strong id="present-today">—</strong></div>
              <div class="card stat-card"><span>Late Check-Ins</span><strong id="late-checkins">—</strong></div>
              <div class="card stat-card"><span>Absent / Outstanding</span><strong id="absent-outstanding">—</strong></div>
            </div>

            <section class="card stream-card">
              <div class="section-head stream-head">
                <div>
                  <h2>Real-time Check-In Stream</h2>
                  <p class="card-description">Live roster updates as students input the code.</p>
                </div>
                <div class="stream-controls">
                  <div class="search-field">${icons.search}<input id="student-search" placeholder="Search student name…"></div>
                  <div class="status-tabs">
                    <button class="status-tab active" data-filter="all">All</button>
                    <button class="status-tab" data-filter="present">Present</button>
                    <button class="status-tab" data-filter="absent">Absent</button>
                  </div>
                </div>
              </div>

              <div class="table-scroll">
                <table class="data-table">
                  <thead><tr><th>Student ID</th><th>Full Name</th><th>Check-In Time</th><th>Status</th><th>Change Status</th></tr></thead>
                  <tbody id="lecturer-table"><tr><td colspan="5" class="empty-row">Generate a session to view check-ins.</td></tr></tbody>
                </table>
              </div>
            </section>
          </section>
        </div>
      </main>
    </div>`;

  bindLogout();

  document.getElementById("generate-session")?.addEventListener("click", generateLecturerSession);
  document.getElementById("student-search")?.addEventListener("input", renderLecturerRows);
  document.querySelectorAll(".status-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".status-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      renderLecturerRows();
    });
  });
}

async function generateLecturerSession() {
  const course = document.getElementById("course-name")?.value.trim();
  const button = document.getElementById("generate-session");
  if (!course) {
    showToast("error", "Please enter the active course name.");
    return;
  }

  button.disabled = true;
  try {
    const now = new Date();
    const end = new Date(now.getTime() + 60 * 60 * 1000);
    activeSession = await activateSession({
      course_name: course,
      start_time: now.toISOString(),
      end_time: end.toISOString()
    });

    document.getElementById("session-code").textContent = activeSession.session_code || "—";
    const image = document.getElementById("qr-image");
    image.src = activeSession.qr_data_uri || "";
    image.hidden = !activeSession.qr_data_uri;
    document.getElementById("qr-placeholder").hidden = !!activeSession.qr_data_uri;

    showInline("lecturer-alert", "success", "Active attendance session created.");
    await loadLecturerAttendance(activeSession.session_id);
    startQrRefresh(activeSession.session_id);
  } catch (error) {
    showInline("lecturer-alert", "error", error.message);
  } finally {
    button.disabled = false;
  }
}

async function loadLecturerAttendance(sessionId) {
  try {
    lecturerRows = await getSessionAttendance(sessionId);
    renderLecturerRows();
  } catch (error) {
    lecturerRows = [];
    renderLecturerRows();
    showToast("error", `Check-in data could not be loaded: ${error.message}`);
  }
}

function renderLecturerRows() {
  const tbody = document.getElementById("lecturer-table");
  if (!tbody) return;

  const query = document.getElementById("student-search")?.value.trim().toLowerCase() || "";
  const filter = document.querySelector(".status-tab.active")?.dataset.filter || "all";

  const rows = lecturerRows.filter(row => {
    const text = `${row.student_code || ""} ${row.student_name || ""}`.toLowerCase();
    const matchesQuery = !query || text.includes(query);
    const matchesFilter = filter === "all" || String(row.status || "").toLowerCase() === filter;
    return matchesQuery && matchesFilter;
  });

  const total = lecturerRows.length;
  const present = lecturerRows.filter(row => String(row.status).toLowerCase() === "present").length;
  const late = lecturerRows.filter(row => String(row.status).toLowerCase() === "late").length;
  const absent = lecturerRows.filter(row => String(row.status).toLowerCase() === "absent").length;

  document.getElementById("total-students").textContent = total || "—";
  document.getElementById("present-today").textContent = total ? present : "—";
  document.getElementById("late-checkins").textContent = total ? late : "—";
  document.getElementById("absent-outstanding").textContent = total ? absent : "—";

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">${lecturerRows.length ? "No matching students found." : "Generate a session to view check-ins."}</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(row => `
    <tr>
      <td>${escapeHtml(row.student_code || "—")}</td>
      <td class="strong">${escapeHtml(row.student_name || "—")}</td>
      <td>${escapeHtml(formatTime(row.timestamp))}</td>
      <td>${statusBadge(row.status)}</td>
      <td><button class="edit-btn" data-record="${escapeHtml(row.record_id || "")}">${icons.edit}<span>Edit</span></button></td>
    </tr>`).join("");

  document.querySelectorAll(".edit-btn").forEach(button => {
    button.addEventListener("click", () => editAttendance(button.dataset.record));
  });
}

async function editAttendance(recordId) {
  if (!recordId) {
    showToast("info", "This attendance record does not contain a record ID.");
    return;
  }

  const status = window.prompt("Enter status: Present, Late, or Absent");
  if (!["Present", "Late", "Absent"].includes(status)) return;

  try {
    await updateAttendance(recordId, status);
    if (activeSession) await loadLecturerAttendance(activeSession.session_id);
    showToast("success", "Attendance status updated.");
  } catch (error) {
    showToast("error", error.message);
  }
}

function startQrRefresh(sessionId) {
  clearQrRefresh();
  qrRefreshTimer = setInterval(async () => {
    try {
      const result = await refreshSessionQr(sessionId);
      const image = document.getElementById("qr-image");
      if (image && result?.qr_data_uri) image.src = result.qr_data_uri;
    } catch (_) {}
  }, 20000);
}

function clearQrRefresh() {
  if (qrRefreshTimer) {
    clearInterval(qrRefreshTimer);
    qrRefreshTimer = null;
  }
}

function adminView() {
  currentUser = currentUser || userFromToken();

  app.innerHTML = `
    <div class="app-shell">
      ${header(currentUser, "admin")}
      <main class="content">
        <div class="admin-stats">
          <div class="card admin-stat"><div><span>Total Active Students</span><strong id="admin-students">—</strong><small>Current registered student accounts</small></div><div class="stat-icon">${icons.users}</div></div>
          <div class="card admin-stat"><div><span>Active Lecturers</span><strong id="admin-lecturers">—</strong><small>Current lecturer accounts</small></div><div class="stat-icon">${icons.user}</div></div>
          <div class="card admin-stat"><div><span>Active Live Sessions</span><strong id="admin-sessions">—</strong><small>Running right now</small></div><div class="stat-icon">${icons.pulse}</div></div>
        </div>

        <div class="admin-grid">
          <section class="card admin-panel">
            <h2>Department Attendance Rates</h2>
            <p class="card-description">Average attendance rates for the current week.</p>
            <div class="rate-list" id="department-rates">
              <div class="empty-panel">Department reporting data will appear when the reporting endpoint is available.</div>
            </div>
          </section>

          <section class="card admin-panel activity-panel">
            <h2>System Log &amp; Activity</h2>
            <p class="card-description">Latest operational and registration entries.</p>
            <div class="activity-list" id="activity-list">
              <div class="activity-empty">No activity-log endpoint is exposed by the supplied frontend API contract.</div>
            </div>
          </section>
        </div>

        <section class="card user-panel">
          <div class="section-head">
            <div>
              <h2>User Management</h2>
              <p class="card-description">Create, update, and delete users.</p>
            </div>
            <button class="primary-btn" id="add-user">${icons.plus}<span>Add User</span></button>
          </div>
          <div class="table-scroll">
            <table class="data-table">
              <thead><tr><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead>
              <tbody id="user-table"><tr><td colspan="5" class="empty-row">Loading users…</td></tr></tbody>
            </table>
          </div>
        </section>
      </main>
    </div>`;

  bindLogout();
  document.getElementById("add-user")?.addEventListener("click", () => openUserModal());
  loadAdminUsers();
}

async function loadAdminUsers() {
  try {
    users = await getUsers();
    renderUsers();
    const counts = users.reduce((acc, user) => {
      const role = String(user.role || "").toLowerCase();
      if (role.includes("student")) acc.students++;
      if (role.includes("lecturer")) acc.lecturers++;
      return acc;
    }, { students: 0, lecturers: 0 });
    document.getElementById("admin-students").textContent = counts.students || "—";
    document.getElementById("admin-lecturers").textContent = counts.lecturers || "—";
  } catch (error) {
    renderUsers(error.message);
  }
}

function renderUsers(errorMessage = "") {
  const tbody = document.getElementById("user-table");
  if (!tbody) return;

  if (errorMessage) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">${escapeHtml(errorMessage)}</td></tr>`;
    return;
  }

  if (!users.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No users found.</td></tr>`;
    return;
  }

  tbody.innerHTML = users.map(user => `
    <tr>
      <td>${escapeHtml(user.username)}</td>
      <td class="strong">${escapeHtml(user.full_name)}</td>
      <td>${escapeHtml(user.email)}</td>
      <td><span class="role-chip">${escapeHtml(user.role)}</span></td>
      <td>
        <div class="row-actions">
          <button class="edit-btn" data-edit-user="${escapeHtml(user.user_id)}">${icons.edit}<span>Edit</span></button>
          <button class="danger-btn" data-delete-user="${escapeHtml(user.user_id)}">${icons.trash}<span>Delete</span></button>
        </div>
      </td>
    </tr>`).join("");

  document.querySelectorAll("[data-edit-user]").forEach(button => {
    button.addEventListener("click", () => {
      const user = users.find(item => item.user_id === button.dataset.editUser);
      if (user) openUserModal(user);
    });
  });

  document.querySelectorAll("[data-delete-user]").forEach(button => {
    button.addEventListener("click", async () => {
      const user = users.find(item => item.user_id === button.dataset.deleteUser);
      if (!user || !confirm(`Delete user "${user.username}"?`)) return;
      try {
        await deleteUser(user.user_id);
        showToast("success", "User deleted.");
        await loadAdminUsers();
      } catch (error) {
        showToast("error", error.message);
      }
    });
  });
}

function openUserModal(user = null) {
  const editing = !!user;
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "user-modal";
  modal.innerHTML = `
    <div class="modal-card form-modal">
      <button class="modal-close" id="close-user-modal" aria-label="Close">×</button>
      <h3>${editing ? "Edit User" : "Create User"}</h3>
      <p class="modal-description">Manage the account information required by the User Management process.</p>
      <form id="user-form">
        <label class="field-label">Username</label>
        <input class="text-input" name="username" value="${escapeHtml(user?.username || "")}" required>
        <label class="field-label">Full Name</label>
        <input class="text-input" name="full_name" value="${escapeHtml(user?.full_name || "")}" required>
        <label class="field-label">Email</label>
        <input class="text-input" type="email" name="email" value="${escapeHtml(user?.email || "")}" required>
        <label class="field-label">Role</label>
        <select class="select-input" name="role">
          ${["Student","Lecturer","Admin"].map(role => `<option ${user?.role === role ? "selected" : ""}>${role}</option>`).join("")}
        </select>
        <label class="field-label">${editing ? "New Password (optional)" : "Password"}</label>
        <input class="text-input" type="password" name="password" ${editing ? "" : "required"}>
        <button class="primary-btn full-btn" type="submit">${editing ? "Save Changes" : "Create User"}</button>
      </form>
    </div>`;
  document.body.appendChild(modal);

  document.getElementById("close-user-modal").addEventListener("click", () => modal.remove());
  document.getElementById("user-form").addEventListener("submit", async event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    if (editing && !data.password) delete data.password;

    try {
      if (editing) await updateUser(user.user_id, data);
      else await createUser(data);
      modal.remove();
      showToast("success", editing ? "User updated." : "User created.");
      await loadAdminUsers();
    } catch (error) {
      showToast("error", error.message);
    }
  });
}

function showDashboard(role) {
  if (role === "student") studentView();
  else if (role === "lecturer") lecturerView();
  else if (role === "admin") adminView();
  else loginView();
}

const token = localStorage.getItem("access_token");
if (token) {
  const payload = decodeTokenPayload(token);
  const role = String(payload?.role || localStorage.getItem("selected_role") || "").toLowerCase();
  if (["student", "lecturer", "admin"].includes(role)) showDashboard(role);
  else loginView();
} else {
  loginView();
}
