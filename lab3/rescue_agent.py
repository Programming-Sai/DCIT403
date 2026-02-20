# lab3/rescue_agent.py
import asyncio
import json
import logging
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from config import AGENTS

# Simple logging setup for rescue agent
logging.basicConfig(
    filename="rescue_logs.log",
    level=logging.INFO,
    format="%(asctime)s | RESCUE | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class RescueAgent(Agent):
    class ListenBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)  # Shorter timeout for debugging
            if not msg:
                return  # no message this cycle

            print(f"\n*** RESCUE: MESSAGE RECEIVED ***")
            print(f"From: {msg.sender}")
            print(f"To: {msg.to}")
            print(f"Body: {msg.body}")
            print(f"Metadata: {msg.metadata}")
            print(f"**********************************\n")
            
            logging.info(f"Received raw message from {msg.sender}: {msg.body}")
            print(f"[{self.agent.jid}] Message received from {msg.sender}")

            try:
                payload = json.loads(msg.body)
                print(f"[{self.agent.jid}] Successfully parsed payload: {payload}")
            except Exception as e:
                print(f"[{self.agent.jid}] Failed to parse message body: {e}")
                logging.error(f"Failed to parse message body: {e}")
                return

            # Expected keys: action (e.g. "deploy"), emergency (bool), area_affected_km2 (float),
            # population_risk (0-10), lava_flow_m3_s (float)
            action = payload.get("action", "respond")
            emergency = bool(payload.get("emergency", False))
            area = float(payload.get("area_affected_km2", 0.0))
            pop_risk = float(payload.get("population_risk", 0.0))
            lava = float(payload.get("lava_flow_m3_s", 0.0))

            print(f"[{self.agent.jid}] Parsed values: action={action}, emergency={emergency}, area={area}, pop_risk={pop_risk}, lava={lava}")
            logging.info(f"Parsed payload: action={action}, emergency={emergency}, area={area}, pop_risk={pop_risk}, lava={lava}")

            # Decide response intensity (simple heuristic)
            base_time = 2
            time_from_area = int(area / 5)
            time_from_pop = int(pop_risk / 2)
            time_from_lava = int(min(lava / 100, 10))

            task_time = max(base_time, base_time + time_from_area + time_from_pop + time_from_lava)

            print(f"[{self.agent.jid}] Computed task time: {task_time}s")
            logging.info(f"Computed task_time={task_time}s for payload; starting task...")
            print(f"[{self.agent.jid}] Deploying response (simulated {task_time}s)...")

            # Simulate doing the rescue work
            try:
                await asyncio.sleep(task_time)
            except asyncio.CancelledError:
                logging.warning("Rescue task cancelled")
                return

            # Compose result
            result = {
                "result": "completed",
                "agent": str(self.agent.jid),
                "task_time_s": task_time,
                "handled_area_km2": area,
                "population_risk": pop_risk,
                "lava_flow_m3_s": lava
            }

            logging.info(f"Task complete: {result}")
            print(f"[{self.agent.jid}] Task complete, sending confirmation to {msg.sender}")

            # Reply to sender (coordinator)
            reply = Message(
                to=str(msg.sender),
                sender=str(self.agent.jid),
                body=json.dumps(result)
            )
            reply.set_metadata("performative", "inform")
            
            print(f"[{self.agent.jid}] Sending confirmation: {reply.body}")
            await self.send(reply)
            print(f"[{self.agent.jid}] Confirmation sent")
            logging.info(f"Sent completion inform to {msg.sender}")

    async def setup(self):
        print(f"[{self.jid}] RescueAgent starting...")
        print(f"[{self.jid}] Connected: {self.is_alive()}")
        print(f"[{self.jid}] Waiting for messages...")
        logging.info("RescueAgent starting")
        self.add_behaviour(self.ListenBehaviour())

    async def shutdown(self):
        logging.info("RescueAgent shutting down")
        await self.stop()

async def main():
    jid = AGENTS["rescue"]["jid"]
    pwd = AGENTS["rescue"]["password"]
    print(f"Starting rescue agent with JID: {jid}")
    agent = RescueAgent(jid, pwd)
    
    try:
        await agent.start(auto_register=True)
        print(f"Rescue agent {jid} started. Connected: {agent.is_alive()}")
        print("Waiting for tasks...")

        # keep alive until interrupted
        while agent.is_alive():
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error starting rescue agent: {e}")
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Rescue agent stopped by user")