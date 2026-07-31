"""Unit tests for tools/comms-lint.py (stdlib unittest only).

comms-lint.py has a hyphen in its filename, so it cannot be imported by
name; it is loaded with importlib.util.spec_from_file_location instead.

Run: python3 -m unittest discover -s tools -p 'test_*.py'   (from repo root)
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(HERE, "comms-lint.py")

_spec = importlib.util.spec_from_file_location("comms_lint", MODULE_PATH)
comms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(comms)

CATEGORY_IDS = set(comms.CATEGORY_IDS)


def run_cli(argv, stdin_text=""):
    """Run the CLI in-process; return (exit_code, stdout_text)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = comms.main(argv, stdin=io.StringIO(stdin_text))
    return code, buf.getvalue()


class CategoryFireTests(unittest.TestCase):
    """Each of the 10 categories fires on a positive example."""

    def _count(self, text, cid):
        return comms.lint_text(text)["counts"][cid]

    def test_long_sentence_fires(self):
        text = ("This sentence contains far more than twenty words in total "
                "and it keeps going well past the threshold without stopping "
                "for a moment.")
        self.assertGreater(self._count(text, "long_sentence"), 0)

    def test_passive_voice_fires(self):
        self.assertGreater(
            self._count("The task was completed by the agent yesterday.", "passive_voice"), 0)

    def test_nominalization_fires(self):
        self.assertGreater(
            self._count("We will perform an analysis of the results.", "nominalization"), 0)

    def test_phrasal_verb_fires(self):
        self.assertGreater(
            self._count("Let me reach out to the maintainer.", "phrasal_verb"), 0)

    def test_marketing_adjective_fires(self):
        self.assertGreater(
            self._count("This is a seamless integration.", "marketing_adjective"), 0)

    def test_hedge_opener_fires(self):
        self.assertGreater(
            self._count("It is important to note that the build failed.", "hedge_opener"), 0)

    def test_banned_word_fires(self):
        self.assertGreater(self._count("Please utilize the new tool.", "banned_word"), 0)

    def test_banned_word_fires_on_inflection(self):
        self.assertGreater(self._count("We leveraged the existing setup.", "banned_word"), 0)

    def test_vague_referent_fires(self):
        self.assertGreater(
            self._count("Check the file and tell me what you see.", "vague_referent"), 0)

    def test_vague_quantifier_fires(self):
        self.assertEqual(
            self._count("There were several issues and about 5 fixes.", "vague_quantifier"), 2)

    def test_vague_quantifier_about_requires_digit(self):
        self.assertEqual(
            self._count("Let me think about the plan.", "vague_quantifier"), 0)

    def test_long_paragraph_fires(self):
        self.assertGreater(
            self._count("One. Two. Three. Four. Five. Six. Seven.", "long_paragraph"), 0)


class VagueReferentExceptionTests(unittest.TestCase):
    """Rule-8 exception: a resolvable referent in the same sentence
    suppresses vague_referent. This is the most important behavior of the
    linter, so it is tested explicitly."""

    def test_path_file_line_referent_suppresses(self):
        text = "The file src/main.py:42 is stale."
        self.assertEqual(comms.lint_text(text)["counts"]["vague_referent"], 0)

    def test_backtick_referent_suppresses(self):
        text = "Check the file `config.json` before continuing."
        self.assertEqual(comms.lint_text(text)["counts"]["vague_referent"], 0)

    def test_absolute_path_referent_suppresses(self):
        text = "The file /tmp/out.log is huge."
        self.assertEqual(comms.lint_text(text)["counts"]["vague_referent"], 0)

    def test_function_referent_suppresses(self):
        text = "The function in src/parse.py:12 fails."
        self.assertEqual(comms.lint_text(text)["counts"]["vague_referent"], 0)

    def test_exception_is_per_sentence(self):
        text = "The file is stale. See src/main.py:42 for the fix."
        self.assertEqual(comms.lint_text(text)["counts"]["vague_referent"], 1)


class CodeExclusionTests(unittest.TestCase):
    def test_fenced_code_excluded_from_scoring(self):
        text = ("The parser is fast.\n"
                "```\nutilize leverage facilitate ensure\n```\n"
                "It is seamless.\n")
        r = comms.lint_text(text)
        self.assertEqual(r["counts"]["banned_word"], 0)
        self.assertEqual(r["counts"]["marketing_adjective"], 1)
        self.assertEqual(r["words"], 7)

    def test_indented_code_excluded_from_scoring(self):
        text = ("The parser is fast.\n"
                "    utilize leverage facilitate ensure\n"
                "It is seamless.\n")
        r = comms.lint_text(text)
        self.assertEqual(r["counts"]["banned_word"], 0)
        self.assertEqual(r["words"], 7)


