from math import floor
import sys
from typing import Any, Iterable, List, Dict, Optional, Tuple, TypeVar, cast


from seedrandom import Random
from goallist import BingoList, BingoTask, parse

TOO_MUCH_SYNERGY = 100.0
SQUARES_PER_ROW = 5
T = TypeVar("T")


class Profile:
    default_minimum_synergy: float
    default_maximum_synergy: float
    default_maximum_individual_synergy: float
    default_maximum_spill: float
    default_initial_offset: float
    default_maximum_offset: float
    baseline_time: float
    time_per_difficulty: float

    def __init__(self) -> None:
        self.default_minimum_synergy = -3.0
        self.default_maximum_synergy = 7.0
        self.default_maximum_individual_synergy = 3.75
        self.default_maximum_spill = 2.0
        self.default_initial_offset = 1.0
        self.default_maximum_offset = 2.0
        self.baseline_time = 27.75
        self.time_per_difficulty = 0.75


class ShortProfile(Profile):
    def __init__(self) -> None:
        super().__init__()
        self.default_maximum_synergy = 3.0
        self.baseline_time = 12.0
        self.time_per_difficulty = 0.5


class BlackoutProfile(Profile):
    def __init__(self) -> None:
        super().__init__()
        self.default_minimum_synergy = -4.0
        self.default_maximum_synergy = 4.0
        self.default_initial_offset = 2.0
        self.default_maximum_offset = 6.0
        self.baseline_time = 12.0
        self.time_per_difficulty = 0.5


class SquareData:
    difficulty: int
    desired_time: float
    synergy: float
    goal: Optional[BingoTask]

    def __init__(self, difficulty: int, time_per_difficulty: float) -> None:
        self.difficulty = difficulty
        self.desired_time = (difficulty + 1) * time_per_difficulty
        self.synergy = 0.0
        self.goal = None

    @property
    def jp(self):
        goal = self.goal
        if isinstance(goal, BingoTask):
            return goal.jp
        else:
            return ""

    @property
    def id(self):
        goal = self.goal
        if isinstance(goal, BingoTask):
            return goal.id
        else:
            return None

    @property
    def name(self):
        goal = self.goal
        if isinstance(goal, BingoTask):
            return goal.name
        else:
            return ""


class SynergiesData:
    types: Dict[str, List[float]]
    subtypes: Dict[str, List[float]]
    rowtypes: Dict[str, List[float]]
    time_differences: List[float]

    def __init__(self) -> None:
        self.types = dict()
        self.subtypes = dict()
        self.rowtypes = dict()
        self.time_differences = []


def shuffle(ar: List[T], rand: Random) -> List[T]:
    ret = ar.copy()
    for i in range(len(ar)):
        j = floor(rand.random() * (i + 1))
        ret[i], ret[j] = ret[j], ret[i]
    return ret


def weighted_shuffle(ar: Iterable[BingoTask], rand: Random) -> List[BingoTask]:
    ret = [
        (
            e,
            e.weight + rand.random() + rand.random() + rand.random() + rand.random(),
        )
        for e in ar
    ]
    ret.sort(key=(lambda p: p[1]), reverse=True)
    return [d[0] for d in ret]


def insert(ar: list, index: int, val: Any):
    ar.append(val)
    i = len(ar) - 2
    while i >= index:
        ar[i], ar[i + 1] = ar[i + 1], ar[i]
        i -= 1


def has_duplicate_strings(ar: Iterable[SquareData | BingoTask]):
    seen = set()
    for el in ar:
        if el.id in seen:
            return True
        if el.id is not None:
            seen.add(el.id)
    return False


def invertObject(ar: Dict[str, List[int]]) -> List[List[str]]:
    ret = [[] for _ in range(25)]
    for key, lis in ar.items():
        for elem in lis:
            ret[elem].append(key)
    return ret


INDICES_PER_ROW = {
    "row1": [0, 1, 2, 3, 4],
    "row2": [5, 6, 7, 8, 9],
    "row3": [10, 11, 12, 13, 14],
    "row4": [15, 16, 17, 18, 19],
    "row5": [20, 21, 22, 23, 24],
    "col1": [0, 5, 10, 15, 20],
    "col2": [1, 6, 11, 16, 21],
    "col3": [2, 7, 12, 17, 22],
    "col4": [3, 8, 13, 18, 23],
    "col5": [4, 9, 14, 19, 24],
    "tlbr": [0, 6, 12, 18, 24],
    "bltr": [4, 8, 12, 16, 20],
}
ROWS_PER_INDEX = invertObject(INDICES_PER_ROW)


