"""Genera il sito statico in dist/ partendo da contenuti/, mazzi/, dati/ e sito.yml.

Uso:  python motore/build.py
"""
import hashlib, html, json, re, shutil, sys, urllib.request
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
E = html.escape
CFG = yaml.safe_load((ROOT / 'sito.yml').read_text(encoding='utf-8'))
HOME = yaml.safe_load((ROOT / 'dati/home.yml').read_text(encoding='utf-8'))
MZ = yaml.safe_load((ROOT / 'dati/mazzi.yml').read_text(encoding='utf-8'))
FORMATI, FAMIGLIE = MZ['formati'], MZ['famiglie']
ERRORI = []


def avviso(msg):
    ERRORI.append(msg)
    print('  ATTENZIONE:', msg)


def leggi_md(path):
    """File con intestazione YAML tra due righe '---', poi il testo."""
    t = path.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', t, re.S)
    if not m:
        raise SystemExit(f'{path}: manca l\'intestazione tra le righe ---')
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise SystemExit(f'{path}: errore nell\'intestazione\n{e}')
    return meta, m.group(2).strip()


# ------------------------------------------------------------------ carte
ORDER = list(CFG['set_in_ordine'])
CARTE_DIR = ROOT / 'dati/carte'
FONTE = 'https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master'


def scarica(nome, url):
    dest = CARTE_DIR / nome
    if dest.exists():
        return
    print('  scarico', url)
    with urllib.request.urlopen(url, timeout=60) as r:
        dest.write_bytes(r.read())


scarica('_set.json', f'{FONTE}/sets/en.json')
for s in ORDER:
    scarica(f'{s}.json', f'{FONTE}/cards/en/{s}.json')
SETNAME = {s['id']: s['name'] for s in json.loads((CARTE_DIR / '_set.json').read_text(encoding='utf-8'))}
CARDS, BYNAME = {}, {}
for s in ORDER:
    for c in json.loads((CARTE_DIR / f'{s}.json').read_text(encoding='utf-8')):
        CARDS[c['id']] = c
        BYNAME.setdefault(c['name'], []).append(c['id'])
BASE_EN = ('Grass', 'Fire', 'Water', 'Lightning', 'Psychic', 'Fighting', 'Darkness', 'Metal')
SKIP = set(CFG.get('non_collegare') or []) | {n for n in BYNAME if len(n) < 3 or (n.endswith(' Energy') and n.split()[0] in BASE_EN)}
SKIP -= {'Darkness Energy', 'Metal Energy'}
NAMES = sorted((n for n in BYNAME if n not in SKIP), key=len, reverse=True)
RX = re.compile(r"(?<![\w'’])(" + '|'.join(re.escape(n) for n in NAMES) + r")(?![\w])")


def era_index(code):
    if code not in ORDER:
        avviso(f'set_carte "{code}" non è in set_in_ordine di sito.yml')
        return len(ORDER) - 1
    return ORDER.index(code)


def pick(name, era, home=None):
    ids = BYNAME[name]
    if home:
        h = [i for i in ids if i.split('-')[0] == home]
        if h:
            return h[0]
    best = None
    for i in ids:
        if ORDER.index(i.split('-')[0]) <= era:
            best = i
    return best or ids[0]


NOLINK = re.compile(r'^<(/?)(h1|h2|h3|h4|a|summary|th|button)\b', re.I)


def collega_carte(h, era, home, usate):
    out, stack = [], 0
    for tok in re.split(r'(<[^>]+>)', h):
        if tok.startswith('<'):
            m = NOLINK.match(tok)
            if m:
                stack += -1 if m.group(1) else 1
            out.append(tok)
            continue
        if stack > 0 or not tok.strip():
            out.append(tok)
            continue

        def rep(m):
            cid = pick(m.group(1), era, home)
            usate.add(cid)
            return f'<span class="cd" tabindex="0" data-c="{cid}">{m.group(1)}</span>'
        out.append(RX.sub(rep, tok))
    return ''.join(out)


T = {'Grass': 'G', 'Fire': 'R', 'Water': 'W', 'Lightning': 'L', 'Psychic': 'P', 'Fighting': 'F', 'Colorless': 'C',
     'Darkness': 'D', 'Metal': 'M', 'Dragon': 'N', 'Free': '0'}


