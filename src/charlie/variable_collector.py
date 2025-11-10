"""Variable collection from environment and user input."""

import os

from charlie.schema import Variable


class VariableCollector:
    """Collects variable values from environment or user input.

    Follows Command-Query Separation:
    - collect() is a query (returns values without side effects)
    """

    def collect(self, variables: dict[str, Variable | None]) -> dict[str, str]:
        """Collect variable values from environment or defaults.

        Args:
            variables: Variable definitions from configuration

        Returns:
            Dictionary mapping variable names to their values
        """
        collected: dict[str, str] = {}

        for name, definition in variables.items():
            value = self._collect_single(name, definition)
            if value is not None:
                collected[name] = value

        return collected

    def _collect_single(self, name: str, definition: Variable | None) -> str | None:
        """Collect a single variable value.

        Args:
            name: Variable name
            definition: Variable definition

        Returns:
            Variable value or None if not available
        """
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
        """Get value from environment variable.

        Args:
            var_name: Environment variable name

        Returns:
            Environment variable value or None
        """
        return os.environ.get(var_name)

    def _validate_choice(self, value: str, choices: list[str], var_name: str) -> str:
        """Validate value against available choices.

        Args:
            value: Value to validate
            choices: Available choices
            var_name: Variable name for error messages

        Returns:
            Validated value
        """
        if value not in choices:
            return choices[0]
        return value
