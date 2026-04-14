import React, { useState, useEffect, useRef, useMemo } from "react";
import KnowledgeGraph from "../components/KnowledgeGraph";
import {
  ArrowRight,
  Play,
  Code2,
  Database,
  Zap,
  TrendingUp,
  GitBranch,
  Layout,
  Activity,
  Network
} from "lucide-react";

import { AgentCard } from "../components/AgentCard"; // ← fixed: matches filename AgentsCard.jsx
import { VideoModal } from "../components/VideoModal";

import {
  agents,
  techStack,
  observabilityMetrics,
  features,
  stats
} from "../mock/data";

// ── Icon Map (hoisted above JSX that uses it) ────────────────
const iconMap = {
  Database,
  GitBranch,
  Zap,
  Layout,
  Activity,
  Network,
};

// ─── Custom cursor hook ───────────────────────────────────────
function useCursor() {
  const dotRef = useRef(null);
  const ringRef = useRef(null);

  useEffect(() => {
    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    let mouseX = 0, mouseY = 0;
    let ringX = 0, ringY = 0;
    let rafId;

    const onMove = (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      dot.style.left = mouseX + "px";
      dot.style.top  = mouseY + "px";
    };

    const lerp = (a, b, t) => a + (b - a) * t;

    const animate = () => {
      ringX = lerp(ringX, mouseX, 0.12);
      ringY = lerp(ringY, mouseY, 0.12);
      ring.style.left = ringX + "px";
      ring.style.top  = ringY + "px";
      rafId = requestAnimationFrame(animate);
    };

    const onEnter = () => ring.classList.add("hovering");
    const onLeave = () => ring.classList.remove("hovering");

    document.addEventListener("mousemove", onMove);
    const interactive = document.querySelectorAll("a, button, .agent-card, .feature-card, .tech-item");
    interactive.forEach(el => {
      el.addEventListener("mouseenter", onEnter);
      el.addEventListener("mouseleave", onLeave);
    });

    rafId = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return { dotRef, ringRef };
}

// ─── Scroll reveal hook ──────────────────────────────────────
function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) entry.target.classList.add("visible");
        });
      },
      { threshold: 0.12 }
    );
    els.forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);
}

