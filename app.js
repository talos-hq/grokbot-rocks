// Grok Bot Rocks — client-side directory search.
// Data comes from data/directory.json, produced by scripts/scrape.py.

const state = {
  entries: [],
  categories: [],
  query: "",
  category: "all",
  sort: "category",
};

const els = {
  q: document.getElementById("q"),
  sort: document.getElementById("sort"),
  reset: document.getElementById("reset"),
  chips: document.getElementById("chips"),
  grid: document.getElementById("grid"),
  empty: document.getElementById("empty"),
  total: document.getElementById("stat-total"),
  cats: document.getElementById("stat-cats"),
  shown: document.getElementById("stat-shown"),
  snapshot: document.getElementById("snapshot"),
};

const collator = new Intl.Collator(undefined, { sensitivity: "base" });
const fold = (value) => value.toLowerCase();

function matches(entry, query) {
  if (!query) return true;
  const haystack = `${entry.name} ${entry.author} ${entry.description} ${entry.category}`;
  return fold(haystack).includes(query);
}

function visibleEntries() {
  const query = fold(state.query.trim());
  return state.entries.filter(
    (entry) =>
      (state.category === "all" || entry.category === state.category) &&
      matches(entry, query),
  );
}

function sortEntries(entries) {
  const byName = (a, b) => collator.compare(a.name, b.name);
  const sorted = [...entries];
  if (state.sort === "name") sorted.sort(byName);
  else if (state.sort === "author")
    sorted.sort((a, b) => collator.compare(a.author, b.author) || byName(a, b));
  else
    sorted.sort(
      (a, b) => collator.compare(a.category, b.category) || byName(a, b),
    );
  return sorted;
}

function card(entry) {
  const node = document.createElement("article");
  node.className = "card";

  const title = document.createElement("h3");
  const link = document.createElement("a");
  link.href = entry.url;
  link.target = "_blank";
  link.rel = "noopener";
  link.textContent = entry.name;
  title.append(link);

  const author = document.createElement("span");
  author.className = "author";
  author.textContent = entry.author ? `by ${entry.author}` : "unattributed";

  const description = document.createElement("p");
  description.textContent = entry.description;

  const category = document.createElement("span");
  category.className = "cat";
  category.textContent = entry.category;

  node.append(title, author, description, category);
  return node;
}

function render() {
  const entries = sortEntries(visibleEntries());
  els.grid.replaceChildren();
  els.shown.textContent = String(entries.length);
  els.empty.hidden = entries.length > 0;

  let currentCategory = null;
  const fragment = document.createDocumentFragment();
  for (const entry of entries) {
    if (state.sort === "category" && entry.category !== currentCategory) {
      currentCategory = entry.category;
      const head = document.createElement("h2");
      head.className = "cat-head";
      head.textContent = entry.category;
      fragment.append(head);
    }
    fragment.append(card(entry));
  }
  els.grid.append(fragment);
}

function renderChips() {
  const counts = new Map();
  for (const entry of state.entries)
    counts.set(entry.category, (counts.get(entry.category) ?? 0) + 1);

  els.chips.replaceChildren();
  const options = [["all", "All bots", state.entries.length]];
  for (const category of state.categories)
    options.push([category, category, counts.get(category) ?? 0]);

  for (const [value, label, count] of options) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.setAttribute("aria-pressed", String(state.category === value));
    chip.append(document.createTextNode(label));
    const badge = document.createElement("span");
    badge.className = "n";
    badge.textContent = String(count);
    chip.append(badge);
    chip.addEventListener("click", () => {
      state.category = value;
      renderChips();
      render();
    });
    els.chips.append(chip);
  }
}

function debounce(fn, delay = 120) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function boot() {
  const response = await fetch("data/directory.json", { cache: "no-cache" });
  if (!response.ok) throw new Error(`directory.json: ${response.status}`);
  const data = await response.json();

  state.entries = data.entries ?? [];
  state.categories = data.categories ?? [];

  els.total.textContent = String(data.total ?? state.entries.length);
  els.cats.textContent = String(state.categories.length);
  if (data.generated) {
    els.snapshot.textContent = new Date(data.generated).toLocaleDateString(
      undefined,
      { year: "numeric", month: "long", day: "numeric" },
    );
  } else {
    els.snapshot.textContent = "bundled snapshot";
  }

  renderChips();
  render();

  els.q.addEventListener(
    "input",
    debounce((event) => {
      state.query = event.target.value;
      render();
    }),
  );
  els.sort.addEventListener("change", (event) => {
    state.sort = event.target.value;
    render();
  });
  els.reset.addEventListener("click", () => {
    state.query = "";
    state.category = "all";
    state.sort = "category";
    els.q.value = "";
    els.sort.value = "category";
    renderChips();
    render();
  });
}

boot().catch((error) => {
  els.grid.textContent = `Could not load the directory: ${error.message}`;
  console.error(error);
});
