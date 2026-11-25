"use strict";

const byID = (id) => document.getElementById(id);
const query = byID("query");
const categorySelect = byID("category");
const reviewOnly = byID("review-only");
const dialog = byID("detail");
const preview = byID("preview");
const play = byID("play");
const pageSizeSelect = byID("page-size");
let takes = [];
let categories = new Map();
let takesByID = new Map();
let page = 0;
let activeTake;
let playing = false;
let stopCardPreview;

function updatePreview() {
  preview.src = playing ? activeTake.animation : activeTake.thumbnail;
  play.textContent = playing ? "Stop preview" : "Play preview";
  play.setAttribute("aria-pressed", String(playing));
}

function syncDetail() {
  const take = takesByID.get(location.hash.slice(1));
  if (!take) {
    if (dialog.open) dialog.close();
    return;
  }
  if (take === activeTake && dialog.open) return;
  stopCardPreview?.();
  activeTake = take;
  playing = false;
  byID("detail-id").textContent = take.id;
  if (take.needsReview) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = "Needs review";
    byID("detail-id").append(badge);
  }
  byID("detail-title").textContent = take.title;
  byID("detail-meta").textContent = `${categories.get(take.category).name} · ${take.duration.toFixed(2)} s`;
  byID("description").textContent = take.description;
  byID("original").textContent = take.original || "Unavailable";
  byID("tags").textContent = take.tags.join(", ") || "None";
  byID("take-link").href = "#" + take.id;
  preview.alt = "Default Human preview for " + take.title;
  updatePreview();
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
}

function cardFor(take) {
  const card = document.createElement("article");
  card.className = "card";
  const detailLink = document.createElement("a");
  detailLink.className = "card-link";
  detailLink.href = "#" + take.id;
  const image = document.createElement("img");
  image.src = take.thumbnail;
  image.loading = "lazy";
  image.width = image.height = 384;
  image.alt = "";
  const copy = document.createElement("div");
  copy.className = "card-copy";
  const id = document.createElement("span");
  id.className = "take-id";
  id.textContent = take.id;
  const title = document.createElement("strong");
  title.textContent = take.title;
  copy.append(id);
  if (take.needsReview) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = "Needs review";
    copy.append(badge);
  }
  copy.append(title);
  detailLink.append(image, copy);

  const button = document.createElement("button");
  button.className = "card-preview";
  button.type = "button";
  button.setAttribute("aria-label", "Quick preview for " + take.id);
  button.setAttribute("aria-pressed", "false");
  button.textContent = "Preview";

  function stop() {
    image.src = take.thumbnail;
    button.textContent = "Preview";
    button.setAttribute("aria-pressed", "false");
    stopCardPreview = undefined;
  }

  button.addEventListener("click", () => {
    const wasPlaying = stopCardPreview === stop;
    stopCardPreview?.();
    if (wasPlaying) return;
    image.src = take.animation;
    button.textContent = "Stop preview";
    button.setAttribute("aria-pressed", "true");
    stopCardPreview = stop;
  });

  card.append(detailLink, button);
  return card;
}

function render() {
  stopCardPreview?.();
  const terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const category = categories.get(categorySelect.value);
  const matches = takes.filter((take) =>
    (!category || take.category === category.id) &&
    (!reviewOnly.checked || take.needsReview) &&
    terms.every((term) => take.searchText.includes(term))
  );
  const count = matches.length;
  const pageSize = pageSizeSelect.value === "all" ? Math.max(1, count) : Number(pageSizeSelect.value);
  const pages = Math.ceil(count / pageSize);
  page = Math.max(0, Math.min(page, pages - 1));
  const start = page * pageSize;
  byID("results").replaceChildren(...matches.slice(start, start + pageSize).map(cardFor));
  byID("category-description").hidden = !category;
  byID("category-description").textContent = category?.definition || "";
  byID("status").textContent = count
    ? `Showing ${start + 1}–${Math.min(start + pageSize, count)} of ${count.toLocaleString()} takes`
    : "No takes match your filters.";
  byID("pagination").hidden = pages <= 1;
  byID("page-number").textContent = `Page ${page + 1} of ${pages}`;
  byID("previous").disabled = page === 0;
  byID("next").disabled = page + 1 >= pages;
}

async function initialize() {
  const response = await fetch("catalog.json");
  if (!response.ok) throw new Error("Catalog request failed");
  const data = await response.json();
  categories = new Map(data.categories.map((category) => [category.id, category]));
  takes = data.takes.map((take) => ({
    ...take,
    searchText: [take.id, take.title, take.description, take.original, ...take.tags].join(" ").toLowerCase(),
  }));
  takesByID = new Map(takes.map((take) => [take.id, take]));
  for (const category of categories.values()) {
    categorySelect.add(new Option(`${category.name} (${category.count})`, category.id));
  }

  byID("filters").addEventListener("submit", (event) => event.preventDefault());
  byID("filters").addEventListener("input", () => {
    page = 0;
    render();
  });
  for (const [id, delta] of [["previous", -1], ["next", 1]]) {
    byID(id).addEventListener("click", () => {
      page += delta;
      render();
      byID("filters").scrollIntoView();
    });
  }
  byID("close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    if (dialog.open) return;
    if (activeTake && location.hash === "#" + activeTake.id) {
      history.replaceState(null, "", location.pathname + location.search);
    }
    activeTake = undefined;
    preview.removeAttribute("src");
  });
  play.addEventListener("click", () => {
    playing = !playing;
    updatePreview();
  });
  window.addEventListener("hashchange", syncDetail);
  render();
  syncDetail();
}

initialize().catch((error) => {
  console.error(error);
  byID("status").textContent = "Could not load the catalog. Reload the page to try again.";
});
