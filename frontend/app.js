// ---------------------------------------------------------------------------
// Mongo Shop — minimal vanilla-JS SPA talking to the FastAPI / MongoDB backend.
// ---------------------------------------------------------------------------
const API = "/api";
const state = { user: null, categories: [], filters: {} };

const EMOJI = {
  Electronics: "📱", Books: "📚", Clothing: "👕", "Home & Kitchen": "🍳",
  Sports: "🏅", "Toys & Games": "🎲", Beauty: "💄", Grocery: "🛒",
  Automotive: "🚗", Garden: "🌱",
};

// ---- helpers --------------------------------------------------------------
async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

const view = () => document.getElementById("view");
const money = (n) => (n ?? 0).toLocaleString("fr-CH", { style: "currency", currency: "CHF" });
const stars = (r) => "★".repeat(Math.round(r || 0)) + "☆".repeat(5 - Math.round(r || 0));

function notify(message, type = "success") {
  const el = document.getElementById("alert");
  el.className = `alert alert-${type}`;
  el.textContent = message;
  setTimeout(() => el.classList.add("d-none"), 3000);
}

// ---- bootstrap ------------------------------------------------------------
async function init() {
  document.querySelectorAll("[data-view]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      route(a.dataset.view);
    })
  );

  const users = await api("/users");
  const sel = document.getElementById("userSelect");
  sel.innerHTML = users
    .map((u) => `<option value="${u._id}">${u.first_name} ${u.last_name}</option>`)
    .join("");
  state.user = users[0]?._id;
  sel.addEventListener("change", (e) => {
    state.user = e.target.value;
    refreshCartBadge();
  });

  state.categories = await api("/categories");
  await refreshCartBadge();
  route("catalog");
}

function route(name) {
  ({ catalog: renderCatalog, cart: renderCart, orders: renderOrders, dashboard: renderDashboard }[name] ||
    renderCatalog)();
}

// ---- catalog --------------------------------------------------------------
async function renderCatalog() {
  const f = state.filters;
  const params = new URLSearchParams();
  if (f.search) params.set("search", f.search);
  if (f.category_id) params.set("category_id", f.category_id);
  if (f.min_price) params.set("min_price", f.min_price);
  if (f.max_price) params.set("max_price", f.max_price);
  if (f.in_stock) params.set("in_stock", "true");
  params.set("sort_by", f.sort_by || "name");
  params.set("order", f.order || "asc");

  const data = await api("/products?" + params.toString());
  const catOptions = state.categories
    .map((c) => `<option value="${c._id}" ${f.category_id === c._id ? "selected" : ""}>${c.name}</option>`)
    .join("");

  view().innerHTML = `
    <div class="row g-3 mb-4 align-items-end">
      <div class="col-md-3">
        <label class="form-label small">Recherche</label>
        <input id="fSearch" class="form-control" value="${f.search || ""}" placeholder="nom, description...">
      </div>
      <div class="col-md-2">
        <label class="form-label small">Catégorie</label>
        <select id="fCat" class="form-select"><option value="">Toutes</option>${catOptions}</select>
      </div>
      <div class="col-md-2">
        <label class="form-label small">Prix min / max</label>
        <div class="input-group">
          <input id="fMin" type="number" class="form-control" placeholder="0" value="${f.min_price || ""}">
          <input id="fMax" type="number" class="form-control" placeholder="∞" value="${f.max_price || ""}">
        </div>
      </div>
      <div class="col-md-2">
        <label class="form-label small">Trier par</label>
        <select id="fSort" class="form-select">
          <option value="name">Nom</option>
          <option value="price" ${f.sort_by === "price" ? "selected" : ""}>Prix</option>
          <option value="stock" ${f.sort_by === "stock" ? "selected" : ""}>Stock</option>
        </select>
      </div>
      <div class="col-md-1">
        <select id="fOrder" class="form-select">
          <option value="asc">↑</option>
          <option value="desc" ${f.order === "desc" ? "selected" : ""}>↓</option>
        </select>
      </div>
      <div class="col-md-2 form-check ms-2">
        <input id="fStock" class="form-check-input" type="checkbox" ${f.in_stock ? "checked" : ""}>
        <label class="form-check-label small">En stock uniquement</label>
      </div>
    </div>
    <p class="text-muted">${data.total} produit(s) trouvé(s)</p>
    <div class="row row-cols-1 row-cols-sm-2 row-cols-lg-4 g-3" id="grid">
      ${data.items.map(productCard).join("") || "<p>Aucun produit.</p>"}
    </div>`;

  const apply = () => {
    state.filters = {
      search: document.getElementById("fSearch").value.trim(),
      category_id: document.getElementById("fCat").value,
      min_price: document.getElementById("fMin").value,
      max_price: document.getElementById("fMax").value,
      sort_by: document.getElementById("fSort").value,
      order: document.getElementById("fOrder").value,
      in_stock: document.getElementById("fStock").checked,
    };
    renderCatalog();
  };
  ["fSearch", "fMin", "fMax"].forEach((id) =>
    document.getElementById(id).addEventListener("keyup", (e) => e.key === "Enter" && apply())
  );
  ["fCat", "fSort", "fOrder", "fStock"].forEach((id) =>
    document.getElementById(id).addEventListener("change", apply)
  );
  document.querySelectorAll("[data-product]").forEach((el) =>
    el.addEventListener("click", () => openProduct(el.dataset.product))
  );
  document.querySelectorAll("[data-add]").forEach((el) =>
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      addToCart(el.dataset.add);
    })
  );
}

