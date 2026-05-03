const baseUrlInput = document.getElementById("baseUrl");
const saveBaseUrlButton = document.getElementById("saveBaseUrlButton");
const sessionBadge = document.getElementById("sessionBadge");
const logoutButton = document.getElementById("logoutButton");
const authMessage = document.getElementById("authMessage");
const dashboardHeading = document.getElementById("dashboardHeading");
const dashboardSubtext = document.getElementById("dashboardSubtext");
const currentRole = document.getElementById("currentRole");
const currentUserId = document.getElementById("currentUserId");
const monthlyTotalEl = document.getElementById("monthlyTotal");
const monthlyCountEl = document.getElementById("monthlyCount");
const transactionCountEl = document.getElementById("transactionCount");
const topCategoryEl = document.getElementById("topCategory");
const topCategoryValueEl = document.getElementById("topCategoryValue");
const chartTotalEl = document.getElementById("chartTotal");
const pieChartEl = document.getElementById("pieChart");
const pieLegendEl = document.getElementById("pieLegend");
const budgetBodyEl = document.getElementById("budgetBody");
const recentBodyEl = document.getElementById("recentBody");
const usersBodyEl = document.getElementById("usersBody");
const adminPanel = document.getElementById("adminPanel");
const adminMessage = document.getElementById("adminMessage");
const refreshButton = document.getElementById("refreshButton");
const loadUsersButton = document.getElementById("loadUsersButton");
const roleForm = document.getElementById("roleForm");
const deleteUserForm = document.getElementById("deleteUserForm");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authTabButtons = document.querySelectorAll("[data-auth-tab]");
const authPanels = document.querySelectorAll("[data-auth-panel]");
const workspaceNavMessage = document.getElementById("workspaceNavMessage");
const workspaceNavButtons = document.querySelectorAll("[data-workspace-target]");
const workspaceSection = document.getElementById("workspaceSection");
const expenseCard = document.getElementById("expenseCard");
const budgetCard = document.getElementById("budgetCard");
const reportCard = document.getElementById("reportCard");
const expenseForm = document.getElementById("expenseForm");
const loadExpensesButton = document.getElementById("loadExpensesButton");
const expenseMessage = document.getElementById("expenseMessage");
const expenseCategorySelect = document.getElementById("expenseCategorySelect");
const expensesBody = document.getElementById("expensesBody");
const budgetForm = document.getElementById("budgetForm");
const loadBudgetsButton = document.getElementById("loadBudgetsButton");
const budgetMessage = document.getElementById("budgetMessage");
const budgetCategorySelect = document.getElementById("budgetCategorySelect");
const budgetsBody = document.getElementById("budgetsBody");
const reportForm = document.getElementById("reportForm");
const loadReportsButton = document.getElementById("loadReportsButton");
const reportMessage = document.getElementById("reportMessage");
const reportsBody = document.getElementById("reportsBody");
const categoryStudio = document.getElementById("categoryStudio");
const categoryForm = document.getElementById("categoryForm");
const loadCategoriesButton = document.getElementById("loadCategoriesButton");
const categoryMessage = document.getElementById("categoryMessage");
const categoriesBody = document.getElementById("categoriesBody");
const recordModal = document.getElementById("recordModal");
const recordModalEyebrow = document.getElementById("recordModalEyebrow");
const recordModalTitle = document.getElementById("recordModalTitle");
const recordModalClose = document.getElementById("recordModalClose");
const recordModalForm = document.getElementById("recordModalForm");
const recordModalMessage = document.getElementById("recordModalMessage");

const colors = ["#38bdf8", "#14b8a6", "#f59e0b", "#818cf8", "#fb7185", "#22c55e", "#a855f7", "#06b6d4"];

const state = {
  baseUrl: localStorage.getItem("financer_base_url") || "http://127.0.0.1:5000",
  session: loadSession(),
  expenses: [],
  budgets: [],
  categories: [],
  activeModal: null,
};

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem("financer_session") || "null");
  } catch {
    return null;
  }
}

function saveSession(user) {
  state.session = user;
  localStorage.setItem("financer_session", JSON.stringify(user));
}

function clearSession() {
  state.session = null;
  localStorage.removeItem("financer_session");
}

function saveBaseUrl(value) {
  state.baseUrl = (value || "http://127.0.0.1:5000").trim().replace(/\/$/, "");
  localStorage.setItem("financer_base_url", state.baseUrl);
  baseUrlInput.value = state.baseUrl;
}

