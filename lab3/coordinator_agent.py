import asyncio
import json
import logging
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, CyclicBehaviour
from spade.message import Message
from config import AGENTS

# Setup logging for coordinator
logging.basicConfig(
    filename="coordinator_logs.log",
    level=logging.INFO,
    format="%(asctime)s | COORDINATOR | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ----------- STATES --------------

class MonitoringState(State):
    async def run(self):
        print("[Coordinator] State: MONITORING")
        logging.info("Entered MONITORING state")
        
        # Wait for a message with a timeout
        msg = await self.receive(timeout=2)
        
        if msg:
            logging.info(f"Received message from {msg.sender}: {msg.body}")
            try:
                data = json.loads(msg.body)
                print(f"[Coordinator] Sensor data received: {data}")
                logging.info(f"Sensor data parsed: {data}")
                
                # Store the data in the agent's memory for later use
                self.agent.last_sensor_data = data
                
                if data.get("emergency"):
                    print("[Coordinator] Emergency detected!")
                    logging.warning(f"EMERGENCY DETECTED in sensor data: {data}")
                    self.set_next_state("ALERT")
                else:
                    # Stay in monitoring state
                    logging.info("No emergency detected, continuing monitoring")
                    self.set_next_state("MONITORING")
                    
            except Exception as e:
                print(f"[Coordinator] Error processing message: {e}")
                logging.error(f"Error processing message: {e}")
                self.set_next_state("MONITORING")
        else:
            # Timeout, stay in monitoring
            logging.debug("No message received (timeout)")
            self.set_next_state("MONITORING")

class AlertState(State):
    async def run(self):
        print("[Coordinator] State: ALERT")
        logging.info("Entered ALERT state")
        print("[Coordinator] Preparing rescue deployment...")
        logging.info("Preparing rescue deployment")
        
        # Use the stored sensor data if available
        if hasattr(self.agent, 'last_sensor_data'):
            data = self.agent.last_sensor_data
            print(f"[Coordinator] Deploying based on data: {data}")
            logging.info(f"Deploying based on sensor data: {data}")
        
        await asyncio.sleep(1)
        logging.info("Alert state complete, transitioning to RESPONDING")
        self.set_next_state("RESPONDING")

class RespondingState(State):
    async def run(self):
        print("[Coordinator] State: RESPONDING")
        logging.info("Entered RESPONDING state")
        
        # Get the latest sensor data to send to rescue
        data = getattr(self.agent, 'last_sensor_data', {})
        print(f"[Coordinator] Using sensor data: {data}")
        logging.info(f"Using sensor data for rescue request: {data}")
        
        # Include all sensor data in the payload
        payload = {
            "action": "deploy",
            "emergency": data.get("emergency", True),
            "area_affected_km2": data.get("area_affected_km2", 0),
            "population_risk": data.get("population_risk", 0),
            "lava_flow_m3_s": data.get("lava_flow_m3_s", 0),
            "status": data.get("status", "unknown")
        }
        
        # Create message properly
        msg = Message(
            to=AGENTS["rescue"]["jid"],
            sender=str(self.agent.jid),
            body=json.dumps(payload)
        )
        msg.set_metadata("performative", "request")
        
        # Debug output
        print(f"[Coordinator] Sending to rescue agent at {AGENTS['rescue']['jid']}")
        print(f"[Coordinator] Message body: {msg.body}")
        print(f"[Coordinator] Message metadata: {msg.metadata}")
        logging.info(f"Sending rescue request to {AGENTS['rescue']['jid']}")
        logging.info(f"Request payload: {payload}")
        
        await self.send(msg)
        print("[Coordinator] Rescue request sent with data:", payload)
        logging.info("Rescue request sent")

        # Wait for confirmation with timeout
        print("[Coordinator] Waiting for rescue confirmation...")
        logging.info("Waiting for rescue confirmation (timeout=15s)")
        reply = await self.receive(timeout=15)
        
        if reply:
            print(f"[Coordinator] Got reply from {reply.sender}")
            print(f"[Coordinator] Reply body: {reply.body}")
            logging.info(f"Received reply from {reply.sender}: {reply.body}")
            try:
                result = json.loads(reply.body)
                print(f"[Coordinator] Rescue completed: {result}")
                logging.info(f"Rescue completed successfully: {result}")
                # Store the result for recovery state
                self.agent.last_rescue_result = result
            except Exception as e:
                print(f"[Coordinator] Error parsing confirmation: {e}")
                print(f"[Coordinator] Raw reply: {reply.body}")
                logging.error(f"Error parsing rescue confirmation: {e}")
                logging.error(f"Raw reply: {reply.body}")
        else:
            print("[Coordinator] No rescue confirmation received (timeout)")
            logging.warning("No rescue confirmation received (timeout)")
            
        logging.info("Responding state complete, transitioning to RECOVERY")
        self.set_next_state("RECOVERY")


class RecoveryState(State):
    async def run(self):
        print("[Coordinator] State: RECOVERY")
        logging.info("Entered RECOVERY state")
        
        # Show rescue result if available
        if hasattr(self.agent, 'last_rescue_result'):
            result = self.agent.last_rescue_result
            print(f"[Coordinator] Recovery from rescue: {result}")
            logging.info(f"Recovery phase with rescue result: {result}")
            
        print("[Coordinator] System stabilizing...")
        logging.info("System stabilization in progress")
        await asyncio.sleep(2)
        
        # Clear old data
        if hasattr(self.agent, 'last_rescue_result'):
            delattr(self.agent, 'last_rescue_result')
            logging.info("Cleared last rescue result data")
            
        logging.info("Recovery complete, transitioning to MONITORING")
        self.set_next_state("MONITORING")

# ----------- AGENT --------------

class CoordinatorAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.last_sensor_data = None  # Store last sensor reading
        
    async def setup(self):
        print(f"[{self.jid}] CoordinatorAgent starting...")
        logging.info(f"CoordinatorAgent starting with JID: {self.jid}")
        print(f"[{self.jid}] Connected: {self.is_alive()}")
        logging.info(f"Connection status: {self.is_alive()}")
        
        # Add debug behaviour
        class DebugBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=1)
                if msg:
                    print(f"\n*** DEBUG: GOT MESSAGE ***")
                    print(f"From: {msg.sender}")
                    print(f"To: {msg.to}")
                    print(f"Body: {msg.body}")
                    print(f"Metadata: {msg.metadata}")
                    print("***************************\n")
                    logging.debug(f"Debug behaviour caught message from {msg.sender}: {msg.body}")
        
        self.add_behaviour(DebugBehaviour())
        logging.info("Debug behaviour added")
        
        # Your FSM
        fsm = FSMBehaviour()
        fsm.add_state(name="MONITORING", state=MonitoringState(), initial=True)
        fsm.add_state(name="ALERT", state=AlertState())
        fsm.add_state(name="RESPONDING", state=RespondingState())
        fsm.add_state(name="RECOVERY", state=RecoveryState())
        
        fsm.add_transition("MONITORING", "ALERT")
        fsm.add_transition("MONITORING", "MONITORING")
        fsm.add_transition("ALERT", "RESPONDING")
        fsm.add_transition("RESPONDING", "RECOVERY")
        fsm.add_transition("RECOVERY", "MONITORING")
        
        self.add_behaviour(fsm)
        logging.info("FSM behaviour added with all states and transitions")
        logging.info("CoordinatorAgent setup complete")

    async def shutdown(self):
        logging.info("CoordinatorAgent shutting down")
        await self.stop()

# ----------- MAIN --------------

async def main():
    logging.info("=== Coordinator Agent Starting ===")
    coord = CoordinatorAgent(
        AGENTS["coordinator"]["jid"],
        AGENTS["coordinator"]["password"]
    )
    
    try:
        await coord.start(auto_register=True)
        print("Coordinator running...")
        logging.info(f"Coordinator agent started with JID: {AGENTS['coordinator']['jid']}")
        logging.info(f"Connected status: {coord.is_alive()}")
        
        # Keep the agent alive
        while coord.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Coordinator stopping...")
        logging.info("Coordinator agent stopped by user")
        await coord.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error in main loop: {e}")
        await coord.shutdown()
    finally:
        logging.info("=== Coordinator Agent Shutdown ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        logging.info("Program interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")