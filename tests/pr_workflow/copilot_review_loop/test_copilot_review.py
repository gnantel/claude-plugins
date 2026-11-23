"""Tests for the command-line handling of the Copilot review loop's message file."""

import pytest

import copilot_review


def test_a_message_file_outside_the_working_tree_is_read(repository) -> None:
    message_file = repository.path.parent / "message.txt"
    message_file.write_text("Add parser\n\nCloses #5\n")
    assert copilot_review.read_message_file(message_file) == "Add parser\n\nCloses #5"


def test_a_message_file_inside_the_working_tree_is_refused(repository) -> None:
    repository.write("message.txt", "Add parser")
    with pytest.raises(SystemExit, match="outside the working tree"):
        copilot_review.read_message_file(repository.path / "message.txt")


def test_no_message_file_means_no_message(repository) -> None:
    assert copilot_review.read_message_file(None) is None
