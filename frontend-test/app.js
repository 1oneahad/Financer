const baseUrlInput = document.getElementById("baseUrl");
const saveBaseUrlButton = document.getElementById("saveBaseUrl");

const outputMap = {
  auth: document.getElementById("authOutput"),
  categories: document.getElementById("categoriesOutput"),
  expenses: document.getElementById("expensesOutput"),
  budgets: document.getElementById("budgetsOutput"),
  reports: document.getElementById("reportsOutput"),
  users: document.getElementById("usersOutput"),
  admin: document.getElementById("adminOutput"),
};

const currentUser = {
  userId: localStorage.getItem("financer_user_id") || "",
  role: localStorage.getItem("financer_role") || "",
  email: localStorage.getItem("financer_email") || "",
};

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
  const response = await fetch(`${getBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
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

function syncCurrentUser(user) {
  currentUser.userId = user?.user_id || "";
  currentUser.role = user?.role || "";
  currentUser.email = user?.email || "";

  localStorage.setItem("financer_user_id", currentUser.userId);
  localStorage.setItem("financer_role", currentUser.role);
  localStorage.setItem("financer_email", currentUser.email);
}

function fillLoginIfPossible() {
  const loginForm = document.getElementById("loginForm");
  if (!loginForm) return;
  loginForm.elements.email.value = currentUser.email || "";
}

saveBaseUrlButton.addEventListener("click", () => {
  setBaseUrl(baseUrlInput.value.trim() || "http://127.0.0.1:5000");
  writeOutput("auth", { message: "Base URL saved", baseUrl: getBaseUrl() });
});

baseUrlInput.value = localStorage.getItem("financer_base_url") || "http://127.0.0.1:5000";
fillLoginIfPossible();

// Auth

document.getElementById("registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;

  try {
    const result = await api("/register", {
      method: "POST",
      body: JSON.stringify(getFormData(form)),
    });
    writeOutput("auth", result);
  } catch (error) {
    writeOutput("auth", error);
  }
});

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;

  try {
    const result = await api("/login", {
      method: "POST",
      body: JSON.stringify(getFormData(form)),
    });
    syncCurrentUser(result.user);
    fillLoginIfPossible();
    writeOutput("auth", {
      ...result,
      note: `Logged in as ${currentUser.email || "user"} (${currentUser.role || "no role"})`,
    });
  } catch (error) {
    writeOutput("auth", error);
  }
});

// Categories

document.getElementById("addCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/add-category", {
      method: "POST",
      body: JSON.stringify(getFormData(event.currentTarget)),
    });
    writeOutput("categories", result);
  } catch (error) {
    writeOutput("categories", error);
  }
});

document.getElementById("loadCategories").addEventListener("click", async () => {
  try {
    const result = await api("/categories");
    writeOutput("categories", result);
  } catch (error) {
    writeOutput("categories", error);
  }
});

document.getElementById("updateCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const categoryId = data.category_id;
  delete data.category_id;

  try {
    const result = await api(`/update-category/${categoryId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    writeOutput("categories", result);
  } catch (error) {
    writeOutput("categories", error);
  }
});

document.getElementById("deleteCategoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const categoryId = data.category_id;
  delete data.category_id;

  try {
    const result = await api(`/delete-category/${categoryId}`, {
      method: "DELETE",
      body: JSON.stringify(data),
    });
    writeOutput("categories", result);
  } catch (error) {
    writeOutput("categories", error);
  }
});

// Expenses

document.getElementById("addExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/add-expense", {
      method: "POST",
      body: JSON.stringify(getFormData(event.currentTarget)),
    });
    writeOutput("expenses", result);
  } catch (error) {
    writeOutput("expenses", error);
  }
});

document.getElementById("loadExpensesForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    const result = await api(`/expenses/${user_id}`);
    writeOutput("expenses", result);
  } catch (error) {
    writeOutput("expenses", error);
  }
});

document.getElementById("updateExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const expenseId = data.expense_id;
  delete data.expense_id;

  try {
    const result = await api(`/update-expense/${expenseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    writeOutput("expenses", result);
  } catch (error) {
    writeOutput("expenses", error);
  }
});

document.getElementById("deleteExpenseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const expenseId = data.expense_id;
  delete data.expense_id;

  try {
    const result = await api(`/delete-expense/${expenseId}`, {
      method: "DELETE",
      body: JSON.stringify(data),
    });
    writeOutput("expenses", result);
  } catch (error) {
    writeOutput("expenses", error);
  }
});

// Budgets

document.getElementById("addBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/add-budget", {
      method: "POST",
      body: JSON.stringify(getFormData(event.currentTarget)),
    });
    writeOutput("budgets", result);
  } catch (error) {
    writeOutput("budgets", error);
  }
});

document.getElementById("loadBudgetsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    const result = await api(`/budgets/${user_id}`);
    writeOutput("budgets", result);
  } catch (error) {
    writeOutput("budgets", error);
  }
});

document.getElementById("updateBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const budgetId = data.budget_id;
  delete data.budget_id;

  try {
    const result = await api(`/update-budget/${budgetId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    writeOutput("budgets", result);
  } catch (error) {
    writeOutput("budgets", error);
  }
});

document.getElementById("deleteBudgetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const budgetId = data.budget_id;
  delete data.budget_id;

  try {
    const result = await api(`/delete-budget/${budgetId}`, {
      method: "DELETE",
      body: JSON.stringify(data),
    });
    writeOutput("budgets", result);
  } catch (error) {
    writeOutput("budgets", error);
  }
});

// Reports

document.getElementById("generateReportForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/generate-report", {
      method: "POST",
      body: JSON.stringify(getFormData(event.currentTarget)),
    });
    writeOutput("reports", result);
  } catch (error) {
    writeOutput("reports", error);
  }
});

document.getElementById("loadReportsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { user_id } = getFormData(event.currentTarget);
  try {
    const result = await api(`/reports/${user_id}`);
    writeOutput("reports", result);
  } catch (error) {
    writeOutput("reports", error);
  }
});

// Admin

document.getElementById("listUsersForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { admin_user_id } = getFormData(event.currentTarget);
  try {
    const result = await api(`/admin/users?admin_user_id=${admin_user_id}`);
    writeOutput("users", result);
  } catch (error) {
    writeOutput("users", error);
  }
});

document.getElementById("updateRoleForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const userId = data.user_id;
  delete data.user_id;

  try {
    const result = await api(`/admin/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    writeOutput("admin", result);
  } catch (error) {
    writeOutput("admin", error);
  }
});

document.getElementById("deleteUserForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const userId = data.user_id;
  delete data.user_id;

  try {
    const result = await api(`/admin/users/${userId}`, {
      method: "DELETE",
      body: JSON.stringify(data),
    });
    writeOutput("admin", result);
  } catch (error) {
    writeOutput("admin", error);
  }
});
