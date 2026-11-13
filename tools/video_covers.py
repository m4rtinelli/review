#!/usr/bin/env python3
"""Gera as capas dos vídeos de um mês, recortando a imagem de cada slide no lugar onde o vídeo está.

uso: video_covers.py <presentation.json> <chave-do-mês> <id-da-apresentação | pasta-com-imagens>
Com o id, baixa cada slide por docs.google.com/.../export/jpeg (só funciona se o deck estiver
compartilhado por link). Com uma pasta, usa <pasta>/<objectId do slide>.png|jpg já baixados.
Grava as folhas sp/<mês>-vN.jpg e o campo `vcs` (id do vídeo -> recorte) em data/posts-<mês>.json.
"""
import json, sys, os, subprocess, tempfile, io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
src, key, where = sys.argv[1:4]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(src)); d = d.get('content', d)
W = d['pageSize']['width']['magnitude']; H = d['pageSize']['height']['magnitude']
CW, CH, COLS, ROWS = 405, 720, 4, 4
def mat(e):
    t = e.get('transform', {}); return (t.get('scaleX',1), t.get('shearX',0), t.get('translateX',0), t.get('shearY',0), t.get('scaleY',1), t.get('translateY',0))
def mul(a, b): return (a[0]*b[0]+a[1]*b[3], a[0]*b[1]+a[1]*b[4], a[0]*b[2]+a[1]*b[5]+a[2], a[3]*b[0]+a[4]*b[3], a[3]*b[1]+a[4]*b[4], a[3]*b[2]+a[4]*b[5]+a[5])
def box(e, m):
    s = e.get('size', {}); w = s.get('width',{}).get('magnitude',0); h = s.get('height',{}).get('magnitude',0)
    xs = [m[0]*x+m[1]*y+m[2] for x in (0,w) for y in (0,h)]; ys = [m[3]*x+m[4]*y+m[5] for x in (0,w) for y in (0,h)]
    return min(xs)/W, min(ys)/H, max(xs)/W, max(ys)/H
vids = {}  # página -> [(id, caixa)]
for s in d['slides']:
    def walk(e, pm):
        m = mul(pm, mat(e))
        if 'video' in e and e['video'].get('id') and e['video'].get('source') == 'DRIVE': vids.setdefault(s['objectId'], []).append((e['video']['id'], box(e, m)))
        for c in e.get('elementGroup', {}).get('children', []): walk(c, m)
    for e in s.get('pageElements', []): walk(e, (1,0,0,0,1,0))
def page(pid):
    if os.path.isdir(where):
        for ext in ('png','jpg','jpeg'):
            f = f'{where}/{pid}.{ext}'
            if os.path.exists(f): return pid, Image.open(f).convert('RGB')
        return pid, None
    u = f'https://docs.google.com/presentation/d/{where}/export/jpeg?id={where}&pageid={pid}'
    for _ in range(3):
        r = subprocess.run(['curl','-sS','-f','-L','--max-time','90',u], capture_output=True)
        if r.returncode == 0:
            try: return pid, Image.open(io.BytesIO(r.stdout)).convert('RGB')
            except Exception: pass
    return pid, None
with ThreadPoolExecutor(6) as ex: pages = dict(ex.map(page, vids))
cell = {}; sheets = []; k = 0
for pid, lst in vids.items():
    im = pages.get(pid)
    if im is None: continue
    for vid, (x0, y0, x1, y1) in lst:
        if vid in cell: continue
        b = [max(0, int(x0*im.width)), max(0, int(y0*im.height)), min(im.width, int(x1*im.width)), min(im.height, int(y1*im.height))]
        if b[2]-b[0] < 40 or b[3]-b[1] < 40: continue
        c = im.crop(b); c.thumbnail((CW, CH))
        if k % 16 == 0: sheets.append(Image.new('RGB', (CW*COLS, CH*ROWS), 'white'))
        col, row = (k % 16) % COLS, (k % 16) // COLS
        sheets[-1].paste(c, (col*CW, row*CH)); cell[vid] = [f'v{len(sheets)-1}', col, row, c.width, c.height]; k += 1
for f in os.listdir(f'{ROOT}/sp'):
    if f.startswith(key + '-v'): os.remove(f'{ROOT}/sp/{f}')
for i, s in enumerate(sheets): s.save(f'{ROOT}/sp/{key}-v{i}.jpg', quality=78, optimize=True)
P = json.load(open(f'{ROOT}/data/posts-{key}.json')); n = 0
for p in P:
    p['vcs'] = {v: cell[v] for v in p.get('vids', []) if v in cell}; n += len(p['vcs'])
json.dump(P, open(f'{ROOT}/data/posts-{key}.json', 'w'), ensure_ascii=False, indent=1)
size = next((im.size for im in pages.values() if im), None)
print(key, 'slides com vídeo', len(vids), 'baixados', sum(1 for v in pages.values() if v), 'tamanho', size, 'capas', k, 'em posts', n, 'de', sum(len(p.get('vids', [])) for p in P))
