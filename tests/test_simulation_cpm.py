"""Critical path tests against answers worked out by hand in my IS3328 notes."""

import pytest

from modulesim.simulation import critical_path

# QuickBrew (IS3328 exercises No 3 and No 4), durations in days.
QUICKBREW_DAYS = {"A": 5, "B": 15, "C": 10, "D": 4, "E": 10, "F": 2,
                  "G": 3, "H": 5, "I": 2, "J": 2, "K": 2}
QUICKBREW_AFTER = {"A": [], "B": ["A"], "C": ["A"], "D": ["A"], "E": ["D"], "F": ["D"],
                   "G": ["B", "C", "E"], "H": ["G", "F"], "I": ["G"], "J": ["E"],
                   "K": ["H", "I", "J"]}


def test_quickbrew_matches_the_hand_worked_answer():
    s = critical_path(QUICKBREW_DAYS, QUICKBREW_AFTER)
    assert s.length == 30
    assert s.critical_paths == [["A", "B", "G", "H", "K"]]
    assert s.float == {"A": 0, "B": 0, "C": 5, "D": 1, "E": 1, "F": 12,
                       "G": 0, "H": 0, "I": 3, "J": 7, "K": 0}
    assert (s.es["G"], s.ef["G"], s.ls["G"], s.lf["G"]) == (20, 23, 20, 23)


def test_quickbrew_path_moves_when_the_build_overruns():
    # My notes: if E takes 13 days, the path becomes A-D-E-G-H-K, 32 days.
    s = critical_path({**QUICKBREW_DAYS, "E": 13}, QUICKBREW_AFTER)
    assert s.length == 32
    assert s.critical_paths == [["A", "D", "E", "G", "H", "K"]]
    assert s.float["B"] == 2


def test_irish_retail_click_and_collect():
    s = critical_path({"A": 3, "B": 2, "C": 1, "D": 2, "E": 4, "F": 1},
                      {"A": [], "B": [], "C": ["A"], "D": ["C"], "E": ["B", "D"], "F": ["E"]})
    assert s.length == 11
    assert s.critical_paths == [["A", "C", "D", "E", "F"]]
    assert s.float["B"] == 4


def test_two_equal_critical_paths_are_both_found():
    s = critical_path({"A": 1, "B": 2, "C": 2, "D": 1},
                      {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]})
    assert s.critical_paths == [["A", "B", "D"], ["A", "C", "D"]]


def test_a_loop_of_tasks_is_rejected():
    with pytest.raises(ValueError, match="loop"):
        critical_path({"A": 1, "B": 1}, {"A": ["B"], "B": ["A"]})


def test_an_unknown_predecessor_is_rejected():
    with pytest.raises(ValueError, match="unknown task"):
        critical_path({"A": 1}, {"A": ["Z"]})
