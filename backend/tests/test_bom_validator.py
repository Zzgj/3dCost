import pytest
from app.services.bom_validator import BOMCycleError, check_bom_cycle


def test_no_cycle_simple():
    """A→B，无循环"""
    edges = {1: [2], 2: []}
    check_bom_cycle(1, edges)  # 不抛异常


def test_self_reference():
    """A→A"""
    edges = {1: [1]}
    with pytest.raises(BOMCycleError):
        check_bom_cycle(1, edges)


def test_indirect_cycle():
    """A→B→C→A"""
    edges = {1: [2], 2: [3], 3: [1]}
    with pytest.raises(BOMCycleError):
        check_bom_cycle(1, edges)


def test_diamond_no_cycle():
    """A→B,C; B→D; C→D（菱形结构不是循环）"""
    edges = {1: [2, 3], 2: [4], 3: [4], 4: []}
    check_bom_cycle(1, edges)  # 不抛异常


def test_deep_chain_no_cycle():
    """A→B→C→D→E，无循环"""
    edges = {1: [2], 2: [3], 3: [4], 4: [5], 5: []}
    check_bom_cycle(1, edges)  # 不抛异常


def test_root_not_in_edges():
    """root 不在 edges 中（无出边）：不抛异常"""
    check_bom_cycle(1, {})  # 不抛异常
