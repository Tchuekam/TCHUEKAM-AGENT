import sqlite3
import os
import re

class SQLitePipeline:
    def __init__(self):
        # Resolve database path relative to this script, matching the Node database
        self.db_path = os.environ.get('DATABASE_PATH') or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            'leads.db'
        )

    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        
        # Ensure database tables are created (redundancy check)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                website TEXT,
                source TEXT NOT NULL,
                category TEXT,
                location TEXT,
                rating REAL,
                date_scraped TEXT DEFAULT CURRENT_TIMESTAMP,
                contacted_status TEXT DEFAULT 'pending',
                priority_score INTEGER,
                message_template TEXT
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def clean_value(self, val):
        if not val:
            return ''
        return str(val).strip().lower()

    def calculate_priority(self, item):
        has_phone = bool(item.get('phone'))
        has_email = bool(item.get('email'))
        has_website = bool(item.get('website'))

        if has_website and has_phone and has_email:
            return 3  # High
        elif has_phone:
            return 2  # Medium
        elif has_email:
            return 1  # Low
        return 1

    def generate_message_template(self, item):
        name = item.get('name', 'Partenaire')
        category = item.get('category', 'Business')
        location = item.get('location', '')
        
        # Keep same cultural Cameroonian template rules
        is_cameroon = 'cameroun' in location.lower() or 'cameroon' in location.lower() or 'yaounde' in location.lower() or 'douala' in location.lower()
        
        if is_cameroon:
            return f"Bonjour {name}, je suis de Giantect Empire à Yaoundé. Nous aidons les entreprises à automatiser leurs opérations avec l'IA. Pour un établissement spécialisé dans le secteur ({category}), nous pouvons optimiser vos processus. Avez-vous 5 minutes cette semaine pour une démo rapide sur WhatsApp ?"
        else:
            return f"Bonjour {name}, nous sommes de Giantect Empire. Nous déployons des systèmes d'IA Agentique autonomes pour automatiser vos tâches opérationnelles dans le domaine ({category}). Seriez-vous disponible cette semaine pour un échange rapide ?"

    def process_item(self, item, spider):
        phone = item.get('phone', '')
        email = item.get('email', '')
        
        cleaned_phone = self.clean_value(phone)
        cleaned_email = self.clean_value(email)
        
        existing = None
        
        # 1. Deduplicate by phone
        if cleaned_phone:
            self.cur.execute("SELECT id, source, name, website, category, location, rating FROM leads WHERE phone = ?", (cleaned_phone,))
            row = self.cur.fetchone()
            if row:
                existing = row
                
        # 2. Deduplicate by email
        if not existing and cleaned_email:
            self.cur.execute("SELECT id, source, name, website, category, location, rating FROM leads WHERE email = ?", (cleaned_email,))
            row = self.cur.fetchone()
            if row:
                existing = row

        priority = self.calculate_priority(item)
        template = self.generate_message_template(item)

        if existing:
            # Merge fields
            existing_id = existing[0]
            existing_source = existing[1]
            
            merged_source = existing_source
            if item.get('source') and item.get('source') not in existing_source:
                merged_source = f"{existing_source}, {item.get('source')}"
                
            self.cur.execute("""
                UPDATE leads SET
                    name = COALESCE(NULLIF(?, ''), name),
                    phone = COALESCE(NULLIF(?, ''), phone),
                    email = COALESCE(NULLIF(?, ''), email),
                    website = COALESCE(NULLIF(?, ''), website),
                    source = ?,
                    category = COALESCE(NULLIF(?, ''), category),
                    location = COALESCE(NULLIF(?, ''), location),
                    rating = COALESCE(?, rating),
                    priority_score = ?,
                    message_template = ?
                WHERE id = ?
            """, (
                item.get('name', ''),
                phone,
                email,
                item.get('website', ''),
                merged_source,
                item.get('category', ''),
                item.get('location', ''),
                item.get('rating', None),
                priority,
                template,
                existing_id
            ))
            spider.log(f"Merged Scrapy lead into database ID: {existing_id}")
        else:
            # Insert fresh lead
            self.cur.execute("""
                INSERT INTO leads (name, phone, email, website, source, category, location, rating, priority_score, message_template)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('name', ''),
                phone,
                email,
                item.get('website', ''),
                item.get('source', 'Scrapy Scraper'),
                item.get('category', ''),
                item.get('location', ''),
                item.get('rating', None),
                priority,
                template
            ))
            spider.log(f"Inserted new Scrapy lead: {item.get('name')}")
            
        self.conn.commit()
        return item
