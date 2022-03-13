import json
import sys
from typing import Dict


class BingoTask:
    id: str
    jp: str
    name: str
    skill: float
    time: float
    types: Dict[str, float]
    rowtypes: Dict[str, float]
    subtypes: Dict[str, float]

    def __init__(self, data: dict):
        self.id = data['id']
        self.jp = data["jp"]
        self.name = data["name"]
        self.skill = data["skill"]
        self.time = data["time"]
        self.types = data["types"]
        self.rowtypes = dict()
        self.subtypes = dict()
        if "rowtypes" in data:
            self.rowtypes = data["rowtypes"]
        self.subtypes = data["subtypes"]


def analyze(data: dict, filename: str, title: str):
    with open(filename, mode="w", encoding="utf_8") as f:
        def write(s):
            print(s, file=f)
        write(f"# {title}")
        for i in range(50):
            elems = data[str(i)]
            if len(elems) == 0:
                continue
            for raw in elems:
                if raw["id"] == "":
                    continue
                write(f"\n## {raw['name']}/{raw['jp']}\n")
                write(f"- time: {raw['time']}")
                write(f"- skill: {raw['skill']}")
                write("- types")
                for key, item in raw["types"].items():
                    write(f"  - {key}: {item}")
                if "subtypes" in raw:
                    write("- sub types")
                    for key, item in raw["subtypes"].items():
                        write(f"  - {key}: {item}")
                if "rowtypes" in raw:
                    write("- row types")
                    for key, item in raw["rowtypes"].items():
                        write(f"  - {key}: {item}")


def main():
    if len(sys.argv) < 4:
        print(
            f"Usage: python3 {sys.argv[0]} <filename> <short goal list name> <normal goal list name>")
        return

    with open(sys.argv[1], encoding='utf_8') as file:
        s: str = file.read()
        i: int = s.find('{')
        data = json.loads(s[i:])

    analyze(data["short"], sys.argv[2], "Short Goal Lists")
    analyze(data["normal"], sys.argv[3], "Normal Goal Lists")


if __name__ == "__main__":
    main()
