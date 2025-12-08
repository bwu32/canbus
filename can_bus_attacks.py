import time
import threading
from dataclasses import dataclass
from collections import defaultdict
from can_bus_simulation import CANFrame, VirtualCANBus, SecurityManager


@dataclass
class AttackStatistics:
    """Track attack success/failure metrics"""
    attack_type: str
    attempts: int = 0
    successful: int = 0
    blocked: int = 0
    detected: int = 0
    target_ids: list = None
    
    def __post_init__(self):
        if self.target_ids is None:
            self.target_ids = []
    
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return (self.successful / self.attempts) * 100
    
    def detection_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return (self.detected / self.attempts) * 100


class AttackManager:
    """Manages all attacks on the CAN bus"""
    
    def __init__(self, bus: VirtualCANBus, security: SecurityManager):
        self.bus = bus
        self.security = security
        self.attacks = {}
        self.active_attacks = set()
        self.compromised_nodes = set()
        
        # Initialize attack statistics
        self.stats = {
            'bus_flooding': AttackStatistics('bus_flooding', target_ids=[]),
            'spoofing': AttackStatistics('spoofing', target_ids=[0x0A0, 0x300, 0x301]),
            'replay': AttackStatistics('replay', target_ids=[0x100, 0x200])
        }
        
        self.attack_log = []
    
    def register_attack(self, attack_name: str, attack_instance):
        """Register an attack"""
        self.attacks[attack_name] = attack_instance
    
    def start_attack(self, attack_name: str):
        """Start a specific attack"""
        if attack_name in self.attacks and attack_name not in self.active_attacks:
            self.active_attacks.add(attack_name)
            attack = self.attacks[attack_name]
            
            # Mark compromised nodes
            if hasattr(attack, 'target_node'):
                self.compromised_nodes.add(attack.target_node)
            
            t = threading.Thread(target=attack.execute, daemon=True)
            t.start()
            
            self.attack_log.append({
                'time': time.time(),
                'attack': attack_name,
                'action': 'started',
                'targets': self.stats[attack_name].target_ids
            })
            
            return True
        return False
    
    def stop_attack(self, attack_name: str):
        """Stop a specific attack"""
        if attack_name in self.active_attacks:
            self.active_attacks.discard(attack_name)
            attack = self.attacks[attack_name]
            attack.stop()
            
            if hasattr(attack, 'target_node'):
                self.compromised_nodes.discard(attack.target_node)
            
            self.attack_log.append({
                'time': time.time(),
                'attack': attack_name,
                'action': 'stopped'
            })
            
            return True
        return False
    
    def get_status(self) -> dict:
        """Get current attack status"""
        return {
            'active_attacks': list(self.active_attacks),
            'compromised_nodes': list(self.compromised_nodes),
            'statistics': {
                name: {
                    'attempts': stat.attempts,
                    'successful': stat.successful,
                    'blocked': stat.blocked,
                    'detected': stat.detected,
                    'success_rate': stat.success_rate(),
                    'detection_rate': stat.detection_rate(),
                    'target_ids': stat.target_ids
                }
                for name, stat in self.stats.items()
            },
            'recent_events': [e for e in self.attack_log if time.time() - e['time'] < 10]
        }


class BusFloodingAttack:
    """
    Attack: Flood the bus with highest priority messages
    Goal: Starve legitimate traffic, cause denial of service
    Target: Entire bus (priority hijack with ID 0x000)
    """
    
    def __init__(self, bus: VirtualCANBus, attack_manager: AttackManager):
        self.bus = bus
        self.manager = attack_manager
        self.running = False
        self.target_node = "BUS_FLOODER"
        self.flood_rate = 0.0001  # Extremely fast flooding
        
    def execute(self):
        """Execute bus flooding attack"""
        self.running = True
        self.manager.bus.compromised = True
        
        print(f"\n🚨 ATTACK STARTED: Bus Flooding (Priority Hijack)")
        print(f"   Target: Entire CAN bus with ID 0x000 (highest priority)")
        
        while self.running and 'bus_flooding' in self.manager.active_attacks:
            # Send highest priority message (ID 0x000) to block all other traffic
            frame = CANFrame(
                arbitration_id=0x000,  # Highest priority
                data=b'\xFF' * 8,       # Garbage data
                source="ATTACKER"
            )
            
            self.manager.stats['bus_flooding'].attempts += 1
            
            # Check if security measures block it
            blocked = False
            
            # Rate limiting would detect this
            if self.manager.security.measures['rate_limiting']:
                allowed, _, rate = self.manager.security.check_rate_limit(0x000)
                if not allowed:
                    self.manager.stats['bus_flooding'].blocked += 1
                    self.manager.stats['bus_flooding'].detected += 1
                    blocked = True
            
            # IDS would detect anomalous frequency
            if self.manager.security.measures['ids'] and not blocked:
                allowed, _, _ = self.manager.security.check_anomaly(0x000)
                if not allowed:
                    self.manager.stats['bus_flooding'].detected += 1
                    # IDS doesn't block, just detects
            
            if not blocked:
                self.bus.send(frame)
                self.manager.stats['bus_flooding'].successful += 1
                # Mark bus as compromised
                self.bus.compromised = True
            
            time.sleep(self.flood_rate)
    
    def stop(self):
        """Stop the attack"""
        self.running = False
        self.manager.bus.compromised = False
        print(f"\n✅ ATTACK STOPPED: Bus Flooding")


