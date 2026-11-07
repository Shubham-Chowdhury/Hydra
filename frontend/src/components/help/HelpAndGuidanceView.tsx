import React, { useState } from 'react';
import {
  HelpCircle,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Scale,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import { PageHeader } from '../common/PageHeader';
import { DemoNoticeBanner } from '../common/DemoNoticeBanner';

export const HelpAndGuidanceView: React.FC = () => {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);

  const toggleFaq = (index: number) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  const faqs = [
    {
      q: 'How does Hydra evaluate my academic eligibility?',
      a: 'Hydra uses deterministic symbolic rule trees executed entirely on the Python backend. For example, if a programme requires Mathematics ≥ 80% and a JEE rank ≤ 35,000, Hydra strictly verifies those facts against your inputs. It never uses probabilistic generative models to decide admission eligibility.',
    },
    {
      q: 'Why does my status show "Needs Review" instead of Eligible or Ineligible?',
      a: 'In Hydra\'s 3-state model, missing facts never default to "satisfies" or "ineligible". If a mandatory prerequisite fact (such as your Chemistry marks or entrance exam score) is absent, Hydra marks the status as "needs_review" to ensure you are alerted to provide the missing document.',
    },
    {
      q: 'Why are eligibility and affordability evaluated separately?',
      a: 'Academic qualification and financial capacity are independent realities. You can be academically eligible for an elite programme that exceeds your stated tuition budget, or within budget for a programme whose prerequisites you have not yet met. Hydra decouples them so you see the complete, transparent picture.',
    },
    {
      q: 'Are the university names in this application real institutions?',
      a: 'No. To ensure absolute integrity during development, all institutions in this demonstration catalog are synthetic (e.g. "Demo Institute of Technology, Bengaluru"). Hydra never fabricates real university names or claims official authority until live verified datasets are released.',
    },
    {
      q: 'What does the Oracle Cutoff Prediction Interval mean?',
      a: 'University cutoffs fluctuate year-to-year based on applicant numbers and exam difficulty. Hydra\'s Oracle agent uses linear regression over historical trends to provide a calibrated prediction interval (p5–p95), showing the realistic range of closing ranks rather than a false single-point certainty.',
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Help, Glossary & Admissions Guide"
        description="Clear, calm explanations of Hydra's evaluation standards, metrics, and admissions counselling terms."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Student Guidance
          </span>
        }
      />

      <DemoNoticeBanner />

      {/* Section 1: The 3-State Model Explained */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
            <Scale className="w-5 h-5 text-[#176B63]" />
            <span>Understanding Hydra's 3-State Eligibility Model</span>
          </h3>
          <p className="text-xs text-[#52615E] mt-0.5">
            Every academic pathway is classified into one of three unambiguous deterministic states.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <div className="p-4 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/20 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#2D6A4F]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Eligible</span>
            </div>
            <p className="text-xs text-[#1C2B2A] font-semibold">
              Every mandatory prerequisite is verified as satisfied with positive evidence.
            </p>
            <p className="text-[11px] text-[#52615E]">
              Subject marks, entrance examination rank, and authority accreditations meet or exceed all requirements.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#FEF7EC] border border-[#8A5B16]/20 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#8A5B16]">
              <HelpCircle className="w-4 h-4 shrink-0" />
              <span>Needs Review</span>
            </div>
            <p className="text-xs text-[#1C2B2A] font-semibold">
              One or more required facts are missing, ambiguous, or unconfirmed.
            </p>
            <p className="text-[11px] text-[#52615E]">
              Hydra never guesses missing scores. When a required subject or document is omitted, it requests review.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#FDE8E8] border border-[#A33434]/20 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#A33434]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Ineligible</span>
            </div>
            <p className="text-xs text-[#1C2B2A] font-semibold">
              At least one mandatory prerequisite is definitively violated.
            </p>
            <p className="text-[11px] text-[#52615E]">
              For instance, if a programme requires Mathematics ≥ 80% and the student scored 65%, admission is barred.
            </p>
          </div>
        </div>
      </div>

      {/* Section 2: Admissions Terminology Glossary */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#176B63]" />
            <span>Admissions Terminology Glossary</span>
          </h3>
          <p className="text-xs text-[#52615E] mt-0.5">
            Key concepts used during Indian college admissions and counselling.
          </p>
        </div>

        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-1">
            <h4 className="text-xs font-bold text-[#1C2B2A]">Opening and Closing Ranks</h4>
            <p className="text-xs text-[#52615E] leading-relaxed">
              <strong>Opening Rank:</strong> The highest rank admitted to a given branch and category in a counselling round.<br />
              <strong>Closing Rank:</strong> The final rank admitted. Applicants with ranks higher (numerically lower) than the closing rank are eligible for consideration.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-1">
            <h4 className="text-xs font-bold text-[#1C2B2A]">Tuition-Only Cost Basis</h4>
            <p className="text-xs text-[#52615E] leading-relaxed">
              Hydra's financial comparison calculates <em>tuition fees only</em> for the entire programme duration (e.g. ₹1.8L/year × 4 years = ₹7.2L). It excludes hostel accommodation, mess charges, and one-time registration deposits, which typically add ₹80,000–₹1,20,000 per year.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-1">
            <h4 className="text-xs font-bold text-[#1C2B2A]">Preference Fit Alignment</h4>
            <p className="text-xs text-[#52615E] leading-relaxed">
              A 0–100% score expressing how well a programme matches your preferred states, cities, and target academic disciplines. High preference fit does not override academic prerequisites.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-1">
            <h4 className="text-xs font-bold text-[#1C2B2A]">4 Evidence Dimensions</h4>
            <p className="text-xs text-[#52615E] leading-relaxed">
              Hydra scores programme recommendations across 4 verified dimensions: <strong>Academic Eligibility</strong>, <strong>Entrance Rank Cutoff</strong>, <strong>Tuition Affordability</strong>, and <strong>Preference Alignment</strong>. When all 4 are evaluated, the evidence is labeled "Comprehensive (4/4 dims)".
            </p>
          </div>
        </div>
      </div>

      {/* Section 3: Frequently Asked Questions */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-[#176B63]" />
            <span>Frequently Asked Questions</span>
          </h3>
          <p className="text-xs text-[#52615E] mt-0.5">
            Common questions regarding decision-making and system guarantees.
          </p>
        </div>

        <div className="space-y-2">
          {faqs.map((faq, index) => {
            const isOpen = openFaqIndex === index;
            return (
              <div
                key={index}
                className="rounded-xl border border-[#DCE5DF] overflow-hidden transition-colors"
              >
                <button
                  onClick={() => toggleFaq(index)}
                  className="w-full p-4 text-left bg-[#F6F8F6] hover:bg-[#FFFFFF] flex items-center justify-between text-xs font-bold text-[#1C2B2A] transition-colors"
                >
                  <span>{faq.q}</span>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-[#64736F] shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#64736F] shrink-0" />
                  )}
                </button>

                {isOpen && (
                  <div className="p-4 bg-white border-t border-[#DCE5DF] text-xs text-[#52615E] leading-relaxed">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 4: Ethical & Student-Centric Decision Framework */}
      <div className="bg-[#E1EEE8] border border-[#A3D1C0] rounded-2xl p-6 text-xs text-[#176B63] space-y-2">
        <div className="flex items-center gap-2 font-bold text-sm">
          <Sparkles className="w-4 h-4" />
          <span>Our Commitment to Calm, Honest Academic Guidance</span>
        </div>
        <p className="text-[#1C2B2A] leading-relaxed">
          Hydra was engineered to eliminate panic, false guarantees, and aggressive commercial hype from college admissions. We believe students deserve calm clarity, transparent criteria, and traceable reasoning when making one of the most important decisions of their lives.
        </p>
      </div>
    </div>
  );
};
