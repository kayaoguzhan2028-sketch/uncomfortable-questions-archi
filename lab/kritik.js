// Kritik kutusu — sadece lab sayfaları için, Webflow'a gitmez.
// Kullanım: <script src="kritik.js" data-sayfa="manifesto-map"></script>
// Her sayfa kendi data-sayfa adıyla saklanır; yorumlar sayfalar arasında karışmaz.
(() => {
  const URL = 'https://dxgwgenzrebnmwzhwhck.supabase.co/rest/v1/kritik';
  const KEY = 'sb_publishable_YP8wq-frx_W7KW3NurAPJw_rBamLIO7'; // herkese açık anahtar, sadece kritik tablosuna erişir
  const SAYFA = document.currentScript.dataset.sayfa;
  const H = { apikey: KEY, 'Content-Type': 'application/json', Prefer: 'return=representation' };
  const api = (q, opt = {}) => fetch(URL + q, { headers: H, ...opt }).then(r => r.ok ? r.json() : Promise.reject(r.status));

  const kutu = document.createElement('section');
  kutu.className = 'kritik';
  kutu.innerHTML = `
    <style>
      .kritik { max-width: 720px; margin: 64px auto; padding: 0 16px; font: 13px/1.6 "Space Mono", monospace; color: inherit; }
      .kritik h2 { font-size: 13px; margin: 0 0 16px; text-transform: uppercase; letter-spacing: .05em; }
      .kritik form { display: grid; gap: 8px; margin-bottom: 24px; }
      .kritik input, .kritik textarea { font: inherit; color: inherit; background: transparent; border: 1px solid currentColor; opacity: .8; padding: 8px; width: 100%; box-sizing: border-box; }
      .kritik textarea { min-height: 72px; resize: vertical; }
      .kritik button { font: inherit; color: inherit; background: none; border: 1px solid currentColor; padding: 4px 12px; cursor: pointer; justify-self: start; }
      .kritik ul { list-style: none; margin: 0; padding: 0; }
      .kritik li { border-top: 1px dashed currentColor; padding: 12px 0; }
      .kritik .ust { display: flex; gap: 12px; align-items: baseline; }
      .kritik .ust b { flex: 1; }
      .kritik .ust small { opacity: .5; }
      .kritik .ust button { border: 0; padding: 0; opacity: .6; }
      .kritik p { margin: 4px 0 0; white-space: pre-wrap; }
      .kritik .bos { opacity: .5; }
    </style>
    <h2>Kritikler</h2>
    <form>
      <input name="isim" placeholder="İsim" maxlength="60" required>
      <textarea name="metin" placeholder="Yorum" maxlength="3000" required></textarea>
      <button>Gönder</button>
    </form>
    <ul></ul>`;
  document.body.appendChild(kutu);

  const form = kutu.querySelector('form'), liste = kutu.querySelector('ul');
  try { form.isim.value = localStorage.getItem('kritik-isim') || ''; } catch (e) {}

  const tarih = t => new Date(t).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' });

  const ciz = rows => {
    liste.innerHTML = rows.length ? '' : '<li class="bos">Henüz kritik yok.</li>';
    rows.forEach(k => {
      const li = document.createElement('li');
      li.innerHTML = '<div class="ust"><b></b><small></small><button data-is="duzenle">düzenle</button><button data-is="sil" aria-label="Sil">✕</button></div><p></p>';
      li.querySelector('b').textContent = k.isim || 'İsimsiz';
      li.querySelector('small').textContent = tarih(k.created_at) + (k.updated_at ? ' · düzenlendi' : '');
      li.querySelector('p').textContent = k.metin;
      li.querySelector('[data-is=sil]').onclick = () => {
        if (confirm('Bu kritik silinsin mi?')) api('?id=eq.' + k.id, { method: 'DELETE' }).then(yukle, hata);
      };
      li.querySelector('[data-is=duzenle]').onclick = () => {
        const yeni = prompt('Yorumu düzenle:', k.metin);
        if (yeni && yeni.trim() && yeni !== k.metin) {
          api('?id=eq.' + k.id, { method: 'PATCH', body: JSON.stringify({ metin: yeni.trim(), updated_at: new Date().toISOString() }) }).then(yukle, hata);
        }
      };
      liste.appendChild(li);
    });
  };

  const hata = () => alert('Bağlantı sorunu, birazdan tekrar dene.');
  const yukle = () => api('?sayfa=eq.' + encodeURIComponent(SAYFA) + '&order=created_at.asc').then(ciz, () => {
    liste.innerHTML = '<li class="bos">Kritikler yüklenemedi.</li>';
  });

  form.onsubmit = e => {
    e.preventDefault();
    const isim = form.isim.value.trim(), metin = form.metin.value.trim();
    if (!isim || !metin) return;
    try { localStorage.setItem('kritik-isim', isim); } catch (e) {}
    form.querySelector('button').disabled = true;
    api('', { method: 'POST', body: JSON.stringify({ sayfa: SAYFA, isim, metin }) })
      .then(() => { form.metin.value = ''; yukle(); }, hata)
      .finally(() => { form.querySelector('button').disabled = false; });
  };

  yukle();
})();