// ─── MetricCard ──────────────────────────────────────────────
function MetricCard({ icon: Icon, value, label }) {
  return (
    <div className="metric-card">
      <Icon size={22} className="metric-icon" />
      <div className="metric-data">
        <span className="metric-value-large">{value}</span>
        <span className="metric-label-large">{label}</span>
      </div>
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────
export default function Landing() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [headerScrolled, setHeaderScrolled] = useState(false);
  const { dotRef, ringRef } = useCursor();
  useReveal();

  useEffect(() => {
    const handleScroll = () => {
      const y = window.scrollY;
      setScrollY(y);
      setHeaderScrolled(y > 60);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const particles = useMemo(
    () =>
      Array.from({ length: 28 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 8,
        duration: 8 + Math.random() * 12,
        size: 1 + Math.random() * 2,
      })),
    []
  );

  return (
    <div className="landing-page">
      <div className="cursor-dot" ref={dotRef} />
      <div className="cursor-ring" ref={ringRef} />
      <div className="noise-overlay" />
      <div className="scan-lines" />

      {/* ── HEADER ───────────────────────────────── */}
      <header className={`dark-header${headerScrolled ? " scrolled" : ""}`}>
        <div className="header-content">
          <div className="logo-wrapper">
            <Code2 size={28} strokeWidth={1.5} className="logo-icon" />
            <span className="logo-text">MonolithMapper</span>
          </div>
          <nav className="dark-nav">
            {["Intelligence", "Agents", "Observability", "Tech Stack"].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase().replace(" ", "-")}`}
                className="dark-nav-link"
              >
                {item}
              </a>
            ))}
          </nav>
          <button className="btn-primary btn-small">
            Get Started <ArrowRight size={16} />
          </button>
        </div>
      </header>

      {/* ── HERO ─────────────────────────────────── */}
      <section className="hero-section">
        <div className="hero-grid">
          <div className="hero-content">
            <div
              style={{
                transform: `translateY(${scrollY * 0.06}px)`,
                opacity: Math.max(0, 1 - scrollY / 700),
              }}
            >
              <div className="hero-eyebrow">
                <span className="hero-eyebrow-dot" />
                <span className="hero-eyebrow-text">AI-Powered Legacy Modernization</span>
              </div>
              <h1 className="hero-title">
                <span className="hero-title-line">Master Your</span>
                <span className="hero-title-line">
                  <span className="hero-title-accent" data-text="Monolith">
                    Monolith
                  </span>
                </span>
              </h1>
              <p className="hero-subtitle">
                Eliminate Knowledge Rot in millions of lines of legacy code
                with AI-powered GraphRAG. Four specialized agents retrieve,
                validate, generate, and evaluate every transformation.
              </p>
              <div className="hero-stats-inline">
                {stats.slice(0, 2).map((stat) => (
                  <div key={stat.id} className="stat-inline">
                    <span className="stat-value-inline">{stat.display}</span>
                    <span className="stat-label-inline">{stat.label}</span>
                  </div>
                ))}
              </div>
              <div className="hero-cta">
                <button className="btn-primary">
                  Get Started <ArrowRight size={18} />
                </button>
                <button className="btn-secondary" onClick={() => setIsModalOpen(true)}>
                  <Play size={18} />
                  <span>Watch Demo</span>
                </button>
              </div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="knowledge-graph-container">
              <KnowledgeGraph />
            </div>
          </div>
        </div>

        <div className="particles-container">
          {particles.map((p) => (
            <div
              key={p.id}
              className="particle"
              style={{
                left: `${p.left}%`,
                width: `${p.size}px`,
                height: `${p.size}px`,
                animationDelay: `${p.delay}s`,
                animationDuration: `${p.duration}s`,
              }}
            />
          ))}
        </div>
      </section>

      {/* ── INTELLIGENCE ─────────────────────────── */}
      <section id="intelligence" className="intelligence-section">
        <div className="section-container">
          <div className="section-header-center reveal">
            <div className="section-label">The Intelligence Layer</div>
            <h2 className="section-title">From Code to Knowledge</h2>
            <p className="section-subtitle">
              Raw source code becomes a queryable knowledge graph powered by
              Tree-sitter AST parsing and GraphRAG embeddings.
            </p>
          </div>
          <div className="intelligence-visual">
            <div className="ast-visualization reveal reveal-delay-1">
              <div className="ast-node">
                <Database size={20} />
                <span>Source Files</span>
              </div>
              <div className="ast-connector" />
              <div className="ast-node">
                <GitBranch size={20} />
                <span>AST Parsing</span>
              </div>
              <div className="ast-connector" />
              <div className="ast-node accent">
                <Zap size={20} />
                <span>Knowledge Graph</span>
              </div>
            </div>
            <div className="features-grid reveal reveal-delay-2">
              {features.map((feature, i) => (
                <div key={feature.id} className="feature-card">
                  <div className="feature-number">0{i + 1}</div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── AGENTS ───────────────────────────────── */}
      <section id="agents" className="agents-section">
        <div className="section-container">
          <div className="section-header-center reveal">
            <div className="section-label">Agentic Architecture</div>
            <h2 className="section-title">The Trust-Bridge</h2>
            <p className="section-subtitle">
              Four specialized AI agents orchestrate every code
              transformation with precision and verifiability.
            </p>
          </div>
          <div className="agents-grid">
            {agents.map((agent, i) => (
              <div key={agent.id} className={`reveal reveal-delay-${(i % 2) + 1}`}>
                <AgentCard agent={agent} index={i} />
              </div>
            ))}
          </div>
          <div className="workflow-diagram reveal">
            <div className="workflow-steps">
              {["Retrieve", "Validate", "Generate", "Evaluate"].map((step, i) => (
                <React.Fragment key={step}>
                  <div className="workflow-step">{step}</div>
                  {i < 3 && <div className="workflow-arrow">→</div>}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── OBSERVABILITY ────────────────────────── */}
      <section id="observability" className="observability-section">
        <div className="section-container">
          <div className="section-header-center reveal">
            <div className="section-label">Live Observability</div>
            <h2 className="section-title">Real-Time Intelligence</h2>
            <p className="section-subtitle">
              Continuous performance monitoring with Langfuse — zero blind spots,
              zero knowledge rot.
            </p>
          </div>
          <div className="dashboard-metrics reveal">
            <MetricCard icon={TrendingUp} value={observabilityMetrics.totalRequests} label="Total Requests" />
            <MetricCard icon={Zap} value={`${observabilityMetrics.avgLatency}ms`} label="Avg Latency" />
            <MetricCard icon={Database} value={`${observabilityMetrics.successRate}%`} label="Success Rate" />
            <MetricCard icon={Code2} value="2.4M" label="Tokens Processed" />
          </div>
          <div className="trace-viewer reveal reveal-delay-1">
            <div className="trace-header">
              <span className="trace-dot" />
              <span className="trace-header-text">
                TRACE — Code Modernization — 1200ms — SUCCESS
              </span>
            </div>
            {observabilityMetrics.traces[0].steps.map((step, i) => (
              <div key={i} className="trace-step">
                <div className="trace-step-info">
                  <span className="trace-step-name">{step.name}</span>
                  <span className="trace-step-time">{step.time}ms</span>
                </div>
                <div className="trace-step-bar">
                  <div
                    className="trace-step-progress"
                    style={{ width: `${Math.min((step.time / 1000) * 100, 100)}%` }}
                  />
                </div>
                <span className="trace-step-tokens">{step.tokens} tok</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TECH STACK ───────────────────────────── */}
      <section id="tech-stack" className="tech-stack-section">
        <div className="section-container">
          <h2 className="section-title-center reveal">
            Powered By Enterprise-Grade Technology
          </h2>
        </div>
        <div className="tech-marquee">
          <div className="tech-marquee-content">
            {[...techStack, ...techStack].map((tech, i) => {
              const Icon = iconMap[tech.icon];
              return (
                <div key={i} className="tech-item">
                  {Icon && <Icon size={22} />}
                  <span>{tech.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────── */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-left">
            <Code2 size={24} className="footer-logo-icon" />
            <span className="footer-brand">MonolithMapper</span>
          </div>
          <span className="footer-text">
            © 2026 MonolithMapper — Eliminating Knowledge Rot
          </span>
        </div>
      </footer>

      <VideoModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}