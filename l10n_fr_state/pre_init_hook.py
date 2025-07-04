# Copyright 2017-2022 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo.tools import file_open

logger = logging.getLogger(__name__)



def create_fr_state_xmlid(env):
    generic_create_state_xmlid(env, "l10n_fr_state", "data/res_country_state.xml")


def generic_create_state_xmlid(env, module_name, data_file):
    """This method is also used by l10n_fr_state and l10n_fr_department_oversea"""
    with file_open(f"{module_name}/{data_file}", "rb") as f:
        xml_root = etree.parse(f)
        data = {}  # key = xmlid, value = {"code": "GP", "country_id": "base.gp"}
        for record in xml_root.xpath("//record"):
            xmlid = record.attrib["id"]
            data[xmlid] = {}
            for xfield in record.xpath("field"):
                xfield_dict = xfield.attrib
                data[xmlid][xfield_dict["name"]] = xfield_dict.get("ref") or xfield.text
        logger.debug("generic_create_state_xmlid data=%s", data)
        for xmlid, state_data in data.items():
            country_id = env.ref(state_data["country_id"]).id
            state = env["res.country.state"].search(
                [("code", "=", state_data["code"]), ("country_id", "=", country_id)],
                limit=1,
            )
            if state:
                env["ir.model.data"].create(
                    {
                        "name": xmlid,
                        "res_id": state.id,
                        "module": module_name,
                        "model": "res.country.state",
                    }
                )
                logger.info(
                    "XMLID %s.%s created for state %s code %s",
                    module_name,
                    xmlid,
                    state.name,
                    state.code,
                )
