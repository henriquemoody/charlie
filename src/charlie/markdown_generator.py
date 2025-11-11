from pathlib import Path
from typing import final

import yaml

from charlie.schema import Metadata


@final
class MarkdownGenerator:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def generate(
        self,
        file: Path,
        body: str,
        metadata: Metadata | None = None,
        allowed_metadata: list[str] | None = None,
    ) -> None:
        frontmatter = ""
        if metadata is not None and allowed_metadata is not None:
            metadata = {key: value for key, value in metadata.items() if key in allowed_metadata}

        if metadata is not None:
            yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            frontmatter += f"---\n{yaml_str}---\n\n"

        file.write_text(frontmatter + body, encoding=self.encoding)
