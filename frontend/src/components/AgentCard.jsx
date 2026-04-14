import React from "react";
import {
  Search,
  ShieldCheck,
  Sparkles,
  Gauge,
  Database,
  GitBranch,
  Zap,
  Layout,
  Activity,
  Network
} from "lucide-react";

const iconMap = {
  Search,
  ShieldCheck,
  Sparkles,
  Gauge,
  Database,
  GitBranch,
  Zap,
  Layout,
  Activity,
  Network
};

export const AgentCard = ({ agent, index = 0 }) => {
  const Icon = iconMap[agent.icon];
  const padded = String(index + 1).padStart(2, "0");

  return (
    <div
      className="agent-card"
      style={{ animationDelay: `${index * 0.12}s` }}
    >
      <div className="agent-card-glow" />

      <span className="agent-index">{padded}</span>

      <div className="agent-icon-wrapper">
        {Icon && (
          <Icon
            className="agent-icon"
            size={28}
            strokeWidth={1.5}
            aria-hidden="true"
          />
        )}
      </div>

      <h3 className="agent-name">{agent.name}</h3>

      <p className="agent-description">{agent.description}</p>

      <div className="agent-metrics">
        {agent.metrics.map((metric) => (
          <div key={metric.label} className="metric-item">
            <span className="metric-label">{metric.label}</span>
            <span className="metric-value">
              {metric.value}{metric.unit}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};