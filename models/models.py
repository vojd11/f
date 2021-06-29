# -*- coding: utf-8 -*-

from odoo import models, fields

from . import pipelines
import logging

_logger = logging.getLogger(__name__)


class QGen(models.Model):
    _name = "slide.qgen"
    _description = "quetion generation"

    name = fields.Char(string="Sample name")
    origin = fields.Text(string="Text to generate quetions")
    channel_name = fields.Many2one("slide.channel", string="")
    result = fields.Text(string="Result")
    slide_name = fields.Many2one("slide.slide", string="")
    question_ids = fields.One2many(
        "slide.question", "gen_q_id", string="Questions", readonly=False
    )

    def gen_quetions(self):
        ress = []
        nlp = pipelines.pipeline("question-generation")
        for seq in self.origin.split("----------------------------------------------"):
            try:
                ress += nlp(seq)
            except ValueError:
                _logger.error("Problem with:")
                _logger.error(seq)
                continue
        self.slide_name = self.env["slide.slide"].create(
            {
                "name": self.name,
                "slide_type": "quiz",
                "channel_id": self.channel_name.id,
            }
        )
        for quiz in ress:
            q_id = self.env["slide.question"].create(
                {
                    "question": quiz["question"],
                    "slide_id": self.slide_name.id,
                    "gen_q_id": self.id,
                }
            )
            self.env["slide.answer"].create(
                {
                    "text_value": quiz["answer"],
                    "question_id": q_id.id,
                    "is_correct": True,
                }
            )
            self.env["slide.answer"].create(
                {
                    "text_value": "Not a {}".format(quiz["answer"].lower()),
                    "question_id": q_id.id,
                    "is_correct": False,
                }
            )
        self.result = str(ress)
