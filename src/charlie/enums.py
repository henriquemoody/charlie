from enum import Enum


class RuleMode(Enum):
    MERGED = "merged"
    SEPARATE = "separate"


class TransportType(Enum):
    STDIO = "stdio"
    HTTP = "http"
