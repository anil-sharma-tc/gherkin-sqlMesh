from pathlib import Path
import pytest
from gherkin_sqlmesh.parser import parse

FIXTURES = Path(__file__).parent / "fixtures" / "features"


def test_parse_empty_feature_returns_feature_with_no_scenarios():
    feature = parse(FIXTURES / "empty.feature")
    assert feature.name == "Empty"
    assert feature.scenarios == []


def test_parse_feature_with_one_empty_scenario():
    feature = parse(FIXTURES / "one_empty_scenario.feature")
    assert len(feature.scenarios) == 1
    assert feature.scenarios[0].name == "Does nothing"
