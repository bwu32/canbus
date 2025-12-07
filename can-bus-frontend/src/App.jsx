import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Shield, ShieldAlert, Activity, Zap, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import './App.css';

function App() {
  const [connected, setConnected] = useState(false);
  const [simState, setSimState] = useState(null);
  const [latencyData, setLatencyData] = useState([]);
  const [attackStats, setAttackStats] = useState({});
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket server
    ws.current = new WebSocket('ws://localhost:8765');

    ws.current.onopen = () => {
      console.log('Connected to CAN simulation');
      setConnected(true);
      // Request initial state
      ws.current.send(JSON.stringify({ command: 'get_state' }));
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.simulation) {
        setSimState(data);
        
        // Update latency data for graph
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
            // Keep last 50 points
            return newData.slice(-50);
          });
        }
        
        // Update attack stats
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

  const getHealthColor = (health) => {
    switch(health) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'compromised': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthIcon = (health) => {
    switch(health) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'compromised': return <XCircle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  if (!connected) {
    return (
      <div className="App min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 animate-spin mx-auto mb-4 text-blue-500" />
          <h2 className="text-2xl font-bold mb-2">Connecting to CAN Simulation...</h2>
          <p className="text-gray-400">Make sure server.py is running on port 8765</p>
        </div>
      </div>
    );
  }

  if (!simState) {
    return (
      <div className="App min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <Activity className="w-8 h-8 animate-spin text-blue-500" />
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
    <div className="App min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
          <Shield className="w-10 h-10 text-blue-500" />
          CAN Bus Security Simulation
        </h1>
        <p className="text-gray-400">Real-time automotive network security analysis & attack simulation</p>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-6 space-y-2">
          {warnings.map((warning, idx) => (
            <div key={idx} className={`p-4 rounded-lg border-2 ${
              warning.level === 'critical' ? 'bg-red-900/20 border-red-500' : 'bg-yellow-900/20 border-yellow-500'
            }`}>
              <div className="flex items-start gap-3">
                <AlertTriangle className={`w-6 h-6 ${warning.level === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                <div>
                  <h3 className="font-bold text-lg mb-1">
                    {warning.level === 'critical' ? '🚨 CRITICAL LATENCY WARNING' : '⚠️ High Latency Warning'}
                  </h3>
                  <p className="text-sm">{warning.message}</p>
                  <p className="text-xs text-gray-400 mt-1">Affected Systems: {warning.system}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Security Measures Panel */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Shield className="w-6 h-6 text-green-500" />
            Security Measures
          </h2>
          
          <div className="space-y-3">
            {Object.entries(securityMeasures).map(([measure, enabled]) => (
              <div key={measure} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${enabled ? 'bg-green-500' : 'bg-gray-500'}`} />
                  <span className="font-medium capitalize">{measure.replace('_', ' ')}</span>
                </div>
                <button
                  onClick={() => toggleSecurity(measure)}
                  className={`px-4 py-1 rounded text-sm font-medium transition-colors ${
                    enabled 
                      ? 'bg-green-600 hover:bg-green-700' 
                      : 'bg-gray-600 hover:bg-gray-500'
                  }`}
                >
                  {enabled ? 'ON' : 'OFF'}
                </button>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-gray-700 rounded">
            <h3 className="font-bold mb-2 text-sm text-gray-300">Total Security Overhead</h3>
            <p className="text-3xl font-bold text-blue-400">{totalOverhead.toFixed(2)} ms</p>
            <div className="mt-2 text-xs text-gray-400 space-y-1">
              <div>Encryption: {(simState.security_overhead?.encryption || 0).toFixed(3)} ms</div>
              <div>Authentication: {(simState.security_overhead?.authentication || 0).toFixed(3)} ms</div>
              <div>Rate Limiting: {(simState.security_overhead?.rate_limiting || 0).toFixed(3)} ms</div>
              <div>IDS: {(simState.security_overhead?.ids || 0).toFixed(3)} ms</div>
            </div>
          </div>
        </div>

        {/* Attack Control Panel */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Zap className="w-6 h-6 text-red-500" />
            Attack Simulation
          </h2>
          
          <div className="space-y-3">
            {['bus_flooding', 'spoofing', 'replay'].map(attackName => {
              const isActive = attacks.active_attacks.includes(attackName);
              const stats = attackStats[attackName] || {};
              
              return (
                <div key={attackName} className="p-4 bg-gray-700 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold capitalize">{attackName.replace('_', ' ')}</span>
                    <button
                      onClick={() => isActive ? stopAttack(attackName) : startAttack(attackName)}
                      className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-red-600 hover:bg-red-700' 
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      {isActive ? 'STOP' : 'START'}
                    </button>
                  </div>
                  
                  {isActive && <div className="text-xs text-red-400 mb-2">🚨 ACTIVE ATTACK</div>}
                  
                  <div className="text-xs text-gray-400 space-y-1">
                    <div>Attempts: {stats.attempts || 0}</div>
                    <div className="flex justify-between">
                      <span>Success: {stats.successful || 0}</span>
                      <span>Blocked: {stats.blocked || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-red-400">Success Rate: {(stats.success_rate || 0).toFixed(1)}%</span>
                      <span className="text-green-400">Detection: {(stats.detection_rate || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded text-xs">
            <p className="text-red-400 font-bold mb-1">⚠️ Compromised Nodes:</p>
            {attacks.compromised_nodes.length > 0 ? (
              <ul className="list-disc list-inside text-gray-300">
                {attacks.compromised_nodes.map(node => (
                  <li key={node}>{node}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400">None</p>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-500" />
            System Health
          </h2>
          
          <div className="space-y-3">
            {controllers.map(ctrl => (
              <div key={ctrl.name} className="p-4 bg-gray-700 rounded">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold">{ctrl.name}</span>
                  <div className={`flex items-center gap-2 ${getHealthColor(ctrl.health)}`}>
                    {getHealthIcon(ctrl.health)}
                    <span className="text-sm uppercase font-medium">{ctrl.health}</span>
                  </div>
                </div>
                
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Avg Latency:</span>
                    <span className={ctrl.avg_latency > 20 ? 'text-yellow-400' : 'text-green-400'}>
                      {ctrl.avg_latency.toFixed(2)} ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Security Overhead:</span>
                    <span>{ctrl.avg_security_overhead.toFixed(2)} ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Attacks:</span>
                    <span className={ctrl.recent_attacks > 0 ? 'text-red-400' : 'text-gray-400'}>
                      {ctrl.recent_attacks}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Security Statistics */}
          <div className="mt-4 p-4 bg-gray-700 rounded">
            <h3 className="font-bold mb-3 text-sm">Security Statistics</h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-gray-800 p-2 rounded">
                <div className="text-gray-400">Attacks Detected</div>
                <div className="text-xl font-bold text-yellow-400">{securityStats.attacks_detected || 0}</div>
              </div>
              <div className="bg-gray-800 p-2 rounded">
                <div className="text-gray-400">Attacks Blocked</div>
                <div className="text-xl font-bold text-green-400">{securityStats.attacks_blocked || 0}</div>
              </div>
              <div className="bg-gray-800 p-2 rounded">
                <div className="text-gray-400">Successful Attacks</div>
                <div className="text-xl font-bold text-red-400">{securityStats.attacks_successful || 0}</div>
              </div>
              <div className="bg-gray-800 p-2 rounded">
                <div className="text-gray-400">Messages Encrypted</div>
                <div className="text-xl font-bold text-blue-400">{securityStats.messages_encrypted || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Latency Graph */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-2xl font-bold mb-4">Real-Time Latency Analysis</h2>
        
        <div className="mb-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded" />
            <span>Critical Threshold: &lt;10ms (Brakes, Airbags)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded" />
            <span>Safety Threshold: &lt;20ms (Steering, ABS)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded" />
            <span>Normal Threshold: &lt;100ms (Telemetry)</span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={latencyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#9CA3AF"
              tick={{fontSize: 12}}
            />
            <YAxis 
              stroke="#9CA3AF"
              label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
              labelStyle={{ color: '#9CA3AF' }}
            />
            <Legend />
            
            {/* Threshold lines */}
            <Line type="monotone" dataKey={() => 10} stroke="#EF4444" strokeDasharray="5 5" name="Critical Threshold" dot={false} />
            <Line type="monotone" dataKey={() => 20} stroke="#F59E0B" strokeDasharray="5 5" name="Safety Threshold" dot={false} />
            <Line type="monotone" dataKey={() => 100} stroke="#10B981" strokeDasharray="5 5" name="Normal Threshold" dot={false} />
            
            {/* Actual latency */}
            <Line type="monotone" dataKey="latency" stroke="#3B82F6" strokeWidth={2} name="Measured Latency" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Events */}
      {attacks.recent_events && attacks.recent_events.length > 0 && (
        <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4">Recent Attack Events</h2>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {attacks.recent_events.slice().reverse().map((event, idx) => (
              <div key={idx} className="p-3 bg-gray-700 rounded text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-red-400">{event.attack}</span>
                  <span className="text-gray-400 text-xs">
                    {new Date(event.time * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-400 text-xs mt-1">
                  Action: {event.action} | Targets: {event.targets?.join(', ') || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;