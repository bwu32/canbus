import time
import heapq
import threading
import json
import hmac
import hashlib
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, List, Set
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# Security Configuration
AES_KEY = get_random_bytes(16)
HMAC_KEY = get_random_bytes(32)
BLOCK_SIZE = 16

# Latency thresholds (milliseconds)
LATENCY_CRITICAL = 10  # Brakes, airbags
LATENCY_SAFETY = 20    # Steering, ABS
LATENCY_NORMAL = 100   # Telemetry, lights

# Critical CAN IDs
CRITICAL_IDS = {0x0A0, 0x0A1}  # Brakes
SAFETY_IDS = {0x0C0, 0x0C1}    # Steering/ABS


@dataclass(order=True)
class CANFrame:
    arbitration_id: int
    data: bytes
    send_time: float = field(default=0.0, compare=False)
    length_bits: int = field(default=128, compare=False)
    source: str = field(default="", compare=False)
    encrypted: bool = field(default=False, compare=False)
    authenticated: bool = field(default=False, compare=False)


class SecurityManager:
    """Manages all security measures with toggle capabilities"""
    
    def __init__(self):
        self.measures = {
            'encryption': False,
            'authentication': False,
            'rate_limiting': False,
            'ids': False
        }
        
        # Statistics
        self.stats = {
            'attacks_detected': 0,
            'attacks_blocked': 0,
            'attacks_successful': 0,
            'messages_encrypted': 0,
            'messages_authenticated': 0,
            'rate_limit_violations': 0,
            'anomalies_detected': 0
        }
        
        # Rate limiting: track message counts per ID per time window
        self.rate_windows = defaultdict(lambda: deque(maxlen=100))
        self.rate_limit_threshold = 20  # Stricter: max 20 messages per ID per second
        
        # IDS: baseline message frequencies and patterns
        self.message_baseline = defaultdict(lambda: {'count': 0, 'avg_interval': 0})
        self.learning_phase = True
        self.learning_samples = defaultdict(list)
        
        # Latency tracking per security measure (cumulative per message)
        self.latency_overhead = {
            'encryption': 0,
            'authentication': 0,
            'rate_limiting': 0,
            'ids': 0
        }
        
        # Track last update time to smooth out values
        self.last_overhead_update = time.time()
        
    def toggle_measure(self, measure: str, enabled: bool):
        """Toggle a security measure on/off"""
        if measure in self.measures:
            self.measures[measure] = enabled
            return True
        return False
    
    def encrypt(self, data: bytes) -> tuple:
        """AES encryption with timing"""
        start = time.time()
        iv = get_random_bytes(BLOCK_SIZE)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        padded = pad(data, BLOCK_SIZE)
        ct = cipher.encrypt(padded)
        overhead = time.time() - start
        # Store round-trip overhead (encrypt + decrypt)
        self.latency_overhead['encryption'] = overhead * 2
        self.stats['messages_encrypted'] += 1
        return iv + ct, overhead
    
    def decrypt(self, data: bytes) -> tuple:
        """AES decryption with timing"""
        start = time.time()
        try:
            iv = data[:BLOCK_SIZE]
            ct = data[BLOCK_SIZE:]
            cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
            pt_padded = cipher.decrypt(ct)
            plaintext = unpad(pt_padded, BLOCK_SIZE)
            overhead = time.time() - start
            return plaintext, overhead, True
        except Exception as e:
            overhead = time.time() - start
            return None, overhead, False
    
    def add_hmac(self, data: bytes) -> tuple:
        """Add HMAC authentication"""
        start = time.time()
        mac = hmac.new(HMAC_KEY, data, hashlib.sha256).digest()
        overhead = time.time() - start
        # Store round-trip overhead (sign + verify)
        self.latency_overhead['authentication'] = overhead * 2
        self.stats['messages_authenticated'] += 1
        return data + mac, overhead
    
    def verify_hmac(self, data: bytes) -> tuple:
        """Verify HMAC authentication"""
        start = time.time()
        try:
            message = data[:-32]
            received_mac = data[-32:]
            expected_mac = hmac.new(HMAC_KEY, message, hashlib.sha256).digest()
            valid = hmac.compare_digest(received_mac, expected_mac)
            overhead = time.time() - start
            return message, overhead, valid
        except Exception:
            overhead = time.time() - start
            return None, overhead, False
    
    def check_rate_limit(self, arb_id: int) -> tuple:
        """Check if message rate exceeds threshold"""
        start = time.time()
        now = time.time()
        
        # Add current timestamp
        self.rate_windows[arb_id].append(now)
        
        # Count messages in last second
        recent = sum(1 for t in self.rate_windows[arb_id] if now - t < 1.0)
        
        overhead = time.time() - start
        self.latency_overhead['rate_limiting'] = overhead
        
        if recent > self.rate_limit_threshold:
            self.stats['rate_limit_violations'] += 1
            return False, overhead, recent
        
        return True, overhead, recent
    
    def check_anomaly(self, arb_id: int) -> tuple:
        """IDS: Detect anomalous message patterns"""
        start = time.time()
        now = time.time()
        
        if self.learning_phase:
            # Learning mode: build baseline
            self.learning_samples[arb_id].append(now)
            if len(self.learning_samples[arb_id]) >= 20:
                samples = self.learning_samples[arb_id]
                intervals = [samples[i] - samples[i-1] for i in range(1, len(samples))]
                self.message_baseline[arb_id] = {
                    'count': len(samples),
                    'avg_interval': sum(intervals) / len(intervals) if intervals else 0
                }
            overhead = time.time() - start
            self.latency_overhead['ids'] = overhead
            return True, overhead, 0
        
        # Detection mode: check against baseline
        baseline = self.message_baseline.get(arb_id)
        if not baseline or baseline['avg_interval'] == 0:
            overhead = time.time() - start
            return True, overhead, 0
        
        # Check if message frequency is abnormal (3x faster than baseline)
        recent_times = [t for t in self.rate_windows[arb_id] if now - t < 1.0]
        if len(recent_times) > 2:
            recent_intervals = [recent_times[i] - recent_times[i-1] 
                              for i in range(1, len(recent_times))]
            avg_recent = sum(recent_intervals) / len(recent_intervals)
            
            # Anomaly if 3x faster than baseline
            if avg_recent < baseline['avg_interval'] / 3:
                self.stats['anomalies_detected'] += 1
                overhead = time.time() - start
                return False, overhead, avg_recent
        
        overhead = time.time() - start
        self.latency_overhead['ids'] = overhead
        return True, overhead, 0
    
    def finish_learning(self):
        """Complete IDS learning phase"""
        self.learning_phase = False


