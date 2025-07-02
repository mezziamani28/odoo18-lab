from odoo import models, fields, api

class Qualification(models.Model):
    _name = 'qualification'
    _description = 'Qualification'
    _rec_name = 'vivier_id'

    partner_id = fields.Many2one('res.partner', string='Compte')
    vivier_id = fields.Many2one('base.siren', string='Vivier')
    siret_id = fields.Many2one('base.siren', string='Vivier')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunities')
    @api.onchange('opportunity_id')
    def onchange_opportunity_id(self):
        if self.opportunity_id.vivier_id:
            self.vivier_id = self.opportunity_id.vivier_id.id
        if self.opportunity_id.partner_id:
            self.partner_id = self.opportunity_id.partner_id.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id.vivier_id:
            self.vivier_id = self.partner_id.vivier_id.id

    @api.onchange('vivier_id')
    def onchange_vivier_id(self):
        if self.vivier_id.partner_id:
            self.partner_id = self.vivier_id.partner_id.id

    qualification_existante = fields.Boolean("Qualification existante ?")
    date_derniere_qualif = fields.Date("Date dernière Qualif.")
    date_rappel = fields.Date("Date Rappel")
    date_dernier_rappel = fields.Date("Date dernier Rappel")

    fixe = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Fixe')
    mobile = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Mobile')
    monetique = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Monétique')
    monetique_nb_c = fields.Integer("Monétique Nb C.")
    internet = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Internet')
    securite = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Sécurité')

    fixe_nb_c = fields.Integer("Fixe Nb C.")
    mobile_nb_c = fields.Integer("Mobile Nb C.")
    internet_nb_c = fields.Integer("Internet Nb C.")
    securite_nb_c = fields.Integer("Sécurité Nb C.")
    total_nb_c = fields.Integer("Total Nb C.")

    qualification_percent = fields.Float("% Qualification")
    qualifie_le = fields.Date("Qualifié le")
    qualifie_par = fields.Many2one('res.users', string="Qualifié par")
