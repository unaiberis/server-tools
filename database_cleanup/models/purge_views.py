# Copyright 2024 Avanzosc <https://avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CleanupPurgeLineUIView(models.TransientModel):
    _inherit = "cleanup.purge.line"
    _name = "cleanup.purge.line.ui.view"
    _description = "Cleanup Purge Line UI View"

    wizard_id = fields.Many2one(
        "cleanup.purge.wizard.ui.view", "Purge Wizard", readonly=True
    )

    def purge(self):
        """
        Uninstall UI views upon manual confirmation, then reload
        the database.
        """
        # Obtener todos los módulos que están instalados
        _logger.info("Fetching installed modules...")
        installed_modules = self.env["ir.module.module"].search([("state", "=", "installed")]).mapped("name")
        _logger.info("Installed modules: %s", installed_modules)

        # Buscar todas las vistas en la base de datos
        _logger.info("Searching for views in the database...")
        all_views = self.env["ir.ui.view"].search([])

        # Filtrar las vistas cuyo módulo asociado no esté instalado
        views_to_remove = all_views.filtered(lambda view: view.module and view.module not in installed_modules)
        _logger.info("Found views to purge: %s", views_to_remove.mapped("name"))

        if not views_to_remove:
            _logger.info("No views found to purge.")
            return True

        _logger.info("Purging views: %s", ", ".join(views_to_remove.mapped("name")))

        # Eliminar las vistas que no pertenecen a módulos instalados
        views_to_remove.unlink()

        return self.write({"purged": True})


class CleanupPurgeWizardUIView(models.TransientModel):
    _inherit = "cleanup.purge.wizard"
    _name = "cleanup.purge.wizard.ui.view"
    _description = "Purge UI views from obsolete modules"

    @api.model
    def find(self):
        res = []
        IrModule = self.env["ir.module.module"]

        # Obtener todos los módulos
        _logger.info("Searching for all modules...")
        all_modules = IrModule.search([])
        _logger.info("Found all modules: %s", all_modules.mapped("name"))

        # Buscar las vistas relacionadas con los módulos
        _logger.info("Searching for views related to all modules...")
        views_to_purge = self.env["ir.ui.view"].search([("module", "in", all_modules.mapped("name"))])
        _logger.info("Found views to purge: %s", views_to_purge.mapped("name"))

        for view in views_to_purge:
            _logger.info("Adding view to purge list: %s (ID: %s)", view.name, view.id)
            res.append((0, 0, {"name": view.name, "view_id": view.id}))

        _logger.info("Total views to purge: %d", len(res))

        return res

    purge_line_ids = fields.One2many(
        "cleanup.purge.line.ui.view", "wizard_id", "Views to purge"
    )
