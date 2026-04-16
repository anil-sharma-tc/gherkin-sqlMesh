"""Parse Gherkin .feature files into a simple AST."""

from dataclasses import dataclass, field
from pathlib import Path

from gherkin.parser import Parser
from gherkin.token_matcher import TokenMatcher
from gherkin.token_scanner import TokenScanner


@dataclass
class Step:
    keyword: str
    text: str
    data_table: list[list[str]] | None = None


@dataclass
class Scenario:
    name: str
    steps: list[Step] = field(default_factory=list)


@dataclass
class Feature:
    name: str
    scenarios: list[Scenario] = field(default_factory=list)


def parse(path: Path) -> Feature:
    """Parse a .feature file and return a Feature object."""
    parser = Parser()
    scanner = TokenScanner(path.read_text())
    matcher = TokenMatcher()
    ast = parser.parse(scanner, matcher)

    feature_node = ast["feature"]
    feature_name = feature_node["name"]

    scenarios = []
    for child in feature_node.get("children", []):
        if "scenario" not in child:
            continue
        scenario_node = child["scenario"]
        scenario = Scenario(name=scenario_node["name"])
        for step_node in scenario_node.get("steps", []):
            keyword = step_node["keyword"].strip().lower()
            text = step_node["text"]
            data_table = None
            argument = step_node.get("argument")
            if argument and "dataTable" in argument:
                rows = argument["dataTable"]["rows"]
                data_table = [
                    [cell["value"] for cell in row["cells"]] for row in rows
                ]
            scenario.steps.append(Step(keyword=keyword, text=text, data_table=data_table))
        scenarios.append(scenario)

    return Feature(name=feature_name, scenarios=scenarios)
