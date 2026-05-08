(function () {
  const scriptEl = document.getElementById("script");
  const densityEl = document.getElementById("density");
  const statusEl = document.getElementById("status");
  const buildBtn = document.getElementById("build-btn");
  const downloadBtn = document.getElementById("download-btn");
  const metricsEl = document.getElementById("metrics");
  const paramsEl = document.getElementById("params");
  const exampleSelect = document.getElementById("example-select");
  const viewerEl = document.getElementById("viewer");
  const addParamBtn = document.getElementById("add-param-btn");
  const addBoxBtn = document.getElementById("add-box-btn");
  const addCylinderBtn = document.getElementById("add-cylinder-btn");
  const addExtrudeBtn = document.getElementById("add-extrude-btn");
  const saveScriptBtn = document.getElementById("save-script-btn");
  const loadScriptBtn = document.getElementById("load-script-btn");
  const loadScriptInput = document.getElementById("load-script-input");
  const exportReportBtn = document.getElementById("export-report-btn");

  const examples = window.APP_EXAMPLES || {};
  let meshData = null;
  let lastBuildData = null;
  let renderWidth = 1;
  let renderHeight = 1;

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  viewerEl.appendChild(canvas);

  const cameraState = {
    yaw: 0.7,
    pitch: -0.45,
    zoom: 1.8,
    dragging: false,
    lastX: 0,
    lastY: 0,
  };

  function fitRenderer() {
    renderWidth = viewerEl.clientWidth || 800;
    renderHeight = viewerEl.clientHeight || 520;
    canvas.width = Math.max(1, Math.floor(renderWidth * (window.devicePixelRatio || 1)));
    canvas.height = Math.max(1, Math.floor(renderHeight * (window.devicePixelRatio || 1)));
    canvas.style.width = `${renderWidth}px`;
    canvas.style.height = `${renderHeight}px`;
    if (ctx) {
      ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);
    }
    draw();
  }

  function rotateVertex(v, yaw, pitch) {
    const x1 = v[0] * Math.cos(yaw) - v[2] * Math.sin(yaw);
    const z1 = v[0] * Math.sin(yaw) + v[2] * Math.cos(yaw);
    const y2 = v[1] * Math.cos(pitch) - z1 * Math.sin(pitch);
    const z2 = v[1] * Math.sin(pitch) + z1 * Math.cos(pitch);
    return [x1, y2, z2];
  }

  function project(v) {
    const distance = 3.0 / cameraState.zoom;
    const z = v[2] + distance;
    const perspective = 220 / Math.max(0.1, z);
    return [
      renderWidth / 2 + v[0] * perspective,
      renderHeight / 2 - v[1] * perspective,
      z,
    ];
  }

  function normalizeMesh(data) {
    const verts = data.vertices || [];
    if (!verts.length) {
      return data;
    }
    let minX = Infinity;
    let minY = Infinity;
    let minZ = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    let maxZ = -Infinity;
    for (const v of verts) {
      if (v[0] < minX) minX = v[0];
      if (v[1] < minY) minY = v[1];
      if (v[2] < minZ) minZ = v[2];
      if (v[0] > maxX) maxX = v[0];
      if (v[1] > maxY) maxY = v[1];
      if (v[2] > maxZ) maxZ = v[2];
    }
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const cz = (minZ + maxZ) / 2;
    const sx = maxX - minX;
    const sy = maxY - minY;
    const sz = maxZ - minZ;
    const scale = 1 / Math.max(1e-9, Math.max(sx, sy, sz));
    return {
      vertices: verts.map((v) => [(v[0] - cx) * scale, (v[1] - cy) * scale, (v[2] - cz) * scale]),
      faces: data.faces || [],
    };
  }

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.style.color = isError ? "#b91c1c" : "#374151";
  }

  window.addEventListener("error", (event) => {
    setStatus(`Ошибка интерфейса: ${event.message}`, true);
  });

  function clearMeshData() {
    if (!meshData) {
      return;
    }
    meshData = null;
    lastBuildData = null;
    draw();
  }

  function addCommandTemplate(template) {
    const current = scriptEl.value.trimEnd();
    scriptEl.value = `${current ? `${current}\n` : ""}${template}\n`;
    scriptEl.focus();
    setStatus("Шаблон команды добавлен.");
  }

  function saveScriptToFile() {
    const text = scriptEl.value;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = "project_script.txt";
    link.click();
    URL.revokeObjectURL(url);
    setStatus("Сценарий сохранен в файл.");
  }

  function formatNumber(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) {
      return String(value);
    }
    if (Math.abs(n) >= 1e4 || Math.abs(n) < 1e-3) {
      return n.toExponential(6);
    }
    return n.toFixed(6);
  }

  function exportReportCsv() {
    if (!lastBuildData) {
      setStatus("Сначала постройте модель, затем экспортируйте отчет.", true);
      return;
    }
    const rows = [];
    rows.push("section,name,value");
    rows.push(`mass_props,volume_m3,${lastBuildData.mass_props.volume}`);
    rows.push(`mass_props,mass_kg,${lastBuildData.mass_props.mass}`);
    rows.push(
      `mass_props,center_of_mass,"${lastBuildData.mass_props.center_of_mass.join(";")}"`
    );
    for (const [name, value] of Object.entries(lastBuildData.params || {})) {
      rows.push(`parameter,${name},${value}`);
    }
    const blob = new Blob([rows.join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = "engineering_report.csv";
    link.click();
    URL.revokeObjectURL(url);
    setStatus("CSV-отчет успешно сохранен.");
  }

  function draw() {
    if (!ctx) {
      return;
    }
    ctx.clearRect(0, 0, renderWidth, renderHeight);
    ctx.fillStyle = "#f9fafb";
    ctx.fillRect(0, 0, renderWidth, renderHeight);

    if (!meshData || !meshData.vertices.length || !meshData.faces.length) {
      ctx.fillStyle = "#6b7280";
      ctx.font = "14px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      ctx.fillText("Модель не построена", 16, 28);
      return;
    }

    const rotated = meshData.vertices.map((v) => rotateVertex(v, cameraState.yaw, cameraState.pitch));
    const tris = meshData.faces.map((f) => {
      const p0 = project(rotated[f[0]]);
      const p1 = project(rotated[f[1]]);
      const p2 = project(rotated[f[2]]);
      const avgZ = (p0[2] + p1[2] + p2[2]) / 3;
      return { p0, p1, p2, avgZ };
    });
    tris.sort((a, b) => b.avgZ - a.avgZ);

    for (const t of tris) {
      const shade = Math.max(80, Math.min(220, Math.floor(220 - t.avgZ * 35)));
      ctx.fillStyle = `rgb(${shade - 30}, ${shade - 10}, ${shade})`;
      ctx.beginPath();
      ctx.moveTo(t.p0[0], t.p0[1]);
      ctx.lineTo(t.p1[0], t.p1[1]);
      ctx.lineTo(t.p2[0], t.p2[1]);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "rgba(30, 64, 175, 0.25)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }

  function renderMetrics(mp) {
    const c = mp.center_of_mass || [0, 0, 0];
    metricsEl.innerHTML = `
      <table>
        <tr><th>Показатель</th><th>Значение</th></tr>
        <tr><td>Объём, м³</td><td>${formatNumber(mp.volume)}</td></tr>
        <tr><td>Масса, кг</td><td>${formatNumber(mp.mass)}</td></tr>
        <tr><td>Центр масс X</td><td>${formatNumber(c[0])}</td></tr>
        <tr><td>Центр масс Y</td><td>${formatNumber(c[1])}</td></tr>
        <tr><td>Центр масс Z</td><td>${formatNumber(c[2])}</td></tr>
      </table>
    `;
  }

  function renderParams(params) {
    const keys = Object.keys(params || {});
    if (!keys.length) {
      paramsEl.innerHTML = "<p>Нет параметров.</p>";
      return;
    }
    const rows = keys
      .map((name) => `<tr><td>${name}</td><td>${formatNumber(params[name])}</td></tr>`)
      .join("");
    paramsEl.innerHTML = `
      <table>
        <tr><th>Имя</th><th>Значение</th></tr>
        ${rows}
      </table>
    `;
  }

  async function buildModel() {
    setStatus("Построение модели...");
    downloadBtn.classList.add("disabled");
    downloadBtn.removeAttribute("href");

    try {
      const density = Number(densityEl.value);
      if (!Number.isFinite(density) || density <= 0) {
        throw new Error("Введите корректную плотность (число больше 0).");
      }

      const response = await fetch("/api/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script: scriptEl.value,
          density,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Не удалось построить модель.");
      }

      lastBuildData = data;
      meshData = normalizeMesh(data.mesh_data || { vertices: [], faces: [] });
      draw();
      renderMetrics(data.mass_props);
      renderParams(data.params);
      downloadBtn.href = `data:model/stl;base64,${data.stl_base64}`;
      downloadBtn.classList.remove("disabled");
      setStatus("Модель успешно построена.");
    } catch (error) {
      clearMeshData();
      metricsEl.innerHTML = "";
      paramsEl.innerHTML = "";
      setStatus(error.message || String(error), true);
    }
  }

  exampleSelect.addEventListener("change", () => {
    const name = exampleSelect.value;
    if (name && Object.prototype.hasOwnProperty.call(examples, name)) {
      scriptEl.value = examples[name];
      setStatus(`Загружен шаблон: ${name}`);
    }
  });

  addParamBtn.addEventListener("click", () => {
    addCommandTemplate("param new_param 0.01");
  });

  addBoxBtn.addEventListener("click", () => {
    addCommandTemplate("box box1 ox oy oz dx dy dz");
  });

  addCylinderBtn.addEventListener("click", () => {
    addCommandTemplate("cylinder cyl1 cx cy cz r h axis z");
  });

  addExtrudeBtn.addEventListener("click", () => {
    addCommandTemplate("extrude ext1 height x0 y0 x1 y0 x1 y1 x0 y1");
  });

  saveScriptBtn.addEventListener("click", saveScriptToFile);

  loadScriptBtn.addEventListener("click", () => {
    loadScriptInput.value = "";
    loadScriptInput.click();
  });

  loadScriptInput.addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      scriptEl.value = String(reader.result || "");
      setStatus(`Проект загружен: ${file.name}`);
    };
    reader.onerror = () => {
      setStatus("Не удалось прочитать файл проекта.", true);
    };
    reader.readAsText(file, "utf-8");
  });

  exportReportBtn.addEventListener("click", exportReportCsv);

  canvas.addEventListener("mousedown", (event) => {
    cameraState.dragging = true;
    cameraState.lastX = event.clientX;
    cameraState.lastY = event.clientY;
  });

  window.addEventListener("mouseup", () => {
    cameraState.dragging = false;
  });

  window.addEventListener("mousemove", (event) => {
    if (!cameraState.dragging) {
      return;
    }
    const dx = event.clientX - cameraState.lastX;
    const dy = event.clientY - cameraState.lastY;
    cameraState.lastX = event.clientX;
    cameraState.lastY = event.clientY;
    cameraState.yaw += dx * 0.01;
    cameraState.pitch += dy * 0.01;
    cameraState.pitch = Math.max(-1.4, Math.min(1.4, cameraState.pitch));
    draw();
  });

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    cameraState.zoom *= event.deltaY > 0 ? 0.92 : 1.08;
    cameraState.zoom = Math.max(0.35, Math.min(4.0, cameraState.zoom));
    draw();
  });

  buildBtn.addEventListener("click", () => {
    void buildModel();
  });

  scriptEl.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      void buildModel();
    }
  });

  window.addEventListener("resize", fitRenderer);

  fitRenderer();
  draw();
})();