def compatta(cid):
    c = CARDS[cid]
    d = {'n': c['name'], 's': SETNAME.get(c['id'].split('-')[0], ''), 'no': c['number'], 'sup': c['supertype'][0], 'sub': c.get('subtypes') or []}
    if c.get('hp'): d['hp'] = c['hp']
    if c.get('types'): d['t'] = ''.join(T.get(x, 'C') for x in c['types'])
    if c.get('evolvesFrom'): d['ev'] = c['evolvesFrom']
    if c.get('abilities'): d['ab'] = [[a.get('type', ''), a['name'], a.get('text', '')] for a in c['abilities']]
    if c.get('attacks'): d['at'] = [[a['name'], ''.join(T.get(x, 'C') for x in a.get('cost', [])), a.get('damage', ''), a.get('text', '')] for a in c['attacks']]
    if c.get('weaknesses'): d['w'] = ' '.join(T.get(x['type'], 'C') + x['value'] for x in c['weaknesses'])
    if c.get('resistances'): d['r'] = ' '.join(T.get(x['type'], 'C') + x['value'] for x in c['resistances'])
    if c.get('convertedRetreatCost') is not None and c['supertype'] == 'Pokémon': d['rc'] = c['convertedRetreatCost']
    if c['supertype'] != 'Pokémon' and c.get('rules'):
        d['ru'] = [x for x in c['rules'] if not x.startswith('You can play only one') and not x.startswith('This card stays in play')][:3]
    if c.get('rarity'): d['ra'] = c['rarity']
    if c.get('images'): d['img'] = c['images'].get('small'); d['big'] = c['images'].get('large')
    return d


# ------------------------------------------------------------------ markdown
TYPES = {"Erba": "t-grass", "Fuoco": "t-fire", "Acqua": "t-water", "Lampo": "t-light", "Psico": "t-psy",
         "Lotta": "t-fight", "Incolore": "t-col", "Buio": "t-dark", "Metallo": "t-metal", "Drago": "t-col",
         "Allenatore": "t-tr", "Strumento": "t-tr", "Stadio": "t-stad", "Aiuto": "t-tr", "Energia": "t-en",
         "Energia Speciale": "t-en", "Energia speciale": "t-en", "Energia Base": "t-en"}
WEIGHT = {"Dominante": "w-dom", "Top tier": "w-top", "Top": "w-top", "Medio": "w-mid", "Secondo piano": "w-mid",
          "Nicchia": "w-niche", "Tech o nicchia": "w-niche", "Casual": "w-cas"}


def md2html(t):
    h = markdown.markdown(t, extensions=['tables', 'sane_lists'])

    def cell(m):
        s = m.group(1).strip()
        if s in TYPES: return f'<td><span class="chip {TYPES[s]}">{s}</span></td>'
        if '/' in s and all(x in TYPES for x in s.split('/')):
            return '<td>' + ''.join(f'<span class="chip {TYPES[x]}">{x}</span>' for x in s.split('/')) + '</td>'
        if s in WEIGHT: return f'<td><span class="wt {WEIGHT[s]}">{s}</span></td>'
        return m.group(0)
    h = re.sub(r'<td>(.*?)</td>', cell, h, flags=re.S)

    def tbl(m):
        body = m.group(0); head = body.split('</tr>')[0]; n = head.count('<th'); rows = body.count('<tr>') - 1
        cls = 'wide' if n >= 8 else ('mid' if n >= 5 else 'narrow')
        if n == 2 and 'Qtà' in head: cls = 'deck'
        if n == 2 and 'Voce' in head: cls = 'facts'
        t = f'<div class="tw"><table class="{cls}">' + body[len('<table>'):] + '</div>'
        if n >= 8 and rows > 25:
            t = f'<details class="big"><summary>Mostra la tabella completa ({rows} carte)</summary>{t}</details>'
        return t
    h = re.sub(r'<table>.*?</table>', tbl, h, flags=re.S)
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    return h


def md_semplice(t):
    return markdown.markdown(t, extensions=['tables'])


# ------------------------------------------------------------------ pagine
PAGINE = []
for f in sorted((ROOT / 'contenuti').rglob('*.md')):
    meta, body = leggi_md(f)
    for k in ('id', 'volume', 'tipo', 'titolo', 'colore', 'set_carte'):
        if k not in meta:
            raise SystemExit(f'{f.relative_to(ROOT)}: manca il campo "{k}" nell\'intestazione')
    lead, _, rest = body.partition('<!-- fine attacco -->') if '<!-- fine attacco -->' in body else ('', '', body)
    meta['_lead'] = md2html(lead.strip()) if lead.strip() else ''
    meta['_html'] = md2html(rest.strip())
    meta['_file'] = f.relative_to(ROOT).as_posix()
    PAGINE.append(meta)
IDS = [p['id'] for p in PAGINE]
for i in set(i for i in IDS if IDS.count(i) > 1):
    raise SystemExit(f'Due pagine hanno lo stesso id "{i}": ogni id deve essere unico')

