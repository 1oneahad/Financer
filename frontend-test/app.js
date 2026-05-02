const baseUrlInput = document.getElementById("baseUrl");
const saveBaseUrlButton = document.getElementById("saveBaseUrl");

const outputMap = {
  auth: document.getElementById("authOutput"),
  dashboard: document.getElementById("dashboardOutput"),
  categories: document.getElementById("categoriesOutput"),
  expenses: document.getElementById("expensesOutput"),
  budgets: document.getElementById("budgetsOutput"),
  reports: document.getElementById("reportsOutput"),
  users: document.getElementById("usersOutput"),
  admin: document.getElementById("adminOutput"),
  adminResource: document.getElementById("adminResourceOutput"),
};

const currentUser = {
  userId: localStorage.getItem("financer_user_id") || "",
  role: localStorage.getItem("financer_role") || "",
  email: localStorage.getItem("financer_email") || "",
};

const sessionState = document.getElementById("sessionState");

function getBaseUrl() {
  return baseUrlInput.value.trim().replace(/\/$/, "");
}

function setBaseUrl(value) {
  baseUrlInput.value = value;
  localStorage.setItem("financer_base_url", value);
}

function writeOutput(key, value) {
  outputMap[key].textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function describeRequest(method, path, body) {
  const request = {
    method,
    url: `${getBaseUrl()}${path}`,
  };

  if (body && Object.keys(body).length) {
    request.body = {
      ...body,
      ...(body.password ? { password: "********" } : {}),
    };
  }

  return request;
}

function normalizeError(error) {
  if (!error) return null;
  if (error instanceof Error) {
    return { message: error.message };
  }
  return error;
}

function writeExchange(key, request, response, error = null) {
  writeOutput(key, {
    request,
    response: error ? undefined : response,
    error: error ? normalizeError(error) : undefined,
  });
}

function getFormData(form) {
  const data = {};
  const formData = new FormData(form);

  for (const [key, value] of formData.entries()) {
    if (key === "is_default") {
      data[key] = form.elements[key].checked;
      continue;
    }

    if (value === "") continue;

    if (["user_id", "category_id", "expense_id", "budget_id", "report_id", "admin_user_id"].includes(key)) {
      data[key] = Number(value);
    } else if (["amount", "amount_limit"].includes(key)) {
      data[key] = Number(value);
    } else {
      data[key] = value;
    }
  }

  if (form.elements["is_default"]) {
    data.is_default = form.elements["is_default"].checked;
  }

  return data;
}

async function api(path, options = {}) {
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
  let payload = text;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    // keep text
  }

  if (!response.ok) {
    throw payload;
  }

  return payload;
}

async function runApi(key, method, path, body) {
  const options = { method };
  if (body && Object.keys(body).length) {
    options.body = JSON.stringify(body);
  }

  const requestInfo = describeRequest(method, path, body);

  try {
    const result = await api(path, options);
    writeExchange(key, requestInfo, result);
    return result;
  } catch (error) {
    writeExchange(key, requestInfo, null, error);
    throw error;
  }
}

function syncCurrentUser(user) {
  currentUser.userId = user?.user_id || "";
  currentUser.role = user?.role || "";
  currentUser.email = user?.email || "";

  localStorage.setItem("financer_user_id", currentUser.userId);
  localStorage.setItem("financer_role", currentUser.role);
  localStorage.setItem("financer_email", currentUser.email);
  renderSessionState();
  fillUserInputs();
}

function fillLoginIfPossible() {
  const loginForm = document.getElementById("loginForm");
  if (!loginForm) return;
  loginForm.elements.email.value = currentUser.email || "";
}

function fillUserInputs() {
  if (!currentUser.userId) return;

  document.querySelectorAll('input[name="user_id"]').forEach((input) => {
    if (!input.value) input.value = currentUser.userId;
  });

  document.querySelectorAll('input[name="admin_user_id"]').forEach((input) => {
    if (!input.value && currentUser.role === "admin") input.value = currentUser.userId;
  });
}

function renderSessionState() {
  const label = currentUser.userId
    ? `Session: user #${currentUser.userId} | ${currentUser.email || "no email"} | ${currentUser.role || "no role"}`
    : "No active session";
  sessionState.textContent = label;
}

saveBaseUrlButton.addEventListener("click", () => {
  setBaseUrl(baseUrlInput.value.trim() || "http://127.0.0.1:5000");
  writeOutput("auth", { message: "Base URL saved", baseUrl: getBaseUrl() });
});

baseUrlInput.value = localStorage.getItem("financer_base_url") || "http://127.0.0.1:5000";
fillLoginIfPossible();
fillUserInputs();
renderSessionState();

// Auth

document.getElementById("registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;

  try {
    await runApi("auth", "POST", "/register", getFormData(form));
  } catch (error) {
    // runApi already printed the request/response exchange.
  }
});

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;

  try {
    const result = await runApi("auth", "POST", "/login", getFormData(form));
    syncCurrentUser(result.user);
    fillLoginIfPossible();
    writeOutput("auth", {
      request: describeRequest("POST", "/login", getFormData(form)),
      response: result,
      note: `Logged in as ${currentUser.email || "user"} (${currentUser.role || "no role"})`,
    });
  } catch (error) {
    // runApi already printed the request/response exchange.
  }
});

