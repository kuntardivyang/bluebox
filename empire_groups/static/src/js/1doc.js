/** @odoo-module **/

import { registry } from "@web/core/registry";
import { DocumentsPermissionPanel } from "@documents/components/documents_permission_panel/documents_permission_panel";

async function openDocumentsShareDialog(env, { params }) {
    const { document_ids = [], partner_ids = [], is_single_document = false, portal_employees = [], non_portal_employees = [] } = params || {};
    
    try {
        // Check if we have documents
        if (!document_ids.length) {
            env.services.notification.add('No documents selected to share', { type: 'warning' });
            return;
        }

        console.log('Opening share dialog for documents:', document_ids);
        console.log('Portal employees:', portal_employees);
        console.log('Non-portal employees:', non_portal_employees);

        // Show warning if some employees don't have portal access
        if (non_portal_employees.length > 0) {
            const nonPortalNames = non_portal_employees.join(', ');
            env.services.notification.add(
                `Warning: These employees don't have portal access and cannot receive documents: ${nonPortalNames}`,
                { type: 'warning', title: 'Portal Access Required', sticky: true }
            );
        }

        // Check if we have portal partners to share with
        if (!partner_ids.length) {
            env.services.notification.add('No employees with portal access found in the group', { type: 'warning' });
            return;
        }

        // Single document: Open permission panel with pre-selected portal partners
        if (is_single_document && document_ids.length === 1) {
            const documentId = document_ids[0];
            
            try {
                // Pre-share the document with all portal partners
                const partnersAccess = {};
                for (const partnerId of partner_ids) {
                    partnersAccess[partnerId] = ['view', null]; // role: view, expiration_date: null
                }
                
                console.log('Pre-sharing document with portal partners:', partnersAccess);
                
                await env.services.orm.call(
                    'documents.document', 
                    'action_update_access_rights', 
                    [documentId],
                    {
                        partners: partnersAccess,
                        notify: false,
                        message: "Pre-shared with Employee Group (Portal Users)"
                    }
                );
                
                // Small delay to ensure access records are created
                await new Promise(resolve => setTimeout(resolve, 100));
                
                // Open the DocumentsPermissionPanel
                env.services.dialog.add(DocumentsPermissionPanel, {
                    document: { id: documentId },
                    onChangesSaved: () => {
                        env.services.notification.add(
                            'Document sharing permissions updated successfully',
                            { type: 'success', title: 'Sharing Updated' }
                        );
                    },
                });
                
                // Show success notification
                const portalNames = portal_employees.join(', ');
                env.services.notification.add(
                    `Permission panel opened with portal users pre-selected: ${portalNames}`,
                    { type: 'info', title: 'Share Dialog Ready' }
                );
                
            } catch (error) {
                console.error('Error opening permission panel:', error);
                env.services.notification.add(
                    `Error opening share dialog: ${error.message}`, 
                    { type: 'danger' }
                );
            }
        } 
        // Multiple documents: Share directly with portal partners
        else {
            try {
                const partnersAccess = {};
                for (const partnerId of partner_ids) {
                    partnersAccess[partnerId] = ['view', null]; // role: view, expiration_date: null
                }
                
                // Share each document with all portal partners
                for (const documentId of document_ids) {
                    await env.services.orm.call(
                        'documents.document', 
                        'action_update_access_rights', 
                        [documentId],
                        {
                            partners: partnersAccess,
                            notify: true,
                            message: "Shared via Employee Groups - Portal Access"
                        }
                    );
                }
                
                // Show success notification
                const portalNames = portal_employees.join(', ');
                const message = `Successfully shared ${document_ids.length} documents with portal users: ${portalNames}`;
                
                env.services.notification.add(
                    message, 
                    { type: 'success', title: 'Documents Shared' }
                );
                
                console.log('Documents shared successfully with portal users');
                
            } catch (error) {
                console.error('Error sharing documents:', error);
                env.services.notification.add(
                    `Error sharing documents: ${error.message}`,
                    { type: 'danger' }
                );
            }
        }
        
    } catch (error) {
        console.error('Error in share dialog:', error);
        env.services.notification.add(`Error: ${error.message}`, { type: 'danger' });
    }
}

registry.category("actions").add("open_documents_share_dialog", openDocumentsShareDialog);