# "Cap. 7" nel Volume IV -> pagina del capitolo
V4 = [p['id'] for p in PAGINE if p['volume'] == 4 and p['tipo'] == 'set']


def link_cap(h):
    def rep(m):
        n = int(m.group(2))
        return f'<a href="#{V4[n-1]}">{m.group(1)} {n}</a>' if 1 <= n <= len(V4) else m.group(0)
    return re.sub(r'(?<![\w">])(Cap\.|Capitolo) (\d{1,2})(?!\d)', rep, h)


for p in PAGINE:
    if p['volume'] == 4:
        p['_html'] = link_cap(p['_html']); p['_lead'] = link_cap(p['_lead'])

# ------------------------------------------------------------------ mazzi
ROLE = {}
for r, names in {
  'Pescata': ["Professor Oak", "Bill", "Professor Elm", "Copycat", "Steven's Advice", "TV Reporter", "Rocket's Admin.", "Professor Oak's Research", "Prof. Oak's Research", "Holon Scientist", "Holon Adventurer", "Mary's Request", "Bill's Maintenance", "Professor Cozmo's Discovery", "Professor Cosmo's Discovery", "Professor Birch", "Oracle", "Rocket's Mission", "Desert Shaman", "Fieldworker", "Imposter Oak's Revenge"],
  'Ricerca': ["Computer Search", "Pokémon Trader", "Celio's Network", "Lanette's Net Search", "Holon Mentor", "Professor Elm's Training Method", "Great Ball", "Dual Ball", "Poké Ball", "Master Ball", "Fast Ball", "Rocket's Poké Ball", "Rocket's Poke Ball", "Scott", "Holon Transceiver", "Holon Researcher", "Mr. Stone's Project", "Energy Search", "Pokédex", "Team Magma Ball", "Team Aqua Ball", "Moo-Moo Milk"],
  'Evoluzione': ["Pokémon Breeder", "Rare Candy", "Wally's Training", "Surprise! Time Machine"],
  'Disturbo': ["Energy Removal", "Super Energy Removal", "Energy Removal 2", "Gust of Wind", "Pokémon Reversal", "Rocket's Sneak Attack", "Pow! Hand Extension", "Imposter Professor Oak", "Double Gust", "Lass", "The Rocket's Trap", "Team Aqua Conspirator", "Desert Ruins", "Battle Frontier", "Cursed Stone", "Chaos Gym", "Narrow Gym"],
  'Danni': ["PlusPower", "Strength Charm", "Solid Rage", "ATM: Rock", "ATM Rock", "Magnetic Storm"],
  'Movimento': ["Switch", "Warp Point", "Swoop! Teleporter", "Scoop Up", "Super Scoop Up", "Crystal Shard", "Balloon Berry"],
  'Cura': ["Pokémon Center", "Super Potion", "Potion", "Life Herb", "Oran Berry", "Mr. Briney's Compassion", "Full Heal", "Gold Berry", "Island Cave"],
  'Recupero': ["Item Finder", "Pokémon Retriever", "Night Maintenance", "Energy Retrieval", "Super Energy Retrieval", "VS Seeker", "Town Volunteers", "Energy Charge", "Pokémon Rescue", "EXP.ALL", "EXP ALL"],
  'Protezione': ["Focus Band", "Buffer Piece"],
}.items():
    for n in names:
        ROLE[n] = r
BASIC_IT = {'Erba', 'Fuoco', 'Acqua', 'Lampo', 'Psico', 'Lotta'}


def base_name(s):
    s = re.sub(r'\s*\(.*?\)\s*$', '', s).strip()
    return s.replace('Prof. Oak', 'Professor Oak') if s.startswith('Prof. Oak') and s not in BYNAME else s


def classify(name):
    if name.startswith('Energia ') and name.split()[1] in BASIC_IT | {'base'}: return 'E'
    n = base_name(name)
    if n in BYNAME:
        return {'Pokémon': 'P', 'Trainer': 'T', 'Energy': 'E'}[CARDS[BYNAME[n][0]]['supertype']]
    return 'E' if 'Energy' in n else 'T'


