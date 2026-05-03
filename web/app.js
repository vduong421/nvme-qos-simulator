const summaryGrid = document.getElementById("summaryGrid");
const workloadGrid = document.getElementById("workloadGrid");
const workloadTableBody = document.getElementById("workloadTableBody");
const recommendations = document.getElementById("recommendations");
const insightList = document.getElementById("insightList");
const deviceDetails = document.getElementById("deviceDetails");
const runButton = document.getElementById("runButton");
const runStatus = document.getElementById("runStatus");
const lastUpdated = document.getElementById("lastUpdated");
const aiAnalyst = document.getElementById("aiAnalyst");
const chatInput = document.getElementById("chatInput");
const askButton = document.getElementById("askButton");
const chatStatus = document.getElementById("chatStatus");
const chatAnswer = document.getElementById("chatAnswer");
const latencyChart = document.getElementById("latencyChart");
const saturationChart = document.getElementById("saturationChart");
const bandwidthChart = document.getElementById("bandwidthChart");

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
  const qosClass = data.summary.worst_case_p99_us < 500 ? "Healthy QoS envelope" : "Tail-latency risk emerging";

  insightList.innerHTML = [
    insightCard("Hotspot Workload", worst.name, `Highest p99 latency at ${worst.p99_us} us`),
    insightCard("Most Saturated Path", busiest.name, `Controller utilization at ${(busiest.saturation * 100).toFixed(1)}%`),
    insightCard("QoS Assessment", qosClass, "Derived from the current worst-case p99 profile"),
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

function renderChart(target, items, field, suffix) {
  const top = [...items].sort((a, b) => b[field] - a[field]).slice(0, 8);
  const max = Math.max(...top.map((item) => item[field]), 1);
  target.innerHTML = top
    .map((item) => `
      <div class="chart-bar">
        <div>${item.name}</div>
        <div class="chart-track"><div class="chart-fill" style="width:${(item[field] / max) * 100}%"></div></div>
        <div>${formatNumber(item[field])}${suffix}</div>
      </div>
    `)
    .join("");
}

function renderAiAnalyst(data) {
  const ai = data.ai_copilot || {};
  aiAnalyst.innerHTML = `
    <b>Result:</b> ${ai.result || "NVMe QoS simulation complete."}<br><br>
    <b>Answer:</b> ${ai.answer || "Deterministic simulator generated workload-level QoS signals."}<br><br>
    <b>Evidence:</b> ${ai.evidence || "Uses achieved IOPS, bandwidth, saturation, and latency percentiles."}<br><br>
    <b>Next Action:</b> ${ai.next_action || "Review top p99 and saturation hotspots."}<br><br>
    <b>Recommendation:</b> ${ai.recommendation || data.recommendations[0] || "Tune queue depth and channels."}<br><br>
    <b>Decision:</b> ${ai.decision || "Use simulation results for design review."}
  `;
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
    ].join("");

    renderAiAnalyst(data);
    workloadGrid.innerHTML = data.workloads.slice(0, 12).map(workloadCard).join("");
    buildTable(data.workloads);
    buildInsights(data);
    buildDeviceDetails(data.device);
    renderChart(latencyChart, data.workloads, "p99_us", " us");
    renderChart(saturationChart, data.workloads, "saturation", "");
    renderChart(bandwidthChart, data.workloads, "bandwidth_gbps", " Gbps");
    recommendations.innerHTML = data.recommendations.map((item) => `<li>${item}</li>`).join("");

    setStatus("Completed", "success");
    lastUpdated.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    setStatus("Error", "error");
    lastUpdated.textContent = `Failed: ${error.message}`;
  } finally {
    runButton.disabled = false;
  }
}

async function askLocalAi() {
  const q = chatInput.value.trim();
  if (!q) {
    chatAnswer.textContent = "Enter a question.";
    return;
  }

  chatStatus.textContent = "Running Local AI...";
  chatStatus.style.color = "var(--warn)";
  chatAnswer.innerHTML = "";

  try {
    const response = await fetch(`/api/chat?q=${encodeURIComponent(q)}`);
    const data = await response.json();
    chatStatus.textContent = "Local AI Finished";
    chatStatus.style.color = "var(--good)";
    chatAnswer.innerHTML = `
      <b>Answer:</b> ${data.answer}<br><br>
      <b>Evidence:</b> ${data.evidence}<br><br>
      <b>Next Action:</b> ${data.next_action}<br><br>
      <b>Recommendation:</b> ${data.recommendation}<br><br>
      <b>Decision:</b> ${data.decision}
    `;
  } catch (error) {
    chatStatus.textContent = "Local AI Failed";
    chatStatus.style.color = "var(--bad)";
    chatAnswer.textContent = "Fallback failed to load. Run the server again.";
  }
}

document.querySelectorAll("[data-q]").forEach((button) => {
  button.addEventListener("click", () => {
    chatInput.value = button.dataset.q;
  });
});

askButton.addEventListener("click", askLocalAi);
runButton.addEventListener("click", runScenario);
runScenario();
