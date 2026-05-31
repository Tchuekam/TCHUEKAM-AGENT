import { generateOutreachMessage } from './outreach.js';

/**
 * Calculates priority score based on lead data density:
 * - website + phone + email = High (3)
 * - only phone = Medium (2)
 * - only email = Low (1)
 * Other fallbacks:
 * - Any record with a phone is Medium (2) or High (3)
 * - Any record without a phone, but with an email is Low (1)
 */
export function calculatePriorityScore(lead) {
  const hasPhone = !!(lead.phone && lead.phone.trim() !== '');
  const hasEmail = !!(lead.email && lead.email.trim() !== '');
  const hasWebsite = !!(lead.website && lead.website.trim() !== '' && lead.website !== 'N/A');

  if (hasWebsite && hasPhone && hasEmail) {
    return 3; // High
  } else if (hasPhone) {
    return 2; // Medium
  } else if (hasEmail) {
    return 1; // Low
  }
  return 1; // Fallback
}

/**
 * Formats a lead list into the strict queue payload consumed by the NEXUS outreach agent.
 * Output per lead: { name, phone, email, intro_message_template, source, priority_score }
 * 
 * @param {Array} leads - Raw database records
 * @returns {Array} Formatted NEXUS leads queue
 */
export function formatNexusQueue(leads) {
  return leads.map(lead => {
    const priority = calculatePriorityScore(lead);
    
    // Set a dummy template if not pre-populated in database
    const messageTemplate = lead.message_template || generateOutreachMessage(lead);

    return {
      name: lead.name,
      phone: lead.phone || '',
      email: lead.email || '',
      intro_message_template: messageTemplate,
      source: lead.source,
      priority_score: priority
    };
  });
}
