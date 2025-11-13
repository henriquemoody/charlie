from enum import Enum


class RuleMode(Enum):
    MERGED = "merged"
    SEPARATE = "separate"


class FileFormat(Enum):
    MARKDOWN = "markdown"
    YAML = "yaml"
    TOML = "toml"


class TransportType(Enum):
    STDIO = "stdio"
    HTTP = "http"
