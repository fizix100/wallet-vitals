const form = document.querySelector("#analysis-form");
const basePath = document.body.dataset.basePath || "";
const reportElement = document.querySelector("#report");
const loading = document.querySelector("#loading");
const errorElement = document.querySelector("#error");
let activeReportId = null;

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});
const compact = new Intl.NumberFormat("en-US", { maximumFractionDigits: 5 });

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function shorten(value, start = 8, end = 6) {
  return `${value.slice(0, start)}…${value.slice(-end)}`;
}

function formatSignedMoney(value) {
  if (value === null || value === undefined) return "—";
  const number = Number(value);
  return `${number >= 0 ? "+" : "−"}${money.format(Math.abs(number))}`;
}

function setBusy(isBusy) {
  loading.hidden = !isBusy;
  form.querySelector("button").disabled = isBusy;
  form.querySelector("button span").textContent = isBusy ? "Analyzing…" : "Run risk check";
}

function showError(message) {
  errorElement.textContent = message;
  errorElement.hidden = false;
}

function renderReport(report) {
  activeReportId = report.report_id;
  document.querySelector("#report-address").textContent = shorten(report.address, 10, 8);
  const severity = document.querySelector("#severity");
  severity.textContent = report.severity.replace("_", " ");
  severity.className = `severity ${report.severity}`;
  document.querySelector("#health-factor").textContent = report.health_factor ?? "No debt";
  document.querySelector("#buffer").textContent = report.liquidation_buffer_pct === null ? "N/A" : `${report.liquidation_buffer_pct}%`;
  document.querySelector("#collateral").textContent = money.format(Number(report.total_collateral_usd));
  document.querySelector("#debt").textContent = money.format(Number(report.total_debt_usd));
  document.querySelector("#narrative").textContent = report.narrative;
  document.querySelector("#narrative-mode").textContent = report.narrative_mode === "openai" ? "AI · evidence locked" : "deterministic";

  document.querySelector("#stress-ladder").innerHTML = report.stress_ladder.map((item) => `
    <div><span>${Math.abs(item.collateral_shock_pct)}% decline</span><strong>${item.health_factor ?? "N/A"}</strong><i class="dot ${escapeHtml(item.severity)}"></i></div>
  `).join("");

  const delta = report.risk_delta;
  const deltaElement = document.querySelector("#delta");
  if (delta.status === "comparable") {
    deltaElement.innerHTML = `
      <div><span>Collateral</span><strong>${formatSignedMoney(delta.collateral_usd_change)}</strong></div>
      <div><span>Debt</span><strong>${formatSignedMoney(delta.debt_usd_change)}</strong></div>
      <div><span>Health factor</span><strong>${delta.health_factor_change === null ? "—" : compact.format(Number(delta.health_factor_change))}</strong></div>
      <small>Block ${delta.previous_block_number} → ${delta.current_block_number}</small>`;
  } else {
    deltaElement.innerHTML = `<p>${delta.status === "no_baseline" ? "First evidence snapshot saved. Run this address again after a later block to unlock a comparable delta." : "Previous evidence was not comparable with this deployment and rules version."}</p>`;
  }

  document.querySelector("#positions").innerHTML = report.assets.length ? report.assets.map((asset) => `
    <tr><td><b>${escapeHtml(asset.symbol)}</b><small>${shorten(asset.address)}</small></td><td>${compact.format(Number(asset.supply))}</td><td>${compact.format(Number(asset.debt))}</td><td>${money.format(Number(asset.price_usd))}</td><td>${(Number(asset.liquidation_threshold_bps) / 100).toFixed(2)}%${asset.e_mode_applied ? " · eMode" : ""}</td></tr>
  `).join("") : `<tr><td colspan="5">No active Aave supply or debt positions were found.</td></tr>`;

  const receipt = report.evidence_receipt;
  const onchain = receipt.onchain_evidence;
  document.querySelector("#verification-status").textContent = onchain?.verification === "matched"
    ? `Aave account cross-check passed · block ${receipt.block_number} · read-only`
    : "No onchain account cross-check is available for this report.";
  document.querySelector("#report-warnings").textContent = (report.warnings || []).join(" ");
  document.querySelector("#receipt-content").innerHTML = `
    <dl><dt>Position provider</dt><dd>The Graph</dd><dt>Network</dt><dd>${escapeHtml(receipt.network)}</dd><dt>Block</dt><dd>${receipt.block_number}</dd><dt>Block time</dt><dd>${escapeHtml(new Date(receipt.block_timestamp).toLocaleString())}</dd><dt>Queried</dt><dd>${escapeHtml(new Date(receipt.queried_at).toLocaleString())}</dd><dt>Deployment</dt><dd><code>${escapeHtml(receipt.deployment)}</code></dd><dt>Subgraph ID</dt><dd><code>${escapeHtml(receipt.subgraph_id)}</code></dd><dt>Rules</dt><dd>${escapeHtml(receipt.rules_version)}</dd></dl>
    ${onchain ? `<h4>Same-block Aave contract evidence</h4><dl><dt>Price source</dt><dd>Aave oracle · getAssetPrice(address)</dd><dt>Oracle</dt><dd><code>${escapeHtml(onchain.oracle_address)}</code></dd><dt>Pool</dt><dd><code>${escapeHtml(onchain.pool_address)}</code></dd><dt>Block hash</dt><dd><code>${escapeHtml(onchain.block_hash)}</code></dd><dt>Contract health factor</dt><dd>${escapeHtml(onchain.health_factor ?? "No debt")}</dd><dt>Account cross-check</dt><dd>${escapeHtml(onchain.verification)} · bounded rounding tolerance</dd></dl>` : ""}
    <h4>Scenario assumptions</h4><ul>${receipt.scenario_assumptions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h4>Evidence references</h4><ul>${receipt.evidence_refs.map((item) => `<li><code>${escapeHtml(item)}</code></li>`).join("") || "<li>No active position references.</li>"}</ul>`;

  document.querySelector("#explanation").hidden = true;
  reportElement.hidden = false;
  reportElement.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadReport(reportId) {
  errorElement.hidden = true;
  setBusy(true);
  try {
    const response = await fetch(`${basePath}/api/reports/${encodeURIComponent(reportId)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Report could not be loaded.");
    renderReport(payload);
  } catch (error) {
    showError(error.message || "Report could not be loaded.");
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorElement.hidden = true;
  reportElement.hidden = true;
  setBusy(true);
  try {
    const response = await fetch(`${basePath}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: form.address.value.trim() }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Analysis failed.");
    renderReport(payload);
  } catch (error) {
    showError(error.message || "Analysis failed.");
  } finally {
    setBusy(false);
  }
});

document.querySelectorAll("[data-intent]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!activeReportId) return;
    const output = document.querySelector("#explanation");
    output.hidden = false;
    output.textContent = "Reading the evidence receipt…";
    try {
      const response = await fetch(`${basePath}/api/reports/${encodeURIComponent(activeReportId)}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intent: button.dataset.intent }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Explanation failed.");
      output.textContent = `${payload.mode === "deterministic" ? "Deterministic" : "AI"} · ${payload.answer}`;
    } catch (error) {
      output.textContent = error.message || "Explanation failed.";
    }
  });
});

document.querySelector("#share-report").addEventListener("click", async (event) => {
  if (!activeReportId) return;
  const button = event.currentTarget;
  const url = `${window.location.origin}${basePath}/reports/${encodeURIComponent(activeReportId)}`;
  try {
    await navigator.clipboard.writeText(url);
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = "Copy report link"; }, 1600);
  } catch {
    showError(`Copy this report link: ${url}`);
  }
});

const initialReportId = document.body.dataset.reportId;
if (initialReportId) loadReport(initialReportId);
