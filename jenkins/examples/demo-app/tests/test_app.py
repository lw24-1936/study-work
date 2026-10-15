import pytest

from app import add, divide, normalize_scores


def test_add():
    assert add(1, 2) == 3


def test_divide_ok():
    assert divide(6, 3) == 2


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(1, 0)


def test_normalize_scores():
    assert normalize_scores([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_normalize_scores_edge_cases():
    assert normalize_scores([]) == []
    assert normalize_scores([3, 3]) == [0.5, 0.5]
