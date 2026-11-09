import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, Volume2, Radio, MessageSquare, VolumeX } from 'lucide-react';
import { voiceManager, VoiceState, VoiceMessage } from '../../services/voiceManager';

interface AudioEqualizerProps {
  onStateChange?: (state: 'idle' | 'listening' | 'speaking' | 'error') => void;
  onOpenGuide?: () => void;
}

const BAR_COUNT = 32;

export const AudioEqualizer: React.FC<AudioEqualizerProps> = ({
  onStateChange,
  onOpenGuide,
}) => {
  const [voiceState, setVoiceState] = useState<VoiceState>(voiceManager.getState());
  const [audioError, setAudioError] = useState<string | null>(voiceManager.getErrorMessage());
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [lastMessage, setLastMessage] = useState<VoiceMessage | null>(null);
  const [peakLevel, setPeakLevel] = useState<number>(0);
  const [isMuted, setIsMuted] = useState<boolean>(voiceManager.isSpeechMuted());
  const [showTranscriptDrawer, setShowTranscriptDrawer] = useState<boolean>(false);
  const [messages, setMessages] = useState<VoiceMessage[]>(voiceManager.getMessages());
  const [textInput, setTextInput] = useState<string>('');

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Shared frequency buffer
  const frequencyDataRef = useRef<Uint8Array | null>(null);
  const barHeightsRef = useRef<number[]>(new Array(BAR_COUNT).fill(8));
  const targetHeightsRef = useRef<number[]>(new Array(BAR_COUNT).fill(8));

  // Subscribe to singleton VoiceManager events
  useEffect(() => {
    const unsubState = voiceManager.subscribeState((newState) => {
      setVoiceState(newState);
      setAudioError(voiceManager.getErrorMessage());
      if (newState === 'listening') {
        onStateChange?.('listening');
      } else if (newState === 'speaking') {
        onStateChange?.('speaking');
      } else if (newState === 'error') {
        onStateChange?.('error');
      } else {
        onStateChange?.('idle');
      }
    });

    const unsubTranscript = voiceManager.subscribeTranscript((text) => {
      setLiveTranscript(text);
    });

    const unsubMessages = voiceManager.subscribeMessages((msgs) => {
      setMessages(msgs);
      if (msgs.length > 0) {
        setLastMessage(msgs[msgs.length - 1]);
      }
    });

    return () => {
      unsubState();
      unsubTranscript();
      unsubMessages();
    };
  }, [onStateChange]);

  const toggleMic = useCallback(async () => {
    await voiceManager.toggleListening();
  }, []);

  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    voiceManager.setMuted(newMuted);
  };

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    voiceManager.sendTextMessage(textInput);
    setTextInput('');
  };

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let startTime = performance.now();

    const render = (now: number) => {
      const elapsed = (now - startTime) / 1000;
      const width = canvas.width;
      const height = canvas.height;

      const analyser = voiceManager.getAnalyser();
      let currentMaxLevel = 0;

      if (voiceState === 'listening' && analyser) {
        // REAL HARDWARE MICROPHONE FFT FREQUENCY DATA
        if (!frequencyDataRef.current || frequencyDataRef.current.length !== analyser.frequencyBinCount) {
          frequencyDataRef.current = new Uint8Array(analyser.frequencyBinCount);
        }
        analyser.getByteFrequencyData(frequencyDataRef.current as any);

        const binCount = analyser.frequencyBinCount; // 64 bins
        for (let i = 0; i < BAR_COUNT; i++) {
          // Voice spectrum concentration: focus mostly on 150Hz - 3.5kHz (bins 2 to 28)
          const distFromCenter = Math.abs(i - BAR_COUNT / 2) / (BAR_COUNT / 2);
          const centerWeight = Math.sin((i / (BAR_COUNT - 1)) * Math.PI);
          const binIndex = Math.min(
            binCount - 1,
            Math.floor(2 + (1 - distFromCenter * 0.4) * (i < BAR_COUNT / 2 ? i * 1.5 : (BAR_COUNT - i) * 1.5))
          );

          const rawVal = frequencyDataRef.current[binIndex] || 0;
          const normalized = rawVal / 255;
          currentMaxLevel = Math.max(currentMaxLevel, normalized);

          // Natural EQ curve with dynamic boost for human speech
          const boosted = Math.pow(normalized, 1.05) * (1.2 - distFromCenter * 0.25);
          const minListening = (0.16 + centerWeight * 0.15) * height * 0.35;
          targetHeightsRef.current[i] = Math.max(16, Math.min(height * 0.80, Math.max(boosted * height * 0.85, minListening)));
        }
      } else if (voiceState === 'speaking') {
        // ASSISTANT SPEAKING: Synchronised Speech Envelope
        for (let i = 0; i < BAR_COUNT; i++) {
          const distFromCenter = Math.abs(i - BAR_COUNT / 2) / (BAR_COUNT / 2);
          const centerWeight = Math.sin((i / (BAR_COUNT - 1)) * Math.PI);
          const syllabicMod = Math.sin(elapsed * 8.5) * 0.35 + Math.cos(elapsed * 13.0) * 0.25;
          const formantMod = Math.sin(elapsed * 4.8 + i * 0.35) * 0.22;
          const envelope = Math.max(0.18, (0.50 + syllabicMod * 0.3 + formantMod + centerWeight * 0.22) * (1.15 - distFromCenter * 0.2));

          targetHeightsRef.current[i] = Math.max(18, Math.min(height * 0.78, envelope * height * 0.72));
        }
        currentMaxLevel = 0.65;
      } else if (voiceState === 'error') {
        // PERMISSION DENIED OR ERROR: Drop bars to absolute baseline immediately
        for (let i = 0; i < BAR_COUNT; i++) {
          targetHeightsRef.current[i] = 4;
        }
        currentMaxLevel = 0;
      } else {
        // IDLE / STANDBY: Elegant, prominent multi-frequency harmonic wave
        for (let i = 0; i < BAR_COUNT; i++) {
          const centerWeight = Math.sin((i / (BAR_COUNT - 1)) * Math.PI);
          const wave1 = Math.sin(elapsed * 2.5 + i * 0.22) * 0.16;
          const wave2 = Math.cos(elapsed * 1.8 - i * 0.18) * 0.12;
          const wave3 = Math.sin(elapsed * 3.8 + i * 0.38) * 0.08;
          const baseCurve = 0.24 + centerWeight * 0.28;
          const combined = Math.max(0.12, baseCurve + wave1 + wave2 + wave3);
          targetHeightsRef.current[i] = Math.max(18, combined * height * 0.52);
        }
        currentMaxLevel = 0.06;
      }

      setPeakLevel((prev) => prev * 0.88 + currentMaxLevel * 0.12);

      // Smooth bar heights with spring interpolation
      for (let i = 0; i < BAR_COUNT; i++) {
        const current = barHeightsRef.current[i];
        const target = targetHeightsRef.current[i];
        // Fast rise, smooth decay
        const speed = target > current ? 0.34 : 0.18;
        barHeightsRef.current[i] = current + (target - current) * speed;
      }

      // CLEAR CANVAS (White background surface)
      ctx.clearRect(0, 0, width, height);

      // BASELINE MEASUREMENTS
      const baselineY = height * 0.72;
      const barSpacing = width / BAR_COUNT;
      const barWidth = Math.max(5, barSpacing * 0.68);

      // 1. DRAW REFLECTIONS FIRST (Under baseline, fading gradient on white)
      for (let i = 0; i < BAR_COUNT; i++) {
        const h = barHeightsRef.current[i];
        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const reflHeight = Math.min(h * 0.30, (height - baselineY) * 0.75);

        const reflGrad = ctx.createLinearGradient(x, baselineY, x, baselineY + reflHeight);
        if (voiceState === 'speaking') {
          reflGrad.addColorStop(0, 'rgba(2, 132, 199, 0.18)');
          reflGrad.addColorStop(0.5, 'rgba(56, 189, 248, 0.06)');
          reflGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        } else if (voiceState === 'listening') {
          reflGrad.addColorStop(0, 'rgba(204, 255, 0, 0.35)');
          reflGrad.addColorStop(0.5, 'rgba(163, 230, 53, 0.12)');
          reflGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        } else {
          reflGrad.addColorStop(0, 'rgba(204, 255, 0, 0.28)');
          reflGrad.addColorStop(0.5, 'rgba(163, 230, 53, 0.08)');
          reflGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        }

        ctx.fillStyle = reflGrad;
        ctx.beginPath();
        ctx.roundRect(x, baselineY + 2, barWidth, reflHeight, [0, 0, barWidth / 2, barWidth / 2]);
        ctx.fill();
      }

      // 2. DRAW MAIN EQUALISER BARS (Completely Vibrant Neon Color)
      for (let i = 0; i < BAR_COUNT; i++) {
        const h = barHeightsRef.current[i];
        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const y = baselineY - h;

        const barGrad = ctx.createLinearGradient(x, baselineY, x, y);
        if (voiceState === 'speaking') {
          barGrad.addColorStop(0, '#0284C7'); // Vibrant azure
          barGrad.addColorStop(0.4, '#38BDF8'); // Bright sky
          barGrad.addColorStop(0.8, '#7DD3FC'); // Neon cyan
          barGrad.addColorStop(1, '#E0F2FE'); // Neon highlight
        } else if (voiceState === 'listening') {
          // Active listening state: Full vibrant neon
          barGrad.addColorStop(0, '#84CC16'); // Bright neon lime base
          barGrad.addColorStop(0.35, '#A3E635'); // Vibrant electric lime
          barGrad.addColorStop(0.75, '#CCFF00'); // Pure electric neon
          barGrad.addColorStop(1, '#F3FF85'); // Fluorescent highlight
        } else {
          // Standby/Idle state: Completely neon lime from base to crown
          barGrad.addColorStop(0, '#74C20C'); // Solid neon lime base
          barGrad.addColorStop(0.4, '#9AE624'); // Electric lime mid
          barGrad.addColorStop(0.8, '#CCFF00'); // Pure fluorescent neon
          barGrad.addColorStop(1, '#E8F84A'); // Ultra-bright neon crown
        }

        // Ambient neon glow
        ctx.shadowColor = voiceState === 'speaking' 
          ? 'rgba(56, 189, 248, 0.40)' 
          : 'rgba(204, 255, 0, 0.45)';
        ctx.shadowBlur = voiceState === 'listening' ? 8 : voiceState === 'speaking' ? 6 : 4;

        ctx.fillStyle = barGrad;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, h, [barWidth / 2, barWidth / 2, 2, 2]);
        ctx.fill();

        // Distinct peak dot on active frequencies
        if (h > height * 0.18 && (voiceState === 'listening' || voiceState === 'speaking')) {
          ctx.shadowBlur = 4;
          ctx.shadowColor = voiceState === 'speaking' ? '#0284C7' : '#CCFF00';
          ctx.fillStyle = voiceState === 'speaking' ? '#38BDF8' : '#CCFF00';
          ctx.beginPath();
          ctx.arc(x + barWidth / 2, y + barWidth / 2, barWidth * 0.26, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.shadowBlur = 0; // Reset shadow

      // 3. DRAW SUBTLE BASELINE PLANE
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.09)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(8, baselineY);
      ctx.lineTo(width - 8, baselineY);
      ctx.stroke();

      animationFrameRef.current = requestAnimationFrame(render);
    };

    animationFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [voiceState]);

  // Adjust canvas pixel density on resize
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.scale(dpr, dpr);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div
      className="lg:col-span-8 bg-white rounded-3xl p-5 border border-gray-200/70 shadow-xs flex flex-col justify-between relative overflow-hidden transition-all min-h-[415px] sm:min-h-[430px]"
    >
      {/* Subtle ambient radial background glow on white */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            voiceState === 'speaking'
              ? 'radial-gradient(ellipse 65% 55% at 50% 65%, rgba(56, 189, 248, 0.10) 0%, rgba(255, 255, 255, 0) 75%)'
              : voiceState === 'listening'
              ? 'radial-gradient(ellipse 65% 55% at 50% 65%, rgba(232, 248, 74, 0.20) 0%, rgba(255, 255, 255, 0) 75%)'
              : 'radial-gradient(ellipse 65% 55% at 50% 65%, rgba(17, 18, 21, 0.02) 0%, rgba(255, 255, 255, 0) 70%)',
        }}
      />

      {/* Top Header Row with Status & Mic Controls */}
      <div className="relative z-10 flex items-center justify-between pb-2">
        {/* Status indicator with honest labels */}
        <div className="flex items-center gap-2.5">
          <div
            className={`w-3 h-3 rounded-full transition-all duration-300 ${
              voiceState === 'listening'
                ? 'bg-[#65A30D] shadow-[0_0_10px_rgba(101,163,13,0.6)] animate-pulse'
                : voiceState === 'speaking'
                ? 'bg-[#0284C7] shadow-[0_0_10px_rgba(2,132,199,0.6)] animate-pulse'
                : voiceState === 'requesting'
                ? 'bg-amber-500 animate-ping'
                : voiceState === 'error'
                ? 'bg-rose-500'
                : 'bg-emerald-500'
            }`}
          />
          <span
            className={`text-xs sm:text-[13px] font-mono tracking-wider font-bold uppercase ${
              voiceState === 'speaking' 
                ? 'text-[#0369A1]' 
                : voiceState === 'listening' 
                ? 'text-[#3F6212]' 
                : voiceState === 'error'
                ? 'text-rose-700'
                : 'text-[#111215]'
            }`}
          >
            {voiceState === 'listening'
              ? 'AUDIO STREAM • ACTIVE MIC (LIVE FFT)'
              : voiceState === 'speaking'
              ? 'HYDRA GUIDE • SPEAKING (SYNCHRONISED ENVELOPE)'
              : voiceState === 'requesting'
              ? 'MICROPHONE • ACQUIRING HARDWARE...'
              : voiceState === 'thinking'
              ? 'HYDRA GUIDE • REASONING...'
              : voiceState === 'error'
              ? 'HARDWARE OFFLINE • PERMISSION ERROR'
              : 'REAL-TIME AUDIO EQUALISER • STANDBY'}
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {audioError && (
            <span className="text-xs text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-full font-medium">
              {audioError}
            </span>
          )}

          {/* Audio Mute/Unmute toggle for TTS */}
          <button
            onClick={toggleMute}
            className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-black border border-gray-200/80 transition-all cursor-pointer shadow-2xs"
            title={isMuted ? 'Unmute Hydra Voice' : 'Mute Hydra Voice'}
          >
            {isMuted ? <VolumeX className="w-4 h-4 text-rose-500" /> : <Volume2 className="w-4 h-4 text-[#4D7C0F]" />}
          </button>

          {/* Interactive Mic Toggle Button with Subtle Neon Effect */}
          <button
            onClick={toggleMic}
            className={`px-4 py-2 rounded-full text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer select-none ${
              voiceState === 'listening'
                ? 'bg-white text-[#111215] border border-[#CCFF00] shadow-[0_0_12px_rgba(204,255,0,0.7)] ring-2 ring-[#CCFF00]/60 font-bold'
                : 'bg-gray-100 hover:bg-gray-200 text-[#111215] border border-gray-300 font-medium'
            }`}
            title={
              voiceState === 'listening'
                ? 'Click to stop live microphone stream'
                : 'Click to start live microphone session with Hydra Guide'
            }
            aria-label={
              voiceState === 'listening'
                ? 'Active microphone, click to stop'
                : 'Start live microphone'
            }
          >
            <Mic className="w-4 h-4 text-[#111215]" />
            <span>Live Mic</span>
          </button>

          {/* Transcript & Guide Drawer Toggle */}
          <button
            onClick={() => {
              if (onOpenGuide) {
                onOpenGuide();
              } else {
                setShowTranscriptDrawer((prev) => !prev);
              }
            }}
            className="px-3.5 py-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-black border border-gray-200/80 text-xs flex items-center gap-1.5 cursor-pointer font-medium shadow-2xs"
            title="Open Hydra Guide Transcript"
          >
            <MessageSquare className="w-4 h-4 text-[#4D7C0F]" />
            <span className="hidden sm:inline">Guide Log</span>
          </button>
        </div>
      </div>

      {/* Center Visualiser Canvas (Generous Height for Tall Prominent Bars) */}
      <div className="relative z-10 flex items-center justify-center my-1.5 w-full h-[185px] sm:h-[205px] overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full h-full block"
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {/* Live Transcript / Dialogue Preview Ticker */}
      <div className="relative z-10 my-2 px-4 py-2.5 rounded-2xl bg-gray-50 border border-gray-200/80 text-xs sm:text-sm text-gray-800 flex items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-2.5 min-w-0">
          <span
            className={`font-mono text-[10px] sm:text-xs uppercase font-bold shrink-0 ${
              voiceState === 'listening' ? 'text-[#3F6212]' : voiceState === 'speaking' ? 'text-[#0369A1]' : 'text-gray-500'
            }`}
          >
            {voiceState === 'listening'
              ? 'Student (Listening):'
              : voiceState === 'speaking'
              ? 'Hydra Guide:'
              : 'Latest Log:'}
          </span>
          <span className="truncate italic text-gray-600 text-xs sm:text-[13px]">
            {voiceState === 'listening'
              ? liveTranscript || 'Listening for your voice instructions...'
              : lastMessage
              ? lastMessage.text
              : 'Hydra Guide is ready. Speak or explore your multi-domain recommendations.'}
          </span>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="hidden md:flex items-center gap-2 shrink-0">
          <button
            onClick={() => voiceManager.handleStudentUtterance('Show me the catalogue')}
            className="text-xs px-2.5 py-1 rounded-lg bg-white hover:bg-gray-100 text-gray-700 hover:text-black border border-gray-200 shadow-2xs transition-all cursor-pointer font-medium"
          >
            "Show catalogue"
          </button>
          <button
            onClick={() => voiceManager.handleStudentUtterance('Compare top programmes')}
            className="text-xs px-2.5 py-1 rounded-lg bg-white hover:bg-gray-100 text-gray-700 hover:text-black border border-gray-200 shadow-2xs transition-all cursor-pointer font-medium"
          >
            "Compare"
          </button>
          <button
            onClick={() => voiceManager.handleStudentUtterance('Give me a report of my profile')}
            className="text-xs px-2.5 py-1 rounded-lg bg-[#E8F84A] hover:bg-[#D8E83A] text-[#111215] border border-[#CCD820] shadow-2xs transition-all cursor-pointer font-bold"
          >
            "Profile Report"
          </button>
          <button
            onClick={() => voiceManager.handleStudentUtterance('What should I do next?')}
            className="text-xs px-2.5 py-1 rounded-lg bg-white hover:bg-gray-100 text-gray-700 hover:text-black border border-gray-200 shadow-2xs transition-all cursor-pointer font-medium"
          >
            "What next?"
          </button>
        </div>
      </div>

      {/* Bottom Audio Calibration Bar (Honest Spectrum / Model Details) */}
      <div className="relative z-10 pt-2.5 border-t border-gray-100 flex flex-wrap items-center justify-between text-xs font-mono text-gray-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-gray-700 font-medium">
            <Radio className="w-3.5 h-3.5 text-[#4D7C0F]" />
            <span>32-BAND SPECTRUM</span>
          </span>
          <span>•</span>
          <span>
            {voiceState === 'listening'
              ? 'FFT 128 / 48kHz (MIC SOURCE)'
              : voiceState === 'speaking'
              ? 'STATE: PROSODIC SPEECH ENVELOPE'
              : 'STANDBY (AMBIENT OSCILLATOR)'}
          </span>
          <span>•</span>
          <span className={peakLevel > 0.4 ? 'text-[#4D7C0F] font-bold' : 'text-gray-400'}>
            PEAK: {Math.round(peakLevel * 100)}%
          </span>
        </div>

        <div className="text-xs text-gray-400 flex items-center gap-1.5">
          <Volume2 className="w-3.5 h-3.5 text-gray-500" />
          <span>HYDRA UNIFIED AUDIO ENGINE</span>
        </div>
      </div>

      {/* Inline Transcript Modal / Drawer if opened */}
      {showTranscriptDrawer && (
        <div
          className="absolute inset-x-0 bottom-0 top-10 z-30 p-4 rounded-b-3xl flex flex-col justify-between backdrop-blur-md bg-white/95 border-t border-gray-200 shadow-xl"
        >
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <span className="text-xs font-mono font-bold text-[#111215] uppercase">
              Hydra Guide Dialogue History
            </span>
            <button
              onClick={() => setShowTranscriptDrawer(false)}
              className="text-xs text-gray-600 hover:text-black px-2 py-0.5 rounded-sm bg-gray-100 hover:bg-gray-200 cursor-pointer"
            >
              Close ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto my-2 space-y-2 pr-1 scrollbar-thin text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`p-2.5 rounded-xl max-w-[85%] ${
                  m.sender === 'student'
                    ? 'ml-auto bg-[#E8F84A] text-[#111215] font-medium border border-[#D4E82E]'
                    : 'mr-auto bg-gray-50 text-gray-800 border border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between gap-3 text-[10px] text-gray-500 mb-1">
                  <span className="font-bold">{m.sender === 'student' ? 'Master Shubham' : 'Hydra Guide'}</span>
                  <span>{m.timestamp}</span>
                </div>
                <p className="leading-relaxed">{m.text}</p>
                {m.intent && (
                  <span className="inline-block mt-1 text-[9px] font-mono px-1.5 py-0.5 rounded-sm bg-black/10 text-sky-800 font-semibold">
                    Action: {m.intent}
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Text Input Fallback */}
          <form onSubmit={handleSendText} className="flex gap-2 pt-2 border-t border-gray-200">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your question or instruction (e.g. 'Show me the catalogue')..."
              className="flex-1 bg-gray-50 border border-gray-300 rounded-xl px-3 py-1.5 text-xs text-gray-900 placeholder-gray-500 focus:outline-hidden focus:border-black"
            />
            <button
              type="submit"
              className="px-4 py-1.5 rounded-xl bg-[#111215] text-white font-bold text-xs hover:bg-black cursor-pointer shadow-xs"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
