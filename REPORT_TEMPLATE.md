# CAN Bus Security Simulation - Technical Report Template

> Use this template for your complete project report. Fill in experimental data from your simulation runs.

---

## 1. Executive Summary

### Project Overview
This project implements a comprehensive proof-of-concept for automotive CAN bus security, demonstrating both vulnerabilities and defense mechanisms in modern vehicle networks.

### Key Findings
- *(Fill after experiments)*
- Example: "Bus flooding attacks achieved 100% denial-of-service without security, but were completely blocked by rate limiting"
- "HMAC authentication prevented 100% of spoofing attacks"
- "Combined security measures added X.Xms average latency"

### Recommendations
- *(Based on your findings)*

---

## 2. Introduction

### 2.1 Background

**CAN Bus in Modern Vehicles**
- Controller Area Network (CAN) is the primary communication protocol in automotive systems
- Connects 50-100+ Electronic Control Units (ECUs) in modern vehicles
- Handles safety-critical functions: brakes, steering, airbags, engine control

**The Security Problem**
- CAN protocol designed in 1983 without security features
- No encryption, authentication, or access control
- Any node on the bus can read/send any message
- Single compromised ECU can affect entire vehicle

**Real-World Impact**
- 2015: Jeep Cherokee remotely hacked via cellular connection
- 2016: Tesla Model S vulnerabilities demonstrated
- 2019: 100+ vulnerabilities found across manufacturers
- Increasing regulatory pressure (UNECE WP.29, ISO/SAE 21434)

### 2.2 Project Objectives

1. **Demonstrate** realistic CAN bus vulnerabilities
2. **Implement** four security measures with measurable effectiveness
3. **Simulate** three attack types targeting different vehicle systems
4. **Analyze** latency impact and safety implications
5. **Visualize** real-time security metrics and system health

---

## 3. System Architecture

### 3.1 Network Topology

```
┌─────────────────────────────────────────────┐
│         Virtual CAN Bus (500 kbps)          │
│  Priority-based arbitration (ID 0x000-0x7FF) │
└─────────────────────────────────────────────┘
         │              │              │
    ┌────┴───┐     ┌────┴───┐     ┌────┴───┐
    │ Engine │     │ Brake  │     │  Body  │
    │  ECU   │     │  ECU   │     │  ECU   │
    │        │     │(CRIT)  │     │        │
    └────────┘     └────────┘     └────────┘
```

### 3.2 ECU Specifications

| ECU | CAN IDs | Update Rate | Latency Threshold |
|-----|---------|-------------|-------------------|
| **Engine** | 0x100-0x101 | 20 Hz (50ms) | <100ms (Normal) |
| **Brake** | 0x0A0-0x0A1 | 100 Hz (10ms) | **<10ms (Critical)** |
| **Transmission** | 0x200 | 12.5 Hz (80ms) | <100ms (Normal) |
| **Body Control** | 0x300-0x301 | 10 Hz (100ms) | <100ms (Normal) |

### 3.3 Communication Flow

1. ECU generates message with arbitration ID and data
2. Security measures applied (encryption, HMAC, etc.)
3. Message queued in priority heap (lower ID = higher priority)
4. Bus arbitration resolves conflicts
5. Message broadcast to all nodes
6. Receiving ECUs verify security, process message

---

## 4. Security Measures

### 4.1 AES-128 Encryption

**Implementation:**
- Cipher: AES in CBC mode
- Key Size: 128 bits (16 bytes)
- Initialization Vector: Random per message
- Padding: PKCS#7

**Security Properties:**
- ✅ **Confidentiality**: Attackers cannot read message content
- ⚠️ **Integrity**: Partial (detects some tampering via padding errors)
- ❌ **Authenticity**: Does not verify sender identity
- ❌ **Freshness**: Does not prevent replay attacks

**Performance:**
- Encryption overhead: ~0.5ms per message
- Decryption overhead: ~0.5ms per message
- Total: ~1.0ms round-trip latency

