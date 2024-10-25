from dataclasses import dataclass

@dataclass
class MergeRequestDiff:
    old_path: str
    new_path: str