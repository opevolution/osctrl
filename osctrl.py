# -*- coding: utf-8 -*-

import time
import datetime
import openerp.addons.decimal_precision as dp
from osv import fields, osv

class osctrl_manufacturer(osv.osv):
    _name ='osctrl.manufacturer'
    _description = 'Manufacturer of Products'
    
    _columns = {
                'name' : fields.char('Manufacturer Name', size=40, required=True),
                }
 
osctrl_manufacturer()   
 
class osctrl_equipment(osv.osv):
    _name ='osctrl.equipment'
    _description = 'Equipment for Maintenance'
    
    _columns = {
                'name' : fields.char('Equipment', size=30, required=True),
                }
 
osctrl_equipment()   
   
class osctrl(osv.osv):
    _name = 'osctrl'
    _description = 'Order Service Control'

    def _get_name(self, cr, uid,context, *args): 
        obj_sequence = self.pool.get('ir.sequence')    
        return obj_sequence.next_by_code(cr, uid, 'osctrl.sequence', context=context)
    
    def _get_delivery(self, cr, uid, ids, context=None):
        dt_atual = datetime.datetime.today()
        dt_new   = dt_atual + datetime.timedelta(days=5)
        return dt_new.strftime('%Y-%m-%d')
        
    def _get_user(self, cr, uid, context=None):
        return self.pool.get('res.users').browse(cr, uid, uid).id

    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates untaxed amount.
        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param uid: The current user ID for security checks
        @param ids: List of selected IDs
        @param field_name: Name of field.
        @param arg: Argument
        @param context: A standard dictionary for contextual values
        @return: Dictionary of values.
        """
        res = {}

        for repair in self.browse(cr, uid, ids, context=context):
            res[repair.id] = 0.0
            for line in repair.products:
                res[repair.id] += line.price_subtotal
            for line in repair.services:
                res[repair.id] += line.price_subtotal
        return res
        
    _columns = {
                'name'          : fields.char('Reference', size=30, required=True),
                'in_date'       : fields.date('Input Date', required=True),
                'delivery_date' : fields.date('Scheduled Output Date'),
                'os_mode'       : fields.selection([
                    ('normal','Normal'),
                    ('gar_int','Guarantee Internal'),
                    ('gar_prod','Guarantee Manufacture'),
                    ('courtesy','Courtesy')
                    ], 'O.S. Mode', required=True),
                'user_id'       : fields.many2one('res.users', 'Attendant', required=True),
                'partner_id'    : fields.many2one('res.partner', 'Partner', required=True),  
                'equipment'     : fields.many2one('osctrl.equipment', 'Equipment', required=True), 
                'manufacturer'  : fields.many2one('osctrl.manufacturer', 'Manufacturer', required=True), 
                'model'         : fields.char('Model', size=40, required=True),
                'serial'        : fields.char('Serial', size=30, required=True),
                'notes'         : fields.text('Internal Notes'),
                'defect'        : fields.text('Problem Description'),
                'guarant_days'  : fields.integer('Warranty Time', required=True),
                'guarant_limit' : fields.date('Warranty Expiration',readonly=True),
                'pricelist_id'  : fields.many2one('product.pricelist', 'Pricelist', help='Pricelist of the selected partner.'),
                'accessories'   : fields.one2many('osctrl.acces.line', 'acces_line_id', 'Accessories Lines'),
                'products'      : fields.one2many('osctrl.prod.line', 'prod_line_id', 'Product Lines'),
                'services'      : fields.one2many('osctrl.serv.line', 'serv_line_id', 'Service Lines'),
                'state'         : fields.selection([
                    ('new','New'),
                    ('draft','Quotation'),
                    ('cancel','Cancelled'),
                    ('confirmed','Confirmed'),
                    ('wait','Waiting'),
                    ('under_repair','Under Repair'),
                    ('ready','Ready to Repair'),
                    ('2binvoiced','To be Invoiced'),
                    ('invoice_except','Invoice Exception'),
                    ('done','Repaired')
                    ], 'Status', readonly=True),

                'amount'        : fields.function(_amount, string='Amount',),
            }
    _defaults = {
                 'name'             : _get_name,
                 'state'            : lambda *a: 'new',
                 'os_mode'          : lambda *a: 'normal',
                 'in_date'          : lambda *a: time.strftime('%Y-%m-%d'),
                 'delivery_date'    : _get_delivery,
                 'guarant_days'     : lambda *a: 30,
                 'user_id'          : _get_user,
                 }
osctrl()

class AccessoriesChangeMixin(object):
    def product_id_change(self, cr, uid, ids, description):
        """ On change of product it sets product .
        @param description: .
        """
        result = {}
        warning = {}

         
        return {'value': result, 'warning': warning}


class osctrl_acces_line(osv.osv, AccessoriesChangeMixin):
    _name = 'osctrl.acces.line'
    _description = 'Accessories Line'
    
    _columns = {
        'acces_line_id'  : fields.many2one('osctrl', 'Service Order Reference',ondelete='cascade',select=True),
        'name'           : fields.char('Description', size=100, select=True,required=True),
        'serial'         : fields.char('Serial', size=30),
    }

osctrl_acces_line()

class ProductChangeMixin(object):
    def product_id_change(self, cr, uid, ids, description):
        """ On change of product it sets product .
        @param description: .
        """
        result = {}
        warning = {}

         
        return {'value': result, 'warning': warning}


class osctrl_prod_line(osv.osv, ProductChangeMixin):
    _name = 'osctrl.prod.line'
    _description = 'Product Line'
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and (line.price_unit * line.product_uom_qty) - line.price_desc or 0
        return res

    _columns = {
        'prod_line_id'   : fields.many2one('osctrl', 'Service Order Reference',ondelete='cascade',select=True),
        'name'           : fields.char('Description', size=64, select=True,required=True),
        'to_invoice'     : fields.boolean('Inv.'),
        'product_id'     : fields.many2one('product.product', 'Product', required=True),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom'    : fields.many2one('product.uom', 'Unit', required=True),
        'price_unit'     : fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_desc'     : fields.float('Discount', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_subtotal' : fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Account')),
        'state'          : fields.selection([
                                            ('draft','Draft'),
                                            ('confirmed','Confirmed'),
                                            ('done','Done'),
                                            ('cancel','Cancelled')], 
                                           'Status', required=True),
    }
    _defaults = {
     'to_invoice'       : lambda *a: True,
     'product_uom_qty'  : lambda *a: 1,
     'price_desc'       : lambda *a: 0,
     'state'            : lambda *a: 'draft',
    }

osctrl_prod_line()

class ServiceChangeMixin(object):
    def service_id_change(self, cr, uid, ids, description):
        """ On change of product it sets product .
        @param description: .
        """
        result = {}
        warning = {}

         
        return {'value': result, 'warning': warning}


class osctrl_serv_line(osv.osv, ServiceChangeMixin):
    _name = 'osctrl.serv.line'
    _description = 'Service Line'
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and (line.price_unit * line.service_uom_qty) - line.price_desc or 0
        return res

    _columns = {
        'serv_line_id'   : fields.many2one('osctrl', 'Service Order Reference',ondelete='cascade',select=True),
        'name'           : fields.char('Description', size=64, select=True,required=True),
        'to_invoice'     : fields.boolean('Inv.'),
        'service_id'     : fields.many2one('product.product', 'Product', required=True),
        'service_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'service_uom'    : fields.many2one('product.uom', 'Unit', required=True),
        'price_unit'     : fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_desc'     : fields.float('Discount', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_subtotal' : fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Account')),
        'state'          : fields.selection([
                                            ('draft','Draft'),
                                            ('confirmed','Confirmed'),
                                            ('done','Done'),
                                            ('cancel','Cancelled')], 
                                           'Status', required=True),
    }
    _defaults = {
     'to_invoice'       : lambda *a: True,
     'service_uom_qty'  : lambda *a: 1,
     'price_desc'       : lambda *a: 0,
     'state'            : lambda *a: 'draft',
    }

osctrl_serv_line()