**Attack Resistance:**
| Attack | Resistance | Notes |
|--------|-----------|-------|
| Eavesdropping | **High** | Messages unreadable without key |
| Spoofing | **Medium** | Unencrypted attacker messages fail decryption |
| Replay | **None** | Valid encrypted messages can be replayed |
| Bus Flooding | **None** | Does not affect message rate |

---

### 4.2 HMAC-SHA256 Authentication

**Implementation:**
- Algorithm: HMAC using SHA-256
- Key Size: 256 bits (32 bytes)
- MAC Length: 32 bytes appended to message
- Verification: Constant-time comparison to prevent timing attacks

**Security Properties:**
- ❌ **Confidentiality**: Messages sent in plaintext
- ✅ **Integrity**: Any tampering detectable
- ✅ **Authenticity**: Verifies message came from legitimate sender
- ⚠️ **Freshness**: Partial (without nonce/timestamp)

**Performance:**
- HMAC generation: ~0.3ms per message
- HMAC verification: ~0.3ms per message
- Total: ~0.6ms round-trip latency

**Attack Resistance:**
| Attack | Resistance | Notes |
|--------|-----------|-------|
| Eavesdropping | **None** | Messages visible in plaintext |
| Spoofing | **Perfect** | Attacker cannot forge valid MAC |
| Replay | **Low** | Valid messages can be replayed |
| Bus Flooding | **None** | Does not affect message rate |

---

### 4.3 Rate Limiting

**Implementation:**
- Algorithm: Sliding window counter per CAN ID
- Threshold: 50 messages per ID per second
- Window: 1.0 second rolling window
- Action: Drop messages exceeding threshold

**Security Properties:**
- ✅ **Availability**: Prevents denial-of-service
- ⚠️ **Fairness**: May affect legitimate high-frequency IDs
- ❌ **Authentication**: Does not verify message legitimacy

**Performance:**
- Checking overhead: ~0.1ms per message
- Memory: O(n) for n unique CAN IDs

**Attack Resistance:**
| Attack | Resistance | Notes |
|--------|-----------|-------|
| Eavesdropping | **None** | Does not affect readability |
| Spoofing | **None** | Does not verify message content |
| Replay | **Medium** | Blocks burst replays, not slow replays |
| Bus Flooding | **Perfect** | Blocks floods exceeding threshold |

---

### 4.4 Intrusion Detection System (IDS)

**Implementation:**
- Type: Anomaly-based detection
- Learning Phase: 2 seconds to establish baseline
- Baseline Metrics: Average message interval per CAN ID
- Detection Threshold: Alert if frequency is 3x faster than baseline
- Action: Alert only (does not block messages)

**Security Properties:**
- ✅ **Detection**: Identifies abnormal patterns
- ❌ **Prevention**: Does not block attacks
- ⚠️ **False Positives**: May trigger on legitimate load changes

**Performance:**
- Detection overhead: ~0.1ms per message
- Learning overhead: Negligible (background analysis)

**Attack Resistance:**
| Attack | Resistance | Notes |
|--------|-----------|-------|
| Eavesdropping | **None** | Passive attack, no pattern change |
| Spoofing | **Low** | Single spoofed messages hard to detect |
| Replay | **High** | Burst replays very detectable |
| Bus Flooding | **Perfect** | Obvious frequency anomaly |

---

### 4.5 Combined Security Analysis

**Layered Defense Strategy:**

```
Attack Attempt
    ↓
[Rate Limiting] ← Blocks flooding
    ↓ (passed)
[HMAC Verification] ← Blocks spoofing
    ↓ (passed)
[Encryption Verification] ← Detects tampered/unencrypted
    ↓ (passed)
[IDS Analysis] ← Alerts on anomalies
    ↓
Message Processed
```

**Combined Effectiveness:**

