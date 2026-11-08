const message = document.getElementById("message");
const customerForm = document.getElementById("customer-form");
const productForm = document.getElementById("product-form");
const orderRows = document.getElementById("order-rows");

let customers = [];
let products = [];
let currentRole = null;

function applyRole(role) {
  currentRole = role;
  document.getElementById("customer-form").classList.toggle("hidden", role !== "admin");
  document.getElementById("product-form").classList.toggle("hidden", role !== "admin");
  document.getElementById("csv-form").classList.toggle("hidden", role !== "admin");
  document.querySelectorAll('[data-page="reports"]').forEach((tab) => {
    tab.classList.toggle("hidden", role !== "admin");
  });
  if (role !== "admin" && document.querySelector('[data-page="reports"]').classList.contains("active")) {
    document.querySelector('[data-page="customers"]').click();
  }
}

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.detail || "Request failed");
  return result;
}

async function withBusy(button, action) {
  button.disabled = true;
  try {
    await action();
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".page").forEach((page) => page.classList.add("hidden"));
    button.classList.add("active");
    document.getElementById(`${button.dataset.page}-page`).classList.remove("hidden");
    showMessage("");
    if (button.dataset.page === "orders") loadOrders();
  });
});

async function loadCustomers() {
  customers = await api("/api/customers");
  document.getElementById("customers-table").innerHTML = customers.map((customer) => `
    <tr>
      <td>${escapeHtml(customer.name)}</td><td>${escapeHtml(customer.email)}</td>
      <td>${escapeHtml(customer.mobile)}</td><td>${escapeHtml(customer.city)}</td>
      <td>${customer.is_active ? "Active" : "Inactive"}</td>
      <td class="actions">${currentRole === "admin" ? `
        <button class="secondary" onclick="editCustomer(${customer.id})">Edit</button>
        <button class="danger" onclick="deleteCustomer(${customer.id})">Delete</button>` : ""}
      </td>
    </tr>`).join("");
  document.getElementById("order-customer").innerHTML = customers
    .filter((customer) => customer.is_active)
    .map((customer) => `<option value="${customer.id}">${escapeHtml(customer.name)}</option>`)
    .join("");
}

customerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = customerForm.querySelector("button[type=submit]");
  await withBusy(button, async () => {
    const form = new FormData(customerForm);
    const data = {
      name: form.get("name"), email: form.get("email"), mobile: form.get("mobile"),
      city: form.get("city"), is_active: form.get("is_active") === "on",
    };
    const id = customerForm.dataset.id;
    await api(id ? `/api/customers/${id}` : "/api/customers", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    customerForm.reset();
    customerForm.elements.is_active.checked = true;
    customerForm.dataset.id = "";
    button.textContent = "Add customer";
    document.getElementById("cancel-customer-edit").classList.add("hidden");
    await loadCustomers();
    showMessage(id ? "Customer updated." : "Customer added.");
  });
});

window.editCustomer = (id) => {
  const customer = customers.find((item) => item.id === id);
  if (!customer) return;
  for (const field of ["name", "email", "mobile", "city"]) customerForm.elements[field].value = customer[field] || "";
  customerForm.elements.is_active.checked = Boolean(customer.is_active);
  customerForm.dataset.id = id;
  customerForm.querySelector("button[type=submit]").textContent = "Save customer";
  document.getElementById("cancel-customer-edit").classList.remove("hidden");
  customerForm.scrollIntoView({ behavior: "smooth" });
};

window.deleteCustomer = async (id) => {
  if (!confirm("Delete this customer?")) return;
  try {
    await api(`/api/customers/${id}`, { method: "DELETE" });
    await loadCustomers();
    showMessage("Customer deleted.");
  } catch (error) { showMessage(error.message, true); }
};

document.getElementById("cancel-customer-edit").addEventListener("click", () => {
  customerForm.reset();
  customerForm.elements.is_active.checked = true;
  customerForm.dataset.id = "";
  customerForm.querySelector("button[type=submit]").textContent = "Add customer";
  document.getElementById("cancel-customer-edit").classList.add("hidden");
});

