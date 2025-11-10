import os

from charlie.schema import Variable


class VariableCollector:
    def collect(self, variables: dict[str, Variable | None]) -> dict[str, str]:
        collected: dict[str, str] = {}

        for name, definition in variables.items():
            value = self._collect_single(name, definition)
            if value is not None:
                collected[name] = value

        return collected

    def _collect_single(self, name: str, definition: Variable | None) -> str | None:
        if definition is None:
            return self._get_from_env(name)

        if definition.env:
            value = self._get_from_env(definition.env)
            if value and definition.choices:
                return self._validate_choice(value, definition.choices, definition.env)
            return value

        if definition.default:
            return definition.default

        return None

    def _get_from_env(self, var_name: str) -> str | None:
        return os.environ.get(var_name)

    def _validate_choice(self, value: str, choices: list[str], var_name: str) -> str:
        if value not in choices:
            return choices[0]
        return value