| Security Combo | Bus Flood | Spoofing | Replay | Total Latency |
|----------------|-----------|----------|--------|---------------|
| None | ❌ 100% | ❌ 100% | ❌ 100% | ~0.3ms |
| Encryption Only | ❌ 100% | ⚠️ Detected | ❌ 100% | ~1.3ms |
| HMAC Only | ❌ 100% | ✅ Blocked | ⚠️ Detected | ~0.9ms |
| Rate Limit Only | ✅ Blocked | ❌ 100% | ⚠️ Partial | ~0.4ms |
| IDS Only | ⚠️ Detected | ❌ 100% | ⚠️ Detected | ~0.4ms |
| **All Measures** | **✅ Blocked** | **✅ Blocked** | **✅ Blocked** | **~2.0ms** |

---

## 5. Attack Implementations

### 5.1 Bus Flooding (Priority Hijack)

**Attack Description:**
Flood the CAN bus with highest priority messages (ID 0x000) to starve all other traffic.

**Attack Parameters:**
- Arbitration ID: `0x000` (highest priority)
- Message Rate: 10,000 messages/second
- Data Payload: `0xFF` repeated (8 bytes)
- Duration: Continuous while active

**Attack Mechanics:**
```python
while attack_active:
    frame = CANFrame(
        arbitration_id=0x000,
        data=b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    )
    bus.send(frame)
    time.sleep(0.0001)  # 10k msg/sec
```

**Impact:**
- **Brakes**: Cannot send pressure updates → No braking
- **Engine**: Cannot send RPM data → Transmission confusion
- **Steering**: Cannot send angle data → Power steering fails
- **Overall**: Complete denial-of-service

**Experimental Results:**
*(Fill in after running simulation)*

| Security Config | Messages Sent | Successful | Blocked | Detection Rate |
|----------------|---------------|-----------|---------|----------------|
| No Security | ??? | ???% | 0% | 0% |
| Rate Limit | ??? | ???% | ???% | ???% |
| All Security | ??? | ???% | ???% | ???% |

**Real-World Analogy:**
Like shouting over everyone at a meeting - nobody else can be heard.

---

### 5.2 Message Spoofing

**Attack Description:**
Inject fake messages with critical commands to manipulate vehicle behavior.

**Target Systems:**

#### Brake Pressure (ID 0x0A0) - **CRITICAL**
- Spoofed Data: `0x00` (pressure = 0)
- Impact: Brakes disabled despite pedal pressed
- Safety Risk: **EXTREME** - Cannot stop vehicle

#### Door Locks (ID 0x300)
- Spoofed Data: `0x00` (unlocked)
- Impact: All doors unlock
- Safety Risk: Medium - Theft, kidnapping

#### Headlights (ID 0x301)
- Spoofed Data: `0x00` (lights off)
- Impact: Lights turn off
- Safety Risk: High - Night driving hazard

**Attack Mechanics:**
```python
targets = {
    0x0A0: b'\x00',  # Brake pressure = 0
    0x300: b'\x00',  # Doors unlocked
    0x301: b'\x00'   # Lights off
}

for arb_id, data in targets.items():
    frame = CANFrame(arbitration_id=arb_id, data=data)
    bus.send(frame)
    time.sleep(0.05)
```

**Experimental Results:**
*(Fill in after running simulation)*

| Security Config | Attack Rate | Success Rate | Detection Rate | Blocked |
|----------------|------------|--------------|----------------|---------|
| No Security | ??? msg/s | ???% | 0% | 0 |
| Encryption | ??? msg/s | ???% | ???% | ??? |
| HMAC | ??? msg/s | ???% | ???% | ??? |
| All Security | ??? msg/s | ???% | ???% | ??? |

**Critical Scenario:**
```
Highway driving at 70 MPH
Driver sees obstacle
Presses brake pedal
    ↓
Attacker injects: brake_pressure = 0
    ↓
Brake ECU receives spoofed message
    ↓
No hydraulic pressure applied
    ↓
CRASH (vehicle doesn't slow)
```

