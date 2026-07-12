/* Gallery is data-driven: assets/gallery.json is generated from the photos/
   folder by scripts/build_gallery.py (run by GitHub Actions on every push). */

const TRAP = "trap-houses"; // rendered in its own bottom section, not the Work grid

const state = { items: [], filter: "all", lightboxItems: [], lightboxIndex: 0 };

const $ = (id) => document.getElementById(id);

async function loadGallery() {
  let items = [];
  try {
    const res = await fetch("assets/gallery.json");
    if (res.ok) items = await res.json();
  } catch (_) { /* fall through to empty state */ }
  state.items = items;
  buildFilters();
  renderGallery();
  renderTrapHouses();
}

function workItems() {
  return state.items.filter((i) => i.category !== TRAP);
}

function categories() {
  const seen = new Map();
  for (const item of workItems()) {
    if (!seen.has(item.category)) seen.set(item.category, item.categoryLabel || item.category);
  }
  return seen;
}

function buildFilters() {
  const cats = categories();
  const wrap = $("filters");
  wrap.innerHTML = "";
  if (cats.size < 2) return;
  const all = [["all", "All"], ...cats];
  for (const [key, label] of all) {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.setAttribute("aria-pressed", String(key === state.filter));
    btn.addEventListener("click", () => {
      state.filter = key;
      wrap.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
      renderGallery();
    });
    wrap.appendChild(btn);
  }
}

function visibleItems() {
  if (state.filter === "all") return workItems();
  return workItems().filter((i) => i.category === state.filter);
}

function renderInto(container, items) {
  container.innerHTML = "";
  items.forEach((item, i) => {
    const fig = document.createElement("figure");
    if (item.w && item.h && item.w / item.h > 2) fig.classList.add("wide");
    if (item.type === "video") fig.classList.add("is-video");
    const img = document.createElement("img");
    img.src = item.thumb || item.poster || item.src;
    img.alt = item.alt || "";
    img.loading = "lazy";
    fig.appendChild(img);
    fig.addEventListener("click", () => openLightbox(items, i));
    fig.tabIndex = 0;
    fig.setAttribute("role", "button");
    fig.setAttribute("aria-label", "View larger: " + (item.alt || "photo"));
    fig.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openLightbox(items, i); }
    });
    container.appendChild(fig);
  });
}

function renderGallery() {
  const items = visibleItems();
  renderInto($("gallery"), items);
  $("gallery-empty").hidden = items.length > 0;
}

function renderTrapHouses() {
  const items = state.items.filter((i) => i.category === TRAP);
  const section = document.getElementById("trap-houses");
  if (!section) return;
  section.hidden = items.length === 0;
  renderInto($("trap-gallery"), items);
}

/* Lightbox */
function openLightbox(items, index) {
  state.lightboxItems = items;
  state.lightboxIndex = index;
  updateLightbox();
  $("lightbox").showModal();
}

function updateLightbox() {
  const items = state.lightboxItems;
  const item = items[state.lightboxIndex];
  if (!item) return;
  const img = $("lb-img");
  const video = $("lb-video");
  video.pause();
  if (item.type === "video") {
    img.hidden = true;
    video.hidden = false;
    video.poster = item.poster || "";
    video.src = item.src;
    video.play().catch(() => {});
  } else {
    video.removeAttribute("src");
    video.hidden = true;
    img.hidden = false;
    img.src = item.src;
    img.alt = item.alt || "";
  }
  $("lb-caption").textContent = item.alt || "";
  const solo = items.length < 2;
  $("lb-prev").hidden = solo;
  $("lb-next").hidden = solo;
}

function stepLightbox(delta) {
  const n = state.lightboxItems.length;
  if (!n) return;
  state.lightboxIndex = (state.lightboxIndex + delta + n) % n;
  updateLightbox();
}

function initLightbox() {
  const box = $("lightbox");
  box.addEventListener("close", () => $("lb-video").pause());
  $("lb-close").addEventListener("click", () => box.close());
  $("lb-prev").addEventListener("click", () => stepLightbox(-1));
  $("lb-next").addEventListener("click", () => stepLightbox(1));
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
  box.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") stepLightbox(-1);
    if (e.key === "ArrowRight") stepLightbox(1);
  });
}

/* Header border + scroll reveals */
function initChrome() {
  const header = document.querySelector(".site-header");
  addEventListener("scroll", () => header.classList.toggle("scrolled", scrollY > 8), { passive: true });

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    }
  }, { threshold: 0.08 });
  document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
}

/* Hide optional images that don't exist yet (hero, portrait) */
function initOptionalImages() {
  for (const id of ["hero-img", "portrait-img"]) {
    const img = $(id);
    img.addEventListener("error", () => img.setAttribute("data-missing", ""));
    if (img.complete && img.naturalWidth === 0) img.setAttribute("data-missing", "");
  }
}

initChrome();
initLightbox();
initOptionalImages();
loadGallery();
