(function (window) {
    'use strict';

    // Базовый URL API (для локальной работы и одного домена — пустая строка;
    // для отдельного фронтенда на Render можно задать window.FC_ALMAZ_API_BASE = 'https://your-app.onrender.com')
    var API_BASE = (window.FC_ALMAZ_API_BASE || '').replace(/\/$/, '');

    function getAccessToken() {
        var stored = localStorage.getItem('access_token');
        if (stored) {
            return stored;
        }
        var meta = document.querySelector('meta[name="jwt-access"]');
        if (meta && meta.content) {
            localStorage.setItem('access_token', meta.content);
            return meta.content;
        }
        return null;
    }

    function setTokens(access, refresh) {
        if (access) localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    }

    function clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    function apiRequest(endpoint, options) {
        options = options || {};
        var headers = Object.assign({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }, options.headers || {});

        var token = getAccessToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }

        return fetch(API_BASE + endpoint, {
            method: options.method || 'GET',
            headers: headers,
            body: options.body ? JSON.stringify(options.body) : undefined
        }).then(function (response) {
            return response.json().catch(function () {
                return {};
            }).then(function (data) {
                if (!response.ok) {
                    var err = new Error(data.error || data.detail || 'Ошибка запроса (' + response.status + ')');
                    err.status = response.status;
                    err.data = data;
                    throw err;
                }
                return data;
            });
        });
    }

    function loginApi(email, password) {
        return apiRequest('/api/auth/login', {
            method: 'POST',
            body: { email: email, password: password }
        }).then(function (data) {
            setTokens(data.access, data.refresh);
            return data;
        });
    }

    function getCart() {
        return apiRequest('/api/cart/');
    }

    function addToCart(productId, quantity) {
        return apiRequest('/api/cart/items/', {
            method: 'POST',
            body: {
                product_id: Number(productId),
                quantity: Number(quantity || 1)
            }
        });
    }

    function updateCartItem(itemId, quantity) {
        return apiRequest('/api/cart/items/' + itemId + '/', {
            method: 'PATCH',
            body: { quantity: Number(quantity) }
        });
    }

    function removeCartItem(itemId) {
        return apiRequest('/api/cart/items/' + itemId + '/', {
            method: 'DELETE'
        });
    }

    function applyPromoCode(code) {
        return apiRequest('/api/cart/apply-promo/', {
            method: 'POST',
            body: { code: code }
        });
    }

    function updateHeaderBadge(cartData) {
        var badge = document.getElementById('cartBadge');
        if (!badge) return;
        if (!cartData || !Array.isArray(cartData.items)) {
            badge.textContent = '';
            return;
        }
        var totalCount = cartData.items.reduce(function (sum, item) {
            return sum + (item.quantity || 0);
        }, 0);
        badge.textContent = totalCount > 0 ? ' (' + totalCount + ')' : '';
    }

    // При загрузке любой страницы подтягиваем актуальный счётчик корзины
    document.addEventListener('DOMContentLoaded', function () {
        if (getAccessToken()) {
            getCart().then(updateHeaderBadge).catch(function () {});
        }
    });

    window.CartAPI = {
        API_BASE: API_BASE,
        getAccessToken: getAccessToken,
        setTokens: setTokens,
        clearTokens: clearTokens,
        loginApi: loginApi,
        getCart: getCart,
        addToCart: addToCart,
        updateCartItem: updateCartItem,
        removeCartItem: removeCartItem,
        applyPromoCode: applyPromoCode,
        updateHeaderBadge: updateHeaderBadge
    };
})(window);