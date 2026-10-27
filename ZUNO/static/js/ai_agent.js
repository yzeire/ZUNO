/**
 * ZUNO - Kişisel Kültür ve Keşif Platformu
 * ZUNO AI Ajanı ve Akıllı Tavsiye Motoru
 * Doküman Bölüm 4 spesifikasyonlarına göre hazırlanmıştır.
 */

const ZunoAI = {
  // Hazır Hızlı Keşif Soruları
  quickPrompts: [
    "Ters köşeli, 2 saatten kısa bir film öner",
    "1984 ve Cesur Yeni Dünya benzeri distopik kitaplar",
    "Suç ve psikoloji temalı sürükleyici bir mini dizi",
    "Dostoyevski tarzı insan ruhunun derinliklerine inen bir klasik",
    "Zihnimi açacak felsefi bir bilim kurgu başyapıtı",
    "Tek oturuşta bitirilebilecek akıcı bir kitap"
  ],

  // AI Yanıtı simüle etme ve yazma efekti
  async streamResponse(element, text, speed = 15) {
    element.innerHTML = "";
    let i = 0;
    return new Promise(resolve => {
      const interval = setInterval(() => {
        if (i < text.length) {
          element.innerHTML += text.charAt(i);
          i++;
        } else {
          clearInterval(interval);
          resolve();
        }
      }, speed);
    });
  },

  // Ruh Hali & Süre Parametreleri
  moods: {
    mind_bending: { label: "🧠 Zihin Açıcı & Ters Köşe", desc: "Zaman paradoksları, rüya katmanları veya algıyı yıkan kurgular" },
    thrilling: { label: "⚡ Adrenalin & Gerilim", desc: "Temposu hiç düşmeyen, soluksuz anlar" },
    philosophical: { label: "🌌 Felsefi & Derin", desc: "Varoluşu, toplumu ve etik ikilemleri sorgulatanlar" },
    epic: { label: "⚔️ Epik & Evren İnşası", desc: "Zengin mitolojiler ve devasa dünyalar" }
  }
};
