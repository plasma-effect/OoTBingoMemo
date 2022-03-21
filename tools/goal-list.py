import json
import sys
from typing import Dict, List, Optional, Tuple, cast


class BingoTask:
    difficulty: int
    id: str
    jp: str
    name: str
    skill: float
    time: float
    weight: float
    types: Dict[str, float]
    rowtypes: Dict[str, float]
    subtypes: Dict[str, float]

    def __init__(
        self,
        difficulty: int,
        id: str,
        jp: str,
        name: str,
        skill: float,
        time: float,
        weight: float,
    ) -> None:
        self.difficulty = difficulty
        self.id = id
        self.jp = jp
        self.name = name
        self.skill = skill
        self.time = time
        self.weight = weight
        self.types = dict()
        self.rowtypes = dict()
        self.subtypes = dict()


class BingoList:
    tasks: List[List[BingoTask]]
    rowtypes: Dict[str, float]
    synfilters: Dict[str, Tuple[str, float]]
    average_standard_deviation: Optional[float]

    def __init__(self, average_standard_deviation: Optional[float] = None) -> None:
        self.tasks = [[] for _ in range(25)]
        self.rowtypes = dict()
        self.synfilters = dict()
        self.average_standard_deviation = average_standard_deviation


def parse(filename: str):
    with open(filename, encoding="utf_8") as f:
        s: str = f.read()
        i: int = s.find("{")
        data = json.loads(s[i:])
    ret = {
        "normal": BingoList(float(data["normal"]["averageStandardDeviation"])),
        "short": BingoList(),
    }
    for mode in ["normal", "short"]:
        raw = data[mode]
        for key, item in raw["rowtypes"].items():
            ret[mode].rowtypes[key] = float(item)
        for key, item in raw["synfilters"].items():
            item = cast(str, item)
            pair = item.split(" ")
            ret[mode].synfilters[key] = pair[0], float(pair[1])
        for i in range(25):
            for elem in raw[str(i + 1)]:
                task = BingoTask(
                    int(elem["difficulty"]),
                    elem["id"],
                    elem["jp"],
                    elem["name"],
                    float(elem["skill"]),
                    float(elem["time"]),
                    float(elem["weight"]) if "weight" in elem else 0.0,
                )
                for k, t in elem["types"].items():
                    task.types[k] = t
                if "subtypes" in elem:
                    for k, t in elem["subtypes"].items():
                        task.subtypes[k] = t
                if "rowtypes" in elem:
                    for k, t in elem["rowtypes"].items():
                        task.subtypes[k] = t
                ret[mode].tasks[i].append(task)
    return ret


def main():
    taskLists = parse(sys.argv[1])
    print(taskLists)


if __name__ == "__main__":
    main()
