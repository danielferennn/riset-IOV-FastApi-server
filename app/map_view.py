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
      grid-template-columns: 360px minmax(0, 1fr);
      width: 100vw;
      height: 100vh;
      min-height: 0;
    }

    .sidebar {
      min-width: 0;
      min-height: 0;
      overflow-y: auto;
      padding: 16px;
      border-right: 1px solid #d6dddf;
      background: #f8faf9;
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

    .marker-wrap {
      position: relative;
      width: 44px;
      height: 58px;
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
        grid-row: 1;
        height: 55vh;
        min-height: 340px;
      }

      .sidebar {
        grid-row: 2;
        border-right: 0;
        border-top: 1px solid #d6dddf;
      }
    }
  </style>
</head>
<body>
  <main class="app-shell">
    <aside class="sidebar">
      <h1>IOV Node Map</h1>
      <div id="status" class="status">Mengambil data node...</div>
      <div id="node-list" class="node-list"></div>
      <div class="icon-attribution">
        Icons:
        <a href="https://www.flaticon.com/free-icons/stride" title="stride icons" target="_blank" rel="noopener">Stride icons created by meaicon - Flaticon</a>
        |
        <a href="https://www.flaticon.com/free-icons/traffic" title="traffic icons" target="_blank" rel="noopener">Traffic icons created by Magnific - Flaticon</a>
      </div>
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
      var markers = {};
      var map = null;
      var hasFittedBounds = false;
      var latestNodes = [];
      var selectedNodeId = null;
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
        if (markerAssetReady[type]) {
          return L.icon({
            iconUrl: markerAssetUrls[type],
            iconSize: type === "phone" ? [38, 38] : [44, 44],
            iconAnchor: type === "phone" ? [19, 38] : [22, 44],
            popupAnchor: [0, -42],
            className: isActive ? "custom-marker active" : "custom-marker"
          });
        }

        return L.divIcon({
          className: "",
          html: [
            '<div class="marker-wrap">',
            '<div class="marker-label">' + escapeHtml(displayPid(node)) + '</div>',
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

      function nodeDetailHtml(node) {
        var gps;
        var telemetry;
        var telemetryRows;
        var sections;

        if (!node) {
          return "";
        }

        gps = node.latest_gps;
        telemetry = node.latest_telemetry;
        sections = [
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

      function previewNode(node) {
        selectedNodeId = node.node_id;
        renderNodeList(latestNodes);
        updateMarkerStyles();
      }

      function popupHtml(node) {
        var gps = node.latest_gps;
        var telemetry = node.latest_telemetry;
        var gpsMetrics = [];
        var telemetryMetrics = [];
        var sections = [];

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
        nodeList.innerHTML = "";
        nodes.forEach(function (node) {
          var gps = node.latest_gps;
          var telemetry = node.latest_telemetry;
          var updatedAt = gps && gps.timestamp ? gps.timestamp : telemetry && telemetry.timestamp ? telemetry.timestamp : null;
          var latLon = gps ? formatNumber(gps.lat, 6) + ", " + formatNumber(gps.lon, 6) : "-";
          var pidLabel = displayPid(node);
          var item = document.createElement("div");
          item.className = (gps ? "node has-gps" : "node") + (selectedNodeId === node.node_id ? " selected" : "");
          item.setAttribute("data-node-id", node.node_id);
          item.innerHTML = [
            '<div class="node-header">',
            '<div class="node-id">' + escapeHtml(pidLabel) + '</div>',
            '<div class="badge ' + (gps ? "" : "missing") + '">' + (gps ? "GPS aktif" : "Belum ada GPS") + '</div>',
            '</div>',
            '<div class="kv">',
          '<div class="key">Tipe</div><div class="value">' + escapeHtml(deviceType(node)) + '</div>',
          '<div class="key">Lat/Lon</div><div class="value">' + escapeHtml(latLon) + '</div>',
          isTelemetryNode(node) ? '<div class="key">Telemetry</div><div class="value">' + escapeHtml(telemetryText(telemetry)) + '</div>' : '<div class="key">Device</div><div class="value">Phone GPS only</div>',
          '<div class="key">Updated</div><div class="value">' + escapeHtml(formatTimestamp(updatedAt)) + '</div>',
          '</div>',
          selectedNodeId === node.node_id ? nodeDetailHtml(node) : ""
        ].join("");

          item.addEventListener("click", function () {
            selectNode(node, Boolean(gps));
          });
          item.addEventListener("mouseenter", function () {
            previewNode(node);
          });

          nodeList.appendChild(item);
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
            previewNode(node);
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

      function refreshNodes() {
        fetch("broadcast/latest", { cache: "no-store" })
          .then(function (response) {
            if (!response.ok) {
              throw new Error("HTTP " + response.status);
            }
            return response.json();
          })
          .then(function (nodes) {
            var withGps = nodes.filter(function (node) {
              return Boolean(node.latest_gps);
            }).length;
            var selectedNode = null;
            latestNodes = nodes;
            if (selectedNodeId) {
              nodes.forEach(function (node) {
                if (node.node_id === selectedNodeId) {
                  selectedNode = node;
                }
              });
            }
            renderNodeList(nodes);
            updateMarkers(nodes);
            if (selectedNodeId && !selectedNode) {
              selectedNodeId = null;
              renderNodeList(nodes);
            }
            statusEl.textContent = nodes.length + " node terdaftar, " + withGps + " node punya GPS. Update " + new Date().toLocaleTimeString();
            if (window.L) {
              hideMessage();
            }
          })
          .catch(function (error) {
            statusEl.textContent = "Gagal mengambil data: " + error.message;
          });
      }

      initMap();
      preloadMarkerAsset("phone");
      preloadMarkerAsset("raspi");
      refreshNodes();
      setInterval(refreshNodes, 2000);
    })();
  </script>
</body>
</html>
"""