class SpoofingAttack:
    """
    Attack: Inject fake critical messages
    Goal: Manipulate vehicle behavior (disable brakes, unlock doors, turn off lights)
    Target: Critical ECUs (Brake, Body Control)
    """
    
    def __init__(self, bus: VirtualCANBus, attack_manager: AttackManager):
        self.bus = bus
        self.manager = attack_manager
        self.running = False
        self.target_node = "BodyECU"
        
        # Target IDs to spoof
        self.targets = {
            0x0A0: b'\x00',      # Brake pressure = 0 (CRITICAL!)
            0x300: b'\x00',      # Doors unlocked
            0x301: b'\x00'       # Lights off
        }
    
    def execute(self):
        """Execute spoofing attack"""
        self.running = True
        
        print(f"\n🚨 ATTACK STARTED: Message Spoofing")
        print(f"   Targets: Brake (0x0A0), Door Lock (0x300), Lights (0x301)")
        
        while self.running and 'spoofing' in self.manager.active_attacks:
            for arb_id, malicious_data in self.targets.items():
                frame = CANFrame(
                    arbitration_id=arb_id,
                    data=malicious_data,
                    source="ATTACKER"
                )
                
                self.manager.stats['spoofing'].attempts += 1
                blocked = False
                
                # Authentication would detect tampered messages
                if self.manager.security.measures['authentication']:
                    # Attacker can't forge valid HMAC without key
                    self.manager.stats['spoofing'].blocked += 1
                    self.manager.stats['spoofing'].detected += 1
                    blocked = True
                
                # Encryption makes it harder (but doesn't prevent injection)
                # Attacker sends unencrypted message, receivers expect encrypted
                if self.manager.security.measures['encryption'] and not blocked:
                    # Message will fail decryption at receiver
                    self.manager.stats['spoofing'].detected += 1
                    blocked = True
                
                if not blocked:
                    self.bus.send(frame)
                    self.manager.stats['spoofing'].successful += 1
                    
                    # Mark affected nodes as compromised
                    if arb_id == 0x0A0:
                        self.manager.compromised_nodes.add("BrakeECU")
                    elif arb_id in [0x300, 0x301]:
                        self.manager.compromised_nodes.add("BodyECU")
            
            time.sleep(0.05)
    
    def stop(self):
        """Stop the attack"""
        self.running = False
        self.manager.compromised_nodes.discard("BrakeECU")
        self.manager.compromised_nodes.discard("BodyECU")
        print(f"\n✅ ATTACK STOPPED: Message Spoofing")


class ReplayAttack:
    """
    Attack: Capture and replay valid messages
    Goal: Confuse ECUs with stale data, cause timing issues
    Target: Engine and Transmission data
    """
    
    def __init__(self, bus: VirtualCANBus, attack_manager: AttackManager):
        self.bus = bus
        self.manager = attack_manager
        self.running = False
        self.target_node = "EngineECU"
        
        # Captured messages (simulated)
        self.captured = {
            0x100: b'\x0B\xB8',  # RPM = 3000
            0x200: b'\x03'        # Gear = 3
        }
        
        self.replay_count = 0
    
    def execute(self):
        """Execute replay attack"""
        self.running = True
        
        print(f"\n🚨 ATTACK STARTED: Replay Attack")
        print(f"   Replaying: Engine RPM (0x100), Gear (0x200)")
        
        while self.running and 'replay' in self.manager.active_attacks:
            for arb_id, captured_data in self.captured.items():
                # Replay old message multiple times rapidly (burst)
                for _ in range(3):
                    self.manager.stats['replay'].attempts += 1
                    blocked = False
                    
                    # Check rate limiting BEFORE creating the frame
                    if self.manager.security.measures['rate_limiting']:
                        allowed, _, rate = self.manager.security.check_rate_limit(arb_id)
                        if not allowed:
                            self.manager.stats['replay'].blocked += 1
                            self.manager.stats['replay'].detected += 1
                            blocked = True
                            print(f"   [Rate Limit] BLOCKED replay on ID={arb_id:03X} (rate: {rate} msg/s)")
                    
                    # Check IDS for anomalies
                    if self.manager.security.measures['ids'] and not blocked:
                        allowed, _, _ = self.manager.security.check_anomaly(arb_id)
                        if not allowed:
                            self.manager.stats['replay'].detected += 1
                            print(f"   [IDS] DETECTED replay anomaly on ID={arb_id:03X}")
                    
                    # HMAC can't prevent replay without timestamps
                    if self.manager.security.measures['authentication'] and not blocked:
                        self.manager.stats['replay'].detected += 1
                    
                    # Only send if not blocked
                    if not blocked:
                        frame = CANFrame(
                            arbitration_id=arb_id,
                            data=captured_data,
                            source="ATTACKER"
                        )
                        self.bus.send(frame)
                        self.manager.stats['replay'].successful += 1
                        self.manager.compromised_nodes.add("EngineECU")
                    
                    time.sleep(0.001)
            
            self.replay_count += 1
            time.sleep(0.1)
    
    def stop(self):
        """Stop the attack"""
        self.running = False
        self.manager.compromised_nodes.discard("EngineECU")
        print(f"\n✅ ATTACK STOPPED: Replay Attack")


def initialize_attacks(bus: VirtualCANBus, security: SecurityManager) -> AttackManager:
    """Initialize all attacks"""
    manager = AttackManager(bus, security)
    
    # Register attacks
    manager.register_attack('bus_flooding', BusFloodingAttack(bus, manager))
    manager.register_attack('spoofing', SpoofingAttack(bus, manager))
    manager.register_attack('replay', ReplayAttack(bus, manager))
    
    return manager