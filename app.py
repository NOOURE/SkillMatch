"""Local web interface. Run: python app.py"""
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, urlencode
from pathlib import Path
import sqlite3
import database
from matching import rank_offers

ROOT = Path(__file__).resolve().parent
DEFAULT_SKILLS = 'Python, Java, SQL, Git, C++'


def options(values, selected, all_label=None):
    output = '<option value="">'+escape(all_label)+'</option>' if all_label else ''
    return output + ''.join(f'<option value="{escape(v)}"{" selected" if v==selected else ""}>{escape(v)}</option>' for v in values)


def render(params):
    skills = params.get('skills', [DEFAULT_SKILLS])[0][:2000]
    interests = params.get('interests', [''])[0][:1000]
    city = params.get('city', [''])[0]
    contract = params.get('contract', [''])[0]
    all_offers = database.get_offers()
    offers = database.get_offers(city=city, contract=contract)
    # Rank the complete corpus before filtering so the same offer keeps its score.
    ranked_all = rank_offers(all_offers, skills, interests)
    ids = {o['id'] for o in offers}
    ranked = [o for o in ranked_all if o['id'] in ids]
    cities = sorted({o['city'] for o in all_offers})
    applied = sum(o['status'] != 'À étudier' for o in all_offers)
    cards = []
    for o in ranked:
        def chips(items, cls):
            return ''.join(f'<span class="chip {cls}">{escape(s)}</span>' for s in items) or '<span class="muted">Aucune</span>'
        hidden = ''.join(f'<input type="hidden" name="{k}" value="{escape(v)}">' for k,v in [('skills',skills),('interests',interests),('city',city),('contract',contract)])
        cards.append(f'''<article class="offer"><div class="offerhead"><div><span class="eyebrow">{escape(o['contract'])} · {escape(o['city'])}</span><h2>{escape(o['title'])}</h2><p class="muted">{escape(o['company'])}</p></div><div class="score">{o['score']}<small>/100</small></div></div>
        <div class="track"><span style="width:{o['score']}%"></span></div><p class="details">Compétences couvertes : {o['coverage']} % · Similarité textuelle : {o['similarity']} %</p><p>{escape(o['description'])}</p>
        <div class="skillgroup"><strong>Compétences communes</strong><div>{chips(o['matched'],'yes')}</div></div>
        <div class="skillgroup"><strong>À développer</strong><div>{chips(o['missing'],'no')}</div></div>
        <form class="status" action="/status" method="post">{hidden}<input type="hidden" name="id" value="{o['id']}"><label>Suivi de candidature<select name="status">{options(database.STATUSES,o['status'])}</select></label><button class="secondary">Enregistrer</button></form></article>''')
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SkillMatch</title><link rel="stylesheet" href="/style.css"></head><body><main>
    <header><span class="brand">SKILLMATCH / PORTFOLIO</span><h1>Le bon poste, les bonnes compétences.</h1><p>Explore les offres, identifie tes points forts et construis ton parcours.</p></header>
    <section class="notice">Démonstration : les 12 offres et entreprises sont fictives. Les scores sont des indicateurs de proximité, pas des probabilités de recrutement.</section>
    <section class="metrics"><div><small>Offres filtrées</small><b>{len(ranked)}</b></div><div><small>Meilleur score</small><b>{str(ranked[0]['score'])+'/100' if ranked else '—'}</b></div><div><small>Offres suivies</small><b>{applied}</b></div></section>
    <section class="panel"><h2>Mon profil</h2><form method="get" action="/"><label>Compétences (séparées par des virgules)<textarea name="skills" rows="2" placeholder="Python, SQL, Git">{escape(skills)}</textarea></label><label>Domaines ou mots-clés souhaités<input name="interests" value="{escape(interests)}" placeholder="Data engineering, intelligence artificielle…"></label><div class="filters"><label>Ville<select name="city">{options(cities,city,'Toutes les villes')}</select></label><label>Contrat<select name="contract">{options(['Stage','Alternance'],contract,'Tous les contrats')}</select></label></div><button>Analyser les offres</button></form></section>
    <section class="results"><div class="sectionhead"><h2>Offres classées</h2><small>80 % compétences · 20 % similarité TF-IDF</small></div>{''.join(cards) or '<p>Aucune offre pour ces filtres.</p>'}</section>
    <footer>Projet pédagogique Python · SQLite · NLP (TF-IDF) · Interface web locale.</footer></main></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/style.css':
            self.respond(200,(ROOT/'static'/'style.css').read_bytes(),'text/css; charset=utf-8')
        elif parsed.path == '/':
            self.respond(200,render(parse_qs(parsed.query,keep_blank_values=True)).encode(),'text/html; charset=utf-8')
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != '/status':
            self.send_error(404); return
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16000:
                self.send_error(400); return
            params = parse_qs(self.rfile.read(length).decode(),keep_blank_values=True)
            database.set_status(int(params['id'][0]),params['status'][0])
        except (ValueError, KeyError, UnicodeError, sqlite3.IntegrityError):
            self.send_error(400); return
        self.send_response(303)
        self.send_header('Location','/?'+urlencode({k:params.get(k,[''])[0] for k in ('skills','interests','city','contract')}))
        self.end_headers()

    def respond(self, code, data, content_type):
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    database.initialize()
    print('SkillMatch : http://127.0.0.1:8000 (Ctrl+C pour arrêter)')
    server = ThreadingHTTPServer(('127.0.0.1',8000),Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
