# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import RootModel


class KillTokenParameter(RootModel[List[str]]):
    root: List[str]
