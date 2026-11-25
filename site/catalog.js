"use strict";

const byID = (id) => document.getElementById(id);
const assetRevision = new URL(document.currentScript.src).search;
const query = byID("query");
const categorySelect = byID("category");
const motionFilterSelect = byID("motion-filter");
const reviewOnly = byID("review-only");
const dialog = byID("detail");
const preview = byID("preview");
const play = byID("play");
const toggle3D = byID("toggle-3d");
const skeletonPreview = byID("skeleton-preview");
const skeletonStatus = byID("skeleton-status");
const skeletonPlayer = byID("skeleton-player");
const pageSizeSelect = byID("page-size");
const bvhLink = byID("bvh-link");
let takes = [];
let categories = new Map();
let takesByID = new Map();
let page = 0;
let activeTake;
let detailOpener;
let playing = false;
let stopCardPreview;
let skeletonRequest;
let releaseSkeleton;

function updatePreview() {
  preview.src = playing ? activeTake.animation : activeTake.thumbnail;
  play.textContent = playing ? "Stop preview" : "Play preview";
  play.setAttribute("aria-pressed", String(playing));
}

function hideSkeletonPreview() {
  skeletonRequest?.abort();
  skeletonRequest = undefined;
  releaseSkeleton?.();
  releaseSkeleton = undefined;
  skeletonPreview.hidden = true;
  skeletonPlayer.hidden = true;
  preview.hidden = false;
  play.hidden = false;
  toggle3D.textContent = "3D Preview";
  toggle3D.setAttribute("aria-expanded", "false");
}

async function toggleSkeletonPreview() {
  if (!skeletonPreview.hidden) {
    hideSkeletonPreview();
    return;
  }
  if (!activeTake?.motion) return;
  const request = new AbortController();
  const { signal } = request;
  skeletonRequest = request;
  skeletonPreview.hidden = false;
  toggle3D.textContent = "Close 3D Preview";
  toggle3D.setAttribute("aria-expanded", "true");
  skeletonStatus.hidden = false;
  skeletonStatus.textContent = "Loading 3D preview…";

  const showUnavailable = () => {
    releaseSkeleton?.();
    releaseSkeleton = undefined;
    skeletonPlayer.hidden = true;
    preview.hidden = false;
    play.hidden = false;
    skeletonStatus.hidden = false;
    skeletonStatus.textContent = "3D preview is unavailable. You can still play the image preview.";
  };
  const motion = activeTake.motion;
  try {
    const [{ showMotion }, text] = await Promise.all([
      import(`./skeleton-viewer.js${assetRevision}`),
      fetch(motion.url, { signal }).then((response) => {
        if (!response.ok) throw new Error(`BVH request failed (${response.status})`);
        return response.text();
      }),
    ]);
    if (signal.aborted || !dialog.open) return;
    skeletonPlayer.hidden = false;
    releaseSkeleton = showMotion(text, motion, {
      viewport: byID("skeleton-viewport"),
      play: byID("skeleton-play"),
      scrubber: byID("skeleton-time"),
      timestamp: byID("skeleton-timestamp"),
      reset: byID("skeleton-reset"),
      view: byID("preview-view"),
      viewStatus: byID("preview-view-status"),
      onUnavailable: showUnavailable,
    });
    playing = false;
    updatePreview();
    preview.hidden = true;
    play.hidden = true;
    skeletonStatus.hidden = true;
  } catch (error) {
    if (signal.aborted) return;
    request.abort();
    console.warn("Could not open 3D preview", error);
    showUnavailable();
  } finally {
    if (skeletonRequest === request) skeletonRequest = undefined;
  }
}

function syncDetail() {
  const take = takesByID.get(location.hash.slice(1));
  if (!take) {
    if (dialog.open) dialog.close();
    return;
  }
  if (take === activeTake && dialog.open) return;
  stopCardPreview?.();
  hideSkeletonPreview();
  activeTake = take;
  detailOpener = undefined;
  toggle3D.hidden = !take.motion;
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
  const bvhURL = take.motion?.url;
  bvhLink.hidden = !bvhURL;
  if (bvhURL) bvhLink.href = bvhURL;
  else bvhLink.removeAttribute("href");
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

  const actions = document.createElement("div");
  actions.className = "card-actions";
  actions.append(button);
  if (take.motion) {
    const preview3D = document.createElement("button");
    preview3D.type = "button";
    preview3D.textContent = "3D Preview";
    preview3D.setAttribute("aria-label", "3D Preview for " + take.id);
    preview3D.setAttribute("aria-haspopup", "dialog");
    preview3D.addEventListener("click", () => {
      location.hash = take.id;
      syncDetail();
      detailOpener = preview3D;
      toggleSkeletonPreview();
    });
    actions.append(preview3D);
  }
  card.append(detailLink, actions);
  return card;
}

function render() {
  stopCardPreview?.();
  const terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const category = categories.get(categorySelect.value);
  const motionFilter = motionFilterSelect.value;
  const matches = takes.filter((take) =>
    (!category || take.category === category.id || take.secondaryCategories?.includes(category.id)) &&
    (!motionFilter || take.motionFilters?.includes(motionFilter)) &&
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
  for (const filter of data.motionFilters ?? []) {
    motionFilterSelect.add(new Option(`${filter.name} (${filter.count})`, filter.id));
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
    hideSkeletonPreview();
    if (activeTake && location.hash === "#" + activeTake.id) {
      history.replaceState(null, "", location.pathname + location.search);
    }
    activeTake = undefined;
    preview.removeAttribute("src");
    if (detailOpener?.isConnected) detailOpener.focus();
    detailOpener = undefined;
  });
  play.addEventListener("click", () => {
    playing = !playing;
    updatePreview();
  });
  toggle3D.addEventListener("click", toggleSkeletonPreview);
  window.addEventListener("hashchange", syncDetail);
  render();
  syncDetail();
}

initialize().catch((error) => {
  console.error(error);
  byID("status").textContent = "Could not load the catalog. Reload the page to try again.";
});
