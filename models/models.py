# -*- coding: utf-8 -*-

from odoo import models, fields

from Questgen import main

from . import pipelines
import logging

_logger = logging.getLogger(__name__)


class QGen(models.Model):
    _name = "slide.qgen"
    _description = "quetion generation"

    name = fields.Char(string="Content name")
    origin = fields.Text(string="Text to generate quetions")
    channel_name = fields.Many2one("slide.channel", string="")
    result = fields.Text(string="Result")
    slide_name = fields.Many2one("slide.slide", string="")
    ml_name = fields.Selection(
        [
            ("question_generation", "patil-suraj/question_generation"),
            ("Questgen.ai", "ramsrigouthamg/Questgen.ai"),
        ],
        string="",
    )
    spliter = fields.Char(
        string="Spliter for text",
        defaul="----------------------------------------------",
    )
    question_ids = fields.One2many(
        "slide.question", "gen_q_id", string="Questions", readonly=False
    )

    def question_generation(self, nlp):
        res = []
        for seq in self.origin.split(self.spliter):
            try:
                quiz = nlp(seq)
                res.append(
                    {
                        "q": quiz["question"],
                        "a": [
                            quiz["answer"],
                            "Not a {}".format(quiz["answer"].lower()),
                        ],
                    }
                )
            except ValueError:
                _logger.error("Problem with:")
                _logger.error(seq)
                continue
        return res

    def quesgen_ai_bool(self, qe):
        # Generate boolean (Yes/No) Questions, now it's random
        res = []

        for seq in self.origin.split(self.spliter):
            output = qe.predict_boolq({"input_text": seq})
            for quiz in output["Boolean Questions"]:
                res.append(
                    {
                        "q": quiz,
                        "a": [
                            "Yes",
                            "No",
                        ],
                    }
                )
        return res

    def gen_question_generation(self):
        if self.ml_name == "question_generation":
            nlp = pipelines.pipeline("question-generation")
            qag = self.question_generation(nlp)
        elif self.ml_name == "Questgen.ai":
            qe = main.BoolQGen()
            # qg = main.QGen()
            qag = self.quesgen_ai_bool(qe)
        self.slide_name = self.env["slide.slide"].create(
            {
                "name": self.name,
                "slide_type": "quiz",
                "channel_id": self.channel_name.id,
            }
        )
        for quiz in qag:
            q_id = self.env["slide.question"].create(
                {
                    "question": quiz["q"],
                    "slide_id": self.slide_name.id,
                    "gen_q_id": self.id,
                }
            )
            self.env["slide.answer"].create(
                {
                    "text_value": quiz["a"],
                    "question_id": q_id.id,
                    "is_correct": True,
                }
            )
            self.env["slide.answer"].create(
                {
                    "text_value": quiz["a"],
                    "question_id": q_id.id,
                    "is_correct": False,
                }
            )
        self.result = str(qag)

    def del_questions_and_content(self):
        for q in self.question_ids:
            q.unlink()
        self.slide_name.unlink()
