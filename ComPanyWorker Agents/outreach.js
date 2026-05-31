/**
 * Culturally intelligent Outreach Message Generator.
 * We enforce zero generic corporate "fluff". The messages must be sharp, warm, 
 * and engineered for immediate conversion.
 */

/**
 * Generates custom messaging templates tailored to lead metadata.
 * Accounts for location, language rules, and business categories.
 * 
 * @param {Object} lead 
 * @returns {string} Compiled template message
 */
export function generateOutreachMessage(lead) {
  const name = lead.name || 'Partenaire';
  const category = (lead.category || '').toLowerCase();
  
  // Standardize location evaluation
  const locationStr = (lead.location || '').toLowerCase();
  const isCameroon = locationStr.includes('cameroun') || 
                     locationStr.includes('cameroon') || 
                     locationStr.includes('yaounde') || 
                     locationStr.includes('douala') || 
                     locationStr.includes('bafoussam') ||
                     locationStr.includes('garoua') || 
                     (lead.phone && lead.phone.startsWith('+237'));

  // Contextualization helper for business category focus
  let businessAction = 'automatiser vos processus répétitifs';
  if (category.includes('restaurant') || category.includes('café') || category.includes('food')) {
    businessAction = 'automatiser la gestion de vos réservations, commandes et retours clients';
  } else if (category.includes('hotel') || category.includes('lodge') || category.includes('hebergement')) {
    businessAction = 'fluidifier votre service client 24h/24 et automatiser la gestion des réservations de chambres';
  } else if (category.includes('boutique') || category.includes('commerce') || category.includes('store') || category.includes('vente')) {
    businessAction = 'automatiser le suivi de vos commandes clients et booster vos ventes via WhatsApp';
  } else if (category.includes('clinique') || category.includes('sante') || category.includes('medical') || category.includes('health')) {
    businessAction = 'automatiser la prise de rendez-vous de vos patients et le suivi de vos consultations';
  } else if (category.includes('school') || category.includes('ecole') || category.includes('formation')) {
    businessAction = 'automatiser les inscriptions des étudiants et la communication avec les parents d\'élèves';
  }

  // 1. Cameroonian Localization
  if (isCameroon) {
    // English-speaking region check (e.g. Southwest / Northwest or containing 'bamenda', 'buea')
    const isEnglishRegion = locationStr.includes('buea') || 
                            locationStr.includes('bamenda') || 
                            locationStr.includes('limbe');

    if (isEnglishRegion) {
      return `Hello ${name}, I am from Giantect Empire in Yaoundé. We support businesses in automating their daily operations using AI. For a business in ${lead.category || 'your sector'}, we can help you ${businessAction.replace('vos', 'your').replace('votre', 'your').replace('booster vos', 'boost your').replace('fluidifier', 'streamline')}. Do you have 5 minutes this week for a quick WhatsApp demo?`;
    } else {
      // Standard French-speaking Cameroonian warm, direct greeting
      return `Bonjour ${name}, je suis de Giantect Empire à Yaoundé. Nous aidons les entreprises à automatiser leurs opérations avec l'IA. Pour un établissement spécialisé dans le secteur (${lead.category || 'votre domaine'}), nous pouvons ${businessAction}. Avez-vous 5 minutes cette semaine pour une démo rapide sur WhatsApp ?`;
    }
  }

  // 2. International Context (US / Europe / Standard professional)
  const isEnglishLoc = locationStr.includes('us') || 
                       locationStr.includes('usa') || 
                       locationStr.includes('united states') || 
                       locationStr.includes('uk') || 
                       locationStr.includes('london') ||
                       locationStr.includes('europe') ||
                       locationStr.includes('canada');

  if (isEnglishLoc) {
    return `Hello ${name}, this is Giantect Empire. We deploy autonomous Agentic AI systems to streamline operations and eliminate manual workflow redundancies. In the ${lead.category || 'your business'} space, our agents automate client interaction and data synchronization. Are you available for a brief 5-minute call this week?`;
  } else {
    return `Bonjour ${name}, nous sommes de Giantect Empire. Nous intégrons des systèmes d'IA Agentique autonomes pour automatiser vos flux opérationnels et éliminer les tâches manuelles chronophages. Pour un acteur de l'industrie (${lead.category || 'votre secteur'}), nous déployons des agents capables de ${businessAction}. Seriez-vous disponible cette semaine pour un échange rapide de 5 minutes ?`;
  }
}