function catName(id) {
  return state.categories.find((c) => c._id === id)?.name || "";
}

function productCard(p) {
  const emoji = EMOJI[catName(p.category_id)] || "📦";
  const out = p.stock <= 0;
  return `
    <div class="col">
      <div class="card product-card cursor-pointer" data-product="${p._id}">
        <div class="product-thumb">${emoji}</div>
        <div class="card-body d-flex flex-column">
          <h6 class="card-title">${p.name}</h6>
          <div class="text-muted small mb-2">${catName(p.category_id)}</div>
          <div class="mt-auto d-flex justify-content-between align-items-center">
            <strong>${money(p.price)}</strong>
            <span class="badge ${out ? "bg-secondary" : "bg-success-subtle text-success-emphasis"}">
              ${out ? "Rupture" : "Stock " + p.stock}
            </span>
          </div>
          <button class="btn btn-sm btn-success mt-2" data-add="${p._id}" ${out ? "disabled" : ""}>
            Ajouter au panier
          </button>
        </div>
      </div>
    </div>`;
}

// ---- product detail -------------------------------------------------------
async function openProduct(id) {
  const p = await api(`/products/${id}`);
  const reviews = p.reviews || [];
  const modalHtml = `
    <div class="modal fade" id="pModal" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${p.name}</h5>
            <button class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <p>${p.description || ""}</p>
            <ul class="list-unstyled">
              <li><strong>Prix :</strong> ${money(p.price)}</li>
              <li><strong>Stock :</strong> ${p.stock}</li>
              <li><strong>Catégorie :</strong> ${p.category?.name || "-"}</li>
              <li><strong>Fournisseur :</strong> ${p.supplier?.name || "-"} (${p.supplier?.country || ""})</li>
              <li><strong>Tags :</strong> ${(p.tags || []).map((t) => `<span class="badge bg-light text-dark">${t}</span>`).join(" ")}</li>
              <li><strong>Note moyenne :</strong> <span class="stars">${stars(p.rating_avg)}</span> (${p.review_count} avis)</li>
            </ul>
            <hr>
            <h6>Avis clients</h6>
            ${
              reviews.length
                ? reviews
                    .map(
                      (r) => `<div class="border-bottom py-2">
                        <span class="stars">${stars(r.rating)}</span> <strong>${r.title || ""}</strong>
                        <div class="small text-muted">${r.comment || ""}</div></div>`
                    )
                    .join("")
                : "<p class='text-muted'>Aucun avis.</p>"
            }
            <hr>
            <h6>Laisser un avis</h6>
            <div class="row g-2">
              <div class="col-3"><select id="rRating" class="form-select">
                ${[5, 4, 3, 2, 1].map((n) => `<option value="${n}">${n} ★</option>`).join("")}
              </select></div>
              <div class="col-4"><input id="rTitle" class="form-control" placeholder="Titre"></div>
              <div class="col"><input id="rComment" class="form-control" placeholder="Commentaire"></div>
              <div class="col-auto"><button id="rSubmit" class="btn btn-outline-success">Publier</button></div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-success" id="mAdd" ${p.stock <= 0 ? "disabled" : ""}>Ajouter au panier</button>
          </div>
        </div>
      </div>
    </div>`;
  document.getElementById("modalHost")?.remove();
  const host = document.createElement("div");
  host.id = "modalHost";
  host.innerHTML = modalHtml;
  document.body.appendChild(host);
  const modal = new bootstrap.Modal(document.getElementById("pModal"));
  modal.show();

  document.getElementById("mAdd").onclick = () => {
    addToCart(p._id);
    modal.hide();
  };
  document.getElementById("rSubmit").onclick = async () => {
    await api("/reviews", {
      method: "POST",
      body: JSON.stringify({
        product_id: p._id,
        user_id: state.user,
        rating: parseInt(document.getElementById("rRating").value),
        title: document.getElementById("rTitle").value,
        comment: document.getElementById("rComment").value,
      }),
    });
    notify("Avis publié !");
    modal.hide();
    openProduct(id);
  };
}

// ---- cart -----------------------------------------------------------------
async function addToCart(productId) {
  try {
    await api(`/carts/${state.user}/items`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity: 1 }),
    });
    notify("Ajouté au panier");
    refreshCartBadge();
  } catch (e) {
    notify(e.message, "danger");
  }
}

async function getCart() {
  try {
    return await api(`/carts/${state.user}`);
  } catch {
    return null;
  }
}

async function refreshCartBadge() {
  const cart = await getCart();
  const count = cart ? cart.items.reduce((s, i) => s + i.quantity, 0) : 0;
  document.getElementById("cartBadge").textContent = count;
}