class VirtualCANBus:
    """Virtual CAN bus with security integration"""
    
    def __init__(self, bitrate=500_000, security_manager=None):
        self.bitrate = bitrate
        self.lock = threading.Lock()
        self.receivers = []
        self.tx_queue = []
        self.security = security_manager
        
        # Metrics
        self.total_messages = 0
        self.blocked_messages = 0
        self.compromised = False
        
    def register(self, controller):
        self.receivers.append(controller)
    
    def send(self, frame: CANFrame):
        with self.lock:
            heapq.heappush(self.tx_queue, frame)
    
    def process_bus(self):
        """Process CAN bus with arbitration"""
        while True:
            frame = None
            with self.lock:
                if self.tx_queue:
                    frame = heapq.heappop(self.tx_queue)
            
            if frame:
                self.total_messages += 1
                
                # Simulate transmission time
                tx_time = frame.length_bits / self.bitrate
                time.sleep(tx_time)
                
                # Broadcast to all receivers
                for node in self.receivers:
                    node.receive(frame)
            else:
                time.sleep(0.0001)


class CANController:
    """CAN Controller with integrated security"""
    
    def __init__(self, ecu_name: str, bus: VirtualCANBus, 
                 security_manager: SecurityManager):
        self.name = ecu_name
        self.bus = bus
        self.security = security_manager
        
        self.pending = {}
        self.subscriptions = []
        self.log = []
        
        # Health status
        self.health_status = "healthy"  # healthy, warning, compromised
        self.attack_events = []
        
        # Latency tracking
        self.latency_history = deque(maxlen=1000)
        self.security_overhead_history = deque(maxlen=1000)
        
        bus.register(self)
    
    def subscribe(self, arb_ids: List[int]):
        self.subscriptions.extend(arb_ids)
    
    def send(self, frame: CANFrame):
        """Send with security measures applied"""
        frame.send_time = time.time()
        frame.source = self.name
        total_overhead = 0
        
        original_data = frame.data
        
        # Apply security measures if enabled
        if self.security.measures['encryption']:
            frame.data, overhead = self.security.encrypt(frame.data)
            frame.encrypted = True
            total_overhead += overhead
        
        if self.security.measures['authentication']:
            frame.data, overhead = self.security.add_hmac(frame.data)
            frame.authenticated = True
            total_overhead += overhead
        
        if self.security.measures['rate_limiting']:
            allowed, overhead, rate = self.security.check_rate_limit(frame.arbitration_id)
            total_overhead += overhead
            if not allowed:
                self.attack_events.append({
                    'time': time.time(),
                    'type': 'rate_limit_violation',
                    'arb_id': frame.arbitration_id,
                    'rate': rate
                })
                return  # Block message
        
        if self.security.measures['ids']:
            allowed, overhead, metric = self.security.check_anomaly(frame.arbitration_id)
            total_overhead += overhead
            if not allowed:
                self.attack_events.append({
                    'time': time.time(),
                    'type': 'anomaly_detected',
                    'arb_id': frame.arbitration_id
                })
                # IDS doesn't block, just alerts
        
        self.security_overhead_history.append(total_overhead * 1000)  # ms
        self.bus.send(frame)
    
    def receive(self, frame: CANFrame):
        """Receive with security verification"""
        now = time.time()
        arb_id = frame.arbitration_id
        total_overhead = 0
        
        data = frame.data
        
        # Verify security measures
        if self.security.measures['authentication'] and frame.authenticated:
            data, overhead, valid = self.security.verify_hmac(data)
            total_overhead += overhead
            if not valid:
                self.attack_events.append({
                    'time': now,
                    'type': 'authentication_failed',
                    'arb_id': arb_id
                })
                self.health_status = "warning"
                return
        
        if self.security.measures['encryption'] and frame.encrypted:
            data, overhead, valid = self.security.decrypt(data)
            total_overhead += overhead
            if not valid:
                self.attack_events.append({
                    'time': now,
                    'type': 'decryption_failed',
                    'arb_id': arb_id
                })
                self.health_status = "warning"
                return
        
        # Process message if subscribed
        if arb_id in self.subscriptions:
            latency = (now - frame.send_time) * 1000  # ms
            self.latency_history.append(latency)
            
            # Check latency thresholds
            if arb_id in CRITICAL_IDS and latency > LATENCY_CRITICAL:
                self.health_status = "warning"
            elif arb_id in SAFETY_IDS and latency > LATENCY_SAFETY:
                self.health_status = "warning"
            
            self.log.append({
                'time': now,
                'arb_id': arb_id,
                'latency': latency,
                'security_overhead': total_overhead * 1000,
                'source': frame.source
            })
    
    def get_status(self) -> dict:
        """Get current controller status"""
        avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        avg_overhead = sum(self.security_overhead_history) / len(self.security_overhead_history) if self.security_overhead_history else 0
        
        return {
            'name': self.name,
            'health': self.health_status,
            'avg_latency': avg_latency,
            'avg_security_overhead': avg_overhead,
            'recent_attacks': len([e for e in self.attack_events if time.time() - e['time'] < 5]),
            'subscriptions': self.subscriptions
        }


