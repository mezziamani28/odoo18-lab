from email.policy import default

from datetime import timedelta

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)
try:
    from stdnum.fr import siren, siret
except ImportError:
    logger.debug("Cannot import stdnum")


class CrmLead(models.Model):
    _inherit = "crm.lead"


    vivier_id = fields.Many2one('base.siren', string='Vivier')
    qualification_ids = fields.One2many('qualification', 'opportunity_id', string="Qualifications")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vivier_id = fields.Many2one('base.siren', string='Vivier')
    qualification_ids = fields.One2many('qualification', 'partner_id', string="Qualifications")
    siren = fields.Char(
        string="SIREN",
        size=9,
        tracking=50,
        help="The SIREN number is the official identity "
        "number of the company in France. It composes "
        "the first 9 digits of the SIRET number.",
    )
    nic = fields.Char(
        string="NIC",
        size=5,
        tracking=51,
        help="The NIC number is the official rank number "
        "of this office in the company in France. It "
        "composes the last 5 digits of the SIRET "
        "number.",
    )
    # the original SIRET field is definied in l10n_fr
    # We add an inverse method to make it easier to copy/paste a SIRET
    # from an external source to the partner form view of Odoo
    siret = fields.Char(
        compute="_compute_siret",
        inverse="_inverse_siret",
        store=True,
        precompute=True,
        readonly=False,
        help="The SIRET number is the official identity number of this "
        "company's office in France. It is composed of the 9 digits "
        "of the SIREN number and the 5 digits of the NIC number, ie. "
        "14 digits.",
    )

    parent_is_company = fields.Boolean(
        related="parent_id.is_company", string="Parent is a Company"
    )
    same_siren_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_same_siren_partner_id",
        string="Partner with same SIREN",
        compute_sudo=True,
    )

    @api.depends("siren", "nic")
    def _compute_siret(self):
        """Concatenate the SIREN and NIC to form the SIRET"""
        for rec in self:
            if rec.siren:
                if rec.nic:
                    rec.siret = rec.siren + rec.nic
                else:
                    rec.siret = rec.siren + "*****"
            else:
                rec.siret = False

    def _inverse_siret(self):
        for rec in self:
            if rec.siret:
                if siret.is_valid(rec.siret):
                    rec.write({"siren": rec.siret[:9], "nic": rec.siret[9:]})
                elif siren.is_valid(rec.siret[:9]) and rec.siret[9:] == "*****":
                    rec.write({"siren": rec.siret[:9], "nic": False})
                else:
                    raise ValidationError(_("SIRET '%s' is invalid.") % rec.siret)
            else:
                rec.write({"siren": False, "nic": False})

    @api.depends("siren", "company_id")
    def _compute_same_siren_partner_id(self):
        # Inspired by same_vat_partner_id from 'base' module
        for partner in self:
            same_siren_partner_id = False
            if partner.siren and not partner.parent_id:
                domain = [
                    ("siren", "=", partner.siren),
                    ("parent_id", "=", False),
                ]
                if partner.company_id:
                    domain += [
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "=", partner.company_id.id),
                    ]
                # use _origin to deal with onchange()
                partner_id = partner._origin.id
                if partner_id:
                    domain.append(("id", "!=", partner_id))
                same_siren_partner_id = (
                    self.with_context(active_test=False).search(domain, limit=1)
                ).id or False
            partner.same_siren_partner_id = same_siren_partner_id

    @api.constrains("siren", "nic")
    def _check_siret(self):
        """Check the SIREN's and NIC's keys (last digits)"""
        for rec in self:
            if rec.type == "contact" and rec.parent_id:
                continue
            if rec.nic:
                # Check the NIC type and length
                if not rec.nic.isdigit() or len(rec.nic) != 5:
                    raise ValidationError(
                        _(
                            "The NIC '{nic}' of partner '{partner_name}' is "
                            "incorrect: it must have exactly 5 digits."
                        ).format(nic=rec.nic, partner_name=rec.display_name)
                    )
            if rec.siren:
                # Check the SIREN type, length and key
                if not rec.siren.isdigit() or len(rec.siren) != 9:
                    raise ValidationError(
                        _(
                            "The SIREN '{siren}' of partner '{partner_name}' is "
                            "incorrect: it must have exactly 9 digits."
                        ).format(siren=rec.siren, partner_name=rec.display_name)
                    )
                if not siren.is_valid(rec.siren):
                    raise ValidationError(
                        _(
                            "The SIREN '{siren}' of partner '{partner_name}' is "
                            "invalid: the checksum is wrong."
                        ).format(siren=rec.siren, partner_name=rec.display_name)
                    )
                # Check the NIC key (you need both SIREN and NIC to check it)
                if rec.nic and not siret.is_valid(rec.siren + rec.nic):
                    raise ValidationError(
                        _(
                            "The SIRET '{siret}' of partner '{partner_name}' is "
                            "invalid: the checksum is wrong."
                        ).format(
                            siret=(rec.siren + rec.nic), partner_name=rec.display_name
                        )
                    )

    @api.model
    def _commercial_fields(self):
        # SIREN is the same for the whole company
        # NIC is different for each address
        res = super()._commercial_fields()
        res.append("siren")
        return res

    @api.model
    def _address_fields(self):
        res = super()._address_fields()
        res.append("nic")
        return res

    statut_client = fields.Selection([
        ('froid', 'Froid'),
        ('chaud', 'Chaud'),
        ('client', 'Client'),
        ('ancien', 'Ancien Client'),
        ('ferme', 'Fermé')
    ], string="Statut du Compte", compute="_compute_statut_client", store=True)

    @api.depends(
        'opportunity_ids.date_deadline',
        'opportunity_ids.active',
        'opportunity_ids.probability'
    )
    def _compute_statut_client(self):
        four_years_ago = (fields.Datetime.now() - timedelta(days=4 * 365)).date()
        for partner in self:
            opps = partner.opportunity_ids
            if not opps:
                partner.statut_client = 'froid'
                continue

            opps_won = opps.filtered(lambda o: o.probability == 100)
            ancien_won = opps_won.filtered(lambda o: o.date_deadline and o.date_deadline < four_years_ago)
            opps_open = opps.filtered(lambda o: o.active and o.probability not in [0, 100])
            opps_ferme = all(o.probability == 0.0 and not o.active for o in opps)

            if ancien_won:
                partner.statut_client = 'ancien'
            elif opps_won:
                partner.statut_client = 'client'
            elif opps_open:
                partner.statut_client = 'chaud'
            elif opps_ferme:
                partner.statut_client = 'ferme'

