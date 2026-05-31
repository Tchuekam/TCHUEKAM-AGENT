// Global State Elements
const scraperForm = document.getElementById('scraperForm');
const submitBtn = document.getElementById('submitBtn');
const terminalBody = document.getElementById('terminalBody');
const refreshBtn = document.getElementById('refreshBtn');
const clearBtn = document.getElementById('clearBtn');
const leadsBody = document.getElementById('leadsBody');

// Establish SSE Connection to compile live logs
function connectTelemetry() {
  const eventSource = new EventSource('/api/logs');

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.log) {
        appendTerminalLog(data.log);
      }
    } catch (e) {
      // Ignored parsing errors
    }
  };

  eventSource.onerror = () => {
    appendTerminalLog('[SYS ERROR] Telemetry line dropped. Reconnecting...', 'text-red');
    eventSource.close();
    // Reconnect in 3s
    setTimeout(connectTelemetry, 3000);
  };
}

// Appends logs to the terminal body with sleek color themes
function appendTerminalLog(message, forceClass = '') {
  const line = document.createElement('div');
  line.className = 'log-line';
  
  if (forceClass) {
    line.classList.add(forceClass);
  } else if (message.includes('[SUCCESS]') || message.includes('[REGISTRY SUCCESS]')) {
    line.classList.add('text-green');
  } else if (message.includes('[SYS]') || message.includes('[STAGE')) {
    line.classList.add('text-cyan');
  } else if (message.includes('[MINING]') || message.includes('[CRAWL]')) {
    line.classList.add('text-orange');
  } else if (message.includes('ERROR') || message.includes('WARNING') || message.includes('FATAL')) {
    line.classList.add('text-red');
  }

  line.textContent = message;
  terminalBody.appendChild(line);

  // Auto-scroll
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

// Formats Priority Badge elements
function getPriorityBadge(score) {
  const level = score === 3 ? 'High' : (score === 2 ? 'Medium' : 'Low');
  return `<span class="priority-badge priority-${score}">${level}</span>`;
}

// Refreshes leads database in browser table
async function refreshLeads() {
  try {
    const response = await fetch('/api/leads');
    if (!response.ok) throw new Error('Database connection failed.');
    
    const leads = await response.json();
    renderLeads(leads);
  } catch (err) {
    appendTerminalLog(`[SYS] Failed to refresh leads: ${err.message}`, 'text-red');
  }
}

// Renders lead list to HTML
function renderLeads(leads) {
  leadsBody.innerHTML = '';

  if (leads.length === 0) {
    leadsBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center" style="opacity: 0.5; padding: 40px 0;">
          No lead coordinates registered yet. Trigger a search to hydrate database.
        </td>
      </tr>
    `;
    return;
  }

  leads.forEach(lead => {
    const tr = document.createElement('tr');

    // Compile contacts cells
    const contacts = [];
    if (lead.phone) contacts.push(`<div>📞 <strong>Phone:</strong> ${lead.phone}</div>`);
    if (lead.email) contacts.push(`<div>✉️ <strong>Email:</strong> ${lead.email}</div>`);
    if (lead.website && lead.website !== 'N/A') {
      contacts.push(`<div>🌐 <strong>Web:</strong> <a href="${lead.website}" target="_blank" style="color: var(--cyan); text-decoration: none;">Link</a></div>`);
    }

    const copyBtnHtml = lead.message_template 
      ? `<button class="btn btn-secondary" style="font-size: 9px; padding: 4px 8px; margin-top: 6px;" onclick="copyOutreachTemplate(\`${lead.message_template.replace(/`/g, '\\`').replace(/"/g, '&quot;')}\`, this)">Copy Script</button>` 
      : '';

    tr.innerHTML = `
      <td><strong>${lead.name}</strong></td>
      <td>${getPriorityBadge(lead.priority_score)}</td>
      <td><span style="opacity: 0.8">${lead.category}</span></td>
      <td>${contacts.join('') || '<span style="opacity: 0.4">No contact lines</span>'}</td>
      <td><span style="opacity: 0.8">${lead.location}</span></td>
      <td><span style="color: var(--orange)">${lead.source}</span></td>
      <td>
        <div style="font-size: 10px; max-width: 250px; max-height: 80px; overflow-y: auto; background: #050505; padding: 8px; border: 1px solid rgba(255,255,255,0.05); white-space: pre-wrap; opacity: 0.85;">${lead.message_template || 'N/A'}</div>
        ${copyBtnHtml}
      </td>
    `;
    leadsBody.appendChild(tr);
  });
}

// Copy outreach templates
window.copyOutreachTemplate = (text, btn) => {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btn.textContent;
    btn.textContent = 'COPIED!';
    btn.style.borderColor = 'var(--green)';
    btn.style.color = 'var(--green)';
    
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.borderColor = '';
      btn.style.color = '';
    }, 2000);
  });
};

// Handle Scraping form triggers
scraperForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const source = document.getElementById('scraperSource').value;
  const query = document.getElementById('searchQuery').value.trim();
  const location = document.getElementById('searchLocation').value.trim();
  const limit = parseInt(document.getElementById('scrapeLimit').value) || 10;

  if (!query || !location) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'HARVESTING...';

  try {
    const response = await fetch('/api/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, query, location, limit })
    });

    if (!response.ok) throw new Error('Job launch rejected.');
    
    appendTerminalLog(`[SYS] Scrape job successfully dispatched. Monitoring logs below...`, 'text-cyan');
    
  } catch (err) {
    appendTerminalLog(`[SYS] Failed to launch job: ${err.message}`, 'text-red');
  } finally {
    // Re-enable form after brief delay
    setTimeout(() => {
      submitBtn.disabled = false;
      submitBtn.textContent = 'LAUNCH HARVEST ENGINE';
    }, 2000);
  }
});

// Refresh button trigger
refreshBtn.addEventListener('click', refreshLeads);

// Purge database trigger
clearBtn.addEventListener('click', async () => {
  if (!confirm('Are you sure you want to completely clear all leads in the database?')) return;

  try {
    const response = await fetch('/api/clear', { method: 'POST' });
    if (!response.ok) throw new Error('Purge command failed.');
    
    appendTerminalLog('[SYS] Database leads table successfully purged.', 'text-red');
    refreshLeads();
  } catch (err) {
    appendTerminalLog(`[SYS] Purge command failed: ${err.message}`, 'text-red');
  }
});

// Run Boot Initializations
connectTelemetry();
refreshLeads();

// Periodically refresh leads table (every 5 seconds) to catch live updates
setInterval(refreshLeads, 5000);
