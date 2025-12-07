# 🚀 Quick Start Guide

Get your CAN Bus Security Simulation running in **under 5 minutes**!

---

## ⚡ Super Quick Start

```bash
# 1. Install dependencies
pip install pycryptodome websockets

# 2. Start server
python server.py

# 3. Open frontend (in Claude.ai or React environment)
# The dashboard will connect automatically
```

That's it! 🎉

---

## 📋 What You Have

Your simulation includes:

### Files
- `can_bus_simulation.py` - Core CAN bus + ECUs + security
- `can_bus_attacks.py` - Three attack types
- `server.py` - WebSocket server (backend)
- `frontend.html` - React dashboard (frontend)
- `config.py` - Easy configuration
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - Complete technical documentation
- `ATTACK_GUIDE.md` - Detailed attack explanations
- `REPORT_TEMPLATE.md` - Template for your report
- `QUICKSTART.md` - This file!

---

## 🎮 First Experiment: See the Vulnerability

**Goal:** Experience how vulnerable unprotected CAN is.

### Step 1: Start with NO Security
1. Open the dashboard (frontend)
2. Verify all 4 security measures are **OFF**
3. Watch the "System Health" panel - all ECUs should be green (healthy)

### Step 2: Launch Bus Flooding Attack
1. In "Attack Simulation" panel
2. Click **START** on "Bus Flooding"
3. **Observe:**
   - Red "ACTIVE ATTACK" indicator appears
   - "Compromised Nodes" shows "BUS_FLOODER"
   - System health degrades rapidly
   - Latency graph spikes

### Step 3: Enable Rate Limiting
1. In "Security Measures" panel
2. Toggle "Rate Limiting" to **ON**
3. **Observe:**
   - Attack still active, but now being **BLOCKED**
   - "Attacks Blocked" counter increases
   - System health improves
   - Latency normalizes

### Step 4: Stop Attack
1. Click **STOP** on "Bus Flooding"
2. System returns to normal

**What You Just Learned:**
- Unprotected CAN → Complete vulnerability
- Rate limiting → Effective defense against flooding
- Security overhead → Minimal (~0.1ms)

---

## 🧪 Second Experiment: Critical System Protection

**Goal:** See why brake systems need special consideration.

### Step 1: Enable ALL Security
1. Turn **ON** all 4 security measures:
   - ✅ Encryption
   - ✅ Authentication
   - ✅ Rate Limiting
   - ✅ IDS

2. **Observe** the "Total Security Overhead"
   - Should show ~2.0ms

3. Look at latency graph
   - Notice increased baseline latency

### Step 2: Launch Spoofing Attack
1. Start "Spoofing" attack
2. **Observe:**
   - Attack attempts shown
   - "Blocked" count increases rapidly
   - BrakeECU stays healthy (not compromised)
   - HMAC authentication is blocking the attack!

### Step 3: Check Latency Warning
1. Look for warning banner at top
2. If security overhead >10ms:
   - 🚨 **CRITICAL LATENCY WARNING** appears
   - "Brakes/Airbags" systems at risk
   - This is **unsafe for real vehicles**!

**What You Just Learned:**
- Full security → Excellent protection
- But too much latency → Safety risk
- Need to balance security with real-time requirements

---

## 🎯 Third Experiment: Optimal Configuration

**Goal:** Find the sweet spot for critical systems.

### Step 1: Try "Balanced" Security
1. Turn **OFF** Encryption
2. Turn **OFF** IDS
3. Keep **ON**: Authentication + Rate Limiting
4. Overhead should be ~0.7ms

### Step 2: Test Against All Attacks
1. Start "Spoofing" → Should be BLOCKED (authentication works)
2. Start "Bus Flooding" → Should be BLOCKED (rate limiting works)
3. Start "Replay" → Partially blocked

### Step 3: Check System Health
- All ECUs should remain healthy
- Latency under 10ms critical threshold
- Attacks mostly blocked

**What You Just Learned:**
- Don't need all 4 measures at once
- Authentication + Rate Limiting = Good balance
- Suitable for critical systems (low latency + high security)

---

## 📊 Understanding the Dashboard

### Top Panels (Left to Right)

**1. Security Measures**
- Toggle each measure ON/OFF
- See total overhead in milliseconds
- Breakdown by measure

**2. Attack Simulation**
- START/STOP each attack type
- See attempt/success/blocked counts
- Success rate and detection rate
- Compromised nodes list

**3. System Health**
- Each ECU's status: Healthy/Warning/Compromised
- Average latency per ECU
- Security overhead per ECU
- Recent attacks counter
- Security statistics totals

### Bottom Panel

**Latency Graph**
- Blue line = measured latency
- Red dashed = 10ms critical threshold
- Yellow dashed = 20ms safety threshold
- Green dashed = 100ms normal threshold
- Watch how enabling security raises the blue line

