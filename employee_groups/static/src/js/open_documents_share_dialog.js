import { registry } from "@web/core/registry";
import { DocumentsPermissionPanel } from "@documents/components/documents_permission_panel/documents_permission_panel";
/**
 * Opens the document sharing dialog for employee groups
 * @param {Object} env - Odoo environment
 * @param {Object} params - Parameters including document_ids, partner_ids, etc.
 */
async function openDocumentsShareDialog(env, { params }) {
    const {
        document_ids = [],
        partner_ids = [],
        is_single_document = false,
        valid_employees = [],
        invalid_employees = []
    } = params || {};
    try {
        if (!document_ids.length) {
            env.services.notification.add('No documents selected to share', { type: 'warning' });
            return;
        }
        if (invalid_employees.length > 0) {
            const invalidEmployeeNames = invalid_employees.join(', ');
            env.services.notification.add(
                `Warning: These employees don't have a user account or partner and cannot receive documents: ${invalidEmployeeNames}`,
                { type: 'warning', title: 'User Account Required', sticky: true }
            );
        }
        // Check if we have valid partners to share with
        if (!partner_ids.length) {
            env.services.notification.add('No employees with user accounts found in the group', { type: 'warning' });
            return;
        }
        if (is_single_document && document_ids.length === 1) {
            await handleSingleDocumentSharing(env, document_ids[0], partner_ids, valid_employees);
        } else {
            await handleMultipleDocumentSharing(env, document_ids, partner_ids, valid_employees);
        }
    } catch (error) {
        console.error('Error in share dialog:', error);
        env.services.notification.add(`Error: ${error.message}`, { type: 'danger' });
    }
}
/**
 * Handle sharing for a single document using the permission panel
 */
async function handleSingleDocumentSharing(env, documentId, partnerIds, valid_employees) {
    try {
        // Pre-share the document with all valid partners
        const partnersAccess = {};
        for (const partnerId of partnerIds) {
            partnersAccess[partnerId] = ['view', null]; // role: view, expiration_date: null
        }
        await env.services.orm.call(
            'documents.document',
            'action_update_access_rights',
            [documentId],
            {
                partners: partnersAccess,
                notify: false,
                message: "Pre-shared with Employee Group"
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
        const employeeNames = valid_employees.join(', ');
        env.services.notification.add(
            `Permission panel opened with employees pre-selected: ${employeeNames}`,
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
/**
 * Handle sharing for multiple documents using direct API calls
 */
async function handleMultipleDocumentSharing(env, documentIds, partnerIds, valid_employees) {
    try {
        const partnersAccess = {};
        for (const partnerId of partnerIds) {
            partnersAccess[partnerId] = ['view', null]; // role: view, expiration_date: null
        }
        // Share each document with all valid partners
        for (const documentId of documentIds) {
            await env.services.orm.call(
                'documents.document',
                'action_update_access_rights',
                [documentId],
                {
                    partners: partnersAccess,
                    notify: true,
                    message: "Shared via Employee Groups"
                }
            );
        }
        // Show success notification
        const employeeNames = valid_employees.join(', ');
        const message = `Successfully shared ${documentIds.length} documents with employees: ${employeeNames}`;
        env.services.notification.add(
            message,
            { type: 'success', title: 'Documents Shared' }
        );
    } catch (error) {
        console.error('Error sharing documents:', error);
        env.services.notification.add(
            `Error sharing documents: ${error.message}`,
            { type: 'danger' }
        );
    }
}
registry.category("actions").add("open_documents_share_dialog", openDocumentsShareDialog);