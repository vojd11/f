# -*- coding: utf-8 -*-

from odoo import models, fields


class GenQuestions(models.Model):
    _inherit = "slide.question"
    _description = "add field for gen_q"

    gen_q_id = fields.Many2one("slide.qgen", string="")
