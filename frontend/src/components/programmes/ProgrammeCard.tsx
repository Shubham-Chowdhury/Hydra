import React from 'react';
import { MapPin, BookOpen, Briefcase, Zap } from 'lucide-react';
import type { ProgrammeEvaluationDto } from '../../api/types';
import { EligibilityBadge } from './EligibilityBadge';
import { AffordabilityBadge } from './AffordabilityBadge';
import { TraceInspector } from '../reasoning/TraceInspector';

interface ProgrammeCardProps {
  evaluation: ProgrammeEvaluationDto;
}

export const ProgrammeCard: React.FC<ProgrammeCardProps> = ({ evaluation }) => {
  const fitPercent = Math.round(evaluation.preference_fit.fit_score * 100);

  // Extract skills and careers from discovered relationships or unique targets
  const discoveredSkills = evaluation.discovered_relationships
    .filter((r) => r.target_type === 'skill')
    .map((r) => r.target);
  const discoveredCareers = evaluation.discovered_relationships
    .filter((r) => r.target_type === 'career')
    .map((r) => r.target);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all shadow-md hover:shadow-cyan-950/20">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/60">
              {evaluation.programme_id}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              {evaluation.discipline}
            </span>
          </div>

          <h3 className="text-lg font-bold text-white mt-1.5 leading-snug">
            {evaluation.programme_title}
          </h3>

          <div className="text-sm text-slate-300 mt-0.5">
            {evaluation.institution_name}
          </div>

          <div className="flex items-center gap-1 text-xs text-slate-400 mt-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>{evaluation.location}</span>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap items-center gap-2 self-start">
          <EligibilityBadge status={evaluation.eligibility_status} />
          <AffordabilityBadge affordability={evaluation.affordability} />
        </div>
      </div>

      {/* Preference Fit Indicator */}
      <div className="mt-4 bg-slate-950 p-3 rounded-lg border border-slate-800/80">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
            Preference Alignment Fit
          </span>
          <span className="font-mono font-bold text-cyan-300">{fitPercent}%</span>
        </div>
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-violet-500 rounded-full transition-all duration-500"
            style={{ width: `${fitPercent}%` }}
            role="progressbar"
            aria-valuenow={fitPercent}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5">{evaluation.preference_fit.notes}</p>
      </div>

      {/* Discovered Graph Skills & Careers */}
      {(discoveredSkills.length > 0 || discoveredCareers.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-1.5 items-center text-xs">
          {discoveredSkills.slice(0, 3).map((skill, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded bg-violet-950/60 text-violet-300 border border-violet-800/50 text-[11px]"
            >
              Skill: {skill}
            </span>
          ))}
          {discoveredCareers.slice(0, 2).map((career, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 text-[11px] flex items-center gap-1"
            >
              <Briefcase className="w-3 h-3" aria-hidden="true" />
              {career}
            </span>
          ))}
        </div>
      )}

      {/* Explanatory Trace Inspector */}
      <TraceInspector evaluation={evaluation} />
    </div>
  );
};

