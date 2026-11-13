#!/usr/bin/env python3
"""Importa um deck "CRONOGRAMA EVEREST | <MÊS>" (JSON da API do Google Slides) para o app.

uso: import_month.py <presentation.json> <chave-do-mês>
Gera data/posts-<chave>.json e as folhas de imagens sp/<chave>-N.jpg (16 peças por folha).
Os links das imagens no JSON expiram em cerca de 30 minutos: rode logo depois de baixar o JSON.
"""
import json, re, sys, os, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

src, key = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(src)); d = d.get('content', d)
W = d['pageSize']['width']['magnitude']; H = d['pageSize']['height']['magnitude']
STAMPS = {'APROVADO':'aprovado','AGUARDANDO INSUMOS':'insumos','AJUSTE':'ajuste','AJUSTES':'ajuste','AGENDADO/POSTADO':'postado','AGENDADO':'postado','POSTADO':'postado','EM APROVAÇÃO':'em_aprovacao'}
CW, CH, COLS, ROWS = 405, 720, 4, 4

def mat(e):
    t = e.get('transform', {})
    return (t.get('scaleX',1), t.get('shearX',0), t.get('translateX',0), t.get('shearY',0), t.get('scaleY',1), t.get('translateY',0))
def mul(a, b):
    return (a[0]*b[0]+a[1]*b[3], a[0]*b[1]+a[1]*b[4], a[0]*b[2]+a[1]*b[5]+a[2], a[3]*b[0]+a[4]*b[3], a[3]*b[1]+a[4]*b[4], a[3]*b[2]+a[4]*b[5]+a[5])
def box(e, m):
    s = e.get('size', {}); w = s.get('width',{}).get('magnitude',0); h = s.get('height',{}).get('magnitude',0)
    xs = [m[0]*x+m[1]*y+m[2] for x in (0,w) for y in (0,h)]; ys = [m[3]*x+m[4]*y+m[5] for x in (0,w) for y in (0,h)]
    return min(xs)/W, min(ys)/H, (max(xs)-min(xs))/W, (max(ys)-min(ys))/H
def text(e):
    return ''.join(x.get('textRun',{}).get('content','') for x in e.get('shape',{}).get('text',{}).get('textElements',[])).replace('\x0b','\n').strip()
def fmt(f):
    f = f.lower()
    if 'reel' in f or 'vídeo' in f or 'video' in f: return 'reels'
    if 'stor' in f: return 'stories'
    if 'carro' in f: return 'carrossel'
    if 'card' in f or 'feed' in f or 'post' in f or 'estático' in f: return 'card'
    return 'tbd'

rows = []
for i, s in enumerate(d['slides']):
    o = {'n':i+1, 'status':None, 'animar':False, 'texts':[], 'imgs':[], 'vids':[], 'day':None, 'fmt':None, 'dated':False}
    def walk(e, pm):
        m = mul(pm, mat(e)); x, y, w, h = box(e, m)
        if 'shape' in e:
            t = text(e); up = t.upper()
            if up in STAMPS or up == 'A ANIMAR':
                if 0 <= x + w/2 <= 1 and 0 <= y + h/2 <= 1:
                    if up == 'A ANIMAR': o['animar'] = True
                    else: o['status'] = STAMPS[up]
            elif t:
                mm = re.match(r'^\s*(\d{1,2}|xx|XX)\s*[/.]\s*(\d{1,2}|xx)\s*[|·\-–:]\s*([^\n]+)', t)
                if mm and not o['dated']:
                    o['dated'] = True; o['day'] = int(mm.group(1)) if mm.group(1).isdigit() else None; o['fmt'] = fmt(mm.group(3))
                    rest = t[mm.end():].strip()
                    if rest: o['texts'].append(rest)
                else: o['texts'].append(t)
        if 'image' in e and e['image'].get('contentUrl') and w >= .07 and h >= .2 and 0 <= x + w/2 <= 1 and 0 <= y + h/2 <= 1:
            o['imgs'].append((x, e['image']['contentUrl']))
        if 'video' in e and e['video'].get('id') and e['video'].get('source') == 'DRIVE': o['vids'].append((x, e['video']['id']))
        for c in e.get('elementGroup', {}).get('children', []): walk(c, m)
    for e in s.get('pageElements', []): walk(e, (1,0,0,0,1,0))
    if o['dated']: rows.append(o)

