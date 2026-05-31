import os
import sqlite3
import time
import threading
import logging
import json
import re

logger = logging.getLogger(__name__)

DB_PATH = os.path.expanduser("~/.tchuekam/tchuekam_index.db")
FILESEARCHED_PATH = os.path.expanduser("~/.tchuekam/filesearched.json")

EXCLUDED_NAMES = {
    "node_modules", ".git", "google", "chrome", "system volume information",
    "$recycle.bin", "venv", ".gradle", "temp", "tmp", "appdata/local/temp",
    "cache", "caches", ".pnpm-store", "$RECYCLE.BIN"
}

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """
    Initialize SQLite FTS5 tables for indexing, automatically performing clean schema upgrades if needed.
    """
    # ── Database validation & self-healing integrity check ──
    try:
        if os.path.exists(DB_PATH):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()
            conn.close()
            if integrity and integrity[0] != "ok":
                raise sqlite3.DatabaseError(f"Integrity check failed: {integrity[0]}")
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
        logger.warning(f"Database validation raised error ({e}). Clearing malformed database.")
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ── Database schema migration / validation check ──
        # Check if files table has content_text column
        try:
            cursor.execute("SELECT content_text FROM files LIMIT 1")
        except sqlite3.OperationalError:
            # Table doesn't exist or column is missing, drop everything to start fresh
            cursor.execute("DROP TABLE IF EXISTS files_fts")
            cursor.execute("DROP TABLE IF EXISTS files")

        # Check if files_fts virtual table has content_text column
        try:
            cursor.execute("SELECT content_text FROM files_fts LIMIT 1")
        except sqlite3.OperationalError:
            # Virtual table lacks the column or doesn't exist, drop to recreate
            cursor.execute("DROP TABLE IF EXISTS files_fts")
        
        # Metadata table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            size INTEGER,
            mtime REAL,
            drive TEXT,
            content_text TEXT
        )
        """)
        try:
            cursor.execute("ALTER TABLE files ADD COLUMN content_text TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
        
        # FTS5 Virtual Table for high-speed prefix search linked securely to the metadata files table
        try:
            cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                name,
                path,
                content_text,
                content='files',
                content_rowid='id'
            )
            """)
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS files_fts")
            cursor.execute("""
            CREATE VIRTUAL TABLE files_fts USING fts5(
                name,
                path,
                content_text,
                content='files',
                content_rowid='id'
            )
            """)
        
        # Drop old triggers first in case we changed columns
        cursor.execute("DROP TRIGGER IF EXISTS trg_files_insert")
        cursor.execute("DROP TRIGGER IF EXISTS trg_files_delete")
        cursor.execute("DROP TRIGGER IF EXISTS trg_files_update")
        
        # Trigger to auto-sync FTS on metadata insert
        cursor.execute("""
        CREATE TRIGGER trg_files_insert AFTER INSERT ON files BEGIN
            INSERT INTO files_fts(rowid, name, path, content_text) VALUES (new.id, new.name, new.path, new.content_text);
        END
        """)
        
        # Trigger to auto-sync FTS on metadata delete
        cursor.execute("""
        CREATE TRIGGER trg_files_delete AFTER DELETE ON files BEGIN
            INSERT INTO files_fts(files_fts, rowid, name, path, content_text) VALUES('delete', old.id, old.name, old.path, old.content_text);
        END
        """)
        
        # Trigger to auto-sync FTS on metadata update
        cursor.execute("""
        CREATE TRIGGER trg_files_update AFTER UPDATE ON files BEGIN
            INSERT INTO files_fts(files_fts, rowid, name, path, content_text) VALUES('delete', old.id, old.name, old.path, old.content_text);
            INSERT INTO files_fts(rowid, name, path, content_text) VALUES (new.id, new.name, new.path, new.content_text);
        END
        """)
        
        conn.commit()
        conn.close()
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
        logger.warning(f"Database initialization failed ({e}). Recreating database file from scratch.")
        try:
            if 'conn' in locals():
                conn.close()
        except Exception:
            pass
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
        # Perform fresh creation
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            size INTEGER,
            mtime REAL,
            drive TEXT,
            content_text TEXT
        )
        """)
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
            name,
            path,
            content_text,
            content='files',
            content_rowid='id'
        )
        """)
        cursor.execute("""
        CREATE TRIGGER trg_files_insert AFTER INSERT ON files BEGIN
            INSERT INTO files_fts(rowid, name, path, content_text) VALUES (new.id, new.name, new.path, new.content_text);
        END
        """)
        cursor.execute("""
        CREATE TRIGGER trg_files_delete AFTER DELETE ON files BEGIN
            INSERT INTO files_fts(files_fts, rowid, name, path, content_text) VALUES('delete', old.id, old.name, old.path, old.content_text);
        END
        """)
        cursor.execute("""
        CREATE TRIGGER trg_files_update AFTER UPDATE ON files BEGIN
            INSERT INTO files_fts(files_fts, rowid, name, path, content_text) VALUES('delete', old.id, old.name, old.path, old.content_text);
            INSERT INTO files_fts(rowid, name, path, content_text) VALUES (new.id, new.name, new.path, new.content_text);
        END
        """)
        conn.commit()
        conn.close()

