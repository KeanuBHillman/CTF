"""Tests for automarking validation logic.

Tests the validate_answer function which supports:
- exact: Case-sensitive or insensitive exact matching
- partial: Contains the expected substring
- multiple_choice: One of many pipe-separated options
- regex: Regex pattern matching
- numeric: Numeric value matching within a tolerance
"""

import pytest
from database import Question
from app.routers.challenges import validate_answer


class TestExactMatching:
    """Test exact answer type validation."""

    def test_exact_match_case_insensitive(self):
        """Exact match with case_sensitive=False should accept different cases."""
        question = Question(
            challenge_id=1,
            question_text="What port?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="8080",
            answer_type="exact",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "8080")
        assert points == 50
        assert status == "correct"

        # Different case should also match
        points, status = validate_answer(question, "8080")
        assert points == 50
        assert status == "correct"

    def test_exact_match_case_sensitive(self):
        """Exact match with case_sensitive=True should reject different cases."""
        question = Question(
            challenge_id=1,
            question_text="What word?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="FLAG",
            answer_type="exact",
            case_sensitive=True,
        )

        points, status = validate_answer(question, "FLAG")
        assert points == 50
        assert status == "correct"

        # Different case should not match
        points, status = validate_answer(question, "flag")
        assert points == 0
        assert status == "incorrect"

    def test_exact_match_wrong_answer(self):
        """Exact match with wrong answer should award 0 points."""
        question = Question(
            challenge_id=1,
            question_text="What port?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="8080",
            answer_type="exact",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "80")
        assert points == 0
        assert status == "incorrect"

    def test_exact_match_with_whitespace(self):
        """Exact match should trim whitespace."""
        question = Question(
            challenge_id=1,
            question_text="What port?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="8080",
            answer_type="exact",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "  8080  ")
        assert points == 50
        assert status == "correct"


class TestPartialMatching:
    """Test partial answer type validation."""

    def test_partial_match_case_insensitive(self):
        """Partial match should find substring."""
        question = Question(
            challenge_id=1,
            question_text="What tool did you use?",
            question_type="text",
            required=True,
            points=100,
            order=3,
            expected_answer="nmap",
            answer_type="partial",
            case_sensitive=False,
        )

        # Exact substring should match
        points, status = validate_answer(question, "nmap")
        assert points == 100
        assert status == "correct"

        # Substring within larger answer should match
        points, status = validate_answer(question, "I used nmap for scanning")
        assert points == 100
        assert status == "correct"

        # Case insensitive
        points, status = validate_answer(question, "I used NMAP for scanning")
        assert points == 100
        assert status == "correct"

    def test_partial_match_case_sensitive(self):
        """Partial match with case_sensitive=True should be case-sensitive."""
        question = Question(
            challenge_id=1,
            question_text="What tool?",
            question_type="text",
            required=True,
            points=100,
            order=3,
            expected_answer="nmap",
            answer_type="partial",
            case_sensitive=True,
        )

        points, status = validate_answer(question, "nmap")
        assert points == 100
        assert status == "correct"

        # Different case should not match
        points, status = validate_answer(question, "NMAP is useful")
        assert points == 0
        assert status == "incorrect"

    def test_partial_match_not_found(self):
        """Partial match with missing substring should award 0 points."""
        question = Question(
            challenge_id=1,
            question_text="What tool?",
            question_type="text",
            required=True,
            points=100,
            order=3,
            expected_answer="nmap",
            answer_type="partial",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "I used Burp Suite")
        assert points == 0
        assert status == "incorrect"


