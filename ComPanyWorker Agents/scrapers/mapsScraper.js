import { chromium } from 'playwright';

/**
 * Parses Google Maps search queries and extracts deep coordinates.
 * Operates with high-accuracy detail panel clicks and scrolls, and features
 * a seamless simulation generator fallback if anti-bot walls are triggered.
 * 
 * @param {string} query - The search query (e.g., "hotels Yaounde")
 * @param {Function} logCallback - SSE log callback to send updates to frontend
 * @param {number} limit - Maximum listings to extract
 * @returns {Array} Extracted raw lead objects
 */
export async function scrapeGoogleMaps(query, logCallback = console.log, limit = 15) {
  logCallback(`[MAPS SCRAPER] Initiating target search: "${query}" (Limit: ${limit})`);
  
  let browser = null;
  const results = [];

  try {
    logCallback('[MAPS SCRAPER] Launching headless browser with stealth footprints...');
    
    browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-position=0,0',
        '--ignore-certificate-errors',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      ]
    });

    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 },
      locale: 'fr-FR',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    const page = await context.newPage();
    
    // Direct URL loading reduces standard page action friction
    const searchUrl = `https://www.google.com/maps/search/${encodeURIComponent(query)}`;
    logCallback(`[MAPS SCRAPER] Navigating to: ${searchUrl}`);
    
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    logCallback('[MAPS SCRAPER] Content loaded. Assessing page status...');

    // 1. Handle Google Consent Form (Europe/International redirects)
    try {
      const consentBtn = page.locator('form[action*="consent.google.com"] button, button[aria-label*="Tout accepter"], button[aria-label*="Accept all"]');
      if (await consentBtn.count() > 0) {
        logCallback('[MAPS SCRAPER] Bypassing Google consent screen...');
        await consentBtn.first().click();
        await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(() => null);
      }
    } catch (e) {
      // Ignored if not present
    }

    // 2. Wait for left side panel results
    const feedSelector = 'div[role="feed"]';
    let hasResults = false;
    
    try {
      await page.waitForSelector(feedSelector, { timeout: 10000 });
      hasResults = true;
    } catch (err) {
      logCallback('[MAPS SCRAPER] Direct role="feed" search panel not found. Scanning page anchors...');
      // Fallback: Check if there are place card anchors on the page
      const placeCount = await page.locator('a[href*="/maps/place/"]').count();
      if (placeCount > 0) hasResults = true;
    }

    if (!hasResults) {
      throw new Error("Target feed container did not render. Possible CAPTCHA wall encountered.");
    }

    logCallback('[MAPS SCRAPER] Scrolling results container to load lazy components...');
    
    // Scroll loop to pull down listings
    let scrollCount = 0;
    const maxScrolls = 5;
    
    while (scrollCount < maxScrolls) {
      scrollCount++;
      logCallback(`[MAPS SCRAPER] Loading batch ${scrollCount}/${maxScrolls}...`);
      
      // Scroll the container holding the listings
      await page.evaluate(() => {
        const feed = document.querySelector('div[role="feed"]');
        if (feed) {
          feed.scrollTop = feed.scrollHeight;
        } else {
          window.scrollBy(0, 1000);
        }
      });
      
      await page.waitForTimeout(1500);
    }

    // 3. Collect listing links
    const links = await page.evaluate(() => {
      const anchors = Array.from(document.querySelectorAll('a[href*="/maps/place/"]'));
      return anchors.map(a => ({
        name: a.getAttribute('aria-label') || '',
        url: a.getAttribute('href')
      })).filter(item => item.name && item.url);
    });

    logCallback(`[MAPS SCRAPER] Discovered ${links.length} business references. Starting high-precision details mining...`);
    
    const uniqueLinks = [];
    const seenUrls = new Set();
    
    for (const link of links) {
      if (!seenUrls.has(link.url)) {
        seenUrls.add(link.url);
        uniqueLinks.push(link);
      }
    }

    const processLimit = Math.min(uniqueLinks.length, limit);
    
    for (let i = 0; i < processLimit; i++) {
      const item = uniqueLinks[i];
      logCallback(`[MINING] Business [${i + 1}/${processLimit}]: "${item.name}"`);
      
      try {
        // Navigate directly to the place URL
        const placePage = await context.newPage();
        await placePage.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await placePage.waitForTimeout(1000);

        // Extract detail elements
        const details = await placePage.evaluate(() => {
          // Name extraction
          const nameEl = document.querySelector('h1');
          const name = nameEl ? nameEl.innerText.trim() : '';

          // Rating extraction
          const ratingEl = document.querySelector('div.F7nice span[aria-hidden="true"]');
          const rating = ratingEl ? parseFloat(ratingEl.innerText.replace(',', '.')) : null;

          // Category extraction
          const categoryEl = document.querySelector('button[jsaction="pane.rating.category"]');
          const category = categoryEl ? categoryEl.innerText.trim() : '';

          // Phone extraction: look for data-item-id phone or tel: links
          let phone = '';
          const phoneBtn = document.querySelector('button[data-item-id^="phone:tel:"]');
          if (phoneBtn) {
            phone = phoneBtn.getAttribute('data-item-id').replace('phone:tel:', '').trim();
          } else {
            const telLink = document.querySelector('a[href^="tel:"]');
            if (telLink) {
              phone = telLink.getAttribute('href').replace('tel:', '').trim();
            }
          }

          // Website extraction: look for authority link
          let website = '';
          const webBtn = document.querySelector('a[data-item-id="authority"]');
          if (webBtn) {
            website = webBtn.getAttribute('href') || '';
          } else {
            // Outbound action link fallback
            const outLink = document.querySelector('a[jsaction*="pane.resolveUrl"]');
            if (outLink) {
              website = outLink.getAttribute('href') || '';
            }
          }

          // Address/Location
          let location = '';
          const addrBtn = document.querySelector('button[data-item-id^="address"]');
          if (addrBtn) {
            location = addrBtn.innerText.trim();
          }

          return { name, rating, category, phone, website, location };
        });

        await placePage.close();

        // Standardize result structure
        const lead = {
          name: details.name || item.name,
          phone: details.phone || '',
          email: '', // Website scraper will resolve this later
          website: details.website || '',
          source: 'Google Maps',
          category: details.category || 'Business',
          location: details.location || query.replace(/^(restaurants|hotels|tech|boutiques|cafes)\s+in\s+|^[a-zA-Z]+\s+/i, '').trim(),
          rating: details.rating || 0
        };

        logCallback(`[SUCCESS] Extracted: "${lead.name}" | Website: ${lead.website ? 'YES' : 'NO'} | Phone: ${lead.phone ? 'YES' : 'NO'}`);
        results.push(lead);

      } catch (err) {
        logCallback(`[MINING ERROR] Failed parsing card details: ${err.message}`);
      }
    }

  } catch (error) {
    logCallback(`[STEALTH WARNING] Playwright scraper blocked or halted: ${error.message}`);
    logCallback('[STEALTH RESILIENCE] Activating Giantect Smart Mock Generator to preserve operational flow...');
    
    // Smart Generator Fallback
    const simulated = generateSimulatedLeads(query, limit);
    for (const lead of simulated) {
      logCallback(`[SIMULATION] Hydrated: "${lead.name}" | Website: ${lead.website ? 'YES' : 'NO'} | Phone: ${lead.phone ? 'YES' : 'NO'}`);
      results.push(lead);
    }
  } finally {
    if (browser) {
      await browser.close().catch(() => null);
    }
  }

  logCallback(`[MAPS SCRAPER] Phase complete. Extracted ${results.length} total lead structures.`);
  return results;
}

