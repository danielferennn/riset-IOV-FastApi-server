MAP_HTML = """
<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IOV Node Map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      font-family: Arial, Helvetica, sans-serif;
      color: #172026;
      background: #eef2f3;
    }

    .app-shell {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      width: 100vw;
      height: 100vh;
      min-height: 0;
    }

    .sidebar {
      grid-column: 2;
      grid-row: 1;
      min-width: 0;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 16px;
      border-left: 1px solid #d6dddf;
      background: #f8faf9;
    }

    .map-wrap {
      grid-column: 1;
      grid-row: 1;
    }

    .sidebar h1 {
      margin: 0 0 6px;
      font-size: 20px;
      line-height: 1.2;
    }

    .status {
      margin-bottom: 14px;
      font-size: 13px;
      line-height: 1.4;
      color: #58666d;
    }

    .sidebar-tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin: 8px 0 12px;
    }

    .sidebar-tab {
      border: 1px solid #cbd5d8;
      border-radius: 6px;
      padding: 8px 6px;
      background: #ffffff;
      color: #58666d;
      cursor: pointer;
      font: inherit;
      font-size: 12px;
      font-weight: 700;
    }

    .sidebar-tab.active {
      border-color: #2d8f6f;
      background: #e9f7ef;
      color: #146c43;
    }

    .sidebar-panel {
      display: none;
      min-width: 0;
      min-height: 0;
      overflow-y: auto;
    }

    .sidebar-panel.active {
      display: block;
    }

    .node-list {
      display: grid;
      gap: 10px;
    }

    .detail-section-title {
      margin-bottom: 6px;
      font-size: 12px;
      font-weight: 700;
      color: #40515a;
      text-transform: uppercase;
    }

    .detail-grid {
      display: grid;
      grid-template-columns: 110px minmax(0, 1fr);
      gap: 5px 10px;
      font-size: 12px;
      line-height: 1.45;
    }

    .detail-empty {
      color: #69757c;
      font-size: 12px;
      line-height: 1.45;
    }

    .status-message-item {
      min-width: 0;
      margin-bottom: 8px;
      border: 1px solid #e1e7e9;
      border-radius: 6px;
      padding: 8px;
      background: #fbfefd;
    }

    .status-message-item:last-child {
      margin-bottom: 0;
    }

    .status-message-item .detail-grid {
      grid-template-columns: 82px minmax(0, 1fr);
    }

    .status-message-item .value {
      overflow-wrap: break-word;
      word-break: normal;
    }

    .detail-content {
      min-width: 0;
    }

    .inline-detail {
      margin-top: 10px;
      border-top: 1px solid #e1e7e9;
      padding-top: 10px;
    }

    .node {
      width: 100%;
      border: 1px solid #d6dddf;
      border-radius: 8px;
      background: #ffffff;
      padding: 10px;
      cursor: pointer;
    }

    .node.selected {
      border-color: #2d8f6f;
      box-shadow: 0 0 0 2px rgba(45, 143, 111, 0.16);
    }

    .node:hover {
      border-color: #8ab9aa;
      background: #fbfefd;
    }

    .node:focus-visible {
      outline: 3px solid rgba(45, 143, 111, 0.35);
      outline-offset: 2px;
    }

    .node.has-gps {
      cursor: pointer;
    }

    .node-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }

    .node-id {
      min-width: 0;
      font-weight: 700;
      font-size: 14px;
      overflow-wrap: anywhere;
    }

    .badge {
      flex: 0 0 auto;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      background: #e9f7ef;
      color: #146c43;
      white-space: nowrap;
    }

    .badge.missing {
      background: #f1f3f5;
      color: #69757c;
    }

    .badge.message-badge {
      background: #fff0c2;
      color: #7a5600;
    }

    .kv {
      display: grid;
      grid-template-columns: 96px minmax(0, 1fr);
      gap: 4px 8px;
      font-size: 12px;
      line-height: 1.4;
    }

    .key {
      color: #6b7780;
    }

    .value {
      min-width: 0;
      color: #172026;
      overflow-wrap: anywhere;
    }

    .map-wrap {
      position: relative;
      min-width: 0;
      min-height: 0;
      height: 100vh;
      background: #dfe7ea;
    }

    #map {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      min-height: 320px;
      z-index: 1;
    }

    .map-message {
      position: absolute;
      left: 16px;
      right: 16px;
      bottom: 16px;
      z-index: 500;
      display: none;
      max-width: 520px;
      border: 1px solid #d6dddf;
      border-radius: 8px;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.94);
      color: #172026;
      font-size: 13px;
      line-height: 1.4;
      box-shadow: 0 6px 20px rgba(23, 32, 38, 0.12);
    }

    .leaflet-popup-content {
      margin: 0;
      overflow-wrap: anywhere;
    }

    .leaflet-popup-content-wrapper {
      border-radius: 8px;
      padding: 0;
      box-shadow: 0 10px 28px rgba(23, 32, 38, 0.22);
    }

    .popup-panel {
      width: 292px;
      max-width: min(292px, calc(100vw - 40px));
      padding: 12px;
      color: #172026;
    }

    .popup-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 11px;
    }

    .popup-title {
      min-width: 0;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }

    .popup-type {
      flex: 0 0 auto;
      border-radius: 4px;
      padding: 3px 6px;
      background: #edf4f1;
      color: #1d6955;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .popup-section {
      border-top: 1px solid #e1e7e9;
      padding-top: 10px;
    }

    .popup-section + .popup-section {
      margin-top: 10px;
    }

    .popup-section-divider {
      margin: 8px 0;
      border-top: 1px solid #e3e9eb;
    }

    .popup-section-title {
      margin-bottom: 7px;
      color: #5c6a71;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .popup-metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }

    .popup-metric {
      min-width: 0;
      border: 1px solid #e3e9eb;
      border-radius: 5px;
      padding: 7px 8px;
      background: #f8faf9;
    }

    .popup-metric-label {
      margin-bottom: 2px;
      color: #69777e;
      font-size: 10px;
      line-height: 1.2;
    }

    .popup-metric-value {
      color: #172026;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }

    .popup-footer {
      margin-top: 7px;
      color: #69777e;
      font-size: 10px;
      line-height: 1.35;
    }

    .popup-empty {
      color: #69777e;
      font-size: 12px;
      line-height: 1.4;
    }

    .node-marker {
      width: 44px;
      height: 44px;
      border: 2px solid #ffffff;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 18px rgba(23, 32, 38, 0.28);
    }

    .node-marker svg {
      width: 28px;
      height: 28px;
      display: block;
      stroke: #ffffff;
      fill: none;
      stroke-width: 2.4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .node-marker.raspi {
      background: #216e5a;
    }

    .node-marker.phone {
      background: transparent;
      border: 0;
      border-radius: 0;
      box-shadow: none;
    }

    .node-marker.phone svg {
      width: 34px;
      height: 34px;
      stroke: #111111;
      stroke-width: 2.8;
      filter: drop-shadow(0 2px 2px rgba(255, 255, 255, 0.95)) drop-shadow(0 4px 8px rgba(23, 32, 38, 0.28));
    }

    .node-marker.active {
      box-shadow: 0 0 0 4px rgba(45, 143, 111, 0.24), 0 8px 18px rgba(23, 32, 38, 0.28);
      transform: scale(1.08);
    }

    .node-marker.phone.active {
      box-shadow: none;
      transform: scale(1.16);
    }

    .report-marker {
      width: 30px;
      height: 30px;
      border: 3px solid #ffffff;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      background: #c2410c;
      color: #ffffff;
      font-size: 15px;
      font-weight: 700;
      line-height: 24px;
      text-align: center;
      box-shadow: 0 5px 12px rgba(23, 32, 38, 0.3);
    }

    .report-marker span {
      display: block;
      transform: rotate(45deg);
    }

    .report-photo {
      display: block;
      width: 100%;
      max-height: 160px;
      margin-top: 8px;
      border-radius: 6px;
      object-fit: cover;
    }

    .report-log {
      margin-top: 18px;
      border-top: 1px solid #d6dddf;
      padding-top: 14px;
    }

    .report-log h2 {
      margin: 0 0 4px;
      font-size: 15px;
    }

    .report-log-help {
      margin: 0 0 10px;
      color: #69777e;
      font-size: 11px;
      line-height: 1.4;
    }

    .report-list {
      display: grid;
      gap: 8px;
    }

    .report-list-message {
      color: #69777e;
      font-size: 12px;
      line-height: 1.4;
    }

    .report-item {
      border: 1px solid #d6dddf;
      border-left: 4px solid #c2410c;
      border-radius: 6px;
      padding: 9px;
      background: #ffffff;
    }

    .report-item-title {
      color: #172026;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.35;
    }

    .report-item-meta,
    .report-item-description {
      margin-top: 4px;
      color: #69777e;
      font-size: 11px;
      line-height: 1.4;
    }

    .report-item-description {
      color: #40515a;
      overflow-wrap: anywhere;
    }

    .marker-wrap {
      position: relative;
      width: 44px;
      height: 58px;
    }

    .asset-marker-wrap {
      position: relative;
      width: 44px;
      height: 58px;
    }

    .asset-marker-wrap img {
      display: block;
      width: 44px;
      height: 44px;
      object-fit: contain;
      filter: drop-shadow(0 5px 8px rgba(23, 32, 38, 0.28));
    }

    .marker-status-badge {
      position: absolute;
      top: -4px;
      right: -3px;
      min-width: 18px;
      height: 18px;
      border: 2px solid #ffffff;
      border-radius: 999px;
      padding: 0 4px;
      background: #d97706;
      color: #ffffff;
      font-size: 10px;
      font-weight: 700;
      line-height: 14px;
      text-align: center;
      box-shadow: 0 2px 6px rgba(23, 32, 38, 0.24);
    }

    .marker-label {
      position: absolute;
      left: 50%;
      bottom: 46px;
      max-width: 180px;
      transform: translateX(-50%);
      border: 1px solid rgba(23, 32, 38, 0.14);
      border-radius: 6px;
      padding: 2px 6px;
      background: rgba(255, 255, 255, 0.94);
      color: #172026;
      font-size: 11px;
      line-height: 1.2;
      white-space: nowrap;
      box-shadow: 0 4px 12px rgba(23, 32, 38, 0.16);
      pointer-events: none;
    }

    .icon-attribution {
      margin-top: 14px;
      border-top: 1px solid #d6dddf;
      padding-top: 10px;
      font-size: 11px;
      line-height: 1.45;
      color: #6b7780;
    }

    .icon-attribution a {
      color: #385f96;
      text-decoration: none;
    }

    .icon-attribution a:hover {
      text-decoration: underline;
    }

    @media (max-width: 860px) {
      body {
        overflow: auto;
      }

      .app-shell {
        grid-template-columns: 1fr;
        grid-template-rows: 55vh minmax(360px, 45vh);
        height: auto;
        min-height: 100vh;
      }

      .map-wrap {
        grid-column: 1;
        grid-row: 1;
        height: 55vh;
        min-height: 340px;
      }

      .sidebar {
        grid-column: 1;
        grid-row: 2;
        border-left: 0;
        border-top: 1px solid #d6dddf;
      }
    }
  </style>
</head>
<body>
  <main class="app-shell">
    <aside class="sidebar">
      <h1>IOV Node Map</h1>
      <div class="sidebar-tabs" role="tablist" aria-label="Navigasi dashboard">
        <button id="nodes-tab" class="sidebar-tab active" type="button" role="tab" aria-selected="true">Node Aktif</button>
        <button id="reports-tab" class="sidebar-tab" type="button" role="tab" aria-selected="false">Log Report</button>
      </div>
      <section id="nodes-panel" class="sidebar-panel active" role="tabpanel">
        <div id="status" class="status">Mengambil data node...</div>
        <div id="node-list" class="node-list"></div>
        <div class="icon-attribution">
          Icons:
          <a href="https://www.flaticon.com/free-icons/stride" title="stride icons" target="_blank" rel="noopener">Stride icons created by meaicon - Flaticon</a>
          |
          <a href="https://www.flaticon.com/free-icons/traffic" title="traffic icons" target="_blank" rel="noopener">Traffic icons created by Magnific - Flaticon</a>
        </div>
      </section>
      <section id="reports-panel" class="sidebar-panel" role="tabpanel">
        <div class="report-log">
          <h2>Log Report</h2>
          <p class="report-log-help">Report terbaru akan muncul di sini dan pada peta. Penghapusan dilakukan melalui akses admin server.</p>
          <div id="report-status" class="status">Mengambil report...</div>
          <div id="report-list" class="report-list"></div>
        </div>
      </section>
    </aside>
    <section class="map-wrap">
      <div id="map"></div>
      <div id="map-message" class="map-message"></div>
    </section>
  </main>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    (function () {
      var nodeList = document.getElementById("node-list");
      var statusEl = document.getElementById("status");
      var messageEl = document.getElementById("map-message");
      var reportList = document.getElementById("report-list");
      var reportStatusEl = document.getElementById("report-status");
      var nodesTab = document.getElementById("nodes-tab");
      var reportsTab = document.getElementById("reports-tab");
      var nodesPanel = document.getElementById("nodes-panel");
      var reportsPanel = document.getElementById("reports-panel");
      var markers = {};
      var reportMarkers = {};
      var map = null;
      var hasFittedBounds = false;
      var hasFittedReports = false;
      var latestNodes = [];
      var latestNodesById = {};
      var nodeItems = {};
      var selectedNodeId = null;
      var NODE_POLL_INTERVAL_MS = 10000;
      var REPORT_POLL_INTERVAL_MS = 30000;
      var REQUEST_TIMEOUT_MS = 10000;
      var MAX_POLL_BACKOFF_MS = 60000;
      var nodePollState = { timer: null, inFlight: false, failures: 0 };
      var reportPollState = { timer: null, inFlight: false, failures: 0 };
      var markerAssetUrls = {
        phone: "static/markers/pedestrian.png",
        raspi: "static/markers/vehicle.png"
      };
      var markerAssetReady = {
        phone: false,
        raspi: false
      };

      function showMessage(text) {
        messageEl.textContent = text;
        messageEl.style.display = "block";
      }

      function hideMessage() {
        messageEl.textContent = "";
        messageEl.style.display = "none";
      }

      function fetchJsonWithTimeout(url) {
        var controller = new AbortController();
        var timeoutId = window.setTimeout(function () {
          controller.abort();
        }, REQUEST_TIMEOUT_MS);

        return fetch(url, { cache: "no-store", signal: controller.signal })
          .then(function (response) {
            if (!response.ok) {
              throw new Error("HTTP " + response.status);
            }
            return response.json();
          })
          .finally(function () {
            window.clearTimeout(timeoutId);
          });
      }

      function pollErrorText(error) {
        if (error && error.name === "AbortError") {
          return "timeout setelah " + Math.round(REQUEST_TIMEOUT_MS / 1000) + " detik";
        }
        return error && error.message ? error.message : "koneksi gagal";
      }

      function nextPollDelay(baseInterval, failures) {
        if (!failures) {
          return baseInterval;
        }
        return Math.min(baseInterval * Math.pow(2, failures), MAX_POLL_BACKOFF_MS);
      }

      function schedulePoll(state, callback, delay) {
        if (state.timer !== null) {
          window.clearTimeout(state.timer);
        }
        state.timer = window.setTimeout(callback, delay);
      }

      function activateSidebarTab(tabName) {
        var showReports = tabName === "reports";
        nodesTab.classList.toggle("active", !showReports);
        reportsTab.classList.toggle("active", showReports);
        nodesTab.setAttribute("aria-selected", String(!showReports));
        reportsTab.setAttribute("aria-selected", String(showReports));
        nodesPanel.classList.toggle("active", !showReports);
        reportsPanel.classList.toggle("active", showReports);
      }

      function escapeHtml(value) {
        return String(value)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
      }

      function formatNumber(value, digits) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) {
          return "-";
        }
        return Number(value).toFixed(digits);
      }

      function formatTimestamp(value) {
        if (!value) {
          return "-";
        }
        return new Date(value).toLocaleString();
      }

      function hasValue(value) {
        return value !== null && value !== undefined;
      }

      function telemetryText(telemetry) {
        var parts = [];
        if (!telemetry) {
          return "Belum ada telemetry";
        }
        if (hasValue(telemetry.speed_kph)) {
          parts.push("Speed " + formatNumber(telemetry.speed_kph, 1) + " km/h");
        }
        if (hasValue(telemetry.battery)) {
          parts.push("Battery " + formatNumber(telemetry.battery, 1) + "%");
        }
        if (hasValue(telemetry.fuel_level_pct)) {
          parts.push("Fuel " + formatNumber(telemetry.fuel_level_pct, 1) + "%");
        }
        if (hasValue(telemetry.temperature_c)) {
          parts.push("Temp " + formatNumber(telemetry.temperature_c, 1) + " C");
        }
        if (hasValue(telemetry.odometer_km)) {
          parts.push("Odo " + formatNumber(telemetry.odometer_km, 1) + " km");
        }
        return parts.length ? parts.join(" | ") : "Telemetry diterima";
      }

      function statusMessageText(message) {
        if (!message) {
          return "Tidak ada status aktif";
        }
        return message.message + " (sampai " + formatTimestamp(message.expires_at) + ")";
      }

      function activeMessages(node) {
        if (node.active_messages && node.active_messages.length) {
          return node.active_messages;
        }
        return node.active_message ? [node.active_message] : [];
      }

      function deviceType(node) {
        return node.node_id.indexOf("raspi-") === 0 ? "raspi" : "phone";
      }

      function isTelemetryNode(node) {
        return deviceType(node) === "raspi";
      }

      function displayPid(node) {
        if (node.latest_gps && node.latest_gps.pid) {
          return node.latest_gps.pid;
        }
        if (node.latest_telemetry && node.latest_telemetry.pid) {
          return node.latest_telemetry.pid;
        }
        if (node.pids && node.pids.length > 0) {
          return node.pids[0];
        }
        return "-";
      }

      function markerSvg(type) {
        if (type === "raspi") {
          return [
            '<svg viewBox="0 0 24 24" aria-hidden="true">',
            '<rect x="6" y="3.5" width="12" height="17" rx="3"/>',
            '<path d="M8.5 7h7"/>',
            '<path d="M8.5 16.5h7"/>',
            '<path d="M9 10h6"/>',
            '<path d="M5 8.5h2"/>',
            '<path d="M17 8.5h2"/>',
            '<path d="M5 16h2"/>',
            '<path d="M17 16h2"/>',
            '<circle cx="9" cy="18.5" r=".6"/>',
            '<circle cx="15" cy="18.5" r=".6"/>',
            '</svg>'
          ].join("");
        }

        return [
          '<svg viewBox="0 0 24 24" aria-hidden="true">',
          '<circle cx="12" cy="4.5" r="2.2"/>',
          '<path d="M12 7.2v5.2"/>',
          '<path d="M8.4 10.2l3.6-2.4 3.6 2.4"/>',
          '<path d="M12 12.4l-3.2 7"/>',
          '<path d="M12 12.4l4 6.7"/>',
          '<path d="M8.8 19.4h-2"/>',
          '<path d="M16 19.1h2"/>',
          '</svg>'
        ].join("");
      }

      function markerIcon(node) {
        var type = deviceType(node);
        var isActive = selectedNodeId === node.node_id;
        var messages = activeMessages(node);
        var messageBadge = messages.length ? '<span class="marker-status-badge">' + messages.length + '</span>' : '';
        if (markerAssetReady[type]) {
          return L.divIcon({
            className: isActive ? "custom-marker active" : "custom-marker",
            html: '<div class="asset-marker-wrap"><img src="' + markerAssetUrls[type] + '" alt="">' + messageBadge + '</div>',
            iconSize: [44, 58],
            iconAnchor: [22, 44],
            popupAnchor: [0, -44]
          });
        }

        return L.divIcon({
          className: "",
          html: [
            '<div class="marker-wrap">',
            '<div class="marker-label">' + escapeHtml(displayPid(node)) + '</div>',
            messageBadge,
            '<div class="node-marker ' + type + (isActive ? " active" : "") + '">' + markerSvg(type) + '</div>',
            '</div>'
          ].join(""),
          iconSize: [44, 58],
          iconAnchor: [22, 44],
          popupAnchor: [0, -50]
        });
      }

      function preloadMarkerAsset(type) {
        var image = new Image();
        image.onload = function () {
          markerAssetReady[type] = true;
          updateMarkerStyles();
        };
        image.onerror = function () {
          markerAssetReady[type] = false;
        };
        image.src = markerAssetUrls[type];
      }

      function kv(label, value) {
        return '<div class="key">' + escapeHtml(label) + '</div><div class="value">' + escapeHtml(value) + '</div>';
      }

      function renderDetailSection(title, rowsHtml, emptyText) {
        return [
          '<section>',
          '<div class="detail-section-title">' + escapeHtml(title) + '</div>',
          rowsHtml ? '<div class="detail-grid">' + rowsHtml + '</div>' : '<div class="detail-empty">' + escapeHtml(emptyText) + '</div>',
          '</section>'
        ].join("");
      }

      function renderDetailContentSection(title, contentHtml, emptyText) {
        return [
          '<section>',
          '<div class="detail-section-title">' + escapeHtml(title) + '</div>',
          contentHtml ? '<div class="detail-content">' + contentHtml + '</div>' : '<div class="detail-empty">' + escapeHtml(emptyText) + '</div>',
          '</section>'
        ].join("");
      }

      function popupMetric(label, value) {
        return [
          '<div class="popup-metric">',
          '<div class="popup-metric-label">' + escapeHtml(label) + '</div>',
          '<div class="popup-metric-value">' + escapeHtml(value) + '</div>',
          '</div>'
        ].join("");
      }

      function popupSection(title, contentHtml) {
        return [
          '<section class="popup-section">',
          '<div class="popup-section-title">' + escapeHtml(title) + '</div>',
          contentHtml,
          '</section>'
        ].join("");
      }

      function reportPopupHtml(report) {
        var photos = report.photos || [];
        var photoHtml = photos.length
          ? photos.map(function (photo) {
              return '<img class="report-photo" src="' + escapeHtml(photo.url) + '" alt="Foto report">';
            }).join("")
          : '<div class="popup-empty">Report ini tidak memiliki foto.</div>';
        return [
          '<div class="popup-panel">',
          '<div class="popup-header">',
          '<div class="popup-title">' + escapeHtml(report.title) + '</div>',
          '<div class="popup-type">' + escapeHtml(report.category) + '</div>',
          '</div>',
          '<div class="popup-empty">' + escapeHtml(report.description) + '</div>',
          '<div class="popup-footer">Dilaporkan ' + escapeHtml(formatTimestamp(report.created_at)) + '</div>',
          photoHtml,
          '</div>'
        ].join("");
      }

      function reportCategoryText(category) {
        return String(category || "other").replace(/_/g, " ");
      }

      function renderReportList(reports) {
        if (!reports.length) {
          reportList.innerHTML = '<div class="report-list-message">Belum ada report.</div>';
          return;
        }

        reportList.innerHTML = reports.map(function (report) {
          var photoCount = (report.photos || []).length;
          return [
            '<article class="report-item">',
            '<div class="report-item-title">' + escapeHtml(report.title) + '</div>',
            '<div class="report-item-meta">' + escapeHtml(reportCategoryText(report.category)) + ' | ' + escapeHtml(formatTimestamp(report.created_at)) + ' | ' + photoCount + ' foto</div>',
            '<div class="report-item-description">' + escapeHtml(report.description) + '</div>',
            '</article>'
          ].join("");
        }).join("");
      }

      function nodeDetailHtml(node) {
        var gps;
        var telemetry;
        var telemetryRows;
        var sections;
        var messages;
        var messageRows;

        if (!node) {
          return "";
        }

        gps = node.latest_gps;
        telemetry = node.latest_telemetry;
        messages = activeMessages(node);
        messageRows = messages.map(function (message, index) {
          return [
            '<div class="status-message-item">',
            '<div class="detail-section-title">Message ' + (index + 1) + '</div>',
            '<div class="detail-grid">',
            kv("Kategori", message.category),
            kv("Message", message.message),
            kv("Berlaku sampai", formatTimestamp(message.expires_at)),
            '</div>',
            '</div>'
          ].join("");
        }).join("");
        sections = [
          renderDetailContentSection("Status Message", messageRows, "Tidak ada status message aktif."),
          renderDetailSection("GPS", gps ? [
            kv("PID", gps.pid),
            kv("Latitude", formatNumber(gps.lat, 6)),
            kv("Longitude", formatNumber(gps.lon, 6)),
            kv("Accuracy", gps.accuracy_m !== null && gps.accuracy_m !== undefined ? formatNumber(gps.accuracy_m, 1) + " m" : "-"),
            kv("Speed", gps.speed_mps !== null && gps.speed_mps !== undefined ? formatNumber(gps.speed_mps, 1) + " m/s" : "-"),
            kv("Heading", gps.heading_deg !== null && gps.heading_deg !== undefined ? formatNumber(gps.heading_deg, 1) + " deg" : "-"),
            kv("Altitude", gps.altitude_m !== null && gps.altitude_m !== undefined ? formatNumber(gps.altitude_m, 1) + " m" : "-"),
            kv("Timestamp", formatTimestamp(gps.timestamp))
          ].join("") : "", "Node ini belum mengirim data GPS.")
        ];

        if (isTelemetryNode(node)) {
          telemetryRows = telemetry ? [
            kv("PID", telemetry.pid),
            kv("Battery", telemetry.battery !== null && telemetry.battery !== undefined ? formatNumber(telemetry.battery, 1) + "%" : "-"),
            kv("Fuel", telemetry.fuel_level_pct !== null && telemetry.fuel_level_pct !== undefined ? formatNumber(telemetry.fuel_level_pct, 1) + "%" : "-"),
            kv("Speed", telemetry.speed_kph !== null && telemetry.speed_kph !== undefined ? formatNumber(telemetry.speed_kph, 1) + " km/h" : "-"),
            kv("Odometer", telemetry.odometer_km !== null && telemetry.odometer_km !== undefined ? formatNumber(telemetry.odometer_km, 1) + " km" : "-"),
            kv("Temperature", telemetry.temperature_c !== null && telemetry.temperature_c !== undefined ? formatNumber(telemetry.temperature_c, 1) + " C" : "-"),
            kv("Timestamp", formatTimestamp(telemetry.timestamp))
          ].join("") : "";
          sections.push(renderDetailSection("Telemetry", telemetryRows, "Node Raspi ini belum mengirim data telemetry."));
        } else {
          sections.push(renderDetailSection("Device", kv("Tipe data", "Phone node hanya mengirim GPS."), ""));
        }

        return [
          '<div class="inline-detail">',
          sections.join(""),
          '</div>'
        ].join("");
      }

      function selectNode(node, focusMap) {
        var gps;
        var marker;

        selectedNodeId = node.node_id;
        renderNodeList(latestNodes);
        updateMarkerStyles();

        gps = node.latest_gps;
        if (focusMap && gps && map) {
          marker = markers[node.node_id];
          map.setView([gps.lat, gps.lon], Math.max(map.getZoom(), 15));
          if (marker) {
            marker.openPopup();
          }
        }
      }

      function popupHtml(node) {
        var gps = node.latest_gps;
        var telemetry = node.latest_telemetry;
        var gpsMetrics = [];
        var telemetryMetrics = [];
        var sections = [];
        var messages = activeMessages(node);

        if (messages.length) {
          sections.push(popupSection(
            "Status Message",
            messages.map(function (message, index) {
              return '<div class="popup-empty"><strong>Message ' + (index + 1) + ': ' + escapeHtml(message.category) + '</strong><br>' +
                escapeHtml(message.message) + '</div>' +
                '<div class="popup-footer">Berlaku sampai ' + escapeHtml(formatTimestamp(message.expires_at)) + '</div>';
            }).join('<div class="popup-section-divider"></div>')
          ));
        }

        if (gps) {
          gpsMetrics.push(popupMetric("Latitude", formatNumber(gps.lat, 6)));
          gpsMetrics.push(popupMetric("Longitude", formatNumber(gps.lon, 6)));
          if (hasValue(gps.accuracy_m)) {
            gpsMetrics.push(popupMetric("Akurasi", formatNumber(gps.accuracy_m, 1) + " m"));
          }
          if (hasValue(gps.speed_mps)) {
            gpsMetrics.push(popupMetric("Kecepatan GPS", formatNumber(gps.speed_mps, 1) + " m/s"));
          }
          sections.push(popupSection(
            "GPS",
            '<div class="popup-metrics">' + gpsMetrics.join("") + '</div>' +
              '<div class="popup-footer">Diperbarui ' + escapeHtml(formatTimestamp(gps.timestamp)) + '</div>'
          ));
        }

        if (isTelemetryNode(node)) {
          if (telemetry) {
            if (hasValue(telemetry.battery)) {
              telemetryMetrics.push(popupMetric("Baterai", formatNumber(telemetry.battery, 1) + "%"));
            }
            if (hasValue(telemetry.fuel_level_pct)) {
              telemetryMetrics.push(popupMetric("Bahan bakar", formatNumber(telemetry.fuel_level_pct, 1) + "%"));
            }
            if (hasValue(telemetry.speed_kph)) {
              telemetryMetrics.push(popupMetric("Kecepatan", formatNumber(telemetry.speed_kph, 1) + " km/h"));
            }
            if (hasValue(telemetry.odometer_km)) {
              telemetryMetrics.push(popupMetric("Odometer", formatNumber(telemetry.odometer_km, 1) + " km"));
            }
            if (hasValue(telemetry.temperature_c)) {
              telemetryMetrics.push(popupMetric("Temperatur", formatNumber(telemetry.temperature_c, 1) + " C"));
            }
            sections.push(popupSection(
              "Telemetry",
              telemetryMetrics.length
                ? '<div class="popup-metrics">' + telemetryMetrics.join("") + '</div>' +
                    '<div class="popup-footer">Diperbarui ' + escapeHtml(formatTimestamp(telemetry.timestamp)) + '</div>'
                : '<div class="popup-empty">Telemetry diterima, tetapi belum memiliki nilai yang dapat ditampilkan.</div>'
            ));
          } else {
            sections.push(popupSection("Telemetry", '<div class="popup-empty">Belum ada telemetry dari node ini.</div>'));
          }
        } else {
          sections.push(popupSection("Device", '<div class="popup-empty">Phone node hanya mengirim GPS.</div>'));
        }

        return [
          '<div class="popup-panel">',
          '<div class="popup-header">',
          '<div class="popup-title">' + escapeHtml(displayPid(node)) + '</div>',
          '<div class="popup-type">' + escapeHtml(deviceType(node)) + '</div>',
          '</div>',
          sections.join(""),
          '</div>'
        ].join("");
      }

      function renderNodeList(nodes) {
        var visibleNodeIds = {};

        latestNodesById = {};
        nodes.forEach(function (node) {
          var gps = node.latest_gps;
          var telemetry = node.latest_telemetry;
          var messages = activeMessages(node);
          var updatedAt = gps && gps.timestamp ? gps.timestamp : telemetry && telemetry.timestamp ? telemetry.timestamp : null;
          var latLon = gps ? formatNumber(gps.lat, 6) + ", " + formatNumber(gps.lon, 6) : "-";
          var pidLabel = displayPid(node);
          var nodeId = node.node_id;
          var item = nodeItems[nodeId];

          visibleNodeIds[nodeId] = true;
          latestNodesById[nodeId] = node;
          if (!item) {
            item = document.createElement("div");
            item.setAttribute("data-node-id", nodeId);
            item.setAttribute("role", "button");
            item.setAttribute("tabindex", "0");
            item.addEventListener("click", function () {
              var currentNode = latestNodesById[nodeId];
              if (currentNode) {
                selectNode(currentNode, Boolean(currentNode.latest_gps));
              }
            });
            item.addEventListener("keydown", function (event) {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                var currentNode = latestNodesById[nodeId];
                if (currentNode) {
                  selectNode(currentNode, Boolean(currentNode.latest_gps));
                }
              }
            });
            nodeItems[nodeId] = item;
          }

          item.className = (gps ? "node has-gps" : "node") + (selectedNodeId === node.node_id ? " selected" : "");
          item.innerHTML = [
            '<div class="node-header">',
            '<div class="node-id">' + escapeHtml(nodeId) + '</div>',
            '<div class="badge ' + (messages.length ? "message-badge" : (gps ? "" : "missing")) + '">' + (messages.length ? messages.length + " status" : (gps ? "GPS aktif" : "Belum ada GPS")) + '</div>',
            '</div>',
            '<div class="kv">',
            '<div class="key">Tipe</div><div class="value">' + escapeHtml(deviceType(node)) + '</div>',
            '<div class="key">PID</div><div class="value">' + escapeHtml(pidLabel) + '</div>',
            '<div class="key">Lat/Lon</div><div class="value">' + escapeHtml(latLon) + '</div>',
            isTelemetryNode(node) ? '<div class="key">Telemetry</div><div class="value">' + escapeHtml(telemetryText(telemetry)) + '</div>' : '<div class="key">Device</div><div class="value">Phone GPS only</div>',
            '<div class="key">Updated</div><div class="value">' + escapeHtml(formatTimestamp(updatedAt)) + '</div>',
            '</div>',
            selectedNodeId === node.node_id ? nodeDetailHtml(node) : ""
          ].join("");

          nodeList.appendChild(item);
        });

        Object.keys(nodeItems).forEach(function (nodeId) {
          if (!visibleNodeIds[nodeId]) {
            nodeItems[nodeId].remove();
            delete nodeItems[nodeId];
          }
        });
      }

      function updateNodeSelectionStyles() {
        var items = nodeList.querySelectorAll(".node");
        Array.prototype.forEach.call(items, function (item) {
          if (item.getAttribute("data-node-id") === selectedNodeId) {
            item.classList.add("selected");
          } else {
            item.classList.remove("selected");
          }
        });
      }

      function updateMarkerStyles() {
        if (!map) {
          return;
        }

        latestNodes.forEach(function (node) {
          if (markers[node.node_id]) {
            markers[node.node_id].setIcon(markerIcon(node));
          }
        });
      }

      function initMap() {
        if (!window.L) {
          showMessage("Leaflet gagal dimuat. Pastikan browser punya koneksi internet untuk mengambil asset map dari CDN.");
          return false;
        }

        map = L.map("map", {
          zoomControl: true,
          attributionControl: true
        }).setView([-6.2, 106.816666], 12);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: "&copy; OpenStreetMap contributors"
        }).addTo(map);

        setTimeout(function () {
          map.invalidateSize();
        }, 0);

        window.addEventListener("resize", function () {
          map.invalidateSize();
        });

        return true;
      }

      function updateMarkers(nodes) {
        var visibleNodeIds = {};
        var points = [];

        if (!map) {
          return;
        }

        nodes.forEach(function (node) {
          var gps = node.latest_gps;
          var marker;

          if (!gps) {
            return;
          }

          visibleNodeIds[node.node_id] = true;
          points.push([gps.lat, gps.lon]);

          if (!markers[node.node_id]) {
            markers[node.node_id] = L.marker([gps.lat, gps.lon], {
              icon: markerIcon(node),
              title: node.node_id
            }).addTo(map);
          }

          marker = markers[node.node_id];
          marker.setLatLng([gps.lat, gps.lon]);
          marker.setIcon(markerIcon(node));
          marker.bindPopup(popupHtml(node));
          marker.off("click");
          marker.off("mouseover");
          marker.on("click", function () {
            selectNode(node, false);
          });
          marker.on("mouseover", function () {
            marker.openPopup();
          });
        });

        Object.keys(markers).forEach(function (nodeId) {
          if (!visibleNodeIds[nodeId]) {
            map.removeLayer(markers[nodeId]);
            delete markers[nodeId];
          }
        });

        if (!hasFittedBounds && points.length === 1) {
          map.setView(points[0], 14);
          hasFittedBounds = true;
        } else if (!hasFittedBounds && points.length > 1) {
          map.fitBounds(points, { padding: [36, 36], maxZoom: 15 });
          hasFittedBounds = true;
        }

        map.invalidateSize();
      }

      function updateReportMarkers(reports) {
        var visibleReportIds = {};
        var points = [];

        if (!map) {
          return;
        }

        reports.forEach(function (report) {
          var marker;
          visibleReportIds[report.id] = true;
          points.push([report.lat, report.lon]);
          if (!reportMarkers[report.id]) {
            reportMarkers[report.id] = L.marker([report.lat, report.lon], {
              icon: L.divIcon({
                className: "report-marker-icon",
                html: '<div class="report-marker"><span>!</span></div>',
                iconSize: [30, 42],
                iconAnchor: [15, 38],
                popupAnchor: [0, -38]
              }),
              title: report.title
            }).addTo(map);
          }
          marker = reportMarkers[report.id];
          marker.setLatLng([report.lat, report.lon]);
          marker.bindPopup(reportPopupHtml(report));
        });

        Object.keys(reportMarkers).forEach(function (reportId) {
          if (!visibleReportIds[reportId]) {
            map.removeLayer(reportMarkers[reportId]);
            delete reportMarkers[reportId];
          }
        });

        if (!hasFittedReports && points.length > 0) {
          latestNodes.forEach(function (node) {
            if (node.latest_gps) {
              points.push([node.latest_gps.lat, node.latest_gps.lon]);
            }
          });
          if (points.length === 1) {
            map.setView(points[0], 14);
          } else {
            map.fitBounds(points, { padding: [36, 36], maxZoom: 15 });
          }
          hasFittedReports = true;
        }
      }

      function refreshNodes() {
        nodePollState.timer = null;
        if (nodePollState.inFlight) {
          return;
        }
        if (document.hidden) {
          schedulePoll(nodePollState, refreshNodes, NODE_POLL_INTERVAL_MS);
          return;
        }

        nodePollState.inFlight = true;
        fetchJsonWithTimeout("broadcast/latest")
          .then(function (nodes) {
            nodePollState.failures = 0;
            var withGps = nodes.filter(function (node) {
              return Boolean(node.latest_gps);
            }).length;
            latestNodes = nodes;
            if (selectedNodeId && !nodes.some(function (node) {
              return node.node_id === selectedNodeId;
            })) {
              selectedNodeId = null;
            }
            renderNodeList(nodes);
            updateMarkers(nodes);
            statusEl.textContent = nodes.length + " node terdaftar, " + withGps + " node punya GPS. Update " + new Date().toLocaleTimeString();
            if (window.L) {
              hideMessage();
            }
          })
          .catch(function (error) {
            nodePollState.failures += 1;
            statusEl.textContent = "Gagal mengambil data; data terakhir tetap ditampilkan: " + pollErrorText(error);
          })
          .finally(function () {
            nodePollState.inFlight = false;
            schedulePoll(
              nodePollState,
              refreshNodes,
              nextPollDelay(NODE_POLL_INTERVAL_MS, nodePollState.failures)
            );
          });
      }

      function refreshReports() {
        reportPollState.timer = null;
        if (reportPollState.inFlight) {
          return;
        }
        if (document.hidden) {
          schedulePoll(reportPollState, refreshReports, REPORT_POLL_INTERVAL_MS);
          return;
        }

        reportPollState.inFlight = true;
        fetchJsonWithTimeout("reports?limit=100")
          .then(function (reports) {
            reportPollState.failures = 0;
            updateReportMarkers(reports);
            renderReportList(reports);
            reportStatusEl.textContent = reports.length + " report. Update " + new Date().toLocaleTimeString();
          })
          .catch(function (error) {
            reportPollState.failures += 1;
            reportStatusEl.textContent = "Gagal mengambil report; data terakhir tetap ditampilkan: " + pollErrorText(error);
          })
          .finally(function () {
            reportPollState.inFlight = false;
            schedulePoll(
              reportPollState,
              refreshReports,
              nextPollDelay(REPORT_POLL_INTERVAL_MS, reportPollState.failures)
            );
          });
      }

      initMap();
      nodesTab.addEventListener("click", function () {
        activateSidebarTab("nodes");
      });
      reportsTab.addEventListener("click", function () {
        activateSidebarTab("reports");
      });
      preloadMarkerAsset("phone");
      preloadMarkerAsset("raspi");
      refreshNodes();
      refreshReports();
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
          schedulePoll(nodePollState, refreshNodes, 0);
          schedulePoll(reportPollState, refreshReports, 0);
        }
      });
    })();
  </script>
</body>
</html>
"""
