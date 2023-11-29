import logging
from langchain.llms import Ollama
from abc import ABC, abstractmethod

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from speak_practice.utils import StdOutHandler


class BaseChatAssistant(ABC):
    def __init__(self):
        self.model = None
        self.conversation_memory = None

    @staticmethod
    def _create_prompt(template: str,
                       use_memory: bool = False) -> ChatPromptTemplate:
        messages = [SystemMessagePromptTemplate.from_template(template), ]
        if use_memory:
            messages += [
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{inputs}"),
            ]
        return ChatPromptTemplate(messages=messages)

    def _create_chain(self, prompt: ChatPromptTemplate,
                      use_memory: bool = False,
                      model: ChatOpenAI = None) -> LLMChain:
        if model is None:
            model = self.model
        chain = LLMChain(llm=model, prompt=prompt)
        if use_memory:
            chain = LLMChain(llm=model, prompt=prompt,
                             memory=self.conversation_memory)
        return chain

    @abstractmethod
    def _init_model(self) -> None:
        ...

    @abstractmethod
    def _init_memory(self) -> None:
        ...

    @abstractmethod
    def _init_chains(self) -> None:
        ...

    @abstractmethod
    def _init_prompts(self) -> None:
        ...


class TalkAssistant(BaseChatAssistant):
    @property
    def logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(StdOutHandler)
        logger.setLevel(logging.DEBUG)
        return logger

    def __init__(self):
        super().__init__()

        self._init_model()
        self._init_memory()
        self._init_prompts()
        self._init_chains()

    def _init_model(self) -> None:
        self.model = Ollama(base_url="http://llm:11434", model="mistral:7b-instruct", temperature=0.0)
        HISTORY_LENGTH = 10

    def _init_memory(self):
        self.conversation_memory = ConversationBufferWindowMemory(
            ai_prefix='task_assist',
            human_prefix='User',
            llm=self.model,
            memory_key="chat_history",
            input_key='inputs',
            return_messages=True,
            max_token_limit=10
        )

    def _init_prompts(self) -> None:
        self.talk_prompt = self._create_prompt(
            """
            Your name is Aola. You are a storyteller.
            Speak with user friendly with pleasure, joy and emoji.
            DONT PRESENT YOURSELF. Say that you start a search and you can discuss something interesting with the user or tell a story. 
            Ask any question.
            DONT USE MORE THAN 15 words.

            {inputs}

            """, True
        )

    def _init_chains(self) -> None:
        self.talk_chain = self._create_chain(self.talk_prompt, True)

