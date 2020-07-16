# -*- coding: utf-8 -*-
# Part of BJustiz. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def action_bom_list_price(self):
        templates = self.filtered(lambda t: t.product_variant_count == 1 and t.bom_count > 0)
        if templates:
            return templates.mapped('product_variant_id').action_bom_list_price()

    def button_bom_list_price(self):
        templates = self.filtered(lambda t: t.product_variant_count == 1 and t.bom_count > 0)
        if templates:
            return templates.mapped('product_variant_id').button_bom_list_price()

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Product'

    def action_bom_list_price(self):
        boms_to_recompute = self.env['mrp.bom'].search(['|', ('product_id', 'in', self.ids), '&', ('product_id', '=', False), ('product_tmpl_id', 'in', self.mapped('product_tmpl_id').ids)])
        for product in self:
            product.list_price = product._get_list_price_from_bom(boms_to_recompute)

    def button_bom_list_price(self):
        self.ensure_one()
        self.list_price = self._get_list_price_from_bom()

    def _get_list_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(product=self)
        return self._compute_bom_list_price(bom, boms_to_recompute=boms_to_recompute)

    def _compute_bom_list_price(self, bom, boms_to_recompute=False):
        self.ensure_one()
        if not bom:
            return self.list_price
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_total = line.product_id._compute_bom_list_price(line.child_bom_id, boms_to_recompute=boms_to_recompute)
                total += line.product_id.uom_id._compute_price(child_total, line.product_uom_id) * line.product_qty
            else:
                total += line.product_id.uom_id._compute_price(line.product_id.list_price, line.product_uom_id) * line.product_qty
        return bom.product_uom_id._compute_price(total / bom.product_qty, self.uom_id)
