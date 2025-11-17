from abc import ABC, abstractmethod

from charlie.enums import RuleMode
from charlie.schema import Command, MCPServer, Rule


class AgentConfigurator(ABC):
    @abstractmethod
    def commands(self, commands: list[Command]) -> None:
        pass

    @abstractmethod
    def rules(self, rules: list[Rule], mode: RuleMode) -> None:
        pass

    @abstractmethod
    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        pass

    @abstractmethod
    def assets(self, assets: list[str]) -> None:
        pass

    @abstractmethod
    def ignore_file(self, patterns: list[str]) -> None:
        pass