posts = []
for r in rows:
    leg, ins, tx, refs = [], [], [], []
    for t in r['texts']:
        if re.match(r'^(Legenda:?|everestoficial_)', t, re.I): leg.append(re.sub(r'^(Legenda:?|everestoficial_)\s*', '', t, flags=re.I).strip())
        elif re.match(r'^Insight\s*ref', t, re.I): refs.append(re.sub(r'^Insight\s*ref:?\s*', '', t, flags=re.I).strip())
        elif re.match(r'^(Insight|Card \d|Texto:|Roteiro)', t, re.I): ins.append(re.sub(r'^Insight:?\s*', '', t, flags=re.I).strip())
        elif re.match(r'^Ref', t, re.I):
            u = re.sub(r'^Refs?(er[êe]ncias?)?:?\s*', '', t, flags=re.I).strip()
            if u: refs.append(u)
        elif re.fullmatch(r'[\dxX\s]+', t): pass
        else: tx.append(t)
    leg = [l for l in leg if l and not re.fullmatch(r'[xX\s]+', l)]
    last = posts[-1] if posts else None
    if last and r['day'] and last['day'] == r['day'] and last['fmt'] == r['fmt'] and last['_n'] == r['n']-1 and r['fmt'] in ('carrossel','tbd'): p = last
    else:
        p = {'id':f"{key}-p{r['n']}", 'month':key, 'day':r['day'], 'fmt':r['fmt'], 'status':None, 'animar':False, 'L':[], 'I':[], 'T':[], 'R':[], 'urls':[], 'vids':[]}
        posts.append(p)
    p['_n'] = r['n']; p['animar'] = p['animar'] or r['animar']; p['status'] = p['status'] or r['status']
    p['L'] += leg; p['I'] += ins; p['T'] += tx; p['R'] += refs
    for _, u in sorted(r['imgs']):
        if u not in p['urls']: p['urls'].append(u)
    for _, v in sorted(r['vids']):
        if v not in p['vids']: p['vids'].append(v)

# imagens: baixa reduzidas e monta as folhas
tmp = tempfile.mkdtemp()
allu = []
for p in posts:
    p['urls'] = p['urls'][:12]
    for u in p['urls']:
        if u not in allu: allu.append(u)
def get(a):
    i, u = a; f = f'{tmp}/{i}'
    u2 = re.sub(r'=s\d+(\?|$)', r'=s720\1', u)
    for _ in range(3):
        if subprocess.run(['curl','-sS','-f','-L','--max-time','60','-o',f,u2], capture_output=True).returncode == 0: break
    try:
        im = Image.open(f); im.load()
        if im.mode in ('RGBA','LA','P'):
            im = im.convert('RGBA'); bg = Image.new('RGB', im.size, 'white'); bg.paste(im, mask=im.split()[3]); im = bg
        else: im = im.convert('RGB')
        im.thumbnail((CW, CH)); return i, im
    except Exception: return i, None
with ThreadPoolExecutor(8) as ex: got = dict(ex.map(get, enumerate(allu)))
cell = {}; sheets = []; k = 0
for i, u in enumerate(allu):
    im = got.get(i)
    if im is None or im.width < 60 or im.height < 60: continue
    if k % (COLS*ROWS) == 0: sheets.append(Image.new('RGB', (CW*COLS, CH*ROWS), 'white'))
    c, r = (k % (COLS*ROWS)) % COLS, (k % (COLS*ROWS)) // COLS
    sheets[-1].paste(im, (c*CW, r*CH)); cell[u] = [len(sheets)-1, c, r, im.width, im.height]; k += 1
for f in os.listdir(f'{ROOT}/sp'):
    if f.startswith(key + '-'): os.remove(f'{ROOT}/sp/{f}')
for i, s in enumerate(sheets): s.save(f'{ROOT}/sp/{key}-{i}.jpg', quality=76, optimize=True)

FL = {'reels':'Reels','stories':'Stories','carrossel':'Carrossel','card':'Card','tbd':'Post'}
out = []
for p in posts:
    I = '\n\n'.join(p['I']); L = '\n\n'.join(p['L'])
    first = lambda s: next((l.strip() for l in s.split('\n') if l.strip() and not re.match(r'^(Roteiro|http|Ref|Legenda|DAs?\b|DA:)', l.strip(), re.I)), '')
    cand = [t for t in p['T'] if len(t) < 50 and not re.fullmatch(r'[xX\s]+', t)]
    title = (first(I) if I else '') or (cand[0] if cand and p['fmt'] != 'stories' else '') or first(L) or (cand[0] if cand else '')
    title = title.replace('\n', ' ')
    if len(title) > 70: title = title[:67].rsplit(' ', 1)[0] + '…'
    if not title: title = f"{FL[p['fmt']]} de {p['day']:02d}" if p['day'] else FL[p['fmt']] + ' sem data'
    sp = [cell[u] for u in p['urls'] if u in cell]
    T = list(dict.fromkeys(t for t in p['T'] if not re.fullmatch(r'[xX\s]+', t)))
    out.append({'id':p['id'], 'month':key, 'day':p['day'], 'fmt':p['fmt'], 'status':p['status'] or 'none', 'animar':p['animar'],
                'frames':0 if (sp or p['vids']) else (1 if p['fmt'] == 'reels' else 0), 'vertical':p['fmt'] in ('reels','stories'),
                'title':title, 'legenda':L, 'insight':I, 'textos':'\n'.join(T), 'refs':'\n'.join(p['R']), 'imgs':[], 'sp':sp, 'vids':p['vids'], 'files':[]})
out.sort(key=lambda p: (p['day'] or 99))
json.dump(out, open(f'{ROOT}/data/posts-{key}.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(key, 'slides', len(d['slides']), 'posts', len(out), 'sem data', sum(1 for p in out if not p['day']), 'imgs', k, '/', len(allu), 'folhas', len(sheets), 'vids', sum(len(p['vids']) for p in out))
print(' status', dict(Counter(p['status'] for p in out)), 'fmt', dict(Counter(p['fmt'] for p in out)))