async function renderCart() {
  const cart = await getCart();
  if (!cart || !cart.items.length) {
    view().innerHTML = `<div class="alert alert-info">Votre panier est vide.</div>`;
    return;
  }
  view().innerHTML = `
    <h3 class="mb-3">Mon panier</h3>
    <table class="table align-middle">
      <thead><tr><th>Produit</th><th>Prix</th><th>Qté</th><th>Sous-total</th><th></th></tr></thead>
      <tbody>
        ${cart.items
          .map(
            (i) => `<tr>
              <td>${i.name}</td><td>${money(i.price)}</td><td>${i.quantity}</td>
              <td>${money(i.subtotal)}</td>
              <td><button class="btn btn-sm btn-outline-danger" data-del="${i.product_id}">✕</button></td>
            </tr>`
          )
          .join("")}
      </tbody>
      <tfoot><tr><th colspan="3" class="text-end">Total</th><th>${money(cart.total)}</th><th></th></tr></tfoot>
    </table>
    <button id="checkout" class="btn btn-success btn-lg">Passer la commande</button>`;

  document.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api(`/carts/${state.user}/items/${b.dataset.del}`, { method: "DELETE" });
      renderCart();
      refreshCartBadge();
    })
  );
  document.getElementById("checkout").onclick = () => checkout(cart);
}

async function checkout(cart) {
  try {
    const order = await api("/orders", {
      method: "POST",
      body: JSON.stringify({
        user_id: state.user,
        lines: cart.items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
      }),
    });
    const payment = await api("/payments", {
      method: "POST",
      body: JSON.stringify({ order_id: order._id, method: "card" }),
    });
    notify(
      payment.status === "succeeded"
        ? `Commande payée ✔ (${money(order.total)})`
        : "Paiement refusé, réessayez.",
      payment.status === "succeeded" ? "success" : "warning"
    );
    refreshCartBadge();
    route("orders");
  } catch (e) {
    notify(e.message, "danger");
  }
}

// ---- orders ---------------------------------------------------------------
async function renderOrders() {
  const orders = await api(`/orders?user_id=${state.user}`);
  view().innerHTML = `
    <h3 class="mb-3">Mes commandes</h3>
    ${
      orders.length
        ? `<table class="table">
            <thead><tr><th>#</th><th>Date</th><th>Statut</th><th>Total</th></tr></thead>
            <tbody>${orders
              .map(
                (o) => `<tr>
                  <td><code>${o._id.slice(-6)}</code></td>
                  <td>${new Date(o.created_at).toLocaleDateString("fr-CH")}</td>
                  <td><span class="badge bg-${statusColor(o.status)}">${o.status}</span></td>
                  <td>${money(o.total)}</td></tr>`
              )
              .join("")}</tbody></table>`
        : `<div class="alert alert-info">Aucune commande pour cet utilisateur.</div>`
    }`;
}

const statusColor = (s) =>
  ({ pending: "secondary", paid: "primary", shipped: "info", delivered: "success", cancelled: "danger" }[s] ||
  "secondary");

// ---- dashboard (aggregations) ---------------------------------------------
async function renderDashboard() {
  const [summary, byCat, top, status] = await Promise.all([
    api("/analytics/summary"),
    api("/analytics/revenue-by-category"),
    api("/analytics/top-products"),
    api("/analytics/orders-by-status"),
  ]);
  view().innerHTML = `
    <h3 class="mb-3">Tableau de bord</h3>
    <div class="row g-3 mb-4">
      ${[
        ["Utilisateurs", summary.users],
        ["Produits", summary.products],
        ["Commandes", summary.orders],
        ["Avis", summary.reviews],
        ["Chiffre d'affaires", money(summary.revenue)],
      ]
        .map(
          ([label, val]) => `<div class="col"><div class="card kpi-card p-3">
            <div class="text-muted small">${label}</div><div class="fs-4 fw-bold">${val}</div></div></div>`
        )
        .join("")}
    </div>
    <div class="row g-4">
      <div class="col-md-6"><div class="card p-3"><h6>Revenu par catégorie</h6>
        <table class="table table-sm"><tbody>${byCat
          .map((c) => `<tr><td>${c.category}</td><td class="text-end">${money(c.revenue)}</td></tr>`)
          .join("")}</tbody></table></div></div>
      <div class="col-md-6"><div class="card p-3"><h6>Top produits (unités vendues)</h6>
        <table class="table table-sm"><tbody>${top
          .map((t) => `<tr><td>${t.name}</td><td class="text-end">${t.units_sold} u.</td></tr>`)
          .join("")}</tbody></table></div></div>
      <div class="col-md-6"><div class="card p-3"><h6>Commandes par statut</h6>
        <table class="table table-sm"><tbody>${status
          .map((s) => `<tr><td><span class="badge bg-${statusColor(s.status)}">${s.status}</span></td>
            <td class="text-end">${s.count} cmd — ${money(s.revenue)}</td></tr>`)
          .join("")}</tbody></table></div></div>
    </div>`;
}

init().catch((e) => notify("Erreur d'initialisation : " + e.message, "danger"));
