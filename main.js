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
