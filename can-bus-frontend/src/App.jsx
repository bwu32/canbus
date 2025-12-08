import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Shield, Zap, Activity, CheckCircle, XCircle, AlertTriangle, Lock, ShieldCheck, Timer, Eye } from 'lucide-react';
import './App.css';

function App() {
  const [connected, setConnected] = useState(false);
  const [simState, setSimState] = useState(null);
  const [latencyData, setLatencyData] = useState([]);
  const [attackStats, setAttackStats] = useState({});
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8765');

    ws.current.onopen = () => {
      console.log('Connected to CAN simulation');
      setConnected(true);
      ws.current.send(JSON.stringify({ command: 'get_state' }));
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.simulation) {
        setSimState(data);

        if (data.latency_data && data.latency_data.length > 0) {
          setLatencyData(prev => {
            const newData = [...prev];
            data.latency_data.forEach(point => {
              newData.push({
                time: new Date(point.time * 1000).toLocaleTimeString(),
                latency: point.latency,
                controller: point.controller
              });
            });
            return newData.slice(-100);
          });
        }

        if (data.attacks && data.attacks.statistics) {
          setAttackStats(data.attacks.statistics);
        }
      }
    };

    ws.current.onclose = () => {
      console.log('Disconnected from CAN simulation');
      setConnected(false);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const toggleSecurity = (measure) => {
    if (!ws.current || !simState) return;

    const currentState = simState.simulation.security_measures[measure];
    ws.current.send(JSON.stringify({
      command: 'toggle_security',
      measure: measure,
      enabled: !currentState
    }));
  };

  const startAttack = (attackName) => {
    if (!ws.current) return;

    ws.current.send(JSON.stringify({
      command: 'start_attack',
      attack: attackName
    }));
  };

  const stopAttack = (attackName) => {
    if (!ws.current) return;

    ws.current.send(JSON.stringify({
      command: 'stop_attack',
      attack: attackName
    }));
  };

  const getSecurityIcon = (measure) => {
    switch (measure) {
      case 'encryption': return <Lock style={{ width: '20px', height: '20px' }} />;
      case 'authentication': return <ShieldCheck style={{ width: '20px', height: '20px' }} />;
      case 'rate_limiting': return <Timer style={{ width: '20px', height: '20px' }} />;
      case 'ids': return <Eye style={{ width: '20px', height: '20px' }} />;
      default: return <Shield style={{ width: '20px', height: '20px' }} />;
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return '#4ade80';
      case 'warning': return '#facc15';
      case 'compromised': return '#f87171';
      default: return '#9ca3af';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return <CheckCircle style={{ width: '16px', height: '16px' }} />;
      case 'warning': return <AlertTriangle style={{ width: '16px', height: '16px' }} />;
      case 'compromised': return <XCircle style={{ width: '16px', height: '16px' }} />;
      default: return <Activity style={{ width: '16px', height: '16px' }} />;
    }
  };

  if (!connected) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#020617',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <Activity style={{ width: '64px', height: '64px', margin: '0 auto 16px', color: '#3b82f6' }} className="spin" />
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>Connecting to CAN Simulation...</h2>
          <p style={{ color: '#9ca3af' }}>Make sure server.py is running on port 8765</p>
        </div>
      </div>
    );
  }

  if (!simState) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#020617',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Activity style={{ width: '32px', height: '32px', color: '#3b82f6' }} className="spin" />
      </div>
    );
  }

  const securityMeasures = simState.simulation.security_measures;
  const securityStats = simState.simulation.security_stats;
  const controllers = simState.simulation.controllers;
  const attacks = simState.attacks;
  const totalOverhead = simState.total_overhead || 0;
  const warnings = simState.warnings || [];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#020617',
      color: 'white',
      padding: '24px'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: 'white' }}>
          CAN Bus Security Simulation
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="pulse-dot"></div>
          <span style={{ fontSize: '14px', color: '#9ca3af' }}>Connected</span>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          {warnings.map((warning, idx) => (
            <div key={idx} style={{
              padding: '16px',
              borderRadius: '8px',
              border: warning.level === 'critical' ? '2px solid #ef4444' : '2px solid #eab308',
              backgroundColor: warning.level === 'critical' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(234, 179, 8, 0.1)',
              marginBottom: '8px'
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <AlertTriangle style={{
                  width: '20px',
                  height: '20px',
                  color: warning.level === 'critical' ? '#f87171' : '#facc15'
                }} />
                <div>
                  <h3 style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                    {warning.level === 'critical' ? 'CRITICAL LATENCY WARNING' : 'High Latency Warning'}
                  </h3>
                  <p style={{ fontSize: '12px', color: '#d1d5db' }}>{warning.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 2fr',
        gap: '24px'
      }}>
        {/* Left Column - Security Measures */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Security Measures */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Shield style={{ width: '20px', height: '20px', color: '#3b82f6' }} />
              <h2 style={{ fontSize: '18px', fontWeight: 'bold' }}>Security Measures</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {Object.entries(securityMeasures).map(([measure, enabled]) => (
                <button
                  key={measure}
                  onClick={() => toggleSecurity(measure)}
                  className={`security-button ${enabled ? 'enabled' : ''}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ color: enabled ? '#3b82f6' : '#6b7280' }}>
                        {getSecurityIcon(measure)}
                      </div>
                      <span style={{ fontWeight: '600', fontSize: '14px', textTransform: 'capitalize' }}>
                        {measure.replace('_', ' ')}
                      </span>
                    </div>
                    <div className={`badge ${enabled ? 'badge-enabled' : 'badge-disabled'}`}>
                      {enabled ? 'ON' : 'OFF'}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Total Overhead */}
            <div className="stat-box" style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                Total Security Overhead
              </div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#3b82f6' }}>
                {totalOverhead.toFixed(2)} ms
              </div>
            </div>
          </div>

          {/* System Health */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Activity style={{ width: '20px', height: '20px', color: '#06b6d4' }} />
              <h2 style={{ fontSize: '18px', fontWeight: 'bold' }}>System Health</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {controllers.map(ctrl => (
                <div key={ctrl.name} className="health-card">
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '4px'
                  }}>
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>{ctrl.name}</span>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: getHealthColor(ctrl.health)
                    }}>
                      {getHealthIcon(ctrl.health)}
                      <span style={{ fontSize: '12px', textTransform: 'uppercase', fontWeight: 'bold' }}>
                        {ctrl.health}
                      </span>
                    </div>
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '8px',
                    fontSize: '12px'
                  }}>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Latency</div>
                      <div style={{
                        fontWeight: 'bold',
                        color: ctrl.avg_latency > 20 ? '#facc15' : '#4ade80'
                      }}>
                        {ctrl.avg_latency.toFixed(2)} ms
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Attacks</div>
                      <div style={{
                        fontWeight: 'bold',
                        color: ctrl.recent_attacks > 0 ? '#f87171' : '#4ade80'
                      }}>
                        {ctrl.recent_attacks}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Security Statistics */}
          <div className="card">
            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
              Security Statistics
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px',
              fontSize: '12px'
            }}>
              <div className="stat-card stat-yellow">
                <div>Detected</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {securityStats.attacks_detected || 0}
                </div>
              </div>
              <div className="stat-card stat-green">
                <div>Blocked</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {securityStats.attacks_blocked || 0}
                </div>
              </div>
              <div className="stat-card stat-red">
                <div>Successful</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {securityStats.attacks_successful || 0}
                </div>
              </div>
              <div className="stat-card stat-blue">
                <div>Encrypted</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {securityStats.messages_encrypted || 0}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle Column - Attacks */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Compromised Nodes - MOVED TO TOP */}
          <div className="card">
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#f87171', marginBottom: '12px' }}>
              ⚠️ Compromised Nodes
            </div>
            {attacks.compromised_nodes.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {attacks.compromised_nodes.map(node => (
                  <div key={node} className="compromised-node">
                    {node}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '14px', color: '#9ca3af' }}>No compromised nodes</div>
            )}
          </div>

          {/* Attack Controls */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Zap style={{ width: '20px', height: '20px', color: '#f87171' }} />
              <h2 style={{ fontSize: '18px', fontWeight: 'bold' }}>Attack Simulation</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {['bus_flooding', 'spoofing', 'replay'].map(attackName => {
                const isActive = attacks.active_attacks.includes(attackName);
                const stats = attackStats[attackName] || {};

                return (
                  <div key={attackName} className="attack-card">
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '10px'
                    }}>
                      <span style={{ fontWeight: 'bold', fontSize: '14px', textTransform: 'capitalize' }}>
                        {attackName.replace('_', ' ')}
                      </span>
                      <button
                        onClick={() => isActive ? stopAttack(attackName) : startAttack(attackName)}
                        className={`attack-button ${isActive ? 'stop' : 'start'}`}
                      >
                        {isActive ? 'STOP' : 'START'}
                      </button>
                    </div>

                    {isActive && (
                      <div style={{
                        fontSize: '12px',
                        color: '#f87171',
                        fontWeight: 'bold',
                        marginBottom: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <div className="pulse-dot-small"></div>
                        ACTIVE
                      </div>
                    )}

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                      fontSize: '12px'
                    }}>
                      <div className="stat-box-small">
                        <div style={{ color: '#9ca3af' }}>Attempts</div>
                        <div style={{ fontWeight: 'bold', color: 'white' }}>{stats.attempts || 0}</div>
                      </div>
                      <div className="stat-box-small">
                        <div style={{ color: '#9ca3af' }}>Success</div>
                        <div style={{ fontWeight: 'bold', color: '#f87171' }}>{stats.successful || 0}</div>
                      </div>
                      <div className="stat-box-small">
                        <div style={{ color: '#9ca3af' }}>Blocked</div>
                        <div style={{ fontWeight: 'bold', color: '#4ade80' }}>{stats.blocked || 0}</div>
                      </div>
                      <div className="stat-box-small">
                        <div style={{ color: '#9ca3af' }}>Detected</div>
                        <div style={{ fontWeight: 'bold', color: '#facc15' }}>{stats.detected || 0}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column - Graph */}
        <div className="card">
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>
            Real-Time Latency Analysis
          </h2>
            
          <ResponsiveContainer width="100%" height={620}>
            <LineChart data={latencyData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="time"
                stroke="#94A3B8"
                tick={{ fontSize: 11 }}
              />
              <YAxis
                stroke="#94A3B8"
                domain={[0, 120]}
                ticks={[0, 10, 20, 50, 100, 120]}
                width={40}
                label={{
                  value: 'Latency (ms)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fill: '#94A3B8', fontSize: 12 }
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid #475569',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#94A3B8' }}
              />
              <Legend
                verticalAlign="bottom"
                align="left"
                wrapperStyle={{
                  display: "flex",
                  flexDirection: "row",
                  overflowX: "auto",
                  width: "80%",
                  padding: "4px 0",
                  fontSize: "16px"        // 👈 SHRINK LEGEND TEXT
                }}
              />

              <Line
                type="monotone"
                dataKey={() => 10}
                stroke="#EF4444"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Critical <10ms (Brakes, Airbags)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey={() => 20}
                stroke="#F59E0B"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Safety <20ms (Steering, ABS)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey={() => 100}
                stroke="#10B981"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Normal <100ms (Telemetry)"
                dot={false}
              />

              <Line
                type="monotone"
                dataKey="latency"
                stroke="#3B82F6"
                strokeWidth={3}
                name="Measured Latency"
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default App;