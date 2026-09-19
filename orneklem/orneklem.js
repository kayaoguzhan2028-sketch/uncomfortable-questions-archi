/* ==========================================================================
   Örneklem sayfalarının ek scripti
   --------------------------------------------------------------------------
   main.js'in kuralı burada da geçerli: sayfa JavaScript olmadan da okunur.
   Kitapçık açılmazsa kapak görünür; slayt açılmazsa ilk slayt görünür;
   indir düğmesi, metin ve bağlantılar yerinde kalır.
   Bileşenler onaylanınca buradaki bölümler (ALAN ETİKETLERİ hariç)
   main.js'e taşınır.
   ========================================================================== */

/* ALAN ETİKETLERİ ----------------------------------------------------------
   Şeritteki düğme: her parçanın Excel'deki sütununu gösterir/gizler.
   sayfa.html?alanlar — etiketler açık gelsin (sayfayı yapacak kişiye link). */
(function () {
  var dugme = document.querySelector("[data-alan-dugme]");
  if (!dugme) return;
  function ayarla(acik) {
    document.body.classList.toggle("alanlar", acik);
    dugme.setAttribute("aria-pressed", acik ? "true" : "false");
  }
  dugme.addEventListener("click", function () {
    ayarla(!document.body.classList.contains("alanlar"));
  });
  if (/[?&]alanlar(&|$)/.test(location.search)) ayarla(true);
})();

/* PENCERE ------------------------------------------------------------------
   [data-pencere="id"] düğmesi o <dialog>'u açar. Şimdilik indir ve anket
   düğmeleri bunu kullanıyor: gerçek bağlantı yerine bir açıklama.
   Altyapı kurulunca <button> yerine <a href="..."> gelecek. */
(function () {
  document.addEventListener("click", function (olay) {
    var dugme = olay.target.closest("[data-pencere]");
    if (!dugme) return;
    var pencere = document.getElementById(dugme.getAttribute("data-pencere"));
    if (pencere && pencere.showModal) pencere.showModal();
    else if (pencere) alert(pencere.innerText);
  });
})();

/* TAM EKRAN ----------------------------------------------------------------
   [data-tam-ekran="id"] düğmesi o bloğu tam ekrana alır. Tarayıcı
   destekliyorsa gerçek tam ekran, desteklemiyorsa (iPhone) sayfayı kaplayan
   katman — ikisinde de blok .tam-ekran sınıfını alır. Kitapçık ve slayt
   pencere boyutu değişince kendini yeniden ölçüyor; o yüzden her geçişte
   bir "resize" olayı yolluyoruz. */
var tamEkran = (function () {
  var acik = null;

  function etiket(blok, durum) {
    var dugmeler = document.querySelectorAll('[data-tam-ekran="' + blok.id + '"]');
    for (var i = 0; i < dugmeler.length; i++) {
      dugmeler[i].textContent = durum ? "Kapat ✕" : "Tam ekran ⤢";
      dugmeler[i].setAttribute("aria-pressed", durum ? "true" : "false");
    }
  }

  function olc() {
    setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 60);
  }

  function ac(blok) {
    acik = blok;
    blok.classList.add("tam-ekran");
    document.documentElement.style.overflow = "hidden";
    etiket(blok, true);
    if (blok.requestFullscreen) blok.requestFullscreen().catch(function () {});
    olc();
  }

  function kapat() {
    if (!acik) return;
    var blok = acik;
    acik = null;
    blok.classList.remove("tam-ekran");
    document.documentElement.style.overflow = "";
    etiket(blok, false);
    if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
    olc();
  }

  document.addEventListener("click", function (olay) {
    var dugme = olay.target.closest("[data-tam-ekran]");
    if (!dugme) return;
    var blok = document.getElementById(dugme.getAttribute("data-tam-ekran"));
    if (!blok) return;
    if (acik === blok) kapat(); else ac(blok);
  });

  // Tarayıcının kendi çıkışı (Esc, geri hareketi) — katmanı da kapat
  document.addEventListener("fullscreenchange", function () {
    if (!document.fullscreenElement && acik) kapat();
  });
  document.addEventListener("keydown", function (olay) {
    if (olay.key === "Escape" && acik && !document.fullscreenElement) kapat();
  });

  // sayfa.html#tamekran — sayfadaki ilk tam ekranlık blok açık gelsin.
  // (Tarayıcı gerçek tam ekranı sadece tıklamayla açar; linkle katman açılır.)
  if (/tamekran/.test(location.hash)) {
    var ilk = document.querySelector("[data-tam-ekran]");
    var blok = ilk && document.getElementById(ilk.getAttribute("data-tam-ekran"));
    if (blok) {
      acik = blok;
      blok.classList.add("tam-ekran");
      document.documentElement.style.overflow = "hidden";
      etiket(blok, true);
    }
  }

  return { acik: function () { return acik; } };
})();

