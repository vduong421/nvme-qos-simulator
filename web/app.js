const summaryGrid = document.getElementById("summaryGrid");
const workloadGrid = document.getElementById("workloadGrid");
const workloadTableBody = document.getElementById("workloadTableBody");
const recommendations = document.getElementById("recommendations");
const insightList = document.getElementById("insightList");
const deviceDetails = document.getElementById("deviceDetails");
const runButton = document.getElementById("runButton");
const runStatus = document.getElementById("runStatus");
const lastUpdated = document.getElementById("lastUpdated");

function formatNumber(value) {
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function setStatus(text, mode) {
  runStatus.textContent = text;
  runStatus.className = `status-badge ${mode}`;
}

function statCard(label, value, hint, trend) {
  return `
    <article class="stat">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
      <div class="mini">${hint}</div>
      <div class="stat-trend">${trend}</div>
    </article>
  `;
}

function workloadCard(item) {
  const saturationPct = Math.min(100, item.saturation * 100);
  return `
    <article class="workload-card">
      <h3>${item.name}</h3>
      <div class="mini">Achieved IOPS: ${formatNumber(item.achieved_iops)}</div>
      <div class="mini">Bandwidth: ${item.bandwidth_gbps} Gbps</div>
      <div class="mini">Latency: p50 ${item.p50_us} us, p95 ${item.p95_us} us, p99 ${item.p99_us} us</div>
      <div class="mini">Coverage: ${item.test_coverage_pct}% | Pass rate: ${item.pass_rate_pct}% | Triage: ${item.triage_label}</div>
      <div class="bar"><span style="width:${saturationPct}%"></span></div>
      <div class="mini">Saturation: ${saturationPct.toFixed(1)}%</div>
    </article>
  `;
}

function insightCard(title, value, note) {
  return `
    <article class="insight-card">
      <div class="insight-title">${title}</div>
      <div class="insight-value">${value}</div>
      <div class="mini">${note}</div>
    </article>
  `;
}

function detailCard(label, value) {
  return `
    <article class="detail-card">
      <div class="detail-label">${label}</div>
      <div class="detail-value">${value}</div>
    </article>
  `;
}

function buildInsights(data) {
  const worst = data.workloads.reduce((max, item) => (item.p99_us > max.p99_us ? item : max), data.workloads[0]);
  const busiest = data.workloads.reduce((max, item) => (item.saturation > max.saturation ? item : max), data.workloads[0]);
  const weakestCoverage = data.workloads.reduce((min, item) => (item.test_coverage_pct < min.test_coverage_pct ? item : min), data.workloads[0]);
  const qosClass = data.summary.worst_case_p99_us < 500 ? "Healthy QoS envelope" : "Tail-latency risk emerging";

  insightList.innerHTML = [
    insightCard("Hotspot Workload", worst.name, `Highest p99 latency at ${worst.p99_us} us`),
    insightCard("Most Saturated Path", busiest.name, `Controller utilization at ${(busiest.saturation * 100).toFixed(1)}%`),
    insightCard("Coverage Gap", weakestCoverage.name, `Lowest validation coverage at ${weakestCoverage.test_coverage_pct}%`),
    insightCard("QoS Assessment", qosClass, data.ai_triage_summary),
  ].join("");
}

function buildDeviceDetails(device) {
  deviceDetails.innerHTML = [
    detailCard("Device", device.name),
    detailCard("PCIe Generation", `Gen${device.pcie_generation}`),
    detailCard("Channels", String(device.channels)),
    detailCard("Max Queue Depth", String(device.max_queue_depth)),
    detailCard("Overprovisioning", `${device.overprovisioning_pct}%`),
  ].join("");
}

function buildTable(workloads) {
  workloadTableBody.innerHTML = workloads
    .map(
      (item) => `
        <tr>
          <td>${item.name}</td>
          <td>${formatNumber(item.achieved_iops)}</td>
          <td>${item.bandwidth_gbps} Gbps</td>
          <td>${item.p50_us} us</td>
          <td>${item.p95_us} us</td>
          <td>${item.p99_us} us</td>
          <td>${(item.saturation * 100).toFixed(1)}%</td>
          <td>${item.test_coverage_pct}%</td>
          <td>${item.triage_label}</td>
        </tr>
      `,
    )
    .join("");
}

async function runScenario() {
  setStatus("Running", "running");
  runButton.disabled = true;

  try {
    const response = await fetch("/api/run");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();

    summaryGrid.innerHTML = [
      statCard("Total IOPS", formatNumber(data.summary.total_achieved_iops), "Aggregate mixed-workload throughput", "Use this in customer sizing conversations"),
      statCard("Total Bandwidth", `${data.summary.total_bandwidth_gbps} Gbps`, "Estimated delivered bandwidth", "Helps frame fabric and host-path impact"),
      statCard("Average Saturation", `${(data.summary.average_saturation * 100).toFixed(1)}%`, "Controller pressure indicator", data.summary.average_saturation > 0.85 ? "Near saturation" : "Operating with headroom"),
      statCard("Worst-Case p99", `${data.summary.worst_case_p99_us} us`, "Tail-latency bound", data.summary.worst_case_p99_us > 700 ? "Needs mitigation" : "Within expected range"),
      statCard("Validation Coverage", `${data.summary.validation_coverage_pct}%`, "Regression visibility across workloads", data.summary.validation_coverage_pct < 85 ? "Coverage gap" : "Coverage healthy"),
      statCard("Pass Rate", `${data.summary.pass_rate_pct}%`, "Recent execution success", data.summary.pass_rate_pct < 97 ? "Triage failures" : "Execution stable"),
      statCard("Stalest Dataset", `${data.summary.stalest_dataset_hours} hrs`, "Oldest workload evidence in the suite", data.summary.stalest_dataset_hours > 24 ? "Refresh scenario" : "Data current"),
    ].join("");

    workloadGrid.innerHTML = data.workloads.map(workloadCard).join("");
    buildTable(data.workloads);
    buildInsights(data);
    buildDeviceDetails(data.device);
    recommendations.innerHTML = [
      `<li>${data.ai_triage_summary}</li>`,
      ...data.recommendations.map((item) => `<li>${item}</li>`),
    ].join("");

    setStatus("Completed", "success");
    lastUpdated.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    setStatus("Error", "error");
    lastUpdated.textContent = `Failed: ${error.message}`;
  } finally {
    runButton.disabled = false;
  }
}

runButton.addEventListener("click", runScenario);
runScenario();
