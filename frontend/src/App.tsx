import React, { useEffect, useState, useCallback } from 'react';
import {
  connectAlertsStream,
  getDriftStatus,
  getGraphState,
  getHealth,
  getMetrics,
  scoreFlow,
  createScenarioFlowBatch,
} from '@/lib/api';
import type {
  AlertStreamItem,
  DriftStatusResponse,
  GraphStateResponse,
  HealthResponse,
  TelemetryMetrics,
} from '@/lib/types';
import { TelemetryTape } from '@/components/telemetry/TelemetryTape';
import { OperationalSidebar } from '@/components/controls/OperationalSidebar';
import { LiveAlertStream } from '@/components/alerts/LiveAlertStream';
import { NetworkTopologyCanvas } from '@/components/graph/NetworkTopologyCanvas';
import { TreeShapInspector } from '@/components/explainability/TreeShapInspector';
import { EvasionLab } from '@/components/evasion/EvasionLab';
import { DriftObservatory } from '@/components/drift/DriftObservatory';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<TelemetryMetrics | null>(null);
  const [graphState, setGraphState] = useState<GraphStateResponse | null>(null);
  const [drift, setDrift] = useState<DriftStatusResponse | null>(null);
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');

  const [alerts, setAlerts] = useState<AlertStreamItem[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AlertStreamItem | null>(null);

  const [costThreshold, setCostThreshold] = useState<number>(0.2376);
  const [aeCutoff, setAeCutoff] = useState<number>(0.8);
  const [currentEpsilon, setCurrentEpsilon] = useState<number>(0.15);
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const [isDriftLoading, setIsDriftLoading] = useState(false);

  // Fetch initial graph state
  const refreshGraph = useCallback(async () => {
    try {
      setIsGraphLoading(true);
      const data = await getGraphState();
      setGraphState(data);
    } catch (err) {
      console.error('Failed to fetch graph state:', err);
    } finally {
      setIsGraphLoading(false);
    }
  }, []);

  // Fetch initial drift status
  const refreshDrift = useCallback(async () => {
    try {
      setIsDriftLoading(true);
      const data = await getDriftStatus();
      setDrift(data);
    } catch (err) {
      console.error('Failed to fetch drift status:', err);
    } finally {
      setIsDriftLoading(false);
    }
  }, []);

  // Fetch telemetry & health
  const refreshTelemetry = useCallback(async () => {
    try {
      const [hData, mData] = await Promise.all([getHealth(), getMetrics()]);
      setHealth(hData);
      setMetrics(mData);
    } catch (err) {
      console.warn('Telemetry fetch error:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    refreshGraph();
    refreshDrift();
    refreshTelemetry();

    // Initial flow batch to seed alert feed if empty
    const seedInitialFlows = async () => {
      try {
        const initialBatch = createScenarioFlowBatch('BENIGN', 12, costThreshold);
        const scoredItems: AlertStreamItem[] = [];
        for (const f of initialBatch) {
          try {
            const res = await scoreFlow(f);
            scoredItems.push({
              alert_id: `ALT-INIT-${Math.floor(f.timestamp * 1000)}-${f.dst_port}`,
              timestamp: f.timestamp,
              src_ip: f.src_ip,
              dst_ip: f.dst_ip,
              dst_port: f.dst_port,
              attack_type: f.attack_type,
              detection_tier: res.detection_tier,
              supervised_probability: res.supervised_probability,
              reconstruction_loss: res.reconstruction_loss,
              is_attack: res.is_attack,
              explanation: {
                predicted_probability: res.supervised_probability,
                base_value: 0.15,
                analyst_summary: `Initial flow scored by ${res.detection_tier}. Probability: ${(res.supervised_probability * 100).toFixed(1)}%.`,
                top_drivers: [
                  {
                    feature: 'flow_packets_per_sec',
                    value: f.flow_packets_per_sec ?? 45.0,
                    shap_attribution: -0.12,
                    direction: 'DECREASES_RISK',
                  },
                  {
                    feature: 'flow_duration_ms',
                    value: f.flow_duration_ms,
                    shap_attribution: -0.05,
                    direction: 'DECREASES_RISK',
                  },
                ],
              },
            });
          } catch (e) {
            // ignore initial seed error
          }
        }
        if (scoredItems.length > 0) {
          setAlerts(scoredItems);
          setSelectedAlert(scoredItems[0]);
        }
      } catch (err) {
        console.warn('Seed flow batch notice:', err);
      }
    };

    seedInitialFlows();

    // Periodic telemetry refresh
    const timer = setInterval(() => {
      refreshTelemetry();
    }, 5000);

    return () => clearInterval(timer);
  }, [refreshGraph, refreshDrift, refreshTelemetry]);

  // Connect live WebSocket stream
  useEffect(() => {
    const disconnect = connectAlertsStream(
      (newAlert) => {
        setAlerts((prev) => {
          const updated = [...prev, newAlert];
          return updated.length > 250 ? updated.slice(-250) : updated;
        });

        // If attack, auto-select for TreeSHAP triage
        if (newAlert.is_attack) {
          setSelectedAlert(newAlert);
        }
      },
      (status) => setWsStatus(status)
    );

    return () => disconnect();
  }, []);

  const handleBatchScored = (newAlerts: AlertStreamItem[]) => {
    setAlerts((prev) => {
      const combined = [...prev, ...newAlerts];
      return combined.length > 250 ? combined.slice(-250) : combined;
    });

    // Select the highest probability attack if available
    const highestRisk = [...newAlerts].sort(
      (a, b) => b.supervised_probability - a.supervised_probability
    )[0];

    if (highestRisk) {
      setSelectedAlert(highestRisk);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090b0e] text-[#e6edf3]">
      {/* Operational Sidebar */}
      <OperationalSidebar
        costThreshold={costThreshold}
        onCostThresholdChange={setCostThreshold}
        aeCutoff={aeCutoff}
        onAeCutoffChange={setAeCutoff}
        onBatchScored={handleBatchScored}
        onRefreshGraph={refreshGraph}
      />

      {/* Main Terminal Workspace */}
      <main className="flex-1 flex flex-col min-w-0 p-2 gap-2 overflow-y-auto">
        {/* Top 36px Telemetry Tape */}
        <TelemetryTape
          health={health}
          metrics={metrics}
          drift={drift}
          wsStatus={wsStatus}
          costThreshold={costThreshold}
        />

        {/* Asymmetric 60/40 SOC Terminal Grid */}
        <div className="grid grid-cols-10 gap-2">
          {/* Left Column (60%): Live Alert Feed + Temporal Graph Canvas */}
          <div className="col-span-6 flex flex-col gap-2">
            <LiveAlertStream
              alerts={alerts}
              selectedAlertId={selectedAlert?.alert_id ?? null}
              onSelectAlert={setSelectedAlert}
              height={360}
            />

            <NetworkTopologyCanvas
              graphState={graphState}
              onRefresh={refreshGraph}
              isLoading={isGraphLoading}
              height={440}
            />
          </div>

          {/* Right Column (40%): TreeSHAP Inspector + Adversarial Evasion Lab */}
          <div className="col-span-4 flex flex-col gap-2">
            <TreeShapInspector
              explanation={selectedAlert?.explanation ?? null}
              alertId={selectedAlert?.alert_id}
              height={360}
            />

            <EvasionLab
              currentEpsilon={currentEpsilon}
              onEpsilonChange={setCurrentEpsilon}
              height={440}
            />
          </div>
        </div>

        {/* Bottom Operational Drawer: Statistical Drift Observatory */}
        <DriftObservatory
          drift={drift}
          onRefresh={refreshDrift}
          isLoading={isDriftLoading}
        />
      </main>
    </div>
  );
};

export default App;