# ECU Applications
class EngineECU:
    """Engine Control Unit"""
    def __init__(self, controller: CANController):
        self.ctrl = controller
        self.running = True
    
    def run(self):
        rpm = 3000
        temp = 90
        while self.running:
            self.ctrl.send(CANFrame(0x100, rpm.to_bytes(2, 'big')))
            self.ctrl.send(CANFrame(0x101, bytes([temp])))
            rpm = (rpm + 50) % 8000
            temp = 85 + (rpm // 400)
            time.sleep(0.05)
    
    def stop(self):
        self.running = False


class BrakeECU:
    """Brake Control Unit (Critical)"""
    def __init__(self, controller: CANController):
        self.ctrl = controller
        self.running = True
    
    def run(self):
        pressure = 0
        while self.running:
            self.ctrl.send(CANFrame(0x0A0, bytes([pressure])))  # Brake pressure
            self.ctrl.send(CANFrame(0x0A1, bytes([1])))  # Brake status OK
            pressure = (pressure + 5) % 100
            time.sleep(0.01)  # Critical timing
    
    def stop(self):
        self.running = False


class TransmissionECU:
    """Transmission Control Unit"""
    def __init__(self, controller: CANController):
        self.ctrl = controller
        self.running = True
    
    def run(self):
        gear = 1
        while self.running:
            self.ctrl.send(CANFrame(0x200, bytes([gear])))
            gear = (gear % 6) + 1
            time.sleep(0.08)
    
    def stop(self):
        self.running = False


class BodyECU:
    """Body Control (Doors, Lights)"""
    def __init__(self, controller: CANController):
        self.ctrl = controller
        self.running = True
    
    def run(self):
        doors_locked = True
        lights_on = True
        while self.running:
            self.ctrl.send(CANFrame(0x300, bytes([int(doors_locked)])))
            self.ctrl.send(CANFrame(0x301, bytes([int(lights_on)])))
            time.sleep(0.1)
    
    def stop(self):
        self.running = False


class CANSimulation:
    """Main simulation orchestrator"""
    
    def __init__(self):
        self.security = SecurityManager()
        self.bus = VirtualCANBus(bitrate=500_000, security_manager=self.security)
        
        # Controllers
        self.eng_ctrl = CANController("EngineECU", self.bus, self.security)
        self.brake_ctrl = CANController("BrakeECU", self.bus, self.security)
        self.tcu_ctrl = CANController("TransmissionECU", self.bus, self.security)
        self.body_ctrl = CANController("BodyECU", self.bus, self.security)
        
        # Subscriptions
        self.eng_ctrl.subscribe([0x0A0, 0x300])
        self.brake_ctrl.subscribe([0x100])
        self.tcu_ctrl.subscribe([0x100, 0x0A0])
        self.body_ctrl.subscribe([0x100, 0x200])
        
        # ECU applications
        self.engine = EngineECU(self.eng_ctrl)
        self.brakes = BrakeECU(self.brake_ctrl)
        self.transmission = TransmissionECU(self.tcu_ctrl)
        self.body = BodyECU(self.body_ctrl)
        
        self.controllers = [self.eng_ctrl, self.brake_ctrl, self.tcu_ctrl, self.body_ctrl]
        self.ecus = [self.engine, self.brakes, self.transmission, self.body]
        
        self.threads = []
        self.running = False
    
    def start(self):
        """Start simulation"""
        self.running = True
        
        # Start bus
        t = threading.Thread(target=self.bus.process_bus, daemon=True)
        t.start()
        self.threads.append(t)
        
        # Start ECUs
        for ecu in self.ecus:
            t = threading.Thread(target=ecu.run, daemon=True)
            t.start()
            self.threads.append(t)
        
        # Learning phase for IDS
        time.sleep(2)
        self.security.finish_learning()
    
    def stop(self):
        """Stop simulation"""
        self.running = False
        for ecu in self.ecus:
            ecu.stop()
    
    def get_state(self) -> dict:
        """Get current simulation state"""
        return {
            'security_measures': self.security.measures,
            'security_stats': self.security.stats,
            'security_overhead': self.security.latency_overhead,
            'controllers': [ctrl.get_status() for ctrl in self.controllers],
            'bus_stats': {
                'total_messages': self.bus.total_messages,
                'blocked_messages': self.bus.blocked_messages,
                'compromised': self.bus.compromised
            }
        }
    
    def toggle_security(self, measure: str, enabled: bool):
        """Toggle security measure"""
        return self.security.toggle_measure(measure, enabled)