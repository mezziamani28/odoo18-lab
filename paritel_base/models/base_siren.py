import csv
import hashlib
import os
import json
import logging
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import zipfile
import shutil
import requests

# Définition des fichiers SIRENE à traiter
SIRENE_FILES = [
    ("StockEtablissement_utf8.zip", "0"),
    ("StockUniteLegale_utf8.zip", "1"),
]

# Dossier temporaire local à adapter selon l’environnement (prod/dev/cloud)
TMP_DIR = "/Users/mezziamani/Desktop/workspace_kairos/workspace_paritel/sirene"

_logger = logging.getLogger(__name__)


class BaseSiren(models.Model):
    _name = 'base.siren'
    _description = 'Enregistrement SIRET'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nom_unite_legale'

    # Champs principaux
    qualification_ids = fields.One2many('qualification', 'siret_id', string="Qualifications")
    naf_code = fields.Char(string="Code NAF")
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    naf_label = fields.Char(string="Activité")
    phone = fields.Char(string="Téléphone")
    mobile = fields.Char(string="Téléphone1")
    email = fields.Char(string="Email")
    street = fields.Char(string="Rue")
    zip = fields.Char(string="Zip")
    city = fields.Char(string="Ville")
    state_id = fields.Many2one(
        'res.country.state',
        string="Fed. State", domain="[('country_id', '=?', country_id)]"
    )
    statut_client = fields.Selection([
        ('froid', 'Froid'),
        ('chaud', 'Chaud'),
        ('client', 'Client'),
        ('ancien', 'Ancien Client'),
        ('ferme', 'Fermé')
    ], string="Statut du Prospect")

    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    siren = fields.Char(string='SIREN')
    nic = fields.Char(string='NIC')
    siret = fields.Char(string='SIRET', index=True)
    statutDiffusionEtablissement = fields.Char(string='Statut de diffusion')
    dateCreationEtablissement = fields.Date(string='Date de création')
    trancheEffectifsEtablissement = fields.Char(string='Tranche d’effectifs')
    anneeEffectifsEtablissement = fields.Char(string='Année des effectifs')
    activitePrincipaleRegistreMetiersEtablissement = fields.Char(string='Activité principale RM')
    dateDernierTraitementEtablissement = fields.Datetime(string='Date de traitement')

    etablissementSiege = fields.Boolean(string='Est-ce le siège ?')

    # Adresse et localisation
    complementAdresseEtablissement = fields.Char(string='Complément adresse')
    numeroVoieEtablissement = fields.Char(string='N° voie')
    indiceRepetitionEtablissement = fields.Char(string='Indice répétition')
    dernierNumeroVoieEtablissement = fields.Char(string='Dernier N° voie')
    indiceRepetitionDernierNumeroVoieEtablissement = fields.Char(string='Indice rép. dernier N° voie')
    typeVoieEtablissement = fields.Char(string='Type voie')
    libelleVoieEtablissement = fields.Char(string='Libellé voie')
    codePostalEtablissement = fields.Char(string='Code postal')
    libelleCommuneEtablissement = fields.Char(string='Commune')
    libelleCommuneEtrangerEtablissement = fields.Char(string='Commune étrangère')
    distributionSpecialeEtablissement = fields.Char(string='Distribution spéciale')
    codeCommuneEtablissement = fields.Char(string='Code commune')
    codeCedexEtablissement = fields.Char(string='Code Cedex')
    libelleCedexEtablissement = fields.Char(string='Libellé Cedex')
    codePaysEtrangerEtablissement = fields.Char(string='Code pays étranger')
    libellePaysEtrangerEtablissement = fields.Char(string='Pays étranger')
    identifiantAdresseEtablissement = fields.Char(string='ID adresse')
    coordonneeLambertAbscisseEtablissement = fields.Float(string='Coordonnée Lambert X')
    coordonneeLambertOrdonneeEtablissement = fields.Float(string='Coordonnée Lambert Y')

    # Adresse secondaire (doublon SIRENE)
    complementAdresse2Etablissement = fields.Char(string='Complément adresse 2')
    numeroVoie2Etablissement = fields.Char(string='N° voie 2')
    indiceRepetition2Etablissement = fields.Char(string='Indice répétition 2')
    typeVoie2Etablissement = fields.Char(string='Type voie 2')
    libelleVoie2Etablissement = fields.Char(string='Libellé voie 2')
    codePostal2Etablissement = fields.Char(string='Code postal 2')
    libelleCommune2Etablissement = fields.Char(string='Commune 2')
    libelleCommuneEtranger2Etablissement = fields.Char(string='Commune étrangère 2')
    distributionSpeciale2Etablissement = fields.Char(string='Distribution spéciale 2')
    codeCommune2Etablissement = fields.Char(string='Code commune 2')
    codeCedex2Etablissement = fields.Char(string='Code Cedex 2')
    libelleCedex2Etablissement = fields.Char(string='Libellé Cedex 2')
    codePaysEtranger2Etablissement = fields.Char(string='Code pays étranger 2')
    libellePaysEtranger2Etablissement = fields.Char(string='Pays étranger 2')

    dateDebut = fields.Date(string='Date de début')
    enseigne1Etablissement = fields.Char(string='Enseigne 1')
    enseigne2Etablissement = fields.Char(string='Enseigne 2')
    enseigne3Etablissement = fields.Char(string='Enseigne 3')
    denominationUsuelleEtablissement = fields.Char(string='Dénomination usuelle')

    activitePrincipaleEtablissement = fields.Char(string='Activité principale')
    nomenclatureActivitePrincipaleEtablissement = fields.Char(string='Nomenclature activité principale')
    nomenclature_activite_principale_unite_legale = fields.Char("Activité legale")
    caractereEmployeurEtablissement = fields.Char(string='Caractère employeur')
    hash_line = fields.Char(string='Hash ligne', index=True)
    color = fields.Integer(string='Couleur')
    statut_diffusion_unite_legale = fields.Char("Statut diffusion unité légale")
    unite_purgee_unite_legale = fields.Boolean("Unité purgée")
    date_creation_unite_legale = fields.Date("Date création")
    sigle_unite_legale = fields.Char("Sigle")
    sexe_unite_legale = fields.Selection([
        ('1', 'Homme'),
        ('2', 'Femme')
    ], "Sexe")
    prenom1_unite_legale = fields.Char("Prénom 1")
    prenom2_unite_legale = fields.Char("Prénom 2")
    prenom3_unite_legale = fields.Char("Prénom 3")
    prenom4_unite_legale = fields.Char("Prénom 4")
    prenom_usuel_unite_legale = fields.Char("Prénom usuel")
    pseudonyme_unite_legale = fields.Char("Pseudonyme")
    identifiant_association_unite_legale = fields.Char("ID Association")
    tranche_effectifs_unite_legale = fields.Char("Tranche effectifs")
    annee_effectifs_unite_legale = fields.Char("Année effectifs")
    date_dernier_traitement_unite_legale = fields.Date("Date dernier traitement")
    nombre_periodes_unite_legale = fields.Integer("Nombre de périodes")
    nombrePeriodesEtablissement = fields.Integer(string='Périodes')

    categorie_entreprise = fields.Char("Catégorie entreprise")
    annee_categorie_entreprise = fields.Char("Année catégorie entreprise")
    date_debut = fields.Date("Date début")
    etat_administratif_unite_legale = fields.Char("État")
    etatAdministratifEtablissement = fields.Char(string='État administratif')

    nom_unite_legale = fields.Char("Nom", index=True, required=True)
    nom_usage_unite_legale = fields.Char("Nom d'usage")
    denomination_unite_legale = fields.Char("Dénomination")
    denomination_usuelle1_unite_legale = fields.Char("Dénomination usuelle 1")
    denomination_usuelle2_unite_legale = fields.Char("Dénomination usuelle 2")
    denomination_usuelle3_unite_legale = fields.Char("Dénomination usuelle 3")
    categorie_juridique_unite_legale = fields.Char("Catégorie juridique")
    activite_principale_unite_legale = fields.Char("Activité principale unite legale")
    nic_siege_unite_legale = fields.Char("NIC siège")
    economie_sociale_solidaire_unite_legale = fields.Boolean("ESS")
    societe_mission_unite_legale = fields.Boolean("Société à mission")
    caractere_employeur_unite_legale = fields.Char("Employeur Unite legale")
    country_id = fields.Many2one(
        comodel_name='res.country',
        string="Pays",
        help="Pays",
        default=lambda self: self.env.ref('base.fr').id
    )
    etablissements_secondaires_ids = fields.One2many(
        comodel_name='base.siren',
        inverse_name='siren_parent_id',
        string="Établissements secondaires"
    )
    siren_parent_id = fields.Many2one(
        comodel_name='base.siren',
        string="Siège",
        store=True,
        index=True
    )

    # Conversion en contact Odoo
    def action_convert_to_partner(self):
        for record in self:
            if record.partner_id:
                continue
            existing_partner = self.env['res.partner'].search([('name', '=', record.nom_unite_legale)], limit=1)
            if existing_partner and existing_partner.siret == record.siret:
                record.partner_id = existing_partner
            else:
                partner_vals = {
                    'name': record.nom_unite_legale,
                    'street': record.street or record.libelleVoieEtablissement,
                    'zip': record.zip or record.codePostalEtablissement,
                    'city': record.city or record.libelleCommuneEtablissement,
                    'phone': record.phone,
                    'email': record.email,
                    'siret': record.siret,
                    'siren': record.siren,
                    'is_company': True,
                    'vivier_id': record.id,
                }
                new_partner = self.env['res.partner'].create(partner_vals)
                record.partner_id = new_partner

    @api.model
    def launch_all_sirene(self):
        """
        Lance toute la séquence (download, extract, merge, import).
        À appeler depuis un bouton, un cron ou la console.
        """
        os.makedirs(TMP_DIR, exist_ok=True)
        for filename, code in SIRENE_FILES:
            self.with_delay(description=f"Download {filename}").download_one_sirene_file(filename, code)

    @api.model
    def download_one_sirene_file(self, filename, code):
        url = f"https://files.data.gouv.fr/insee-sirene/{filename}"
        local_path = os.path.join(TMP_DIR, filename)
        try:
            _logger.info("Téléchargement de %s", filename)
            with requests.get(url, stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            param_key = f"base_siren.import_zip_path_{code}"
            self.env['ir.config_parameter'].sudo().set_param(param_key, local_path)
            _logger.info("Fichier %s téléchargé avec succès.", filename)
            # Extraction enchaînée !
            self.with_delay(description=f"Extract {filename}").extract_one_sirene_file(local_path, code)
        except Exception as e:
            _logger.exception("Erreur lors du téléchargement de %s : %s", filename, str(e))

    @api.model
    def extract_one_sirene_file(self, zip_path, code):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(TMP_DIR)
                extracted_files = zip_ref.namelist()
                for f in extracted_files:
                    if f.endswith('.csv'):
                        csv_path = os.path.join(TMP_DIR, f)
                        param_key = f"base_siren.import_csv_path_{code}"
                        self.env['ir.config_parameter'].sudo().set_param(param_key, csv_path)
                        _logger.info("Fichier %s extrait vers %s", f, csv_path)
            # Quand extraction du dernier fichier (code == "1") : fusion
            if code == "1":
                self.with_delay(description="Merge CSV SIRENE").launch_merge_job()
        except Exception as e:
            _logger.exception("Erreur lors de l'extraction de %s : %s", zip_path, str(e))

    @api.model
    def _get_merged_path(self, path):
        base, ext = os.path.splitext(path)
        return f"{base}_merged{ext}"

    @api.model
    def launch_merge_job(self):
        param = self.env['ir.config_parameter'].sudo()
        path_main = param.get_param("base_siren.import_csv_path_0")
        path_secondary = param.get_param("base_siren.import_csv_path_1")
        if not path_main or not path_secondary:
            raise ValidationError("Chemins des fichiers CSV non définis.")
        # Headers fusionnés
        with open(path_main, 'r', encoding='utf-8') as f_main, \
             open(path_secondary, 'r', encoding='utf-8') as f_sec:
            header_main = set(csv.DictReader(f_main).fieldnames or [])
            header_sec = set(csv.DictReader(f_sec).fieldnames or [])
            full_headers = sorted(header_main.union(header_sec))
        path_merged = self._get_merged_path(path_main)
        with open(path_merged, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=full_headers)
            writer.writeheader()
        batch_size = 100000   # < 2min/batch !
        total_lines = sum(1 for _ in open(path_main, 'r', encoding='utf-8')) - 1
        batches = (total_lines + batch_size - 1) // batch_size
        for i in range(batches):
            self.with_delay(description=f'Fusion batch {i}').process_main_batch(
                path_main, path_merged, i * batch_size, batch_size, full_headers
            )
        # Ajout du secondaire à la fin
        self.with_delay(priority=90, description='Fusion second file').process_secondary(
            path_secondary, path_merged, full_headers
        )
        # Finalisation (swap et lancement import)
        self.with_delay(priority=100, description='Final merge').finalize_merge(
            path_main, path_merged
        )

    @api.model
    def process_main_batch(self, path_main, path_merged, start_line, batch_size, full_headers):
        seen_sirens = set()
        count = 0
        # Récupère déjà les siren du merged (important en cas de relance)
        with open(path_merged, 'r', encoding='utf-8') as f_merge:
            for row in csv.DictReader(f_merge):
                siren = row.get('siren')
                if siren:
                    seen_sirens.add(siren)
        with open(path_main, 'r', encoding='utf-8') as f_main:
            reader = csv.DictReader(f_main)
            for _ in range(start_line + 1):
                next(reader, None)
            with open(path_merged, 'a', encoding='utf-8', newline='') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=full_headers)
                for i, row in enumerate(reader):
                    if i >= batch_size:
                        break
                    siren = row.get('siren')
                    if siren and siren not in seen_sirens:
                        seen_sirens.add(siren)
                        writer.writerow({key: row.get(key, '') for key in full_headers})
                        count += 1
        _logger.info("Batch %s terminé : %d lignes ajoutées", start_line // batch_size, count)

    @api.model
    def process_secondary(self, path_secondary, path_merged, full_headers):
        seen_sirens = set()
        count = 0
        with open(path_merged, 'r', encoding='utf-8') as f_merge:
            for row in csv.DictReader(f_merge):
                siren = row.get('siren')
                if siren:
                    seen_sirens.add(siren)
        with open(path_secondary, 'r', encoding='utf-8') as f_sec, \
                open(path_merged, 'a', encoding='utf-8', newline='') as f_out:
            reader = csv.DictReader(f_sec)
            writer = csv.DictWriter(f_out, fieldnames=full_headers)
            for row in reader:
                siren = row.get('siren')
                if siren and siren not in seen_sirens:
                    seen_sirens.add(siren)
                    writer.writerow({key: row.get(key, '') for key in full_headers})
                    count += 1
        _logger.info("Fichier secondaire fusionné : %d lignes ajoutées", count)

    @api.model
    def finalize_merge(self, path_main, path_merged):
        backup_path = path_main + ".bak"
        os.replace(path_main, backup_path)
        os.replace(path_merged, path_main)
        _logger.info("Fusion terminée. Ancien fichier sauvegardé : %s", backup_path)
        _logger.info("Nouveau fichier principal : %s", path_main)
        # Import Odoo asynchrone
        self.sudo().with_delay().start_import()

    # --- IMPORT BATCHÉ (asynchrone) ---
    @api.model
    def start_import(self):
        file_path = self.env["ir.config_parameter"].sudo().get_param("base_siren.import_file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValidationError(_("SIRENE file not found."))
        chunk_size = 100000  # <2min/batch!
        batch = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row_index, row in enumerate(reader, 1):
                vals = {key.strip(): val.strip() if val else "" for key, val in zip(headers, row)}
                batch.append(vals)
                if len(batch) >= chunk_size:
                    self._enqueue_batch(batch)
                    batch = []
            if batch:
                self._enqueue_batch(batch)
        _logger.info("SIRENE import successfully launched.")

    def _enqueue_batch(self, batch):
        if not batch:
            return
        try:
            self.env.cr.commit()
            batch_json = json.dumps(batch)
            batch_rec = self.env["base.siren.batch"].sudo().create({"data": batch_json})
            batch_rec.with_delay().process_batch_job()
        except Exception as e:
            _logger.error("Failed to enqueue batch: %s", str(e))
            self.env.cr.rollback()

    # -- DEDUPLICATION/INSERTION --
    @api.model
    def rasage_or_create(self, values):
        if values.get('etatAdministratifEtablissement') != 'A':
            return None
        hash_fields = [str(values.get(field, '')) for field in self._fields if field != 'id']
        raw_string = '|'.join(hash_fields)
        line_hash = hashlib.md5(raw_string.encode('utf-8')).hexdigest()
        values['hash_line'] = line_hash
        for field_name, field in self._fields.items():
            if field_name in values and isinstance(field, fields.Datetime):
                val = values[field_name]
                if val and 'T' in val:
                    try:
                        values[field_name] = datetime.fromisoformat(val).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        _logger.warning("Erreur lors de la conversion datetime pour %s : %s", field_name, e)
        existing = self.search([('hash_line', '=', line_hash)], limit=1)
        if existing:
            return
        return self.create(values)

# --- GESTION DU BATCH ---
class BaseSirenBatch(models.Model):
    _name = 'base.siren.batch'
    _description = "Lot d'import SIREN"
    data = fields.Text(string="Batch JSON")
    def process_batch_job(self):
        batch = json.loads(self.data)
        siren_model = self.env['base.siren']
        for vals in batch:
            siren_model.rasage_or_create(vals)
