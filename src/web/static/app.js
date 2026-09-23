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
const riskEvent = document.querySelector("#risk-event");
const saveScenarioButton = document.querySelector("#save-scenario");
const exportReportButton = document.querySelector("#export-report");
const scenarioStatus = document.querySelector("#scenario-status");
const savedScenarios = document.querySelector("#saved-scenarios");

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
  result.append(grid); renderVisuals(result, data); result.append(element("div", "narrative", data.narrative));
  result.scrollIntoView({behavior: "smooth", block: "start"});
}

async function calculateScenario() {
  message.hidden = true; result.hidden = true; calculate.disabled = true;
  try {
    const response = await fetch("/api/score", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({items: selectedItems(), event: riskEvent.value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось рассчитать сценарий.");
    if (!data.valid) showMessage(data.reasons);
    else { lastResult = data; renderResult(data); renderRecommendations(data); }
  } catch (error) { showMessage([error.message]); }
  finally { calculate.disabled = false; }
}

async function init() {
  try {
    const response = await fetch("/api/catalogue");
    if (!response.ok) throw new Error("Каталог недоступен.");
    catalogue = await response.json(); populateEvents(); buildRows(); updateBudget(); renderSaved(); calculate.addEventListener("click", calculateScenario); saveScenarioButton.addEventListener("click", saveScenario); exportReportButton.addEventListener("click", exportReport);
  } catch (error) { showMessage([error.message]); }
}
init();

function svgNode(tag, attributes = {}, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderVisuals(container, data) {
  const section = element("section", "visuals");
  section.append(element("p", "eyebrow", "ГРАФИЧЕСКИЙ ОБЗОР"));
  section.append(element("h3", "visual-title", "Как сценарий меняет районы"));
  section.append(buildDistrictChart(data.districts));
  const explorer = element("div", "indicator-explorer");
  const heading = element("div", "visual-heading");
  heading.append(element("h3", "", "Показатели района"));
  const picker = document.createElement("select");
  picker.setAttribute("aria-label", "Выберите район для просмотра показателей");
  data.districts.forEach((district) => picker.add(new Option(district.name, district.id)));
  heading.append(picker);
  const detail = element("div", "indicator-detail");
  const redraw = () => renderIndicatorDetail(detail, data.districts.find((district) => district.id === picker.value));
  picker.addEventListener("change", redraw);
  redraw();
  explorer.append(heading, detail);
  section.append(explorer);
  container.append(section);
}

function buildDistrictChart(districts) {
  const figure = element("figure", "district-chart");
  const caption = element("figcaption", "", "Районные оценки: до и после выбранного сценария");
  const legend = element("div", "chart-legend");
  legend.append(element("span", "legend-before", "До"), element("span", "legend-after", "После"));
  const svg = svgNode("svg", {viewBox: "0 0 760 250", role: "img", "aria-label": "Сравнение районных оценок до и после сценария"});
  svg.append(svgNode("line", {x1: 138, y1: 25, x2: 138, y2: 224, class: "chart-axis"}));
  [0, 25, 50, 75, 100].forEach((value) => {
    const x = 138 + value * 5.6;
    svg.append(svgNode("line", {x1: x, y1: 25, x2: x, y2: 224, class: "chart-grid"}));
    svg.append(svgNode("text", {x, y: 242, class: "chart-tick", "text-anchor": "middle"}, value));
  });
  districts.forEach((district, index) => {
    const y = 33 + index * 38;
    svg.append(svgNode("text", {x: 128, y: y + 15, class: "chart-label", "text-anchor": "end"}, district.name));
    svg.append(svgNode("rect", {x: 138, y, width: district.before * 5.6, height: 12, class: "chart-bar chart-before"}));
    svg.append(svgNode("rect", {x: 138, y: y + 15, width: district.after * 5.6, height: 12, class: "chart-bar chart-after"}));
    svg.append(svgNode("text", {x: 704, y: y + 20, class: "chart-value"}, `${district.before.toFixed(1)} → ${district.after.toFixed(1)}`));
  });
  figure.append(caption, legend, svg);
  return figure;
}

function renderIndicatorDetail(target, district) {
  target.replaceChildren();
  const intro = element("p", "indicator-intro", `${district.name}: шкала 0–100, больше — лучше.`);
  const list = element("div", "indicator-list");
  district.indicators.forEach((indicator) => {
    const row = element("div", "indicator-row");
    const label = element("div", "indicator-label");
    label.append(element("b", "", indicator.id), element("span", indicator.delta ? "positive" : "", `${indicator.before.toFixed(1)} → ${indicator.after.toFixed(1)}`));
    const track = element("div", "indicator-track");
    const before = element("i", "indicator-before"); before.style.width = `${indicator.before}%`;
    const after = element("i", "indicator-after"); after.style.width = `${indicator.after}%`;
    track.append(before, after);
    row.append(label, track);
    list.append(row);
  });
  target.append(intro, list);
}

let lastResult = null;
function populateEvents() { catalogue.events.forEach((event) => riskEvent.add(new Option(event.name, event.id))); }
function saveScenario() {
  if (!lastResult || !lastResult.valid) { scenarioStatus.textContent = "Сначала рассчитайте допустимый сценарий."; return; }
  const saved = JSON.parse(localStorage.getItem("akim-scenarios") || "[]");
  saved.push({items: selectedItems(), event: riskEvent.value, score: lastResult.score, name: lastResult.event.name});
  localStorage.setItem("akim-scenarios", JSON.stringify(saved.slice(-6)));
  scenarioStatus.textContent = "Сценарий сохранён для сравнения в этом браузере."; renderSaved();
}
function renderSaved() {
  const saved = JSON.parse(localStorage.getItem("akim-scenarios") || "[]");
  savedScenarios.hidden = !saved.length; savedScenarios.replaceChildren(); if (!saved.length) return;
  savedScenarios.append(element("h3", "", "Сравнение сохранённых сценариев"));
  const list = element("div", "scenario-list");
  saved.forEach((item, index) => list.append(element("div", "scenario-row", "#" + (index + 1) + " · " + item.name + " · Score " + item.score.toFixed(2))));
  savedScenarios.append(list);
}
function exportReport() {
  if (!lastResult || !lastResult.valid) { scenarioStatus.textContent = "Для экспорта нужен рассчитанный допустимый сценарий."; return; }
  const lines = ["# Отчёт «Аким на 5 часов»", "", "Событие: " + lastResult.event.name, "Score: " + lastResult.score.toFixed(2), "Бюджет: " + lastResult.budget_used + "/100", "", "## Выбранные меры"].concat(selectedItems().map((item) => "- " + item.measure_id + (item.district ? ": " + item.district : ""))).concat(["", lastResult.narrative]);
  const url = URL.createObjectURL(new Blob([lines.join("\n")], {type: "text/markdown;charset=utf-8"}));
  const link = document.createElement("a"); link.href = url; link.download = "akim-scenario-report.md"; link.click(); URL.revokeObjectURL(url);
  scenarioStatus.textContent = "Markdown-отчёт подготовлен для скачивания.";
}
function renderRecommendations(data) {
  if (!data.recommendations || !data.recommendations.length) return;
  const box = element("section", "recommendations");
  box.append(element("h3", "", "Варианты улучшения"), element("p", "", "Одношаговые замены, найденные детерминированной моделью."));
  const list = element("ul");
  data.recommendations.forEach((entry) => list.append(element("li", "", "Score " + entry.score.toFixed(2) + ": " + entry.items.map((item) => item.measure_id + (item.district ? "→" + item.district : "")).join(", "))));
  box.append(list); result.append(box);
}

const language = document.querySelector("#language");
const translations = {
  ru: {tag:"ГОРОДСКАЯ ЛАБОРАТОРИЯ · 8 КВАРТАЛОВ", intro:"Соберите пять управленческих решений и увидьте их проверяемый эффект на районы Астаны.", scenario:"ВАШ СЦЕНАРИЙ", decisions:"Пять решений", calculate:"Рассчитать сценарий →", how:"КАК ЭТО РАБОТАЕТ", honest:"Честная модель, а не чёрный ящик"},
  kk: {tag:"ҚАЛАЛЫҚ ЗЕРТХАНА · 8 ТОҚСАН", intro:"Бес басқарушылық шешімді таңдап, олардың Астана аудандарына тексерілетін әсерін көріңіз.", scenario:"СІЗДІҢ СЦЕНАРИЙІҢІЗ", decisions:"Бес шешім", calculate:"Сценарийді есептеу →", how:"БҰЛ ҚАЛАЙ ЖҰМЫС ІСТЕЙДІ", honest:"Ашық модель, жабық қорап емес"},
  en: {tag:"CITY LAB · 8 QUARTERS", intro:"Choose five city decisions and see their auditable impact on Astana districts.", scenario:"YOUR SCENARIO", decisions:"Five decisions", calculate:"Calculate scenario →", how:"HOW IT WORKS", honest:"A transparent model, not a black box"}
};
function applyLanguage() {
  const copy = translations[language.value]; document.documentElement.lang = language.value;
  document.querySelector(".hero .eyebrow").textContent = copy.tag;
  document.querySelector(".hero > p:last-child").textContent = copy.intro;
  document.querySelector(".builder .eyebrow").textContent = copy.scenario;
  document.querySelector("#builder-heading").textContent = copy.decisions;
  calculate.textContent = copy.calculate;
  document.querySelector(".how .eyebrow").textContent = copy.how;
  document.querySelector(".how h2").textContent = copy.honest;
  localStorage.setItem("akim-language", language.value);
}
language.value = localStorage.getItem("akim-language") || "ru";
language.addEventListener("change", applyLanguage);
applyLanguage();
