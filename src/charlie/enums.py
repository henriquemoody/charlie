from enum import Enum


class ScriptType(Enum):
    SH = "sh"
    PS = "ps"


class RulesMode(Enum):
    MERGED = "merged"
    SEPARATE = "separate"


class FileFormat(Enum):
    MARKDOWN = "markdown"
    YAML = "yaml"
