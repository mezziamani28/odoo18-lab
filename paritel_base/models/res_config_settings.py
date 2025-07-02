from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

import csv
import io
import logging
import requests
import base64
import os
from odoo.tools import ustr

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    import_file_path_0 = fields.Char(string=' Chemin du fichier Stock Etablissement')
    import_file_path_1 = fields.Char(string=' Chemin du fichier Stock Unite Legale')

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('base_siren.import_file_path', self.import_file_path)
        self.env['ir.config_parameter'].sudo().set_param('base_siren.import_file_path_1', self.import_file_path_1)

    def get_values(self):
        res = super().get_values()
        res.update({
            'import_file_path': self.env['ir.config_parameter'].sudo().get_param('base_siren.import_file_path'),
            'import_file_path_1': self.env['ir.config_parameter'].sudo().get_param('base_siren.import_file_path_1'),
        })
        return res