/* KİTAPÇIK -----------------------------------------------------------------
   StPageFlip (lib/page-flip.browser.js, MIT). Sayfalar <div class="sayfa">
   içinde <img data-src>. Hepsi birden inmesin diye sadece açık sayfanın
   çevresindekiler yükleniyor: 136 sayfalık fanzin 11 MB, ilk açılışta
   bunun onda biri iniyor.

   Bir sayfada birden fazla kitapçık olabilir (rapor: TR ve EN). Gizli
   olanı (hidden) görünür olduğunda kuruyoruz: gizli bir kutunun genişliği
   0, kütüphane onu ölçemez. */
var kitapcik = (function () {
  var aktif = null;   // ok tuşları hangi kitabı çevirsin

  function kur(kutu) {
    if (!window.St || kutu.kitap) return;

    var sahne = kutu.querySelector(".kitapcik-kitap");
    var sayfalar = sahne.querySelectorAll(".sayfa");
    var geri = kutu.querySelector(".geri");
    var ileri = kutu.querySelector(".ileri");
    var kaydirac = kutu.querySelector("input[type=range]");
    var sayac = kutu.querySelector(".kitapcik-sayac");
    var toplam = sayfalar.length;

    // Görsel ölçüsü: data-en / data-boy (piksel). A5 ile A4 aynı orana
    // sahip; ikisi de aynı ayarla çalışır.
    var en = +kutu.getAttribute("data-en") || 760;
    var boy = +kutu.getAttribute("data-boy") || 1079;
    var oran = boy / en;
    kutu.style.setProperty("--sayfa-orani", (en / boy).toFixed(4));

    function yukle(merkez) {
      for (var i = merkez - 2; i <= merkez + 5; i++) {
        var img = sayfalar[i] && sayfalar[i].querySelector("img[data-src]");
        if (img) {
          img.src = img.getAttribute("data-src");
          img.removeAttribute("data-src");
        }
      }
    }
    yukle(0);

    kutu.classList.add("kitapcik-hazir");

    var kitap = new St.PageFlip(sahne, {
      width: 400,
      height: Math.round(400 * oran),
      size: "stretch",
      // Kutu 2 × minWidth'ten darsa kütüphane tek sayfaya geçer (telefon).
      minWidth: 260,
      maxWidth: 1000,            // tam ekranda büyüyebilsin; normalde kutu sınırlıyor
      minHeight: Math.round(260 * oran),
      maxHeight: Math.round(1000 * oran),
      showCover: true,           // kapak tek, iç sayfalar karşılıklı
      usePortrait: true,
      mobileScrollSupport: false, // telefonda sayfa kaydırması kitabı çevirmesin
      maxShadowOpacity: 0.35,
      flippingTime: 700
    });
    kitap.loadFromHTML(sayfalar);
    kutu.kitap = kitap;

    function guncelle() {
      var i = kitap.getCurrentPageIndex();
      yukle(i);
      var yatay = kitap.getOrientation() === "landscape";
      // Yatayda karşılıklı iki sayfa açık: "2–3 / 136". Kapak ve arka kapak tek.
      var metin = String(i + 1);
      if (yatay && i > 0 && i < toplam - 1) metin = (i + 1) + "–" + (i + 2);
      sayac.textContent = metin + " / " + toplam;
      kaydirac.value = i + 1;
      geri.disabled = i === 0;
      ileri.disabled = i >= toplam - (yatay ? 2 : 1);
    }

    kitap.on("flip", guncelle);
    kitap.on("changeOrientation", guncelle);
    kitap.on("init", guncelle);

    geri.addEventListener("click", function () { kitap.flipPrev(); });
    ileri.addEventListener("click", function () { kitap.flipNext(); });

    kaydirac.max = toplam;
    kaydirac.addEventListener("input", function () {
      var i = +kaydirac.value - 1;
      yukle(i);
      kitap.turnToPage(i);
      guncelle();
    });

    // sayfa.html#sayfa=12 — doğrudan o sayfadan açılsın
    var m = /sayfa=(\d+)/.exec(location.hash);
    if (m) {
      var hedef = Math.min(Math.max(+m[1], 1), toplam) - 1;
      yukle(hedef);
      kitap.turnToPage(hedef);
    }

    guncelle();
    aktif = kitap;
  }

  function gorunenleriKur() {
    var kutular = document.querySelectorAll(".kitapcik");
    for (var i = 0; i < kutular.length; i++) {
      if (!kutular[i].closest("[hidden]")) {
        kur(kutular[i]);
        aktif = kutular[i].kitap || aktif;
      }
    }
  }

  document.addEventListener("keydown", function (olay) {
    if (!aktif || olay.target.closest("input, textarea, dialog[open]")) return;
    var acik = tamEkran.acik();
    if (acik && !acik.classList.contains("kitapcik")) return;
    if (olay.key === "ArrowLeft") aktif.flipPrev();
    if (olay.key === "ArrowRight") aktif.flipNext();
  });

  gorunenleriKur();
  return { gorunenleriKur: gorunenleriKur };
})();

