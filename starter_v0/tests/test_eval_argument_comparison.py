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


def test_eval_checks_write_permission_before_creating_provider(monkeypatch, tmp_path):
    import sys
    import pytest
    import run_eval
    monkeypatch.setattr(sys, 'argv', ['run_eval.py', '--provider', 'openrouter', '--version', 'test', '--runs-dir', str(tmp_path)])
    def denied(**kwargs):
        raise PermissionError('evidence directory is not writable')
    def must_not_create_provider(*args, **kwargs):
        raise AssertionError('provider should not be created without writable evidence storage')
    monkeypatch.setattr(run_eval.tempfile, 'TemporaryFile', denied)
    monkeypatch.setattr(run_eval, 'make_provider', must_not_create_provider)
    with pytest.raises(PermissionError):
        run_eval.main()
