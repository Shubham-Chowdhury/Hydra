/**
 * Unified Voice & Audio Session Manager for Hydra Guide and AudioEqualizer.
 *
 * Implements a single-source-of-truth audio session to prevent duplicate
 * microphone streams, duplicate permission prompts, and resource leaks.
 */

export type VoiceState =
  | 'idle'
  | 'requesting'
  | 'listening'
  | 'transcribing'
  | 'thinking'
  | 'speaking'
  | 'error';

export interface VoiceMessage {
  id: string;
  sender: 'student' | 'hydra';
  text: string;
  timestamp: string;
  intent?: string | null;
}

type StateListener = (state: VoiceState) => void;
type TranscriptListener = (transcript: string, isFinal: boolean) => void;
type MessageListener = (messages: VoiceMessage[]) => void;
type NavigationListener = (intent: string) => void;

class VoiceManager {
  private state: VoiceState = 'idle';
  private errorMessage: string | null = null;

  // Web Audio Graph (Shared Singleton)
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private mediaStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;

  // Speech Recognition (STT)
  private recognition: any = null;
  private isRecognitionActive: boolean = false;

  // Speech Synthesis (TTS)
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private isMuted: boolean = false;

  // Conversation history
  private messages: VoiceMessage[] = [
    {
      id: 'msg-welcome',
      sender: 'hydra',
      text: "Hello Master Shubham. I am your Hydra Guide. Your academic profile and multi-domain pathways are ready. You can speak to me or ask what to explore next.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ];

  // Listeners
  private stateListeners: Set<StateListener> = new Set();
  private transcriptListeners: Set<TranscriptListener> = new Set();
  private messageListeners: Set<MessageListener> = new Set();
  private navigationListeners: Set<NavigationListener> = new Set();

  constructor() {
    this.initSpeechRecognition();
  }

  // Navigation and active view context
  private currentDestination: string = 'overview';

  public setCurrentDestination(dest: string) {
    this.currentDestination = dest;
  }

  public getCurrentDestination(): string {
    return this.currentDestination;
  }

  public getState(): VoiceState {
    return this.state;
  }

  public getErrorMessage(): string | null {
    return this.errorMessage;
  }

  public getAnalyser(): AnalyserNode | null {
    return this.analyser;
  }

  public getMessages(): VoiceMessage[] {
    return [...this.messages];
  }

  public isSpeechMuted(): boolean {
    return this.isMuted;
  }

  public isSpeaking(): boolean {
    return Boolean(this.currentUtterance && this.state === 'speaking');
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (muted && typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      if (this.state === 'speaking') {
        this.setState('idle');
      }
    }
  }

  // Listener subscriptions
  public subscribeState(fn: StateListener): () => void {
    this.stateListeners.add(fn);
    fn(this.state);
    return () => this.stateListeners.delete(fn);
  }

  public subscribeTranscript(fn: TranscriptListener): () => void {
    this.transcriptListeners.add(fn);
    return () => this.transcriptListeners.delete(fn);
  }

  public subscribeMessages(fn: MessageListener): () => void {
    this.messageListeners.add(fn);
    fn(this.messages);
    return () => this.messageListeners.delete(fn);
  }

  public subscribeNavigation(fn: NavigationListener): () => void {
    this.navigationListeners.add(fn);
    return () => this.navigationListeners.delete(fn);
  }

  private setState(newState: VoiceState, error: string | null = null) {
    this.state = newState;
    this.errorMessage = error;
    this.stateListeners.forEach((fn) => fn(newState));
  }

  private notifyTranscript(text: string, isFinal: boolean) {
    this.transcriptListeners.forEach((fn) => fn(text, isFinal));
  }

  private addMessage(sender: 'student' | 'hydra', text: string, intent?: string | null) {
    const newMsg: VoiceMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      sender,
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent,
    };
    this.messages = [...this.messages, newMsg];
    this.messageListeners.forEach((fn) => fn(this.messages));
  }

  // Initialise Speech Recognition if supported in browser
  private initSpeechRecognition() {
    if (typeof window === 'undefined') return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-IN'; // Default to Indian English / English

      rec.onresult = (event: any) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        const currentText = final || interim;
        if (currentText) {
          this.notifyTranscript(currentText, Boolean(final));
        }

        if (final) {
          this.handleStudentUtterance(final);
        }
      };

      rec.onerror = (event: any) => {
        if (event.error === 'no-speech') {
          // Normal timeout with no speech
          return;
        }
        if (event.error === 'not-allowed') {
          this.setState('error', 'Microphone access denied by browser');
        } else {
          this.setState('error', `Speech error: ${event.error}`);
        }
      };

      rec.onend = () => {
        this.isRecognitionActive = false;
        if (this.state === 'listening') {
          this.setState('idle');
        }
      };

      this.recognition = rec;
    }
  }

  /**
   * Activate microphone session.
   * Acquires single MediaStream, connects single AnalyserNode, starts recognition.
   */
  public async startListening(): Promise<boolean> {
    if (this.state === 'listening' || this.state === 'requesting') {
      return true;
    }

    // Stop any active speech before listening
    this.stopSpeaking();
    this.setState('requesting');

    try {
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('Microphone audio capture is not supported in this environment.');
      }

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Lazy-initialise AudioContext on user gesture
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) {
        throw new Error('Web Audio API is not available.');
      }

      let audioCtx = this.audioContext;
      if (!audioCtx || audioCtx.state === 'closed') {
        audioCtx = new AudioCtx();
        this.audioContext = audioCtx;
      }
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }

      // Setup AnalyserNode for frequency analysis
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.75;
      analyser.minDecibels = -85;
      analyser.maxDecibels = -15;

      const sourceNode = audioCtx.createMediaStreamSource(stream);
      sourceNode.connect(analyser);

      this.mediaStream = stream;
      this.analyser = analyser;
      this.sourceNode = sourceNode;

      // Start recognition if available
      if (this.recognition && !this.isRecognitionActive) {
        try {
          this.recognition.start();
          this.isRecognitionActive = true;
        } catch {
          // Already started or busy
        }
      }

      this.setState('listening');
      return true;
    } catch (err: any) {
      this.stopListening();
      const msg =
        err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError'
          ? 'Microphone permission denied'
          : err.message || 'Microphone activation failed';
      this.setState('error', msg);
      return false;
    }
  }

  /**
   * Stop microphone session and clean up all audio hardware resources.
   */
  public stopListening() {
    if (this.recognition && this.isRecognitionActive) {
      try {
        this.recognition.stop();
      } catch {}
      this.isRecognitionActive = false;
    }

    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect();
      } catch {}
      this.sourceNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {}
      });
      this.mediaStream = null;
    }

    this.analyser = null;

    if (this.state === 'listening' || this.state === 'requesting') {
      this.setState('idle');
    }
  }

  public toggleListening(): Promise<boolean> {
    if (this.state === 'listening' || this.state === 'requesting') {
      this.stopListening();
      return Promise.resolve(false);
    } else {
      return this.startListening();
    }
  }

  /**
   * Select a sweet, high-clarity natural female voice for Hydra Guide.
   * Prioritizes high-end neural and natural female voices across browsers.
   */
  private selectSweetFemaleVoice(): SpeechSynthesisVoice | null {
    if (typeof window === 'undefined' || !window.speechSynthesis) return null;
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return null;

    // Prioritized list for sweet, natural, friendly female voices
    const preferredKeywords = [
      'google uk english female',
      'jenny',
      'aria',
      'zira',
      'sonia',
      'samantha',
      'victoria',
      'karen',
      'neerja',
      'natural',
      'female',
    ];

    for (const kw of preferredKeywords) {
      const match = voices.find(
        (v) =>
          v.lang.startsWith('en') &&
          v.name.toLowerCase().includes(kw)
      );
      if (match) return match;
    }

    // Secondary fallback: any voice with "female" in description or name
    const anyFemale = voices.find(
      (v) =>
        v.lang.startsWith('en') &&
        (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('woman'))
    );
    if (anyFemale) return anyFemale;

    // Tertiary fallback: clean English voice
    return voices.find((v) => v.lang.startsWith('en')) || voices[0] || null;
  }

  /**
   * Process spoken or typed student utterance with natural conversational intelligence.
   * Capable of executing every task and navigating to every destination in the application.
   */
  public async handleStudentUtterance(text: string) {
    if (!text || !text.trim()) return;

    const trimmed = text.trim();
    this.addMessage('student', trimmed);
    this.stopListening();
    this.setState('thinking');

    const lower = trimmed.toLowerCase();
    let reply = '';
    let navIntent: string | null = null;

    // 1. GREETINGS & CASUAL INTERACTION (Natural, warm, polite — never echo back robotically)
    if (
      lower === 'hi' ||
      lower === 'hello' ||
      lower === 'hey' ||
      lower === 'hey hi' ||
      lower === 'hello hydra' ||
      lower === 'hey hydra' ||
      lower.startsWith('good morning') ||
      lower.startsWith('good afternoon') ||
      lower.startsWith('good evening') ||
      lower.includes('how are you') ||
      lower.includes('whats up') ||
      lower.includes('namaste')
    ) {
      reply =
        "Hello Master Shubham! Wonderful to speak with you. I'm your Hydra Guide, ready to assist with any admissions task, explore pathways, or run simulations. What would you like to do?";
    }

    // 2. COMPREHENSIVE ASSESSMENT & NEURAL CAREER PATHWAY REPORT
    else if (
      lower.includes('detailed report') ||
      lower.includes('assessment report') ||
      lower.includes('assesment report') ||
      lower.includes('profile report') ||
      lower.includes('career report') ||
      lower.includes('carrer report') ||
      lower.includes('pathway report') ||
      lower.includes('comprehensive report') ||
      lower.includes('voice report') ||
      lower.includes('deep learning report') ||
      lower.includes('give me a report') ||
      lower.includes('give me my report') ||
      (lower.includes('report') &&
        (lower.includes('profile') ||
          lower.includes('assessment') ||
          lower.includes('assesment') ||
          lower.includes('career') ||
          lower.includes('carrer') ||
          lower.includes('pathway') ||
          lower.includes('my') ||
          lower.includes('progress') ||
          lower.includes('me'))) ||
      lower.includes('track what i am doing') ||
      lower.includes('track what im doing')
    ) {
      reply =
        "Synthesizing your comprehensive academic assessment and deep learning career pathway report now. Consolidating deterministic eligibility with neural trajectory sequence projections.";
      navIntent = 'action_generate_assessment_report';
    }

    // 3. IN-UNIT ACTIONS (EXECUTE SIMULATIONS INSIDE SUB-UNITS)
    // B. Heist Planner pathway calculation
    else if (
      ((lower.includes('run') || lower.includes('execute') || lower.includes('plan') || lower.includes('calculate') || lower.includes('generate')) &&
        (lower.includes('heist') || lower.includes('planner') || lower.includes('prerequisite plan') || lower.includes('roadmap'))) ||
      (this.currentDestination === 'planner' &&
        (lower.includes('run') || lower.includes('plan') || lower.includes('execute') || lower.includes('inside')) &&
        !lower.includes('auction') && !lower.includes('franchise') && !lower.includes('boss'))
    ) {
      reply =
        "Executing the A* heuristic pathway planner now to compute your optimal prerequisite milestones.";
      navIntent = 'action_run_planner';
    }
    // C. Boss Fight stress test
    else if (
      (lower.includes('boss') || lower.includes('interview') || lower.includes('board defense')) &&
      (lower.includes('run') || lower.includes('start') || lower.includes('simulate') || lower.includes('test') || lower.includes('fight'))
    ) {
      reply =
        "Initiating Boss-Fight simulation now to stress-test your admissions case against institutional admission boards.";
      navIntent = 'action_run_boss_fight';
    }
    // D. Admissions resilience simulation / Monte Carlo
    else if (
      ((lower.includes('run') || lower.includes('simulate') || lower.includes('start')) &&
        (lower.includes('stress test') || lower.includes('monte carlo') || lower.includes('adverse scenario') || (lower.includes('simulation') && !lower.includes('franchise') && !lower.includes('auction')))) ||
      (this.currentDestination === 'simulation' &&
        (lower.includes('run') || lower.includes('simulate') || lower.includes('inside')) &&
        !lower.includes('auction') && !lower.includes('franchise') && !lower.includes('planner'))
    ) {
      reply =
        "Running admissions resilience simulation now across adverse tuition and cutoff shifts.";
      navIntent = 'action_run_simulation';
    }
    // E. Oracle Cutoff Forecast
    else if (
      ((lower.includes('run') || lower.includes('forecast') || lower.includes('predict') || lower.includes('calculate')) &&
        (lower.includes('oracle') || lower.includes('cutoff') || lower.includes('closing rank') || lower.includes('trend'))) ||
      (this.currentDestination === 'oracle' &&
        (lower.includes('run') || lower.includes('forecast') || lower.includes('predict') || lower.includes('inside')) &&
        !lower.includes('auction') && !lower.includes('franchise'))
    ) {
      reply =
        "Executing the Oracle cutoff forecast now. Generating calibrated closing rank trajectories with probabilistic uncertainty bounds.";
      navIntent = 'action_run_forecast';
    }
    // F. Central Referee multi-agent consensus
    else if (
      ((lower.includes('run') || lower.includes('synthesize') || lower.includes('orchestrate') || lower.includes('evaluate')) &&
        (lower.includes('referee') || lower.includes('consensus') || lower.includes('council') || lower.includes('all agents'))) ||
      (this.currentDestination === 'referee' &&
        (lower.includes('run') || lower.includes('synthesize') || lower.includes('inside')) &&
        !lower.includes('auction') && !lower.includes('franchise'))
    ) {
      reply =
        "Orchestrating multi-agent consensus evaluation across all six specialized agents now.";
      navIntent = 'action_run_referee';
    }
    // G. Interest Decoder
    else if (
      (lower.includes('decode') && (lower.includes('interest') || lower.includes('affinity') || lower.includes('narrative'))) ||
      (this.currentDestination === 'interests' &&
        (lower.includes('run') || lower.includes('decode') || lower.includes('inside')))
    ) {
      reply =
        "Decoding student natural language narrative into canonical academic ontology concepts.";
      navIntent = 'action_run_decode';
    }
    // A. Franchise Auction simulation execution
    else if (
      ((lower.includes('run') || lower.includes('execute') || lower.includes('start') || lower.includes('simulate')) &&
        (lower.includes('auction') || (lower.includes('franchise') && (lower.includes('simulation') || lower.includes('bid'))))) ||
      (this.currentDestination === 'franchise' &&
        (lower.includes('run') || lower.includes('simulate') || lower.includes('start') || lower.includes('inside') || lower.includes('bid')) &&
        !lower.includes('planner') && !lower.includes('boss') && !lower.includes('oracle'))
    ) {
      reply =
        "Executing simulated programme auction now. Autonomous university agents are submitting their bids based on your credentials and budget.";
      navIntent = 'action_run_franchise_auction';
    }

    // 4. PROGRAMME COMPARISON & ACTIONS
    else if (
      lower.includes('compare top') ||
      lower.includes('compare best') ||
      lower.includes('compare recommendations')
    ) {
      reply =
        "Adding your top recommended programmes to the comparison deck.";
      navIntent = 'action_compare_top';
    } else if (
      lower.includes('clear compare') ||
      lower.includes('reset compare') ||
      lower.includes('empty compare')
    ) {
      reply = "Clearing your programme comparison list.";
      navIntent = 'action_clear_compare';
    } else if (
      lower.includes('compare') ||
      lower.includes('comparison') ||
      lower.includes('side by side') ||
      lower.includes('versus') ||
      lower.includes('difference between')
    ) {
      reply =
        "Navigating to Programme Comparison. You can compare curriculum prerequisites, tuition costs, and placement trajectories side-by-side.";
      navIntent = 'navigate_compare';
    }

    // 5. FRANCHISE AUCTION NAVIGATION
    else if (
      lower.includes('franchise') ||
      lower.includes('auction') ||
      lower.includes('bids') ||
      lower.includes('bidding') ||
      lower.includes('tokens') ||
      lower.includes('quota')
    ) {
      reply =
        "Opening the Franchise Auction now. Here you can inspect autonomous university agent bids, quota valuations, and scholarship allocations.";
      navIntent = 'navigate_franchise';
    }

    // 4. PROGRAMME CATALOGUE / DISCOVERY
    else if (
      lower.includes('catalogue') ||
      lower.includes('catalog') ||
      lower.includes('programme') ||
      lower.includes('program') ||
      lower.includes('courses') ||
      lower.includes('degrees') ||
      lower.includes('show college') ||
      lower.includes('show university')
    ) {
      reply =
        "Opening your Programme Catalogue. 17 accredited programmes across 8 academic disciplines are ready for your review.";
      navIntent = 'navigate_catalog';
    }

    // 5. CENTRAL REFEREE / COUNCIL CONSENSUS
    else if (
      lower.includes('referee') ||
      lower.includes('council') ||
      lower.includes('consensus') ||
      lower.includes('multi-agent') ||
      lower.includes('multi agent') ||
      lower.includes('verdict') ||
      lower.includes('synthesis')
    ) {
      reply =
        "Opening Central Referee consensus synthesis. All six intelligence agents have agreed on your top multi-domain recommendations.";
      navIntent = 'navigate_referee';
    }

    // 6. STUDENT DIGITAL TWIN
    else if (
      lower.includes('twin') ||
      lower.includes('digital twin') ||
      lower.includes('student model') ||
      lower.includes('my twin') ||
      lower.includes('capability matrix')
    ) {
      reply =
        "Opening your Student Digital Twin. You can inspect your capability vectors, subject masteries, and preference embeddings.";
      navIntent = 'navigate_twin';
    }

    // 7. HEIST PLANNER / STRATEGIC PATHWAY
    else if (
      lower.includes('planner') ||
      lower.includes('heist') ||
      lower.includes('pathway') ||
      lower.includes('roadmap') ||
      lower.includes('heuristic') ||
      lower.includes('prerequisite plan')
    ) {
      reply =
        "Opening the Heist Planner. A* heuristic pathway planning has structured your prerequisite milestones step-by-step.";
      navIntent = 'navigate_planner';
    }

    // 8. SIMULATOR & BOSS-FIGHT
    else if (
      lower.includes('simulator') ||
      lower.includes('boss') ||
      lower.includes('simulation') ||
      lower.includes('interview') ||
      lower.includes('defense') ||
      lower.includes('stress test')
    ) {
      reply =
        "Opening Simulator and Boss-Fight. You can stress-test your admissions case and interview scenarios against institutional admission boards.";
      navIntent = 'navigate_simulation';
    }

    // 9. ORACLE FORECAST & CUTOFFS
    else if (
      lower.includes('oracle') ||
      lower.includes('forecast') ||
      lower.includes('cutoff') ||
      lower.includes('cut off') ||
      lower.includes('closing rank') ||
      lower.includes('prediction') ||
      lower.includes('rank trends')
    ) {
      reply =
        "Opening Oracle Forecast. Reviewing historical closing rank cutoffs, percentile trends, and probabilistic forecast bands.";
      navIntent = 'navigate_oracle';
    }

    // 10. INTEREST DECODER
    else if (
      lower.includes('interest') ||
      lower.includes('decoder') ||
      lower.includes('affinity') ||
      lower.includes('passions') ||
      lower.includes('subject weight')
    ) {
      reply =
        "Opening Interest Decoder. Visualizing your academic affinities and inter-disciplinary interests.";
      navIntent = 'navigate_interests';
    }

    // 11. DEGREE TRAJECTORIES & CAREER EXPLORATION
    else if (
      lower.includes('career') ||
      lower.includes('job') ||
      lower.includes('salary') ||
      lower.includes('trajectories') ||
      lower.includes('employment') ||
      lower.includes('placement') ||
      lower.includes('industry')
    ) {
      reply =
        "Opening Degree Trajectories and Career Exploration. Exploring industry benchmarks, employment rates, and career progression.";
      navIntent = 'navigate_career';
    }

    // 12. ACTION PLAN
    else if (
      lower.includes('action plan') ||
      lower.includes('milestones') ||
      lower.includes('tasks') ||
      lower.includes('checklist') ||
      lower.includes('to do') ||
      lower.includes('todo')
    ) {
      reply =
        "Opening your Action Plan. Reviewing your upcoming prerequisite deadlines and application milestones.";
      navIntent = 'navigate_plan';
    }

    // 13. INSTITUTION DIRECTORY & SOURCES
    else if (
      lower.includes('directory') ||
      lower.includes('institution') ||
      lower.includes('sources') ||
      lower.includes('accredited') ||
      lower.includes('partners') ||
      lower.includes('colleges list')
    ) {
      reply =
        "Opening the Institution Directory and verification sources across accredited universities.";
      navIntent = 'navigate_sources';
    }

    // 14. HELP CENTER & RULES GUIDE
    else if (
      lower.includes('help') ||
      lower.includes('rules') ||
      lower.includes('criteria') ||
      lower.includes('scoring formula') ||
      lower.includes('academy') ||
      lower.includes('how it works')
    ) {
      reply =
        "Opening Help Center and the deterministic Criteria & Rules Guide.";
      navIntent = 'navigate_help';
    }

    // 15. STUDENT PROFILE / EDIT MARKS
    else if (
      lower.includes('profile') ||
      lower.includes('edit profile') ||
      lower.includes('change mark') ||
      lower.includes('change score') ||
      lower.includes('my scores') ||
      lower.includes('update rank') ||
      lower.includes('my budget') ||
      lower.includes('preferences')
    ) {
      reply =
        "Opening your Student Profile editor. You can update your Class 12 scores, entrance ranks, and budget preferences here.";
      navIntent = 'navigate_profile';
    }

    // 16. OVERVIEW / HOME / RADAR
    else if (
      lower.includes('overview') ||
      lower.includes('radar') ||
      lower.includes('home') ||
      lower.includes('dashboard') ||
      lower.includes('main page') ||
      lower.includes('go back')
    ) {
      reply = "Returning to Admissions Radar overview.";
      navIntent = 'navigate_overview';
    }

    // 17. ACTIONS: RE-RUN EVALUATION
    else if (
      lower.includes('evaluate') ||
      lower.includes('evaluation') ||
      lower.includes('re-evaluate') ||
      lower.includes('re evaluate') ||
      lower.includes('assess me') ||
      lower.includes('calculate eligibility') ||
      lower.includes('refresh results')
    ) {
      reply =
        "Re-running multi-domain symbolic eligibility evaluation now. Checking all prerequisites across the knowledge graph.";
      navIntent = 'action_evaluate';
    }

    // 18. ACTIONS: OPEN SETTINGS / TECHNICAL DRAWER
    else if (
      lower.includes('settings') ||
      lower.includes('technical drawer') ||
      lower.includes('backend status') ||
      lower.includes('telemetry') ||
      lower.includes('configuration')
    ) {
      reply = "Opening system settings and technical telemetry drawer.";
      navIntent = 'action_open_settings';
    }

    // 21. GUIDANCE: EXPLAIN ELIGIBILITY STATUS
    else if (
      lower.includes('why am i eligible') ||
      lower.includes('why not eligible') ||
      lower.includes('why ineligible') ||
      lower.includes('am i qualified') ||
      lower.includes('eligibility rule')
    ) {
      reply =
        "Eligibility is strictly deterministic in Hydra. We verify mandatory Class 12 subject cutoffs and entrance exam criteria directly against accredited university requirements without approximation.";
      navIntent = 'explain_eligibility';
    }

    // 22. GUIDANCE: WHAT TO DO NEXT
    else if (
      lower.includes('what should i do next') ||
      lower.includes('what next') ||
      lower.includes('where to start') ||
      lower.includes('next step') ||
      lower.includes('what do you suggest')
    ) {
      reply =
        "Based on your verified 88% in Mathematics and strong JEE Main rank, your best immediate move is reviewing the Programme Catalogue or examining Franchise Auction bids. Shall I open the Catalogue or the Auction?";
      navIntent = 'show_next_recommended_step';
    }

    // 23. WHO ARE YOU / IDENTITY
    else if (
      lower.includes('who are you') ||
      lower.includes('what are you') ||
      lower.includes('what can you do')
    ) {
      reply =
        "I am your Hydra Guide, powered by Hydra's multi-agent admissions architecture. I can navigate to any section of the platform—like Franchise Auction, Twin Engine, or Heist Planner—explain eligibility rules, or evaluate your academic options.";
    }

    // 24. MUTE / SILENCE
    else if (
      lower.includes('be quiet') ||
      lower.includes('mute') ||
      lower.includes('stop talking') ||
      lower.includes('silence')
    ) {
      reply = "Understood. Muting voice responses. You can unmute me anytime.";
      this.setMuted(true);
    }

    // 25. INTELLIGENT FALLBACK (Friendly, helpful guidance — never echo or say "I noted: ...")
    else {
      reply =
        "I'm listening, Master Shubham. Would you like me to open the Franchise Auction, inspect the Programme Catalogue, run the Heist Planner, or re-evaluate your profile?";
    }

    this.addMessage('hydra', reply, navIntent);

    // Speak reply using browser SpeechSynthesis with sweet female voice
    await this.speak(reply);

    // Trigger navigation callbacks
    if (navIntent) {
      this.navigationListeners.forEach((fn) => fn(navIntent!));
      if ((window as any).__HYDRA_NAVIGATE_CALLBACK__) {
        (window as any).__HYDRA_NAVIGATE_CALLBACK__(navIntent);
      }
    }
  }

  /**
   * Send a text message to Hydra Guide (for keyboards or text fallback).
   */
  public async sendTextMessage(text: string) {
    if (!text || !text.trim()) return;
    await this.handleStudentUtterance(text.trim());
  }

  /**
   * Speak reply using SpeechSynthesis.
   * State is explicitly 'speaking' with a synchronised envelope.
   */
  public speak(text: string): Promise<void> {
    return new Promise((resolve) => {
      if (this.isMuted || typeof window === 'undefined' || !window.speechSynthesis) {
        this.setState('idle');
        resolve();
        return;
      }

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.98; // Natural, articulate, friendly cadence
      utterance.pitch = 1.10; // Warm, sweeter melodic pitch
      utterance.lang = 'en-US';

      // Pick a sweet, pleasant female voice
      const sweetVoice = this.selectSweetFemaleVoice();
      if (sweetVoice) {
        utterance.voice = sweetVoice;
        utterance.lang = sweetVoice.lang;
      }

      utterance.onstart = () => {
        this.setState('speaking');
      };

      utterance.onend = () => {
        this.currentUtterance = null;
        this.setState('idle');
        resolve();
      };

      utterance.onerror = () => {
        this.currentUtterance = null;
        this.setState('idle');
        resolve();
      };

      this.currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
    });
  }

  public stopSpeaking() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    this.currentUtterance = null;
    if (this.state === 'speaking') {
      this.setState('idle');
    }
  }
}

// Export singleton
export const voiceManager = new VoiceManager();

if (typeof window !== 'undefined') {
  (window as any).__voiceManager = voiceManager;
}