/* DİL SEÇİMİ ---------------------------------------------------------------
   Rapor: aynı sayfada TR ve EN kitapçık. Düğme birini gizler, ötekini
   gösterir; ilk kez görünen kitapçık o an kurulur. ?dil=en ile EN açılır. */
(function () {
  var secim = document.querySelector(".dil-secim");
  if (!secim) return;
  var dugmeler = secim.querySelectorAll("button[data-dil]");
  var bloklar = document.querySelectorAll(".dil-blok");

  function goster(dil) {
    for (var i = 0; i < bloklar.length; i++) {
      bloklar[i].hidden = bloklar[i].getAttribute("data-dil") !== dil;
    }
    for (var j = 0; j < dugmeler.length; j++) {
      dugmeler[j].setAttribute("aria-pressed",
        dugmeler[j].getAttribute("data-dil") === dil ? "true" : "false");
    }
    kitapcik.gorunenleriKur();
  }

  secim.addEventListener("click", function (olay) {
    var dugme = olay.target.closest("button[data-dil]");
    if (dugme) goster(dugme.getAttribute("data-dil"));
  });

  var m = /[?&]dil=(\w+)/.exec(location.search);
  if (m && document.querySelector('.dil-blok[data-dil="' + m[1] + '"]')) goster(m[1]);
})();

/* SLAYT --------------------------------------------------------------------
   Swiper (lib/swiper-bundle.min.js, MIT). Üstte büyük slayt, altta küçük
   önizlemeler. Ok tuşları, parmakla kaydırma, "3 / 21" sayacı. */
(function () {
  if (!window.Swiper) return;
  var kutular = document.querySelectorAll(".slayt");
  for (var i = 0; i < kutular.length; i++) {
    var kutu = kutular[i];
    var kucuk = new Swiper(kutu.querySelector(".slayt-kucuk"), {
      slidesPerView: "auto",
      spaceBetween: 8,
      freeMode: true,
      watchSlidesProgress: true
    });
    new Swiper(kutu.querySelector(".slayt-ana"), {
      spaceBetween: 16,
      keyboard: { enabled: true },
      navigation: { prevEl: kutu.querySelector(".geri"), nextEl: kutu.querySelector(".ileri") },
      pagination: { el: kutu.querySelector(".slayt-sayac"), type: "fraction" },
      thumbs: { swiper: kucuk }
    });
  }
})();

/* BÜYÜTEÇ ------------------------------------------------------------------
   <button class="buyut-ac" data-grup="g" data-buyuk="...webp" data-alt="...">
   Tıklanınca aynı gruptaki bütün görseller ekranı kaplayan bir Swiper'da
   açılır; çift tıkla / iki parmakla yakınlaştırılır. Swiper yoksa görsel
   yeni sekmede açılır. */