async function loadProducts() {
  const result = await api("/api/products?limit=100");
  products = result.items;
  document.getElementById("products-table").innerHTML = products.map((product) => `
    <tr>
      <td>${escapeHtml(product.product_code)}</td><td>${escapeHtml(product.name)}</td>
      <td>${escapeHtml(product.category)}</td><td>${Number(product.price).toFixed(2)}</td>
      <td>${product.stock_quantity}</td><td>${product.is_active ? "Active" : "Inactive"}</td>
      <td class="actions">${currentRole === "admin" ? `
        <button class="secondary" onclick="editProduct(${product.id})">Edit</button>
        <button class="secondary" onclick="adjustProductStock(${product.id})">Stock</button>
        <button class="danger" onclick="deleteProduct(${product.id})">Delete</button>` : ""}
      </td>
    </tr>`).join("");
}

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = productForm.querySelector("button[type=submit]");
  await withBusy(button, async () => {
    const form = new FormData(productForm);
    const data = {
      product_code: form.get("product_code"), name: form.get("name"),
      category: form.get("category"), price: Number(form.get("price")),
      stock_quantity: Number(form.get("stock_quantity")), is_active: form.get("is_active") === "on",
    };
    const id = productForm.dataset.id;
    await api(id ? `/api/products/${id}` : "/api/products", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    productForm.reset();
    productForm.elements.is_active.checked = true;
    productForm.dataset.id = "";
    button.textContent = "Add product";
    document.getElementById("cancel-product-edit").classList.add("hidden");
    await loadProducts();
    await refreshOrderRows();
    showMessage(id ? "Product updated." : "Product added.");
  });
});

window.editProduct = (id) => {
  const product = products.find((item) => item.id === id);
  if (!product) return;
  productForm.elements.product_code.value = product.product_code;
  productForm.elements.name.value = product.name;
  productForm.elements.category.value = product.category;
  productForm.elements.price.value = product.price;
  productForm.elements.stock_quantity.value = product.stock_quantity;
  productForm.elements.is_active.checked = Boolean(product.is_active);
  productForm.dataset.id = id;
  productForm.querySelector("button[type=submit]").textContent = "Save product";
  document.getElementById("cancel-product-edit").classList.remove("hidden");
  productForm.scrollIntoView({ behavior: "smooth" });
};

window.deleteProduct = async (id) => {
  if (!confirm("Delete this product?")) return;
  try {
    await api(`/api/products/${id}`, { method: "DELETE" });
    await loadProducts();
    showMessage("Product deleted.");
  } catch (error) { showMessage(error.message, true); }
};

window.adjustProductStock = async (id) => {
  const change = prompt("Stock change: use a positive number to add or negative to remove.");
  if (change === null) return;
  const quantity_change = Number(change);
  if (!Number.isInteger(quantity_change)) return showMessage("Enter a whole number.", true);
  const reason = prompt("Reason for the stock change:");
  if (!reason) return;
  try {
    await api(`/api/products/${id}/stock-adjustments`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity_change, reason }),
    });
    await loadProducts();
    showMessage("Stock adjusted.");
  } catch (error) { showMessage(error.message, true); }
};

document.getElementById("cancel-product-edit").addEventListener("click", () => {
  productForm.reset();
  productForm.elements.is_active.checked = true;
  productForm.dataset.id = "";
  productForm.querySelector("button[type=submit]").textContent = "Add product";
  document.getElementById("cancel-product-edit").classList.add("hidden");
});

document.getElementById("csv-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button");
  await withBusy(button, async () => {
    const result = await api("/api/products/import-csv", { method: "POST", body: new FormData(form) });
    form.reset();
    await loadProducts();
    showMessage(result.message);
  });
});