class StatusLineTests(unittest.TestCase):
    def test_report_mode_flags_missing_status(self):
        code, _ = run_cli(["--mode", "report"],
                          stdin_text="The deploy finished.\nAll green.\n")
        _, out = run_cli(["--mode", "report", "--json"],
                         stdin_text="The deploy finished.\n")
        self.assertIs(json.loads(out)["missing_status_line"], True)
        self.assertEqual(code, 1)

    def test_report_mode_accepts_present_status(self):
        for first_line in ("Status: done", "done", "blocked", "CONFIRMED"):
            _, out = run_cli(["--mode", "report", "--json"],
                             stdin_text=first_line + "\nmore prose.\n")
            self.assertIs(json.loads(out)["missing_status_line"], False, first_line)
        code, _ = run_cli(["--mode", "report"], stdin_text="Status: done\nmore prose.\n")
        self.assertEqual(code, 0)

    def test_message_mode_skips_status_check(self):
        _, out = run_cli(["--json"], stdin_text="The deploy finished.\n")
        self.assertIsNone(json.loads(out)["missing_status_line"])
        code, _ = run_cli([], stdin_text="The deploy finished.\n")
        self.assertEqual(code, 0)


class ExitCodeTests(unittest.TestCase):
    def test_clean_text_scores_zero_and_exits_zero(self):
        text = "The parser reads src/main.py:42.\n"
        r = comms.lint_text(text)
        self.assertEqual(r["score"], 0.0)
        self.assertEqual(r["total"], 0)
        code, _ = run_cli([], stdin_text=text)
        self.assertEqual(code, 0)

    def test_violating_text_exits_one_with_breakdown(self):
        text = ("It is important to note that the file was utilized to "
                "facilitate several seamless improvements which were then "
                "leveraged.\n")
        code, out = run_cli([], stdin_text=text)
        self.assertEqual(code, 1)
        self.assertIn("score: ", out)
        self.assertIn("banned_word: ", out)

    def test_max_score_flag_relaxes_exit_code(self):
        text = ("It is important to note that the file was utilized to "
                "facilitate several seamless improvements which were then "
                "leveraged.\n")
        self.assertEqual(run_cli([], stdin_text=text)[0], 1)
        self.assertEqual(run_cli(["--max-score", "100"], stdin_text=text)[0], 0)


class OutputShapeTests(unittest.TestCase):
    def test_json_has_all_keys_and_all_categories(self):
        _, out = run_cli(["--json", "--mode", "report"],
                         stdin_text="Status: done\nEverything is fine.\n")
        data = json.loads(out)
        self.assertEqual(
            sorted(data.keys()),
            sorted(["counts", "total", "words", "score", "missing_status_line"]),
        )
        self.assertEqual(set(data["counts"].keys()), CATEGORY_IDS)
        self.assertIs(data["missing_status_line"], False)
        self.assertEqual(data["score"], 0.0)

    def test_human_output_omits_zero_categories(self):
        _, out = run_cli([], stdin_text="The parser reads src/main.py:42.\n")
        self.assertNotIn("long_sentence:", out)
        self.assertIn("total: 0", out)
        self.assertIn("words: 4", out)
        self.assertIn("score: 0.00 violations/100 words", out)


class SentenceSplittingTests(unittest.TestCase):
    def test_decimals_and_abbreviations_do_not_split_sentences(self):
        text = "The value is 3.14 and e.g. Dr. Smith said so. That's all."
        self.assertEqual(len(comms.split_sentences(text)), 2)

    def test_ellipsis_does_not_split_sentences(self):
        self.assertEqual(len(comms.split_sentences("Wait for it... then go.")), 1)


class FileInputTests(unittest.TestCase):
    def test_multiple_files_are_concatenated(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "a.txt")
            p2 = os.path.join(d, "b.txt")
            with open(p1, "w") as fh:
                fh.write("One sentence.")
            with open(p2, "w") as fh:
                fh.write("Two sentences here.")
            code, out = run_cli([p1, p2, "--json"])
            data = json.loads(out)
            self.assertEqual(data["words"], 5)
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