class BingoGenerator:
    mode: str
    seed: int
    rand: Random
    bingo_list: BingoList
    goals_by_difficulty: List[List[BingoTask]]
    rowtype_time_save: Dict[str, float]
    synergy_filters: Dict[str, Tuple[str, int]]
    goal_list: List[BingoTask]
    goal_by_name: Dict[str, BingoTask]
    profile: Profile

    def __init__(self, bingo_lists: Dict[str, BingoList], mode: str, seed: int) -> None:
        self.mode = mode
        self.seed = seed
        if mode in bingo_lists:
            self.bingo_list = bingo_lists[mode]
        elif "normal" in bingo_lists:
            self.bingo_list = bingo_lists["normal"]
        else:
            raise RuntimeError(
                f'bingoList doesn\'t contain a valid sub goal list for mode: "{self.mode}"'
            )
        self.goals_by_difficulty = self.bingo_list.tasks
        self.rowtype_time_save = self.bingo_list.rowtypes
        self.synergy_filters = self.bingo_list.synfilters
        self.goal_list = []
        for i in range(25):
            self.goal_list += self.bingo_list.tasks[i]
        self.goal_list.sort(key=lambda task: (task.time, task.id))
        self.goal_by_name = dict()
        for task in self.goal_list:
            self.goal_by_name[task.name] = task
        self.profile = (
            ShortProfile()
            if self.mode == "short"
            else BlackoutProfile()
            if self.mode == "blackout"
            else Profile()
        )
        self.rand = Random(str(seed))

    def make_card(self) -> Optional[List[SquareData]]:
        board = self.generate_magic_square()
        population_order = self.generate_poluration_order(board)
        for next_position in population_order:
            goal, synergy = self.choose_goal_for_position(next_position, board)
            if isinstance(goal, BingoTask):
                board[next_position].goal = goal
                board[next_position].synergy = synergy
            else:
                return None
        return board

    def generate_magic_square(self) -> List[SquareData]:
        table = self.difficulty_table()
        return [SquareData(d, self.profile.time_per_difficulty) for d in table]

    def choose_goal_for_position(
        self, position: int, board: List[SquareData]
    ) -> Tuple[Optional[BingoTask], float]:
        desired_time = board[position].desired_time
        offset = self.profile.default_initial_offset
        max_offset = self.profile.default_maximum_offset
        max_synergy = self.profile.default_maximum_synergy
        min_synergy = self.profile.default_minimum_synergy
        while offset <= max_offset:
            min_time = desired_time - offset
            max_time = desired_time + offset
            goals_at_time = self.get_goals_in_time_range(min_time, max_time)
            shuffled = weighted_shuffle(goals_at_time, self.rand)
            for goal in shuffled:
                if self.has_goal_on_board(goal, board):
                    continue
                if self.mode == "blackout" and self.has_conflicts_on_board(goal, board):
                    continue
                min_s, max_s = self.check_line(position, goal, board)
                if max_synergy >= max_s and min_s >= min_synergy:
                    return goal, max_s
            offset += 1.0
        return None, 0.0

    def generate_poluration_order(self, board: List[SquareData]) -> List[int]:
        diagonals = shuffle([0, 6, 18, 24, 4, 8, 16, 20], self.rand)
        nondiagonals = shuffle(
            [1, 2, 3, 5, 7, 9, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23], self.rand
        )
        ret = [12] + diagonals + nondiagonals
        for k in [22, 23, 24]:
            current_square = self.get_difficulty_index(k, board)
            if isinstance(current_square, int):
                for i in range(25):
                    if ret[i] == current_square:
                        ret = [current_square] + ret[0:i] + ret[i + 1 :]
                        break
        return ret

    def difficulty_table(self) -> List[int]:
        def make_subtable(seed: int, remT: int):
            rem8 = seed % 8
            rem4 = rem8 // 2
            rem2 = rem8 % 2
            rem5 = seed % 5
            rem3 = seed % 3
            remT = remT * 8 + seed // 120
            table = [0]
            insert(table, rem2, 1)
            insert(table, rem3, 2)
            insert(table, rem4, 3)
            insert(table, rem5, 4)
            return table, remT

        table5, remT = make_subtable(self.seed % 1000, 0)
        table1, remT = make_subtable((self.seed // 1000) % 1000, remT)
        remT %= 5
        table = []
        for i in range(25):
            x = (i + remT) % 5
            y = i // 5
            e5 = table5[(x + 3 * y) % 5]
            e1 = table1[(3 * x + y) % 5]
            table.append(5 * e5 + e1)
        return table

    def get_difficulty_index(
        self, difficulty: int, board: List[SquareData]
    ) -> Optional[int]:
        for i in range(25):
            if board[i].difficulty == difficulty:
                return i
        return None

    def get_goals_in_time_range(
        self, min_time: float, max_time: float
    ) -> List[BingoTask]:
        return [e for e in self.goal_list if min_time <= e.time and e.time <= max_time]

    def has_goal_on_board(self, task: BingoTask, board: List[SquareData]):
        for i in range(25):
            square = board[i].goal
            if isinstance(square, BingoTask) and task.id == square.id:
                return True
        return False

    def has_conflicts_on_board(self, task: BingoTask, board: List[SquareData]) -> bool:
        for square in board:
            goal = square.goal
            if isinstance(goal, BingoTask):
                synergy = self.evaluate_squares([task, goal])
                if synergy >= TOO_MUCH_SYNERGY:
                    return True
        return False

    def get_other_squares(
        self, row: str, position: int, board: List[SquareData]
    ) -> List[SquareData]:
        row_indices = filter((lambda idx: idx != position), INDICES_PER_ROW[row])
        return [board[idx] for idx in row_indices]

    def check_line(
        self, position: int, potential_task: BingoTask, board: List[SquareData]
    ) -> Tuple[float, float]:
        rows = ROWS_PER_INDEX[position]
        max_s = 0.0
        min_s = TOO_MUCH_SYNERGY
        for row in rows:
            potential_square = SquareData(
                board[position].difficulty, self.profile.time_per_difficulty
            )
            potential_square.goal = potential_task
            potential_row = self.get_other_squares(row, position, board) + [
                potential_square
            ]
            s = self.evaluate_squares(potential_row)
            max_s = max(max_s, s)
            min_s = min(min_s, s)
        return min_s, max_s

    def evaluate_squares(self, tasks: Iterable[SquareData | BingoTask]) -> float:
        if has_duplicate_strings(tasks):
            return TOO_MUCH_SYNERGY
        synergies_for_squares = self.calculate_synergies_for_squares(tasks)
        return self.calculate_effective_synergy_for_squares(synergies_for_squares)

    def calculate_synergies_for_squares(
        self, squares: Iterable[SquareData | BingoTask]
    ) -> SynergiesData:
        ret = SynergiesData()
        for square in squares:
            if isinstance(square, SquareData):
                if square.goal is None:
                    continue
                goal = cast(BingoTask, square.goal)
            else:
                goal = square
            self.merge_type_synergies(ret.types, goal.types)
            self.merge_type_synergies(ret.subtypes, goal.subtypes)
            self.merge_type_synergies(ret.rowtypes, goal.rowtypes)
            if isinstance(square, SquareData):
                ret.time_differences.append(square.desired_time - goal.time)
        return ret

    def merge_type_synergies(
        self, synergies: Dict[str, List[float]], new_synergies: Dict[str, float]
    ):
        for t, s in new_synergies.items():
            if t not in synergies:
                synergies[t] = [s]
            else:
                synergies[t].append(s)

    def calculate_combined_type_synergies(
        self, synergies: SynergiesData
    ) -> Dict[str, List[float]]:
        ret: Dict[str, List[float]] = dict()
        for t in synergies.types:
            if t in synergies.subtypes:
                ret[t] = synergies.types[t] + synergies.subtypes[t]
            else:
                ret[t] = synergies.types[t]
        return ret

    def filter_rowtype_synergies(self, synergies: SynergiesData) -> Dict[str, float]:
        rowtype_synergies = dict()
        for rowtype, synergy in synergies.rowtypes.items():
            if len(synergy) < SQUARES_PER_ROW:
                continue
            rowtype_cost = sum(synergy)
            rowtype_threshold = self.rowtype_time_save[rowtype]
            if rowtype_threshold > 0 and rowtype_threshold > rowtype_cost:
                rowtype_synergies[rowtype] = rowtype_threshold - rowtype_cost
            elif rowtype_threshold < 0 and rowtype_threshold > rowtype_cost:
                rowtype_synergies[rowtype] = rowtype_cost - rowtype_threshold
        return rowtype_synergies

    def calculate_effective_type_synergies(
        self, synergies: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        effective_type_synergies = dict()
        for t, s in synergies.items():
            effective_synergies = self.filter_synergy_values_for_type(t, s)
            if len(effective_synergies):
                effective_type_synergies[t] = effective_synergies
        return effective_type_synergies

    def filter_synergy_values_for_type(
        self, t: str, synergies: List[float]
    ) -> List[float]:
        synergies.sort()
        if t in self.synergy_filters:
            s, v = self.synergy_filters[t]
            if s == "max":
                synergies.reverse()
            return synergies[0:v]
        else:
            return synergies[0:-1]

    def calculate_effective_synergy_for_squares(
        self, synergies_for_squares: SynergiesData
    ) -> float:
        type_synergies = self.calculate_combined_type_synergies(synergies_for_squares)
        rowtype_synergies = self.filter_rowtype_synergies(synergies_for_squares)
        effective_type_synergies = self.calculate_effective_type_synergies(
            type_synergies
        )
        row_synergy = 0.0
        for synergies in effective_type_synergies.values():
            for s in synergies:
                if s > self.profile.default_maximum_individual_synergy:
                    return TOO_MUCH_SYNERGY
                row_synergy += s
        for s in rowtype_synergies.values():
            row_synergy += s
        time_differences = synergies_for_squares.time_differences
        for diff in time_differences:
            row_synergy += diff
        return row_synergy


def oot_bingo_generator(
    bingo_lists: Dict[str, BingoList], mode: str, seed: int
) -> Optional[List[SquareData]]:
    generator = BingoGenerator(bingo_lists, mode, seed)
    card: Optional[List[SquareData]] = None
    for _ in range(100):
        card = generator.make_card()
        if card is not None:
            break
    return card


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <goal-list> <seed>")
        return
    card = oot_bingo_generator(parse(sys.argv[1]), "normal", int(sys.argv[2]))
    if card is not None:
        for square in card:
            print(square.name)


if __name__ == "__main__":
    main()
