import os
import sqlite3
import time
import logging

logger = logging.getLogger(__name__)

MEM_DB_PATH = os.path.expanduser("~/.hermes/tchuekam_memory.db")

def get_mem_connection():
    os.makedirs(os.path.dirname(MEM_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(MEM_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_memory_db():
    """
    Initialize SQLite schema for the TCHUEKAM Entity-Relationship Memory Graph.
    """
    conn = get_mem_connection()
    cursor = conn.cursor()
    
    # 1. Projects table (scoped by directory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at REAL NOT NULL,
        status TEXT DEFAULT 'active'
    )
    """)
    
    # 2. Entities table (clients, files, conventions, architectural states)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'client', 'file', 'convention', 'preference', 'variable'
        value TEXT NOT NULL,
        updated_at REAL NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        UNIQUE(project_id, name, type)
    )
    """)
    
    # 3. Decisions table (architectural decisions log)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        rationale TEXT NOT NULL,
        timestamp REAL NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """)
    
    # 4. Relationships table (links between entities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        target_id INTEGER NOT NULL,
        type TEXT NOT NULL, -- 'affects', 'implemented_in', 'assigned_to'
        FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE,
        UNIQUE(source_id, target_id, type)
    )
    """)
    
    conn.commit()
    conn.close()

def get_or_create_project(project_path, conn):
    """
    Get or create a project record based on its absolute path.
    """
    cursor = conn.cursor()
    norm_path = os.path.normpath(os.path.abspath(project_path)).replace("\\", "/")
    
    cursor.execute("SELECT id FROM projects WHERE path = ?", (norm_path,))
    row = cursor.fetchone()
    if row:
        return row["id"]
        
    name = os.path.basename(norm_path) or "Root"
    cursor.execute(
        "INSERT INTO projects (path, name, created_at) VALUES (?, ?, ?)",
        (norm_path, name, time.time())
    )
    conn.commit()
    return cursor.lastrowid

def record_project_decision(project_path, description, rationale):
    """
    Surgically record an architectural decision for a specific project.
    """
    initialize_memory_db()
    conn = get_mem_connection()
    try:
        project_id = get_or_create_project(project_path, conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO decisions (project_id, description, rationale, timestamp) VALUES (?, ?, ?, ?)",
            (project_id, description.strip(), rationale.strip(), time.time())
        )
        conn.commit()
        return {"success": True, "message": "Architectural decision successfully recorded."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def record_project_entity(project_path, name, entity_type, value):
    """
    Record or update an entity (client, convention, code variable) scoped by project.
    """
    initialize_memory_db()
    conn = get_mem_connection()
    try:
        project_id = get_or_create_project(project_path, conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities (project_id, name, type, value, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name, type) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (project_id, name.strip(), entity_type.strip(), value.strip(), time.time())
        )
        conn.commit()
        return {"success": True, "message": f"Entity '{name}' ({entity_type}) recorded."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def load_project_memory_snapshot(project_path):
    """
    Query the memory graph and construct a rich context snapshot for prompt injection.
    """
    initialize_memory_db()
    conn = get_mem_connection()
    cursor = conn.cursor()
    
    norm_path = os.path.normpath(os.path.abspath(project_path)).replace("\\", "/")
    
    # Check if project exists
    cursor.execute("SELECT id, name FROM projects WHERE path = ?", (norm_path,))
    proj = cursor.fetchone()
    if not proj:
        conn.close()
        return ""
        
    project_id = proj["id"]
    
    # 1. Fetch all entities
    cursor.execute(
        "SELECT name, type, value FROM entities WHERE project_id = ? ORDER BY type, name",
        (project_id,)
    )
    entities = cursor.fetchall()
    
    # 2. Fetch all decisions
    cursor.execute(
        "SELECT description, rationale, timestamp FROM decisions WHERE project_id = ? ORDER BY timestamp DESC",
        (project_id,)
    )
    decisions = cursor.fetchall()
    conn.close()
    
    if not entities and not decisions:
        return ""
        
    # Render the snapshot block in premium TCHUEKAM style
    lines = []
    lines.append("=" * 60)
    lines.append(f"TCHUEKAM MEMORY GRAPH SNAPSHOT: {proj['name']}")
    lines.append(f"Path: {norm_path}")
    lines.append("=" * 60)
    
    # Group entities by type
    grouped = {}
    for ent in entities:
        grouped.setdefault(ent["type"], []).append(ent)
        
    for etype, items in grouped.items():
        lines.append(f"\n--- {etype.upper()} ENTITIES ---")
        for item in items:
            lines.append(f"* {item['name']}: {item['value']}")
            
    if decisions:
        lines.append("\n--- RECORDED ARCHITECTURAL DECISIONS ---")
        for i, dec in enumerate(decisions, 1):
            date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dec["timestamp"]))
            lines.append(f"[{i}] {date_str} - {dec['description']}")
            lines.append(f"    Rationale: {dec['rationale']}")
            
    lines.append("=" * 60)
    return "\n".join(lines)
