from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour
import asyncio

from config import AGENTS


class BasicAgent(Agent):
    class ConnectBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"{self.agent.jid} connected successfully!")

    class MonitorBehaviour(PeriodicBehaviour):
        async def run(self):
            print(f"{self.agent.jid} monitoring environment...")

    async def setup(self):
        print(f"Starting {self.jid}...")
        self.add_behaviour(self.ConnectBehaviour())
        # Runs every 5 seconds
        self.add_behaviour(self.MonitorBehaviour(period=5))



async def main():
    sensor_jid = AGENTS["sensor"]["jid"]
    sensor_pwd = AGENTS["sensor"]["password"]

    sensor = BasicAgent(sensor_jid, sensor_pwd)
    await sensor.start(auto_register=True)

    print("Sensor agent is running. Press Ctrl+C to stop.")

    # Keep agent alive so SPADE can manage behaviours
    while sensor.is_alive():
        await asyncio.sleep(1)

asyncio.run(main())