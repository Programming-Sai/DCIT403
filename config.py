from dotenv import load_dotenv
import os

load_dotenv()  # reads the .env file

AGENTS = {
    "sensor": {"jid": os.getenv("SENSOR_JID"), "password": os.getenv("SENSOR_PASSWORD")},
    "rescue": {"jid": os.getenv("RESCUE_JID"), "password": os.getenv("RESCUE_PASSWORD")},
    "logistics": {"jid": os.getenv("LOGISTICS_JID"), "password": os.getenv("LOGISTICS_PASSWORD")},
    "coordinator": {"jid": os.getenv("COORDINATOR_JID"), "password": os.getenv("COORDINATOR_PASSWORD")},
    "sender": {"jid": os.getenv("SENDER_JID"), "password": os.getenv("SENDER_PASSWORD")},
    "receiver": {"jid": os.getenv("RECEIVER_JID"), "password": os.getenv("RECEIVER_PASSWORD")},
}