MAZZI = []
for f in sorted((ROOT / 'mazzi').glob('*.md')):
    meta, body = leggi_md(f)
    rel = f.relative_to(ROOT).as_posix()
    for k in ('slug', 'nome', 'famiglia', 'formato', 'in_breve'):
        if k not in meta:
            raise SystemExit(f'{rel}: manca il campo "{k}"')
    if meta['formato'] not in FORMATI:
        raise SystemExit(f'{rel}: formato "{meta["formato"]}" non esiste in dati/mazzi.yml')
    if meta['famiglia'] not in FAMIGLIE:
        raise SystemExit(f'{rel}: famiglia "{meta["famiglia"]}" non esiste in dati/mazzi.yml')
    parts = re.split(r'^## (.+)$', body, flags=re.M)
    sec = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    rows = []
    for ln in sec.get('lista', '').splitlines():
        ln = ln.strip().lstrip('-').strip()
        if not ln:
            continue
        m = re.match(r'^(\d+)\s*x?\s+(.+)$', ln)
        if not m:
            avviso(f'{rel}: riga della lista non capita: "{ln}" (scrivi per esempio "4 Electabuzz")')
            continue
        rows.append((int(m.group(1)), m.group(2).strip()))
    tot = sum(q for q, _ in rows)
    if rows and tot != 60:
        avviso(f'{rel}: la lista ha {tot} carte invece di 60')
    meta.update(_rows=rows, _come=sec.get('come funziona', ''), _note=sec.get('note', ''), _file=rel)
    meta.setdefault('punti_deboli', []); meta.setdefault('matchup', [])
    MAZZI.append(meta)
SLUGS = {d['slug']: d for d in MAZZI}
ESITO = {'favorevole': 'F', 'pari': 'P', 'sfavorevole': 'S'}
for d in MAZZI:
    for m in d['matchup']:
        if m.get('contro') not in SLUGS:
            avviso(f'{d["_file"]}: matchup contro "{m.get("contro")}", ma nessun mazzo ha questo slug')
        if m.get('esito') not in ESITO:
            avviso(f'{d["_file"]}: esito "{m.get("esito")}" non valido (usa favorevole, pari o sfavorevole)')


def stima(d):
    mus = [m for m in d['matchup'] if m.get('esito') in ESITO]
    F = sum(1 for m in mus if m['esito'] == 'favorevole'); P = sum(1 for m in mus if m['esito'] == 'pari')
    S = sum(1 for m in mus if m['esito'] == 'sfavorevole')
    return F, P, S, len(mus), (round(100 * (F + .5 * P) / len(mus)) if mus else None)


def pagina_mazzo(d):
    fm = FORMATI[d['formato']]
    keytext = (d['in_breve'] + ' ' + d['_come']).lower()
    groups = {'P': [], 'T': [], 'E': []}
    for q, c in d['_rows']:
        groups[classify(c)].append((q, c))

    def row(q, c):
        n = base_name(c); tag = ''
        if classify(c) == 'P' and n.lower() in keytext: tag = '<span class="role key">Carta chiave</span>'
        elif n in ROLE: tag = f'<span class="role">{ROLE[n]}</span>'
        return f'<tr><td class="q">{q}</td><td>{E(c)}</td><td class="r">{tag}</td></tr>'
    lists = ''
    for k, lab in (('P', 'Pokémon'), ('T', 'Allenatori'), ('E', 'Energie')):
        g = groups[k]
        if g:
            lists += f'<div class="lg"><h4>{lab} <span>{sum(q for q, _ in g)}</span></h4><div class="tw"><table class="dl"><tbody>{"".join(row(q, c) for q, c in g)}</tbody></table></div></div>'
    F, Pn, S, tot, pct = stima(d)
    lab = {'F': 'Favorevole', 'P': 'Pari', 'S': 'Sfavorevole'}
    mrows = ''
    for m in d['matchup']:
        r = ESITO.get(m.get('esito'), 'P'); o = m.get('contro')
        nome = E(SLUGS[o]['nome']) if o in SLUGS else E(str(o))
        mrows += f'<tr><td><a href="#mazzo-{o}">{nome}</a></td><td><span class="mu mu-{r}">{lab[r]}</span></td><td>{E(m.get("perche", ""))}</td></tr>'
    bal = ''
    if pct is not None:
        bal = f'''<div class="bal"><div class="bal-n"><b>{pct}%</b><span>stima di vittoria nel formato</span></div>
<div class="bar" role="img" aria-label="{F} favorevoli, {Pn} pari, {S} sfavorevoli"><i class="b-F" style="flex:{F}"></i><i class="b-P" style="flex:{Pn}"></i><i class="b-S" style="flex:{S}"></i></div>
<p>{F} favorevoli · {Pn} pari · {S} sfavorevoli su {tot} matchup analizzati. È una stima qualitativa: favorevole conta 1, pari 0,5, sfavorevole 0. Per i tornei del 1999–2006 non esistono statistiche di vittoria.</p></div>'''
    var = [x for x in MAZZI if x['famiglia'] == d['famiglia'] and x['slug'] != d['slug']]
    vhtml = ''
    if var:
        vhtml = '<h2>Le varianti di questo mazzo</h2><p class="sub">Altri mazzi della stessa famiglia, in ordine cronologico.</p><ul class="vlist">' + ''.join(
            f'<li><a href="#mazzo-{x["slug"]}" style="--fc:{FORMATI[x["formato"]]["colore"]}"><span class="vf">{E(FORMATI[x["formato"]]["nome"])}</span><b>{E(x["nome"])}</b></a></li>' for x in var) + '</ul>'
    src = d.get('pagina_della_lista') or fm['pagina']
    res = d.get('risultato')
    deboli = ''.join(f'<li>{E(w)}</li>' for w in d['punti_deboli'])
    body = f'''<div class="dk-top"><div class="dk-sum"><p class="dk-micro">{E(d["in_breve"])}</p>
{('<p class="dk-res"><b>Risultato.</b> ' + E(res) + '</p>') if res else ''}
<p class="dk-arch">Famiglia: <b>{E(FAMIGLIE[d["famiglia"]])}</b> · Formato: <a href="#{fm["pagina"]}">{E(fm["nome"])}</a></p></div>{bal}</div>
<h2>Come funziona</h2><div class="prose-in">{md_semplice(d["_come"])}{md_semplice(d["_note"]) if d["_note"] else ""}</div>
<h2>La lista completa</h2><p class="sub">60 carte. Le etichette indicano il ruolo di ogni Allenatore; «Carta chiave» segna i Pokémon citati nella spiegazione. Passa il mouse su un nome per vedere la carta.</p>
<div class="lists">{lists}</div>
<h2>Punti deboli</h2><ul>{deboli}</ul>
<h2>Matchup</h2><div class="tw"><table class="mid"><thead><tr><th>Contro</th><th>Esito</th><th>Perché</th></tr></thead><tbody>{mrows}</tbody></table></div>
{vhtml}
<p class="src">Lista e analisi complete nella pagina <a href="#{src}">del volume</a>.</p>'''
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    return {'id': f'mazzo-{d["slug"]}', 'volume': 0, 'tipo': 'deck', 'titolo': d['nome'], 'occhiello': f'Mazzi · {fm["nome"]} · {fm["periodo"]}',
            'colore': fm['colore'], 'set_carte': fm['set_carte'], '_lead': '', '_html': body, 'sottotitolo': '', '_desc': d['in_breve']}


