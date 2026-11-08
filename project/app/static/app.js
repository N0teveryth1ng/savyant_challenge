const message = document.getElementById("message");
const customerForm = document.getElementById("customer-form");
const productForm = document.getElementById("product-form");
const orderRows = document.getElementById("order-rows");

let customers = [];
let products = [];

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
  customers = await api("/customers");
  document.getElementById("customers-table").innerHTML = customers.map((customer) => `
    <tr>
      <td>${escapeHtml(customer.name)}</td><td>${escapeHtml(customer.email)}</td>
      <td>${escapeHtml(customer.mobile)}</td><td>${escapeHtml(customer.city)}</td>
      <td>${customer.is_active ? "Active" : "Inactive"}</td>
      <td class="actions">
        <button class="secondary" onclick="editCustomer(${customer.id})">Edit</button>
        <button class="danger" onclick="deleteCustomer(${customer.id})">Delete</button>
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
    await api(id ? `/customers/${id}` : "/customers", {
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
    await api(`/customers/${id}`, { method: "DELETE" });
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
  products = await api("/products");
  document.getElementById("products-table").innerHTML = products.map((product) => `
    <tr>
      <td>${escapeHtml(product.product_code)}</td><td>${escapeHtml(product.name)}</td>
      <td>${escapeHtml(product.category)}</td><td>${Number(product.price).toFixed(2)}</td>
      <td>${product.stock_quantity}</td><td>${product.is_active ? "Active" : "Inactive"}</td>
      <td class="actions">
        <button class="secondary" onclick="editProduct(${product.id})">Edit</button>
        <button class="secondary" onclick="adjustProductStock(${product.id})">Stock</button>
        <button class="danger" onclick="deleteProduct(${product.id})">Delete</button>
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
    await api(id ? `/products/${id}` : "/products", {
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
    await api(`/products/${id}`, { method: "DELETE" });
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
    await api(`/products/${id}/stock-adjustments`, {
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
    const result = await api("/products/import-csv", { method: "POST", body: new FormData(form) });
    form.reset();
    await loadProducts();
    showMessage(result.message);
  });
});

function addOrderRow() {
  const options = products.filter((product) => product.is_active)
    .map((product) => `<option value="${product.id}" data-price="${Number(product.price)}">${escapeHtml(product.name)} — ${Number(product.price).toFixed(2)}</option>`)
    .join("");
  const row = document.createElement("div");
  row.className = "order-row";
  row.innerHTML = `<select class="order-product" required>${options}</select>
    <input class="order-quantity" type="number" min="1" step="1" value="1" required>
    <button type="button" class="danger remove-row">Remove</button>`;
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
  let valid = orderRows.children.length > 0;
  orderRows.querySelectorAll(".order-row").forEach((row) => {
    const product = row.querySelector(".order-product").selectedOptions[0];
    const quantity = Number(row.querySelector(".order-quantity").value);
    if (!product || !Number.isInteger(quantity) || quantity < 1) valid = false;
    else subtotal += Number(product.dataset.price) * quantity;
  });
  const discount = Number(document.getElementById("discount").value);
  if (discount < 0 || discount > 20) valid = false;
  document.getElementById("subtotal").textContent = subtotal.toFixed(2);
  document.getElementById("total").textContent = (subtotal * (1 - discount / 100)).toFixed(2);
  document.getElementById("create-order-button").disabled = !valid;
}

document.getElementById("add-order-row").addEventListener("click", addOrderRow);
document.getElementById("discount").addEventListener("input", updateTotals);

document.getElementById("order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("create-order-button");
  await withBusy(button, async () => {
    const items = [...orderRows.querySelectorAll(".order-row")].map((row) => ({
      product_id: Number(row.querySelector(".order-product").value),
      quantity: Number(row.querySelector(".order-quantity").value),
    }));
    const result = await api("/orders", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: Number(document.getElementById("order-customer").value),
        items, discount_percent: Number(document.getElementById("discount").value),
      }),
    });
    showMessage(`Draft order #${result.id} created.`);
    await loadOrders();
  });
});

async function loadOrders() {
  try {
    const orders = await api("/orders");
    document.getElementById("orders-table").innerHTML = orders.map((order) => {
      const customer = customers.find((item) => item.id === order.customer_id);
      const action = order.status === "draft"
        ? `<button onclick="confirmOrder(${order.id})">Confirm</button><button class="secondary" onclick="cancelOrder(${order.id})">Cancel</button>`
        : order.status === "confirmed"
          ? `<button class="secondary" onclick="cancelOrder(${order.id})">Cancel</button>` : "";
      return `<tr><td>${order.id}</td><td>${escapeHtml(customer?.name || order.customer_id)}</td>
        <td>${escapeHtml(order.status)}</td><td>${Number(order.subtotal).toFixed(2)}</td>
        <td>${Number(order.total).toFixed(2)}</td><td class="actions">${action}</td></tr>`;
    }).join("");
  } catch (error) { showMessage(error.message, true); }
}

window.confirmOrder = async (id) => {
  if (!confirm(`Confirm order #${id}? This will deduct stock.`)) return;
  try {
    await api(`/orders/${id}/confirm`, { method: "POST" });
    await loadProducts(); await loadOrders();
    showMessage(`Order #${id} confirmed.`);
  } catch (error) { showMessage(error.message, true); }
};

window.cancelOrder = async (id) => {
  if (!confirm(`Cancel order #${id}?`)) return;
  try {
    await api(`/orders/${id}/cancel`, { method: "POST" });
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
      const rows = await api(`/reports/${button.dataset.report}`);
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
    form.reset();
    showMessage(`Logged in as ${result.role}.`);
    await loadOrders();
  });
});

document.getElementById("logout-button").addEventListener("click", async (event) => {
  await withBusy(event.currentTarget, async () => {
    await api("/api/logout", { method: "POST" });
    document.getElementById("orders-table").replaceChildren();
    showMessage("Logged out.");
  });
});

document.getElementById("reload-customers").addEventListener("click", (event) => withBusy(event.currentTarget, loadCustomers));
document.getElementById("reload-products").addEventListener("click", (event) => withBusy(event.currentTarget, loadProducts));
document.getElementById("reload-orders").addEventListener("click", (event) => withBusy(event.currentTarget, loadOrders));

loadCustomers().catch((error) => showMessage(error.message, true));
loadProducts().then(refreshOrderRows).catch((error) => showMessage(error.message, true));
