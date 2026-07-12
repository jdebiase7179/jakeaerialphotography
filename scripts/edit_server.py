#!/usr/bin/env python3
"""Local edit mode for the site.

Run it, open the URL it prints, then:
  • Click any text on the page, type to change it, hit "Save changes".
  • Drag an image from your computer onto the big hero picture, the portrait
    spot, or any gallery tile to drop your own photo in.

Text edits are written straight back into index.html. Dropped photos are saved
into the right place (assets/img for hero/portrait, photos/<category>/ for the
gallery) and the gallery rebuilds itself. Nothing is deployed until you commit +
push — this only touches your local files.

    python3 scripts/edit_server.py
"""
import http.server
import socketserver
import json
import re
import os
import io
import shutil
import subprocess
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
SITE = os.path.join(ROOT, "_site")
IMG_DIR = os.path.join(ROOT, "assets", "img")
PHOTOS = os.path.join(ROOT, "photos")
BUILD = os.path.join(ROOT, "scripts", "build_gallery.py")
PORT = int(os.environ.get("PORT", 8010))

HERO_EDGE = 2400      # long edge for the big hero image
PORTRAIT_EDGE = 1600  # long edge for the portrait
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff",
              ".mp4", ".mov", ".webm", ".m4v"}

# Injected into the served page (never written to disk). Makes every element
# tagged data-edit="..." editable, and turns the hero/portrait/gallery into
# drop zones for images.
EDITOR = """
<style>
  .reveal{opacity:1 !important;transform:none !important;}
  [data-edit]{outline:1px dashed transparent;transition:outline-color .15s;cursor:text;}
  [data-edit]:hover{outline-color:rgba(10,102,232,.55);}
  [data-edit]:focus{outline:2px solid #0A66E8;outline-offset:3px;}
  .drop-zone{position:relative;}
  .drop-hot{outline:3px dashed #0A66E8 !important;outline-offset:-3px;}
  .drop-zone::after{content:"⬇ Drop photo";position:absolute;inset:0;
    display:none;align-items:center;justify-content:center;text-align:center;
    background:rgba(10,102,232,.75);color:#fff;font:600 15px/1.3 Inter,sans-serif;
    border-radius:inherit;pointer-events:none;z-index:5;padding:8px;}
  .drop-zone.drop-hot::after{display:flex;}
  #edit-bar{position:fixed;left:0;right:0;bottom:0;z-index:99999;display:flex;
    gap:16px;align-items:center;justify-content:center;padding:12px 16px;
    background:#0A66E8;color:#fff;font:600 14px/1.3 Inter,system-ui,sans-serif;
    box-shadow:0 -6px 24px rgba(0,0,0,.18);flex-wrap:wrap;text-align:center;}
  #edit-bar button{font:inherit;padding:10px 22px;border:0;border-radius:9px;
    background:#fff;color:#0A66E8;cursor:pointer;}
  #edit-bar button:disabled{opacity:.5;cursor:default;}
  #edit-msg{font-weight:500;opacity:.95;}
  body{padding-bottom:64px !important;}
</style>
<div id="edit-bar">
  <span id="edit-msg">✏️ Click text to edit · 🖼️ Drag an image onto a photo to replace it</span>
  <button id="edit-save" disabled>Save text changes</button>
</div>
<script>
(function(){
  var save=document.getElementById('edit-save'), msg=document.getElementById('edit-msg');

  /* ---- text editing ---- */
  var nodes=document.querySelectorAll('[data-edit]');
  nodes.forEach(function(el){
    el.setAttribute('contenteditable','true');
    el.setAttribute('spellcheck','true');
    el.addEventListener('input',function(){save.disabled=false;msg.textContent='Unsaved text changes';});
    if(el.tagName==='A')el.addEventListener('click',function(e){e.preventDefault();});
  });
  save.addEventListener('click',function(){
    var data={};
    nodes.forEach(function(el){data[el.getAttribute('data-edit')]=el.innerHTML;});
    save.disabled=true;msg.textContent='Saving…';
    fetch('/__save',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)}).then(function(r){return r.json();})
      .then(function(j){msg.textContent=j.ok?'Saved ✓  (index.html updated)':'Error: '+j.error;
        if(!j.ok)save.disabled=false;})
      .catch(function(e){msg.textContent='Error: '+e;save.disabled=false;});
  });

  /* ---- image drag + drop ---- */
  function upload(file, headers, done){
    if(!file){return;}
    if(!/^image\\/|^video\\//.test(file.type||'') && !/\\.(jpe?g|png|webp|heic|tiff?|mp4|mov|webm|m4v)$/i.test(file.name)){
      msg.textContent='That doesn\\'t look like an image or video file.';return;
    }
    msg.textContent='Uploading '+file.name+' …';
    var h=Object.assign({'Content-Type':file.type||'application/octet-stream'},headers);
    fetch('/__upload',{method:'POST',headers:h,body:file})
      .then(function(r){return r.json();})
      .then(function(j){if(j.ok){msg.textContent=j.msg||'Photo added ✓';done&&done(j);}
        else{msg.textContent='Error: '+j.error;}})
      .catch(function(e){msg.textContent='Error: '+e;});
  }
  function zone(el){ if(el){el.classList.add('drop-zone');} return el; }
  function wire(el, handler){
    if(!el)return;
    el.addEventListener('dragover',function(e){e.preventDefault();el.classList.add('drop-hot');});
    el.addEventListener('dragleave',function(e){if(e.target===el)el.classList.remove('drop-hot');});
    el.addEventListener('drop',function(e){e.preventDefault();el.classList.remove('drop-hot');
      handler(e.dataTransfer.files[0]);});
  }

  var hero=document.getElementById('hero-img');
  wire(zone(hero&&hero.parentElement),function(f){
    upload(f,{'X-Target':'hero'},function(){
      hero.removeAttribute('data-missing');hero.src='assets/img/hero.jpg?t='+Date.now();});
  });

  var por=document.getElementById('portrait-img');
  wire(zone(por&&por.parentElement),function(f){
    upload(f,{'X-Target':'portrait'},function(){
      por.removeAttribute('data-missing');por.src='assets/img/portrait.jpg?t='+Date.now();});
  });

  /* gallery tiles are generated by app.js — use event delegation */
  var gal=document.getElementById('gallery');
  if(gal){
    gal.addEventListener('dragover',function(e){var fig=e.target.closest('figure');
      if(fig){e.preventDefault();fig.classList.add('drop-zone','drop-hot');}});
    gal.addEventListener('dragleave',function(e){var fig=e.target.closest('figure');
      if(fig)fig.classList.remove('drop-hot');});
    gal.addEventListener('drop',function(e){var fig=e.target.closest('figure');if(!fig)return;
      e.preventDefault();fig.classList.remove('drop-hot');
      var cat=fig.dataset.category||'aerial';
      upload(e.dataTransfer.files[0],{'X-Target':'photo','X-Category':cat,
        'X-Filename':encodeURIComponent((e.dataTransfer.files[0]||{}).name||'photo')},function(){
        msg.textContent='Added to "'+cat+'" — rebuilding gallery…';
        if(window.loadGallery)window.loadGallery();else location.reload();});
    });
  }
})();
</script>
"""