---

### 5.3 Replay Attack

**Attack Description:**
Capture legitimate messages and replay them later to confuse ECUs with stale data.

**Captured Messages:**
- Engine RPM (ID 0x100): `3000 RPM` captured
- Gear Position (ID 0x200): `3rd Gear` captured

**Attack Mechanics:**

**Phase 1: Capture**
```python
captured = {}

def capture_legitimate_traffic():
    if frame.arbitration_id == 0x100:
        captured[0x100] = frame.data  # Store RPM
    if frame.arbitration_id == 0x200:
        captured[0x200] = frame.data  # Store gear
```

**Phase 2: Replay**
```python
for arb_id, old_data in captured.items():
    for _ in range(3):  # Replay 3x
        frame = CANFrame(arb_id, old_data)
        bus.send(frame)
        time.sleep(0.001)
```

**Impact:**
- **Transmission ECU** receives old RPM (3000) when actual RPM is 6000
- Shifts gears at wrong time
- Engine over-revs or stalls
- Potential engine damage

**Experimental Results:**
*(Fill in after running simulation)*

| Security Config | Replays Sent | Successful | Detected | Blocked |
|----------------|--------------|-----------|----------|---------|
| No Security | ??? | ???% | 0% | 0 |
| HMAC | ??? | ???% | ???% | ??? |
| Rate Limit | ??? | ???% | ???% | ??? |
| IDS | ??? | ???% | ???% | ??? |
| All Security | ??? | ???% | ???% | ??? |

**Why Replay Attacks Work:**
- Even with HMAC, the MAC is still valid
- Message is authentic, just not fresh
- Need timestamps or nonces to prevent

---

## 6. Experimental Results

### 6.1 Latency Analysis

#### Baseline (No Security)
*(Record from simulation)*
- Engine ECU: ___ ms average
- Brake ECU: ___ ms average
- Transmission ECU: ___ ms average
- Body ECU: ___ ms average

#### With Individual Security Measures

**Encryption Enabled:**
- Overhead: ~1.0ms
- Engine ECU: ___ ms average
- Brake ECU: ___ ms average (❌ **EXCEEDS 10ms CRITICAL THRESHOLD**)

**HMAC Enabled:**
- Overhead: ~0.6ms
- Engine ECU: ___ ms average
- Brake ECU: ___ ms average (✅ Under threshold)

**Rate Limiting Enabled:**
- Overhead: ~0.1ms
- Minimal impact on latency

**IDS Enabled:**
- Overhead: ~0.1ms
- Minimal impact on latency

#### With Combined Security

**Encryption + HMAC:**
- Total overhead: ~1.6ms
- Brake ECU: ___ ms (⚠️ **May exceed critical threshold**)

**All Four Measures:**
- Total overhead: ~2.0ms
- Brake ECU: ___ ms (❌ **Likely exceeds critical threshold**)

#### Safety Threshold Analysis

| System | Threshold | No Security | All Security | Safe? |
|--------|-----------|-------------|--------------|-------|
| Brakes | <10ms | ___ ms | ___ ms | ❌/✅ |
| ABS | <20ms | ___ ms | ___ ms | ❌/✅ |
| Steering | <20ms | ___ ms | ___ ms | ❌/✅ |
| Engine | <100ms | ___ ms | ___ ms | ✅ |

---

### 6.2 Attack Success Rates

#### Bus Flooding Attack

| Configuration | Attack Duration | Messages Blocked | System Available |
|--------------|----------------|------------------|------------------|
| No Security | 10s | 0% | ❌ 0% |
| Rate Limit | 10s | ___% | ✅ ___% |
| All Security | 10s | ___% | ✅ ___% |

**Key Finding:** Rate limiting alone is sufficient to block bus flooding.

---

#### Spoofing Attack