function getBaseUrl() {
  return (baseUrlInput.value || state.baseUrl || "http://127.0.0.1:5000").trim().replace(/\/$/, "");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function buildFormPayload(form, extras = {}) {
  const payload = { ...extras };
  const formData = new FormData(form);

  for (const [key, value] of formData.entries()) {
    if (value === "") {
      continue;
    }

    if (key === "is_default") {
      payload.is_default = form.elements.is_default?.checked || false;
      continue;
    }

    if (key === "category_id" || key === "user_id" || key === "budget_id" || key === "report_id" || key === "expense_id") {
      payload[key] = Number(value);
      continue;
    }

    if (key === "amount" || key === "amount_limit") {
      payload[key] = Number(value);
      continue;
    }

    payload[key] = value;
  }

  return payload;
}

function requestMessage(target, text, isError = false) {
  target.textContent = text;
  target.className = isError ? "status-text error" : "status-text";
}

function setAuthMessage(text, isError = false) {
  requestMessage(authMessage, text, isError);
}

function setAdminMessage(text, isError = false) {
  requestMessage(adminMessage, text, isError);
}

function setExpenseMessage(text, isError = false) {
  requestMessage(expenseMessage, text, isError);
}

function setBudgetMessage(text, isError = false) {
  requestMessage(budgetMessage, text, isError);
}

function setReportMessage(text, isError = false) {
  requestMessage(reportMessage, text, isError);
}

function setCategoryMessage(text, isError = false) {
  requestMessage(categoryMessage, text, isError);
}

function setWorkspaceNavMessage(text, isError = false) {
  requestMessage(workspaceNavMessage, text, isError);
}

function setModalMessage(text, isError = false) {
  requestMessage(recordModalMessage, text, isError);
}

function categoryName(categoryId) {
  const match = state.categories.find((category) => Number(category.category_id) === Number(categoryId));
  return match?.name || `Category ${categoryId}`;
}

function categoryOptions(selectedId) {
  const options = state.categories.map((category) => `
    <option value="${category.category_id}" ${Number(category.category_id) === Number(selectedId) ? "selected" : ""}>${escapeHtml(category.name)}</option>
  `).join("");

  return `<option value="">Choose a category</option>${options}`;
}

function closeRecordModal() {
  state.activeModal = null;
  recordModal.classList.add("hidden");
  recordModalForm.innerHTML = "";
  setModalMessage("");
}

function openRecordModal({ type, mode, item }) {
  state.activeModal = { type, mode, item };
  recordModalEyebrow.textContent = mode === "delete" ? "Delete" : "Edit";
  recordModalTitle.textContent = `${mode === "delete" ? "Delete" : "Edit"} ${type}`;
  setModalMessage("");

  if (mode === "delete") {
    const label = type === "expense"
      ? `${escapeHtml(item.expense_date)} - ${money(item.amount)}`
      : type === "budget"
        ? `${escapeHtml(categoryName(item.category_id))} - ${money(item.amount_limit)}`
        : escapeHtml(item.name);
    const id = type === "expense" ? item.expense_id : type === "budget" ? item.budget_id : item.category_id;
    recordModalForm.innerHTML = `
      <p class="subtext">This will remove ${type} #${id}: <strong>${label}</strong>.</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" data-modal-close>Cancel</button>
        <button class="danger-button" type="submit">Delete ${type}</button>
      </div>
    `;
  } else if (type === "expense") {
    recordModalForm.innerHTML = `
      <label>
        Category
        <select name="category_id" required>${categoryOptions(item.category_id)}</select>
      </label>
      <label>
        Amount
        <input name="amount" type="number" min="0.01" step="0.01" value="${escapeHtml(item.amount)}" required />
      </label>
      <label>
        Date
        <input name="expense_date" type="date" value="${escapeHtml(item.expense_date)}" required />
      </label>
      <label>
        Notes
        <textarea name="notes" rows="3">${escapeHtml(item.notes || "")}</textarea>
      </label>
      <div class="modal-actions">
        <button class="ghost-button" type="button" data-modal-close>Cancel</button>
        <button class="primary-button" type="submit">Save expense</button>
      </div>
    `;
  } else if (type === "budget") {
    recordModalForm.innerHTML = `
      <label>
        Category
        <select name="category_id" required>${categoryOptions(item.category_id)}</select>
      </label>
      <label>
        Limit
        <input name="amount_limit" type="number" min="0.01" step="0.01" value="${escapeHtml(item.amount_limit)}" required />
      </label>
      <label>
        Period
        <select name="period" required>
          <option value="weekly" ${item.period === "weekly" ? "selected" : ""}>weekly</option>
          <option value="monthly" ${item.period === "monthly" ? "selected" : ""}>monthly</option>
        </select>
      </label>
      <label>
        Start date
        <input name="start_date" type="date" value="${escapeHtml(item.start_date)}" required />
      </label>
      <div class="modal-actions">
        <button class="ghost-button" type="button" data-modal-close>Cancel</button>
        <button class="primary-button" type="submit">Save budget</button>
      </div>
    `;
  } else {
    recordModalForm.innerHTML = `
      <label>
        Name
        <input name="name" type="text" value="${escapeHtml(item.name)}" required />
      </label>
      <label>
        Description
        <input name="description" type="text" value="${escapeHtml(item.description || "")}" />
      </label>
      <div class="modal-actions">
        <button class="ghost-button" type="button" data-modal-close>Cancel</button>
        <button class="primary-button" type="submit">Save category</button>
      </div>
    `;
  }

  recordModal.classList.remove("hidden");
  recordModalForm.querySelector("input, select, textarea, button")?.focus();
}

function setAuthTab(tab) {
  authTabButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.authTab === tab);
  });

  authPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.authPanel !== tab);
  });
}

