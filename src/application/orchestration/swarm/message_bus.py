import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class TypedMessage(BaseModel):
    msg_id: str
    msg_type: str  # PROPOSAL, OBSERVATION, REQUEST, RESPONSE, DELEGATION, ARBITRATION, BROADCAST
    sender_id: str
    recipient_id: str  # Specific agent ID or "BROADCAST"
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    timestamp: float = Field(default_factory=time.time)


class SwarmMessageBus:
    """
    Cross-Agent Communication Message Bus.
    Supports typed messages, priority routing, delegation, arbitration, and broadcast.
    """

    def __init__(self):
        self.message_inbox: Dict[str, List[TypedMessage]] = {}
        self.delivered_messages: List[TypedMessage] = []

    def send_message(self, msg: TypedMessage) -> None:
        self.delivered_messages.append(msg)
        if msg.recipient_id == "BROADCAST":
            for agent_id in self.message_inbox:
                self.message_inbox[agent_id].append(msg)
        else:
            if msg.recipient_id not in self.message_inbox:
                self.message_inbox[msg.recipient_id] = []
            self.message_inbox[msg.recipient_id].append(msg)

    def fetch_messages(self, agent_id: str) -> List[TypedMessage]:
        msgs = self.message_inbox.get(agent_id, [])
        self.message_inbox[agent_id] = []
        return msgs
