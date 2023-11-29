from typing import Dict, Any, Optional

from speak_practice.speak_assistant import BaseChatAssistant, TalkAssistant
from speak_practice.utils import get_logger

from dataclasses import dataclass


logger = get_logger(__name__)


@dataclass
class ConversationYieldObject:
    text: str
    is_the_end: bool = False


class AssistantBackend:
    def __init__(self):
        self.HISTORY_MINUTES: int = 5
        self.RECONNECT_SOCKET_HISTORY_DEPTH: int = 8
        self.tg_user: Optional[Dict[str, Any]] = None
        self.user_id: Optional[int] = None
        self.logger = None
        self.assistant: Optional[BaseChatAssistant] = None

    async def main_loop(self, message_txt: str, tg_user: Dict[str, Any]):
        self.tg_user = tg_user
        if self.assistant is None:
            self.user_id = self.tg_user["id"]
            self.logger = get_logger(f"AssistantBackend ({self.user_id})")
            self.assistant = TalkAssistant()
        self.logger.info(f"user message: {message_txt}")

        response = await self.assistant.talk_chain.arun(message_txt)

        logger.info(response)
        yield ConversationYieldObject(text=response, is_the_end=True)
