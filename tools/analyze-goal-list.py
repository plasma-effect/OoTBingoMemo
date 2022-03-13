import json
import sys
from typing import Dict


class BingoTask:
    id: str
    jp: str
    name: str
    skill: float
    time: float
    weight: float
    types: Dict[str, float]
    rowtypes: Dict[str, float]
    subtypes: Dict[str, float]

    def BingoTasks(self, data: dict):
        self.id = data['id']
        self.jp = data["jp"]
        self.name = data["name"]
        self.skill = data["skill"]
        self.time = data["time"]
        self.weight = data["weight"]
        self.types = data["types"]
        self.rowtypes = data["rowtypes"]
        self.subtypes = data["subtypes"]


def analyze(data: dict):
    for i in range(50):
        elems = data[str(i)]
        if len(elems):
            continue


def main():
    if len(sys.argv) == 1:
        print(f"Usage: python3 {sys.argv[0]} <filename>")
        return

    with open(sys.argv[1], encoding='utf_8') as file:
        s: str = file.read()
        i: int = s.find('{')
        data = json.loads(s[i:])

    analyze(data["short"])
    analyze(data["normal"])


if __name__ == "__main__":
    main()
