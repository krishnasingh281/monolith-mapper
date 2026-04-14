import React, { useEffect, useRef, useState } from "react";

const NODE_DEFS = [
  { label: "UserService.java",  type: "file",     color: "#00ffd1", desc: "User authentication & management" },
  { label: "OrderRepo.js",      type: "file",     color: "#00ffd1", desc: "Order data repository" },
  { label: "PaymentAPI.py",     type: "file",     color: "#00ffd1", desc: "Payment gateway integration" },
  { label: "AuthModule.ts",     type: "file",     color: "#00ffd1", desc: "Authorization middleware" },
  { label: "DB Schema",         type: "schema",   color: "#4488ff", desc: "Database architecture" },
  { label: "GraphRAG",          type: "core",     color: "#00ffd1", desc: "Central knowledge graph" },
  { label: "AST Tree",          type: "ast",      color: "#ff8844", desc: "Abstract syntax tree" },
  { label: "LegacyCore.java",   type: "file",     color: "#00ffd1", desc: "Legacy system core" },
  { label: "EventBus.ts",       type: "file",     color: "#00ffd1", desc: "Event-driven messaging" },
  { label: "KnowledgeNode",     type: "knowledge",color: "#b388ff", desc: "AI knowledge extraction" },
  { label: "DepGraph",          type: "schema",   color: "#4488ff", desc: "Dependency mapping" },
  { label: "Config.yml",        type: "file",     color: "#00ffd1", desc: "System configuration" },
  { label: "CacheLayer.rs",     type: "file",     color: "#00ffd1", desc: "Performance caching" },
  { label: "Embeddings",        type: "knowledge",color: "#b388ff", desc: "Vector embeddings" },
  { label: "EntryPoint",        type: "ast",      color: "#ff8844", desc: "Application entry" },
];

const EDGES = [
  [0,5],[1,5],[2,5],[3,5],[4,5],[6,5],[7,5],[8,5],
  [9,5],[10,5],[11,5],[12,5],[13,5],[14,5],
  [0,6],[1,4],[2,4],[3,6],[7,14],[8,10],
  [9,13],[11,12],[4,10],[6,14],[13,9],
];

function hexAlpha(n) {
  return Math.round(n * 255).toString(16).padStart(2, "0");
}

function initNodes(W, H) {
  const cx = W * 0.5, cy = H * 0.5;
  return NODE_DEFS.map((def, i) => {
    if (i === 5) {
      return {
        ...def,
        id: i,
        x: cx,
        y: cy,
        vx: 0,
        vy: 0,
        radius: 38,
        pulsePhase: 0,
        opacity: 1,
        hoverScale: 1,
        targetHoverScale: 1,
      };
    }
    const angle = (i / (NODE_DEFS.length - 1)) * Math.PI * 2;
    const dist = i % 2 === 0 ? 130 + (i % 5) * 14 : 195 + (i % 4) * 12;
    return {
      ...def,
      id: i,
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      radius: def.type === "knowledge" ? 22 : def.type === "schema" ? 20 : 18,
      pulsePhase: Math.random() * Math.PI * 2,
      opacity: 0.85 + Math.random() * 0.15,
      hoverScale: 1,
      targetHoverScale: 1,
    };
  });
}

function initPulses() {
  return EDGES.map((edge) => ({
    edge,
    t: Math.random(),
    speed: 0.003 + Math.random() * 0.004,
    size: 3 + Math.random() * 2,
    delay: Math.floor(Math.random() * 80),
    highlighted: false,
  }));
}

