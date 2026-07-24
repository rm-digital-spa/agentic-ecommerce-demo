import logging
import re
from logging import Logger
from typing import Any, Optional

from strands.hooks import (
    AfterInvocationEvent,
    AgentInitializedEvent,
    BeforeInvocationEvent,
    HookProvider,
    HookRegistry,
)


class LoggingHook(HookProvider):
    def __init__(self, name: str, logger: Optional[Logger] = None):
        if not logger:
            self.__init__logger()

        self._logger.info(f"Initializing LoogingHook with name: {name}")
        self._name = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeInvocationEvent, self.log_start)
        registry.add_callback(AfterInvocationEvent, self.log_end)

    def log_start(self, event: BeforeInvocationEvent) -> None:
        self._logger.info(
            f"[{self._name}-logger]: BeforeInvocationEvent captured for {event.agent.name}"
        )

    def log_end(self, event: AfterInvocationEvent) -> None:
        self._logger.info(
            f"[{self._name}-logger]: AfterInvocationEvent captured for {event.agent.name}"
        )

    def __init__logger(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        self._logger = logger


class NamedAgentHook(HookProvider):
    def __init__(self, name: str):
        self._name = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(AgentInitializedEvent, self.set_agent_name)

    def set_agent_name(self, event: AgentInitializedEvent) -> None:
        event.agent.name = self._name
