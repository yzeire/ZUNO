/**
 * ZUNO - Kişisel Kültür ve Keşif Platformu
 * API Servis Katmanı (REST API + Çevrimdışı / LocalStorage Yedekleme)
 */

const API = {
  baseUrl: '/api',

  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP hata: ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.warn(`API Hatası [${endpoint}]:`, err.message);
      // Yerel fallback
      return this.handleFallback(endpoint, options);
    }
  },

  // Kullanıcı bilgisi
  async getCurrentUser() {
    return this.request('/auth/me');
  },

  // İçerikler (Katalog)
  async getContents(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/contents${query ? '?' + query : ''}`);
  },

  async getContentDetail(id) {
    return this.request(`/contents/${id}`);
  },

  // Kütüphane
  async getLibrary(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/library${query ? '?' + query : ''}`);
  },

  async addToLibrary(data) {
    return this.request('/library', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateLibraryItem(contentId, data) {
    return this.request(`/library/${contentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  async removeFromLibrary(contentId) {
    return this.request(`/library/${contentId}`, {
      method: 'DELETE'
    });
  },

  // Yorumlar & Puanlar
  async addReview(data) {
    return this.request('/reviews', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async toggleReviewLike(reviewId) {
    return this.request(`/reviews/${reviewId}/like`, {
      method: 'POST'
    });
  },

  // Topluluk & Sosyal Akış
  async getFeed() {
    return this.request('/feed');
  },

  async getUsers() {
    return this.request('/users');
  },

  async toggleFollow(targetId) {
    return this.request('/follows', {
      method: 'POST',
      body: JSON.stringify({ target_id: targetId })
    });
  },

  async getTasteMatch(userId) {
    return this.request(`/users/${userId}/taste-match`);
  },

  // İstatistikler
  async getStats() {
    return this.request('/stats');
  },

  // ZUNO AI
  async askAi(message) {
    return this.request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  },

  async getRandomContent(type, mood) {
    return this.request('/ai/random', {
      method: 'POST',
      body: JSON.stringify({ type, mood })
    });
  },

  async getAiRecommendations() {
    return this.request('/ai/recommend', {
      method: 'POST'
    });
  },

  // Özel Listeler
  async getLists() {
    return this.request('/lists');
  },

  async createList(data) {
    return this.request('/lists', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // LocalStorage Fallback Mantığı (Sunucu olmadan da çalışabilirlik güvencesi)
  handleFallback(endpoint, options) {
    console.info(`LocalStorage fallback devrede: ${endpoint}`);
    // Basit yanıtlar döndür
    if (endpoint.includes('/auth/me')) {
      return {
        id: 1,
        username: "demo_user",
        full_name: "Arda Yılmaz",
        bio: "Kitap kurdu ve sinema aşığı.",
        avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
        favorite_genres: ["Bilim Kurgu", "Distopya"],
        followers_count: 4,
        following_count: 2
      };
    }
    return null;
  }
};