function addOrderRow() {
  const options = products.filter((product) => product.is_active)
    .map((product) => `<option value="${product.id}" data-price="${Number(product.price)}">${escapeHtml(product.name)} — ${Number(product.price).toFixed(2)} (stock ${product.stock_quantity})</option>`)
    .join("");
  const row = document.createElement("div");
  row.className = "order-row";
  row.innerHTML = `<select class="order-product" required>${options}</select>
    <input class="order-quantity" type="number" min="1" step="1" value="1" required>
    <span class="order-amount">0.00</span><button type="button" class="danger remove-row">Remove</button>`;
  orderRows.appendChild(row);
  row.addEventListener("input", updateTotals);
  row.addEventListener("change", updateTotals);
  row.querySelector(".remove-row").addEventListener("click", () => {
    row.remove(); updateTotals();
  });
  updateTotals();
}

async function refreshOrderRows() {
  orderRows.replaceChildren();
  if (products.some((product) => product.is_active)) addOrderRow();
}

function updateTotals() {
  let subtotal = 0;
  let valid = orderRows.children.length > 0 && Boolean(document.getElementById("order-customer").value);
  orderRows.querySelectorAll(".order-row").forEach((row) => {
    const product = row.querySelector(".order-product").selectedOptions[0];
    const quantity = Number(row.querySelector(".order-quantity").value);
    if (!product || !Number.isInteger(quantity) || quantity < 1) valid = false;
    else {
      const amount = Number(product.dataset.price) * quantity;
      subtotal += amount;
      row.querySelector(".order-amount").textContent = amount.toFixed(2);
    }
  });
  const discount = Number(document.getElementById("discount").value);
  if (discount < 0 || discount > 20) valid = false;
  const discountAmount = subtotal * discount / 100;
  document.getElementById("subtotal").textContent = subtotal.toFixed(2);
  document.getElementById("discount-amount").textContent = discountAmount.toFixed(2);
  document.getElementById("total").textContent = (subtotal - discountAmount).toFixed(2);
  document.getElementById("create-order-button").disabled = !valid;
}

document.getElementById("add-order-row").addEventListener("click", addOrderRow);
document.getElementById("discount").addEventListener("input", updateTotals);
document.getElementById("order-customer").addEventListener("change", updateTotals);

document.getElementById("order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("create-order-button");
  await withBusy(button, async () => {
    const items = [...orderRows.querySelectorAll(".order-row")].map((row) => ({
      product_id: Number(row.querySelector(".order-product").value),
      quantity: Number(row.querySelector(".order-quantity").value),
    }));
    const orderId = event.currentTarget.dataset.editId;
    const result = await api(orderId ? `/api/orders/${orderId}` : "/api/orders", {
      method: orderId ? "PUT" : "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: Number(document.getElementById("order-customer").value),
        items, discount_percent: Number(document.getElementById("discount").value),
      }),
    });
    event.currentTarget.reset();
    event.currentTarget.dataset.editId = "";
    await refreshOrderRows();
    showMessage(orderId ? "Draft order updated." : `Draft order ${result.order_number} created.`);
    await loadOrders();
  });
});

async function loadOrders() {
  try {
    const orders = await api("/api/orders");
    document.getElementById("orders-table").innerHTML = orders.map((order) => {
      const customer = customers.find((item) => item.id === order.customer_id);
      const action = order.status === "draft"
        ? `<button class="secondary" onclick="editOrder(${order.id})">Edit</button><button onclick="confirmOrder(${order.id})">Confirm</button><button class="secondary" onclick="cancelOrder(${order.id})">Cancel</button>`
        : order.status === "confirmed"
          ? `<button class="secondary" onclick="cancelOrder(${order.id})">Cancel</button>` : "";
      return `<tr><td>${escapeHtml(order.order_number || order.id)}</td><td>${escapeHtml(customer?.name || order.customer_id)}</td>
        <td>${escapeHtml(order.status)}</td><td>${Number(order.subtotal).toFixed(2)}</td>
        <td>${Number(order.total).toFixed(2)}</td><td class="actions">${action}</td></tr>`;
    }).join("");
  } catch (error) { showMessage(error.message, true); }
}