def should_exclude(path):
    parts = path.lower().replace("\\", "/").split("/")
    return any(name in EXCLUDED_NAMES for name in parts)

def scan_directory(root_path, conn):
    """
    Surgically scans a target directory, indexing both folders and files, and updates the SQLite index.
    """
    if not os.path.exists(root_path):
        return 0
        
    cursor = conn.cursor()
    batch = []
    batch_size = 1000
    total_indexed = 0
    
    from tools.document_extractor import extract_text
    
    drive_letter = os.path.splitdrive(root_path)[0] or "C:"
    
    # Load existing path modifications to bypass unchanged files/folders
    existing_mtimes = {}
    try:
        cursor.execute("SELECT path, mtime FROM files WHERE path LIKE ?", (f"{root_path}%",))
        for row in cursor.fetchall():
            existing_mtimes[row["path"]] = row["mtime"]
    except Exception:
        pass
    
    for root, dirs, files in os.walk(root_path):
        # Exclude directories in-place to prevent os.walk from entering them
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        
        # Index folders first
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                stat = os.stat(dp)
                size = 0
                mtime = stat.st_mtime
                if dp in existing_mtimes and abs(existing_mtimes[dp] - mtime) < 0.01:
                    continue
                batch.append((dp, d, size, mtime, drive_letter, "[FOLDER]"))
            except OSError:
                continue
                
            if len(batch) >= batch_size:
                cursor.executemany(
                    "INSERT OR REPLACE INTO files (path, name, size, mtime, drive, content_text) VALUES (?, ?, ?, ?, ?, ?)",
                    batch
                )
                conn.commit()
                total_indexed += len(batch)
                batch.clear()
        
        # Index files
        for file in files:
            fp = os.path.join(root, file)
            if should_exclude(fp):
                continue
                
            try:
                stat = os.stat(fp)
                size = stat.st_size
                mtime = stat.st_mtime
                if fp in existing_mtimes and abs(existing_mtimes[fp] - mtime) < 0.01:
                    continue
                
                content_text = ""
                ext = os.path.splitext(fp)[1].lower()
                if ext in [".pdf", ".docx", ".xlsx"]:
                    # Limit size to 50MB to prevent hangs
                    if size < 50 * 1024 * 1024:
                        content_text = extract_text(fp)
                elif ext in [".txt", ".md", ".csv", ".py", ".json", ".yaml", ".yml", ".ini", ".cfg", ".log"]:
                    # Limit to 5MB for plaintext files to prevent database bloating
                    if size < 5 * 1024 * 1024:
                        try:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                                content_text = f.read()
                        except Exception:
                            pass
                        
                batch.append((fp, file, size, mtime, drive_letter, content_text))
            except OSError:
                continue
                
            if len(batch) >= batch_size:
                cursor.executemany(
                    "INSERT OR REPLACE INTO files (path, name, size, mtime, drive, content_text) VALUES (?, ?, ?, ?, ?, ?)",
                    batch
                )
                conn.commit()
                total_indexed += len(batch)
                batch.clear()
                
    if batch:
        cursor.executemany(
            "INSERT OR REPLACE INTO files (path, name, size, mtime, drive, content_text) VALUES (?, ?, ?, ?, ?, ?)",
            batch
        )
        conn.commit()
        total_indexed += len(batch)
        
    return total_indexed