function updateWorkspaceNavState() {
  const role = state.session?.role || "guest";

  workspaceNavButtons.forEach((button) => {
    const target = button.dataset.workspaceTarget;
    const isLocked = target === "categoryStudio" && role !== "premium" && role !== "admin";
    button.classList.toggle("locked", isLocked);
  });
}

function openWorkspaceTarget(targetName) {
  const role = state.session?.role || "guest";
  const targetMap = {
    expenseCard,
    budgetCard,
    reportCard,
    categoryStudio,
  };

  if (!state.session?.user_id) {
    setWorkspaceNavMessage("Sign in first to use the workspace shortcuts.", true);
    return;
  }

  if (targetName === "categoryStudio" && role !== "premium" && role !== "admin") {
    setWorkspaceNavMessage("Categories require premium access.", true);
    return;
  }

  const target = targetMap[targetName];
  if (!target) {
    return;
  }

  target.scrollIntoView({ behavior: "smooth", block: "start" });

  if (targetName === "categoryStudio") {
    setWorkspaceNavMessage("Premium category studio opened.");
  } else if (targetName === "expenseCard") {
    setWorkspaceNavMessage("Expenses opened.");
  } else if (targetName === "budgetCard") {
    setWorkspaceNavMessage("Budgets opened.");
  } else if (targetName === "reportCard") {
    setWorkspaceNavMessage("Reports opened.");
  }
}

async function request(path, options = {}) {
  const headers = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${getBaseUrl()}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  let payload = {};

  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { message: text || "Unexpected response" };
  }

  if (!response.ok) {
    throw new Error(payload.message || payload.error || "Request failed");
  }

  return payload;
}

function renderPieChart(items) {
  if (!items.length) {
    pieChartEl.style.backgroundImage = "radial-gradient(circle at center, rgba(255,255,255,0.93) 0 34%, rgba(255,255,255,0.08) 35% 100%)";
    pieLegendEl.innerHTML = '<li class="legend-empty">No category data loaded yet.</li>';
    chartTotalEl.textContent = "0.00";
    topCategoryEl.textContent = "-";
    topCategoryValueEl.textContent = "Log in to load insights";
    return;
  }

  const total = items.reduce((sum, item) => sum + Number(item.total_spent || 0), 0);
  let start = 0;
  const slices = [];

  items.forEach((item, index) => {
    const degrees = total ? (Number(item.total_spent || 0) / total) * 360 : 0;
    const end = index === items.length - 1 ? 360 : start + degrees;
    slices.push(`${colors[index % colors.length]} ${start.toFixed(3)}deg ${end.toFixed(3)}deg`);
    start = end;
  });

  pieChartEl.style.backgroundImage = `conic-gradient(${slices.join(", ")})`;
  chartTotalEl.textContent = money(total);
  topCategoryEl.textContent = items[0]?.category_name || "-";
  topCategoryValueEl.textContent = `${money(items[0]?.total_spent || 0)} spent this month`;

  pieLegendEl.innerHTML = items.map((item, index) => `
    <li>
      <span class="legend-swatch" style="background:${colors[index % colors.length]}"></span>
      <span>${escapeHtml(item.category_name)}</span>
      <strong>${money(item.total_spent)}</strong>
    </li>
  `).join("");
}

function renderBudgetRows(items) {
  if (!items.length) {
    budgetBodyEl.innerHTML = '<tr><td colspan="5" class="empty-cell">No budget data loaded yet.</td></tr>';
    return;
  }

  budgetBodyEl.innerHTML = items.map((item) => `
    <tr class="${item.over_budget ? "row-warning" : ""}">
      <td>${escapeHtml(item.category_name)}</td>
      <td>${money(item.amount_limit)}</td>
      <td>${money(item.total_spent)}</td>
      <td>${money(item.remaining)}</td>
      <td><span class="pill ${item.over_budget ? "danger" : "success"}">${item.over_budget ? "Over budget" : "Remaining"}</span></td>
    </tr>
  `).join("");
}

function renderRecentRows(items) {
  if (!items.length) {
    recentBodyEl.innerHTML = '<tr><td colspan="4" class="empty-cell">No recent transactions loaded yet.</td></tr>';
    return;
  }

  recentBodyEl.innerHTML = items.map((item) => `
    <tr>
      <td>${escapeHtml(item.expense_date)}</td>
      <td>${escapeHtml(item.category_name)}</td>
      <td>${money(item.amount)}</td>
      <td>${escapeHtml(item.notes || "-")}</td>
    </tr>
  `).join("");
}

function renderUsers(items) {
  if (!items.length) {
    usersBodyEl.innerHTML = '<tr><td colspan="4" class="empty-cell">No users loaded yet.</td></tr>';
    return;
  }

  usersBodyEl.innerHTML = items.map((user) => `
    <tr>
      <td>${user.user_id}</td>
      <td>${escapeHtml(user.username)}</td>
      <td>${escapeHtml(user.email)}</td>
      <td><span class="pill ${user.role === "admin" ? "danger" : "success"}">${escapeHtml(user.role)}</span></td>
    </tr>
  `).join("");
}

