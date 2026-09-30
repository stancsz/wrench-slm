"""Validation and bounded deterministic oracles for synthetic gateway pilots."""

from __future__ import annotations

import ast
import json
from typing import Any


FAMILIES = {
    "source_localization",
    "bounded_code_repair",
    "test_log_diagnosis",
    "configuration_documentation",
}
EXPECTED_FAMILY_COUNTS = {family: 3 for family in FAMILIES}
SAFE_FUNCTION_NODES = {
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Return,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Call,
    ast.BinOp,
    ast.Pow,
    ast.Mult,
    ast.Add,
    ast.Sub,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
}
SAFE_CALLS = {"max", "min"}


def _fail(code: str) -> None:
    raise ValueError(code)


def _safe_relative_path(value: Any) -> bool:
    if type(value) is not str or not value or "\\" in value:
        return False
    parts = value.split("/")
    return not value.startswith("/") and all(part not in {"", ".", ".."} for part in parts)


def validate_diverse_manifest(manifest: Any) -> dict[str, int]:
    """Fail closed on malformed, incomplete, duplicate, or no-op pilot tasks."""
    if type(manifest) is not dict or manifest.get("schema") != "wrench.gateway-diverse-pilot.v1":
        _fail("manifest_schema_invalid")
    repositories = manifest.get("repositories")
    if type(repositories) is not list or len(repositories) != 3:
        _fail("manifest_repository_count_invalid")

    repo_ids: set[str] = set()
    episode_ids: set[str] = set()
    family_counts = {family: 0 for family in FAMILIES}
    total = 0
    for repository in repositories:
        if type(repository) is not dict:
            _fail("repository_record_invalid")
        repo_id = repository.get("id")
        files = repository.get("files")
        episodes = repository.get("episodes")
        if type(repo_id) is not str or not repo_id or repo_id in repo_ids:
            _fail("repository_id_invalid_or_duplicate")
        repo_ids.add(repo_id)
        if type(files) is not dict or not files:
            _fail("repository_files_invalid")
        for path, content in files.items():
            if not _safe_relative_path(path) or type(content) is not str:
                _fail("fixture_path_or_content_invalid")
        if type(episodes) is not list or len(episodes) != 4:
            _fail("repository_episode_count_invalid")

        observed_families: set[str] = set()
        for episode in episodes:
            if type(episode) is not dict:
                _fail("episode_record_invalid")
            episode_id = episode.get("id")
            if type(episode_id) is not str or not episode_id or episode_id in episode_ids:
                _fail("episode_id_invalid_or_duplicate")
            episode_ids.add(episode_id)
            family = episode.get("family")
            if family not in FAMILIES or family in observed_families:
                _fail("episode_family_missing_or_duplicate_within_repository")
            observed_families.add(family)
            family_counts[family] += 1
            total += 1

            request = episode.get("request")
            template = episode.get("query_template")
            if type(request) is not str or not request.strip() or len(request) > 1000:
                _fail("episode_request_invalid")
            if type(template) is not str or not template.strip() or len(template) > 512:
                _fail("episode_query_template_invalid")
            try:
                query = template.format(**episode)
            except (KeyError, ValueError, IndexError):
                _fail("episode_query_template_unbound")
            if not query.strip() or len(query) > 512:
                _fail("episode_rendered_query_invalid")

            required_paths = episode.get("required_paths", [episode.get("required_path")])
            if (
                type(required_paths) is not list
                or not required_paths
                or any(path not in files for path in required_paths)
            ):
                _fail("episode_required_paths_missing_from_fixture")
            oracle = episode.get("oracle")
            if type(oracle) is not dict:
                _fail("episode_oracle_invalid")
            for quote in oracle.get("quotes", []):
                if type(quote) is not str or not quote or not any(quote in files[path] for path in required_paths):
                    _fail("oracle_quote_not_present_in_required_fixture")
            for term in oracle.get("required_answer_terms", []):
                if type(term) is not str or not term.strip():
                    _fail("oracle_answer_term_invalid")

            if oracle.get("kind") == "python_function_cases":
                _validate_code_oracle(oracle)
                _ensure_initial_function_requires_a_change(files, required_paths, oracle)
            elif oracle.get("kind") == "required_evidence":
                if not oracle.get("quotes"):
                    _fail("evidence_oracle_has_no_quotes")
                if family == "source_localization" and episode.get("symbol") not in oracle["quotes"][0]:
                    _fail("localization_oracle_not_bound_to_symbol")
            elif oracle.get("kind") == "exact_json":
                if type(oracle.get("value")) is not dict:
                    _fail("exact_json_oracle_invalid")
            else:
                _fail("oracle_kind_unsupported")

        if observed_families != FAMILIES:
            _fail("repository_family_coverage_incomplete")

    if total != 12 or family_counts != EXPECTED_FAMILY_COUNTS:
        _fail("manifest_task_or_family_denominator_invalid")
    comparison = manifest.get("comparison")
    if (
        type(comparison) is not dict
        or comparison.get("frontier_calls") is not False
        or comparison.get("arms") != ["full_context", "wrench_prepared"]
    ):
        _fail("comparison_contract_invalid")
    return {"repositories": len(repositories), "episodes": total, **family_counts}


