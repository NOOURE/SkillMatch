"""SQLite persistence and fictional offer seeding."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'skillmatch.db'


def initialize(path=DB):
    with sqlite3.connect(path) as conn:
        conn.executescript('''
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, company TEXT NOT NULL,
            city TEXT NOT NULL, contract TEXT NOT NULL, description TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS skills (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS offer_skills (
            offer_id INTEGER REFERENCES offers(id), skill_id INTEGER REFERENCES skills(id),
            PRIMARY KEY(offer_id, skill_id)
        );
        CREATE TABLE IF NOT EXISTS applications (
            offer_id INTEGER PRIMARY KEY REFERENCES offers(id),
            status TEXT NOT NULL CHECK(status IN ('À étudier','Candidature envoyée','Entretien','Refus','Acceptée'))
        );
        ''')
        if not conn.execute('SELECT 1 FROM offers LIMIT 1').fetchone():
            for o in json.loads((ROOT/'data'/'offers.json').read_text(encoding='utf-8')):
                cursor = conn.execute('INSERT INTO offers(title, company, city, contract, description) VALUES (?,?,?,?,?)',
                                      tuple(o[k] for k in ('title','company','city','contract','description')))
                for skill in o['skills']:
                    conn.execute('INSERT OR IGNORE INTO skills(name) VALUES (?)', (skill,))
                    conn.execute('INSERT INTO offer_skills SELECT ?,id FROM skills WHERE name=?', (cursor.lastrowid,skill))


def get_offers(path=DB, city='', contract=''):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''SELECT o.*, COALESCE(a.status,'À étudier') AS status
          FROM offers o LEFT JOIN applications a ON o.id=a.offer_id
          WHERE (?='' OR city=?) AND (?='' OR contract=?) ORDER BY o.id''',
          (city,city,contract,contract)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item['skills'] = [r[0] for r in conn.execute('''SELECT s.name FROM skills s JOIN offer_skills os
                ON s.id=os.skill_id WHERE os.offer_id=? ORDER BY s.name''', (row['id'],))]
            results.append(item)
        return results


STATUSES = ['À étudier','Candidature envoyée','Entretien','Refus','Acceptée']


def set_status(offer_id, status, path=DB):
    if status not in STATUSES:
        raise ValueError('Statut invalide')
    with sqlite3.connect(path) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('INSERT INTO applications(offer_id,status) VALUES (?,?) ON CONFLICT(offer_id) DO UPDATE SET status=excluded.status', (offer_id,status))
