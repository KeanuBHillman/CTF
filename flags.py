from typing import TypedDict, Dict


class Flag(TypedDict):
    name: str
    flag: str
    points: int


flags: Dict[int, Flag] = {
    0: {"name": "Cool flag", "flag": "this_is_a_flag", "points": 1},
    1: {"name": "Cool flag 2", "flag": "this_is_a_flag_too", "points": 2},
    2: {"name": "Cool flag 3", "flag": "this_is_a_flag_too2", "points": 3},
    3: {"name": "Cool flag 4", "flag": "this_is_a_flag_too3", "points": 4},
    4: {"name": "Cool flag 5", "flag": "this_is_a_flag_too3", "points": 6},
    5: {"name": "Cool flag 6", "flag": "this_is_a_flag_too3", "points": 7},
    6: {"name": "Cool flag 7", "flag": "this_is_a_flag_too3", "points": 8},
    7: {"name": "Cool flag 8", "flag": "this_is_a_flag_too3", "points": 9},
    8: {"name": "Cool flag 9", "flag": "this_is_a_flag_too3", "points": 10},
}
