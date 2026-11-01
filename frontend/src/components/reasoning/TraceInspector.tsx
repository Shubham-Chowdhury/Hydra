import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Network,
  AlertOctagon,
  FileText,
  ArrowRight,
  GitBranch,
  Layers,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import type { ProgrammeEvaluationDto, ReasoningTreeNodeDto } from '../../api/types';

interface TraceInspectorProps {
  evaluation: ProgrammeEvaluationDto;
}

const statusBadge = (status: string) => {
  const isSatisfied = status === 'SATISFIED' || status === 'eligible';
  const isViolated = status === 'VIOLATED' || status === 'ineligible';
  if (isSatisfied) {
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3" />
        {status}
      </span>
    );
  }
  if (isViolated) {
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-rose-950 text-rose-400 border border-rose-800 flex items-center gap-1">
        <XCircle className="w-3 h-3" />
        {status}
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-1">
      <AlertCircle className="w-3 h-3" />
      {status}
    </span>
  );
};

const sourceTypeBadge = (sourceType?: string) => {
  switch (sourceType) {
    case 'inherited':
      return (
        <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-800/60 font-mono">
          inherited
        </span>
      );
    case 'traversed':
      return (
        <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 font-mono">
          traversed
        </span>
      );
    case 'direct':
    default:
      return (
        <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 font-mono">
          direct
        </span>
      );
  }
};