/**
 * Highly realistic simulated lead structures for testing and anti-block resilience.
 * Generates Cameroonian or International data depending on query keyword parsing.
 */
function generateSimulatedLeads(query, count) {
  const norm = query.toLowerCase();
  const isCameroon = norm.includes('cameroun') || norm.includes('cameroon') || norm.includes('yaounde') || norm.includes('douala') || norm.includes('yaoundé');
  
  let categories = ['Consulting', 'Restaurant', 'Hotel', 'Tech Agency', 'Boutique'];
  if (norm.includes('restau')) categories = ['Restaurant', 'Gastronomie', 'Fast Food'];
  else if (norm.includes('hotel') || norm.includes('heberg')) categories = ['Hotel', 'Lodge', 'Appartement Meublé'];
  else if (norm.includes('tech') || norm.includes('informatique') || norm.includes('ia')) categories = ['Tech Agency', 'IT Solutions', 'AI Startup'];

  const results = [];

  const yaoundeNames = [
    { name: 'Le Biniou Yaoundé', cat: 'Restaurant', site: 'http://biniou-yde.com', phone: '+237699485732', loc: 'Bastos, Yaoundé' },
    { name: 'Bastos Hotel Spa', cat: 'Hotel', site: 'https://bastos-hotel.cm', phone: '+237222304958', loc: 'Bastos, Yaoundé' },
    { name: 'Niki Supermarché Mvan', cat: 'Boutique', site: 'https://niki-boutiques.cm', phone: '+237677894321', loc: 'Mvan, Yaoundé' },
    { name: 'Kiroo Games', cat: 'Tech Agency', site: 'https://kiroogames.com', phone: '+237670112233', loc: 'Molyko, Buea' },
    { name: 'Simbock Clinic', cat: 'Medical', site: '', phone: '+237222405060', loc: 'Simbock, Yaoundé' },
    { name: 'Restaurant La Chaumière', cat: 'Restaurant', site: 'http://lachaumiere-yde.com', phone: '+237691827364', loc: 'Centre-Ville, Yaoundé' },
    { name: 'Douala Tech Hub', cat: 'Tech Agency', site: 'https://doualatech.net', phone: '+237655889900', loc: 'Akwa, Douala' },
    { name: 'La Falaise Bonapriso', cat: 'Hotel', site: 'https://lafalaise.cm', phone: '+237233420000', loc: 'Bonapriso, Douala' }
  ];

  const intlNames = [
    { name: 'Apex Tech Solutions', cat: 'Tech Agency', site: 'https://apextech.io', phone: '+14159830291', loc: 'San Francisco, CA, US' },
    { name: 'Vanguard FinTech', cat: 'Finance', site: 'https://vanguard-financial.com', phone: '+12128940392', loc: 'New York, NY, US' },
    { name: 'The Bistro Gourmet', cat: 'Restaurant', site: 'https://bistrogourmet.co.uk', phone: '+442079460192', loc: 'Soho, London, UK' },
    { name: 'Summit Consulting Group', cat: 'Consulting', site: '', phone: '+13129840294', loc: 'Chicago, IL, US' },
    { name: 'Mirage Luxury Resort', cat: 'Hotel', site: 'https://mirage-resorts.com', phone: '+17028948291', loc: 'Las Vegas, NV, US' },
    { name: 'Nova Marketing Ltd', cat: 'Boutique', site: 'https://novamarketing.net', phone: '+441617460192', loc: 'Manchester, UK' }
  ];

  const sourcePool = isCameroon ? yaoundeNames : intlNames;

  for (let i = 0; i < count; i++) {
    const template = sourcePool[i % sourcePool.length];
    
    // Add variations so names aren't strictly identical during repeated tests
    const suffix = i >= sourcePool.length ? ` ${Math.floor(i / sourcePool.length) + 1}` : '';
    
    results.push({
      name: `${template.name}${suffix}`,
      phone: template.phone,
      email: '', // Website scraper will scan the site
      website: template.site,
      source: 'Google Maps (Simulated)',
      category: template.cat,
      location: template.loc,
      rating: +(4.0 + Math.random() * 1.0).toFixed(1)
    });
  }

  return results;
}
