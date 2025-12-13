# CAN Bus Security Simulation

**Disclaimer: Generative AI was used in this project to assist in implementation of cybersecurity topics as discussed in class.**

## 🎯 Objective

**Goal:** Simulate in-vehicle CAN communications to demonstrate how attackers can inject, replay, or flood messages to manipulate ECUs, then apply computer security principles to strengthen those vulnerabilities.

This proof-of-concept demonstrates:
- How attackers exploit CAN bus vulnerabilities
- Real-time effects of attacks on vehicle systems
- Effectiveness of security countermeasures
- Trade-offs between security and real-time performance

---

## 🚗 Why is CAN Important?

### What is CAN?
**CAN (Controller Area Network)** is the primary communication protocol in modern vehicles, connecting 50-100+ Electronic Control Units (ECUs).

### What are ECUs?
**ECUs (Electronic Control Units)** are small embedded computers that control specific vehicle functions:
- **Engine ECU**: Manages fuel injection, RPM, temperature
- **Brake ECU**: Controls braking pressure, ABS (CRITICAL)
- **Transmission ECU**: Handles gear shifting
- **Body ECU**: Manages doors, lights, windows

### The Security Problem
**CAN has essentially no security:**
- **No encryption** - All messages visible in plaintext
- **No authentication** - Any ECU can send any message
- **No access control** - No verification of sender identity
- **No freshness guarantees** - Old messages can be replayed

Designed in 1983 for reliability and speed, not security. Today's connected vehicles make this a critical vulnerability.

---

## 🔓 Vulnerabilities

### Real-World Consequences
- **2015 Jeep Cherokee**: Hackers remotely disabled brakes at highway speeds → 1.4M vehicles recalled
- **2016 Tesla Model S**: Researchers unlocked doors and started engine via CAN injection
- **Ongoing**: 100+ vulnerabilities discovered across major manufacturers

### Attack Surfaces
1. **OBD-II Port** (under steering wheel) - Direct CAN access
2. **Wireless** (Bluetooth, Wi-Fi, Cellular) - Remote exploitation
3. **Infotainment Systems** - Bridge to CAN network
4. **Physical Tampering** - Wire splicing, rogue ECUs

### Current Solutions (Insufficient)
- **Network Segmentation** - Separate critical/non-critical buses (bypassed if gateway compromised)
- **Firewalls** - Limited effectiveness without authentication
- **Anomaly Detection** - Can detect but not prevent attacks
- **Physical Security** - Doesn't stop wireless attacks

**Problem:** Retrofitting security into CAN is expensive and complex. This simulation explores practical solutions.

---

## 🖥️ Simulation Overview

### Architecture
Our code simulates a virtual CAN network with multiple ECUs communicating like in a real vehicle.

**Components:**

1. **Virtual CAN Bus**
   - Shared communication line (500 kbps bitrate)
   - Handles message priority (lower arbitration ID = higher priority)
   - Simulates timing (128 bits per frame = 0.256ms transmission)
   - Broadcasts messages to all connected ECUs

2. **ECUs (Electronic Control Units)**
   - **Engine ECU**: Sends RPM (0x100) and temperature (0x101) every 50ms
   - **Brake ECU**: Sends brake pressure (0x0A0) and status (0x0A1) every 10ms (CRITICAL)
   - **Transmission ECU**: Sends gear position (0x200) every 80ms
   - **Body ECU**: Sends door locks (0x300) and lights (0x301) every 100ms

3. **CAN Controllers**
   - Each ECU has a controller that:
     - **Sends messages** with security measures applied
     - **Receives subscribed messages** (only listens to relevant IDs)
     - **Applies security checks** (encryption, authentication, rate limiting, IDS)
     - **Tracks latency** for performance analysis

4. **Parallel Operation**
   - All ECUs run in separate threads
   - Simulate real-time concurrent communication
   - System logs message latency continuously
   - WebSocket server broadcasts updates every 100ms to frontend

---

## 🔴 Attacks Implemented

### 1. Bus Flooding (Priority Hijack)
**Method:** Spam arbitration ID `0x000` (highest priority) at 10,000 messages/second

**How it works:**
- CAN uses priority-based arbitration (lower ID wins)
- Attacker floods with ID 0x000
- Legitimate messages (brakes, steering) are starved
- Vehicle systems paralyzed

**Real-world impact:**
- Brakes unresponsive
- Steering power assist disabled
- Complete denial of service

**Blocked by:** Rate Limiting (detects >20 msg/sec)

---

### 2. Message Spoofing
**Method:** Inject fake messages with malicious commands

**Targets:**
- **Brake Pressure (0x0A0)**: Set to 0 → Disables brakes (CRITICAL!)
- **Door Locks (0x300)**: Set to unlocked → Security bypass
- **Lights (0x301)**: Turn off → Safety hazard at night

**How it works:**
- Attacker sends messages impersonating legitimate ECUs
- Without authentication, receivers trust all messages
- Malicious commands executed immediately

**Real-world impact:**
- Direct control of vehicle functions
- Safety systems compromised
- Potential for crashes or theft