# ---------------------------------------------------------------------------
# text edits -> index.html
# ---------------------------------------------------------------------------
def apply_edits(edits):
    with open(INDEX, encoding="utf-8") as f:
        src = f.read()
    for eid, new_html in edits.items():
        pat = re.compile(
            r'(<([a-zA-Z0-9]+)\b[^>]*\bdata-edit="' + re.escape(eid) + r'"[^>]*>)(.*?)(</\2>)',
            re.DOTALL,
        )
        src, n = pat.subn(lambda m: m.group(1) + new_html + m.group(4), src, count=1)
        if n == 0:
            raise ValueError('could not find element data-edit="%s"' % eid)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(src)


# ---------------------------------------------------------------------------
# image uploads
# ---------------------------------------------------------------------------
def save_fixed_image(raw, dest_path, long_edge):
    """Downscale/normalize a hero or portrait image and save it as JPEG."""
    from PIL import Image, ImageOps
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
    im = Image.open(io.BytesIO(raw))
    im = ImageOps.exif_transpose(im)
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((long_edge, long_edge))
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    im.save(dest_path, "JPEG", quality=85, optimize=True, progressive=True)


def safe_name(name):
    name = os.path.basename(unquote(name or "photo"))
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "photo"
    if not os.path.splitext(name)[1]:
        name += ".jpg"
    return name


def unique_path(directory, name):
    stem, ext = os.path.splitext(name)
    candidate, i = name, 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = "%s-%d%s" % (stem, i, ext)
        i += 1
    return os.path.join(directory, candidate)


def run_build():
    subprocess.run([sys.executable, BUILD], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def handle_upload(target, raw, category=None, filename=None):
    if target == "hero":
        save_fixed_image(raw, os.path.join(IMG_DIR, "hero.jpg"), HERO_EDGE)
        return "Hero photo updated ✓"
    if target == "portrait":
        save_fixed_image(raw, os.path.join(IMG_DIR, "portrait.jpg"), PORTRAIT_EDGE)
        return "Portrait updated ✓"
    if target == "photo":
        category = re.sub(r"[^a-z0-9-]+", "", (category or "aerial").lower()) or "aerial"
        name = safe_name(filename)
        ext = os.path.splitext(name)[1].lower()
        if ext not in PHOTO_EXTS:
            raise ValueError("unsupported file type: %s" % ext)
        cat_dir = os.path.join(PHOTOS, category)
        os.makedirs(cat_dir, exist_ok=True)
        dest = unique_path(cat_dir, name)
        with open(dest, "wb") as f:
            f.write(raw)
        run_build()  # regenerate _site/assets/gallery.json + resized photos
        return "Added %s to %s ✓" % (os.path.basename(dest), category)
    raise ValueError("unknown upload target: %s" % target)


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def translate_path(self, path):
        # Serve freshly-built gallery data/photos from _site so dropped photos
        # show up immediately, while everything else comes from the source tree.
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/assets/gallery.json" or clean.startswith("/assets/gallery/"):
            built = os.path.join(SITE, clean.lstrip("/"))
            if os.path.exists(built):
                return built
        return super().translate_path(path)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            with open(INDEX, encoding="utf-8") as f:
                doc = f.read()
            doc = doc.replace("</body>", EDITOR + "\n</body>", 1)
            body = doc.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def end_headers(self):
        # never cache gallery data during editing
        if self.path.split("?")[0].startswith("/assets/gallery"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            if self.path == "/__save":
                apply_edits(json.loads(raw or b"{}"))
                out = {"ok": True}
            elif self.path == "/__upload":
                msg = handle_upload(
                    self.headers.get("X-Target", ""),
                    raw,
                    self.headers.get("X-Category"),
                    self.headers.get("X-Filename"),
                )
                out = {"ok": True, "msg": msg}
            else:
                self.send_error(404)
                return
        except Exception as e:  # noqa: BLE001 - surface any error to the browser
            out = {"ok": False, "error": str(e)}
        body = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("\n  Edit mode is live:  http://localhost:%d\n" % PORT)
        print("  • Click any text, type, then \"Save text changes\".")
        print("  • Drag an image onto the hero, portrait, or a gallery tile.")
        print("  Everything saves locally. Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Stopped.\n")