def _validate_code_oracle(oracle: dict[str, Any]) -> None:
    name = oracle.get("function")
    signature = oracle.get("signature")
    cases = oracle.get("cases")
    if (
        type(name) is not str
        or not name.isidentifier()
        or type(signature) is not list
        or not signature
        or any(type(arg) is not str or not arg.isidentifier() for arg in signature)
        or type(cases) is not list
        or len(cases) < 3
    ):
        _fail("python_function_oracle_shape_invalid")
    for case in cases:
        if type(case) is not list or len(case) != len(signature) + 1:
            _fail("python_function_oracle_case_shape_invalid")
        if any(type(value) not in {int, float, str, bool} for value in case):
            _fail("python_function_oracle_case_value_invalid")


def _parse_safe_function(
    source: str, name: str, signature: list[str], *, allow_other_definitions: bool = False
) -> Any | None:
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError:
        return None
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1 or (not allow_other_definitions and len(tree.body) != 1):
        return None
    function = matches[0]
    if function.name != name or [arg.arg for arg in function.args.args] != signature:
        return None
    if function.args.posonlyargs or function.args.vararg or function.args.kwonlyargs or function.args.kwarg:
        return None
    for node in ast.walk(function):
        if type(node) not in SAFE_FUNCTION_NODES:
            return None
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name)
            or node.func.id not in SAFE_CALLS
            or node.keywords
        ):
            return None
    namespace: dict[str, Any] = {"__builtins__": {}, "min": min, "max": max}
    try:
        module = ast.Module(body=[function], type_ignores=[])
        exec(compile(module, "<bounded-synthetic-function>", "exec"), namespace, namespace)
    except Exception:
        return None
    return namespace.get(name)


def _function_passes(function: Any, oracle: dict[str, Any]) -> bool:
    try:
        for case in oracle["cases"]:
            actual = function(*case[:-1])
            expected = case[-1]
            if type(actual) is not type(expected) or actual != expected:
                return False
    except Exception:
        return False
    return True


def _ensure_initial_function_requires_a_change(
    files: dict[str, str], required_paths: list[str], oracle: dict[str, Any]
) -> None:
    name = oracle["function"]
    signature = oracle["signature"]
    for path in required_paths:
        function = _parse_safe_function(files[path], name, signature, allow_other_definitions=True)
        if function is not None:
            if _function_passes(function, oracle):
                _fail("code_repair_task_is_noop_on_initial_fixture")
            return
    # A missing target or incompatible signature is also a real change request.


def verify_episode_answer(episode: dict[str, Any], answer: str) -> dict[str, Any]:
    """Apply the manifest's exact oracle without executing unrestricted output."""
    if type(answer) is not str:
        return {"passed": False, "reason": "answer_not_text"}
    oracle = episode.get("oracle", {})
    kind = oracle.get("kind")
    if kind == "required_evidence":
        missing_quotes = [quote for quote in oracle.get("quotes", []) if quote not in answer]
        missing_terms = [term for term in oracle.get("required_answer_terms", []) if term.casefold() not in answer.casefold()]
        symbol = episode.get("symbol")
        symbol_missing = episode.get("family") == "source_localization" and (
            not symbol or symbol not in answer
        )
        passed = not missing_quotes and not missing_terms and not symbol_missing
        return {
            "passed": passed,
            "reason": None if passed else "required_evidence_or_answer_term_missing",
            "missing_quotes": missing_quotes,
            "missing_answer_terms": missing_terms,
            "symbol_missing": symbol_missing,
        }
    if kind == "exact_json":
        try:
            value = json.loads(answer)
        except json.JSONDecodeError:
            return {"passed": False, "reason": "invalid_json"}
        passed = type(value) is dict and value == oracle["value"]
        return {"passed": passed, "reason": None if passed else "json_value_mismatch"}
    if kind == "python_function_cases":
        function = _parse_safe_function(answer, oracle["function"], oracle["signature"])
        if function is None:
            return {"passed": False, "reason": "function_ast_or_signature_invalid", "cases": []}
        results = []
        for case in oracle["cases"]:
            error_type = None
            try:
                actual = function(*case[:-1])
                passed = type(actual) is type(case[-1]) and actual == case[-1]
            except Exception as exc:
                actual = None
                passed = False
                error_type = type(exc).__name__
            row = {"inputs": case[:-1], "expected": case[-1], "actual": actual, "passed": passed}
            if error_type:
                row["error_type"] = error_type
            results.append(row)
        passed = all(row["passed"] for row in results)
        return {"passed": passed, "reason": None if passed else "behavior_mismatch", "cases": results}
    return {"passed": False, "reason": "oracle_kind_unsupported"}