**Blocked by:** HMAC Authentication (attacker can't forge valid MAC without secret key)

---

### 3. Replay Attack
**Method:** Capture legitimate messages and retransmit them later

**Targets:**
- **Engine RPM (0x100)**: Replay old RPM value
- **Gear Position (0x200)**: Replay incorrect gear data

**How it works:**
- Attacker records valid messages (with encryption/HMAC intact)
- Replays messages in rapid bursts (3x per cycle)
- ECUs receive stale/incorrect data

**Real-world impact:**
- Transmission shifts at wrong RPM → Engine damage
- Confuses control logic with outdated sensor data
- Dashboard shows false information

**Blocked by:** Rate Limiting (catches burst replays at >20 msg/sec)

---

## 🛡️ Security Measures

### 1. AES-128 Encryption
**Purpose:** Confidentiality - prevents eavesdropping

**How it works:**
```
Sender: Plaintext → AES-CBC encrypt (random IV) → Ciphertext
Receiver: Ciphertext → AES-CBC decrypt → Plaintext
```

**Process:**
- Each message encrypted with shared 128-bit key
- Random Initialization Vector (IV) per message
- Receiver decrypts and verifies padding

**Overhead:** ~1.0ms (0.5ms encrypt + 0.5ms decrypt)

**Effectiveness:**
- ✅ Blocks eavesdropping (attacker can't read messages)
- ⚠️ Partial against spoofing (unencrypted messages fail decryption)
- ❌ Doesn't prevent replay (encrypted message still valid)

---

### 2. HMAC-SHA256 Authentication
**Purpose:** Integrity & Authenticity - prevents tampering and spoofing

**How it works:**
```
Sender: Message → HMAC(secret_key, message) → Message + MAC
Receiver: Verify HMAC(secret_key, message) == received_MAC
```

**Process:**
- Generate 32-byte MAC using SHA-256 hash with secret key
- Append MAC to message
- Receiver recalculates MAC and compares
- Mismatch = message rejected

**Overhead:** ~0.6ms (0.3ms sign + 0.3ms verify)

**Effectiveness:**
- ❌ Doesn't encrypt (messages visible)
- ✅ **Blocks spoofing** (attacker can't forge valid MAC)
- ⚠️ Doesn't prevent replay (valid MAC can be replayed)

**Why spoofing fails:**
- Attacker doesn't know secret key
- Can't generate valid MAC for fake messages
- All forged messages rejected

---

### 3. Rate Limiting
**Purpose:** Prevent denial-of-service and burst attacks

**How it works:**
```
For each CAN ID:
  Count messages in last 1 second
  If count > 20: BLOCK message
  Else: ALLOW message
```

**Process:**
- Track timestamps of messages per arbitration ID
- Sliding window (last 1 second)
- Threshold: 20 messages per ID per second
- Exceeding threshold = message dropped

**Overhead:** ~0.1ms (timestamp check)

**Effectiveness:**
- ❌ Doesn't prevent spoofing
- ✅ **Blocks bus flooding** (catches 10,000 msg/sec attacks)
- ✅ **Blocks replay bursts** (3 replays in 0.003s exceeds threshold)

**Why flooding fails:**
- Attacker sends 10,000 msg/sec
- Rate limiter allows only 20/sec
- 99.8% of attack messages dropped

---

### 4. Intrusion Detection System (IDS)
**Purpose:** Detect anomalous message patterns

**How it works:**
```
Learning Phase (2 seconds):
  Record normal message frequencies per ID
  Calculate baseline: avg_interval between messages

Detection Phase:
  If new_interval < baseline/3: ALERT (3x faster than normal)
```

**Process:**
- Learn normal behavior (first 2 seconds)
- Calculate average message intervals for each ID
- Flag messages arriving 3x faster than baseline
- **Does not block** - only detects and alerts

**Overhead:** ~0.1ms (pattern comparison)

**Effectiveness:**
- ❌ Doesn't block attacks
- ⚠️ Detects bus flooding (obvious frequency spike)
- ⚠️ Detects replay bursts (unusual duplication)
- ✅ Provides visibility into attacks

**Limitation:** Cannot prevent attacks, only raise alerts

---

## 📊 Simulation Evaluation

### Latency Thresholds (Safety-Critical)
Modern vehicles have **hard real-time requirements**:

| System | Threshold | Why It Matters |
|--------|-----------|----------------|
| **Brakes/Airbags** | <10ms | 10ms delay = 1m stopping distance at highway speed |
| **Steering/ABS** | <20ms | Required for responsive handling |
| **Telemetry** | <100ms | Non-critical data |

**Warning:** If security overhead exceeds these thresholds, safety is compromised.

---

### Attack Effectiveness Matrix

| Attack | No Security | Rate Limit | Encryption | HMAC | IDS | **All Security** |
|--------|------------|-----------|------------|------|-----|------------------|
| **Bus Flooding** | ❌ 100% success | ✅ **BLOCKED** | ❌ 100% | ❌ 100% | ⚠️ Detected | ✅ **BLOCKED** |
| **Spoofing** | ❌ 100% success | ❌ 100% | ⚠️ Detected | ✅ **BLOCKED** | ❌ 100% | ✅ **BLOCKED** |
| **Replay** | ❌ 100% success | ✅ **BLOCKED** | ❌ 100% | ⚠️ Detected | ⚠️ Detected | ✅ **BLOCKED** |

**Key Finding:** No single measure stops all attacks - **layered defense is essential**.

---

### Security vs. Performance Trade-offs

**Measured Latency (Average):**

| Configuration | Total Overhead | Safe for Brakes? | Safe for Steering? |
|--------------|----------------|------------------|-------------------|
| No Security | ~0.3ms | ✅ Yes | ✅ Yes |
| Encryption Only | ~1.0ms | ✅ Yes | ✅ Yes |
| HMAC Only | ~0.6ms | ✅ Yes | ✅ Yes |
| Rate Limit + IDS | ~0.2ms | ✅ Yes | ✅ Yes |
| **All Security** | **~2.0ms** | ✅ Yes | ✅ Yes |

**Result:** All security measures stay **well under 10ms critical threshold** - safe for deployment.

---

### Recommended Configuration

**For Critical Systems (Brakes, Airbags):**
- ✅ HMAC Authentication (~0.6ms)
- ✅ Rate Limiting (~0.1ms)
- **Total: ~0.7ms** (safe)

**For Safety Systems (Steering, ABS):**
- ✅ Encryption (~1.0ms)
- ✅ HMAC Authentication (~0.6ms)
- ✅ Rate Limiting (~0.1ms)
- **Total: ~1.7ms** (safe)

**For Normal Systems (Telemetry, Body Controls):**
- ✅ All 4 measures (~2.0ms)
- **Total: ~2.0ms** (safe, plenty of margin)

---

## 🔬 Significance

### Why This Matters

**Automotive Cybersecurity is Critical:**
- 300+ million connected vehicles by 2025
- Average vehicle has 100+ ECUs and 100 million lines of code
- One vulnerability can affect millions of vehicles
- Lives depend on secure vehicle systems

**This Simulation Demonstrates:**
1. **CAN is fundamentally insecure** - No protection by design
2. **Attacks are practical** - Simple code can compromise vehicles
3. **Security is feasible** - Countermeasures work within real-time constraints
4. **Trade-offs exist** - Must balance security with performance

**Real-World Application:**
- Automotive manufacturers implementing these exact techniques
- Standards emerging (AUTOSAR SecOC, ISO/SAE 21434)
- Regulatory requirements (UNECE WP.29) mandate cybersecurity

---

## ✅ Conclusion

### Key Findings

1. **CAN buses are vulnerable by design** - Trivial to attack without security
2. **Layered security is essential** - No single measure stops all attacks
3. **Performance impact is acceptable** - Security overhead stays under critical thresholds
4. **Real-time constraints are satisfied** - All configurations safe for deployment

### Security Effectiveness

**Best Protection:**
- **HMAC Authentication** stops spoofing (100% effective)
- **Rate Limiting** stops flooding and replay attacks (>99% effective)
- Combined: Blocks all three attack types

**Weaknesses:**
- Basic HMAC doesn't prevent replay (needs timestamps/nonces)
- IDS only detects, doesn't prevent
- Key management not addressed (how to distribute/rotate keys)

### Future Improvements

1. **Timestamp-based replay protection** - Add sequence numbers or timestamps to HMAC
2. **Key rotation** - Periodic key updates to limit compromise impact
3. **Hardware Security Modules (HSM)** - Secure key storage
4. **Machine learning IDS** - Better anomaly detection
5. **Multi-domain segmentation** - Separate critical/non-critical networks

### Final Recommendation

Deploy **HMAC + Rate Limiting** on all CAN networks as minimum baseline security. This provides:
- ✅ Spoofing protection (HMAC)
- ✅ Flooding protection (Rate Limiting)
- ✅ Replay protection (Rate Limiting catches bursts)
- ✅ Low latency (~0.7ms overhead)
- ✅ Compatible with real-time requirements

**The automotive industry must adopt these measures to protect vehicle safety and security.**

---

## 📚 Running the Simulation

### Setup
```bash
# Install dependencies
pip install pycryptodome websockets

# Start backend
python server.py

# Open frontend in browser (React app on localhost:5173)
npm run dev
```

### Usage
1. Toggle security measures ON/OFF to see latency impact
2. Start attacks to observe blocking effectiveness
3. Monitor real-time latency graph (must stay under thresholds)
4. Check statistics to verify security is working

---

## 📖 References

### Standards
- ISO 11898: CAN Bus Standard
- ISO/SAE 21434: Automotive Cybersecurity Standard
- AUTOSAR SecOC: Secure Onboard Communication

### Research
- Miller & Valasek (2015): "Remote Exploitation of an Unaltered Passenger Vehicle"
- Checkoway et al. (2011): "Comprehensive Experimental Analyses of Automotive Attack Surfaces"

---

**Built by:** Aidan Shaheen, Brian Wu, Calvin Berlin 
**Course:** ENEE457  

**Date:** Fall 2025


