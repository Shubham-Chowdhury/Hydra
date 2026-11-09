/**
 * Interest Decoder Component for Hydra.
 *
 * Implements neural/semantic decoding of natural-language student interest
 * narratives into canonical ontology concepts, supporting the strict tripartite
 * lifecycle: STUDENT_STATED -> MODEL_SUGGESTED -> USER_CONFIRMED.
 */

import React, { useEffect, useState } from 'react';
import { hydraApi } from '../../api/client';
import type {
  CandidateConceptDto,
  ConfirmedInterestResponseDto,
  InterestDecodingResponseDto,
  InterestModelStatusDto,
} from '../../api/types';
import {
  Sparkles,
  CheckCircle2,
  Search,
  RotateCw,
  Compass,
} from 'lucide-react';

export const InterestDecoderView: React.FC = () => {
  const [inputText, setInputText] = useState<string>(
    'I love building autonomous robots, experimenting with sensors and actuators, and writing intelligent embedded firmware for control systems.'
  );
  const [modelStatus, setModelStatus] = useState<InterestModelStatusDto | null>(null);
  const [decoding, setDecoding] = useState<boolean>(false);
  const [decodeResult, setDecodeResult] = useState<InterestDecodingResponseDto | null>(null);
  const [confirmedList, setConfirmedList] = useState<ConfirmedInterestResponseDto[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchModelStatus();
  }, []);

  const fetchModelStatus = async () => {
    try {
      const res = await hydraApi.getInterestModelStatus();
      setModelStatus(res);
    } catch {
      // Model offline fallback
    }
  };

  const executeDecode = async () => {
    if (!inputText.trim()) return;

    setDecoding(true);
    setErrorMessage(null);

    try {
      const res = await hydraApi.decodeInterests(inputText);
      setDecodeResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error decoding interests.');
    } finally {
      setDecoding(false);
    }
  };

  useEffect(() => {
    const handleVoiceDecode = () => {
      executeDecode();
    };
    window.addEventListener('hydra:run_decode', handleVoiceDecode);
    return () => window.removeEventListener('hydra:run_decode', handleVoiceDecode);
  }, [inputText]);

  const handleDecode = async (e: React.FormEvent) => {
    e.preventDefault();
    executeDecode();
  };

  const handleConfirm = async (candidate: CandidateConceptDto) => {
    try {
      const res = await hydraApi.confirmInterest(
        candidate.concept.concept_id,
        candidate.similarity_score
      );
      setConfirmedList((prev) => [...prev, res]);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error confirming concept.');
    }
  };

  const handlePreset = (presetText: string) => {
    setInputText(presetText);
  };

  return (
    <div className="space-y-6 text-[#111215]">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🧠</span>
              <h2 className="text-2xl font-bold tracking-tight text-[#111215]">
                Neural Interest Decoder
              </h2>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Translates unconstrained natural-language interest statements into canonical ontology concepts using local neural embeddings.
            </p>
          </div>

          {modelStatus && (
            <div className="text-right text-xs bg-gray-50 p-3 rounded-2xl border border-gray-200/70">
              <span className="text-gray-400 block font-semibold">Encoder Model</span>
              <span className="font-mono text-purple-700 font-bold block">{modelStatus.architecture}</span>
              <span className="text-[11px] text-gray-500">
                {modelStatus.dimensions}D Hypersphere | {modelStatus.canonical_concepts_indexed} Concepts Loaded
              </span>
            </div>
          )}
        </div>

        {/* Tripartite Confirmation Lifecycle Pill */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 font-semibold">Tripartite Safety Contract:</span>
            <span className="px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-700 font-mono text-[11px]">
              1. STUDENT_STATED
            </span>
            <span className="text-gray-400">➔</span>
            <span className="px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-800 border border-purple-200 font-mono text-[11px]">
              2. MODEL_SUGGESTED
            </span>
            <span className="text-gray-400">➔</span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[11px]">
              3. USER_CONFIRMED
            </span>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-medium">
          {errorMessage}
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Input Form (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#111215]">Natural Language Narrative</h3>
            <span className="text-[11px] text-gray-400 font-mono">{inputText.length} / 1000</span>
          </div>

          {/* Quick presets */}
          <div className="space-y-1.5">
            <span className="text-[11px] text-gray-400 block uppercase tracking-wider font-bold">
              Try A Narrative
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => handlePreset('I love building autonomous robots, experimenting with sensors and actuators, and writing intelligent embedded firmware.')}
                className="text-[11px] px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold transition cursor-pointer"
              >
                🤖 Robotics & Firmware
              </button>
              <button
                type="button"
                onClick={() => handlePreset('Passionate about deep learning, neural network architectures, machine learning models, and computer vision.')}
                className="text-[11px] px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold transition cursor-pointer"
              >
                🧠 Deep Learning & AI
              </button>
              <button
                type="button"
                onClick={() => handlePreset('Interested in thermal engineering, aerodynamics, heat transfer, and mechanical CAD design for engines.')}
                className="text-[11px] px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold transition cursor-pointer"
              >
                ⚙️ Thermal & Mechanics
              </button>
            </div>
          </div>

          <form onSubmit={handleDecode} className="space-y-4">
            <textarea
              rows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Describe your technical interests, projects you enjoy, or subjects you're excited about..."
              className="w-full bg-gray-50/70 border border-gray-200/80 rounded-2xl p-3.5 text-[#111215] text-xs focus:bg-white focus:outline-none focus:border-[#111215] leading-relaxed font-sans shadow-2xs"
            />

            <button
              type="submit"
              disabled={decoding || inputText.trim().length < 3}
              className="w-full py-3 px-4 rounded-full bg-[#111215] hover:bg-black disabled:bg-gray-200 disabled:text-gray-400 text-white font-bold tracking-wide transition shadow-sm text-xs cursor-pointer flex items-center justify-center gap-2"
            >
              {decoding ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin text-[#E8F84A]" />
                  <span>Decoding Concepts & Traversing Graph...</span>
                </>
              ) : (
                <>
                  <span>Decode Concepts & Traverse Graph</span>
                  <Sparkles className="w-3.5 h-3.5 text-[#E8F84A]" />
                </>
              )}
            </button>
          </form>

          {/* Confirmed list */}
          {confirmedList.length > 0 && (
            <div className="mt-5 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase font-bold text-emerald-800 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Confirmed Student Interests ({confirmedList.length})</span>
                </span>
                <span className="text-[10px] text-gray-400 font-mono">USER_CONFIRMED</span>
              </div>
              <p className="text-[11px] text-gray-500 mb-3">
                These concepts have been explicitly accepted and authorized to update the Digital Twin.
              </p>
              <div className="space-y-2">
                {confirmedList.map((c) => (
                  <div
                    key={c.concept_id}
                    className="p-3 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-emerald-950 block">{c.concept_name}</span>
                      <span className="text-[10px] text-emerald-700 capitalize">{c.concept_type}</span>
                    </div>
                    <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-600 text-white font-bold">
                      ✓ Confirmed
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Decoded Candidates (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {!decodeResult && !decoding && (
            <div className="bg-white rounded-3xl border border-gray-200/70 p-12 text-center text-gray-400 shadow-xs space-y-3">
              <div className="w-12 h-12 rounded-full bg-purple-50 mx-auto flex items-center justify-center text-purple-600">
                <Search className="w-5 h-5" />
              </div>
              <p className="text-sm font-bold text-gray-800">
                Enter your interest narrative to decode semantic concepts.
              </p>
              <p className="text-xs text-gray-400 max-w-sm mx-auto">
                The Interest Decoder retrieves ontology candidates from Hydra's semantic network without silently mutating your profile.
              </p>
            </div>
          )}

          {decodeResult && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-[#111215] uppercase tracking-wider">
                  Decoded Ontology Candidates ({decodeResult.candidates.length})
                </h3>
                <span className="text-xs font-mono text-gray-500">
                  Taxonomy: {decodeResult.taxonomy_version}
                </span>
              </div>

              <div className="space-y-3">
                {decodeResult.candidates.map((candidate: CandidateConceptDto) => {
                  const isConfirmed = confirmedList.some((c) => c.concept_id === candidate.concept.concept_id);
                  const simPct = (candidate.similarity_score * 100).toFixed(1);

                  return (
                    <div
                      key={candidate.concept.concept_id}
                      className="bg-white rounded-3xl p-5 border border-gray-200/70 shadow-xs hover:shadow-md transition-all space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-base font-bold text-[#111215]">
                              {candidate.concept.name}
                            </h4>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 border border-purple-200 uppercase">
                              {candidate.concept.concept_type}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mt-1">{candidate.concept.description}</p>
                        </div>

                        {/* Confirmation Button */}
                        <button
                          onClick={() => handleConfirm(candidate)}
                          disabled={isConfirmed}
                          className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all shrink-0 cursor-pointer ${
                            isConfirmed
                              ? 'bg-emerald-100 text-emerald-800 cursor-default'
                              : 'bg-[#111215] hover:bg-black text-white hover:scale-105'
                          }`}
                        >
                          {isConfirmed ? '✓ Confirmed' : '+ Confirm Interest'}
                        </button>
                      </div>

                      {/* Visual Proximity Bar */}
                      <div>
                        <div className="flex justify-between text-[11px] mb-1 font-semibold">
                          <span className="text-gray-400">Vector Proximity Match</span>
                          <span className="text-purple-700 font-bold">{simPct}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(10, candidate.similarity_score * 100))}%` }}
                          />
                        </div>
                      </div>

                      {/* Discovered Knowledge Graph Connections */}
                      {candidate.related_graph_nodes && candidate.related_graph_nodes.length > 0 && (
                        <div className="pt-2 border-t border-gray-100 flex flex-wrap items-center gap-2 text-xs">
                          <span className="text-[11px] font-bold text-gray-400">Discovered Graph Nodes:</span>
                          {candidate.related_graph_nodes.map((node, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-200 text-[11px] font-semibold flex items-center gap-1"
                            >
                              <Compass className="w-3 h-3" />
                              <span>{node.name}</span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
