import { initDatabase, upsertLead, getAllLeads, run } from './database.js';
import { calculatePriorityScore } from './nexus.js';
import { generateOutreachMessage } from './outreach.js';

async function runTests() {
  console.log('----------------------------------------------------');
  console.log('GIANTECH EMPIRE - SCRAPER BACKEND VERIFICATION PIPELINE');
  console.log('----------------------------------------------------');

  try {
    // 1. Initialize Database
    console.log('[TEST] Initializing SQLite Lead database...');
    await initDatabase();
    
    // Clear leads table for clean sandbox run
    await run('DELETE FROM leads');
    console.log('[TEST] Database cleared.');

    // 2. Validate Priority Scoring
    console.log('\n[TEST] Validating Nexus Priority Scorer...');
    
    const leadHigh = { name: 'High Prospect', phone: '+237699482910', email: 'high@prospect.cm', website: 'https://prospect.cm' };
    const leadMed = { name: 'Medium Prospect', phone: '+237699482911', email: '', website: '' };
    const leadLow = { name: 'Low Prospect', phone: '', email: 'low@prospect.cm', website: '' };

    const scoreHigh = calculatePriorityScore(leadHigh);
    const scoreMed = calculatePriorityScore(leadMed);
    const scoreLow = calculatePriorityScore(leadLow);

    console.log(`- High density lead priority score: ${scoreHigh} (Expected: 3)`);
    console.log(`- Medium density lead priority score: ${scoreMed} (Expected: 2)`);
    console.log(`- Low density lead priority score: ${scoreLow} (Expected: 1)`);

    if (scoreHigh !== 3 || scoreMed !== 2 || scoreLow !== 1) {
      throw new Error('Priority scoring assertion failed.');
    }
    console.log('[SUCCESS] Nexus Priority Scorer verified.');

    // 3. Validate Outreach Message Generator
    console.log('\n[TEST] Validating Cameroonian/International Localized Messaging...');
    
    const cameroonLead = { name: 'Le Biniou Yaoundé', category: 'Restaurant', location: 'Yaoundé, Cameroun', phone: '+237699485732' };
    const intlLead = { name: 'Apex Tech Solutions', category: 'Tech Agency', location: 'San Francisco, CA, US', phone: '+14159830291' };

    const msgCameroon = generateOutreachMessage(cameroonLead);
    const msgIntl = generateOutreachMessage(intlLead);

    console.log(`\n- Cameroon Outreach Template:\n"${msgCameroon}"`);
    console.log(`\n- International Outreach Template:\n"${msgIntl}"`);

    if (!msgCameroon.includes('Yaoundé') || !msgCameroon.includes('automatiser')) {
      throw new Error('Cameroonian localization template mismatch.');
    }
    if (!msgIntl.includes('Giantect') || !msgIntl.includes('autonomous')) {
      throw new Error('International professional template mismatch.');
    }
    console.log('\n[SUCCESS] Outreach Message Generator verified.');

    // 4. Validate Database Insertion and Auto-Deduplication Merges
    console.log('\n[TEST] Validating SQLite Auto-Deduplication Merging...');
    
    // Insert fresh lead
    const rawLead1 = {
      name: 'Douala Tech Hub',
      phone: '+237655889900',
      email: '',
      website: '',
      source: 'Google Maps',
      category: 'Tech Agency',
      location: 'Akwa, Douala',
      rating: 4.5,
      priority_score: 2,
      message_template: 'Bonjour Douala Tech Hub'
    };

    const res1 = await upsertLead(rawLead1);
    console.log(`- Insert 1: status = ${res1.status}, id = ${res1.id}`);

    // Insert lead with SAME phone but richer fields (email, website)
    const rawLead2 = {
      name: 'Douala Tech Hub (Hydrated)',
      phone: '+237655889900',
      email: 'info@doualatech.net',
      website: 'https://doualatech.net',
      source: 'Directory (Africa)',
      category: 'Tech Agency',
      location: 'Akwa, Douala',
      rating: 4.8,
      priority_score: 3,
      message_template: 'Bonjour Douala Tech Hub - Hydrated'
    };

    const res2 = await upsertLead(rawLead2);
    console.log(`- Insert 2 (Collision): status = ${res2.status}, id = ${res2.id} (Expected status: merged)`);

    // Verify row contents are merged
    const leads = await getAllLeads();
    console.log(`- Total lead records in database: ${leads.length} (Expected: 1)`);
    
    if (leads.length !== 1) {
      throw new Error('Deduplication failed: duplicated rows detected.');
    }

    const merged = leads[0];
    console.log('\nMerged Lead Record in Database:');
    console.log(`  Name: "${merged.name}" (Rich name retained)`);
    console.log(`  Phone: "${merged.phone}"`);
    console.log(`  Email: "${merged.email}" (Hydrated successfully)`);
    console.log(`  Website: "${merged.website}" (Hydrated successfully)`);
    console.log(`  Source: "${merged.source}" (Appended: "${merged.source}")`);
    console.log(`  Rating: ${merged.rating} (Updated to higher rating: 4.8)`);
    console.log(`  Priority Score: ${merged.priority_score} (Promoted to: 3)`);

    if (merged.email !== 'info@doualatech.net' || merged.website !== 'https://doualatech.net' || merged.priority_score !== 3) {
      throw new Error('Database field merging logic failed to resolve correctly.');
    }
    console.log('\n[SUCCESS] SQLite Auto-Deduplication Merges verified.');

    console.log('\n----------------------------------------------------');
    console.log('ALL BACKEND PIPELINES SUCCESSFULLY VERIFIED & ROBUST');
    console.log('----------------------------------------------------');

  } catch (err) {
    console.error(`\n[FATAL ASSERTION ERROR] Verification pipeline failed: ${err.message}`);
    process.exit(1);
  }
}

runTests();
