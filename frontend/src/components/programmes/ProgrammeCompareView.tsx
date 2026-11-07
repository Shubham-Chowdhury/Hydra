import React from 'react';
import {
  Scale,
  X,
  Plus,
  CheckCircle2,
  XCircle,
  MapPin,
} from 'lucide-react';
import type { ProgrammeEvaluationDto } from '../../api/types';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { EvidenceBadge } from '../common/EvidenceBadge';
import { DemoNoticeBanner } from '../common/DemoNoticeBanner';

interface ProgrammeCompareViewProps {
  comparedProgrammes: ProgrammeEvaluationDto[];
  allEvaluations: ProgrammeEvaluationDto[];
  onRemoveCompare: (programmeId: string) => void;
  onAddCompare: (programmeId: string) => void;
  onClearCompare: () => void;
  onNavigateToExplore: () => void;
}

export const ProgrammeCompareView: React.FC<ProgrammeCompareViewProps> = ({
  comparedProgrammes,
  allEvaluations,
  onRemoveCompare,
  onAddCompare,
  onClearCompare,
  onNavigateToExplore,
}) => {
  const hasEnough = comparedProgrammes.length >= 2;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Side-by-Side Programme Comparison"
        description="Compare 2 to 4 academic pathways across deterministic prerequisites, total INR tuition, preference fit, and evidence coverage."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Decision Matrix
          </span>
        }
      />

      <DemoNoticeBanner />

      {/* Comparison Actions Bar */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-[#176B63]" />
          <span className="text-sm font-bold text-[#1C2B2A]">
            Comparing {comparedProgrammes.length} of 4 Max Programmes
          </span>
        </div>

        <div className="flex items-center gap-2">
          {comparedProgrammes.length > 0 && (
            <button
              onClick={onClearCompare}
              className="px-3 py-1.5 rounded-lg border border-[#DCE5DF] text-xs font-semibold text-[#52615E] hover:bg-[#EDF4F1] transition-colors"
            >
              Clear Comparison
            </button>
          )}
          <button
            onClick={onNavigateToExplore}
            className="px-3 py-1.5 rounded-lg bg-[#176B63] hover:bg-[#155E57] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add More from Catalog</span>
          </button>
        </div>
      </div>

      {!hasEnough ? (
        /* Empty State with quick add suggestions */
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-[#E1EEE8] text-[#176B63] mx-auto flex items-center justify-center">
            <Scale className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-[#1C2B2A]">
              Select At Least Two Programmes to Compare
            </h3>
            <p className="text-xs text-[#52615E]">
              You currently have {comparedProgrammes.length} programme selected. Select another to see detailed prerequisite differences side-by-side.
            </p>
          </div>

          {/* Quick Add demo options from all evaluations */}
          {allEvaluations.length > 0 && (
            <div className="pt-4 border-t border-[#DCE5DF] max-w-xl mx-auto">
              <span className="text-xs font-bold text-[#64736F] uppercase tracking-wider block mb-3">
                Quick-add from evaluated programmes:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {allEvaluations.slice(0, 4).map((ev) => {
                  const isAlreadyAdded = comparedProgrammes.some((c) => c.programme_id === ev.programme_id);
                  return (
                    <button
                      key={ev.programme_id}
                      onClick={() => !isAlreadyAdded && onAddCompare(ev.programme_id)}
                      disabled={isAlreadyAdded}
                      className={`text-left p-3 rounded-xl border text-xs flex items-center justify-between transition-colors ${
                        isAlreadyAdded
                          ? 'border-[#DCE5DF] bg-[#F6F8F6] text-[#64736F] opacity-60 cursor-not-allowed'
                          : 'border-[#DCE5DF] bg-white hover:border-[#176B63] hover:bg-[#E1EEE8] text-[#1C2B2A]'
                      }`}
                    >
                      <div className="truncate mr-2">
                        <div className="font-bold truncate">{ev.programme_title}</div>
                        <div className="text-[11px] text-[#52615E] truncate">{ev.institution_name}</div>
                      </div>
                      <span className="shrink-0 text-xs font-semibold text-[#176B63]">
                        {isAlreadyAdded ? 'Added' : '+ Add'}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Side-by-Side Comparison Table */
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl shadow-xs overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse min-w-[700px]">
            <thead>
              <tr className="border-b border-[#DCE5DF] bg-[#F6F8F6]">
                <th className="p-4 w-48 text-[#64736F] font-bold uppercase tracking-wider">
                  Attribute
                </th>
                {comparedProgrammes.map((p) => (
                  <th key={p.programme_id} className="p-4 border-l border-[#DCE5DF] min-w-[220px]">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-mono text-[10px] text-[#64736F] bg-[#EDF4F1] px-1.5 py-0.5 rounded">
                          {p.programme_id}
                        </span>
                        <div className="text-sm font-bold text-[#1C2B2A] mt-1 leading-snug">
                          {p.programme_title}
                        </div>
                        <div className="text-xs text-[#52615E] mt-0.5 font-normal">
                          {p.institution_name}
                        </div>
                      </div>
                      <button
                        onClick={() => onRemoveCompare(p.programme_id)}
                        className="p-1 rounded-md text-[#64736F] hover:bg-[#FDE8E8] hover:text-[#A33434] transition-colors"
                        title="Remove from comparison"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#DCE5DF]">
              {/* Row: Eligibility Status */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Academic Eligibility
                </td>
                {comparedProgrammes.map((p) => (
                  <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF]">
                    <StatusBadge status={p.eligibility_status} />
                  </td>
                ))}
              </tr>

              {/* Row: Total 4-Year Tuition */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Total Tuition (INR)
                </td>
                {comparedProgrammes.map((p) => {
                  const isAffordable = p.affordability?.is_affordable === true;
                  return (
                    <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF]">
                      <div className="text-sm font-bold text-[#1C2B2A]">
                        ₹{(p.affordability.estimated_total_tuition_inr / 100000).toFixed(2)} Lakh
                      </div>
                      <span
                        className={`inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          isAffordable
                            ? 'bg-[#E6F4ED] text-[#2D6A4F]'
                            : 'bg-[#FDE8E8] text-[#A33434]'
                        }`}
                      >
                        {isAffordable ? 'Within Budget' : 'Exceeds Budget'}
                      </span>
                    </td>
                  );
                })}
              </tr>

              {/* Row: Location & Campus */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Campus Location
                </td>
                {comparedProgrammes.map((p) => (
                  <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF] text-[#52615E]">
                    <div className="flex items-center gap-1 font-medium text-[#1C2B2A]">
                      <MapPin className="w-3.5 h-3.5 text-[#64736F]" />
                      <span>{p.location}</span>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Row: Preference Alignment */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Preference Fit
                </td>
                {comparedProgrammes.map((p) => {
                  const fit = Math.round((p.preference_fit?.fit_score || 0) * 100);
                  return (
                    <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-[#176B63]">{fit}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-[#DCE5DF] rounded-full overflow-hidden">
                        <div className="h-full bg-[#176B63] rounded-full" style={{ width: `${fit}%` }} />
                      </div>
                      <div className="text-[11px] text-[#64736F] mt-1 truncate">
                        {p.preference_fit?.notes || 'Discipline alignment'}
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Row: Evaluated Prerequisite Rules */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Prerequisites Summary
                </td>
                {comparedProgrammes.map((p) => (
                  <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF]">
                    <div className="space-y-1.5">
                      {p.rules_fired?.map((rule, idx) => {
                        const isSatisfied = rule.status === 'SATISFIED';
                        return (
                          <div key={idx} className="flex items-center gap-1.5 text-[11px]">
                            {isSatisfied ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-[#A33434] shrink-0" />
                            )}
                            <span className={isSatisfied ? 'text-[#1C2B2A]' : 'text-[#A33434] font-medium'}>
                              {rule.rule_name}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </td>
                ))}
              </tr>

              {/* Row: Evidence Coverage */}
              <tr>
                <td className="p-4 font-bold text-[#1C2B2A] bg-[#F6F8F6]">
                  Evidence Rigor
                </td>
                {comparedProgrammes.map((p) => (
                  <td key={p.programme_id} className="p-4 border-l border-[#DCE5DF]">
                    <EvidenceBadge
                      activeDimensionsCount={p.evidence ? p.evidence.length : 4}
                    />
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
