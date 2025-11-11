import os

from charlie.schema import VariableSpec


class VariableCollector:
    def collect(self, variables: dict[str, VariableSpec | None]) -> dict[str, str]:
        collected: dict[str, str] = {}

        for name, definition in variables.items():
            collected[name] = self._collect_single(name, definition)

        return collected

    def _collect_single(self, name: str, spec: VariableSpec | None) -> str:
        value = None
        if spec and spec.env:
            value = os.environ.get(spec.env)

        if not value and spec and spec.default:
            value = spec.default

        if not value:
            prompt = f"Enter value for {name}"
            if spec and spec.choices:
                prompt += f" (choices: {', '.join(spec.choices)})"
            value = input(prompt + ": ")

        if spec and spec.choices and value not in spec.choices:
            raise ValueError(f"Invalid choice: {value}")

        return value