const ReasoningNodeView: React.FC<{ node: ReasoningTreeNodeDto; depth?: number }> = ({
  node,
  depth = 0,
}) => {
  const hasChildren = node.children && node.children.length > 0;
  const isComposite = node.expression_type === 'ALL_OF' || node.expression_type === 'ANY_OF';

  return (
    <div
      className={`rounded bg-slate-950 border border-slate-800/80 p-2.5 space-y-1.5 ${
        depth > 0 ? 'ml-3 border-l-2 border-l-cyan-600/40' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          {isComposite ? (
            <span className="px-1.5 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800/60 font-mono text-[10px] font-bold">
              {node.expression_type === 'ALL_OF' ? 'ALL OF (Conjunction)' : 'ANY OF (Disjunction)'}
            </span>
          ) : (
            <span className="font-mono text-cyan-300 font-medium text-xs">
              {node.node_id}
            </span>
          )}
          <span className="text-[10px] text-slate-400 font-mono">
            {node.is_mandatory ? '[mandatory]' : '[optional]'}
          </span>
          {node.provenance && (
            <span className="text-[10px] text-purple-300 font-mono bg-purple-950/50 px-1 rounded">
              prov: {node.provenance}
            </span>
          )}
        </div>
        {statusBadge(node.status)}
      </div>

      {node.explanation && (
        <p className="text-slate-300 text-xs">{node.explanation}</p>
      )}

      {!isComposite && (
        <div className="grid grid-cols-2 gap-2 mt-1 text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-900">
          <div>
            <span className="text-slate-400">Expected: </span>
            <span className="text-slate-200">{node.expected_value}</span>
          </div>
          <div>
            <span className="text-slate-400">Observed: </span>
            <span className="text-slate-200">{node.observed_value}</span>
          </div>
        </div>
      )}

      {hasChildren && (
        <div className="mt-2 space-y-2 pt-1 border-t border-slate-900/80">
          {node.children!.map((child, idx) => (
            <ReasoningNodeView key={child.node_id || idx} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export const TraceInspector: React.FC<TraceInspectorProps> = ({ evaluation }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'tree' | 'flat'>(
    evaluation.reasoning_tree ? 'tree' : 'flat'
  );

  return (
    <div className="mt-4 border-t border-slate-800/80 pt-3">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-2 text-xs font-mono uppercase tracking-wider text-cyan-400 hover:text-cyan-300 transition-colors focus:outline-none focus:ring-1 focus:ring-cyan-500 rounded px-1"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" aria-hidden="true" />
          <span>{isOpen ? 'Hide Audit Reasoning Trace' : 'Inspect Audit Reasoning Trace & Graph Evidence'}</span>
        </span>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="mt-3 space-y-4 bg-slate-900/90 rounded-lg p-4 border border-slate-800 text-xs">
          {/* Summary Explanation */}
          <div>
            <h4 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1">
              Arbitration Summary
            </h4>
            <p className="text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800">
              {evaluation.reasoning_trace}
            </p>
          </div>

          {/* Missing Facts (if any) */}
          {evaluation.missing_facts.length > 0 && (
            <div>
              <h4 className="font-semibold text-amber-400 uppercase tracking-wider text-[11px] mb-1 flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5" aria-hidden="true" />
                Missing or Incompatible Facts ({evaluation.missing_facts.length})
              </h4>
              <ul className="space-y-1 bg-amber-950/20 border border-amber-900/40 rounded p-2.5 text-amber-200">
                {evaluation.missing_facts.map((fact, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{fact}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Evaluated Rules / Reasoning Tree */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
                Reasoning Architecture ({evaluation.rules_fired.length} Rules Evaluated)
              </h4>
              {evaluation.reasoning_tree && (
                <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded border border-slate-800 text-[10px]">
                  <button
                    type="button"
                    onClick={() => setViewMode('tree')}
                    className={`px-2 py-0.5 rounded flex items-center gap-1 transition-colors ${
                      viewMode === 'tree'
                        ? 'bg-cyan-900/70 text-cyan-300 font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <GitBranch className="w-3 h-3" />
                    Tree AST
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('flat')}
                    className={`px-2 py-0.5 rounded flex items-center gap-1 transition-colors ${
                      viewMode === 'flat'
                        ? 'bg-cyan-900/70 text-cyan-300 font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Layers className="w-3 h-3" />
                    Flat Rules
                  </button>
                </div>
              )}
            </div>

            {viewMode === 'tree' && evaluation.reasoning_tree ? (
              <div className="space-y-2">
                <ReasoningNodeView node={evaluation.reasoning_tree} depth={0} />
              </div>
            ) : (
              <div className="space-y-2">
                {evaluation.rules_fired.map((rule, idx) => {
                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-slate-950 border border-slate-800/80 space-y-1"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-cyan-300 font-medium">
                          {rule.rule_id}
                        </span>
                        {statusBadge(rule.status)}
                      </div>

                      <p className="text-slate-300">{rule.explanation}</p>

                      <div className="grid grid-cols-2 gap-2 mt-1 text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-900">
                        <div>
                          <span className="text-slate-400">Expected: </span>
                          <span className="text-slate-200">{rule.expected_value}</span>
                        </div>
                        <div>
                          <span className="text-slate-400">Observed: </span>
                          <span className="text-slate-200">{rule.observed_value}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Graph Traversals (Programme -> Skills -> Careers) */}
          {evaluation.discovered_relationships.length > 0 && (
            <div>
              <h4 className="font-semibold text-violet-300 uppercase tracking-wider text-[11px] mb-1.5 flex items-center gap-1.5">
                <Network className="w-3.5 h-3.5 text-violet-400" aria-hidden="true" />
                Semantic Graph Traversal Evidence ({evaluation.discovered_relationships.length})
              </h4>
              <div className="space-y-1.5 bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[11px]">
                {evaluation.discovered_relationships.map((rel, idx) => (
                  <div key={idx} className="flex items-center gap-1.5 text-slate-300 flex-wrap">
                    <span className="text-cyan-400">{rel.source}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" aria-hidden="true" />
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-900 text-violet-400 border border-violet-900/50">
                      {rel.relationship}
                    </span>
                    <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" aria-hidden="true" />
                    <span className="text-emerald-300 font-semibold">{rel.target}</span>
                    <span className="text-slate-400 text-[10px]">({rel.target_type})</span>
                    {sourceTypeBadge(rel.source_type)}
                    {rel.provenance_path && rel.provenance_path.length > 1 && (
                      <span className="text-[10px] text-slate-400">
                        [{rel.provenance_path.join(' → ')}]
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Provenance Metadata & Frame Hierarchy */}
          <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span>Label: {evaluation.data_provenance.dataset_label}</span>
              {evaluation.parent_frame_id && (
                <span className="text-cyan-400">
                  Parent Frame: {evaluation.parent_frame_id}
                </span>
              )}
            </div>
            <span>Provenance: {evaluation.data_provenance.provenance}</span>
          </div>
        </div>
      )}
    </div>
  );
};
