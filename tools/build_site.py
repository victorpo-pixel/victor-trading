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
doc = ('<!doctype html><html lang="it" class="vt-site"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
       '<meta name="theme-color" content="#0a0e1a">'
       '<link rel="apple-touch-icon" href="icon.png">'
       '</head><body>' + body + '</body></html>')

SALT_FILE = os.path.join(OUT, 'tools', 'salt.b64')
os.makedirs(os.path.dirname(SALT_FILE), exist_ok=True)
if os.path.exists(SALT_FILE):
    salt = base64.b64decode(open(SALT_FILE).read().strip())
else:
    salt = os.urandom(16); open(SALT_FILE, 'w').write(base64.b64encode(salt).decode())
iv = os.urandom(12)
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
<style id="login-css">
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: radial-gradient(circle at 30% 10%, rgba(227,179,65,.16), transparent 50%), #0a0e1a; color: #ededf0; font-family: -apple-system, system-ui, sans-serif; padding: 24px; }
.box { width: 100%; max-width: 360px; text-align: center; }
.logo { display: block; width: 88px; height: 88px; border-radius: 22px; background: #e3b341; color: #000; display: grid; place-items: center; font: 800 30px ui-monospace, Menlo, monospace; margin: 0 auto 18px; box-shadow: 0 0 30px rgba(227,179,65,.35); }
h1 { font: 600 15px ui-monospace, Menlo, monospace; letter-spacing: .22em; margin: 0 0 6px; }
p { color: #8a96b0; font-size: 14px; margin: 0 0 22px; }
input[type=password] { width: 100%; padding: 15px 16px; border-radius: 12px; border: 1px solid #34415f; background: #0f1528; color: #fff; font-size: 17px; outline: none; }
input[type=password]:focus { border-color: #e3b341; }
button { width: 100%; margin-top: 12px; padding: 15px; border: 0; border-radius: 12px; background: #e3b341; color: #000; font-weight: 700; font-size: 16px; cursor: pointer; }
button:active { transform: scale(.98); }
label { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 14px; color: #8a96b0; font-size: 13px; }
.err { color: #ef5a6f; font-size: 14px; min-height: 20px; margin-top: 12px; }
</style></head>
<body>
<form class="box" id="f" autocomplete="on" style="visibility:hidden">
  <img class="logo" src="icon-512.png" alt="Victor Trading">
  <h1>VICTOR · TRADING</h1>
  <p>Inserisci la password per aprire la dashboard</p>
  <input type="text" name="username" value="victor" autocomplete="username" hidden>
  <input type="password" id="pw" autocomplete="current-password" placeholder="Password" autofocus>
  <button type="submit" id="go">Apri</button>
  <label><input type="checkbox" id="rem" checked> Ricordami su questo telefono</label>
  <div class="err" id="err"></div>
</form>
<script>
(function () {
const D = __PAYLOAD__;
const KEY_NAME = 'vt-key-' + D.s;
const u8 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
let opened = false;
async function keyFromPw(pw) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({name: 'PBKDF2', salt: u8(D.s), iterations: D.n, hash: 'SHA-256'}, base, {name: 'AES-GCM', length: 256}, true, ['decrypt']);
}
async function decrypt(key) {
  const pt = await crypto.subtle.decrypt({name: 'AES-GCM', iv: u8(D.i)}, key, u8(D.c));
  return new TextDecoder().decode(pt);
}
// Apre la dashboard come pagina normale (niente iframe: lo scorrimento funziona sempre)
async function show(html) {
  if (opened) return; opened = true;
  const doc = new DOMParser().parseFromString(html, 'text/html');
  document.getElementById('login-css').remove();
  document.documentElement.className = doc.documentElement.className;
  document.title = 'Victor Trading';
  const scripts = [];
  for (const el of [...doc.head.children]) {
    if (el.tagName === 'SCRIPT') scripts.push(el);
    else if (el.tagName === 'STYLE' || (el.tagName === 'LINK' && el.rel === 'stylesheet')) document.head.appendChild(document.importNode(el, true));
  }
  document.body.innerHTML = '';
  for (const n of [...doc.body.childNodes]) {
    if (n.nodeType === 1 && n.tagName === 'SCRIPT') { scripts.push(n); continue; }
    document.body.appendChild(document.importNode(n, true));
  }
  for (const old of scripts) {
    const sc = document.createElement('script');
    for (const a of old.attributes) sc.setAttribute(a.name, a.value);
    if (old.src) {
      await new Promise(res => { sc.onload = sc.onerror = res; document.head.appendChild(sc); });
    } else {
      sc.textContent = old.textContent; document.body.appendChild(sc);
    }
  }
  window.scrollTo(0, 0);
}
async function tryRemembered() {
  let saved = null;
  try { saved = localStorage.getItem(KEY_NAME); } catch (_) {}
  if (!saved) { document.getElementById('f').style.visibility = 'visible'; return; }
  try {
    const k = await crypto.subtle.importKey('raw', u8(saved), 'AES-GCM', false, ['decrypt']);
    await show(await decrypt(k));
  } catch (e) {
    try { localStorage.removeItem(KEY_NAME); } catch (_) {}
    if (!opened) document.getElementById('f').style.visibility = 'visible';
  }
}
document.getElementById('f').addEventListener('submit', async e => {
  e.preventDefault();
  if (opened) return;
  const err = document.getElementById('err'), btn = document.getElementById('go');
  err.textContent = ''; btn.textContent = 'Apro…'; btn.disabled = true;
  try {
    const key = await keyFromPw(document.getElementById('pw').value);
    const html = await decrypt(key);
    if (document.getElementById('rem').checked) {
      try { localStorage.setItem(KEY_NAME, b64(await crypto.subtle.exportKey('raw', key))); } catch (_) {}
    }
    await show(html);
  } catch (e2) {
    err.textContent = 'Password sbagliata, riprova.'; btn.textContent = 'Apri'; btn.disabled = false;
  }
});
tryRemembered();
})();
</script>
</body></html>
'''.replace('__PAYLOAD__', payload)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)

# Icona per la schermata Home (disegno in tools/icon-1024.png)
src_icon = Image.open(os.path.join(OUT, 'tools', 'icon-1024.png')).convert('RGB')
src_icon.resize((180, 180), Image.LANCZOS).save(os.path.join(OUT, 'icon.png'))
src_icon.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, 'icon-512.png'))
print('ok', len(page))
