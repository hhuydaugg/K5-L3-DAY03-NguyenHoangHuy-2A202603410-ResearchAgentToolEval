"""Regression for object-list arguments previously mislabeled as provider errors."""
from run_eval import compare_subset, evaluate_phase_b


def test_object_lists_compare_without_type_error_and_keep_existing_unordered_semantics():
    expected = {"items": [{"url": "https://example.org/a", "title": "A"}, {"url": "https://example.org/b"}]}
    actual = {"items": [{"url": "https://example.org/b"}, {"title": "A", "url": "https://example.org/a"}]}
    assert compare_subset(expected, actual) == (True, [], 1, 1)


def test_object_list_value_mismatch_is_a_failure_not_an_exception():
    passed, failures, correct, total = compare_subset(
        {"items": [{"url": "https://example.org/a"}]},
        {"items": [{"url": "https://example.org/b"}]},
    )
    assert not passed and correct == 0 and total == 1
    assert failures


def test_new_tool_case_can_be_graded_with_object_arguments():
    items = [{"url": "https://example.org/a"}, {"url": "https://example.org/a"}]
    case = {"failure_type": "wrong_tool", "expect": {"tool_calls": [
        {"name": "deduplicate_sources", "args": {"items": items}}
    ]}}
    result = evaluate_phase_b(case, [{"name": "deduplicate_sources", "args": {"items": items}}], None)
    assert result["passed"] is True
