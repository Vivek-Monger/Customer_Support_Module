from odoo import models, fields

class phase(models.Model):
    _name = 'progress.phase'
    _description = 'List of Phases'
    _rec_name = "phase"

    phase = fields.Char()
    