def indice_mazzi():
    out = ['<p class="dk-intro">Tutti i mazzi con lista completa citati nell\'enciclopedia, in ordine cronologico dal Set Base del 1999 alla stagione 2005–06. Ogni scheda spiega in breve come funziona il mazzo, mostra la lista spiegata, i punti deboli, i matchup e le varianti della stessa famiglia.</p>',
           '<p class="note">La «stima di vittoria» riassume i matchup qualitativi analizzati nelle schede: non esistono statistiche ufficiali di vittoria per i tornei di quegli anni.</p>',
           '<div class="dk-filter" role="group" aria-label="Filtra per famiglia"><button class="on" data-a="">Tutte le famiglie</button>' +
           ''.join(f'<button data-a="{k}">{E(v)}</button>' for k, v in FAMIGLIE.items() if sum(1 for d in MAZZI if d['famiglia'] == k) > 1) + '</div>']
    for fk, fm in FORMATI.items():
        ds = [d for d in MAZZI if d['formato'] == fk]
        if not ds:
            continue
        ch = ''
        for d in ds:
            pct = stima(d)[4]
            micro = d['in_breve'] if len(d['in_breve']) <= 150 else d['in_breve'][:150].rsplit(' ', 1)[0] + '…'
            ch += f'''<a class="dkc" href="#mazzo-{d["slug"]}" data-a="{d["famiglia"]}"><span class="dkc-a">{E(FAMIGLIE[d["famiglia"]])}</span><b>{E(d["nome"])}</b>
{('<span class="dkc-r">' + E(d["risultato"]) + '</span>') if d.get("risultato") else ''}<span class="dkc-m">{E(micro)}</span>
{f'<span class="dkc-p"><i style="width:{pct}%"></i><em>{pct}%</em></span>' if pct is not None else ''}</a>'''
        out.append(f'<section class="dk-era" style="--fc:{fm["colore"]}"><div class="dk-eh"><h2>{E(fm["nome"])}</h2><span>{E(fm["periodo"])} · {len(ds)} mazzi</span></div><div class="dk-grid">{ch}</div></section>')
    return {'id': 'mazzi', 'volume': 0, 'tipo': 'decks', 'titolo': 'I mazzi iconici', 'occhiello': 'Catalogo cronologico · 1999–2006',
            'sottotitolo': f'{len(MAZZI)} mazzi con lista completa, dal Set Base a EX Holon Phantoms', 'colore': '#c99a16', 'set_carte': ORDER[-1],
            '_lead': '', '_html': '\n'.join(out), '_nolink': True}