// Dashboard data used by the main website

document.getElementById("syncUserForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);

  try {
    const result = await runApi("dashboard", "GET", `/user/${user_id}`);
    syncCurrentUser(result.user);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("dashboardCallsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  const calls = [
    ["monthlyTotal", `/insights/total-monthly/${user_id}`],
    ["spentByCategory", `/insights/spent-by-category/${user_id}`],
    ["budgetVsActual", `/insights/budget-vs-actual/${user_id}`],
    ["recentTransactions", `/insights/recent-transactions/${user_id}`],
    ["categoriesForUser", `/categories?user_id=${user_id}`],
    ["expenses", `/expenses/${user_id}`],
    ["budgets", `/budgets/${user_id}`],
    ["reports", `/reports/${user_id}`],
  ];

  const results = {};
  for (const [name, path] of calls) {
    try {
      results[name] = {
        request: describeRequest("GET", path),
        response: await api(path),
      };
    } catch (error) {
      results[name] = {
        request: describeRequest("GET", path),
        error,
      };
    }
  }

  writeOutput("dashboard", results);
});

// Categories

document.getElementById("addCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await runApi("categories", "POST", "/add-category", getFormData(event.currentTarget));
  } catch (error) {
    // output already handled
  }
});

document.getElementById("loadCategoriesForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  const path = user_id ? `/categories?user_id=${user_id}` : "/categories";

  try {
    await runApi("categories", "GET", path);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("updateCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const categoryId = data.category_id;
  delete data.category_id;

  try {
    await runApi("categories", "PUT", `/update-category/${categoryId}`, data);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("deleteCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const categoryId = data.category_id;
  delete data.category_id;

  try {
    await runApi("categories", "DELETE", `/delete-category/${categoryId}`, data);
  } catch (error) {
    // output already handled
  }
});

// Expenses

document.getElementById("addExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await runApi("expenses", "POST", "/add-expense", getFormData(event.currentTarget));
  } catch (error) {
    // output already handled
  }
});

document.getElementById("loadExpensesForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    await runApi("expenses", "GET", `/expenses/${user_id}`);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("getExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { expense_id } = getFormData(event.currentTarget);

  try {
    await runApi("expenses", "GET", `/expense/${expense_id}`);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("updateExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const expenseId = data.expense_id;
  delete data.expense_id;

  try {
    await runApi("expenses", "PUT", `/update-expense/${expenseId}`, data);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("deleteExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const expenseId = data.expense_id;
  delete data.expense_id;

  try {
    await runApi("expenses", "DELETE", `/delete-expense/${expenseId}`, data);
  } catch (error) {
    // output already handled
  }
});

// Budgets

document.getElementById("addBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await runApi("budgets", "POST", "/add-budget", getFormData(event.currentTarget));
  } catch (error) {
    // output already handled
  }
});

document.getElementById("loadBudgetsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    await runApi("budgets", "GET", `/budgets/${user_id}`);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("updateBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const budgetId = data.budget_id;
  delete data.budget_id;

  try {
    await runApi("budgets", "PUT", `/update-budget/${budgetId}`, data);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("deleteBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const budgetId = data.budget_id;
  delete data.budget_id;

  try {
    await runApi("budgets", "DELETE", `/delete-budget/${budgetId}`, data);
  } catch (error) {
    // output already handled
  }
});

// Reports

document.getElementById("generateReportForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await runApi("reports", "POST", "/generate-report", getFormData(event.currentTarget));
  } catch (error) {
    // output already handled
  }
});

document.getElementById("loadReportsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    await runApi("reports", "GET", `/reports/${user_id}`);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("deleteReportForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const reportId = data.report_id;
  delete data.report_id;

  try {
    await runApi("reports", "DELETE", `/delete-report/${reportId}`, data);
  } catch (error) {
    // output already handled
  }
});

// Admin

document.getElementById("listUsersForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { admin_user_id } = getFormData(event.currentTarget);
  try {
    await runApi("users", "GET", `/admin/users?admin_user_id=${admin_user_id}`);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("updateRoleForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const userId = data.user_id;
  delete data.user_id;

  try {
    await runApi("admin", "PUT", `/admin/users/${userId}/role`, data);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("deleteUserForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const userId = data.user_id;
  delete data.user_id;

  try {
    await runApi("admin", "DELETE", `/admin/users/${userId}`, data);
  } catch (error) {
    // output already handled
  }
});

document.getElementById("adminResourceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const query = new URLSearchParams({ admin_user_id: data.admin_user_id });
  if (data.resource === "audit-logs" && data.limit) {
    query.set("limit", data.limit);
  }

  try {
    await runApi("adminResource", "GET", `/admin/${data.resource}?${query.toString()}`);
  } catch (error) {
    // output already handled
  }
});
