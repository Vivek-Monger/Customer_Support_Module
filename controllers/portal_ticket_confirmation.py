from odoo import http
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)

class CustomerSupportTicketConfirmation(http.Controller):
    def _priority_label(self, priority):
        return {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent'
        }.get(priority, 'Low')

    # Confirmation Page
    @http.route(
        ['/my/tickets/create/confirm'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True
    )
    def portal_ticket_confirm(self, **post):
        """Show confirmation page and store files temporarily in session"""
        
        _logger.info("="*80)
        _logger.info("CONFIRMATION PAGE - Processing files")
        
        # Get previously stored files (if user went back and is resubmitting)
        existing_files = request.session.get('temp_ticket_files', [])
        _logger.info(f"Existing files in session: {len(existing_files)}")
        
        # Handle NEW file attachments
        files = request.httprequest.files.getlist('attachment')
        _logger.info(f"New files received: {len(files)}")
        
        # Start with existing files (if any)
        file_data_list = existing_files.copy()
        
        # Add new files
        for f in files:
            if f and f.filename:
                try:
                    file_content = f.read()
                    if file_content:
                        # Check if file already exists (avoid duplicates)
                        if not any(existing['filename'] == f.filename for existing in file_data_list):
                            file_data_list.append({
                                'filename': f.filename,
                                'content': base64.b64encode(file_content).decode('utf-8'),
                                'mimetype': f.content_type or 'application/octet-stream',
                                'size': len(file_content)
                            })
                            _logger.info(f"  ✓ Added file: {f.filename} ({len(file_content)} bytes)")
                        else:
                            _logger.info(f"  → File already exists: {f.filename}")
                except Exception as e:
                    _logger.error(f"  ✗ Error reading file: {str(e)}")
        
        # Store both form data AND files in session
        request.session['temp_ticket_data'] = {
            'subject': post.get('subject'),
            'description': post.get('description'),
            'priority': post.get('priority') or '0',
            'project_id': post.get('project_id'),
        }
        request.session['temp_ticket_files'] = file_data_list
        _logger.info(f"Stored form data and {len(file_data_list)} total files in session")
        
        # Get project name for display
        project_name = ''
        if post.get('project_id'):
            try:
                project = request.env['customer.project'].sudo().browse(int(post.get('project_id')))
                if project.exists():
                    project_name = project.project
            except:
                pass
        
        values = {
            'subject': post.get('subject'),
            'description': post.get('description'),
            'priority': post.get('priority') or '0',
            'priority_label': self._priority_label(post.get('priority')),
            'project_id': post.get('project_id'),
            'project_name': project_name,
            'file_count': len(file_data_list),
            'files': file_data_list,
        }
        
        _logger.info("="*80)
        return request.render(
            'customer_support_module.portal_ticket_confirmation',
            values
        )

    # Back to Edit
    @http.route(
        ['/my/tickets/create/edit'],
        type='http',
        auth='user',
        methods=['GET'],
        website=True
    )
    def portal_ticket_edit(self, **kwargs):
        """Return to edit form with preserved data"""
        
        _logger.info("="*80)
        _logger.info("BACK TO EDIT - Retrieving session data")
        
        # Get data from session
        ticket_data = request.session.get('temp_ticket_data', {})
        file_data_list = request.session.get('temp_ticket_files', [])
        
        _logger.info(f"Retrieved data: {ticket_data}")
        _logger.info(f"Retrieved {len(file_data_list)} files")
        _logger.info("="*80)
        
        # Redirect to create page with flag to load from session
        return request.redirect('/my/tickets/create?from_confirm=1')

    # Final Ticket Creation
    @http.route(
        ['/my/tickets/create/final'],
        type='http',
        auth='user',
        methods=['POST'],
        website=True
    )
    def portal_ticket_create_final(self, **post):
        """Create ticket with files retrieved from session"""
        
        _logger.info("="*80)
        _logger.info("FINAL TICKET CREATION")
        
        ticket_vals = {
            'subject': post.get('subject'),
            'description': post.get('description'),
            'priority': post.get('priority') or '0',
            'create_uid': request.env.uid,
            'phase_id': 'new',
            'new_phase_id': 'new',
        }

        project_id = post.get('project_id')
        if project_id:
            ticket_vals['project_id'] = int(project_id)

        # Create the ticket
        ticket = request.env['customer.support.module'].sudo().create(ticket_vals)
        _logger.info(f"✓ Ticket created: ID={ticket.id}, Ticket#={ticket.ticket_id}")
        
        # Retrieve files from session
        file_data_list = request.session.get('temp_ticket_files', [])
        _logger.info(f"Retrieved {len(file_data_list)} files from session")
        
        attachments = []
        for file_data in file_data_list:
            try:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': file_data['filename'],
                    'type': 'binary',
                    'datas': file_data['content'], 
                    'res_model': 'customer.support.module',
                    'res_id': ticket.id,
                    'mimetype': file_data['mimetype'],
                })
                attachments.append(attachment.id)
                _logger.info(f"  ✓ Attachment created: {file_data['filename']} (ID: {attachment.id})")
            except Exception as e:
                _logger.error(f"  ✗ Error creating attachment: {str(e)}")

        if attachments:
            ticket.write({'attachment_ids': [(6, 0, attachments)]})
            _logger.info(f"✓ Linked {len(attachments)} attachments to ticket")
        
        # Clear session data
        request.session.pop('temp_ticket_files', None)
        request.session.pop('temp_ticket_data', None)
        _logger.info("Session data cleared")
        
        _logger.info("="*80)
        return request.redirect('/my/tickets')