def run_background_index(paths=None):
    """
    Build or refresh the TCHUEKAM file index on a background thread.
    """
    if paths is None:
        paths = ["C:\\Users\\CLINIC", "D:\\", "H:\\"]
        
    def _worker():
        try:
            print("[TCHUEKAM INDEXER] Starting background drive index scan...", flush=True)
            initialize_db()
            conn = get_db_connection()
            
            # Clear old records first for a fresh start or let it overwrite
            cursor = conn.cursor()
            cursor.execute("DELETE FROM files")
            cursor.execute("DELETE FROM files_fts")
            conn.commit()
            
            start_time = time.time()
            total = 0
            for path in paths:
                if os.path.exists(path):
                    print(f"[TCHUEKAM INDEXER] Scanning path: {path}...", flush=True)
                    count = scan_directory(path, conn)
                    total += count
                    print(f"[TCHUEKAM INDEXER] Completed {path}: Indexed {count} files/folders.", flush=True)
            
            conn.close()
            elapsed = time.time() - start_time
            print(f"[TCHUEKAM INDEXER] Scan completed in {elapsed:.2f}s. Total files/folders indexed: {total:,}", flush=True)
        except Exception as e:
            print(f"[TCHUEKAM INDEXER] Error: {e}", flush=True)
            
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread

def query_index(query_str, limit=50):
    """
    Instantly query the FTS5 index for path, filename, or content keywords.
    First checks the filesearched.json memory cache for blazing fast search hits.
    """
    q_clean = query_str.strip().lower()
    
    # ── filesearched.json Memory Cache Hit check ──
    mem_cache = {}
    if os.path.exists(FILESEARCHED_PATH):
        try:
            with open(FILESEARCHED_PATH, "r", encoding="utf-8") as f:
                mem_cache = json.load(f)
        except Exception:
            pass
            
    if q_clean in mem_cache:
        cached_results = mem_cache[q_clean]
        valid_cached = []
        for item in cached_results:
            if os.path.exists(item["path"]):
                item["cached_hit"] = True
                valid_cached.append(item)
        if valid_cached:
            return {
                "results": valid_cached[:limit],
                "count": len(valid_cached[:limit]),
                "latency_ms": 0.0,
                "memory_cached": True
            }

    # Substring terms search over all previously searched files in the memory cache
    cached_matches = []
    seen_paths = set()
    
    # 1. Search in global discovered items (__all_found_items__) first for maximum precision
    global_items = mem_cache.get("__all_found_items__", {})
    if isinstance(global_items, dict):
        for path_key, item in global_items.items():
            path = item.get("path", "")
            name = item.get("name", "")
            
            terms = q_clean.split()
            if terms and all(t in name.lower() or t in path.lower() for t in terms):
                if os.path.exists(path):
                    item_copy = item.copy()
                    item_copy["cached_hit"] = True
                    cached_matches.append(item_copy)
                    seen_paths.add(path.lower())
                    
    # 2. Fallback to search query-cached entries (backward compatibility)
    for cached_list in mem_cache.values():
        if not isinstance(cached_list, list):
            continue
        for item in cached_list:
            if not isinstance(item, dict) or "path" not in item:
                continue
            path = item["path"]
            name = item.get("name", "")
            if path.lower() in seen_paths:
                continue
            
            terms = q_clean.split()
            if terms and all(t in name.lower() or t in path.lower() for t in terms):
                if os.path.exists(path):
                    item_copy = item.copy()
                    item_copy["cached_hit"] = True
                    cached_matches.append(item_copy)
                    seen_paths.add(path.lower())
                    
    if cached_matches:
        return {
            "results": cached_matches[:limit],
            "count": len(cached_matches[:limit]),
            "latency_ms": 0.0,
            "memory_cached": True
        }

    initialize_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We use FTS5 prefix match search
    # Sanitize query by extracting alphanumeric words to avoid crash on special characters
    terms = re.findall(r'\w+', query_str)
    if not terms:
        conn.close()
        return {"results": [], "count": 0, "latency_ms": 0.0}
        
    fts_query = " AND ".join([f"{term}*" for term in terms])
    
    sql = """
    SELECT f.path, f.name, f.size, f.mtime, f.drive, snippet(files_fts, -1, '[', ']', '...', 64) as snippet
    FROM files f
    JOIN files_fts fts ON fts.rowid = f.id
    WHERE files_fts MATCH ?
    LIMIT ?
    """
    
    start_time = time.time()
    results = []
    try:
        cursor.execute(sql, (fts_query, limit))
        rows = cursor.fetchall()
        elapsed = time.time() - start_time
        
        for r in rows:
            snippet_str = r["snippet"] if r["snippet"] else ""
            snippet_str = snippet_str.replace("\n", " ").strip()
            results.append({
                "path": r["path"],
                "name": r["name"],
                "size_kb": round(r["size"] / 1024, 2),
                "mtime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r["mtime"])),
                "drive": r["drive"],
                "snippet": snippet_str
            })
    except sqlite3.OperationalError as e:
        # Fallback to standard LIKE if FTS query syntax fails on special chars
        fallback_sql = """
        SELECT path, name, size, mtime, drive, content_text 
        FROM files 
        WHERE name LIKE ? OR path LIKE ? OR content_text LIKE ?
        LIMIT ?
        """
        like_query = f"%{query_str}%"
        cursor.execute(fallback_sql, (like_query, like_query, like_query, limit))
        rows = cursor.fetchall()
        elapsed = time.time() - start_time
        
        for r in rows:
            snippet_str = ""
            content = r["content_text"]
            if content and query_str.lower() in content.lower():
                idx = content.lower().find(query_str.lower())
                start_idx = max(0, idx - 30)
                end_idx = min(len(content), idx + len(query_str) + 30)
                snippet_str = "..." + content[start_idx:end_idx].replace("\n", " ") + "..."
            results.append({
                "path": r["path"],
                "name": r["name"],
                "size_kb": round(r["size"] / 1024, 2),
                "mtime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r["mtime"])),
                "drive": r["drive"],
                "snippet": snippet_str
            })
    finally:
        conn.close()

    # Save results to memory cache file for blazing fast lookup next time
    if results:
        mem_cache[q_clean] = results[:5]  # Cache top 5 matches
        try:
            os.makedirs(os.path.dirname(FILESEARCHED_PATH), exist_ok=True)
            with open(FILESEARCHED_PATH, "w", encoding="utf-8") as f:
                json.dump(mem_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:
            save_to_search_memory(results)
        except Exception:
            pass

    return {
        "results": results,
        "count": len(results),
        "latency_ms": round(elapsed * 1000, 2)
    }

def save_to_search_memory(files_list):
    """
    Saves a list of found files or folders directly to the filesearched.json memory cache.
    Permits the agent to memorize the location of every file/folder it encounters during any search.
    """
    if not files_list:
        return
        
    try:
        mem_cache = {}
        if os.path.exists(FILESEARCHED_PATH):
            try:
                with open(FILESEARCHED_PATH, "r", encoding="utf-8") as f:
                    mem_cache = json.load(f)
            except Exception:
                pass
                
        # Initialize the global discovered items storage if not present
        if "__all_found_items__" not in mem_cache:
            mem_cache["__all_found_items__"] = {}
            
        dirty = False
        for item in files_list:
            if not isinstance(item, dict) or "path" not in item:
                continue
            path = item["path"]
            name = item.get("name", os.path.basename(path))
            
            # Construct standard metadata dictionary
            size_kb = item.get("size_kb")
            if size_kb is None and "size" in item:
                size_kb = round(item["size"] / 1024, 2)
            elif size_kb is None:
                try:
                    size_kb = round(os.path.getsize(path) / 1024, 2)
                except OSError:
                    size_kb = 0.0
                    
            mtime = item.get("mtime")
            if mtime is None:
                try:
                    mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(path)))
                except OSError:
                    mtime = time.strftime('%Y-%m-%d %H:%M:%S')
                    
            drive = item.get("drive") or os.path.splitdrive(path)[0] or "C:"
            
            item_entry = {
                "path": path,
                "name": name,
                "size_kb": size_kb,
                "mtime": mtime,
                "drive": drive
            }
            
            # Save or update if the path is not yet stored
            path_key = path.lower()
            if path_key not in mem_cache["__all_found_items__"]:
                mem_cache["__all_found_items__"][path_key] = item_entry
                dirty = True
                
        if dirty:
            os.makedirs(os.path.dirname(FILESEARCHED_PATH), exist_ok=True)
            with open(FILESEARCHED_PATH, "w", encoding="utf-8") as f:
                json.dump(mem_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"Failed to write to search memory cache: {e}")