class TestMultipleChoice:
    """Test multiple_choice answer type validation."""

    def test_multiple_choice_single_option(self):
        """Multiple choice should accept any of the pipe-separated options."""
        question = Question(
            challenge_id=1,
            question_text="What web framework?",
            question_type="text",
            required=True,
            points=75,
            order=2,
            expected_answer="Flask|Django|FastAPI|Express",
            answer_type="multiple_choice",
            case_sensitive=False,
        )

        for option in ["Flask", "Django", "FastAPI", "Express"]:
            points, status = validate_answer(question, option)
            assert points == 75, f"Failed for option: {option}"
            assert status == "correct", f"Failed for option: {option}"

    def test_multiple_choice_case_insensitive(self):
        """Multiple choice should be case insensitive by default."""
        question = Question(
            challenge_id=1,
            question_text="What framework?",
            question_type="text",
            required=True,
            points=75,
            order=2,
            expected_answer="Flask|Django|FastAPI|Express",
            answer_type="multiple_choice",
            case_sensitive=False,
        )

        for option in ["flask", "DJANGO", "fastapi", "EXPRESS"]:
            points, status = validate_answer(question, option)
            assert points == 75
            assert status == "correct"

    def test_multiple_choice_case_sensitive(self):
        """Multiple choice with case_sensitive=True should enforce case."""
        question = Question(
            challenge_id=1,
            question_text="What framework?",
            question_type="text",
            required=True,
            points=75,
            order=2,
            expected_answer="Flask|Django|FastAPI|Express",
            answer_type="multiple_choice",
            case_sensitive=True,
        )

        points, status = validate_answer(question, "Flask")
        assert points == 75
        assert status == "correct"

        # Wrong case should fail
        points, status = validate_answer(question, "flask")
        assert points == 0
        assert status == "incorrect"

    def test_multiple_choice_invalid_option(self):
        """Multiple choice with invalid option should award 0 points."""
        question = Question(
            challenge_id=1,
            question_text="What framework?",
            question_type="text",
            required=True,
            points=75,
            order=2,
            expected_answer="Flask|Django|FastAPI|Express",
            answer_type="multiple_choice",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "Ruby on Rails")
        assert points == 0
        assert status == "incorrect"


class TestRegexMatching:
    """Test regex answer type validation."""

    def test_regex_simple_pattern(self):
        """Regex should match pattern."""
        question = Question(
            challenge_id=1,
            question_text="What flag?",
            question_type="text",
            required=False,
            points=150,
            order=4,
            expected_answer="CTF_.*",
            answer_type="regex",
            case_sensitive=False,
        )

        valid_flags = ["CTF_flag123", "CTF_test", "CTF_a", "ctf_lowercase"]
        for flag in valid_flags:
            points, status = validate_answer(question, flag)
            assert points == 150, f"Failed for flag: {flag}"
            assert status == "correct", f"Failed for flag: {flag}"

    def test_regex_case_insensitive(self):
        """Regex should be case insensitive when case_sensitive=False."""
        question = Question(
            challenge_id=1,
            question_text="What flag?",
            question_type="text",
            required=False,
            points=150,
            order=4,
            expected_answer="flag_[0-9]+",
            answer_type="regex",
            case_sensitive=False,
        )

        # Pattern should match regardless of case
        points, status = validate_answer(question, "FLAG_123")
        assert points == 150
        assert status == "correct"

        points, status = validate_answer(question, "Flag_456")
        assert points == 150
        assert status == "correct"

    def test_regex_case_sensitive(self):
        """Regex should be case sensitive when case_sensitive=True."""
        question = Question(
            challenge_id=1,
            question_text="What flag?",
            question_type="text",
            required=False,
            points=150,
            order=4,
            expected_answer="flag_[0-9]+",
            answer_type="regex",
            case_sensitive=True,
        )

        # Correct case should match
        points, status = validate_answer(question, "flag_123")
        assert points == 150
        assert status == "correct"

        # Wrong case should not match
        points, status = validate_answer(question, "FLAG_123")
        assert points == 0
        assert status == "incorrect"

    def test_regex_no_match(self):
        """Regex with no match should award 0 points."""
        question = Question(
            challenge_id=1,
            question_text="What flag?",
            question_type="text",
            required=False,
            points=150,
            order=4,
            expected_answer="CTF_.*",
            answer_type="regex",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "INVALID_flag")
        assert points == 0
        assert status == "incorrect"

    def test_regex_invalid_pattern_fallback(self):
        """Invalid regex pattern should fall back to exact matching."""
        question = Question(
            challenge_id=1,
            question_text="What answer?",
            question_type="text",
            required=False,
            points=100,
            order=1,
            expected_answer="[invalid(regex",  # Invalid regex
            answer_type="regex",
            case_sensitive=False,
        )

        # Should fall back to exact matching
        points, status = validate_answer(question, "[invalid(regex")
        assert points == 100
        assert status == "correct"

        points, status = validate_answer(question, "different answer")
        assert points == 0
        assert status == "incorrect"


