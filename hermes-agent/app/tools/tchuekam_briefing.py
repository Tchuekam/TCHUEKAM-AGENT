import os
import time
import sqlite3
import logging
from tools.tchuekam_memory import get_mem_connection, initialize_memory_db
from tools.tchuekam_indexer import get_db_connection, initialize_db, scan_directory

logger = logging.getLogger(__name__)

def generate_morning_brief(project_path):
    """
    Generate a 2-minute premium daily brief for the CEO.
    Combines drive index telemetry, memory graph, and local folder changes in the last 24h.
    """
    initialize_db()
    initialize_memory_db()
    
    start_time = time.time()
    norm_path = os.path.normpath(os.path.abspath(project_path)).replace("\\", "/")
    project_name = os.path.basename(norm_path) or "Active Workspace"
    
    # Fast scan active workspace folder to ensure briefing activity metrics are 100% real-time accurate
    try:
        conn_scan = get_db_connection()
        scan_directory(norm_path, conn_scan)
        conn_scan.close()
    except Exception as e:
        logger.warning(f"Briefing fast scan failed: {e}")
    
    # 1. Query recently modified files in the last 24 hours from SQLite index
    now_ts = time.time()
    day_ago_ts = now_ts - 86400
    
    conn_idx = get_db_connection()
    cursor_idx = conn_idx.cursor()
    
    recent_files = []
    try:
        cursor_idx.execute(
            """
            SELECT path, name, size, mtime 
            FROM files 
            WHERE path LIKE ? AND mtime >= ? 
            ORDER BY mtime DESC 
            LIMIT 10
            """,
            (f"{norm_path}%", day_ago_ts)
        )
        rows = cursor_idx.fetchall()
        for r in rows:
            recent_files.append({
                "path": r["path"],
                "name": r["name"],
                "size_kb": round(r["size"] / 1024, 2),
                "mtime": time.strftime('%H:%M:%S', time.localtime(r["mtime"]))
            })
    except Exception as e:
        logger.warning(f"Failed to fetch recent files: {e}")
    finally:
        conn_idx.close()
        
    # 2. Query Active Memory Graph details (entities & decisions)
    conn_mem = get_mem_connection()
    cursor_mem = conn_mem.cursor()
    
    entities = []
    decisions = []
    project_id = None
    try:
        cursor_mem.execute("SELECT id FROM projects WHERE path = ?", (norm_path,))
        proj_row = cursor_mem.fetchone()
        if proj_row:
            project_id = proj_row["id"]
            
            # Fetch active variables/clients
            cursor_mem.execute(
                "SELECT name, type, value FROM entities WHERE project_id = ? LIMIT 10",
                (project_id,)
            )
            entities = cursor_mem.fetchall()
            
            # Fetch active decisions in last 7 days
            week_ago_ts = now_ts - (7 * 86400)
            cursor_mem.execute(
                "SELECT description, rationale, timestamp FROM decisions WHERE project_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
                (project_id, week_ago_ts)
            )
            decisions = cursor_mem.fetchall()
    except Exception as e:
        logger.warning(f"Failed to fetch memory snapshot: {e}")
    finally:
        conn_mem.close()
        
    # 3. Compile the premium TCHUEKAM daily brief
    brief = []
    brief.append("=" * 60)
    brief.append("          TCHUEKAM EXECUTIVE DAILY BRIEF")
    brief.append(f"          Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_ts))}")
    brief.append("=" * 60)
    brief.append(f"\n[ACTIVE PROJECT]: {project_name}")
    brief.append(f"Workspace Path:  {norm_path}")
    
    # Section A: Telemetry
    brief.append("\n[TELEMETRY & ACTIVITY (LAST 24 HOURS)]")
    brief.append("-" * 40)
    if recent_files:
        brief.append(f"Detected {len(recent_files)} active file operations:")
        for f in recent_files:
            brief.append(f"  * {f['mtime']} | {f['name']} ({f['size_kb']} KB) -> {os.path.dirname(f['path'])}")
    else:
        brief.append("  * Zero file modifications recorded in this workspace directory.")
        
    # Section B: Sovereign Context
    brief.append("\n[SOVEREIGN METADATA GRAPH]")
    brief.append("-" * 40)
    if entities:
        for ent in entities:
            brief.append(f"  * {ent['type'].upper()} | {ent['name']}: {ent['value']}")
    else:
        brief.append("  * No active entity variables mapped to this project workspace.")
        
    # Section C: Design Lock
    brief.append("\n[ACTIVE ARCHITECTURAL DECISIONS (LAST 7 DAYS)]")
    brief.append("-" * 40)
    if decisions:
        for i, dec in enumerate(decisions, 1):
            ts_str = time.strftime('%Y-%m-%d', time.localtime(dec["timestamp"]))
            brief.append(f"  [{i}] {ts_str} - {dec['description']}")
            brief.append(f"      Rationale: {dec['rationale']}")
    else:
        brief.append("  * Zero strategic decisions logged in this period.")
        
    elapsed = time.time() - start_time
    brief.append("\n" + "=" * 60)
    brief.append(f"Brief compiled in {elapsed * 1000:.2f}ms | Offline Secured.")
    brief.append("=" * 60)
    
    return "\n".join(brief)
