/* ==========================================================================
   Mimarlıkta Rahatsız Edici Sorular — sitenin TEK script dosyası
   --------------------------------------------------------------------------
   Site JavaScript olmadan da tam çalışır. Buradaki her şey "üstüne ekleme":
   script inmezse ya da çalışmazsa sayfa yine okunur, video yine izlenir
   (kapağın altındaki "YouTube'da izle" bağlantısı üzerinden).
   ========================================================================== */

(function () {
  "use strict";

  /* VİDEO KAPAĞI ---------------------------------------------------------
     Sayfa açılırken YouTube'a hiçbir istek gitmez. Ziyaretçi kapağa
     tıklayınca iframe oluşturulup kapağın yerine konur ve video başlar. */

  function oynat(kutu) {
    var kimlik = kutu.getAttribute("data-video");
    if (!kimlik) return;

    var cerceve = document.createElement("iframe");
    cerceve.src =
      "https://www.youtube-nocookie.com/embed/" + kimlik +
      "?autoplay=1&rel=0";
    cerceve.title = kutu.getAttribute("data-baslik") || "Video";
    cerceve.allow =
      "accelerometer; autoplay; clipboard-write; encrypted-media; " +
      "gyroscope; picture-in-picture; web-share";
    cerceve.referrerPolicy = "strict-origin-when-cross-origin";
    cerceve.allowFullscreen = true;

    kutu.innerHTML = "";
    kutu.appendChild(cerceve);
  }

  document.addEventListener("click", function (olay) {
    var dugme = olay.target.closest(".video-ac");
    if (!dugme) return;
    olay.preventDefault();
    oynat(dugme.parentNode);
  });
})();

/* DİL SEÇİMİ ---------------------------------------------------------------
   Nav'daki TR/EN düğmesine basıldığında tercihi saklıyoruz. Kökteki
   index.html bir dahaki sefere önce buraya bakıyor, tarayıcı diline değil:
   ziyaretçinin açık seçimi tahminden üstün.

   localStorage kapalı olabilir (gizli sekme, site verisi engelli), o yüzden
   try/catch — hata sayfayı durdurmasın, bağlantı yine de çalışır. */
(function () {
  document.addEventListener("click", function (olay) {
    var bag = olay.target.closest("[data-dil]");
    if (!bag) return;
    try {
      localStorage.setItem("uqa-dil", bag.getAttribute("data-dil"));
    } catch (e) { /* saklayamadık; yönlendirme yine de çalışır */ }
  });
})();