DECKP = [indice_mazzi()] + [pagina_mazzo(d) for d in MAZZI]
TUTTE = PAGINE + DECKP
TUTTI_ID = {p['id'] for p in TUTTE} | {'home'}

# ------------------------------------------------------------------ layout
VOLS = HOME['volumi']
def parti(v):
    """Le parti di un volume, se in dati/home.yml c'è la voce parti_volume_<n>."""
    d = HOME.get(f'parti_volume_{v}') or {}
    return {int(k): x for k, x in d.items()}


def nav(cur):
    on = lambda i: ' class="on"' if i == cur else ''
    deck_on = ' on' if cur == 'mazzi' or cur.startswith('mazzo-') else ''
    out = [f'<a class="nav-home" href="#home"><span class="bm" aria-hidden="true"></span>{E(CFG["titolo"])}</a>',
           f'<a class="nav-decks{deck_on}" href="#mazzi"><span>I mazzi iconici</span><span class="ny">{len(MAZZI)} schede</span></a>']
    for v in VOLS:
        items = [p for p in PAGINE if p['volume'] == v['volume']]
        out.append(f'<div class="nav-vol" style="--vc:{v["colore"]}"><a class="nav-vh" href="#{v["prima_pagina"]}"><span class="nv">{E(v["nome"])}</span><span class="ny">{E(v["anni"])}</span></a><ul>')
        last = None
        for p in items:
            if p.get('parte') and p.get('parte') != last:
                last = p.get('parte'); pp = parti(v['volume']).get(last) or {'nome': f'Parte {last}', 'titolo': ''}
                out.append(f'<li class="nav-part">{E(pp["nome"])} · {E(pp["titolo"][-7:])}</li>')
            labn = {'intro': 'Introduzione', 'concl': 'Bilancio della stagione' if p.get('parte') else 'Conclusione'}.get(p['tipo'], p['titolo'])
            out.append(f'<li><a href="#{p["id"]}"{on(p["id"])} data-k="{p["tipo"]}">{E(labn)}</a></li>')
        out.append('</ul></div>')
    return '\n'.join(out)


def home_html():
    H = HOME; ap = H['apertura']; ere = H['ere']
    strip = ''.join(f'<a class="seg" href="#{e["pagina"]}" style="--ec:{e["colore"]};flex:{e["peso"]}" title="{E(e["formato"])}"><span>{E(e["anni"])}</span></a>' for e in ere)
    eras = ''
    for e in ere:
        ds = ''.join(f'<li>{E(x)}</li>' for x in e['mazzi'])
        eras += f'''<li class="era" style="--ec:{e["colore"]}">
  <div class="era-when"><span class="era-y">{E(e["anni"])}</span><span class="era-d">{E(e["periodo"])}</span></div>
  <div class="era-body"><p class="era-f">{E(e["formato"])}</p><h3>{E(e["titolo"])}</h3><p>{E(e["testo"])}</p><ul class="decks">{ds}</ul>
  <a class="more" href="#{e["pagina"]}">Leggi l'analisi</a></div></li>'''
    champs = ''.join(f'<tr><td class="num">{E(str(c["anno"]))}</td><td>{E(c["sede"])}</td><td><a href="#{c["pagina"]}">{E(c["mazzo"])}</a></td><td>{E(c["giocatore"])}</td><td>{E(c["pokemon_ex"])}</td></tr>' for c in H['campioni'])
    vols = ''
    for v in VOLS:
        sets = [p['titolo'] for p in PAGINE if p['volume'] == v['volume'] and p['tipo'] == 'set']
        extra = ''
        pv = parti(v['volume'])
        if pv:
            primo = {p['parte']: p['id'] for p in reversed(PAGINE) if p['volume'] == v['volume'] and p.get('parte')}
            extra = '<div class="vparts">' + ''.join(f'<a href="#{primo.get(k, v["prima_pagina"])}">{E(x["nome"])} · {E(x["titolo"])}</a>' for k, x in pv.items()) + '</div>'
        vols += f'''<article class="vol" style="--vc:{v["colore"]}"><a class="vol-link" href="#{v["prima_pagina"]}"><span class="vol-n">{E(v["nome"])}</span><span class="vol-y">{E(v["anni"])}</span><h3>{E(v["titolo"])}</h3></a>
<p class="vol-sets">{E(" · ".join(sets))}</p>{extra}</article>'''
    ev = H['in_evidenza']
    lib = ''.join(f'<a class="book" href="#pdf/{b["file"]}.pdf" target="_blank" rel="noopener"><img src="#img/{b["file"]}.jpg" alt="Copertina: {E(b["volume"])}" width="160" height="226" loading="lazy"><span class="bk-v">{E(b["volume"])}</span><span class="bk-t">{E(b["titolo"])}</span><span class="bk-p">PDF · {b["pagine"]} pagine</span></a>' for b in H['pdf'])
    return f'''<section class="hero">
  <p class="eyebrow">{E(ap["occhiello"])}</p>
  <h1>{ap["titolo"]}</h1>
  <p class="dek">{E(ap["testo"])}</p>
  <div class="strip" aria-label="Le ere del meta">{strip}</div>
  <div class="strip-axis"><span>{E(str(ap["inizio"]))}</span><span>{E(str(ap["fine"]))}</span></div>
</section>
<section class="hsec promo"><a href="#{ev["pagina"]}"><span class="eyebrow">{E(ev["etichetta"])}</span><b>{E(ev["titolo"])}</b><span>{E(ev["testo"].replace("{n}", str(len(MAZZI))))}</span></a></section>
<section class="hsec"><div class="hsec-h"><h2>L'evoluzione del meta</h2><p>{E(H["sottotitolo_ere"])}</p></div>
<ol class="eras">{eras}</ol></section>
<section class="hsec two"><div class="consts"><h2>Le tre costanti</h2>
<ul>{"".join(f"<li>{x}</li>" for x in H["costanti"])}</ul></div>
<div class="champs"><h2>Campioni del mondo</h2><div class="tw"><table class="mid"><thead><tr><th>Anno</th><th>Sede</th><th>Mazzo</th><th>Giocatore (15+ anni)</th><th>Pokémon-ex</th></tr></thead><tbody>{champs}</tbody></table></div>
<p class="note">{E(H["nota_campioni"])}</p></div></section>
<section class="hsec"><div class="hsec-h"><h2>I volumi</h2><p>Ogni volume racconta un'era: scheda e novità di ogni set, carte più giocate, mazzi con le liste complete, rarità e tabella di tutte le carte.</p></div>
<div class="vols">{vols}</div></section>
<section class="hsec" id="biblioteca"><div class="hsec-h"><h2>La biblioteca dei PDF</h2><p>Le edizioni impaginate dei manuali, con copertina e indice. Si aprono in una nuova scheda.</p></div>
<div class="lib">{lib}</div></section>'''