### Bottom Events Log (if attacks active)
- Recent attack events
- Timestamps
- Attack types and targets

---

## 🔧 Common Issues & Solutions

### "WebSocket connection failed"
**Problem:** Frontend can't connect to backend  
**Solution:**
```bash
# Make sure server is running
python server.py

# Check it says "Server ready! Connect from frontend at ws://localhost:8765"
# Then open/refresh frontend
```

### "Module not found: pycryptodome"
**Problem:** Missing Python dependencies  
**Solution:**
```bash
pip install pycryptodome websockets

# Or use requirements file
pip install -r requirements.txt
```

### "Port 8765 already in use"
**Problem:** Another process using the port  
**Solution:**
```bash
# Kill existing server
# Linux/Mac:
lsof -ti:8765 | xargs kill -9

# Windows:
netstat -ano | findstr :8765
taskkill /PID <PID_NUMBER> /F

# Or change port in config.py:
WEBSOCKET_PORT = 8766  # Use different port
```

### Latency graph not updating
**Problem:** No data flowing  
**Solution:**
- Check WebSocket connection (should show "Connected")
- Refresh browser
- Restart server
- Make sure ECUs are actually sending messages

### Attack statistics all zeros
**Problem:** Attacks not running  
**Solution:**
- Click START button for attack (should turn red)
- Check "Active Attacks" list in dashboard
- Look for "🚨 ACTIVE ATTACK" indicator
- Restart attack if needed

---

## 💡 Pro Tips

### For Best Demo Effect
1. Start with NO security, run all 3 attacks simultaneously
   - Watch chaos unfold
2. Enable security measures one by one
   - Show progressive improvement
3. End with optimal config (Auth + Rate Limit)
   - Show balance of security and performance

### For Report Data Collection
1. Run each configuration for at least 60 seconds
2. Export latency_log.csv for analysis
3. Screenshot latency graph for each config
4. Record attack statistics tables
5. Note any system warnings

### For Impressive Visuals
- Let attacks run for 10-15 seconds before stopping
- Watch compromised nodes accumulate
- Show latency spikes in real-time
- Toggle security while attacks are active (watch immediate effect)

---

## 🎓 Next Steps

### Understanding the Code
1. Read `README.md` for full technical details
2. Study `ATTACK_GUIDE.md` for attack mechanics
3. Review `config.py` for customization options

### Experimenting
1. Try different security combinations
2. Modify attack parameters in `config.py`
3. Add new CAN IDs or ECUs
4. Test different latency thresholds

### Report Writing
1. Use `REPORT_TEMPLATE.md` as guide
2. Fill in experimental data
3. Analyze trade-offs
4. Make recommendations

---

## 🆘 Still Stuck?

### Check Logs
```bash
# Server should print:
✅ CAN Simulation started
🚀 WebSocket server starting on ws://localhost:8765
✅ Server ready!
📊 Broadcasting updates every 100ms
```

### Verify Python Version
```bash
python --version
# Should be 3.8 or higher
```

### Test Dependencies
```python
# Run in Python shell:
import Crypto.Cipher.AES  # Should work
import websockets          # Should work
```

### Frontend Debug
- Open browser console (F12)
- Check for WebSocket connection messages
- Look for any JavaScript errors

---

## 🎉 Success Checklist

- [ ] Server starts without errors
- [ ] Frontend shows "Connected"
- [ ] Dashboard displays 4 ECUs in "System Health"
- [ ] Latency graph is drawing
- [ ] Can toggle security measures
- [ ] Can start/stop attacks
- [ ] Attack statistics update
- [ ] Latency warnings appear when appropriate

If all checked ✅ → You're ready to go! 🚗💨

---

## 📚 Quick Reference

### File Purposes
| File | Purpose |
|------|---------|
| `can_bus_simulation.py` | ECUs, security measures, core logic |
| `can_bus_attacks.py` | Attack implementations |
| `server.py` | WebSocket server, connects backend to frontend |
| `frontend.html` | React dashboard with visualizations |
| `config.py` | All tunable parameters |

### Key Concepts
| Concept | Meaning |
|---------|---------|
| **Arbitration ID** | Message priority (lower = higher priority) |
| **ECU** | Electronic Control Unit (mini-computer in car) |
| **CAN Bus** | Communication network connecting ECUs |
| **Latency** | Delay from send to receive |
| **Security Overhead** | Extra latency added by security |

### Attack Types
| Attack | What It Does | Blocked By |
|--------|-------------|-----------|
| **Bus Flooding** | Spam highest priority → DoS | Rate Limiting |
| **Spoofing** | Fake critical commands | HMAC Auth |
| **Replay** | Repeat old valid messages | Rate Limit + IDS |

---

**Ready to explore automotive cybersecurity? Let's go! 🔐🚗**