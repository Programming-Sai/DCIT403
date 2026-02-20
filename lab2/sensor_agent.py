import asyncio
import logging
import signal
import sys
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from lab2.environment import generate_sensor_data
from config import AGENTS
import json
from spade.message import Message

# Setup logging
logging.basicConfig(
    filename="sensor_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class SensorAgent(Agent):
    class SenseBehaviour(PeriodicBehaviour):
        async def run(self):
            try:
                # Generate sensor data with dormancy bias (0.8 for realistic dormancy)
                data = generate_sensor_data(dormancy_bias=0.75)
                # Print to console
                print(f"[{self.agent.jid}] Sensor reading: {data}")
                # Log to file
                logging.info(f"{self.agent.jid} - {data}")
                msg = Message(
                    to=AGENTS["coordinator"]["jid"],
                    sender=str(self.agent.jid),  # Explicitly set the sender
                    body=json.dumps(data)
                )
                msg.set_metadata("performative", "inform")
                msg.body = json.dumps(data)

                print(f"[{self.agent.jid}] Sending {msg} to {AGENTS['coordinator']['jid']}")
                await self.send(msg)
                print(f"[{self.agent.jid}] Message sent")
            except Exception as e:
                logging.error(f"Error in sensor reading: {e}")
                print(f"Error reading sensor: {e}")

        async def on_end(self):
            print(f"Behaviour {self.name} has finished.")

    async def setup(self):
        print(f"Starting {self.jid}...")
        # Run SenseBehaviour every 5 seconds
        behaviour = self.SenseBehaviour(period=5)
        self.add_behaviour(behaviour)

    async def shutdown(self):
        print(f"Shutting down {self.jid}...")
        await self.stop()
        print(f"{self.jid} has been stopped.")

async def main():
    # Get agent credentials
    try:
        sensor_jid = AGENTS["sensor"]["jid"]
        sensor_pwd = AGENTS["sensor"]["password"]
    except KeyError as e:
        print(f"Configuration error: Missing {e} in AGENTS dictionary")
        return

    # Create agent
    sensor_agent = SensorAgent(sensor_jid, sensor_pwd)
    
    # Create shutdown event
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        print("\nReceived shutdown signal...")
        shutdown_event.set()
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows fallback
            pass

    try:
        await sensor_agent.start(auto_register=True)
        print(f"Agent {sensor_jid} started successfully.")
        print("Sensor agent is running. Press Ctrl+C to stop.")

        # Wait for shutdown signal
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Shutting down gracefully...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error(f"Unexpected error in main: {e}")
    finally:
        # Graceful shutdown without task cancellation
        print("Initiating graceful shutdown...")
        await sensor_agent.shutdown()
        print("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")
        sys.exit(1)