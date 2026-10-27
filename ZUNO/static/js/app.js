/**
 * ZUNO - Kişisel Kültür ve Keşif Platformu
 * Ana Uygulama Mantığı & Tek Sayfa Uygulaması (SPA) Yönlendiricisi
 */

const App = {
  state: {
    user: null,
    currentView: 'home',
    contents: [],
    library: [],
    feed: [],
    stats: null,
    catalogFilters: {
      type: 'all',
      category: 'all',
      search: '',
      sort: 'popular'
    },
    libraryFilters: {
      type: 'all',
      status: 'all'
    },
    activeContentId: null
  },

  async init() {
    console.log("🌟 ZUNO Platformu başlatılıyor...");
    this.bindEvents();
    await this.loadInitialData();
    this.handleRoute();
    this.renderHeroAIChips();
  },

  // Olay Dinleyicileri (Event Listeners)
  bindEvents() {
    // Navigasyon linkleri (Sidebar & Mobil)
    document.querySelectorAll('[data-view]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.getAttribute('data-view');
        this.navigateTo(view);
      });
    });

    // Üst arama çubuğu
    const headerSearch = document.getElementById('header-search-input');
    if (headerSearch) {
      headerSearch.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        this.state.catalogFilters.search = val;
        if (this.state.currentView !== 'catalog') {
          this.navigateTo('catalog');
        } else {
          this.renderCatalog();
        }
      });
    }

    // Modal Kapatma
    const modalBackdrop = document.getElementById('content-modal');
    if (modalBackdrop) {
      modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop || e.target.closest('.modal-close-btn')) {
          this.closeContentModal();
        }
      });
    }

    // Ortak Zevkler Modal Kapatma
    const tasteModal = document.getElementById('taste-modal');
    if (tasteModal) {
      tasteModal.addEventListener('click', (e) => {
        if (e.target === tasteModal || e.target.closest('.modal-close-btn')) {
          tasteModal.classList.remove('active');
        }
      });
    }

    // AI Sohbet Gönderme
    const aiForm = document.getElementById('ai-chat-form');
    if (aiForm) {
      aiForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('ai-chat-input');
        if (input && input.value.trim()) {
          this.handleAiChatSubmit(input.value.trim());
          input.value = '';
        }
      });
    }

    // Rastgele Seçim Formu
    const randomBtn = document.getElementById('btn-random-pick');
    if (randomBtn) {
      randomBtn.addEventListener('click', () => this.handleRandomPick());
    }

    // Hero AI hızlı arama
    const heroAiForm = document.getElementById('hero-ai-form');
    if (heroAiForm) {
      heroAiForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('hero-ai-input');
        if (input && input.value.trim()) {
          this.navigateTo('ai');
          setTimeout(() => {
            this.handleAiChatSubmit(input.value.trim());
            input.value = '';
          }, 200);
        }
      });
    }
  },

  async loadInitialData() {
    try {
      this.state.user = await API.getCurrentUser();
      this.updateUserUI();

      this.state.contents = await API.getContents();
      this.state.library = await API.getLibrary();
      this.state.stats = await API.getStats();
    } catch (err) {
      console.warn("Veri yükleme uyarısı:", err);
    }
  },

  updateUserUI() {
    if (!this.state.user) return;
    const userNameEls = document.querySelectorAll('.bind-user-name');
    userNameEls.forEach(el => el.textContent = this.state.user.full_name || this.state.user.username);
    
    const userHandleEls = document.querySelectorAll('.bind-user-handle');
    userHandleEls.forEach(el => el.textContent = `@${this.state.user.username}`);

    const userAvatarEls = document.querySelectorAll('.bind-user-avatar');
    userAvatarEls.forEach(el => {
      if (el.tagName === 'IMG') el.src = this.state.user.avatar;
    });
  },

  // Sayfa Yönlendirme (SPA Router)
  navigateTo(viewName) {
    this.state.currentView = viewName;
    window.location.hash = viewName;

    // Menü aktifliğini güncelle
    document.querySelectorAll('.nav-item, .nav-link, .mobile-nav-link').forEach(link => {
      if (link.getAttribute('data-view') === viewName) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Görünüm bölümlerini gizle/göster
    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const activeSec = document.getElementById(`view-${viewName}`);
    if (activeSec) {
      activeSec.classList.add('active');
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // İlgili görünümü yeniden çiz
    switch (viewName) {
      case 'home':
        this.renderHome();
        break;
      case 'catalog':
        this.renderCatalog();
        break;
      case 'library':
        this.renderLibrary();
        break;
      case 'ai':
        this.renderAI();
        break;
      case 'community':
        this.renderCommunity();
        break;
      case 'stats':
        this.renderStats();
        break;
      case 'profile':
        this.renderProfile();
        break;
    }
  },

  handleRoute() {
    const hash = window.location.hash.replace('#', '') || 'home';
    this.navigateTo(hash);
  },

  // ==========================================
  // 1. ANA SAYFA GÖRÜNÜMÜ (HOME)
  // ==========================================
  async renderHome() {
    // 1. İstatistik Sayaçları
    const stats = this.state.stats || await API.getStats();
    if (stats) {
      const bRead = document.getElementById('hero-books-read');
      if (bRead) bRead.textContent = stats.books_read || 0;

      const mWatch = document.getElementById('hero-movies-watched');
      if (mWatch) mWatch.textContent = stats.movies_watched || 0;

      const sComp = document.getElementById('hero-series-completed');
      if (sComp) sComp.textContent = stats.series_completed || 0;

      const avgR = document.getElementById('hero-avg-rating');
      if (avgR) avgR.textContent = stats.avg_rating || "0.0";
    }

    // 2. Devam Edilenler (Currently Reading / Watching)
    const activeShelf = document.getElementById('home-continue-grid');
    if (activeShelf) {
      const activeItems = (this.state.library || []).filter(item => 
        item.status === 'Okunuyor' || item.status === 'İzleniyor'
      );

      if (activeItems.length === 0) {
        activeShelf.innerHTML = `
          <div style="grid-column: 1/-1; padding: 24px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed var(--border-subtle); color: var(--text-muted);">
            <i class="fa-solid fa-bookmark" style="font-size: 24px; margin-bottom: 8px; color: var(--primary);"></i>
            <p>Şu an aktif olarak okuduğun bir kitap veya izlediğin bir dizi bulunmuyor.</p>
            <button class="btn btn-sm btn-glass" style="margin-top: 12px;" onclick="App.navigateTo('catalog')">Kataloğa Göz At</button>
          </div>
        `;
      } else {
        activeShelf.innerHTML = activeItems.map(item => this.createContinueCardHTML(item)).join('');
      }
    }

    // 3. Senin İçin Seçilenler (AI Recommendations)
    const aiRecGrid = document.getElementById('home-ai-recs-grid');
    if (aiRecGrid) {
      const recs = (this.state.contents || []).slice(0, 4);
      aiRecGrid.innerHTML = recs.map(c => this.createContentCardHTML(c)).join('');
    }

    // 4. Trend Olan Başyapıtlar
    const trendingGrid = document.getElementById('home-trending-grid');
    if (trendingGrid) {
      const trending = [...(this.state.contents || [])].sort((a, b) => b.votes_count - a.votes_count).slice(0, 4);
      trendingGrid.innerHTML = trending.map(c => this.createContentCardHTML(c)).join('');
    }

    // 5. Topluluk Akışı Önizlemesi
    const feedContainer = document.getElementById('home-feed-preview');
    if (feedContainer) {
      const feed = await API.getFeed();
      if (feed && feed.length > 0) {
        feedContainer.innerHTML = feed.slice(0, 3).map(f => this.createFeedItemHTML(f)).join('');
      }
    }
  },

  renderHeroAIChips() {
    const container = document.getElementById('ai-quick-chips');
    if (!container) return;
    container.innerHTML = ZunoAI.quickPrompts.slice(0, 4).map(prompt => `
      <span class="prompt-chip" onclick="App.handleAiQuickChip('${prompt}')">
        <i class="fa-solid fa-sparkles"></i> ${prompt}
      </span>
    `).join('');
  },

  handleAiQuickChip(prompt) {
    this.navigateTo('ai');
    setTimeout(() => {
      this.handleAiChatSubmit(prompt);
    }, 200);
  },

  // ==========================================
  // 2. KATALOG & KEŞFET GÖRÜNÜMÜ (CATALOG)
  // ==========================================
  async renderCatalog() {
    const grid = document.getElementById('catalog-grid');
    if (!grid) return;

    // Filtre butonları bağlama
    this.bindCatalogFilters();

    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size: 28px; color: var(--primary);"></i><p style="margin-top: 12px; color: var(--text-muted);">Katalog yükleniyor...</p></div>';

    const params = {
      type: this.state.catalogFilters.type,
      category: this.state.catalogFilters.category,
      search: this.state.catalogFilters.search,
      sort: this.state.catalogFilters.sort
    };

    const contents = await API.getContents(params);
    this.state.contents = contents;

    const countEl = document.getElementById('catalog-results-count');
    if (countEl) countEl.textContent = `${contents.length} içerik bulundu`;

    if (contents.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <i class="fa-solid fa-magnifying-glass" style="font-size: 38px; color: var(--text-dim); margin-bottom: 14px;"></i>
          <h3 style="font-size: 18px; margin-bottom: 6px;">Eşleşen içerik bulunamadı</h3>
          <p style="color: var(--text-muted); font-size: 14px; max-width: 420px; margin: 0 auto 18px auto;">
            Arama kriterlerinizi değiştirerek veya filtreleri temizleyerek tekrar deneyebilirsiniz.
          </p>
          <button class="btn btn-glass btn-sm" onclick="App.resetCatalogFilters()">Filtreleri Temizle</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = contents.map(item => this.createContentCardHTML(item)).join('');
  },

  bindCatalogFilters() {
    // Tür hapları (Tümü, Kitap, Film, Dizi)
    document.querySelectorAll('[data-catalog-type]').forEach(btn => {
      btn.onclick = (e) => {
        document.querySelectorAll('[data-catalog-type]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.state.catalogFilters.type = btn.getAttribute('data-catalog-type');
        this.renderCatalog();
      };
    });

    // Kategori seçici
    const catSelect = document.getElementById('catalog-category-select');
    if (catSelect) {
      catSelect.onchange = (e) => {
        this.state.catalogFilters.category = e.target.value;
        this.renderCatalog();
      };
    }

    // Sıralama seçici
    const sortSelect = document.getElementById('catalog-sort-select');
    if (sortSelect) {
      sortSelect.onchange = (e) => {
        this.state.catalogFilters.sort = e.target.value;
        this.renderCatalog();
      };
    }
  },

  resetCatalogFilters() {
    this.state.catalogFilters = { type: 'all', category: 'all', search: '', sort: 'popular' };
    const searchInput = document.getElementById('header-search-input');
    if (searchInput) searchInput.value = '';
    document.querySelectorAll('[data-catalog-type]').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-catalog-type="all"]')?.classList.add('active');
    this.renderCatalog();
  },

  // ==========================================
  // 3. KÜTÜPHANEM GÖRÜNÜMÜ (MY LIBRARY)
  // ==========================================
  async renderLibrary() {
    const grid = document.getElementById('library-grid');
    if (!grid) return;

    this.bindLibraryFilters();

    const params = {
      type: this.state.libraryFilters.type,
      status: this.state.libraryFilters.status
    };

    const items = await API.getLibrary(params);
    this.state.library = items;

    const countEl = document.getElementById('library-count');
    if (countEl) countEl.textContent = `${items.length} Öğe`;

    if (items.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <i class="fa-solid fa-book-bookmark" style="font-size: 38px; color: var(--primary); margin-bottom: 14px;"></i>
          <h3 style="font-size: 18px; margin-bottom: 6px;">Bu filtrede kütüphanenizde kayıt yok</h3>
          <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">
            Katalogdan yeni kitaplar, filmler veya diziler keşfedip durumlarını kaydedebilirsiniz.
          </p>
          <button class="btn btn-white btn-sm" onclick="App.navigateTo('catalog')">Kataloğu Keşfet</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = items.map(item => this.createLibraryCardHTML(item)).join('');
  },

  bindLibraryFilters() {
    // Tür filtresi
    document.querySelectorAll('[data-library-type]').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('[data-library-type]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.state.libraryFilters.type = btn.getAttribute('data-library-type');
        this.updateLibraryStatusFilterButtons();
        this.renderLibrary();
      };
    });
  },

  updateLibraryStatusFilterButtons() {
    const container = document.getElementById('library-status-pills');
    if (!container) return;

    const type = this.state.libraryFilters.type;
    let statuses = ['all'];

    if (type === 'book') {
      statuses = ['all', 'Okunacak', 'Okunuyor', 'Okundu', 'Yarım Bırakıldı'];
    } else if (type === 'movie') {
      statuses = ['all', 'İzlenecek', 'İzlendi'];
    } else if (type === 'series') {
      statuses = ['all', 'İzlenecek', 'İzleniyor', 'Tamamlandı', 'Ara Verildi', 'Bırakıldı'];
    } else {
      statuses = ['all', 'Okundu', 'İzlendi', 'Tamamlandı', 'Okunuyor', 'İzleniyor', 'Okunacak', 'İzlenecek'];
    }

    container.innerHTML = statuses.map(s => {
      const label = s === 'all' ? 'Tümü' : s;
      const isActive = this.state.libraryFilters.status === s ? 'active' : '';
      return `<button class="filter-pill ${isActive}" data-status="${s}" onclick="App.setLibraryStatusFilter('${s}')">${label}</button>`;
    }).join('');
  },

  setLibraryStatusFilter(status) {
    this.state.libraryFilters.status = status;
    document.querySelectorAll('#library-status-pills .filter-pill').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-status') === status);
    });
    this.renderLibrary();
  },

  // ==========================================
  // 4. ZUNO AI & SOHBET TABANLI KEŞİF (AI VIEW)
  // ==========================================
  async renderAI() {
    const chipsContainer = document.getElementById('ai-chat-chips');
    if (chipsContainer) {
      chipsContainer.innerHTML = ZunoAI.quickPrompts.map(p => `
        <span class="prompt-chip" onclick="App.handleAiChatSubmit('${p}')">${p}</span>
      `).join('');
    }
  },

  async handleAiChatSubmit(userMessage) {
    const chatBox = document.getElementById('ai-chat-messages');
    if (!chatBox) return;

    // Kullanıcı mesajı ekle
    chatBox.innerHTML += `
      <div class="chat-bubble user">
        ${userMessage}
      </div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;

    // AI Yükleniyor baloncuğu
    const tempBotId = `ai-msg-${Date.now()}`;
    chatBox.innerHTML += `
      <div class="chat-bubble bot" id="${tempBotId}">
        <i class="fa-solid fa-circle-notch fa-spin"></i> ZUNO yapay zekası kataloğu tarıyor...
      </div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const response = await API.askAi(userMessage);
      const botEl = document.getElementById(tempBotId);

      if (botEl) {
        let itemsHtml = '';
        if (response.items && response.items.length > 0) {
          itemsHtml = `
            <div class="chat-bot-items">
              ${response.items.map(item => `
                <div class="chat-suggested-item" onclick="App.openContentModal(${item.id})">
                  <img src="${item.poster_url}" alt="${item.title}">
                  <div style="flex: 1;">
                    <div style="font-size: 13px; font-weight: 700; color: #fff;">${item.title} <span style="font-size: 11px; color: var(--accent-amber);">★ ${item.rating}</span></div>
                    <div style="font-size: 11px; color: var(--text-muted);">${item.creator} • ${item.category} (${item.year})</div>
                  </div>
                  <i class="fa-solid fa-arrow-up-right-from-square" style="color: var(--primary); font-size: 13px;"></i>
                </div>
              `).join('')}
            </div>
          `;
        }

        botEl.innerHTML = `
          <div style="font-size: 14px; line-height: 1.5; white-space: pre-line;">${response.reply}</div>
          ${itemsHtml}
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    } catch (err) {
      const botEl = document.getElementById(tempBotId);
      if (botEl) {
        botEl.innerHTML = `Üzgünüm, şu an öneri üretilirken bir bağlantı sorunu yaşandı. Lütfen tekrar deneyin.`;
      }
    }
  },

  async handleRandomPick() {
    const type = document.getElementById('random-type')?.value || 'all';
    const mood = document.getElementById('random-mood')?.value || 'any';
    const resultBox = document.getElementById('random-result-box');

    if (!resultBox) return;

    resultBox.innerHTML = `
      <div style="text-align: center; padding: 20px;">
        <i class="fa-solid fa-dice-d20 fa-spin" style="font-size: 32px; color: var(--primary);"></i>
        <p style="margin-top: 10px; font-size: 13px; color: var(--text-muted);">ZUNO zarları atılıyor...</p>
      </div>
    `;

    setTimeout(async () => {
      const res = await API.getRandomContent(type, mood);
      if (res && res.picked) {
        const p = res.picked;
        resultBox.innerHTML = `
          <div style="border: 1px solid var(--border-glow); border-radius: var(--radius-md); overflow: hidden; background: var(--bg-elevated); animation: fadeIn 0.3s ease;">
            <div style="position: relative; height: 160px; overflow: hidden;">
              <img src="${p.backdrop_url || p.poster_url}" style="width: 100%; height: 100%; object-fit: cover;">
              <div style="position: absolute; inset: 0; background: linear-gradient(180deg, transparent, rgba(7,9,14,0.9));"></div>
              <div style="position: absolute; bottom: 10px; left: 14px;">
                <span class="card-type-badge badge-${p.type}">${p.type.toUpperCase()}</span>
                <h4 style="font-size: 18px; font-weight: 800; margin-top: 4px;">${p.title}</h4>
              </div>
            </div>
            <div style="padding: 14px;">
              <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">${p.description.slice(0, 110)}...</p>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; color: var(--accent-amber); font-weight: 700;">★ ${p.rating} / 10</span>
                <button class="btn btn-white btn-sm" onclick="App.openContentModal(${p.id})">İncele & Ekle</button>
              </div>
            </div>
          </div>
        `;
      }
    }, 450);
  },

  // ==========================================
  // 5. TOPLULUK & SOSYAL AKIŞ (COMMUNITY)
  // ==========================================
  async renderCommunity() {
    const feedList = document.getElementById('community-feed-list');
    if (feedList) {
      feedList.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size: 24px; color: var(--primary);"></i></div>';
      const feed = await API.getFeed();
      if (feed && feed.length > 0) {
        feedList.innerHTML = feed.map(item => this.createFeedItemHTML(item)).join('');
      } else {
        feedList.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 40px;">Henüz topluluk hareketi yok.</p>';
      }
    }

    // Topluluk Kullanıcıları (Sağ Panel)
    const userList = document.getElementById('community-users-list');
    if (userList) {
      const users = await API.getUsers();
      if (users && users.length > 0) {
        userList.innerHTML = users.map(u => `
          <div class="user-card-sm">
            <div style="display: flex; align-items: center; gap: 10px;">
              <img src="${u.avatar}" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover;">
              <div>
                <div style="font-size: 13px; font-weight: 700;">${u.full_name}</div>
                <div style="font-size: 11px; color: var(--text-dim);">@${u.username}</div>
              </div>
            </div>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-sm btn-icon" title="Ortak Zevkleri Karşılaştır" onclick="App.openTasteMatchModal(${u.id})">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
              </button>
              <button class="btn btn-sm ${u.is_following ? 'btn-glass' : 'btn-white'}" onclick="App.toggleFollowUser(${u.id}, this)">
                ${u.is_following ? 'Takipte' : 'Takip Et'}
              </button>
            </div>
          </div>
        `).join('');
      }
    }
  },

  async toggleFollowUser(userId, btnEl) {
    const res = await API.toggleFollow(userId);
    if (res && res.is_following !== undefined) {
      btnEl.textContent = res.is_following ? 'Takipte' : 'Takip Et';
      btnEl.className = `btn btn-sm ${res.is_following ? 'btn-secondary' : 'btn-outline-purple'}`;
      this.showToast(res.is_following ? 'Kullanıcı takip edildi' : 'Takipten çıkıldı');
    }
  },

  async openTasteMatchModal(userId) {
    const modal = document.getElementById('taste-modal');
    if (!modal) return;

    modal.classList.add('active');
    const contentBox = document.getElementById('taste-modal-content');
    contentBox.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size: 28px; color: var(--primary);"></i><p style="margin-top: 10px;">Ortak zevkler hesaplanıyor...</p></div>';

    const res = await API.getTasteMatch(userId);
    if (res && res.user) {
      contentBox.innerHTML = `
        <div style="text-align: center; margin-bottom: 24px;">
          <div style="display: inline-flex; align-items: center; justify-content: center; width: 84px; height: 84px; border-radius: 50%; background: var(--grad-primary); box-shadow: 0 0 30px var(--primary-glow); margin-bottom: 14px;">
            <span style="font-size: 26px; font-weight: 800; font-family: var(--font-display); color: #fff;">%${res.match_percentage}</span>
          </div>
          <h3 style="font-size: 20px; font-weight: 800;">${res.user.full_name} ile Kültür Uyumu</h3>
          <p style="font-size: 13px; color: var(--text-muted); max-width: 440px; margin: 4px auto 0 auto;">
            Kütüphane kayıtlarınız ve puanlamalarınıza göre hesaplanan ortak zevk katsayısı.
          </p>
        </div>

        <h4 style="font-size: 14px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 12px;">Ortak İçerikler (${res.common_count})</h4>
        <div style="display: flex; flex-direction: column; gap: 10px; max-height: 260px; overflow-y: auto;">
          ${res.common_items.map(ci => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
              <div style="display: flex; align-items: center; gap: 12px;">
                <img src="${ci.poster_url}" style="width: 36px; height: 50px; object-fit: cover; border-radius: 4px;">
                <div>
                  <div style="font-size: 14px; font-weight: 700;">${ci.title}</div>
                  <div style="font-size: 11px; color: var(--text-dim);">${ci.type.toUpperCase()} • ${ci.year}</div>
                </div>
              </div>
              <div style="text-align: right; font-size: 12px;">
                <div>Sen: <b style="color: var(--accent-amber);">★ ${ci.my_rating || '-'}</b></div>
                <div>${res.user.username}: <b style="color: var(--primary);">★ ${ci.their_rating || '-'}</b></div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }
  },

  // ==========================================
  // 6. İSTATİSTİKLER GÖRÜNÜMÜ (ANALYTICS)
  // ==========================================
  async renderStats() {
    const stats = await API.getStats();
    if (!stats) return;

    // Metrikler
    document.getElementById('stat-books-count').textContent = stats.books_read;
    document.getElementById('stat-pages-count').textContent = `~${stats.est_pages.toLocaleString()} sayfa`;

    document.getElementById('stat-movies-count').textContent = stats.movies_watched;
    document.getElementById('stat-hours-count').textContent = `~${stats.est_movie_hours} saat`;

    document.getElementById('stat-series-count').textContent = stats.series_completed;
    document.getElementById('stat-avg-rating').textContent = `★ ${stats.avg_rating}`;

    // Tür Dağılım Grafiği (Canvas Donut)
    this.drawGenreChart(stats.genre_distribution || []);

    // Durum Dağılım Grafiği (Bar Chart)
    this.drawStatusBarChart(stats.status_distribution || []);
  },

  drawGenreChart(data) {
    const canvas = document.getElementById('genre-chart-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (data.length === 0) {
      ctx.fillStyle = '#94a3b8';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Henüz tür verisi yok', canvas.width / 2, canvas.height / 2);
      return;
    }

    const total = data.reduce((sum, d) => sum + d.count, 0);
    const colors = ['#8b5cf6', '#6366f1', '#ec4899', '#06b6d4', '#10b981', '#f59e0b'];
    let startAngle = -0.5 * Math.PI;

    const centerX = canvas.width / 2 - 40;
    const centerY = canvas.height / 2;
    const radius = 80;

    data.forEach((d, idx) => {
      const sliceAngle = (d.count / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.arc(centerX, centerY, radius - 30, startAngle + sliceAngle, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = colors[idx % colors.length];
      ctx.fill();
      startAngle += sliceAngle;
    });

    // Gösterge (Legend)
    const legendBox = document.getElementById('genre-chart-legend');
    if (legendBox) {
      legendBox.innerHTML = data.map((d, idx) => `
        <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 6px;">
          <span style="width: 10px; height: 10px; border-radius: 50%; background: ${colors[idx % colors.length]};"></span>
          <span style="color: var(--text-main); font-weight: 600;">${d.category}</span>
          <span style="color: var(--text-dim); margin-left: auto;">${d.count} öğe</span>
        </div>
      `).join('');
    }
  },

  drawStatusBarChart(data) {
    const container = document.getElementById('status-chart-bars');
    if (!container) return;

    if (data.length === 0) {
      container.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">Kütüphane durumu bulunamadı.</p>';
      return;
    }

    const maxCount = Math.max(...data.map(d => d.count), 1);
    container.innerHTML = data.map(d => {
      const pct = (d.count / maxCount) * 100;
      return `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
            <span style="font-weight: 600; color: var(--text-main);">${d.status}</span>
            <span style="color: var(--text-muted);">${d.count} kayıt</span>
          </div>
          <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: var(--grad-primary); border-radius: 4px; transition: width 0.6s ease;"></div>
          </div>
        </div>
      `;
    }).join('');
  },

  // ==========================================
  // 7. PROFİL GÖRÜNÜMÜ (PROFILE)
  // ==========================================
  renderProfile() {
    if (!this.state.user) return;
    const u = this.state.user;

    document.getElementById('profile-name').textContent = u.full_name || u.username;
    document.getElementById('profile-handle').textContent = `@${u.username}`;
    document.getElementById('profile-bio').textContent = u.bio || "ZUNO kültür kaşifi.";
    document.getElementById('profile-avatar').src = u.avatar;

    document.getElementById('profile-followers').textContent = u.followers_count || 0;
    document.getElementById('profile-following').textContent = u.following_count || 0;

    const genresBox = document.getElementById('profile-genres-badges');
    if (genresBox) {
      genresBox.innerHTML = (u.favorite_genres || []).map(g => `
        <span class="filter-pill active">${g}</span>
      `).join('');
    }
  },

  // ==========================================
  // 8. İÇERİK DETAY MODALI (CONTENT DETAIL & REVIEWS)
  // ==========================================
  async openContentModal(contentId) {
    this.state.activeContentId = contentId;
    const modal = document.getElementById('content-modal');
    if (!modal) return;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    const container = document.getElementById('modal-content-body');
    container.innerHTML = '<div style="text-align: center; padding: 60px;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size: 32px; color: var(--primary);"></i><p style="margin-top: 14px; color: var(--text-muted);">İçerik detayları getiriliyor...</p></div>';

    const c = await API.getContentDetail(contentId);
    if (!c || c.error) {
      container.innerHTML = '<p style="padding: 40px; text-align: center;">İçerik bulunamadı.</p>';
      return;
    }

    const userLib = c.user_library || {};
    const currentStatus = userLib.status || '';
    const userRating = userLib.user_rating || 0;

    // Durum Seçenekleri (Kitap / Film / Dizi'ye göre özelleştirilmiş)
    let statusOptions = [];
    if (c.type === 'book') {
      statusOptions = ['Okunacak', 'Okunuyor', 'Okundu', 'Yarım Bırakıldı'];
    } else if (c.type === 'movie') {
      statusOptions = ['İzlenecek', 'İzlendi'];
    } else if (c.type === 'series') {
      statusOptions = ['İzlenecek', 'İzleniyor', 'Tamamlandı', 'Ara Verildi', 'Bırakıldı'];
    }

    container.innerHTML = `
      <div class="modal-hero-cover">
        <img src="${c.backdrop_url || c.poster_url}" alt="${c.title}">
        <div class="modal-hero-overlay"></div>
      </div>

      <div class="modal-body">
        <div class="modal-top-row">
          <img src="${c.poster_url}" class="modal-floating-poster" alt="${c.title}">
          <div class="modal-title-info">
            <span class="card-type-badge badge-${c.type}" style="position: static; margin-bottom: 8px;">${c.type.toUpperCase()}</span>
            <h2>${c.title}</h2>
            <div style="font-size: 14px; color: var(--text-muted); margin-top: 4px;">
              ${c.original_title ? `<span style="font-style: italic;">${c.original_title}</span> • ` : ''}
              <b>${c.creator}</b> (${c.year}) • ${c.duration_pages}
            </div>
            <div style="display: flex; align-items: center; gap: 14px; margin-top: 10px;">
              <span style="font-size: 16px; font-weight: 800; color: var(--accent-amber);"><i class="fa-solid fa-star"></i> ${c.rating} / 10</span>
              <span style="font-size: 12px; color: var(--text-dim);">${c.votes_count.toLocaleString()} değerlendirme</span>
            </div>
          </div>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px;">
          ${(c.tags || []).map(t => `<span class="prompt-chip" style="font-size: 11px;">#${t}</span>`).join('')}
        </div>

        <p style="font-size: 14px; line-height: 1.6; color: var(--text-muted); margin-bottom: 24px;">
          ${c.description}
        </p>

        <!-- Kütüphane Durumu & Puanlama Eylemleri -->
        <div class="modal-action-bar">
          <div>
            <label style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); display: block; margin-bottom: 6px;">Kütüphane Durumu</label>
            <select id="modal-status-select" class="filter-select" onchange="App.handleModalStatusChange(${c.id}, this.value)">
              <option value="">+ Kütüphaneye Ekle</option>
              ${statusOptions.map(opt => `<option value="${opt}" ${currentStatus === opt ? 'selected' : ''}>${opt}</option>`).join('')}
            </select>
          </div>

          <div>
            <label style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); display: block; margin-bottom: 6px;">Senin Puanın (1 - 10)</label>
            <div class="stars-picker" id="modal-stars-picker">
              ${[1,2,3,4,5,6,7,8,9,10].map(num => `
                <i class="fa-solid fa-star ${num <= userRating ? 'active' : ''}" 
                   title="${num} Puan" 
                   onclick="App.handleModalRatingChange(${c.id}, ${num})"></i>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Yorum Formu (Spoiler Korumalı!) -->
        <div class="review-form-card">
          <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Düşüncelerini Paylaş</h4>
          <textarea id="new-review-comment" placeholder="${c.title} hakkında incelemen veya yorumun..."></textarea>
          <div class="review-form-footer">
            <label class="spoiler-checkbox-label">
              <input type="checkbox" id="new-review-spoiler">
              <span>⚠️ Bu yorum spoiler içeriyor</span>
            </label>
            <button class="btn btn-white btn-sm" onclick="App.handleReviewSubmit(${c.id})">Yorumu Yayınla</button>
          </div>
        </div>

        <!-- Yorumlar Listesi -->
        <div style="margin-top: 28px;">
          <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Topluluk Değerlendirmeleri (${(c.reviews || []).length})</h3>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${(c.reviews || []).map(r => this.createReviewItemHTML(r)).join('')}
          </div>
        </div>

        <!-- Benzer İçerikler -->
        ${c.similar && c.similar.length > 0 ? `
          <div style="margin-top: 36px;">
            <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Benzer İçerikler</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px;">
              ${c.similar.map(sim => `
                <div class="content-card" onclick="App.openContentModal(${sim.id})" style="box-shadow: none;">
                  <div class="card-poster-wrap">
                    <img src="${sim.poster_url}" class="card-poster">
                    <span class="card-type-badge badge-${sim.type}">${sim.type.toUpperCase()}</span>
                    <span class="card-rating-badge">★ ${sim.rating}</span>
                  </div>
                  <div style="padding: 10px;">
                    <div style="font-size: 13px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${sim.title}</div>
                    <div style="font-size: 11px; color: var(--text-dim);">${sim.category} (${sim.year})</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  },

  closeContentModal() {
    const modal = document.getElementById('content-modal');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = 'auto';
    }
  },

  async handleModalStatusChange(contentId, newStatus) {
    if (!newStatus) return;
    await API.addToLibrary({ content_id: contentId, status: newStatus });
    this.showToast(`Durum '${newStatus}' olarak kaydedildi!`);
    await this.loadInitialData();
  },

  async handleModalRatingChange(contentId, rating) {
    await API.addToLibrary({ content_id: contentId, status: 'Okundu', user_rating: rating });
    
    // Yıldızları UI'da güncelle
    const stars = document.querySelectorAll('#modal-stars-picker i');
    stars.forEach((star, idx) => {
      star.classList.toggle('active', (idx + 1) <= rating);
    });

    this.showToast(`${rating} / 10 puan verildi!`);
    await this.loadInitialData();
  },

  async handleReviewSubmit(contentId) {
    const textEl = document.getElementById('new-review-comment');
    const spoilerEl = document.getElementById('new-review-spoiler');
    if (!textEl || !textEl.value.trim()) {
      this.showToast('Lütfen bir yorum yazın', 'error');
      return;
    }

    const comment = textEl.value.trim();
    const isSpoiler = spoilerEl ? spoilerEl.checked : false;

    await API.addReview({
      content_id: contentId,
      rating: 9.0,
      comment: comment,
      is_spoiler: isSpoiler
    });

    this.showToast('Yorumunuz toplulukla paylaşıldı!');
    textEl.value = '';
    if (spoilerEl) spoilerEl.checked = false;

    // Modalı yenile
    this.openContentModal(contentId);
    await this.loadInitialData();
  },

  // Spoiler Aç / Kapat
  revealSpoiler(shieldEl) {
    const parent = shieldEl.closest('.spoiler-container');
    if (parent) {
      shieldEl.style.display = 'none';
      const text = parent.querySelector('.spoiler-text-revealed');
      if (text) text.classList.add('active');
    }
  },

  async toggleLikeReview(reviewId, btnEl) {
    const res = await API.toggleReviewLike(reviewId);
    if (res && res.likes_count !== undefined) {
      btnEl.classList.toggle('liked', res.liked);
      const span = btnEl.querySelector('span');
      if (span) span.textContent = res.likes_count;
    }
  },

  // ==========================================
  // 9. YARDIMCI HTML ŞABLON ÜRETECİLERİ
  // ==========================================
  createContentCardHTML(item) {
    const userBadge = item.user_status ? `<span class="card-user-status-pill">${item.user_status}</span>` : '';
    return `
      <div class="content-card" onclick="App.openContentModal(${item.id})">
        <div class="card-poster-wrap">
          <img src="${item.poster_url}" class="card-poster" alt="${item.title}" loading="lazy">
          <span class="card-type-badge badge-${item.type}">
            ${item.type === 'book' ? '<i class="fa-solid fa-book"></i> KİTAP' : 
              item.type === 'movie' ? '<i class="fa-solid fa-film"></i> FİLM' : 
              '<i class="fa-solid fa-tv"></i> DİZİ'}
          </span>
          <span class="card-rating-badge">
            <i class="fa-solid fa-star"></i> ${item.rating}
          </span>
          ${userBadge}
        </div>
        <div class="card-info">
          <h3 class="card-title">${item.title}</h3>
          <p class="card-creator">${item.creator} (${item.year})</p>
          <div class="card-footer">
            <span>${item.duration_pages}</span>
            <span class="card-add-btn">
              ${item.user_status ? '<i class="fa-solid fa-check"></i>' : '<i class="fa-solid fa-plus"></i> Ekle'}
            </span>
          </div>
        </div>
      </div>
    `;
  },

  createContinueCardHTML(item) {
    return `
      <div class="content-card" onclick="App.openContentModal(${item.content_id})">
        <div class="card-poster-wrap">
          <img src="${item.poster_url}" class="card-poster" alt="${item.title}">
          <span class="card-type-badge badge-${item.type}">${item.status}</span>
        </div>
        <div class="card-info">
          <h3 class="card-title">${item.title}</h3>
          <p class="card-creator">${item.creator}</p>
          <div style="font-size: 11px; color: var(--accent-emerald); font-weight: 600; margin-top: auto;">
            <i class="fa-solid fa-spinner fa-spin"></i> Devam Ediliyor
          </div>
        </div>
      </div>
    `;
  },

  createLibraryCardHTML(item) {
    return `
      <div class="content-card" onclick="App.openContentModal(${item.content_id})">
        <div class="card-poster-wrap">
          <img src="${item.poster_url}" class="card-poster" alt="${item.title}">
          <span class="card-type-badge badge-${item.type}">${item.status}</span>
          ${item.user_rating > 0 ? `<span class="card-rating-badge" style="color: var(--primary);">★ ${item.user_rating}</span>` : ''}
        </div>
        <div class="card-info">
          <h3 class="card-title">${item.title}</h3>
          <p class="card-creator">${item.creator} (${item.year})</p>
          ${item.personal_note ? `<p style="font-size: 11px; font-style: italic; color: var(--text-dim); margin-top: 4px;">"${item.personal_note.slice(0, 50)}..."</p>` : ''}
          <div class="card-footer">
            <span style="font-size: 11px; color: var(--accent-emerald); font-weight: 700;">${item.status}</span>
            <span class="card-add-btn" style="color: var(--text-dim);">Düzenle</span>
          </div>
        </div>
      </div>
    `;
  },

  createFeedItemHTML(item) {
    const isSpoiler = item.is_spoiler === 1;
    return `
      <div class="feed-item">
        <div class="feed-header">
          <div class="feed-user-info">
            <img src="${item.avatar}" class="feed-avatar" alt="${item.username}">
            <div class="feed-meta">
              <h4>${item.full_name || item.username}</h4>
              <span>@${item.username}</span>
            </div>
          </div>
          <div style="font-size: 13px; font-weight: 700; color: var(--accent-amber);">
            <i class="fa-solid fa-star"></i> ${item.rating} / 10
          </div>
        </div>

        <div class="feed-content-card" onclick="App.openContentModal(${item.content_id})" style="cursor: pointer;">
          <img src="${item.poster_url}" alt="${item.content_title}">
          <div class="feed-content-details">
            <h5>${item.content_title}</h5>
            <p>${item.creator || ''} (${item.year || ''})</p>
          </div>
        </div>

        <!-- SPOILER KORUMASI GÖVDE -->
        ${isSpoiler ? `
          <div class="spoiler-container">
            <div class="spoiler-shield" onclick="App.revealSpoiler(this)">
              <div class="spoiler-shield-text">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span>Bu yorumda spoiler bulunmaktadır.</span>
              </div>
              <span class="spoiler-shield-btn">Spoileri Göster</span>
            </div>
            <div class="spoiler-text-revealed">
              ${item.comment}
            </div>
          </div>
        ` : `
          <p style="font-size: 14px; line-height: 1.5; color: var(--text-main); margin: 12px 0;">
            ${item.comment}
          </p>
        `}

        <div class="feed-actions">
          <button class="like-action-btn" onclick="App.toggleLikeReview(${item.id}, this)">
            <i class="fa-solid fa-heart"></i>
            <span>${item.likes_count || 0}</span>
          </button>
          <span style="margin-left: auto; font-size: 11px; color: var(--text-dim);">${new Date(item.created_at || Date.now()).toLocaleDateString('tr-TR')}</span>
        </div>
      </div>
    `;
  },

  createReviewItemHTML(r) {
    const isSpoiler = r.is_spoiler === 1;
    return `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <img src="${r.avatar}" style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover;">
            <span style="font-size: 13px; font-weight: 700;">${r.full_name || r.username}</span>
          </div>
          <span style="font-size: 13px; font-weight: 700; color: var(--accent-amber);">★ ${r.rating}</span>
        </div>

        ${isSpoiler ? `
          <div class="spoiler-container">
            <div class="spoiler-shield" onclick="App.revealSpoiler(this)" style="padding: 10px 14px;">
              <div class="spoiler-shield-text" style="font-size: 12px;">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span>Spoiler içerir. Okumak için tıklayın</span>
              </div>
              <span class="spoiler-shield-btn">Aç</span>
            </div>
            <div class="spoiler-text-revealed">
              ${r.comment}
            </div>
          </div>
        ` : `
          <p style="font-size: 13px; color: var(--text-main); line-height: 1.5;">${r.comment}</p>
        `}

        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 11px; color: var(--text-dim);">
          <button class="like-action-btn ${r.is_liked ? 'liked' : ''}" onclick="App.toggleLikeReview(${r.id}, this)">
            <i class="fa-solid fa-heart"></i>
            <span>${r.likes_count || 0}</span>
          </button>
          <span>${new Date(r.created_at || Date.now()).toLocaleDateString('tr-TR')}</span>
        </div>
      </div>
    `;
  },

  showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <i class="fa-solid ${type === 'error' ? 'fa-circle-xmark' : 'fa-circle-check'}" style="color: ${type === 'error' ? 'var(--accent-rose)' : 'var(--accent-emerald)'};"></i>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }
};

// Uygulama yüklendiğinde başlat
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