class TestNumericMatching:
    """Test numeric answer type validation."""

    def test_numeric_exact_match(self):
        """Numeric match with zero tolerance should require exact value."""
        question = Question(
            challenge_id=1,
            question_text="What is 2+2?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="4",
            answer_type="numeric",
            tolerance=0.0,
        )

        points, status = validate_answer(question, "4")
        assert points == 50
        assert status == "correct"

        points, status = validate_answer(question, "4.0")
        assert points == 50
        assert status == "correct"

        points, status = validate_answer(question, "5")
        assert points == 0
        assert status == "incorrect"

    def test_numeric_with_tolerance(self):
        """Numeric match should accept values within tolerance."""
        question = Question(
            challenge_id=1,
            question_text="What is pi?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="3.14159",
            answer_type="numeric",
            tolerance=0.01,
        )

        # Exact value
        points, status = validate_answer(question, "3.14159")
        assert points == 100
        assert status == "correct"

        # Within tolerance (upper bound)
        points, status = validate_answer(question, "3.15")
        assert points == 100
        assert status == "correct"

        # Within tolerance (lower bound)
        points, status = validate_answer(question, "3.1316")
        assert points == 100
        assert status == "correct"

        # Outside tolerance
        points, status = validate_answer(question, "3.20")
        assert points == 0
        assert status == "incorrect"

    def test_numeric_invalid_number(self):
        """Non-numeric answer should award 0 points."""
        question = Question(
            challenge_id=1,
            question_text="What is the answer?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="42",
            answer_type="numeric",
            tolerance=0.0,
        )

        points, status = validate_answer(question, "not a number")
        assert points == 0
        assert status == "incorrect"

        points, status = validate_answer(question, "42abc")
        assert points == 0
        assert status == "incorrect"

    def test_numeric_negative_values(self):
        """Numeric matching should work with negative values."""
        question = Question(
            challenge_id=1,
            question_text="What is -5 * 3?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="-15",
            answer_type="numeric",
            tolerance=0.0,
        )

        points, status = validate_answer(question, "-15")
        assert points == 50
        assert status == "correct"

        points, status = validate_answer(question, "15")
        assert points == 0
        assert status == "incorrect"


class TestDateMatching:
    """Test strict date answer type validation."""

    def test_date_exact_match(self):
        """Date answers should match strict YYYY - MM - DD format and value."""
        question = Question(
            challenge_id=1,
            question_text="When was the image taken?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="2002 - 08 - 09",
            answer_type="date",
        )

        points, status = validate_answer(question, "2002 - 08 - 09")
        assert points == 100
        assert status == "correct"

    def test_date_wrong_value(self):
        """A correctly formatted but different date should be incorrect."""
        question = Question(
            challenge_id=1,
            question_text="When was the image taken?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="2002 - 08 - 09",
            answer_type="date",
        )

        points, status = validate_answer(question, "2002 - 08 - 10")
        assert points == 0
        assert status == "incorrect"

    def test_date_invalid_format(self):
        """Wrong date formatting should return invalid_date_format."""
        question = Question(
            challenge_id=1,
            question_text="When was the image taken?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="2002 - 08 - 09",
            answer_type="date",
        )

        points, status = validate_answer(question, "2002-08-09")
        assert points == 0
        assert status == "invalid_date_format"

    def test_date_invalid_calendar_date(self):
        """Impossible calendar values should return invalid_date_format."""
        question = Question(
            challenge_id=1,
            question_text="When was the image taken?",
            question_type="text",
            required=True,
            points=100,
            order=1,
            expected_answer="2002 - 08 - 09",
            answer_type="date",
        )

        points, status = validate_answer(question, "2002 - 02 - 30")
        assert points == 0
        assert status == "invalid_date_format"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_answer(self):
        """Empty answer should return empty_answer status."""
        question = Question(
            challenge_id=1,
            question_text="What?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="answer",
            answer_type="exact",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "")
        assert points == 0
        assert status == "empty_answer"

        points, status = validate_answer(question, "   ")
        assert points == 0
        assert status == "empty_answer"

    def test_missing_expected_answer(self):
        """Question without expected_answer should return missing_expected_answer."""
        question = Question(
            challenge_id=1,
            question_text="What?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer=None,
            answer_type="exact",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "any answer")
        assert points == 0
        assert status == "missing_expected_answer"

    def test_invalid_answer_type(self):
        """Unknown answer type should return invalid_answer_type."""
        question = Question(
            challenge_id=1,
            question_text="What?",
            question_type="text",
            required=True,
            points=50,
            order=1,
            expected_answer="answer",
            answer_type="unknown_type",
            case_sensitive=False,
        )

        points, status = validate_answer(question, "answer")
        assert points == 0
        assert status == "invalid_answer_type"

    def test_multiple_choice_with_spaces(self):
        """Multiple choice options should handle extra spaces correctly."""
        question = Question(
            challenge_id=1,
            question_text="What framework?",
            question_type="text",
            required=True,
            points=75,
            order=2,
            expected_answer="  Flask  |  Django  |  FastAPI  ",
            answer_type="multiple_choice",
            case_sensitive=False,
        )

        # Each option is trimmed
        points, status = validate_answer(question, "Flask")
        assert points == 75
        assert status == "correct"

        points, status = validate_answer(question, "Django")
        assert points == 75
        assert status == "correct"
