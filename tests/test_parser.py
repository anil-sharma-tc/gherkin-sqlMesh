from pathlib import Path
import pytest
from gherkin_sqlmesh.parser import parse

FIXTURES = Path(__file__).parent / "fixtures" / "features"


def test_parse_empty_feature_returns_feature_with_no_scenarios():
    feature = parse(FIXTURES / "empty.feature")
    assert feature.name == "Empty"
    assert feature.scenarios == []
