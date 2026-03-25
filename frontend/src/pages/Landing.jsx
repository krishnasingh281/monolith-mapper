import React, { useState, useEffect, useMemo } from "react";
import Spline from "@splinetool/react-spline";
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

import { AgentCard } from "../components/AgentCard";
import { VideoModal } from "../components/VideoModal";

import {
  agents,
  techStack,
  observabilityMetrics,
  features,
  stats
} from "../mock/data";

export default function Landing() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  // Scroll listener
  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll);

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Stable particles (prevents re-render flicker)
  const particles = useMemo(
    () =>
      Array.from({ length: 20 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 5,
        duration: 6 + Math.random() * 10
      })),
    []
  );

  return (
    <div className="landing-page">

      {/* HEADER */}
      <header className="dark-header">
        <div className="header-content">
          <div className="logo-wrapper">
            <Code2 size={32} strokeWidth={1.5} className="logo-icon" />
            <span className="logo-text">MonolithMapper</span>
          </div>

          <nav className="dark-nav">
            <a href="#intelligence" className="dark-nav-link">
              Intelligence
            </a>
            <a href="#agents" className="dark-nav-link">
              Agents
            </a>
            <a href="#observability" className="dark-nav-link">
              Observability
            </a>
            <a href="#tech" className="dark-nav-link">
              Tech Stack
            </a>
          </nav>

          <button className="btn-primary btn-small">
            Get Started
            <ArrowRight size={18} />
          </button>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="hero-section">
        <div className="hero-grid">
          <div className="hero-content">
            <div
              className="hero-text"
              style={{
                transform: `translateY(${scrollY * 0.08}px)`,
                opacity: 1 - scrollY / 900
              }}
            >
              <h1 className="hero-title">
                Master Your
                <span className="hero-title-accent"> Monolith</span>
              </h1>

              <p className="hero-subtitle">
                Eliminate Knowledge Rot in millions of lines of legacy code
                with AI-powered GraphRAG. Four specialized agents retrieve,
                validate, generate, and evaluate every transformation.
              </p>

              <div className="hero-stats-inline">
                {stats.slice(0, 2).map((stat) => (
                  <div key={stat.id} className="stat-inline">
                    <span className="stat-value-inline">
                      {stat.display}
                    </span>
                    <span className="stat-label-inline">
                      {stat.label}
                    </span>
                  </div>
                ))}
              </div>

              <div className="hero-cta">
                <button className="btn-primary">
                  Get Started
                  <ArrowRight size={20} />
                </button>

                <button
                  className="btn-secondary"
                  onClick={() => setIsModalOpen(true)}
                >
                  <Play size={20} />
                  Watch Demo
                </button>
              </div>
            </div>
          </div>

          {/* 3D VISUAL */}
          <div className="hero-visual">
            <div className="spline-container">
              <Spline scene="https://prod.spline.design/NbVmy6DPLhY-5Lvg/scene.splinecode" />
            </div>

            <div className="visual-overlay-text">
              <span className="overlay-label">
                Live Knowledge Graph
              </span>
            </div>
          </div>
        </div>

        {/* PARTICLES */}
        <div className="particles-container">
          {particles.map((p) => (
            <div
              key={p.id}
              className="particle"
              style={{
                left: `${p.left}%`,
                animationDelay: `${p.delay}s`,
                animationDuration: `${p.duration}s`
              }}
            />
          ))}
        </div>
      </section>

      {/* INTELLIGENCE SECTION */}
      <section id="intelligence" className="intelligence-section">
        <div className="section-container">
          <div className="section-header-center">
            <h2 className="section-title">The Intelligence Layer</h2>
            <p className="section-subtitle">
              From raw source code to a queryable knowledge graph powered by
              Tree-sitter AST parsing and GraphRAG embeddings.
            </p>
          </div>

          <div className="intelligence-visual">
            <div className="ast-visualization">
              <div className="ast-node">
                <Database size={24} />
                <span>Source Files</span>
              </div>

              <div className="ast-connector"></div>

              <div className="ast-node">
                <GitBranch size={24} />
                <span>AST Parsing</span>
              </div>

              <div className="ast-connector"></div>

              <div className="ast-node accent">
                <Zap size={24} />
                <span>Knowledge Graph</span>
              </div>
            </div>

            <div className="features-grid">
              {features.map((feature) => (
                <div key={feature.id} className="feature-card">
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* AGENTS */}
      <section id="agents" className="agents-section">
        <div className="section-container">
          <div className="section-header-center">
            <h2 className="section-title">The Trust-Bridge</h2>
            <p className="section-subtitle">
              Four specialized AI agents orchestrate every code
              transformation with precision.
            </p>
          </div>

          <div className="agents-grid">
            {agents.map((agent, i) => (
              <AgentCard key={agent.id} agent={agent} index={i} />
            ))}
          </div>

          <div className="workflow-diagram">
            <div className="workflow-line"></div>
            <div className="workflow-steps">
              <div className="workflow-step">Retrieve</div>
              <div className="workflow-arrow">→</div>
              <div className="workflow-step">Validate</div>
              <div className="workflow-arrow">→</div>
              <div className="workflow-step">Generate</div>
              <div className="workflow-arrow">→</div>
              <div className="workflow-step">Evaluate</div>
            </div>
          </div>
        </div>
      </section>

      {/* OBSERVABILITY */}
      <section id="observability" className="observability-section">
        <div className="section-container">
          <div className="section-header-center">
            <h2 className="section-title">Live Observability</h2>
            <p className="section-subtitle">
              Real-time performance monitoring with Langfuse.
            </p>
          </div>

          <div className="dashboard-metrics">
            <MetricCard
              icon={TrendingUp}
              value={observabilityMetrics.totalRequests}
              label="Total Requests"
            />
            <MetricCard
              icon={Zap}
              value={`${observabilityMetrics.avgLatency}ms`}
              label="Avg Latency"
            />
            <MetricCard
              icon={Database}
              value={`${observabilityMetrics.successRate}%`}
              label="Success Rate"
            />
            <MetricCard
              icon={Code2}
              value={observabilityMetrics.tokensProcessed}
              label="Tokens Processed"
            />
          </div>

          <div className="trace-viewer">
            {observabilityMetrics.traces[0].steps.map((step, i) => (
              <div key={i} className="trace-step">
                <div className="trace-step-info">
                  <span className="trace-step-name">{step.name}</span>
                  <span className="trace-step-time">{step.time}ms</span>
                </div>

                <div className="trace-step-bar">
                  <div
                    className="trace-step-progress"
                    style={{
                      width: `${Math.min(
                        (step.time / 1000) * 100,
                        100
                      )}%`
                    }}
                  />
                </div>

                <span className="trace-step-tokens">
                  {step.tokens} tokens
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TECH STACK */}
      <section id="tech" className="tech-stack-section">
        <div className="section-container">
          <h2 className="section-title-center">
            Powered By Enterprise-Grade Technology
          </h2>

          <div className="tech-marquee">
            <div className="tech-marquee-content">
              {[...techStack, ...techStack].map((tech, i) => {
                const Icon = iconMap[tech.icon];
                return (
                  <div key={i} className="tech-item">
                    {Icon && <Icon size={28} />}
                    <span>{tech.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-left">
            <Code2 size={28} className="footer-logo-icon" />
            <span className="footer-brand">MonolithMapper</span>
          </div>

          <div className="footer-right">
            <span className="footer-text">
              © 2026 MonolithMapper — Eliminating Knowledge Rot
            </span>
          </div>
        </div>
      </footer>

      <VideoModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}

/* Metric Card Component */
function MetricCard({ icon: Icon, value, label }) {
  return (
    <div className="metric-card">
      <Icon size={24} className="metric-icon" />
      <div className="metric-data">
        <span className="metric-value-large">{value}</span>
        <span className="metric-label-large">{label}</span>
      </div>
    </div>
  );
}

/* Icon Map */
const iconMap = {
  Database,
  GitBranch,
  Zap,
  Layout,
  Activity,
  Network
};