def articolo(p, seq):
    i = seq.index(p)
    prev = seq[i - 1] if i > 0 else None; nxt = seq[i + 1] if i < len(seq) - 1 else None
    deck = p['tipo'] in ('deck', 'decks')
    meta = f'<div class="a-meta"><span>{E(p.get("uscita", ""))}</span><span>{E(p.get("carte", ""))}</span></div>' if p['tipo'] == 'set' else ''
    lead = f'<div class="a-lead">{p["_lead"]}</div>' if p.get('_lead') else ''
    tag = f'<p class="a-tag">{E(p["sottotitolo"])}</p>' if p.get('sottotitolo') else ''
    w1, w2 = ('Precedente', 'Successivo') if deck else ('Precedente', 'Successiva')
    pn = f'<a class="pn prev" href="#{prev["id"]}"><span>{w1}</span>{E(prev["titolo"])}</a>' if prev else '<span></span>'
    if nxt: pn += f'<a class="pn next" href="#{nxt["id"]}"><span>{w2}</span>{E(nxt["titolo"])}</a>'
    back = '<a class="back" href="#mazzi">← Tutti i mazzi</a>' if p['tipo'] == 'deck' else ''
    return f'''<article class="page k-{p["tipo"]}" id="p-{p["id"]}" data-id="{p["id"]}" style="--pc:{p["colore"]}">{back}
<header class="a-head"><p class="a-kick">{E(p.get("occhiello", ""))}</p><h1>{E(p["titolo"])}</h1>{tag}{meta}</header>
{lead}<div class="prose">{p["_html"]}</div><nav class="pnav">{pn}</nav></article>'''


def testo_puro(h, n=158):
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


def url_di(pid, pre):
    return (pre or './') if pid == 'home' else f'{pre}{pid}/'


def sistema_link(h, pre):
    """Trasforma i collegamenti interni "#id-pagina" in indirizzi veri."""
    def rep(m):
        attr, target = m.group(1), m.group(2)
        if target.startswith(('pdf/', 'img/')):
            return f'{attr}="{pre}{target}"'
        pid, _, frag = target.partition('#')
        if pid in TUTTI_ID:
            return f'{attr}="{url_di(pid, pre)}{("#" + frag) if frag else ""}"'
        if pid == 'biblioteca':
            return f'{attr}="{pre}#biblioteca"'
        avviso(f'collegamento interno a "#{target}" che non corrisponde a nessuna pagina')
        return m.group(0)
    return re.sub(r'(href|src)="#([^"]+)"', rep, h)