function renderWorkspaceTable(target, items, emptyMessage, columns, rowBuilder) {
  if (!target) {
    return;
  }

  if (!items.length) {
    target.innerHTML = `<tr><td colspan="${columns}" class="empty-cell">${emptyMessage}</td></tr>`;
    return;
  }

  target.innerHTML = items.map(rowBuilder).join("");
}

function populateCategorySelects(items) {
  const options = items.length
    ? items.map((item) => `<option value="${item.category_id}">${escapeHtml(item.name)}</option>`).join("")
    : '<option value="">No categories available</option>';

  [expenseCategorySelect, budgetCategorySelect].forEach((select) => {
    if (!select) {
      return;
    }

    select.innerHTML = `<option value="">Choose a category</option>${options}`;
    select.disabled = items.length === 0;
  });
}

function renderExpensesRows(items) {
  renderWorkspaceTable(
    expensesBody,
    items,
    "No expenses loaded yet.",
    6,
    (item) => `
      <tr>
        <td>${item.expense_id}</td>
        <td>${escapeHtml(item.expense_date)}</td>
        <td>${escapeHtml(categoryName(item.category_id))}</td>
        <td>${money(item.amount)}</td>
        <td>${escapeHtml(item.notes || "-")}</td>
        <td>
          <div class="row-actions">
            <button class="admin-btn" type="button" data-record-action="edit-expense" data-expense-id="${escapeHtml(item.expense_id)}">Edit</button>
            <button class="admin-btn admin-btn-danger" type="button" data-record-action="delete-expense" data-expense-id="${escapeHtml(item.expense_id)}">Delete</button>
          </div>
        </td>
      </tr>
    `,
  );
}

function renderBudgetRecords(items) {
  renderWorkspaceTable(
    budgetsBody,
    items,
    "No budgets loaded yet.",
    6,
    (item) => `
      <tr>
        <td>${item.budget_id}</td>
        <td>${escapeHtml(categoryName(item.category_id))}</td>
        <td>${money(item.amount_limit)}</td>
        <td>${escapeHtml(item.period)}</td>
        <td>${escapeHtml(item.start_date)}</td>
        <td>
          <div class="row-actions">
            <button class="admin-btn" type="button" data-record-action="edit-budget" data-budget-id="${escapeHtml(item.budget_id)}">Edit</button>
            <button class="admin-btn admin-btn-danger" type="button" data-record-action="delete-budget" data-budget-id="${escapeHtml(item.budget_id)}">Delete</button>
          </div>
        </td>
      </tr>
    `,
  );
}