window.editOrder = async (id) => {
  try {
    const order = await api(`/api/orders/${id}`);
    document.getElementById("order-customer").value = order.customer_id;
    document.getElementById("discount").value = order.discount_percent;
    orderRows.replaceChildren();
    for (const item of order.items) {
      addOrderRow();
      const row = orderRows.lastElementChild;
      row.querySelector(".order-product").value = item.product_id;
      row.querySelector(".order-quantity").value = item.quantity;
    }
    document.getElementById("order-form").dataset.editId = id;
    updateTotals();
    document.querySelector('[data-page="orders"]').click();
    document.getElementById("order-form").scrollIntoView({ behavior: "smooth" });
  } catch (error) { showMessage(error.message, true); }
};

window.confirmOrder = async (id) => {
  if (!confirm(`Confirm order #${id}? This will deduct stock.`)) return;
  try {
    await api(`/api/orders/${id}/confirm`, { method: "POST" });
    await loadProducts(); await loadOrders();
    showMessage(`Order #${id} confirmed.`);
  } catch (error) { showMessage(error.message, true); }
};

window.cancelOrder = async (id) => {
  if (!confirm(`Cancel order #${id}?`)) return;
  try {
    await api(`/api/orders/${id}/cancel`, { method: "POST" });
    await loadProducts(); await loadOrders();
    showMessage(`Order #${id} cancelled.`);
  } catch (error) { showMessage(error.message, true); }
};

function showReport(rows) {
  const target = document.getElementById("report-results");
  if (!rows.length) { target.textContent = "No rows to show."; return; }
  const columns = Object.keys(rows[0]);
  target.innerHTML = `<table><thead><tr>${columns.map((key) => `<th>${escapeHtml(key.replaceAll("_", " "))}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${columns.map((key) => `<td>${escapeHtml(row[key])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

document.querySelectorAll("[data-report]").forEach((button) => {
  button.addEventListener("click", async () => {
    await withBusy(button, async () => {
      const query = new URLSearchParams();
      if (button.dataset.report === "customer-sales") {
        const from = document.getElementById("report-date-from").value;
        const to = document.getElementById("report-date-to").value;
        if (from) query.set("date_from", from);
        if (to) query.set("date_to", to);
      }
      if (button.dataset.report === "low-stock") {
        query.set("threshold", document.getElementById("report-threshold").value || "5");
      }
      const queryString = query.toString();
      const suffix = queryString ? `?${queryString}` : "";
      const rows = await api(`/api/reports/${button.dataset.report}${suffix}`);
      showReport(rows);
      showMessage("Report loaded.");
    });
  });
});

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  await withBusy(button, async () => {
    const values = new FormData(form);
    const result = await api("/api/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: values.get("email"), password: values.get("password") }),
    });
    applyRole(result.role);
    form.reset();
    showMessage(`Logged in as ${result.role}.`);
    await loadCustomers();
    await loadProducts();
    await refreshOrderRows();
    await loadOrders();
  });
});

document.getElementById("logout-button").addEventListener("click", async (event) => {
  await withBusy(event.currentTarget, async () => {
    await api("/api/logout", { method: "POST" });
    applyRole(null);
    customers = [];
    products = [];
    document.getElementById("customers-table").replaceChildren();
    document.getElementById("products-table").replaceChildren();
    document.getElementById("orders-table").replaceChildren();
    document.getElementById("order-customer").replaceChildren();
    orderRows.replaceChildren();
    showMessage("Logged out.");
  });
});

document.getElementById("reload-customers").addEventListener("click", (event) => withBusy(event.currentTarget, loadCustomers));
document.getElementById("reload-products").addEventListener("click", (event) => withBusy(event.currentTarget, loadProducts));
document.getElementById("reload-orders").addEventListener("click", (event) => withBusy(event.currentTarget, loadOrders));

api("/api/me").then(async (user) => {
  applyRole(user.role);
  await loadCustomers();
  await loadProducts();
  await refreshOrderRows();
  await loadOrders();
}).catch(() => {});
