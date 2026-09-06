const DEMO_USERS = [
  { user_id: "u1", username: "student01", full_name: "Sarah Chen", email: "sarah.chen@uth.edu", role: "Student" },
  { user_id: "u2", username: "lecturer01", full_name: "Dr. Michael Lee", email: "michael.lee@uth.edu", role: "Lecturer" },
  { user_id: "u3", username: "admin01", full_name: "System Admin", email: "admin@uth.edu", role: "Admin" }
];

let demoUsers = structuredClone(DEMO_USERS);
let demoAttendance = [
  { record_id:"r1", student_code:"SV001", student_name:"Sarah Chen", course_name:"CS301 - Database Systems", lecturer_name:"Dr. Michael Lee", session_code:"482913", timestamp:"2026-09-06T08:10:00", status:"Present", semester:"Fall 2024" },
  { record_id:"r2", student_code:"SV002", student_name:"Alex Nguyen", course_name:"CS301 - Database Systems", lecturer_name:"Dr. Michael Lee", session_code:"482913", timestamp:"2026-09-06T08:12:00", status:"Late", semester:"Fall 2024" },
  { record_id:"r3", student_code:"SV003", student_name:"Minh Tran", course_name:"CS302 - Web Development", lecturer_name:"Dr. Anna Smith", session_code:"135724", timestamp:"2026-09-05T10:02:00", status:"Present", semester:"Spring 2025" }
];

function demoToken(role, username) {
  const payload = btoa(JSON.stringify({ role, username })).replace(/=/g, "");
  return `demo.${payload}.token`;
}

async function login(username, password) {
  if (!username || !password) throw new Error("Username and password are required.");
  const role = localStorage.getItem("selected_role") || "student";
  const token = demoToken(role, username);
  localStorage.setItem("access_token", token);
  localStorage.setItem("token_type", "bearer");
  return { access_token: token, token_type: "bearer" };
}

function decodeTokenPayload(token = localStorage.getItem("access_token")) {
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    return JSON.parse(atob(part));
  } catch (_) { return null; }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");
  localStorage.removeItem("selected_role");
}

async function getAttendanceHistory() { return structuredClone(demoAttendance); }
async function activateSession(payload) {
  const sessionId = `demo-session-${Date.now()}`;
  return {
    session_id: sessionId,
    course_name: payload.course_name,
    lecturer_code: "LECT01",
    start_time: payload.start_time,
    end_time: payload.end_time,
    session_code: "482913",
    qr_data_uri: makeDemoQr("482913")
  };
}
async function refreshSessionQr(sessionId) {
  return { session_id: sessionId, qr_data_uri: makeDemoQr(String(Math.floor(100000 + Math.random() * 900000))) };
}
async function getSessionAttendance() { return structuredClone(demoAttendance); }
async function updateAttendance(recordId, status) {
  const row = demoAttendance.find(item => item.record_id === recordId);
  if (row) row.status = status;
  return row;
}
async function getUsers() { return structuredClone(demoUsers); }
async function createUser(payload) {
  const user = { ...payload, user_id: `u${Date.now()}` };
  demoUsers.push(user); return user;
}
async function updateUser(userId, payload) {
  const index = demoUsers.findIndex(user => user.user_id === userId);
  if (index >= 0) demoUsers[index] = { ...demoUsers[index], ...payload };
  return demoUsers[index];
}
async function deleteUser(userId) { demoUsers = demoUsers.filter(user => user.user_id !== userId); }
async function getCourses() { return [{ course_name: "CS301 - Database Systems" }, { course_name: "CS302 - Web Development" }]; }

function makeDemoQr(value) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240"><rect width="240" height="240" fill="white"/><rect x="18" y="18" width="62" height="62" fill="none" stroke="#111" stroke-width="10"/><rect x="160" y="18" width="62" height="62" fill="none" stroke="#111" stroke-width="10"/><rect x="18" y="160" width="62" height="62" fill="none" stroke="#111" stroke-width="10"/><path d="M105 24h25v25h-25zM105 65h18v18h-18zM96 106h22v22H96zM126 106h32v18h-32zM166 105h28v28h-28zM105 145h18v22h-18zM130 150h30v30h-30zM170 150h22v22h-22zM98 190h25v25H98zM138 192h18v18h-18z" fill="#111"/><text x="120" y="238" text-anchor="middle" font-size="12" font-family="Arial">${value}</text></svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}
