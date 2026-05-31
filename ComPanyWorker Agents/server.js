import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { 
  initDatabase, 
  upsertLead, 
  getAllLeads, 
  getNexusQueue, 
  generateLeadsCSV, 
  run 
} from './database.js';
import { scrapeGoogleMaps } from './scrapers/mapsScraper.js';
import { scrapeWebsiteContacts } from './scrapers/contactScraper.js';
import { scrapeDirectory } from './scrapers/directoryScraper.js';
import { scrapeLinkedInProfiles } from './scrapers/linkedinScraper.js';
import { calculatePriorityScore } from './nexus.js';
import { generateOutreachMessage } from './outreach.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
// Serve static frontend assets
app.use(express.static(path.join(__dirname, 'public')));

// List of connected SSE clients for real-time terminal feedback
let sseClients = [];

/**
 * Broadcasts a telemetry message to the active terminal dashboard
 */
function broadcastLog(message) {
  const formattedMsg = `[${new Date().toLocaleTimeString()}] ${message}`;
  console.log(formattedMsg);
  
  sseClients.forEach(client => {
    client.write(`data: ${JSON.stringify({ log: formattedMsg })}\n\n`);
  });
}

// SSE Logging Endpoint
app.get('/api/logs', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });
  res.write('\n');
  
  sseClients.push(res);
  
  broadcastLog('[SYS] Dark Power terminal telemetry connection established.');

  req.on('close', () => {
    sseClients = sseClients.filter(c => c !== res);
  });
});

// Start Scraping Job (runs asynchronously in background to prevent browser timeouts)
app.post('/api/scrape', async (req, res) => {
  const { source, query, location, limit = 10 } = req.body;
  
  if (!query || !location) {
    return res.status(400).json({ error: 'Search query and geographic location are required.' });
  }

  // Accept job immediately
  res.status(202).json({ status: 'queued', message: 'Scrape job accepted and running in the background.' });

  broadcastLog(`[SYS] Scraper task initiated. Source: [${source.toUpperCase()}] | Query: "${query}" | Geo: "${location}"`);

  try {
    let rawLeads = [];

    // 1. Core target extraction
    if (source === 'maps' || source === 'all') {
      const mapsLeads = await scrapeGoogleMaps(`${query} in ${location}`, broadcastLog, limit);
      rawLeads.push(...mapsLeads);
    }
    
    if (source === 'directory' || source === 'all') {
      const directoryLeads = await scrapeDirectory(query, location, broadcastLog);
      rawLeads.push(...directoryLeads);
    }

    if (source === 'linkedin' || source === 'all') {
      const linkedinLeads = await scrapeLinkedInProfiles(query, location, broadcastLog);
      rawLeads.push(...linkedinLeads);
    }

    broadcastLog(`[SYS] Initial mining complete. Found ${rawLeads.length} prospects. Initiating deep contact crawl and priority grading...`);

    // 2. Domain Deep Crawl, Priorities calculation, and Message Synthesis
    let index = 0;
    for (const lead of rawLeads) {
      index++;
      broadcastLog(`[STAGE 2] Prospect [${index}/${rawLeads.length}]: "${lead.name}"`);

      // Crawl website contacts if website exists
      if (lead.website && lead.website !== 'N/A' && lead.website.trim() !== '') {
        const contacts = await scrapeWebsiteContacts(lead.website, broadcastLog);
        
        // Merge contacts back to lead structure
        if (contacts.emails && contacts.emails.length > 0) {
          lead.email = contacts.emails.join(', ');
        }
        // If Google Maps didn't have a phone, try to use phone found on website
        if (!lead.phone && contacts.phones && contacts.phones.length > 0) {
          lead.phone = contacts.phones.join(', ');
        }
      }

      // Calculate priority score
      lead.priority_score = calculatePriorityScore(lead);

      // Synthesize cultural outreach text template
      lead.message_template = generateOutreachMessage(lead);

      // Save lead safely to SQLite with deduplication rules
      const dbResult = await upsertLead(lead);
      if (dbResult.status === 'merged') {
        broadcastLog(`[DB MERGE] Consolidated lead "${lead.name}" (ID: ${dbResult.id})`);
      } else {
        broadcastLog(`[DB INSERT] Registered new lead "${lead.name}" (ID: ${dbResult.id}) with priority level: ${lead.priority_score}`);
      }
    }

    broadcastLog(`[SYS] Scraper task completed successfully. System database hydrated.`);

  } catch (error) {
    broadcastLog(`[SYS FATAL ERROR] Scraping process crashed: ${error.message}`);
  }
});

// Fetch all database leads (with filter support)
app.get('/api/leads', async (req, res) => {
  try {
    const filters = {
      source: req.query.source,
      category: req.query.category,
      location: req.query.location,
      priority: req.query.priority
    };
    const leads = await getAllLeads(filters);
    res.json(leads);
  } catch (err) {
    res.status(500).json({ error: 'Failed to retrieve leads database.' });
  }
});

// Nexus Integration Queue Endpoint
app.get('/api/queue', async (req, res) => {
  try {
    const queue = await getNexusQueue();
    res.json(queue);
  } catch (err) {
    res.status(500).json({ error: 'Failed to compile Nexus outreach queue.' });
  }
});

// CSV Export Endpoint
app.get('/api/export', async (req, res) => {
  try {
    const csvContent = await generateLeadsCSV();
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=leads_export.csv');
    res.status(200).send(csvContent);
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate CSV export.' });
  }
});

// Database Clear Endpoint (Demo reset)
app.post('/api/clear', async (req, res) => {
  try {
    await run('DELETE FROM leads');
    broadcastLog('[DB RESET] Database leads table completely cleared.');
    res.json({ status: 'cleared', message: 'Leads database successfully purged.' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to clear leads database.' });
  }
});

// Boot operations
async function startServer() {
  broadcastLog('[SYS] Booting Giantect SCRAPER Engine...');
  await initDatabase();
  broadcastLog('[SYS] SQLite schemas initiated.');
  
  app.listen(PORT, () => {
    broadcastLog(`[SYS] Giantect SCRAPER Server online at http://localhost:${PORT}`);
  });
}

startServer();
