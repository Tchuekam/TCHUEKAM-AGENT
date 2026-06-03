import time
import sys
import os

sys.path.append('d:/TCHUEKAMV1/tchuekam-agent/app')

try:
    from tools.tchuekam_indexer import get_db_connection, initialize_db, scan_directory
except ImportError as e:
    print(f"Error importing: {e}")
    sys.exit(1)

def main():
    target_dir = 'd:/TCHUEKAMV1'
    print(f"Benchmarking indexing on {target_dir}...")
    
    conn = get_db_connection()
    initialize_db()
    
    start = time.time()
    scan_directory(target_dir, conn)
    duration = time.time() - start
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    file_count = cursor.fetchone()[0]
    
    print(f"Scan complete in {duration:.2f} seconds.")
    print(f"Total files indexed: {file_count}")
    if duration > 0:
        print(f"Speed: {file_count / duration:.2f} files/second")
    
if __name__ == "__main__":
    main()
