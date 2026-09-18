import { ArrowRight, Terminal, Zap, Eye } from 'lucide-react';

interface HeroLandingProps {
  onLaunchConsole: () => void;
  onExploreTab: (tab: string) => void;
}

export const HeroLanding: React.FC<HeroLandingProps> = ({
  onLaunchConsole,
  onExploreTab,
}) => {
  return (
    <section className="relative overflow-hidden bg-[#060c14] border-b border-[#1b2738] px-6 py-12 md:py-16 text-[#e6edf3] select-none">
      {/* Background Cyber Grid & Glows */}
      <div
        className="absolute inset-0 pointer-events-none opacity-25"
        style={{
          backgroundImage: `linear-gradient(to right, #162b47 1px, transparent 1px), linear-gradient(to bottom, #162b47 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, black 20%, transparent 85%)',
        }}
      />
      <div
        className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full pointer-events-none opacity-20 blur-3xl"
        style={{ background: 'radial-gradient(circle, #58a6ff 0%, transparent 70%)' }}
      />
      <div
        className="absolute bottom-10 right-1/4 w-80 h-80 rounded-full pointer-events-none opacity-15 blur-3xl"
        style={{ background: 'radial-gradient(circle, #f85149 0%, transparent 70%)' }}
      />

      <div className="relative max-w-6xl mx-auto flex flex-col items-start">
        {/* Terminal Subheader Tag */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-[2px] bg-[#162b47]/60 border border-[#23426e] font-mono text-[9px] text-[#58a6ff] tracking-[0.2em] uppercase mb-5">
          <Terminal className="w-3 h-3 text-[#58a6ff]" />
          <span>SENTINELNET // AIR-GAPPED SOC TELEMETRY MATRIX</span>
        </div>

        {/* Oversized Headline */}
        <h1 className="font-heading font-black text-3xl sm:text-5xl lg:text-6xl tracking-tight leading-[1.05] max-w-4xl text-[#f0f6fc] mb-5">
          Stop zero-day <span className="text-[#f85149] underline decoration-[#f85149]/40 underline-offset-4">intrusions</span> before lateral pivoting spreads.
        </h1>

        {/* One-Line Thesis */}
        <p className="font-mono text-xs sm:text-sm text-[#8b949e] max-w-2xl leading-relaxed mb-8">
          SentinelNet pairs sub-millisecond supervised signatures with unsupervised autoencoder reconstruction,
          temporal graph interaction tracking, and exact TreeSHAP feature attributions into an air-gapped,
          production-grade defense command system.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center gap-3.5 mb-12">
          <button
            onClick={onLaunchConsole}
            className="flex items-center gap-2 px-6 py-3 rounded-[2px] bg-[#58a6ff] hover:bg-[#3b82f6] text-[#090b0e] font-heading font-bold text-xs tracking-wider uppercase transition-all duration-150 cursor-pointer shadow-[0_0_16px_rgba(88,166,255,0.35)]"
          >
            <span>LAUNCH SOC CONSOLE</span>
            <ArrowRight className="w-4 h-4 stroke-[2.5]" />
          </button>

          <button
            onClick={() => onExploreTab('graph')}
            className="flex items-center gap-2 px-5 py-3 rounded-[2px] bg-[#0a1422] hover:bg-[#162b47] text-[#58a6ff] border border-[#23426e] font-mono text-xs tracking-wider uppercase transition-all duration-150 cursor-pointer"
          >
            <Eye className="w-4 h-4 text-[#58a6ff]" />
            <span>TOPOLOGY GRAPH</span>
          </button>

          <button
            onClick={() => onExploreTab('evasion')}
            className="flex items-center gap-2 px-5 py-3 rounded-[2px] bg-[#0a1422] hover:bg-[#162b47] text-[#bc8cff] border border-[#3b2a59] font-mono text-xs tracking-wider uppercase transition-all duration-150 cursor-pointer"
          >
            <Zap className="w-4 h-4 text-[#bc8cff]" />
            <span>EVASION LAB</span>
          </button>
        </div>

        {/* SOC Benchmark Stats Strip */}
        <div className="w-full grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8 border-t border-[#162b47] font-mono">
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className="font-heading text-2xl sm:text-3xl font-black text-[#3fb950]">
                &lt;1.5
              </span>
              <span className="text-xs text-[#8b949e]">ms</span>
            </div>
            <span className="text-[8.5px] text-[#527194] tracking-widest uppercase font-semibold mt-1">
              INFERENCE SLA PER FLOW
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className="font-heading text-2xl sm:text-3xl font-black text-[#58a6ff]">
                5
              </span>
              <span className="text-xs text-[#8b949e]">TIERS</span>
            </div>
            <span className="text-[8.5px] text-[#527194] tracking-widest uppercase font-semibold mt-1">
              DEFENSE IN DEPTH MATRIX
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className="font-heading text-2xl sm:text-3xl font-black text-[#d29922]">
                $50k
              </span>
              <span className="text-xs text-[#8b949e]">FN</span>
            </div>
            <span className="text-[8.5px] text-[#527194] tracking-widest uppercase font-semibold mt-1">
              COST-CALIBRATED MATRIX
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className="font-heading text-2xl sm:text-3xl font-black text-[#bc8cff]">
                100%
              </span>
              <span className="text-xs text-[#8b949e]">SHAP</span>
            </div>
            <span className="text-[8.5px] text-[#527194] tracking-widest uppercase font-semibold mt-1">
              AUDIT-READY EXPLAINABILITY
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
