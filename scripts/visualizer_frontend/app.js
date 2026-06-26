(function () {
  const model = window.__VISUALIZER_MODEL__;
  const moduleByName = new Map(model.modules.map((m) => [m.name, m]));
  const parentIndex = buildParentIndex(model.modules);
  const initialIndex = Math.max(0, model.modules.findIndex((m) => m.isTop));
  const state = {
    moduleIndex: initialIndex,
    navStack: [{ moduleName: (model.modules[initialIndex] || {}).name || model.top || "", via: "" }],
    view: "hierarchy",
    selected: null,
    scale: 1,
    tx: 60,
    ty: 60,
    dragging: false,
    dragStart: null,
    didDrag: false,
    trace: "",
    expanded: new Set(),
    allExpanded: false,
  };

  const svg = document.getElementById("diagram");
  const moduleList = document.getElementById("moduleList");
  const moduleSearch = document.getElementById("moduleSearch");
  const traceInput = document.getElementById("traceInput");
  const NS = "http://www.w3.org/2000/svg";

  document.getElementById("topName").textContent = model.top || "unknown";
  document.getElementById("moduleCount").textContent = model.moduleCount;
  resetHierarchyExpansion();

  function currentModule() {
    const current = state.navStack[state.navStack.length - 1];
    return moduleByName.get(current && current.moduleName) || model.modules[state.moduleIndex] || emptyModule();
  }

  function emptyModule() {
    return { nodes: [], edges: [], counts: {}, instances: [], ports: [], signals: [] };
  }

  function el(name, attrs = {}, parent = null) {
    const node = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (parent) parent.appendChild(node);
    return node;
  }

  function makeNode(id, label, type, detail, raw = null) {
    return { id, label, type, detail, raw: raw || { label, type, detail } };
  }

  function buildParentIndex(modules) {
    const index = new Map();
    modules.forEach((parent) => {
      (parent.instances || []).forEach((inst, instIndex) => {
        if (!inst.module || !moduleByName.has(inst.module)) return;
        if (!index.has(inst.module)) index.set(inst.module, []);
        index.get(inst.module).push({
          parentName: parent.name,
          instanceName: inst.name || "(unnamed)",
          instanceIndex: instIndex,
          instance: inst,
        });
      });
    });
    return index;
  }

  function graphForHierarchy(mod) {
    const rootId = rootNodeId(mod);
    const nodes = [];
    const edges = [];
    const path = findPathFromTop(mod.name);

    path.slice(0, -1).forEach((entry, index) => {
      const id = ancestorNodeId(entry, index);
      const nextId = index === path.length - 2 ? rootId : ancestorNodeId(path[index + 1], index + 1);
      const node = makeNode(id, entry.moduleName, "parent", entry.via || (index === 0 ? "root" : "parent"), entry);
      node.depth = index;
      node.expandable = false;
      node.expanded = false;
      node.pathIndex = index;
      nodes.push(node);
      edges.push({ source: id, target: nextId, label: path[index + 1].via || "", kind: "parent-link" });
    });

    const root = makeNode(rootId, mod.name, "module", mod.isTop ? "top module" : "current module", mod.raw);
    root.depth = Math.max(0, path.length - 1);
    root.expandable = hasVisibleChildren(mod);
    root.expanded = state.expanded.has(rootId);
    nodes.push(root);

    if (state.expanded.has(rootId)) {
      appendHierarchyChildren(mod, rootId, mod.name, root.depth + 1, nodes, edges);
    }
    return layoutHierarchyGraph(nodes, edges);
  }

  function findPathFromTop(targetModuleName) {
    const topName = model.top || (model.modules[0] && model.modules[0].name) || targetModuleName;
    if (targetModuleName === topName) return [{ moduleName: topName, via: "" }];
    const queue = [{ moduleName: topName, via: "", path: [{ moduleName: topName, via: "" }] }];
    const seen = new Set([topName]);
    while (queue.length) {
      const current = queue.shift();
      const mod = moduleByName.get(current.moduleName);
      if (!mod) continue;
      for (const inst of mod.instances || []) {
        if (!inst.module || !moduleByName.has(inst.module)) continue;
        const nextPath = current.path.concat({ moduleName: inst.module, via: inst.name || "(unnamed)" });
        if (inst.module === targetModuleName) return nextPath;
        const seenKey = current.moduleName + "->" + inst.name + "->" + inst.module;
        if (seen.has(seenKey)) continue;
        seen.add(seenKey);
        queue.push({ moduleName: inst.module, via: inst.name || "(unnamed)", path: nextPath });
      }
    }
    const parents = parentIndex.get(targetModuleName) || [];
    if (parents.length) {
      return [
        { moduleName: parents[0].parentName, via: "" },
        { moduleName: targetModuleName, via: parents[0].instanceName },
      ];
    }
    return [{ moduleName: targetModuleName, via: "" }];
  }

  function ancestorNodeId(entry, index) {
    return "ancestor:" + index + ":" + entry.moduleName + ":" + (entry.via || "root");
  }

  function appendHierarchyChildren(mod, parentId, path, depth, nodes, edges) {
    const instances = mod.instances || [];
    if (instances.length > 50) {
      const byType = new Map();
      instances.forEach((inst) => {
        const type = inst.module || "unknown";
        if (!byType.has(type)) byType.set(type, []);
        byType.get(type).push(inst);
      });
      [...byType.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])).forEach(([type, list]) => {
        const id = path + "/group:" + type;
        const known = moduleByName.has(type);
        const node = makeNode(id, type, known ? "module" : "group", list.length + " instances", { module: type, instances: list });
        node.depth = depth;
        node.expandable = known && hasVisibleChildren(moduleByName.get(type));
        node.expanded = state.expanded.has(id);
        nodes.push(node);
        edges.push({ source: parentId, target: id, label: String(list.length), kind: "hierarchy" });
        if (node.expanded) appendHierarchyChildren(moduleByName.get(type), id, id, depth + 1, nodes, edges);
      });
      return;
    }

    instances.forEach((inst, index) => {
      const id = path + "/inst:" + index + ":" + (inst.name || "unnamed");
      const targetMod = moduleByName.get(inst.module || "");
      const node = makeNode(id, inst.name || "(unnamed)", "instance", inst.module || "instance", inst);
      node.depth = depth;
      node.expandable = Boolean(targetMod && hasVisibleChildren(targetMod));
      node.expanded = state.expanded.has(id);
      nodes.push(node);
      edges.push({ source: parentId, target: id, label: inst.module || "", kind: "hierarchy" });
      if (node.expanded) appendHierarchyChildren(targetMod, id, id, depth + 1, nodes, edges);
    });
  }

  function hasVisibleChildren(mod) {
    return Boolean(mod && Array.isArray(mod.instances) && mod.instances.length);
  }

  function rootNodeId(mod) {
    return "module:" + (mod && mod.name ? mod.name : "unknown");
  }

  function layoutHierarchyGraph(nodes, edges) {
    const positions = new Map();
    const depthCounts = new Map();
    let maxDepth = 0;
    let maxY = 0;
    nodes.forEach((node) => {
      const depth = node.depth || 0;
      const index = depthCounts.get(depth) || 0;
      depthCounts.set(depth, index + 1);
      maxDepth = Math.max(maxDepth, depth);
      const x = 60 + depth * 430;
      const y = 40 + index * 82;
      const w = node.type === "instance" ? 240 : 230;
      positions.set(node.id, { x, y, w, h: 58 });
      maxY = Math.max(maxY, y + 100);
    });
    return { nodes, edges, positions, width: Math.max(1280, 60 + (maxDepth + 1) * 430 + 280), height: Math.max(620, maxY + 80) };
  }

  function graphForModule(mod) {
    const nodes = [];
    const edges = [];
    const instances = mod.instances || [];
    nodes.push(makeNode("group:inputs", "Inputs", "group", String((mod.ports || []).filter((p) => p.direction === "input").length)));
    nodes.push(makeNode("group:outputs", "Outputs", "group", String((mod.ports || []).filter((p) => p.direction === "output").length)));
    nodes.push(makeNode("group:signals", "Internal signals", "group", String((mod.signals || []).length)));
    instances.forEach((inst, index) => nodes.push(makeNode("inst:" + index + ":" + inst.name, inst.name || "(unnamed)", "instance", inst.module || "instance", inst)));

    const signalNames = new Set((mod.signals || []).map((s) => s.name));
    instances.forEach((inst, index) => {
      const target = "inst:" + index + ":" + inst.name;
      let inputCount = 0;
      let internalCount = 0;
      (inst.port_connections || []).forEach((conn) => {
        const value = exprToText(conn.connection);
        if (!value) return;
        if (signalNames.has(value)) internalCount += 1;
        else inputCount += 1;
      });
      if (inputCount) edges.push({ source: "group:inputs", target, label: String(inputCount), kind: "summary" });
      if (internalCount) edges.push({ source: "group:signals", target, label: String(internalCount), kind: "summary" });
    });
    if ((mod.assignments || []).length) {
      edges.push({ source: "group:signals", target: "group:outputs", label: String(mod.assignments.length), kind: "summary" });
    }
    return layoutGraph(nodes, edges, "columns");
  }

  function graphForTrace(mod) {
    const term = state.trace.trim().toLowerCase();
    if (!term) {
      const node = makeNode("trace-empty", "Enter a trace query", "group", "signal, port, or instance");
      node.traceLane = "center";
      return layoutTraceGraph([node], []);
    }
    const nodes = new Map();
    const edges = [];
    const signalNames = new Set((mod.signals || []).map((s) => s.name));
    const add = (node) => nodes.set(node.id, node);

    (mod.instances || []).forEach((inst, index) => {
      const instId = "inst:" + index + ":" + inst.name;
      const instMatches = [inst.name, inst.module].join(" ").toLowerCase().includes(term);
      (inst.port_connections || []).forEach((conn) => {
        const value = exprToText(conn.connection);
        const hit = instMatches || String(conn.port || "").toLowerCase().includes(term) || value.toLowerCase().includes(term);
        if (!hit) return;
        const sigId = (signalNames.has(value) ? "signal:" : "external:") + value;
        const portId = "port:" + index + ":" + conn.port;
        const sigNode = makeNode(sigId, value || "(open)", signalNames.has(value) ? "signal" : "external", "signal/expression", conn);
        sigNode.traceLane = "source";
        const instNode = makeNode(instId, inst.name || "(unnamed)", "instance", inst.module || "instance", inst);
        instNode.traceLane = "instance";
        const portNode = makeNode(portId, conn.port || "(port)", "group", "port", conn);
        portNode.traceLane = "port";
        add(sigNode);
        add(instNode);
        add(portNode);
        edges.push({ source: sigId, target: instId, label: "", kind: "trace" });
        edges.push({ source: instId, target: portId, label: conn.port || "", kind: "trace" });
      });
    });

    (mod.assignments || []).forEach((assign) => {
      const lhs = exprToText(assign.lhs);
      const rhs = exprToText(assign.rhs);
      if (![lhs, rhs, assign.id].join(" ").toLowerCase().includes(term)) return;
      const lhsId = (signalNames.has(lhs) ? "signal:" : "external:") + lhs;
      const rhsId = (signalNames.has(rhs) ? "signal:" : "external:") + rhs;
      const assignId = "assign:" + (assign.id || lhs + ":" + rhs);
      const rhsNode = makeNode(rhsId, rhs, signalNames.has(rhs) ? "signal" : "external", "rhs", assign);
      rhsNode.traceLane = "source";
      const assignNode = makeNode(assignId, assign.id || "assign", "group", "assign", assign);
      assignNode.traceLane = "instance";
      const lhsNode = makeNode(lhsId, lhs, signalNames.has(lhs) ? "signal" : "external", "lhs", assign);
      lhsNode.traceLane = "port";
      add(rhsNode);
      add(assignNode);
      add(lhsNode);
      edges.push({ source: rhsId, target: assignId, label: "rhs", kind: "trace" });
      edges.push({ source: assignId, target: lhsId, label: "lhs", kind: "trace" });
    });

    if (!nodes.size) {
      const node = makeNode("trace-empty", "No trace result", "group", state.trace);
      node.traceLane = "center";
      add(node);
    }
    return layoutTraceGraph([...nodes.values()], edges);
  }

  function layoutTraceGraph(nodes, edges) {
    const positions = new Map();
    const lanes = { source: [], instance: [], port: [], center: [] };
    nodes.forEach((node) => (lanes[node.traceLane || "center"] || lanes.center).push(node));
    const xByLane = { source: 70, instance: 500, port: 930, center: 420 };
    let maxY = 0;
    Object.entries(lanes).forEach(([lane, list]) => {
      list.forEach((node, index) => {
        const y = 50 + index * 86;
        positions.set(node.id, { x: xByLane[lane], y, w: lane === "center" ? 280 : 260, h: 58 });
        maxY = Math.max(maxY, y + 92);
      });
    });
    return { nodes, edges, positions, width: 1260, height: Math.max(620, maxY + 80) };
  }

  function layoutGraph(nodes, edges, mode) {
    const positions = new Map();
    if (mode === "radial") {
      positions.set(nodes[0].id, { x: 520, y: 280, w: 230, h: 64 });
      const rest = nodes.slice(1);
      const radiusX = Math.max(360, Math.min(780, rest.length * 34));
      const radiusY = Math.max(220, Math.min(520, rest.length * 18));
      rest.forEach((node, i) => {
        const angle = (Math.PI * 2 * i) / Math.max(1, rest.length);
        positions.set(node.id, { x: 520 + Math.cos(angle) * radiusX, y: 280 + Math.sin(angle) * radiusY, w: 230, h: 58 });
      });
      return { nodes, edges, positions, width: radiusX * 2 + 1000, height: radiusY * 2 + 760 };
    }

    const columns = { group: [], module: [], instance: [], signal: [], external: [] };
    nodes.forEach((node) => (columns[node.type] || columns.group).push(node));
    [
      ["group", 60],
      ["module", 60],
      ["instance", 360],
      ["signal", 700],
      ["external", 1000],
    ].forEach(([type, x]) => {
      columns[type].forEach((node, i) => positions.set(node.id, { x, y: 40 + i * 82, w: type === "instance" ? 240 : 220, h: 58 }));
    });
    const maxCount = Math.max(...Object.values(columns).map((list) => list.length), 1);
    return { nodes, edges, positions, width: 1280, height: Math.max(620, 40 + maxCount * 82 + 80) };
  }

  function activeGraph() {
    const mod = currentModule();
    if (state.view === "module") return graphForModule(mod);
    if (state.view === "trace") return graphForTrace(mod);
    return graphForHierarchy(mod);
  }

  function renderModuleList() {
    const term = moduleSearch.value.trim().toLowerCase();
    moduleList.innerHTML = "";
    model.modules.forEach((mod, index) => {
      const haystack = [mod.name, ...mod.instances.map((i) => i.name), ...mod.instances.map((i) => i.module)].join(" ").toLowerCase();
      if (term && !haystack.includes(term)) return;
      const item = document.createElement("button");
      item.className = "module-item" + (index === state.moduleIndex ? " active" : "");
      item.innerHTML = `
        <div>
          <div class="module-name">${escapeHtml(mod.name)}${mod.isTop ? ' <span class="badge">top</span>' : ""}</div>
          <div class="module-meta">${mod.counts.instances} instances · ${mod.counts.signals} signals</div>
        </div>
        <span class="badge">${mod.counts.ports} ports</span>
      `;
      item.addEventListener("click", () => {
        navigateToModule(index);
        render();
      });
      moduleList.appendChild(item);
    });
  }

  function renderDiagram() {
    const graph = activeGraph();
    svg.innerHTML = "";
    svg.setAttribute("viewBox", "0 0 " + svg.clientWidth + " " + svg.clientHeight);
    const defs = el("defs", {}, svg);
    const marker = el("marker", { id: "arrow", viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, defs);
    el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#7d8da1" }, marker);
    const root = el("g", { transform: `translate(${state.tx} ${state.ty}) scale(${state.scale})` }, svg);
    el("rect", { x: 0, y: 0, width: graph.width, height: graph.height, fill: "rgba(255,255,255,.48)", stroke: "#d7dde5", rx: 8 }, root);
    const edgePathLayer = el("g", { class: "edge-path-layer" }, root);
    const edgeLabelLayer = el("g", { class: "edge-label-layer" }, root);
    const nodeLayer = el("g", {}, root);

    graph.edges.forEach((edge) => {
      const a = graph.positions.get(edge.source);
      const b = graph.positions.get(edge.target);
      if (!a || !b) return;
      const x1 = a.x + a.w;
      const y1 = a.y + a.h / 2;
      const x2 = b.x;
      const y2 = b.y + b.h / 2;
      const mid = Math.max(x1 + 34, (x1 + x2) / 2);
      const p = el("path", { d: `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`, class: "edge " + (edge.kind || "") }, edgePathLayer);
      p.addEventListener("click", (evt) => {
        evt.stopPropagation();
        state.selected = { type: "edge", data: edge };
        updateInspector();
      });
      if (edge.label) {
        const gap = Math.max(34, x2 - x1);
        const maxWidth = Math.max(28, Math.min(180, gap - 70));
        const labelX = x1 + 18 + maxWidth / 2;
        const labelY = (y1 + y2) / 2;
        drawEdgeLabel(edgeLabelLayer, edge.label, labelX, labelY, maxWidth);
      }
    });

    graph.nodes.forEach((node) => {
      const pos = graph.positions.get(node.id);
      if (!pos) return;
      const selected = state.selected && state.selected.data && state.selected.data.id === node.id;
      const g = el("g", { class: `node ${node.type}${selected ? " selected" : ""}`, transform: `translate(${pos.x} ${pos.y})`, tabindex: "0" }, nodeLayer);
      el("rect", { width: pos.w, height: pos.h }, g);
      el("title", {}, g).textContent = [node.label, node.detail].filter(Boolean).join(" · ");
      const title = el("text", { x: 13, y: 22, class: "node-title" }, g);
      title.textContent = fitTextToWidth(node.label, pos.w - (node.expandable ? 48 : 26), 13);
      const kind = el("text", { x: 13, y: 42, class: "node-kind" }, g);
      kind.textContent = fitTextToWidth(node.detail || node.type, pos.w - (node.expandable ? 48 : 26), 11);
      if (node.expandable) {
        const control = el("g", { class: "expand-control", transform: `translate(${pos.w - 25} 12)`, tabindex: "0" }, g);
        el("circle", { cx: 9, cy: 9, r: 9 }, control);
        const symbol = el("text", { x: 9, y: 13, "text-anchor": "middle" }, control);
        symbol.textContent = node.expanded ? "−" : "+";
        control.addEventListener("pointerdown", (evt) => evt.stopPropagation());
        control.addEventListener("click", (evt) => {
          evt.stopPropagation();
          toggleExpanded(node.id);
        });
        control.addEventListener("keydown", (evt) => {
          if (evt.key === "Enter" || evt.key === " ") {
            evt.preventDefault();
            evt.stopPropagation();
            toggleExpanded(node.id);
          }
        });
      }
      g.addEventListener("pointerdown", (evt) => evt.stopPropagation());
      g.addEventListener("click", (evt) => {
        evt.stopPropagation();
        handleNodeActivation(node);
      });
      g.addEventListener("keydown", (evt) => {
        if (evt.key === "Enter" || evt.key === " ") {
          evt.preventDefault();
          handleNodeActivation(node);
        }
      });
    });

    updateOverview();
    updateInspector();
  }

  function handleNodeActivation(node) {
    if (canDrillInto(node)) {
      drillInto(node);
      return;
    }
    state.selected = { type: "node", data: node };
    updateInspector();
    renderDiagram();
  }

  function drawEdgeLabel(parent, label, x, y, maxWidth) {
    const textValue = fitTextToWidth(label, maxWidth - 12, 11);
    const labelGroup = el("g", { class: "edge-label-group" }, parent);
    const estimatedWidth = Math.max(24, Math.min(maxWidth, textValue.length * 6.2 + 14));
    el("rect", {
      x: x - estimatedWidth / 2,
      y: y - 10,
      width: estimatedWidth,
      height: 20,
      rx: 5,
      ry: 5,
      class: "edge-label-bg",
    }, labelGroup);
    const text = el("text", { x, y, class: "edge-label", "text-anchor": "middle" }, labelGroup);
    text.textContent = textValue;
    el("title", {}, labelGroup).textContent = String(label || "");
  }

  function fitTextToWidth(value, maxWidth, fontSize) {
    const text = String(value || "");
    const avg = fontSize * 0.58;
    const maxChars = Math.max(4, Math.floor(maxWidth / avg));
    if (text.length <= maxChars) return text;
    return text.slice(0, Math.max(1, maxChars - 1)) + "…";
  }

  function drillInto(node) {
    let moduleName = "";
    let via = "";
    if (node.type === "instance") {
      moduleName = node.detail;
      via = node.label;
    } else if (node.type === "group" && moduleByName.has(node.label)) {
      moduleName = node.label;
      via = node.raw && Array.isArray(node.raw.instances) ? `${node.raw.instances.length}x` : "";
    } else if (node.type === "parent") {
      const parentIndex = model.modules.findIndex((m) => m.name === node.label);
      if (parentIndex >= 0) {
        navigateToModule(parentIndex);
        render();
      }
      return;
    }
    if (!moduleName || !moduleByName.has(moduleName)) return;
    pushModule(moduleName, via);
    resetViewPosition();
    render();
  }

  function canDrillInto(node) {
    const current = currentModule().name;
    if (!node) return false;
    if (node.type === "instance") return moduleByName.has(node.detail) && node.detail !== current;
    if (node.type === "group") return moduleByName.has(node.label) && node.label !== current;
    if (node.type === "parent") return moduleByName.has(node.label) && node.label !== current;
    return false;
  }

  function pushModule(moduleName, via) {
    const nextIndex = model.modules.findIndex((m) => m.name === moduleName);
    if (nextIndex < 0) return;
    state.moduleIndex = nextIndex;
    state.navStack.push({ moduleName, via: via || "" });
    resetHierarchyExpansion();
  }

  function navigateToModule(index) {
    const mod = model.modules[index];
    if (!mod) return;
    state.moduleIndex = index;
    state.navStack = [{ moduleName: mod.name, via: "" }];
    resetHierarchyExpansion();
    resetViewPosition();
  }

  function goToCrumb(index) {
    state.navStack = state.navStack.slice(0, index + 1);
    const mod = currentModule();
    state.moduleIndex = Math.max(0, model.modules.findIndex((m) => m.name === mod.name));
    resetHierarchyExpansion();
    resetViewPosition();
    render();
  }

  function toggleExpanded(nodeId) {
    if (state.expanded.has(nodeId)) state.expanded.delete(nodeId);
    else state.expanded.add(nodeId);
    state.selected = null;
    renderDiagram();
  }

  function expandAllTrees() {
    const btn = document.getElementById("expandAll");
    if (state.allExpanded) {
      resetHierarchyExpansion();
      state.allExpanded = false;
      btn.textContent = "Expand All";
    } else {
      const mod = currentModule();
      const rootId = rootNodeId(mod);
      state.expanded.clear();
      state.expanded.add(rootId);
      const visited = new Set();
      visited.add(mod.name);
      expandAllRecursive(mod, mod.name, visited);
      state.allExpanded = true;
      btn.textContent = "Collapse All";
    }
    state.selected = null;
    renderDiagram();
  }

  function expandAllRecursive(mod, path, visited) {
    const instances = mod.instances || [];
    if (instances.length > 50) {
      const byType = new Map();
      instances.forEach((inst) => {
        const type = inst.module || "unknown";
        if (!byType.has(type)) byType.set(type, []);
        byType.get(type).push(inst);
      });
      byType.forEach((list, type) => {
        const id = path + "/group:" + type;
        const targetMod = moduleByName.get(type);
        if (targetMod && hasVisibleChildren(targetMod) && !visited.has(type)) {
          state.expanded.add(id);
          visited.add(type);
          expandAllRecursive(targetMod, id, visited);
        }
      });
    } else {
      instances.forEach((inst, index) => {
        const id = path + "/inst:" + index + ":" + (inst.name || "unnamed");
        const targetMod = moduleByName.get(inst.module || "");
        if (targetMod && hasVisibleChildren(targetMod) && !visited.has(inst.module)) {
          state.expanded.add(id);
          visited.add(inst.module);
          expandAllRecursive(targetMod, id, visited);
        }
      });
    }
  }

  function resetHierarchyExpansion() {
    state.expanded = new Set();
    state.allExpanded = false;
    const mod = currentModule();
    if (mod && mod.name) state.expanded.add(rootNodeId(mod));
    const btn = document.getElementById("expandAll");
    if (btn) btn.textContent = "Expand All";
  }

  function updateHeader() {
    const mod = currentModule();
    const mode = state.view[0].toUpperCase() + state.view.slice(1);
    document.getElementById("activeTitle").textContent = mod.name || "No module";
    renderBreadcrumb();
    document.getElementById("activeMeta").textContent = `${mode} · ${mod.counts.ports || 0} ports · ${mod.counts.instances || 0} instances · ${mod.counts.signals || 0} signals`;
    document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === state.view));
  }

  function renderBreadcrumb() {
    const box = document.getElementById("breadcrumb");
    box.innerHTML = "";
    state.navStack.forEach((entry, index) => {
      if (index > 0) {
        box.appendChild(textSpan("/", "crumb-sep"));
        if (entry.via) {
          const via = textSpan(entry.via, "");
          via.title = entry.via;
          box.appendChild(via);
          box.appendChild(textSpan("/", "crumb-sep"));
        }
      }
      const btn = document.createElement("button");
      btn.className = "crumb";
      btn.textContent = entry.moduleName;
      btn.title = entry.moduleName;
      btn.disabled = index === state.navStack.length - 1;
      btn.addEventListener("click", () => goToCrumb(index));
      box.appendChild(btn);
    });
  }

  function textSpan(text, className) {
    const span = document.createElement("span");
    span.textContent = text;
    if (className) span.className = className;
    return span;
  }

  function updateOverview() {
    const mod = currentModule();
    const graph = activeGraph();
    const stats = [
      ["Visible nodes", graph.nodes.length],
      ["Visible edges", graph.edges.length],
      ["Instances", mod.counts.instances],
      ["Signals", mod.counts.signals],
    ];
    document.getElementById("overview").innerHTML = stats.map(([label, value]) => `<div class="stat"><strong>${value || 0}</strong><span>${label}</span></div>`).join("");
  }

  function updateInspector() {
    const selected = state.selected;
    const mod = currentModule();
    const summary = document.getElementById("summary");
    const jsonPanel = document.getElementById("jsonPanel");
    const hint = document.getElementById("inspectorHint");
    const connections = document.getElementById("connectionsPanel");

    if (!selected) {
      hint.textContent = "Module overview";
      summary.innerHTML = rows([
        ["module", mod.name],
        ["view", state.view],
        ["top", mod.isTop ? "yes" : "no"],
      ]);
      connections.innerHTML = moduleConnectionSummary(mod);
      jsonPanel.textContent = JSON.stringify({ name: mod.name, counts: mod.counts, ports: mod.ports.slice(0, 20), instances: mod.instances.slice(0, 20) }, null, 2);
      return;
    }

    if (selected.type === "edge") {
      const e = selected.data;
      hint.textContent = "Connection";
      summary.innerHTML = rows([
        ["source", e.source],
        ["target", e.target],
        ["label", e.label || "-"],
        ["kind", e.kind || "-"],
      ]);
      connections.innerHTML = '<div class="empty">Select an instance for port-level connections.</div>';
      jsonPanel.textContent = JSON.stringify(e, null, 2);
      return;
    }

    const n = selected.data;
    hint.textContent = n.type;
    summary.innerHTML = rows([
      ["name", n.label],
      ["type", n.type],
      ["detail", n.detail || "-"],
    ]);
    connections.innerHTML = instanceConnections(n.raw);
    jsonPanel.textContent = JSON.stringify(n.raw || n, null, 2);
  }

  function moduleConnectionSummary(mod) {
    const body = (mod.instances || []).slice(0, 18).map((inst) => {
      const count = (inst.port_connections || []).filter((c) => c.connection).length;
      return `<tr><td>${escapeHtml(inst.name || "")}</td><td>${escapeHtml(inst.module || "")}</td><td>${count}</td></tr>`;
    }).join("");
    if (!body) return '<div class="empty">No instances in this module.</div>';
    return `<table class="conn-table"><thead><tr><th>Instance</th><th>Module</th><th>Conns</th></tr></thead><tbody>${body}</tbody></table>`;
  }

  function instanceConnections(raw) {
    if (!raw || !Array.isArray(raw.port_connections)) return '<div class="empty">No port connections.</div>';
    const body = raw.port_connections.map((conn) => `<tr><td>${escapeHtml(conn.port || "")}</td><td>${escapeHtml(exprToText(conn.connection) || "-")}</td></tr>`).join("");
    return body ? `<table class="conn-table"><thead><tr><th>Port</th><th>Signal / Expr</th></tr></thead><tbody>${body}</tbody></table>` : '<div class="empty">No port connections.</div>';
  }

  function exprToText(expr) {
    if (expr == null) return "";
    if (typeof expr !== "object") return String(expr);
    for (const key of ["ref", "literal", "value", "name"]) if (key in expr) return String(expr[key]);
    if (expr.type === "bit_select" || expr.type === "select") {
      const source = exprToText(expr.source || expr.base);
      if (expr.index) return source + "[" + exprToText(expr.index) + "]";
      if (expr.range) return source + "[" + exprToText(expr.range.msb) + ":" + exprToText(expr.range.lsb) + "]";
      return source;
    }
    if (expr.type === "concat") return "{" + (expr.parts || []).map(exprToText).join(", ") + "}";
    if (expr.type === "cond") return exprToText(expr.condition) + " ? " + exprToText(expr.true_expr) + " : " + exprToText(expr.false_expr);
    if ("left" in expr && "right" in expr) return exprToText(expr.left) + " " + (expr.op || "?") + " " + exprToText(expr.right);
    if ("operand" in expr) return (expr.op || "") + exprToText(expr.operand);
    return JSON.stringify(expr);
  }

  function rows(items) {
    return items.map(([k, v]) => `<div>${escapeHtml(k)}</div><div>${escapeHtml(String(v ?? ""))}</div>`).join("");
  }

  function compact(text, max) {
    text = String(text || "");
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  function escapeHtml(value) {
    return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  }

  function resetViewPosition() {
    state.selected = null;
    state.scale = 1;
    state.tx = 60;
    state.ty = 60;
  }

  function render() {
    renderModuleList();
    updateHeader();
    renderDiagram();
  }

  function zoom(factor) {
    state.scale = Math.max(0.35, Math.min(2.6, state.scale * factor));
    renderDiagram();
  }

  document.querySelectorAll(".tab-btn").forEach((btn) => btn.addEventListener("click", () => {
    state.view = btn.dataset.view;
    if (state.view === "trace") traceInput.focus();
    resetViewPosition();
    render();
  }));
  document.getElementById("zoomIn").addEventListener("click", () => zoom(1.16));
  document.getElementById("zoomOut").addEventListener("click", () => zoom(0.86));
  document.getElementById("fitView").addEventListener("click", () => {
    resetViewPosition();
    renderDiagram();
  });
  document.getElementById("expandAll").addEventListener("click", () => {
    expandAllTrees();
  });

  document.getElementById("exportSvg").addEventListener("click", () => {
    const graph = activeGraph();
    const clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", NS);
    clone.setAttribute("viewBox", "0 0 " + graph.width + " " + graph.height);
    clone.setAttribute("width", graph.width);
    clone.setAttribute("height", graph.height);

    const rootG = clone.querySelector("g");
    if (rootG) rootG.setAttribute("transform", "translate(0, 0) scale(1)");

    const styleEl = document.createElement("style");
    let cssText = "";
    try {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            cssText += rule.cssText + "\n";
          }
        } catch (_) { /* cross-origin or inaccessible */ }
      }
    } catch (_) { /* ignore */ }
    styleEl.textContent = cssText;
    clone.insertBefore(styleEl, clone.firstChild);

    const svgString = new XMLSerializer().serializeToString(clone);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    const img = new Image();
    img.onload = () => {
      const scale = 2;
      const canvas = document.createElement("canvas");
      canvas.width = graph.width * scale;
      canvas.height = graph.height * scale;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#f9fbfd";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);
      ctx.drawImage(img, 0, 0);

      canvas.toBlob((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = (currentModule().name || "diagram") + "-" + state.view + ".png";
        a.click();
        URL.revokeObjectURL(a.href);
        URL.revokeObjectURL(url);
      }, "image/png");
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      alert("Failed to export PNG. The diagram may be too large.");
    };
    img.src = url;
  });
  moduleSearch.addEventListener("input", renderModuleList);
  traceInput.addEventListener("input", () => {
    state.trace = traceInput.value;
    if (state.trace && state.view !== "trace") state.view = "trace";
    resetViewPosition();
    render();
  });
  svg.addEventListener("click", () => {
    if (state.didDrag) return;
    state.selected = null;
    updateInspector();
    renderDiagram();
  });
  svg.addEventListener("wheel", (evt) => {
    evt.preventDefault();
    zoom(evt.deltaY < 0 ? 1.08 : 0.92);
  }, { passive: false });
  svg.addEventListener("pointerdown", (evt) => {
    state.dragging = true;
    state.didDrag = false;
    state.dragStart = { x: evt.clientX, y: evt.clientY, tx: state.tx, ty: state.ty };
    svg.classList.add("dragging");
    svg.setPointerCapture(evt.pointerId);
  });
  svg.addEventListener("pointermove", (evt) => {
    if (!state.dragging) return;
    const dx = evt.clientX - state.dragStart.x;
    const dy = evt.clientY - state.dragStart.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) state.didDrag = true;
    state.tx = state.dragStart.tx + dx;
    state.ty = state.dragStart.ty + dy;
    renderDiagram();
  });
  svg.addEventListener("pointerup", (evt) => {
    state.dragging = false;
    svg.classList.remove("dragging");
    if (svg.hasPointerCapture(evt.pointerId)) svg.releasePointerCapture(evt.pointerId);
    setTimeout(() => { state.didDrag = false; }, 0);
  });
  window.addEventListener("resize", renderDiagram);
  render();
})();
