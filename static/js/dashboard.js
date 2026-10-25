// Draws all charts with Chart.js. Each chart only runs if its <canvas> exists on the page.

// ---------- Pollution trend (dashboard) ----------
let trendChart = null;
async function loadTrend(days) {
  const data = await (await fetch(`/api/trend?days=${days}`)).json();
  // Show a red dot only on anomaly days (null = no point)
  const anomalyPoints = data.pm25.map((v, i) => data.anomaly[i] ? v : null);
  if (trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById("trendChart"), {
    type: "line",
    data: { labels: data.dates, datasets: [
      { label: "PM2.5", data: data.pm25, borderColor: "#198754", pointRadius: 0, tension: 0.2 },
      { label: "7-day average", data: data.ma7, borderColor: "#fd7e14", borderDash: [5, 4], pointRadius: 0 },
      { label: "Unusual", data: anomalyPoints, borderColor: "red", backgroundColor: "red",
        showLine: false, pointRadius: 5 }
    ]},
    options: { scales: { x: { ticks: { maxTicksLimit: 10 } }, y: { title: { display: true, text: "µg/m³" } } } }
  });
}
if (document.getElementById("trendChart")) {
  loadTrend(90);
  document.getElementById("daysSelect").addEventListener("change", e => loadTrend(e.target.value));
}

// ---------- Predicted vs actual (dashboard) ----------
if (document.getElementById("predChart")) {
  fetch("/api/predictions").then(r => r.json()).then(d => {
    new Chart(document.getElementById("predChart"), {
      type: "line",
      data: { labels: d.dates, datasets: [
        { label: "Actual", data: d.actual, borderColor: "#0d6efd", pointRadius: 0 },
        { label: "Predicted", data: d.predicted, borderColor: "#dc3545", pointRadius: 0, borderDash: [4, 3] }
      ]},
      options: { scales: { x: { ticks: { maxTicksLimit: 10 } } } }
    });
  });
}

// ---------- Model comparison + feature importance (models page) ----------
if (document.getElementById("metricChart")) {
  fetch("/api/metrics").then(r => r.json()).then(m => {
    const names = Object.keys(m.results);
    new Chart(document.getElementById("metricChart"), {
      type: "bar",
      data: { labels: names, datasets: [
        { label: "MAE",  data: names.map(n => m.results[n].mae),  backgroundColor: "#198754" },
        { label: "RMSE", data: names.map(n => m.results[n].rmse), backgroundColor: "#fd7e14" }
      ]}
    });
    new Chart(document.getElementById("importanceChart"), {
      type: "bar",
      data: { labels: Object.keys(m.feature_importance),
              datasets: [{ label: "Importance", data: Object.values(m.feature_importance), backgroundColor: "#0d6efd" }] },
      options: { indexAxis: "y" }
    });
  });
}
