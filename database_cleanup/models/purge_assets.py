# Copyright 2024 Avanzosc <https://avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CleanupPurgeLineAssets(models.TransientModel):
    _inherit = "cleanup.purge.line"
    _name = "cleanup.purge.line.assets"
    _description = "Cleanup Purge Line Assets"

    wizard_id = fields.Many2one(
        "cleanup.purge.wizard.assets", "Purge Wizard", readonly=True
    )

    def purge(self):
        """
        Uninstall assets upon manual confirmation, then reload
        the database.
        """
        # Obtener todos los módulos que están instalados
        _logger.info("Fetching installed modules...")
        installed_modules = self.env["ir.module.module"].search([("state", "=", "installed")]).mapped("name")
        _logger.info("Installed modules: %s", installed_modules)

        # Buscar todos los assets en la base de datos
        _logger.info("Searching for assets in the database...")
        try:
            all_assets = self.env["ir.asset"].search([
                ("path", "not in", installed_modules)
            ])
        except Exception as e:
            _logger.error("Error fetching assets: %s", e)
            raise UserError(_("Could not fetch assets from the database."))

        _logger.info("Found assets to purge: %s", all_assets.mapped("path"))

        if not all_assets:
            _logger.info("No assets found to purge.")
            return True

        _logger.info("Purging assets: %s", ", ".join(all_assets.mapped("path")))

        # Eliminar los assets que no pertenecen a módulos instalados
        all_assets.unlink()

        return self.write({"purged": True})

class CleanupPurgeWizardAssets(models.TransientModel):
    _inherit = "cleanup.purge.wizard"
    _name = "cleanup.purge.wizard.assets"
    _description = "Purge assets from all modules"

    @api.model
    def find(self):
        res = []
        IrModule = self.env["ir.module.module"]

        # Obtener una lista de todos los módulos
        _logger.info("Searching for all modules...")
        all_modules = IrModule.search([])
        _logger.info("Found all modules: %s", all_modules.mapped("name"))

        # Buscar los assets relacionados con los módulos (usa el modelo correcto)
        _logger.info("Searching for assets related to all modules...")
        try:
            all_assets = self.env["ir.asset"].search([("module_id", "in", all_modules.ids)])  # Cambia aquí si el modelo es diferente
        except Exception as e:
            _logger.error("Error fetching assets: %s", e)
            raise UserError(_("Could not fetch assets related to modules."))

        _logger.info("Found assets to purge: %s", all_assets.mapped("path"))

        for asset in all_assets:
            _logger.info("Adding asset to purge list: %s (ID: %s)", asset.path, asset.id)
            res.append((0, 0, {"name": asset.path, "asset_id": asset.id}))

        _logger.info("Total assets to purge: %d", len(res))

        return res

    purge_line_ids = fields.One2many(
        "cleanup.purge.line.assets", "wizard_id", "Assets to purge"
    )
