# CAN Bus Simulation Configuration

# ==================== CAN BUS SETTINGS ====================

# CAN bus bitrate (bits per second)
CAN_BITRATE = 500_000  # 500 kbps (standard automotive)

# CAN frame length in bits
CAN_FRAME_LENGTH = 128  # Classical CAN with 8-byte payload

# ==================== SECURITY SETTINGS ====================

# AES encryption
AES_KEY_SIZE = 16  # 128-bit AES

# HMAC authentication
HMAC_KEY_SIZE = 32  # 256-bit key for SHA-256

# Rate limiting
RATE_LIMIT_THRESHOLD = 50  # Max messages per ID per second
RATE_LIMIT_WINDOW = 1.0    # Time window in seconds

# IDS (Intrusion Detection System)
IDS_LEARNING_TIME = 2.0         # Seconds to learn baseline
IDS_ANOMALY_MULTIPLIER = 3      # Alert if frequency is 3x baseline
IDS_MINIMUM_SAMPLES = 20        # Min samples before baseline established

# ==================== LATENCY THRESHOLDS ====================

# Critical systems (milliseconds)
LATENCY_CRITICAL = 10    # Brakes, Airbags
LATENCY_SAFETY = 20      # Steering, ABS
LATENCY_NORMAL = 100     # Telemetry, Body controls

# CAN IDs for critical systems
CRITICAL_IDS = {0x0A0, 0x0A1}    # Brakes
SAFETY_IDS = {0x0C0, 0x0C1}      # Steering, ABS
NORMAL_IDS = {0x100, 0x101, 0x200, 0x300, 0x301}  # Others

# ==================== ECU CONFIGURATION ====================

# ECU message intervals (seconds)
ENGINE_ECU_INTERVAL = 0.05      # 20 Hz (RPM, temperature)
BRAKE_ECU_INTERVAL = 0.01       # 100 Hz (critical timing)
TRANSMISSION_ECU_INTERVAL = 0.08  # 12.5 Hz (gear position)
BODY_ECU_INTERVAL = 0.1         # 10 Hz (doors, lights)

# ==================== CAN MESSAGE IDs ====================

# Engine Control
ID_ENGINE_RPM = 0x100
ID_ENGINE_TEMP = 0x101

# Brake System (CRITICAL)
ID_BRAKE_PRESSURE = 0x0A0
ID_BRAKE_STATUS = 0x0A1

# Transmission
ID_GEAR_POSITION = 0x200

# Body Control
ID_DOOR_LOCKS = 0x300
ID_LIGHTS = 0x301

# Steering & ABS (SAFETY)
ID_STEERING_ANGLE = 0x0C0
ID_ABS_STATUS = 0x0C1

# OBD-II Diagnostics
ID_OBD_REQUEST = 0x7DF
ID_OBD_RESPONSE = 0x7E8

# ==================== ATTACK SETTINGS ====================

# Bus Flooding Attack
FLOOD_ATTACK_ID = 0x000         # Highest priority
FLOOD_ATTACK_RATE = 0.0001      # 10,000 messages/sec
FLOOD_ATTACK_DATA = b'\xFF' * 8  # Garbage data

# Spoofing Attack
SPOOF_TARGETS = {
    ID_BRAKE_PRESSURE: b'\x00',  # Disable brakes (CRITICAL!)
    ID_DOOR_LOCKS: b'\x00',      # Unlock doors
    ID_LIGHTS: b'\x00'           # Turn off lights
}
SPOOF_INTERVAL = 0.05  # Seconds between spoofed messages

# Replay Attack
REPLAY_TARGETS = {
    ID_ENGINE_RPM: b'\x0B\xB8',  # 3000 RPM
    ID_GEAR_POSITION: b'\x03'     # 3rd gear
}
REPLAY_BURST_COUNT = 3    # Replay each message 3 times
REPLAY_BURST_DELAY = 0.001  # 1ms between replays
REPLAY_INTERVAL = 0.1       # Seconds between bursts

# ==================== WEBSOCKET SERVER ====================

WEBSOCKET_HOST = 'localhost'
WEBSOCKET_PORT = 8765
UPDATE_INTERVAL = 0.1  # 100ms update frequency (10 Hz)

# ==================== LOGGING & MONITORING ====================