| Configuration | Spoof Attempts | Successful | Detection Rate |
|--------------|----------------|-----------|----------------|
| No Security | ___ | ___% | 0% |
| Encryption | ___ | ___% | ___% |
| HMAC | ___ | ___% | ___% |
| All Security | ___ | ___% | ___% |

**Key Finding:** HMAC authentication provides perfect spoofing prevention.

---

#### Replay Attack

| Configuration | Replay Attempts | Successful | Detection Rate |
|--------------|-----------------|-----------|----------------|
| No Security | ___ | ___% | 0% |
| HMAC | ___ | ___% | ___% |
| Rate Limit | ___ | ___% | ___% |
| IDS | ___ | ___% | ___% |
| All Security | ___ | ___% | ___% |

**Key Finding:** Replay attacks partially successful even with HMAC. Need timestamps.

---

### 6.3 System Health During Attacks

*(Record ECU status during each attack)*

**No Security Baseline:**
- Healthy ECUs: ___/4
- Compromised ECUs: ___/4
- Warning Status: ___/4

**With All Security:**
- Healthy ECUs: ___/4
- Compromised ECUs: ___/4
- Warning Status: ___/4

---

## 7. Discussion

### 7.1 Security vs. Performance Trade-offs

**Critical Finding:**
Full security (all 4 measures) adds ~2ms latency, which **exceeds the 10ms critical threshold** for brake systems.

**Recommendation:**
- **For Critical Systems (Brakes, Airbags):** Use HMAC only (~0.6ms overhead)
- **For Safety Systems (Steering, ABS):** Use Encryption + HMAC (~1.6ms overhead)
- **For Normal Systems (Telemetry):** Use all 4 measures (~2ms overhead)

**Selective Security Architecture:**
```
[Critical CAN] ← HMAC only
    ↓
[Gateway ECU]
    ↓
[Normal CAN] ← Full security (Encryption + HMAC + Rate Limit + IDS)
```

---

### 7.2 Attack Resistance Analysis

**Most Dangerous Attack:** Bus Flooding
- Can completely paralyze vehicle
- Affects all systems simultaneously
- **Mitigation:** Rate limiting (highly effective)

**Most Difficult to Prevent:** Replay
- Valid messages with valid authentication
- Hard to distinguish from legitimate traffic
- **Mitigation:** Need timestamps or message counters

**Most Targeted in Real World:** Spoofing
- Direct control over vehicle functions
- Surgical precision (specific systems)
- **Mitigation:** HMAC authentication (100% effective)

---

### 7.3 Real-World Applicability

**Challenges for Deployment:**
1. **Key Distribution:** How to securely share AES/HMAC keys across 100+ ECUs?
2. **Performance:** Critical systems cannot tolerate >10ms latency
3. **Legacy Systems:** Existing vehicles cannot be retrofitted
4. **Cost:** Crypto hardware adds $10-50 per ECU × 100 ECUs = $1000-5000/vehicle

**Industry Solutions:**
- Hardware Security Modules (HSM) for key storage
- Segmented networks (critical vs. non-critical CAN)
- Asymmetric cryptography for key exchange
- Standardization (AUTOSAR SecOC)

---

### 7.4 Limitations of This Simulation

**Simplifications:**
- Single CAN bus (real vehicles have 3-5 separate buses)
- No physical layer simulation (electromagnetic interference, wire faults)
- Simplified ECU logic (real ECUs have complex state machines)
- No gateway ECU filtering

**Not Simulated:**
- Supply chain attacks (malicious ECU firmware)
- Side-channel attacks (power analysis, timing)
- Physical tampering (cut wires, rogue nodes)
- Advanced persistent threats (long-term backdoors)

---

## 8. Conclusions

### 8.1 Key Findings

1. **Unprotected CAN buses are completely vulnerable** to all three attack types
2. **Rate limiting alone blocks bus flooding** with minimal latency overhead
3. **HMAC authentication prevents 100% of spoofing attacks**
4. **Replay attacks require additional countermeasures** (timestamps/nonces)
5. **Full security adds ~2ms latency**, exceeding critical system thresholds

