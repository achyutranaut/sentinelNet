import React, { useMemo, useState } from 'react';
import { Database, RefreshCw, CheckCircle, Search, ArrowUpDown, Play } from 'lucide-react';
import type { DriftStatusResponse } from '@/lib/types';

interface DriftViewProps {
  drift: DriftStatusResponse | null;
  onRefreshDrift: () => void;
  isLoading: boolean;
}

export const DriftView: React.FC<DriftViewProps> = ({
  drift,
  onRefreshDrift,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'CRITICAL' | 'MODERATE' | 'NOMINAL'>('ALL');
  const [sortField, setSortField] = useState<'psi_score' | 'ks_statistic' | 'feature_name'>('psi_score');
  const [sortAsc, setSortAsc] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainSuccess, setRetrainSuccess] = useState<string | null>(null);

  const isRetrainRecommended = drift?.retraining_recommended ?? false;
  const totalFeatures = drift?.total_features_evaluated ?? 30;
  const numDrifted = drift?.num_drifted_features ?? 0;
  const driftRatio = drift ? (drift.drift_feature_ratio * 100).toFixed(1) : '0.0';

  const featureDetails = useMemo(() => drift?.feature_details || [], [drift?.feature_details]);

  // Filter and sort features
  const filteredFeatures = useMemo(() => {
    return featureDetails
      .filter((feat) => {
        const sev = feat.severity.toUpperCase();
        if (severityFilter !== 'ALL' && sev !== severityFilter) return false;
        if (searchTerm.trim()) {
          return feat.feature_name.toLowerCase().includes(searchTerm.toLowerCase().trim());
        }
        return true;
      })
      .sort((a, b) => {
        let valA: any = a[sortField];
        let valB: any = b[sortField];
        if (typeof valA === 'string') {
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return sortAsc ? valA - valB : valB - valA;
      });
  }, [featureDetails, searchTerm, severityFilter, sortField, sortAsc]);

  const handleSort = (field: 'psi_score' | 'ks_statistic' | 'feature_name') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleTriggerRetraining = () => {
    setIsRetraining(true);
    setRetrainSuccess(null);
    setTimeout(() => {
      setIsRetraining(false);
      setRetrainSuccess('Continuous Training (CT) Pipeline job queued successfully.');
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Header & Status */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#0d1117] border border-[#1f2937] p-5 rounded-lg shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2 font-heading">
            <Database className="w-5 h-5 text-sky-400" />
            <span>Statistical Drift Observatory & MLOps Governance</span>
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Continuous distribution stability tracking using Kolmogorov-Smirnov test and Population Stability Index (PSI)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onRefreshDrift}
            disabled={isLoading}
            className="flex items-center gap-2 px-3.5 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 font-sans text-xs cursor-pointer transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Recalculate Drift</span>
          </button>

          <button
            type="button"
            onClick={handleTriggerRetraining}
            disabled={isRetraining}
            className={`flex items-center gap-2 px-4 py-2 rounded font-sans text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${
              isRetrainRecommended
                ? 'bg-[#f85149] hover:bg-red-600 text-slate-950 shadow-[0_0_12px_rgba(248,81,73,0.3)]'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isRetraining ? 'animate-spin' : ''}`} />
            <span>{isRetraining ? 'Triggering Pipeline...' : 'Trigger Retraining'}</span>
          </button>
        </div>
      </div>

      {retrainSuccess && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded text-xs text-emerald-300 flex items-center gap-2 font-sans">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <span>{retrainSuccess}</span>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Features Evaluated
          </span>
          <span className="text-3xl font-extrabold font-mono text-slate-100 mt-2 block">
            {totalFeatures}
          </span>
          <span className="text-xs text-slate-400 mt-1 block">Full NetFlow feature vector</span>
        </div>

        <div className="stat-card">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Drifted Features
          </span>
          <span className={`text-3xl font-extrabold font-mono mt-2 block ${
            numDrifted > 0 ? 'text-[#f85149]' : 'text-[#3fb950]'
          }`}>
            {numDrifted}
          </span>
          <span className="text-xs text-slate-400 mt-1 block">PSI &gt; 0.25 threshold</span>
        </div>

        <div className="stat-card">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Drift Feature Ratio
          </span>
          <span className={`text-3xl font-extrabold font-mono mt-2 block ${
            parseFloat(driftRatio) > 10 ? 'text-[#f85149]' : 'text-[#3fb950]'
          }`}>
            {driftRatio}%
          </span>
          <span className="text-xs text-slate-400 mt-1 block">Tolerable threshold: 10%</span>
        </div>

        <div className="stat-card">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Retraining Recommendation
          </span>
          <div className="mt-2 flex items-center gap-2">
            <span className={`text-lg font-bold font-sans ${
              isRetrainRecommended ? 'text-[#f85149]' : 'text-[#3fb950]'
            }`}>
              {isRetrainRecommended ? 'TRIGGER CT PIPELINE' : 'MODEL STABLE'}
            </span>
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            {isRetrainRecommended ? 'Significant covariate shift detected' : 'In-distribution operation'}
          </span>
        </div>
      </div>

      {/* Feature Stability Matrix (Re-engineered: Readable 13px Cards with Intentional Color) */}
      <div className="soc-card p-5 space-y-3">
        <div className="flex justify-between items-center pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-200 font-sans">
              Feature Distribution Stability Matrix (30 Features)
            </h3>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Population Stability Index (PSI) across active ingestion window vs training baseline
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-sans">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span>Critical (PSI &gt; 0.25)</span>
            </span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>Moderate (PSI &gt; 0.10)</span>
            </span>
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Stable (PSI ≤ 0.10)</span>
            </span>
          </div>
        </div>

        {/* Readable Card Grid - grid-cols-2 md:grid-cols-4 lg:grid-cols-6 */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 pt-2">
          {featureDetails.slice(0, 30).map((feat) => {
            const isCrit = feat.severity.toLowerCase() === 'critical';
            const isWarn = feat.severity.toLowerCase() === 'moderate';

            const borderCol = isCrit
              ? 'border-red-800/50 bg-red-950/30'
              : isWarn
              ? 'border-amber-800/50 bg-amber-950/30'
              : 'border-slate-800 bg-slate-900/60';

            const dotCol = isCrit ? '#f85149' : isWarn ? '#d29922' : '#3fb950';

            return (
              <div
                key={feat.feature_name}
                className={`p-3.5 rounded-lg border ${borderCol} flex flex-col justify-between transition-all hover:border-slate-600 shadow-xs`}
                title={`${feat.feature_name} | PSI: ${feat.psi_score.toFixed(4)} | KS: ${feat.ks_statistic.toFixed(4)}`}
              >
                <div className="flex items-start justify-between gap-1.5">
                  <span className="text-xs font-semibold text-slate-200 font-sans truncate" title={feat.feature_name}>
                    {feat.feature_name}
                  </span>
                  <span className="w-2.5 h-2.5 rounded-full mt-0.5 shrink-0" style={{ backgroundColor: dotCol }} />
                </div>
                <div className="mt-2.5 flex items-baseline justify-between border-t border-slate-800/60 pt-1.5">
                  <span className="text-[11px] text-slate-400 uppercase font-sans font-semibold">PSI</span>
                  <span className="font-mono text-sm font-bold tabular-nums text-slate-100">
                    {feat.psi_score.toFixed(3)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real Readable, Sortable & Filterable Drifted Features Table (100% Width & Proportional Columns) */}
      <div className="soc-card p-5 space-y-4 w-full">
        {/* Table Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-200 font-sans">
              Feature Drift Statistical Diagnostics
            </h3>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Ranked Kolmogorov-Smirnov and PSI divergence scores
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Filter feature..."
                className="bg-slate-900 border border-slate-700 rounded px-2.5 pl-8 py-1.5 text-xs text-slate-200 font-sans focus:border-sky-400 outline-none w-48 transition-colors"
              />
            </div>

            {/* Severity Filter Chips */}
            <div className="flex items-center gap-1">
              {(['ALL', 'CRITICAL', 'MODERATE', 'NOMINAL'] as const).map((sev) => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setSeverityFilter(sev)}
                  className={`px-2.5 py-1 rounded text-xs font-sans font-semibold transition-colors cursor-pointer border ${
                    severityFilter === sev
                      ? 'bg-sky-500/20 text-sky-400 border-sky-500/60'
                      : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-slate-500 hover:text-slate-200'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 100% Full-Width Proportional Distribution Table */}
        <div className="w-full overflow-x-auto border border-slate-800 rounded-lg shadow-xs">
          <table className="w-full text-left font-sans text-xs border-collapse table-fixed">
            <colgroup>
              <col className="w-[26%]" />
              <col className="w-[14%]" />
              <col className="w-[14%]" />
              <col className="w-[14%]" />
              <col className="w-[16%]" />
              <col className="w-[16%]" />
            </colgroup>
            <thead className="bg-[#161b22] text-slate-300 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th
                  onClick={() => handleSort('feature_name')}
                  className="py-3 px-4 cursor-pointer hover:text-sky-400 transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Feature Name</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('psi_score')}
                  className="py-3 px-4 cursor-pointer hover:text-sky-400 transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>PSI Score</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('ks_statistic')}
                  className="py-3 px-4 cursor-pointer hover:text-sky-400 transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>KS Statistic</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-4">KS p-value</th>
                <th className="py-3 px-4">Drift Severity</th>
                <th className="py-3 px-4">Distribution Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs tabular-nums">
              {filteredFeatures.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No features match current search and filter criteria.
                  </td>
                </tr>
              ) : (
                filteredFeatures.map((feat) => {
                  const isCrit = feat.severity.toLowerCase() === 'critical';
                  const isWarn = feat.severity.toLowerCase() === 'moderate';

                  return (
                    <tr key={feat.feature_name} className="hover:bg-slate-900/60 transition-colors">
                      <td className="py-3 px-4 font-sans font-medium text-slate-200 truncate" title={feat.feature_name}>
                        {feat.feature_name}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-100">
                        {feat.psi_score.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {feat.ks_statistic.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {feat.ks_pvalue.toExponential(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={
                            isCrit
                              ? 'badge-critical'
                              : isWarn
                              ? 'badge-warning'
                              : 'badge-secure'
                          }
                        >
                          {feat.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans text-xs">
                        {isCrit ? (
                          <span className="text-red-400 font-semibold flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                            <span>Trigger CT Pipeline</span>
                          </span>
                        ) : isWarn ? (
                          <span className="text-amber-400">Continuous Monitor</span>
                        ) : (
                          <span className="text-emerald-400">Baseline Pass</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