(function () {
  var pencere = null, kaydirici = null, grupAdi = null;

  function kur() {
    pencere = document.createElement("dialog");
    pencere.className = "buyutec";
    pencere.innerHTML =
      '<div class="buyutec-ust"><span class="buyutec-baslik"></span>' +
      '<span class="buyutec-sayac"></span>' +
      '<button class="buyutec-kapat" type="button">Kapat ✕</button></div>' +
      '<div class="swiper"><div class="swiper-wrapper"></div>' +
      '<div class="swiper-button-prev"></div><div class="swiper-button-next"></div></div>';
    document.body.appendChild(pencere);
    pencere.querySelector(".buyutec-kapat").addEventListener("click", function () { pencere.close(); });
  }

  function doldur(grup) {
    var dugmeler = document.querySelectorAll('.buyut-ac[data-grup="' + grup + '"]');
    var sarici = pencere.querySelector(".swiper-wrapper");
    sarici.innerHTML = "";
    for (var i = 0; i < dugmeler.length; i++) {
      var slayt = document.createElement("div");
      slayt.className = "swiper-slide";
      var zoom = document.createElement("div");
      zoom.className = "swiper-zoom-container";
      var img = document.createElement("img");
      img.src = dugmeler[i].getAttribute("data-buyuk");
      img.alt = dugmeler[i].getAttribute("data-alt") || "";
      img.loading = "lazy";
      zoom.appendChild(img);
      slayt.appendChild(zoom);
      slayt.setAttribute("data-alt", img.alt);
      sarici.appendChild(slayt);
    }
    return dugmeler;
  }

  function baslik() {
    var s = kaydirici.slides[kaydirici.activeIndex];
    pencere.querySelector(".buyutec-baslik").textContent = s ? s.getAttribute("data-alt") : "";
    pencere.querySelector(".buyutec-sayac").textContent =
      kaydirici.slides.length > 1 ? (kaydirici.activeIndex + 1) + " / " + kaydirici.slides.length : "";
  }

  // Galerinin / tek görselin altındaki "Tam ekran" düğmesi: hemen üstündeki
  // bloğun ilk görselini açar.
  document.addEventListener("click", function (olay) {
    var tam = olay.target.closest("[data-tam-galeri]");
    if (!tam) return;
    var ilk = tam.parentNode.previousElementSibling.querySelector(".buyut-ac");
    if (ilk) ilk.click();
  });

  document.addEventListener("click", function (olay) {
    var dugme = olay.target.closest(".buyut-ac");
    if (!dugme) return;
    olay.preventDefault();
    if (!window.Swiper || !window.HTMLDialogElement) {
      window.open(dugme.getAttribute("data-buyuk"), "_blank");
      return;
    }
    if (!pencere) kur();
    var grup = dugme.getAttribute("data-grup");
    var dugmeler = doldur(grup);
    var sira = Array.prototype.indexOf.call(dugmeler, dugme);
    pencere.showModal();
    if (kaydirici) kaydirici.destroy(true, true);
    kaydirici = new Swiper(pencere.querySelector(".swiper"), {
      initialSlide: sira,
      zoom: { maxRatio: 3 },
      keyboard: { enabled: true },
      navigation: {
        prevEl: pencere.querySelector(".swiper-button-prev"),
        nextEl: pencere.querySelector(".swiper-button-next")
      },
      on: { slideChange: baslik }
    });
    grupAdi = grup;
    baslik();
  });
})();

/* DİNLE (Spotify) ----------------------------------------------------------
   Video kapağıyla aynı: sayfa açılırken Spotify'a hiçbir istek gitmez.
   Tıklanınca oynatıcı iframe'i kartın yerine konur. */
(function () {
  document.addEventListener("click", function (olay) {
    var dugme = olay.target.closest(".dinle-ac");
    if (!dugme) return;
    olay.preventDefault();
    var kutu = dugme.parentNode;
    var kimlik = kutu.getAttribute("data-spotify");
    if (!kimlik) return;
    var cerceve = document.createElement("iframe");
    cerceve.src = "https://open.spotify.com/embed/episode/" + kimlik + "?utm_source=generator&autoplay=1";
    cerceve.title = kutu.getAttribute("data-baslik") || "Podcast";
    cerceve.allow = "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture";
    cerceve.loading = "lazy";
    kutu.innerHTML = "";
    kutu.appendChild(cerceve);
  });
})();