# History lengths (number of samples to keep)
LATENCY_HISTORY_SIZE = 1000
SECURITY_OVERHEAD_HISTORY_SIZE = 1000

# Attack event log retention
ATTACK_EVENT_RETENTION = 10  # Seconds

# CSV log filename
LATENCY_LOG_FILE = 'latency_log.csv'

# ==================== SIMULATION SETTINGS ====================

# Simulation duration (seconds) if running standalone
SIMULATION_DURATION = 10

# Retry mechanism for lost messages
ACK_TIMEOUT = 0.02      # 20ms timeout
MAX_RETRIES = 3         # Retry up to 3 times

# ==================== ADVANCED SECURITY ====================

# Enable/disable security measures by default
DEFAULT_SECURITY_STATE = {
    'encryption': False,
    'authentication': False,
    'rate_limiting': False,
    'ids': False
}

# Simulated crypto processing delays (seconds)
ENCRYPTION_DELAY = 0.0005   # 0.5ms per encryption
DECRYPTION_DELAY = 0.0005   # 0.5ms per decryption
HMAC_SIGN_DELAY = 0.0003    # 0.3ms per HMAC generation
HMAC_VERIFY_DELAY = 0.0003  # 0.3ms per HMAC verification

# ==================== DATASET IMPORT (FUTURE) ====================

# CSV format for attack dataset
ATTACK_DATASET_FORMAT = {
    'columns': ['timestamp', 'attack_type', 'target_id', 'data'],
    'delimiter': ',',
    'header': True
}

# ==================== COLOR CODING (for visualization) ====================

HEALTH_COLORS = {
    'healthy': '#10B981',    # Green
    'warning': '#F59E0B',    # Yellow
    'compromised': '#EF4444' # Red
}

ATTACK_COLORS = {
    'bus_flooding': '#DC2626',  # Red
    'spoofing': '#EA580C',       # Orange
    'replay': '#D97706'          # Amber
}

# ==================== HELPER FUNCTIONS ====================

def get_threshold_for_id(arb_id):
    """Get latency threshold for a given CAN ID"""
    if arb_id in CRITICAL_IDS:
        return LATENCY_CRITICAL
    elif arb_id in SAFETY_IDS:
        return LATENCY_SAFETY
    else:
        return LATENCY_NORMAL

def get_system_name(arb_id):
    """Get human-readable system name for CAN ID"""
    system_map = {
        ID_ENGINE_RPM: "Engine RPM",
        ID_ENGINE_TEMP: "Engine Temperature",
        ID_BRAKE_PRESSURE: "Brake Pressure (CRITICAL)",
        ID_BRAKE_STATUS: "Brake Status (CRITICAL)",
        ID_GEAR_POSITION: "Transmission Gear",
        ID_DOOR_LOCKS: "Door Locks",
        ID_LIGHTS: "Headlights/Taillights",
        ID_STEERING_ANGLE: "Steering Angle (SAFETY)",
        ID_ABS_STATUS: "ABS Status (SAFETY)",
        ID_OBD_REQUEST: "OBD-II Request",
        ID_OBD_RESPONSE: "OBD-II Response"
    }
    return system_map.get(arb_id, f"Unknown ID (0x{arb_id:03X})")

# ==================== VALIDATION ====================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check bitrate
    if CAN_BITRATE not in [125_000, 250_000, 500_000, 1_000_000]:
        errors.append(f"Unusual CAN bitrate: {CAN_BITRATE} (common: 125k, 250k, 500k, 1M)")
    
    # Check latency thresholds
    if LATENCY_CRITICAL >= LATENCY_SAFETY:
        errors.append("LATENCY_CRITICAL must be < LATENCY_SAFETY")
    
    if LATENCY_SAFETY >= LATENCY_NORMAL:
        errors.append("LATENCY_SAFETY must be < LATENCY_NORMAL")
    
    # Check update interval
    if UPDATE_INTERVAL < 0.05:
        errors.append("UPDATE_INTERVAL too fast (<50ms), may overload WebSocket")
    
    # Check rate limit
    if RATE_LIMIT_THRESHOLD < 10:
        errors.append("RATE_LIMIT_THRESHOLD too strict (<10/sec), may block legitimate traffic")
    
    return errors

# Run validation on import
_validation_errors = validate_config()
if _validation_errors:
    print("⚠️  Configuration Warnings:")
    for error in _validation_errors:
        print(f"   - {error}")