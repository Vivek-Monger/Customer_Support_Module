from odoo import http
from odoo.http import request
import json

class FAQController(http.Controller):
    
    @http.route('/faq/dashboard', type='http', auth='user', website=True)
    def faq_dashboard(self, **kwargs):
        """Render FAQ dashboard"""
        faqs = request.env['customer.support.faq'].search([('active', '=', True)], order='sequence, id')
        return request.render('your_module_name.faq_dashboard_template', {
            'faqs': faqs
        })
    
    @http.route('/faq/get_all', type='json', auth='user')
    def get_all_faqs(self, **kwargs):
        """Get all FAQs as JSON"""
        faqs = request.env['customer.support.faq'].search([('active', '=', True)], order='sequence, id')
        return [{
            'id': faq.id,
            'name': faq.name,
            'answer': faq.answer,
            'last_updated': faq.last_updated.strftime('%b %d, %Y') if faq.last_updated else '',
        } for faq in faqs]
    
    @http.route('/faq/create', type='json', auth='user')
    def create_faq(self, name, answer, category_id=None, **kwargs):
        """Create a new FAQ"""
        vals = {
            'name': name,
            'answer': answer,
        }
        if category_id:
            vals['category_id'] = category_id
        
        faq = request.env['customer.support.faq'].create(vals)
        return {
            'id': faq.id,
            'name': faq.name,
            'answer': faq.answer,
            'last_updated': faq.last_updated.strftime('%b %d, %Y') if faq.last_updated else '',
        }
    
    @http.route('/faq/update', type='json', auth='user')
    def update_faq(self, faq_id, name=None, answer=None, **kwargs):
        """Update an existing FAQ"""
        faq = request.env['customer.support.faq'].browse(faq_id)
        if not faq.exists():
            return {'error': 'FAQ not found'}
        
        vals = {}
        if name:
            vals['name'] = name
        if answer:
            vals['answer'] = answer
        
        faq.write(vals)
        return {
            'id': faq.id,
            'name': faq.name,
            'answer': faq.answer,
            'last_updated': faq.last_updated.strftime('%b %d, %Y') if faq.last_updated else '',
        }
    
    @http.route('/faq/delete', type='json', auth='user')
    def delete_faq(self, faq_id, **kwargs):
        """Delete an FAQ"""
        faq = request.env['customer.support.faq'].browse(faq_id)
        if not faq.exists():
            return {'error': 'FAQ not found'}
        
        faq.unlink()
        return {'success': True}