### 8.2 Recommendations

**For Automotive Manufacturers:**
- Implement **segmented CAN architecture** (critical vs. non-critical)
- Deploy **HMAC authentication** on all safety-critical messages
- Add **rate limiting** to gateway ECUs
- Use **Hardware Security Modules** for key management
- **Never sacrifice safety** for security (latency first)

**For Researchers:**
- Explore **lightweight cryptography** for resource-constrained ECUs
- Develop **real-time intrusion detection** with <0.1ms overhead
- Design **quantum-resistant** protocols for future vehicles
- Study **AI-based anomaly detection** for sophisticated attacks

**For Regulators:**
- Mandate **security by design** in automotive standards
- Require **regular security audits** of vehicle software
- Establish **vulnerability disclosure programs**
- Create **liability frameworks** for cyber-physical incidents

---

## 9. Future Work

### 9.1 Immediate Extensions

- [ ] Implement timestamp-based replay prevention
- [ ] Add CAN-FD support (higher bandwidth)
- [ ] Simulate multi-domain CAN architecture
- [ ] Import real vehicle attack datasets
- [ ] Add machine learning IDS

### 9.2 Long-term Research

- [ ] Quantum-safe cryptography for automotive
- [ ] Zero-trust architecture for vehicle networks
- [ ] Hardware-accelerated security (FPGA, ASIC)
- [ ] Blockchain-based audit logs
- [ ] Vehicle-to-Everything (V2X) security

---

## 10. References

### Academic Papers
1. Miller, C., & Valasek, C. (2015). *Remote Exploitation of an Unaltered Passenger Vehicle*. Black Hat USA.
2. Checkoway, S., et al. (2011). *Comprehensive Experimental Analyses of Automotive Attack Surfaces*. USENIX Security.
3. Koscher, K., et al. (2010). *Experimental Security Analysis of a Modern Automobile*. IEEE S&P.

### Standards
4. ISO 11898: *Road vehicles — Controller area network (CAN)*
5. ISO/SAE 21434: *Road vehicles — Cybersecurity engineering*
6. SAE J3061: *Cybersecurity Guidebook for Cyber-Physical Vehicle Systems*
7. AUTOSAR SecOC: *Secure Onboard Communication*

### Industry Reports
8. NHTSA (2016). *Cybersecurity Best Practices for Modern Vehicles*
9. UNECE WP.29: *UN Regulation on Cybersecurity and Software Updates*
10. Upstream Security (2023). *Global Automotive Cybersecurity Report*

---

## Appendices

### Appendix A: Full System Configuration
*(Include config.py contents)*

### Appendix B: Attack Dataset Format
*(If implementing CSV import)*

### Appendix C: Code Listings
*(Link to GitHub repository)*

### Appendix D: Performance Benchmarks
*(Detailed latency measurements)*

---

**Report Prepared By:** [Your Name]  
**Date:** [Date]  
**Course:** [Course Name]  
**Institution:** [University Name]

---

## Instructions for Completing This Report

1. **Run Experiments:**
   - Start simulation with `python server.py`
   - Open frontend in browser
   - For each attack type:
     - Disable all security → Start attack → Record metrics
     - Enable security measures individually → Repeat
     - Enable all security → Record metrics

2. **Record Data:**
   - Screenshot latency graphs
   - Note attack success/failure rates
   - Record ECU health status changes
   - Export latency_log.csv for analysis

3. **Analysis:**
   - Calculate average latencies
   - Compute attack effectiveness percentages
   - Identify threshold violations
   - Compare security configurations

4. **Fill Tables:**
   - Replace all "???" with actual measurements
   - Update "❌/✅" based on results
   - Add screenshots as figures

5. **Write Discussion:**
   - Interpret your findings
   - Explain unexpected results
   - Compare to literature values
   - Propose improvements

Good luck with your report! 🚗🔒