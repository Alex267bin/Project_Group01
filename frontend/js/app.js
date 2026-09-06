const app = document.getElementById("app");

const icons = {
  check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 4.8 2.8 18a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3l-7.5-13.2a2 2 0 0 0-3.4 0Z"/>`,
  search: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 5 5"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`
};

app.innerHTML = `
  <main class="content" style="max-width:1200px;margin:auto">
    <div class="section-head">
      <div>
        <h1 style="margin:0;font-size:30px">UTH Attendance Design System</h1>
        <p class="card-description">Shared visual foundations and reusable UI components for the attendance application.</p>
      </div>
    </div>

    <section class="card attendance-card">
      <h2>Typography &amp; colors</h2>
      <p class="card-description">Primary, semantic, surface and muted tokens are defined in the shared stylesheet.</p>
      <div class="demo-grid">
        <div><span class="status-badge">Neutral</span><span class="status-badge present">Present</span><span class="status-badge late">Late</span><span class="status-badge absent">Absent</span></div>
        <div class="inline-alert success">${icons.check}<span>Success feedback component</span></div>
        <div class="inline-alert error">${icons.alert}<span>Error feedback component</span></div>
        <div class="inline-alert info">${icons.alert}<span>Informational feedback component</span></div>
      </div>
    </section>

    <section class="card attendance-card">
      <h2>Buttons &amp; form controls</h2>
      <p class="card-description">Buttons, inputs, selects and code-entry controls used throughout the screens.</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
        <button class="primary-btn">${icons.check}<span>Primary Button</span></button>
        <button class="secondary-btn">Secondary Button</button>
        <button class="primary-btn">${icons.plus}<span>Add User</span></button>
        <button class="secondary-btn">${icons.search}<span>Search</span></button>
        <input class="text-input" placeholder="Text input" style="max-width:250px">
        <select class="select-input"><option>Select option</option><option>Option 2</option></select>
      </div>
      <div class="code-inputs" style="margin-top:24px">
        ${[1,2,3,4,5,6].map(() => `<input class="code-input" value="" aria-label="Code digit">`).join("")}
      </div>
    </section>

    <section class="card history-card">
      <div class="section-head"><div><h2>Table &amp; badges</h2><p class="card-description">Reusable data-table treatment for attendance history and management screens.</p></div></div>
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Date &amp; Time</th><th>Course Name</th><th>Student ID</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr><td>Sep 06, 2026 09:10</td><td class="strong">Database Systems</td><td>SV001</td><td><span class="status-badge present">Present</span></td><td><button class="edit-btn">Edit</button></td></tr>
            <tr><td>Sep 06, 2026 09:14</td><td class="strong">Web Development</td><td>SV002</td><td><span class="status-badge late">Late</span></td><td><button class="edit-btn">Edit</button></td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>`;
