# Costruisce il sito cifrato di Victor Trading da /home/claude/dashboard.html
# Uso: python3 build_site.py PASSWORD
import sys, os, base64, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from PIL import Image, ImageDraw, ImageFont

PWD = sys.argv[1].encode()
SRC = '/home/claude/dashboard.html'
OUT = '/home/claude/victor-trading'
ITER = 310000

body = open(SRC, encoding='utf-8').read()
doc = ('<!doctype html><html lang="it"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
       '<meta name="theme-color" content="#0a0e1a">'
       '<link rel="apple-touch-icon" href="icon.png">'
       '</head><body>' + body + '</body></html>')

salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(PWD)
ct = AESGCM(key).encrypt(iv, doc.encode('utf-8'), None)
b64 = lambda b: base64.b64encode(b).decode()
payload = json.dumps({'s': b64(salt), 'i': b64(iv), 'c': b64(ct), 'n': ITER})

page = r'''<!doctype html>
<html lang="it"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Victor Trading</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Victor Trading">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0a0e1a">
<meta name="robots" content="noindex,nofollow">
<link rel="apple-touch-icon" href="icon.png">
<link rel="icon" href="icon.png">
<style>
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: radial-gradient(circle at 30% 10%, rgba(0,255,136,.16), transparent 50%), #0a0e1a; color: #ededf0; font-family: -apple-system, system-ui, sans-serif; padding: 24px; }
.box { width: 100%; max-width: 360px; text-align: center; }
.logo { width: 64px; height: 64px; border-radius: 16px; background: #00ff88; color: #000; display: grid; place-items: center; font: 800 30px ui-monospace, Menlo, monospace; margin: 0 auto 18px; box-shadow: 0 0 30px rgba(0,255,136,.35); }
h1 { font: 600 15px ui-monospace, Menlo, monospace; letter-spacing: .22em; margin: 0 0 6px; }
p { color: #8a96b0; font-size: 14px; margin: 0 0 22px; }
input[type=password] { width: 100%; padding: 15px 16px; border-radius: 12px; border: 1px solid #34415f; background: #0f1528; color: #fff; font-size: 17px; outline: none; }
input[type=password]:focus { border-color: #00ff88; }
button { width: 100%; margin-top: 12px; padding: 15px; border: 0; border-radius: 12px; background: #00ff88; color: #000; font-weight: 700; font-size: 16px; cursor: pointer; }
button:active { transform: scale(.98); }
label { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 14px; color: #8a96b0; font-size: 13px; }
.err { color: #ef5a6f; font-size: 14px; min-height: 20px; margin-top: 12px; }
</style></head>
<body>
<form class="box" id="f" autocomplete="on">
  <div class="logo">V</div>
  <h1>VICTOR · TRADING</h1>
  <p>Inserisci la password per aprire la dashboard</p>
  <input type="text" name="username" value="victor" autocomplete="username" hidden>
  <input type="password" id="pw" autocomplete="current-password" placeholder="Password" autofocus>
  <button type="submit" id="go">Apri</button>
  <label><input type="checkbox" id="rem" checked> Ricordami su questo telefono</label>
  <div class="err" id="err"></div>
</form>
<script>
const D = __PAYLOAD__;
const u8 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
async function keyFromPw(pw) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({name: 'PBKDF2', salt: u8(D.s), iterations: D.n, hash: 'SHA-256'}, base, {name: 'AES-GCM', length: 256}, true, ['decrypt']);
}
async function openWith(key) {
  const pt = await crypto.subtle.decrypt({name: 'AES-GCM', iv: u8(D.i)}, key, u8(D.c));
  const html = new TextDecoder().decode(pt);
  document.open(); document.write(html); document.close();
}
// Chiave ricordata (valida finché la password non cambia)
(async () => {
  try {
    const saved = localStorage.getItem('vt-key-' + D.s);
    if (saved) { const k = await crypto.subtle.importKey('raw', u8(saved), 'AES-GCM', false, ['decrypt']); await openWith(k); }
  } catch (e) { try { localStorage.removeItem('vt-key-' + D.s); } catch (_) {} }
})();
document.getElementById('f').addEventListener('submit', async e => {
  e.preventDefault();
  const err = document.getElementById('err'), btn = document.getElementById('go');
  err.textContent = ''; btn.textContent = 'Apro…'; btn.disabled = true;
  try {
    const key = await keyFromPw(document.getElementById('pw').value);
    if (document.getElementById('rem').checked) {
      try { localStorage.setItem('vt-key-' + D.s, b64(await crypto.subtle.exportKey('raw', key))); } catch (_) {}
    }
    await openWith(key);
  } catch (e2) {
    err.textContent = 'Password sbagliata, riprova.'; btn.textContent = 'Apri'; btn.disabled = false;
  }
});
</script>
</body></html>
'''.replace('__PAYLOAD__', payload)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)

# Icona per la schermata Home
im = Image.new('RGB', (180, 180), (10, 14, 26)); d = ImageDraw.Draw(im)
d.rounded_rectangle([22, 22, 158, 158], 30, fill=(0, 255, 136))
try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 92)
except Exception: f = ImageFont.load_default()
d.text((90, 92), 'V', font=f, fill=(0, 0, 0), anchor='mm')
im.save(os.path.join(OUT, 'icon.png'))
print('ok', len(page))
