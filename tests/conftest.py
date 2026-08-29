# -*- coding: utf-8 -*-
"""pytest 公共 fixture。"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.problems import load_problems  # noqa: E402

PROBLEMS_PATH = os.path.join(ROOT, "data", "problems.json")
SAMPLES_PATH = os.path.join(ROOT, "data", "samples.json")


@pytest.fixture(scope="session")
def problems():
    return load_problems(PROBLEMS_PATH)


@pytest.fixture(scope="session")
def samples():
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        return json_load(f)


def json_load(f):
    import json
    return json.load(f)
