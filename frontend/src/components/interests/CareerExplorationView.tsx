import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Brain,
  AlertCircle,
  Plus,
} from 'lucide-react';
import { hydraApi } from '../../api/client';
import type {
  CandidateConceptDto,
  ConfirmedInterestResponseDto,
  InterestDecodingResponseDto,
} from '../../api/types';
import { PageHeader } from '../common/PageHeader';
import { ProvenanceIndicator } from '../common/ProvenanceIndicator';
import { DemoNoticeBanner } from '../common/DemoNoticeBanner';

export const CareerExplorationView: React.FC = () => {
  const [inputText, setInputText] = useState<string>(
    'I love building autonomous robots, experimenting with sensors and actuators, and writing intelligent embedded firmware for control systems.'
  );
  const [decoding, setDecoding] = useState<boolean>(false);
  const [decodeResult, setDecodeResult] = useState<InterestDecodingResponseDto | null>(null);
  const [confirmedList, setConfirmedList] = useState<ConfirmedInterestResponseDto[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    // Non-critical background ping
    hydraApi.getInterestModelStatus().catch(() => {});
  }, []);

  const handleDecode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setDecoding(true);
    setErrorMessage(null);

    try {
      const res = await hydraApi.decodeInterests(inputText.trim());
      setDecodeResult(res);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message || 'Failed to decode interest narrative.');
      } else {
        setErrorMessage('Failed to decode interest narrative.');
      }
    } finally {
      setDecoding(false);
    }
  };

  const handleConfirm = async (candidate: CandidateConceptDto) => {
    try {
      const confirmed = await hydraApi.confirmInterest(
        candidate.concept.concept_id,
        candidate.similarity_score
      );
      setConfirmedList((prev) => {
        if (prev.some((c) => c.concept_id === confirmed.concept_id)) return prev;
        return [...prev, confirmed];
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message || 'Failed to confirm interest.');
      } else {
        setErrorMessage('Failed to confirm interest.');
      }
    }
  };

  const sampleNarratives = [
    {
      label: 'Robotics & Embedded Systems',
      text: 'I love building autonomous robots, experimenting with microcontrollers, sensors, actuators, and writing embedded firmware.',
    },
    {
      label: 'AI & Data Science',
      text: 'Passionate about deep learning, natural language processing, predictive statistics, and building large-scale machine learning systems.',
    },
    {
      label: 'Renewable Clean Energy',
      text: 'Interested in smart grid optimization, solar photovoltaics, energy storage materials, and electrical power transmission.',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Career & Interest Exploration"
        description="Decode your personal passions into canonical academic disciplines. Our 3-stage lifecycle ensures you always retain full agency over AI suggestions."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Tripartite Interest Lifecycle
          </span>
        }
      />

      <DemoNoticeBanner />

      {/* 3-Stage Lifecycle Stepper Info Banner */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-[#1C2B2A]">
            The 3-Stage Interest Lifecycle
          </h3>
          <p className="text-xs text-[#52615E] mt-0.5">
            Hydra never assumes or forces career suggestions. Suggestions transition only through explicit student consent.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3.5 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF]">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-5 h-5 rounded-full bg-[#176B63] text-white flex items-center justify-center text-[10px] font-bold">
                1
              </span>
              <span className="text-xs font-bold text-[#1C2B2A]">Stage 1: Student Stated</span>
            </div>
            <p className="text-[11px] text-[#52615E]">
              You describe what you enjoy in plain, natural conversational English without technical jargon.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#FEF7EC] border border-[#8A5B16]/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-5 h-5 rounded-full bg-[#8A5B16] text-white flex items-center justify-center text-[10px] font-bold">
                2
              </span>
              <span className="text-xs font-bold text-[#8A5B16]">Stage 2: Model Suggested</span>
            </div>
            <p className="text-[11px] text-[#52615E]">
              FastEmbed MiniLM neural embeddings identify canonical curriculum concepts with similarity scores.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-5 h-5 rounded-full bg-[#2D6A4F] text-white flex items-center justify-center text-[10px] font-bold">
                3
              </span>
              <span className="text-xs font-bold text-[#2D6A4F]">Stage 3: User Confirmed</span>
            </div>
            <p className="text-[11px] text-[#52615E]">
              You explicitly review and confirm concepts. Only confirmed concepts influence preference fit scoring.
            </p>
          </div>
        </div>
      </div>

      {/* Input Narrative Card */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-[#FDE8E8] border border-[#A33434]/30 text-[#A33434] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-[#1C2B2A]">
            Describe Your Academic & Career Interests (In Your Own Words):
          </label>
          <span className="text-[11px] text-[#64736F]">
            {inputText.length} characters
          </span>
        </div>

        <form onSubmit={handleDecode} className="space-y-3">
          <textarea
            rows={3}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Tell us what subjects you find fascinating, what projects you like making, or problems you want to solve..."
            className="w-full p-3 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs text-[#1C2B2A] focus:bg-white focus:outline-none focus:border-[#176B63] transition-colors"
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] text-[#64736F] font-semibold">Try sample narrative:</span>
              {sampleNarratives.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setInputText(s.text)}
                  className="px-2 py-0.5 rounded-md bg-[#EDF4F1] hover:bg-[#DCE5DF] text-[#176B63] text-[11px] font-medium transition-colors"
                >
                  {s.label}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={decoding || !inputText.trim()}
              className="px-4 py-2 rounded-xl bg-[#176B63] hover:bg-[#155E57] text-white text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
            >
              <Brain className={`w-4 h-4 ${decoding ? 'animate-spin' : ''}`} />
              <span>{decoding ? 'Decoding Semantics...' : 'Decode Interests'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Model Suggestions (Stage 2) */}
      {decodeResult && (
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#DCE5DF]">
            <div>
              <h3 className="text-sm font-bold text-[#1C2B2A]">
                Stage 2: Model Suggested Concepts ({decodeResult.candidates?.length || 0})
              </h3>
              <p className="text-xs text-[#52615E]">
                Mapped via {decodeResult.model_version || 'FastEmbed MiniLM-L6-v2'} cosine similarity.
              </p>
            </div>
            <ProvenanceIndicator category="estimated" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {decodeResult.candidates?.map((cand) => {
              const isConfirmed = confirmedList.some(
                (c) => c.concept_id === cand.concept.concept_id
              );
              const scorePercent = Math.round(cand.similarity_score * 100);

              return (
                <div
                  key={cand.concept.concept_id}
                  className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2 flex flex-col justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#1C2B2A]">
                        {cand.concept.name}
                      </span>
                      <span className="text-[11px] font-mono text-[#176B63] font-semibold">
                        {scorePercent}% match
                      </span>
                    </div>
                    <div className="text-[11px] text-[#52615E]">
                      {cand.concept.description || cand.concept.concept_type}
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-[#DCE5DF]">
                    <span className="text-[10px] font-mono text-[#64736F]">
                      {cand.concept.concept_id}
                    </span>

                    {isConfirmed ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#2D6A4F]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleConfirm(cand)}
                        className="px-2.5 py-1 rounded-lg bg-[#176B63] hover:bg-[#155E57] text-white text-[11px] font-semibold transition-colors flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" />
                        <span>Confirm Interest</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Confirmed Concepts (Stage 3) */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#DCE5DF]">
          <div>
            <h3 className="text-sm font-bold text-[#1C2B2A]">
              Stage 3: Confirmed Student Interests ({confirmedList.length})
            </h3>
            <p className="text-xs text-[#52615E]">
              These verified concepts are recorded in your Student Digital Twin and used for preference weighting.
            </p>
          </div>
          <ProvenanceIndicator category="user_provided" />
        </div>

        {confirmedList.length === 0 ? (
          <div className="p-6 rounded-xl bg-[#F6F8F6] border border-dashed border-[#DCE5DF] text-center space-y-1">
            <p className="text-xs font-semibold text-[#1C2B2A]">
              No confirmed concepts yet.
            </p>
            <p className="text-[11px] text-[#52615E]">
              Decode an interest narrative above and click 'Confirm Interest' to add concepts to your active profile.
            </p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {confirmedList.map((c) => (
              <div
                key={c.concept_id}
                className="px-3 py-1.5 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/30 text-xs text-[#2D6A4F] font-semibold flex items-center gap-2"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{c.concept_name}</span>
                <span className="text-[10px] text-[#2D6A4F]/80 font-mono">
                  ({Math.round(c.original_similarity * 100)}%)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
