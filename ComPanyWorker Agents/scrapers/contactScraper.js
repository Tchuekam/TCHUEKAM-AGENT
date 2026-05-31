import * as cheerio from 'cheerio';

/**
 * Normalizes a URL, ensuring it has http or https protocol
 */
function normalizeUrl(url) {
  if (!url) return '';
  let clean = url.trim();
  if (!/^https?:\/\//i.test(clean)) {
    clean = 'http://' + clean;
  }
  return clean;
}

/**
 * Helper to make a fetch request with a realistic User-Agent and timeout
 */
async function fetchHtml(url) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 8000); // 8 second timeout

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr,en-US;q=0.7,en;q=0.3'
      }
    });

    clearTimeout(id);

    if (!response.ok) return '';
    return await response.text();
  } catch (err) {
    clearTimeout(id);
    return '';
  }
}

/**
 * Extracts emails from a body of text
 */
function extractEmails(text) {
  if (!text) return [];
  // Avoid capturing common image/script extensions disguised as emails
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,12}/g;
  const matches = text.match(emailRegex) || [];
  
  // Filter out web assets/junk matches
  return [...new Set(matches.filter(email => {
    const lower = email.toLowerCase();
    return !lower.endsWith('.png') && 
           !lower.endsWith('.jpg') && 
           !lower.endsWith('.jpeg') && 
           !lower.endsWith('.gif') &&
           !lower.endsWith('.svg') &&
           !lower.endsWith('w3.org') &&
           !lower.endsWith('example.com');
  }))];
}

/**
 * Extracts phone numbers from a body of text and links
 */
function extractPhones(text, cheerioDoc = null) {
  const phones = new Set();

  // 1. Scan a[href^="tel:"] anchors
  if (cheerioDoc) {
    cheerioDoc('a[href^="tel:"]').each((_, el) => {
      const tel = cheerioDoc(el).attr('href').replace('tel:', '').trim();
      if (tel) phones.add(tel);
    });
  }

  // 2. Regular expression scan for typical phone formats (including Cameroonian +237)
  if (text) {
    // Matches: +237 6xx xx xx xx, +237222xxxxxx, +1-xxx-xxx-xxxx, etc.
    const phoneRegex = /(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+237[-.\s]?[268]\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}/g;
    const matches = text.match(phoneRegex) || [];
    matches.forEach(m => {
      const cleaned = m.trim();
      if (cleaned.length >= 8 && cleaned.length <= 18) {
        phones.add(cleaned);
      }
    });
  }

  return [...phones];
}

/**
 * Crawls a business website, finds contact subpages, and extracts emails, phones, and social profiles.
 * 
 * @param {string} rawUrl - The domain URL to analyze
 * @param {Function} logCallback - Logger stream update function
 * @returns {Object} Extracted data: { emails, phones, socialLinks: { facebook, linkedin, instagram, twitter } }
 */
export async function scrapeWebsiteContacts(rawUrl, logCallback = console.log) {
  const url = normalizeUrl(rawUrl);
  if (!url) return { emails: [], phones: [], socialLinks: {} };

  logCallback(`[CONTACT SCRAPER] Starting crawler on domain: ${url}`);
  
  const emails = new Set();
  const phones = new Set();
  const socialLinks = {
    facebook: '',
    linkedin: '',
    instagram: '',
    twitter: '',
    youtube: ''
  };

  try {
    const html = await fetchHtml(url);
    if (!html) {
      logCallback(`[CONTACT SCRAPER] Failed to fetch homepage for domain: ${url} (or site offline).`);
      return { emails: [], phones: [], socialLinks: {} };
    }

    const $ = cheerio.load(html);
    const bodyText = $('body').text();

    // 1. Extract from home page
    extractEmails(bodyText).forEach(e => emails.add(e));
    extractPhones(bodyText, $).forEach(p => phones.add(p));

    // Scan social links on homepage
    const scanSocials = (cheerioDoc) => {
      cheerioDoc('a[href]').each((_, el) => {
        const href = cheerioDoc(el).attr('href').trim();
        if (/facebook\.com/i.test(href) && !socialLinks.facebook) socialLinks.facebook = href;
        if (/linkedin\.com/i.test(href) && !socialLinks.linkedin) socialLinks.linkedin = href;
        if (/instagram\.com/i.test(href) && !socialLinks.instagram) socialLinks.instagram = href;
        if (/(twitter\.com|x\.com)/i.test(href) && !socialLinks.twitter) socialLinks.twitter = href;
        if (/youtube\.com/i.test(href) && !socialLinks.youtube) socialLinks.youtube = href;
      });
    };

    scanSocials($);

    // 2. Discover and crawl Contact / A Propos links
    const contactLinks = new Set();
    const domainAuthority = new URL(url).hostname.replace('www.', '');

    $('a[href]').each((_, el) => {
      const href = $(el).attr('href').trim();
      const text = $(el).text().toLowerCase();

      // Look for contact indicators
      const isContactAnchor = /contact/i.test(href) || 
                              /about/i.test(href) || 
                              /apropos/i.test(href) || 
                              /a-propos/i.test(href) ||
                              /mentions/i.test(href) || 
                              /legal/i.test(href) ||
                              /contact/i.test(text) || 
                              /à propos/i.test(text) || 
                              /qui sommes/i.test(text);

      if (isContactAnchor) {
        try {
          // Resolve relative URLs to absolute
          const resolved = new URL(href, url).href;
          // Safeguard: Make sure it's on the same domain to prevent external crawls
          if (resolved.includes(domainAuthority)) {
            contactLinks.add(resolved);
          }
        } catch (e) {
          // Skip invalid URLs
        }
      }
    });

    const subpageList = [...contactLinks].slice(0, 3); // Limit subpages to 3 to prevent bloat
    if (subpageList.length > 0) {
      logCallback(`[CONTACT SCRAPER] Discovered ${subpageList.length} contact/about subpage candidates: ${subpageList.join(', ')}`);
      
      for (const subpageUrl of subpageList) {
        logCallback(`[CONTACT CRAWL] Fetching subpage: ${subpageUrl}`);
        const subHtml = await fetchHtml(subpageUrl);
        if (!subHtml) continue;

        const $sub = cheerio.load(subHtml);
        const subText = $sub('body').text();

        // Extract credentials
        extractEmails(subText).forEach(e => emails.add(e));
        extractPhones(subText, $sub).forEach(p => phones.add(p));
        scanSocials($sub);
      }
    }

  } catch (error) {
    logCallback(`[CONTACT SCRAPER ERROR] Crawler hit an exception for ${url}: ${error.message}`);
  }

  const results = {
    emails: [...emails],
    phones: [...phones],
    socialLinks
  };

  logCallback(`[CONTACT SCRAPER] Completed crawl on ${url}. Extracted: Emails=[${results.emails.join(', ')}], Phones=[${results.phones.join(', ')}]`);
  return results;
}
