import asyncio
import json
import websockets
import threading
import time
from can_bus_simulation import CANSimulation
from can_bus_attacks import initialize_attacks


class CANWebSocketServer:
    """WebSocket server for real-time CAN simulation data"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        
        # Initialize simulation
        self.simulation = CANSimulation()
        self.attack_manager = initialize_attacks(
            self.simulation.bus, 
            self.simulation.security
        )
        
        self.running = False
        self.update_interval = 0.1  # 100ms updates
    
    async def register(self, websocket):
        """Register new client"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial state
        await self.send_state_update(websocket)
    
    async def unregister(self, websocket):
        """Unregister client"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def send_state_update(self, websocket=None):
        """Send simulation state to client(s)"""
        state = self.get_full_state()
        message = json.dumps(state)
        
        if websocket:
            await websocket.send(message)
        else:
            # Broadcast to all clients
            if self.clients:
                await asyncio.gather(
                    *[client.send(message) for client in self.clients],
                    return_exceptions=True
                )
    
    def get_full_state(self) -> dict:
        """Get complete simulation state"""
        sim_state = self.simulation.get_state()
        attack_state = self.attack_manager.get_status()
        
        # Collect latency data from all controllers
        latency_data = []
        for ctrl in self.simulation.controllers:
            if ctrl.latency_history:
                latency_data.extend([
                    {
                        'controller': ctrl.name,
                        'latency': lat,
                        'time': time.time()
                    }
                    for lat in list(ctrl.latency_history)[-10:]  # Last 10 samples
                ])
        
        # Get security overhead
        security_overhead = {
            measure: overhead * 1000  # Convert to ms
            for measure, overhead in sim_state['security_overhead'].items()
        }
        
        # Calculate average actual latency from recent messages (from the graph)
        recent_latencies = []
        for ctrl in self.simulation.controllers:
            if ctrl.latency_history:
                recent_latencies.extend(list(ctrl.latency_history)[-50:])
        
        # This is the ACTUAL overhead shown in the graph
        avg_actual_latency = sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0
        
        # Use the measured latency as total overhead (this is what's shown in graph)
        total_overhead = avg_actual_latency
        
        # Determine latency warnings
        warnings = []
        if total_overhead > 10:
            warnings.append({
                'level': 'critical',
                'message': f'Critical latency: {total_overhead:.2f}ms exceeds safe threshold for brakes/airbags (<10ms)',
                'system': 'Brakes, Airbags'
            })
        elif total_overhead > 20:
            warnings.append({
                'level': 'warning',
                'message': f'High latency: {total_overhead:.2f}ms may affect steering/ABS (<20ms)',
                'system': 'Steering, ABS'
            })
        
        return {
            'timestamp': time.time(),
            'simulation': sim_state,
            'attacks': attack_state,
            'latency_data': latency_data,
            'security_overhead': security_overhead,
            'total_overhead': total_overhead,
            'avg_actual_latency': avg_actual_latency,
            'warnings': warnings
        }
    
    async def handle_command(self, websocket, message):
        """Handle commands from client"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            response = {'success': False, 'message': 'Unknown command'}
            
            if command == 'toggle_security':
                measure = data.get('measure')
                enabled = data.get('enabled')
                success = self.simulation.toggle_security(measure, enabled)
                response = {
                    'success': success,
                    'message': f"Security measure '{measure}' {'enabled' if enabled else 'disabled'}"
                }
            
            elif command == 'start_attack':
                attack_name = data.get('attack')
                success = self.attack_manager.start_attack(attack_name)
                response = {
                    'success': success,
                    'message': f"Attack '{attack_name}' started" if success else f"Failed to start '{attack_name}'"
                }
            
            elif command == 'stop_attack':
                attack_name = data.get('attack')
                success = self.attack_manager.stop_attack(attack_name)
                response = {
                    'success': success,
                    'message': f"Attack '{attack_name}' stopped" if success else f"Failed to stop '{attack_name}'"
                }
            
            elif command == 'get_state':
                # Send full state
                await self.send_state_update(websocket)
                return
            
            # Send response
            await websocket.send(json.dumps(response))
            
            # Send updated state
            await self.send_state_update(websocket)
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'success': False,
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                'success': False,
                'message': f'Error: {str(e)}'
            }))
    
    async def client_handler(self, websocket):
        """Handle WebSocket client connection"""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                await self.handle_command(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def broadcast_updates(self):
        """Periodically broadcast state updates"""
        while self.running:
            await self.send_state_update()
            await asyncio.sleep(self.update_interval)
    
    def start_simulation(self):
        """Start CAN simulation in background thread"""
        self.simulation.start()
        print("✅ CAN Simulation started")
    
    async def start_server(self):
        """Start WebSocket server"""
        self.running = True
        
        # Start simulation
        self.start_simulation()
        
        # Start WebSocket server
        print(f"🚀 WebSocket server starting on ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.client_handler, self.host, self.port):
            # Start broadcast task
            broadcast_task = asyncio.create_task(self.broadcast_updates())
            
            print(f"✅ Server ready! Connect from frontend at ws://{self.host}:{self.port}")
            print(f"📊 Broadcasting updates every {self.update_interval*1000}ms")
            
            # Keep server running
            await asyncio.Future()  # Run forever
    
    def stop(self):
        """Stop server and simulation"""
        self.running = False
        self.simulation.stop()


def main():
    """Main entry point"""
    server = CANWebSocketServer(host='localhost', port=8765)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop()


if __name__ == "__main__":
    main()