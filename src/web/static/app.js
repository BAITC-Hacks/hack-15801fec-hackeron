const directions = {transport: "Транспорт", ecology: "Экология", social: "Соцсфера", safety: "Безопасность", services: "Сервисы"};
let catalogue;

const decisions = document.querySelector("#decisions");
const template = document.querySelector("#decision-template");
const budget = document.querySelector("#budget");
const fill = document.querySelector("#budget-fill");
const budgetStatus = document.querySelector("#budget-status");
const message = document.querySelector("#message");
const result = document.querySelector("#result");
const calculate = document.querySelector("#calculate");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function buildRows() {
  for (let index = 0; index < catalogue.required_decisions; index += 1) {
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector(".decision");
    row.querySelector(".number").textContent = `0${index + 1}`;
    const measureSelect = row.querySelector(".measure");
    const districtSelect = row.querySelector(".district");
    for (const measure of catalogue.measures) {
      const option = new Option(`${measure.id} · ${measure.name}`, measure.id);
      measureSelect.add(option);
    }
    for (const district of catalogue.districts) {
      districtSelect.add(new Option(district.name, district.id));
    }
    districtSelect.disabled = true;
    measureSelect.addEventListener("change", () => updateRow(row));
    districtSelect.addEventListener("change", updateBudget);
    decisions.append(fragment);
  }
}

function updateRow(row) {
  const selected = catalogue.measures.find((measure) => measure.id === row.querySelector(".measure").value);
  const district = row.querySelector(".district");
  const meta = row.querySelector(".measure-meta");
  if (!selected) {
    district.value = "";
    district.disabled = true;
    meta.textContent = "Выберите мероприятие, чтобы увидеть стоимость и эффект.";
  } else {
    const isDistrict = selected.type === "district";
    district.disabled = !isDistrict;
    if (!isDistrict) district.value = "";
    const effects = Object.entries(selected.effects).map(([indicator, delta]) => `${indicator} ${delta > 0 ? "+" : ""}${delta}`).join(", ");
    meta.textContent = `${directions[selected.direction]} · ${isDistrict ? "район" : "город"} · ${selected.cost} ед. · лаг ${selected.lag} кв. · ${effects}`;
  }
  updateBudget();
}

function selectedItems() {
  return [...document.querySelectorAll(".decision")].map((row) => {
    const measure = catalogue.measures.find((item) => item.id === row.querySelector(".measure").value);
    return measure ? {
      measure_id: measure.id,
      district: measure.type === "district" ? (row.querySelector(".district").value || null) : null,
    } : null;
  }).filter(Boolean);
}

function updateBudget() {
  const selected = selectedItems();
  const spent = selected.reduce((sum, item) => sum + catalogue.measures.find((measure) => measure.id === item.measure_id).cost, 0);
  budget.textContent = `${spent} / ${catalogue.budget}`;
  fill.style.width = `${Math.min(spent / catalogue.budget * 100, 100)}%`;
  fill.style.background = spent > catalogue.budget ? "#ff957d" : "var(--lime)";
  budgetStatus.textContent = spent > catalogue.budget ? "Бюджет превышен — измените набор." : `Осталось: ${catalogue.budget - spent} ед. · выбрано: ${selected.length}/5.`;
}

function showMessage(reasons) {
  message.hidden = false;
  message.replaceChildren(element("strong", "", "Сценарий пока нельзя рассчитать."));
  const list = element("ul");
  reasons.forEach((reason) => list.append(element("li", "", reason)));
  message.append(list);
}

function renderResult(data) {
  result.hidden = false;
  result.replaceChildren();
  const header = element("div", "result-header");
  const scoreBlock = element("div");
  scoreBlock.append(element("p", "eyebrow", "ASTANA QUALITY OF LIFE SCORE"));
  scoreBlock.append(element("div", "score", data.score.toFixed(2)));
  scoreBlock.append(element("p", "score-note", `${data.score_delta >= 0 ? "+" : ""}${data.score_delta.toFixed(2)} к базовому сценарию · бюджет ${data.budget_used}/100`));
  const stats = element("div", "stats");
  [["Среднее по городу", data.d_avg], ["Минимум района", data.min_district], ["Критических", data.n_crit]].forEach(([label, value]) => {
    const stat = element("div"); stat.append(element("span", "", label), element("b", "", typeof value === "number" && label !== "Критических" ? value.toFixed(2) : String(value))); stats.append(stat);
  });
  header.append(scoreBlock, stats); result.append(header);
  result.append(element("p", "eyebrow", "ИЗМЕНЕНИЯ ПО РАЙОНАМ"));
  const grid = element("div", "district-grid");
  data.districts.forEach((district) => {
    const card = element("article", "district");
    card.append(element("h3", "", district.name), element("div", "district-score", `${district.before.toFixed(2)} → ${district.after.toFixed(2)}`));
    const changes = district.changes.length ? district.changes.map((change) => `${change.indicator} ${change.delta >= 0 ? "+" : ""}${change.delta.toFixed(2)}`).join(" · ") : "Без изменений";
    card.append(element("p", "changes", changes)); grid.append(card);
  });
  result.append(grid, element("div", "narrative", data.narrative));
  result.scrollIntoView({behavior: "smooth", block: "start"});
}

async function calculateScenario() {
  message.hidden = true; result.hidden = true; calculate.disabled = true;
  try {
    const response = await fetch("/api/score", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({items: selectedItems()})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось рассчитать сценарий.");
    if (!data.valid) showMessage(data.reasons);
    else renderResult(data);
  } catch (error) { showMessage([error.message]); }
  finally { calculate.disabled = false; }
}

async function init() {
  try {
    const response = await fetch("/api/catalogue");
    if (!response.ok) throw new Error("Каталог недоступен.");
    catalogue = await response.json(); buildRows(); updateBudget(); calculate.addEventListener("click", calculateScenario);
  } catch (error) { showMessage([error.message]); }
}
init();