function reportTypeLabel(type) {
  const labels = {
    monthly_summary: "Monthly summary",
    by_category: "Category breakdown",
    date_range: "Detailed date range",
    "30_days": "Last 30 days",
  };
  return labels[type] || type || "Report";
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderReportMiniList(items, emptyText, itemBuilder) {
  if (!items.length) {
    return `<span class="muted-cell">${escapeHtml(emptyText)}</span>`;
  }

  return `
    <ul class="report-mini-list">
      ${items.map(itemBuilder).join("")}
    </ul>
  `;
}

function renderReportSummaryGrid(items) {
  return `
    <div class="report-summary-grid">
      ${items.map((item) => `
        <span>
          <strong>${escapeHtml(item.value)}</strong>
          <small>${escapeHtml(item.label)}</small>
        </span>
      `).join("")}
    </div>
  `;
}

function renderReportNote(text) {
  return `<span class="muted-cell">${escapeHtml(text)}</span>`;
}

function renderReportBreakdown(item, summary, categories, budgets) {
  if (item.report_type === "by_category") {
    return renderReportMiniList(categories, "No category spending in this range.", (category) => `
      <li>
        <span>${escapeHtml(category.category_name || `Category ${category.category_id}`)}</span>
        <strong>${money(category.total_amount)}</strong>
      </li>
    `);
  }

  if (item.report_type === "monthly_summary") {
    const topCategory = summary.top_category;
    if (!topCategory) {
      return renderReportNote("No spending recorded for this summary.");
    }

    return `
      <div class="report-highlight">
        <small>Top category</small>
        <strong>${escapeHtml(topCategory.category_name || `Category ${topCategory.category_id}`)}</strong>
        <span>${money(topCategory.total_amount)}</span>
      </div>
    `;
  }

  const budgetRows = budgets.slice(0, 3);
  return renderReportMiniList(budgetRows, "No budgets matched this range.", (budget) => `
    <li>
      <span>${escapeHtml(budget.category_name || `Category ${budget.category_id}`)} ${budget.over_budget ? "(over)" : "(ok)"}</span>
      <strong>${money(budget.remaining)}</strong>
    </li>
  `);
}

function renderReportDetails(item, recent) {
  if (item.report_type === "date_range") {
    return renderReportMiniList(recent.slice(0, 5), "No transactions in this range.", (expense) => `
      <li>
        <span>${escapeHtml(expense.expense_date)} - ${escapeHtml(expense.category_name || `Category ${expense.category_id}`)}</span>
        <strong>${money(expense.amount)}</strong>
      </li>
    `);
  }

  if (item.report_type === "by_category") {
    return renderReportNote("Focused on category totals. Use Detailed date range when you need transaction-level lines.");
  }

  return renderReportNote("High-level summary for the selected period.");
}

function renderReportRecords(items) {
  renderWorkspaceTable(
    reportsBody,
    items,
    "No reports loaded yet.",
    4,
    (item) => {
      const summary = item.summary || {};
      const categories = summary.category_breakdown || [];
      const recent = item.views?.recent_transactions || [];
      const budgets = item.views?.budget_vs_actual?.items || [];
      const overBudgetCount = budgets.filter((budget) => budget.over_budget).length;
      const topCategory = summary.top_category;
      const summaryItems = item.report_type === "by_category"
        ? [
            { value: money(summary.total_amount || 0), label: "Total spent" },
            { value: String(categories.length), label: "Categories" },
            { value: String(summary.expense_count || 0), label: "Transactions" },
            { value: topCategory ? money(topCategory.total_amount) : "0.00", label: "Top category" },
          ]
        : [
            { value: money(summary.total_amount || 0), label: "Total spent" },
            { value: String(summary.expense_count || 0), label: "Transactions" },
            { value: money(summary.average_expense || 0), label: "Average" },
            { value: String(overBudgetCount), label: "Over budget" },
          ];

      return `
        <tr>
          <td>
            <strong>${escapeHtml(reportTypeLabel(item.report_type))}</strong>
            <span class="report-meta">#${escapeHtml(item.report_id)} - ${escapeHtml(item.date_from)} to ${escapeHtml(item.date_to)}</span>
            <span class="report-meta">Created ${escapeHtml(formatDateTime(item.generated_at))}</span>
          </td>
          <td>
            ${renderReportSummaryGrid(summaryItems)}
          </td>
          <td>
            ${renderReportBreakdown(item, summary, categories.slice(0, 5), budgets)}
          </td>
          <td>
            ${renderReportDetails(item, recent)}
          </td>
        </tr>
      `;
    },
  );
}

function renderCategoryRecords(items) {
  renderWorkspaceTable(
    categoriesBody,
    items,
    "No categories loaded yet.",
    5,
    (item) => {
      const canManage = Boolean(
        state.session?.user_id
        && !item.is_default
        && Number(item.created_by) === Number(state.session.user_id),
      );

      return `
        <tr>
          <td>${item.category_id}</td>
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.description || "-")}</td>
          <td><span class="pill ${item.is_default ? "success" : ""}">${item.is_default ? "Yes" : "No"}</span></td>
          <td>
            ${canManage ? `
              <div class="row-actions">
                <button class="admin-btn" type="button" data-record-action="edit-category" data-category-id="${escapeHtml(item.category_id)}">Edit</button>
                <button class="admin-btn admin-btn-danger" type="button" data-record-action="delete-category" data-category-id="${escapeHtml(item.category_id)}">Delete</button>
              </div>
            ` : '<span class="muted-cell">System</span>'}
          </td>
        </tr>
      `;
    },
  );
}

function updateSessionView() {
  baseUrlInput.value = state.baseUrl;

  if (!state.session) {
    sessionBadge.textContent = "Guest mode";
    logoutButton.classList.add("hidden");
    workspaceSection.classList.remove("hidden");
    adminPanel.classList.add("hidden");
    categoryStudio.classList.add("hidden");
    adminPanelButton.classList.add("hidden");
    dashboardHeading.textContent = "Sign in to unlock your overview";
    dashboardSubtext.textContent = "Use the login form on the left. The workspace controls appear after sign in.";
    currentRole.textContent = "guest";
    currentUserId.textContent = "User ID: -";
    monthlyTotalEl.textContent = "0.00";
    monthlyCountEl.textContent = "No transactions loaded yet";
    transactionCountEl.textContent = "0";
    topCategoryEl.textContent = "-";
    topCategoryValueEl.textContent = "Log in to load insights";
    chartTotalEl.textContent = "0.00";
    renderPieChart([]);
    renderBudgetRows([]);
    renderRecentRows([]);
    renderUsers([]);
    renderExpensesRows([]);
    renderBudgetRecords([]);
    renderReportRecords([]);
    renderCategoryRecords([]);
    populateCategorySelects([]);
    updateWorkspaceNavState();
    setWorkspaceNavMessage("Sign in to use the workspace shortcuts.");
    return;
  }

  const role = state.session.role || "user";
  sessionBadge.textContent = `${role} - ${state.session.username || state.session.email}`;
  logoutButton.classList.remove("hidden");
  workspaceSection.classList.remove("hidden");
  dashboardHeading.textContent = `Welcome back, ${state.session.username || state.session.email}`;
  dashboardSubtext.textContent = role === "premium"
    ? "Premium controls are unlocked. You can add expenses, budgets, reports, and categories."
    : role === "admin"
      ? "Admin controls are unlocked below. Category creation stays premium-only."
      : "Use the workspace controls below to add expenses, budgets, and reports.";
  currentRole.textContent = role;
  currentUserId.textContent = `User ID: ${state.session.user_id || "-"}`;

  categoryStudio.classList.toggle("hidden", role !== "premium" && role !== "admin");
  updateWorkspaceNavState();

  // Show admin button only for admins
  if (adminPanelButton) {
    adminPanelButton.classList.toggle("hidden", role !== "admin");
  }

  if (role === "admin") {
    adminPanel.classList.remove("hidden");
  } else {
    adminPanel.classList.add("hidden");
  }
}

async function refreshSessionRole() {
  if (!state.session?.user_id) {
    throw new Error("Log in first.");
  }

  const result = await request(`/user/${state.session.user_id}`);
  if (!result.user) {
    throw new Error("Could not verify admin session.");
  }

  state.session = {
    ...state.session,
    ...result.user,
  };
  localStorage.setItem("financer_session", JSON.stringify(state.session));
  updateSessionView();

  if (state.session.role !== "admin") {
    throw new Error(`Current session is ${state.session.role || "not admin"}. Log in with the admin account, then try again.`);
  }

  return state.session.user_id;
}

async function loadCategoriesList() {
  try {
    const url = state.session?.user_id ? `/categories?user_id=${state.session.user_id}` : "/categories";
    const items = await request(url);
    state.categories = items || [];
    populateCategorySelects(items || []);
    renderCategoryRecords(items || []);
    setCategoryMessage(`${(items || []).length} category${(items || []).length === 1 ? "" : "s"} loaded.`);
    return items || [];
  } catch (error) {
    populateCategorySelects([]);
    state.categories = [];
    renderCategoryRecords([]);
    setCategoryMessage(error.message, true);
    return [];
  }
}

async function loadExpensesList() {
  if (!state.session?.user_id) {
    state.expenses = [];
    renderExpensesRows([]);
    setExpenseMessage("Log in to load expenses.", true);
    return [];
  }

  try {
    const items = await request(`/expenses/${state.session.user_id}`);
    state.expenses = items || [];
    renderExpensesRows(items || []);
    setExpenseMessage(`${(items || []).length} expense${(items || []).length === 1 ? "" : "s"} loaded.`);
    return items || [];
  } catch (error) {
    state.expenses = [];
    setExpenseMessage(error.message, true);
    return [];
  }
}

async function loadBudgetRecords() {
  if (!state.session?.user_id) {
    state.budgets = [];
    renderBudgetRecords([]);
    setBudgetMessage("Log in to load budgets.", true);
    return [];
  }

  try {
    const items = await request(`/budgets/${state.session.user_id}`);
    state.budgets = items || [];
    renderBudgetRecords(items || []);
    setBudgetMessage(`${(items || []).length} budget${(items || []).length === 1 ? "" : "s"} loaded.`);
    return items || [];
  } catch (error) {
    state.budgets = [];
    setBudgetMessage(error.message, true);
    return [];
  }
}

async function loadReportRecords() {
  if (!state.session?.user_id) {
    renderReportRecords([]);
    setReportMessage("Log in to load reports.", true);
    return [];
  }

  try {
    const items = await request(`/reports/${state.session.user_id}`);
    renderReportRecords(items || []);
    setReportMessage(`${(items || []).length} report${(items || []).length === 1 ? "" : "s"} loaded.`);
    return items || [];
  } catch (error) {
    setReportMessage(error.message, true);
    return [];
  }
}

async function loadDashboard() {
  if (!state.session?.user_id) {
    setAuthMessage("Log in first to load dashboard data.", true);
    return;
  }

  const failures = [];
  const loadPart = async (label, callback) => {
    try {
      await callback();
    } catch (error) {
      failures.push(`${label}: ${error.message}`);
    }
  };

  await loadPart("Monthly total", async () => {
    const monthlyTotal = await request(`/insights/total-monthly/${state.session.user_id}`);
    monthlyTotalEl.textContent = money(monthlyTotal.spent_monthly);
    monthlyCountEl.textContent = `${monthlyTotal.expense_count} transaction${monthlyTotal.expense_count === 1 ? "" : "s"} this month`;
    transactionCountEl.textContent = String(monthlyTotal.expense_count || 0);
  });

  await loadPart("Spent by category", async () => {
    const spentByCategory = await request(`/insights/spent-by-category/${state.session.user_id}`);
    renderPieChart(spentByCategory.items || []);
  });

  await loadPart("Budget vs actual", async () => {
    const budgetVsActual = await request(`/insights/budget-vs-actual/${state.session.user_id}`);
    renderBudgetRows(budgetVsActual.items || []);
  });

  await loadPart("Recent transactions", async () => {
    const recentTransactions = await request(`/insights/recent-transactions/${state.session.user_id}`);
    renderRecentRows(recentTransactions.items || []);
  });

  try {
    await loadCategoriesList();
    await loadExpensesList();
    await loadBudgetRecords();
    await loadReportRecords();

    if (failures.length) {
      setAuthMessage(`Dashboard partially loaded. ${failures.join(" | ")}`, true);
      return;
    }

    setAuthMessage(`Dashboard loaded for ${state.session.username || state.session.email}.`);
  } catch (error) {
    setAuthMessage(error.message, true);
  }
}

async function loadUsers() {
  try {
    const adminUserId = await refreshSessionRole();
    const users = await request(`/admin/users?admin_user_id=${adminUserId}`);
    renderUsers(users || []);
    setAdminMessage("Users loaded.");
  } catch (error) {
    setAdminMessage(error.message, true);
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(loginForm);

  try {
    const result = await request("/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    saveSession(result.user);
    updateSessionView();
    await loadDashboard();

    if ((state.session?.role || "") === "admin") {
      await loadUsers();
    }
  } catch (error) {
    setAuthMessage(error.message, true);
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(registerForm);

  try {
    await request("/register", {
      method: "POST",
      body: JSON.stringify({
        username: formData.get("username"),
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    setAuthTab("login");
    registerForm.reset();
    setAuthMessage("Account created. Now sign in with the same email and password.");
  } catch (error) {
    setAuthMessage(error.message, true);
  }
});

authTabButtons.forEach((button) => {
  button.addEventListener("click", () => setAuthTab(button.dataset.authTab));
});

logoutButton.addEventListener("click", () => {
  clearSession();
  updateSessionView();
  setAuthMessage("Logged out.");
});

// Sync role from backend
async function syncRoleFromBackend() {
  if (!state.session?.user_id) {
    setAuthMessage("Log in first to sync role.", true);
    return;
  }

  try {
    const response = await fetch(`${getBaseUrl()}/user/${state.session.user_id}`);
    const result = await response.json();

    if (response.ok && result.user) {
      state.session.role = result.user.role;
      state.session.username = result.user.username || state.session.username;
      state.session.email = result.user.email || state.session.email;
      localStorage.setItem("financer_session", JSON.stringify(state.session));
      updateSessionView();
      await loadDashboard();
      setAuthMessage("Role synced from database.");
    } else {
      setAuthMessage("Failed to sync role: " + (result.message || result.error), true);
    }
  } catch (error) {
    setAuthMessage("Error syncing role: " + error.message, true);
  }
}

const syncRoleButton = document.getElementById("syncRoleButton");
const adminPanelButton = document.getElementById("adminPanelButton");

syncRoleButton.addEventListener("click", syncRoleFromBackend);

adminPanelButton.addEventListener("click", () => {
  window.location.href = "admin.html";
});

refreshButton.addEventListener("click", loadDashboard);
loadUsersButton.addEventListener("click", loadUsers);
loadCategoriesButton.addEventListener("click", loadCategoriesList);
loadExpensesButton.addEventListener("click", loadExpensesList);
loadBudgetsButton.addEventListener("click", loadBudgetRecords);
loadReportsButton.addEventListener("click", loadReportRecords);
workspaceNavButtons.forEach((button) => {
  button.addEventListener("click", () => openWorkspaceTarget(button.dataset.workspaceTarget));
});

expensesBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-record-action]");
  if (!button) return;

  const item = state.expenses.find((expense) => Number(expense.expense_id) === Number(button.dataset.expenseId));
  if (!item) {
    setExpenseMessage("Load expenses again before editing this record.", true);
    return;
  }

  openRecordModal({
    type: "expense",
    mode: button.dataset.recordAction.startsWith("delete") ? "delete" : "edit",
    item,
  });
});

budgetsBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-record-action]");
  if (!button) return;

  const item = state.budgets.find((budget) => Number(budget.budget_id) === Number(button.dataset.budgetId));
  if (!item) {
    setBudgetMessage("Load budgets again before editing this record.", true);
    return;
  }

  openRecordModal({
    type: "budget",
    mode: button.dataset.recordAction.startsWith("delete") ? "delete" : "edit",
    item,
  });
});

categoriesBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-record-action]");
  if (!button) return;

  const item = state.categories.find((category) => Number(category.category_id) === Number(button.dataset.categoryId));
  if (!item) {
    setCategoryMessage("Load categories again before editing this record.", true);
    return;
  }

  if (item.is_default || Number(item.created_by) !== Number(state.session?.user_id)) {
    setCategoryMessage("System categories are read-only here.", true);
    return;
  }

  openRecordModal({
    type: "category",
    mode: button.dataset.recordAction.startsWith("delete") ? "delete" : "edit",
    item,
  });
});

