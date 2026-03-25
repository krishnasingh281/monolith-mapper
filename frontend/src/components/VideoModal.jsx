import React, { useEffect } from "react";
import { X, Activity } from "lucide-react";

export const VideoModal = ({ isOpen, onClose }) => {

  // Close on ESC key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "auto";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="modal-close"
          onClick={onClose}
          aria-label="Close modal"
        >
          <X size={24} />
        </button>

        <div className="modal-body">
          <h2 className="modal-title">
            Product Demo Coming Soon
          </h2>

          <p className="modal-text">
            Watch how MonolithMapper transforms legacy
            codebases using our 4-agent workflow powered
            by GraphRAG and Tree-sitter AST parsing.
          </p>

          <div className="demo-placeholder">
            <Activity
              size={64}
              strokeWidth={1}
              className="demo-icon"
            />

            <p className="demo-text">
              Demo video will be available here
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};