export default function KnowledgeGraph() {
  const canvasRef = useRef(null);
  const stateRef = useRef(null);
  const rafRef   = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, node: null });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width  = rect.width  * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width  = rect.width  + "px";
      canvas.style.height = rect.height + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      stateRef.current = {
        W: rect.width,
        H: rect.height,
        nodes: initNodes(rect.width, rect.height),
        pulses: initPulses(),
        frame: 0,
        hoveredNodeId: null,
        connectedNodes: new Set(),
      };
    };

    resize();
    window.addEventListener("resize", resize);

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const s = stateRef.current;
      if (!s) return;

      let foundNode = null;
      let minDist = Infinity;

      for (const node of s.nodes) {
        const dx = mouseX - node.x;
        const dy = mouseY - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < node.radius * node.hoverScale + 10 && dist < minDist) {
          foundNode = node;
          minDist = dist;
        }
      }

      if (foundNode) {
        s.hoveredNodeId = foundNode.id;
        canvas.style.cursor = "pointer";
        s.connectedNodes.clear();
        EDGES.forEach(([a, b]) => {
          if (a === foundNode.id) s.connectedNodes.add(b);
          if (b === foundNode.id) s.connectedNodes.add(a);
        });
        s.connectedNodes.add(foundNode.id);
        s.pulses.forEach(p => {
          const [a, b] = p.edge;
          p.highlighted = (a === foundNode.id || b === foundNode.id);
        });
        setTooltip({ show: true, x: e.clientX, y: e.clientY, node: foundNode });
        setHoveredNode(foundNode.id);
      } else {
        s.hoveredNodeId = null;
        s.connectedNodes.clear();
        s.pulses.forEach(p => { p.highlighted = false; });
        canvas.style.cursor = "default";
        setTooltip({ show: false, x: 0, y: 0, node: null });
        setHoveredNode(null);
      }
    };

    canvas.addEventListener("mousemove", handleMouseMove);

    const draw = () => {
      const s = stateRef.current;
      if (!s) { rafRef.current = requestAnimationFrame(draw); return; }
      const { W, H, nodes, pulses, connectedNodes, hoveredNodeId } = s;
      s.frame++;
      const f = s.frame;

      ctx.clearRect(0, 0, W, H);
      const CENTER = nodes[5];

      nodes.forEach(n => {
        n.targetHoverScale = n.id === hoveredNodeId ? 1.3 : connectedNodes.has(n.id) ? 1.15 : 1;
        n.hoverScale += (n.targetHoverScale - n.hoverScale) * 0.15;
      });

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n.id === 5) continue;
        n.x += n.vx; n.y += n.vy;
        const dx = CENTER.x - n.x, dy = CENTER.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        if (dist < 100) { n.vx -= (dx / dist) * 0.07; n.vy -= (dy / dist) * 0.07; }
        else if (dist > 270) { n.vx += (dx / dist) * 0.04; n.vy += (dy / dist) * 0.04; }
        n.vx *= 0.98; n.vy *= 0.98;
        const mg = n.radius + 20;
        if (n.x < mg) n.vx += 0.08; if (n.x > W - mg) n.vx -= 0.08;
        if (n.y < mg) n.vy += 0.08; if (n.y > H - mg) n.vy -= 0.08;
      }

      EDGES.forEach(([a, b]) => {
        const nA = nodes[a], nB = nodes[b];
        const isCentral = a === 5 || b === 5;
        const isHighlighted = connectedNodes.has(a) && connectedNodes.has(b);
        let alpha = isCentral ? 0.32 : 0.16;
        let lineWidth = isCentral ? 1 : 0.5;
        if (isHighlighted) { alpha = 0.8; lineWidth = 2; }
        const grd = ctx.createLinearGradient(nA.x, nA.y, nB.x, nB.y);
        grd.addColorStop(0, nA.color + hexAlpha(alpha));
        grd.addColorStop(1, nB.color + hexAlpha(alpha * 0.5));
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(nA.x, nA.y);
        ctx.lineTo(nB.x, nB.y);
        ctx.strokeStyle = grd;
        ctx.lineWidth = lineWidth;
        if (isHighlighted) { ctx.shadowColor = nA.color; ctx.shadowBlur = 15; }
        ctx.stroke();
        ctx.restore();
      });

      pulses.forEach(p => {
        if (p.delay > 0) { p.delay--; return; }
        p.t += p.speed * (p.highlighted ? 2 : 1);
        if (p.t > 1) p.t = 0;
        const [a, b] = p.edge;
        const nA = nodes[a], nB = nodes[b];
        const px = nA.x + (nB.x - nA.x) * p.t;
        const py = nA.y + (nB.y - nA.y) * p.t;
        const col = (a === 5 || b === 5) ? "#00ffd1" : nodes[a].color;
        const size = p.highlighted ? p.size * 1.5 : p.size;
        ctx.save();
        const grd = ctx.createRadialGradient(px, py, 0, px, py, size * 3);
        grd.addColorStop(0, col + "ff");
        grd.addColorStop(1, col + "00");
        ctx.beginPath();
        ctx.arc(px, py, size * 3, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.globalAlpha = p.highlighted ? 0.95 : 0.75;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(px, py, size * 0.6, 0, Math.PI * 2);
        ctx.fillStyle = "#fff";
        ctx.globalAlpha = p.highlighted ? 1 : 0.95;
        ctx.fill();
        ctx.restore();
      });

      nodes.forEach(n => {
        const isHovered = n.id === hoveredNodeId;
        const isConnected = connectedNodes.has(n.id) && !isHovered;
        const pulse = Math.sin(f * 0.04 + n.pulsePhase) * 0.1;
        const r = n.radius * (1 + pulse) * n.hoverScale;
        ctx.save();
        if (n.id === 5 || n.type === "knowledge" || isHovered || isConnected) {
          const glowIntensity = isHovered ? 30 : isConnected ? 20 : 16;
          const gr = r + glowIntensity + Math.sin(f * 0.05 + n.pulsePhase) * 5;
          const g = ctx.createRadialGradient(n.x, n.y, r * 0.5, n.x, n.y, gr + 10);
          g.addColorStop(0, n.color + (isHovered ? "50" : "28"));
          g.addColorStop(1, n.color + "00");
          ctx.beginPath();
          ctx.arc(n.x, n.y, gr + 10, 0, Math.PI * 2);
          ctx.fillStyle = g;
          ctx.fill();
        }
        if (isHovered) { ctx.shadowColor = n.color; ctx.shadowBlur = 30; }
        const bg = ctx.createRadialGradient(n.x - r * 0.3, n.y - r * 0.3, 0, n.x, n.y, r);
        bg.addColorStop(0, n.color + (isHovered ? "40" : "20"));
        bg.addColorStop(1, n.color + (isHovered ? "15" : "06"));
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = bg;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.strokeStyle = n.color + (isHovered ? "ff" : (n.id === 5 ? "cc" : "55"));
        ctx.lineWidth = isHovered ? 3 : (n.id === 5 ? 2 : 1);
        ctx.stroke();
        if (n.id !== 5) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, isHovered ? 6 : 4, 0, Math.PI * 2);
          ctx.fillStyle = n.color;
          ctx.globalAlpha = isHovered ? 1 : 0.85;
          ctx.fill();
        } else {
          ctx.strokeStyle = "#00ffd1";
          ctx.lineWidth = isHovered ? 2 : 1;
          ctx.globalAlpha = isHovered ? 0.8 : 0.5;
          const crossSize = isHovered ? 18 : 14;
          ctx.beginPath();
          ctx.moveTo(n.x - crossSize, n.y); ctx.lineTo(n.x + crossSize, n.y);
          ctx.moveTo(n.x, n.y - crossSize); ctx.lineTo(n.x, n.y + crossSize);
          ctx.stroke();
        }
        ctx.restore();

        ctx.save();
        const fontSize = isHovered ? 12 : (n.id === 5 ? 11 : 10);
        ctx.font = n.id === 5
          ? `bold ${fontSize}px 'Space Mono', monospace`
          : `${fontSize}px 'Space Mono', monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const lY = n.y + r + 14;
        const tw = ctx.measureText(n.label).width + 10;
        ctx.fillStyle = isHovered ? "rgba(0,255,209,0.15)" : "rgba(0,0,0,0.7)";
        ctx.fillRect(n.x - tw / 2, lY - 7, tw, 14);
        if (isHovered || isConnected) {
          ctx.strokeStyle = n.color + (isHovered ? "aa" : "44");
          ctx.lineWidth = 1;
          ctx.strokeRect(n.x - tw / 2, lY - 7, tw, 14);
        }
        ctx.fillStyle = isHovered ? "#00ffd1" : (n.id === 5 ? "#00ffd1" : "rgba(255,255,255,0.65)");
        ctx.globalAlpha = isHovered ? 1 : n.opacity;
        ctx.fillText(n.label, n.x, lY);
        ctx.restore();
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      canvas.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <canvas
        ref={canvasRef}
        style={{ display: "block", width: "100%", height: "100%" }}
      />

      {tooltip.show && tooltip.node && (
        <div
          style={{
            position: "fixed",
            left: tooltip.x + 15,
            top: tooltip.y + 15,
            background: "rgba(0,0,0,0.95)",
            border: "1px solid #00ffd1",
            padding: "12px 16px",
            borderRadius: "0px",
            pointerEvents: "none",
            zIndex: 1000,
            backdropFilter: "blur(10px)",
            boxShadow: "0 0 20px rgba(0,255,209,0.3)",
            animation: "tooltipFadeIn 0.2s ease",
          }}
        >
          <div style={{ fontFamily: "'Space Mono', monospace", fontSize: "11px", color: "#00ffd1", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            {tooltip.node.type}
          </div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontSize: "14px", color: "#fff", fontWeight: 700, marginBottom: "6px" }}>
            {tooltip.node.label}
          </div>
          <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: "12px", color: "rgba(255,255,255,0.7)", maxWidth: "200px" }}>
            {tooltip.node.desc}
          </div>
        </div>
      )}

      <div style={hudStyle("topLeft")}>
        <span style={hudText}>NODES {NODE_DEFS.length}</span>
        <span style={hudText}>EDGES {EDGES.length}</span>
        {hoveredNode !== null && <span style={{ ...hudText, color: "#00ffd1" }}>SELECTED</span>}
      </div>
      <div style={hudStyle("topRight")}>
        <span style={{ ...hudText, color: "#00ffd1" }}>● LIVE</span>
      </div>
      <div style={hudStyle("bottomLeft")}>
        <span style={hudText}>GraphRAG v2.4</span>
      </div>
      <div style={hudStyle("bottomRight")}>
        <span style={hudText}>KNOWLEDGE GRAPH</span>
      </div>

      <style>{`
        @keyframes tooltipFadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function hudStyle(pos) {
  const base = {
    position: "absolute",
    display: "flex",
    flexDirection: "column",
    gap: 3,
    padding: "6px 10px",
    border: "1px solid rgba(0,255,209,0.15)",
    background: "rgba(0,0,0,0.65)",
    backdropFilter: "blur(8px)",
    pointerEvents: "none",
  };
  if (pos === "topLeft")     return { ...base, top: 12, left: 12 };
  if (pos === "topRight")    return { ...base, top: 12, right: 12 };
  if (pos === "bottomLeft")  return { ...base, bottom: 12, left: 12 };
  if (pos === "bottomRight") return { ...base, bottom: 12, right: 12 };
}

const hudText = {
  fontFamily: "'Space Mono', monospace",
  fontSize: 9,
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  color: "rgba(255,255,255,0.4)",
};