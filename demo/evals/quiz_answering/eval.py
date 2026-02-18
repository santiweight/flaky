"""
Eval case for quiz answering.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flaky import EvalCase, expect
from quiz_app.answer import answer_question


class QuizAnsweringEval(EvalCase):
    """Tests the quiz answering pipeline on trivia questions."""

    def setUp(self):
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures" / "quizzes"
        manifest_path = fixtures_dir / "manifest.json"
        
        with open(manifest_path) as f:
            self.questions = json.load(f)

    def test_question_1(self):
        q = self.questions[0]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_2(self):
        q = self.questions[1]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_3(self):
        q = self.questions[2]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_4(self):
        q = self.questions[3]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_5(self):
        q = self.questions[4]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_6(self):
        q = self.questions[5]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_7(self):
        q = self.questions[6]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_8(self):
        q = self.questions[7]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_9(self):
        q = self.questions[8]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])

    def test_question_10(self):
        q = self.questions[9]
        answer = answer_question(q["question"], q["choices"])
        expect(answer).to_equal(q["correct"])
