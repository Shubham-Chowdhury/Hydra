import React, { useEffect, useState } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  X,
  Sparkles,
} from 'lucide-react';
import { voiceManager, VoiceState, VoiceMessage } from '../../services/voiceManager';
import type { NavigationDestination } from '../layout/StudentSidebar';

interface FloatingVoiceAssistantProps {
  currentDestination: NavigationDestination;
  onNavigate?: (dest: NavigationDestination) => void;
}

export const FloatingVoiceAssistant: React.FC<FloatingVoiceAssistantProps> = ({
  currentDestination,
}) => {
  const [voiceState, setVoiceState] = useState<VoiceState>(voiceManager.getState());
  const [messages, setMessages] = useState<VoiceMessage[]>(voiceManager.getMessages());
  const [transcript, setTranscript] = useState<string>('');
  const [isMuted, setIsMuted] = useState<boolean>(voiceManager.isSpeechMuted());
  const [isOpen, setIsOpen] = useState<boolean>(false);

  useEffect(() => {
    const unsubState = voiceManager.subscribeState((state) => {
      setVoiceState(state);
    });

    const unsubTranscript = voiceManager.subscribeTranscript((text) => {
      setTranscript(text);
    });

    const unsubMessages = voiceManager.subscribeMessages((msgs) => {
      setMessages(msgs);
    });

    return () => {
      unsubState();
      unsubTranscript();
      unsubMessages();
    };
  }, []);

  const lastHydraMsg = [...messages].reverse().find((m) => m.sender === 'hydra');
  const lastStudentMsg = [...messages].reverse().find((m) => m.sender === 'student');

  const toggleMic = () => {
    voiceManager.toggleListening();
  };

  const toggleMute = () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    voiceManager.setMuted(nextMuted);
  };

  // On overview page, the central Equalizer and Guide log are active, so hide floating widget entirely
  if (currentDestination === 'overview') {
    return null;
  }

  // Floating Minimized Button
  if (!isOpen) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          voiceManager.startListening();
        }}
        className={`fixed bottom-6 right-6 z-40 px-4 py-3 rounded-full flex items-center gap-2.5 shadow-xl transition-all hover:scale-105 cursor-pointer border ${
          voiceState === 'listening'
            ? 'bg-[#E8F84A] text-[#111215] border-[#D4E82E] shadow-[0_0_20px_rgba(232,248,74,0.6)] animate-pulse font-bold'
            : voiceState === 'speaking'
            ? 'bg-[#0284C7] text-white border-sky-400 shadow-[0_0_20px_rgba(2,132,199,0.5)] animate-pulse font-bold'
            : 'bg-[#111215] text-white border-gray-700/80 hover:bg-black font-semibold'
        }`}
        title="Open Hydra Voice Guide"
        aria-label="Open Hydra Voice Guide"
      >
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            voiceState === 'listening'
              ? 'bg-[#111215] animate-ping'
              : voiceState === 'speaking'
              ? 'bg-sky-200 animate-ping'
              : 'bg-emerald-400'
          }`}
        />
        <Mic className="w-4 h-4" />
        <span className="text-xs">Hydra Voice Guide</span>
      </button>
    );
  }

  return (
    <div
      className="fixed bottom-6 right-6 z-40 max-w-sm sm:max-w-md w-[calc(100vw-3rem)] bg-white/95 backdrop-blur-md rounded-3xl p-4 sm:p-5 border border-gray-200/80 shadow-2xl transition-all duration-300 animate-in slide-in-from-bottom-4"
      role="region"
      aria-label="Hydra Voice Assistant Companion"
    >
      {/* Top Header Row */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              voiceState === 'listening'
                ? 'bg-[#65A30D] shadow-[0_0_10px_rgba(101,163,13,0.6)] animate-pulse'
                : voiceState === 'speaking'
                ? 'bg-[#0284C7] shadow-[0_0_10px_rgba(2,132,199,0.6)] animate-pulse'
                : voiceState === 'requesting'
                ? 'bg-amber-400 animate-ping'
                : 'bg-emerald-500'
            }`}
          />
          <div className="flex flex-col">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#111215] flex items-center gap-1.5">
              <span>Hydra Voice Guide</span>
              <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-semibold border border-emerald-200">
                <Sparkles className="w-2.5 h-2.5 text-emerald-600" />
                Natural Voice
              </span>
            </span>
            <span className="text-[10px] text-gray-400 font-mono">
              {voiceState === 'listening'
                ? 'LISTENING TO YOUR SPEECH...'
                : voiceState === 'speaking'
                ? 'SPEAKING (SWEET NATURAL CADENCE)'
                : voiceState === 'thinking'
                ? 'PROCESSING INTENT...'
                : 'READY • SPEAK OR TAP ACTION'}
            </span>
          </div>
        </div>

        {/* Top Controls: Mute & Close */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={toggleMute}
            className="p-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
            title={isMuted ? 'Unmute voice' : 'Mute voice'}
          >
            {isMuted ? <VolumeX className="w-3.5 h-3.5 text-rose-500" /> : <Volume2 className="w-3.5 h-3.5 text-emerald-700" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-black transition-colors"
            title="Minimize Assistant"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mini Equalizer Bar Animation */}
      <div className="flex items-center justify-center gap-1.5 py-3 h-10">
        {[...Array(16)].map((_, i) => {
          const isCenter = Math.abs(i - 8) < 4;
          return (
            <div
              key={`mini-eq-${i}`}
              className={`w-1 rounded-full transition-all duration-150 ${
                voiceState === 'listening'
                  ? 'bg-[#65A30D]'
                  : voiceState === 'speaking'
                  ? 'bg-[#0284C7]'
                  : 'bg-gray-300'
              }`}
              style={{
                height:
                  voiceState === 'listening'
                    ? `${Math.max(6, Math.sin(Date.now() / 150 + i * 0.4) * 14 + (isCenter ? 12 : 8))}px`
                    : voiceState === 'speaking'
                    ? `${Math.max(6, Math.sin(Date.now() / 200 + i * 0.5) * 16 + 14)}px`
                    : '6px',
              }}
            />
          );
        })}
      </div>

      {/* Spoken Dialogue Feed */}
      <div className="bg-gray-50 rounded-2xl p-3 border border-gray-200/70 space-y-2 text-xs">
        {/* Student Utterance */}
        {(transcript || lastStudentMsg) && (
          <div className="flex items-start gap-2 text-gray-700">
            <span className="font-bold text-[10px] uppercase text-gray-400 shrink-0 mt-0.5">You:</span>
            <span className="italic text-gray-800 font-medium">
              "{transcript || lastStudentMsg?.text}"
            </span>
          </div>
        )}

        {/* Hydra Response */}
        <div className="flex items-start gap-2 text-[#111215]">
          <span className="font-bold text-[10px] uppercase text-[#3F6212] shrink-0 mt-0.5">Hydra:</span>
          <span className="font-normal text-gray-900 leading-relaxed">
            {lastHydraMsg?.text || "How can I guide your admissions journey today, Master Shubham?"}
          </span>
        </div>
      </div>

      {/* Quick Voice Command Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-2.5 scrollbar-none">
        {[
          { label: 'Franchise Auction', cmd: 'Open Franchise Auction' },
          { label: 'Catalogue', cmd: 'Show me the catalogue' },
          { label: 'Compare', cmd: 'Compare top programmes' },
          { label: 'Heist Planner', cmd: 'Open Heist Planner' },
          { label: 'Re-Evaluate', cmd: 'Re-run evaluation' },
          { label: 'What Next?', cmd: 'What should I do next?' },
        ].map((chip) => (
          <button
            key={chip.label}
            onClick={() => voiceManager.handleStudentUtterance(chip.cmd)}
            className="px-2.5 py-1 rounded-lg bg-gray-100 hover:bg-[#E8F84A] hover:text-[#111215] text-gray-700 text-[11px] font-medium whitespace-nowrap border border-gray-200 shadow-2xs transition-all cursor-pointer"
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Bottom Action Row: Push-to-Talk Mic Bar */}
      <div className="pt-2 flex items-center justify-between gap-3">
        <button
          onClick={toggleMic}
          className={`flex-1 py-2.5 px-4 rounded-2xl flex items-center justify-center gap-2 text-xs font-bold transition-all shadow-xs cursor-pointer ${
            voiceState === 'listening'
              ? 'bg-[#E8F84A] text-[#111215] border border-[#D4E82E] shadow-[0_0_12px_rgba(204,255,0,0.5)]'
              : voiceState === 'requesting'
              ? 'bg-amber-400 text-[#111215] animate-pulse'
              : 'bg-[#111215] hover:bg-black text-white hover:scale-[1.01]'
          }`}
        >
          {voiceState === 'listening' ? (
            <>
              <MicOff className="w-4 h-4 text-[#111215]" />
              <span>Listening (Tap to Stop)</span>
            </>
          ) : (
            <>
              <Mic className="w-4 h-4 text-[#E8F84A]" />
              <span>Tap to Speak</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