recordModalClose.addEventListener("click", closeRecordModal);
recordModal.addEventListener("click", (event) => {
  if (event.target === recordModal || event.target.closest("[data-modal-close]")) {
    closeRecordModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !recordModal.classList.contains("hidden")) {
    closeRecordModal();
  }
});

recordModalForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!state.session?.user_id || !state.activeModal) {
    setModalMessage("Log in first.", true);
    return;
  }

  const { type, mode, item } = state.activeModal;
  const id = type === "expense" ? item.expense_id : type === "budget" ? item.budget_id : item.category_id;
  const path = type === "expense" ? `/update-expense/${id}` : type === "budget" ? `/update-budget/${id}` : `/update-category/${id}`;
  const deletePath = type === "expense" ? `/delete-expense/${id}` : type === "budget" ? `/delete-budget/${id}` : `/delete-category/${id}`;

  try {
    if (mode === "delete") {
      await request(deletePath, {
        method: "DELETE",
        body: JSON.stringify({ user_id: state.session.user_id }),
      });
    } else {
      await request(path, {
        method: "PUT",
        body: JSON.stringify(buildFormPayload(recordModalForm, { user_id: state.session.user_id })),
      });
    }

    closeRecordModal();
    await loadDashboard();
    if (type === "expense") {
      setExpenseMessage(`Expense ${mode === "delete" ? "deleted" : "updated"}.`);
    } else if (type === "budget") {
      setBudgetMessage(`Budget ${mode === "delete" ? "deleted" : "updated"}.`);
    } else {
      setCategoryMessage(`Category ${mode === "delete" ? "deleted" : "updated"}.`);
    }
  } catch (error) {
    setModalMessage(error.message, true);
  }
});

expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!state.session?.user_id) {
    setExpenseMessage("Log in first.", true);
    return;
  }

  try {
    await request("/add-expense", {
      method: "POST",
      body: JSON.stringify(buildFormPayload(expenseForm, { user_id: state.session.user_id })),
    });

    expenseForm.reset();
    setDefaultFormDates();
    await loadDashboard();
    setExpenseMessage("Expense added.");
  } catch (error) {
    setExpenseMessage(error.message, true);
  }
});

budgetForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!state.session?.user_id) {
    setBudgetMessage("Log in first.", true);
    return;
  }

  try {
    await request("/add-budget", {
      method: "POST",
      body: JSON.stringify(buildFormPayload(budgetForm, { user_id: state.session.user_id })),
    });

    budgetForm.reset();
    setDefaultFormDates();
    await loadDashboard();
    setBudgetMessage("Budget added.");
  } catch (error) {
    setBudgetMessage(error.message, true);
  }
});

reportForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!state.session?.user_id) {
    setReportMessage("Log in first.", true);
    return;
  }

  try {
    await request("/generate-report", {
      method: "POST",
      body: JSON.stringify(buildFormPayload(reportForm, { user_id: state.session.user_id })),
    });

    reportForm.reset();
    setDefaultFormDates();
    await loadDashboard();
    setReportMessage("Report generated.");
  } catch (error) {
    setReportMessage(error.message, true);
  }
});

categoryForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!state.session?.user_id) {
    setCategoryMessage("Log in first.", true);
    return;
  }

  if ((state.session?.role || "") !== "premium" && (state.session?.role || "") !== "admin") {
    setCategoryMessage("Premium access required to add categories.", true);
    return;
  }

  try {
    await request("/add-category", {
      method: "POST",
      body: JSON.stringify(buildFormPayload(categoryForm, { user_id: state.session.user_id })),
    });

    categoryForm.reset();
    await loadDashboard();
    setCategoryMessage("Category added.");
  } catch (error) {
    setCategoryMessage(error.message, true);
  }
});

roleForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(roleForm);
  const userId = formData.get("user_id");

  try {
    const adminUserId = await refreshSessionRole();
    await request(`/admin/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({
        admin_user_id: adminUserId,
        role: formData.get("role"),
      }),
    });

    setAdminMessage("Role updated.");
    await loadUsers();
  } catch (error) {
    setAdminMessage(error.message, true);
  }
});

deleteUserForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(deleteUserForm);
  const userId = formData.get("user_id");

  try {
    const adminUserId = await refreshSessionRole();
    await request(`/admin/users/${userId}`, {
      method: "DELETE",
      body: JSON.stringify({
        admin_user_id: adminUserId,
      }),
    });

    setAdminMessage("User deleted.");
    await loadUsers();
  } catch (error) {
    setAdminMessage(error.message, true);
  }
});

loadCategoriesList();

saveBaseUrlButton.addEventListener("click", () => {
  saveBaseUrl(baseUrlInput.value.trim());
  setAuthMessage("Backend URL saved.");
});

baseUrlInput.addEventListener("change", () => {
  saveBaseUrl(baseUrlInput.value.trim());
  setAuthMessage("Backend URL saved.");
});

function setDefaultFormDates() {
  const today = new Date().toISOString().slice(0, 10);
  const monthStart = `${today.slice(0, 8)}01`;

  const expenseDate = expenseForm.elements.expense_date;
  const budgetStartDate = budgetForm.elements.start_date;
  const reportDateFrom = reportForm.elements.date_from;
  const reportDateTo = reportForm.elements.date_to;

  if (expenseDate && !expenseDate.value) expenseDate.value = today;
  if (budgetStartDate && !budgetStartDate.value) budgetStartDate.value = monthStart;
  if (reportDateFrom && !reportDateFrom.value) reportDateFrom.value = monthStart;
  if (reportDateTo && !reportDateTo.value) reportDateTo.value = today;
}

saveBaseUrl(state.baseUrl);
setDefaultFormDates();
updateSessionView();

if (state.session?.user_id) {
  loadDashboard().then(() => {
    if ((state.session?.role || "") === "admin") {
      loadUsers();
    }
  });
}