CSS_VER = hashlib.md5(((ROOT / 'motore/style.css').read_text(encoding='utf-8') + (ROOT / 'motore/app.js').read_text(encoding='utf-8')).encode()).hexdigest()[:8]


def documento(pid, titolo, desc, corpo, pre, cjson):
    full = CFG['titolo'] if pid == 'home' else f'{titolo} · {CFG["titolo"]}'
    url = CFG['indirizzo'].rstrip('/') + '/' + ('' if pid == 'home' else pid + '/')
    redir = ''
    if pid == 'home':
        redir = '<script>(function(){var h=location.hash.slice(1);if(h&&h!=="home"&&h!=="biblioteca"&&/^[a-z0-9-]+$/.test(h))location.replace(h+"/");})();</script>'
    return f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta property="og:title" content="{E(full)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{E(url)}"><meta property="og:locale" content="it_IT">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..600&display=swap">
<link rel="stylesheet" href="{pre}assets/style.css?v={CSS_VER}">
{redir}</head><body>
<div class="shell">
<header class="top"><a class="brand" href="{pre or './'}"><span class="bm" aria-hidden="true"></span>{E(CFG["titolo"])}</a>
<button class="menu" id="menuBtn" aria-expanded="false" aria-controls="side">Indice</button></header>
<aside class="side" id="side"><nav>{sistema_link(nav(pid), pre)}</nav></aside>
<main id="main">
{corpo}
<footer class="foot"><p>{CFG["pie_di_pagina"]}</p></footer>
</main></div>
<div class="pop" id="pop" role="dialog" aria-label="Anteprima della carta" hidden></div>
<script type="application/json" id="cardsdata">{cjson}</script>
<script src="{pre}assets/app.js?v={CSS_VER}"></script>
</body></html>
'''


def cards_json(usate):
    return json.dumps({c: compatta(c) for c in sorted(usate)}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def scrivi(rel, testo):
    p = DIST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(testo, encoding='utf-8')


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    # file statici
    for f in (ROOT / 'static').rglob('*'):
        if f.is_file():
            dest = DIST / f.relative_to(ROOT / 'static')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
    (DIST / 'assets').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'motore/style.css', DIST / 'assets/style.css')
    shutil.copy2(ROOT / 'motore/app.js', DIST / 'assets/app.js')

    # home
    usate = set()
    corpo = f'<article class="page home" id="p-home" data-id="home" style="--pc:#5b2a6e">{home_html()}</article>'
    scrivi('index.html', documento('home', CFG['titolo'], CFG['descrizione'].strip(), sistema_link(corpo, ''), '', cards_json(usate)))

    # pagine dei volumi e dei mazzi
    for seq in (PAGINE, DECKP):
        for p in seq:
            usate = set()
            art = articolo(p, seq)
            if not p.get('_nolink'):
                home_set = p['set_carte'] if p['tipo'] == 'set' else None
                art = collega_carte(art, era_index(p['set_carte']), home_set, usate)
            desc = p.get('_desc') or p.get('sottotitolo') or testo_puro(p.get('_lead') or p['_html'])
            scrivi(f'{p["id"]}/index.html', documento(p['id'], p['titolo'], testo_puro(desc), sistema_link(art, '../'), '../', cards_json(usate)))

    # 404, sitemap, robots
    nf = '<article class="page" style="--pc:#5b2a6e"><header class="a-head"><p class="a-kick">Errore 404</p><h1>Pagina non trovata</h1></header><div class="prose"><p>La pagina che cerchi non esiste o è stata spostata. <a href="#home">Torna all\'inizio</a> oppure usa l\'indice.</p></div></article>'
    base = CFG['indirizzo'].rstrip('/')
    pre404 = base + '/'
    scrivi('404.html', documento('404', 'Pagina non trovata', CFG['descrizione'].strip(), sistema_link(nf, pre404), pre404, '{}'))
    urls = [base + '/'] + [f'{base}/{p["id"]}/' for p in TUTTE]
    scrivi('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{E(u)}</loc></url>\n' for u in urls) + '</urlset>\n')
    scrivi('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n')
    scrivi('.nojekyll', '')
    print(f'Sito generato in dist/: {len(PAGINE)} pagine dei volumi, {len(MAZZI)} mazzi.')
    if ERRORI:
        print(f'{len(ERRORI)} avvisi da controllare (vedi sopra).')


if __name__ == '__main__':
    main()
