from importlib.metadata import version

__version__ = version("charlie-agents")

from charlie.agent_registry import AgentRegistry
from charlie.configurators import AgentConfigurator, AgentConfiguratorFactory
from charlie.placeholder_transformer import PlaceholderTransformer
from charlie.tracker import Tracker
from charlie.variable_collector import VariableCollector

__all__ = [
    "AgentConfigurator",
    "AgentConfiguratorFactory",
    "AgentRegistry",
    "PlaceholderTransformer",
    "Tracker",
    "VariableCollector",
    "__version__",
]
