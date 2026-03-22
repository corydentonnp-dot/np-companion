"""
Migration: Create 10 structured API cache tables.

Run once:
    python migrate_add_api_cache_tables.py

Tables created:
    rxclass_cache, fda_label_cache, faers_cache, recall_cache,
    loinc_cache, umls_cache, healthfinder_cache, pubmed_cache,
    medlineplus_cache, cdc_immunization_cache
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

TABLES = [
    {
        'name': 'rxclass_cache',
        'ddl': '''
            CREATE TABLE rxclass_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rxcui VARCHAR(20) NOT NULL,
                class_id VARCHAR(50) NOT NULL,
                class_name VARCHAR(300) DEFAULT '',
                class_type VARCHAR(50) DEFAULT '',
                source VARCHAR(30) DEFAULT 'rxclass_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (rxcui, class_id)
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_rxclass_cache_rxcui ON rxclass_cache (rxcui)',
        ],
    },
    {
        'name': 'fda_label_cache',
        'ddl': '''
            CREATE TABLE fda_label_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rxcui VARCHAR(20) NOT NULL UNIQUE,
                spl_id VARCHAR(80) DEFAULT '',
                brand_name VARCHAR(300) DEFAULT '',
                warnings_summary TEXT DEFAULT '',
                boxed_warning TEXT DEFAULT '',
                contra_summary TEXT DEFAULT '',
                source VARCHAR(30) DEFAULT 'openfda_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_fda_label_cache_rxcui ON fda_label_cache (rxcui)',
        ],
    },
    {
        'name': 'faers_cache',
        'ddl': '''
            CREATE TABLE faers_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rxcui VARCHAR(20) NOT NULL UNIQUE,
                total_reports INTEGER DEFAULT 0,
                serious_count INTEGER DEFAULT 0,
                top_reactions JSON DEFAULT '[]',
                report_period VARCHAR(50) DEFAULT '',
                source VARCHAR(30) DEFAULT 'openfda_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_faers_cache_rxcui ON faers_cache (rxcui)',
        ],
    },
    {
        'name': 'recall_cache',
        'ddl': '''
            CREATE TABLE recall_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recall_id VARCHAR(50) NOT NULL UNIQUE,
                product_description TEXT DEFAULT '',
                reason TEXT DEFAULT '',
                status VARCHAR(30) DEFAULT '',
                classification VARCHAR(20) DEFAULT '',
                recall_date DATETIME,
                source VARCHAR(30) DEFAULT 'openfda_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_recall_cache_recall_id ON recall_cache (recall_id)',
        ],
    },
    {
        'name': 'loinc_cache',
        'ddl': '''
            CREATE TABLE loinc_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loinc_code VARCHAR(20) NOT NULL UNIQUE,
                component VARCHAR(300) DEFAULT '',
                system_type VARCHAR(100) DEFAULT '',
                method VARCHAR(200) DEFAULT '',
                display_name VARCHAR(300) DEFAULT '',
                source VARCHAR(30) DEFAULT 'loinc_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_loinc_cache_loinc_code ON loinc_cache (loinc_code)',
        ],
    },
    {
        'name': 'umls_cache',
        'ddl': '''
            CREATE TABLE umls_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cui VARCHAR(20) NOT NULL UNIQUE,
                preferred_name VARCHAR(400) DEFAULT '',
                semantic_type VARCHAR(200) DEFAULT '',
                source_vocab VARCHAR(50) DEFAULT '',
                source VARCHAR(30) DEFAULT 'umls_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_umls_cache_cui ON umls_cache (cui)',
        ],
    },
    {
        'name': 'healthfinder_cache',
        'ddl': '''
            CREATE TABLE healthfinder_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id VARCHAR(30) NOT NULL UNIQUE,
                title VARCHAR(300) DEFAULT '',
                category VARCHAR(100) DEFAULT '',
                url VARCHAR(500) DEFAULT '',
                last_updated DATETIME,
                source VARCHAR(30) DEFAULT 'healthfinder_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_healthfinder_cache_topic_id ON healthfinder_cache (topic_id)',
        ],
    },
    {
        'name': 'pubmed_cache',
        'ddl': '''
            CREATE TABLE pubmed_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pmid VARCHAR(20) NOT NULL UNIQUE,
                title TEXT DEFAULT '',
                abstract_text TEXT DEFAULT '',
                authors VARCHAR(500) DEFAULT '',
                pub_date DATETIME,
                journal VARCHAR(300) DEFAULT '',
                mesh_terms JSON DEFAULT '[]',
                source VARCHAR(30) DEFAULT 'pubmed_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_pubmed_cache_pmid ON pubmed_cache (pmid)',
        ],
    },
    {
        'name': 'medlineplus_cache',
        'ddl': '''
            CREATE TABLE medlineplus_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id VARCHAR(30) NOT NULL UNIQUE,
                title VARCHAR(300) DEFAULT '',
                url VARCHAR(500) DEFAULT '',
                summary TEXT DEFAULT '',
                language VARCHAR(10) DEFAULT 'en',
                source VARCHAR(30) DEFAULT 'medlineplus_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_medlineplus_cache_topic_id ON medlineplus_cache (topic_id)',
        ],
    },
    {
        'name': 'cdc_immunization_cache',
        'ddl': '''
            CREATE TABLE cdc_immunization_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vaccine_code VARCHAR(20) NOT NULL UNIQUE,
                vaccine_name VARCHAR(200) DEFAULT '',
                schedule_description TEXT DEFAULT '',
                min_age VARCHAR(30) DEFAULT '',
                max_age VARCHAR(30) DEFAULT '',
                source VARCHAR(30) DEFAULT 'cdc_api',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS ix_cdc_immunization_cache_vaccine_code ON cdc_immunization_cache (vaccine_code)',
        ],
    },
]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for tbl in TABLES:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (tbl['name'],),
        )
        if cur.fetchone():
            print(f"[{tbl['name']}] Already exists — skipping.")
        else:
            cur.execute(tbl['ddl'])
            for idx_sql in tbl['indexes']:
                cur.execute(idx_sql)
            print(f"[{tbl['name']}] Created.")

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()
