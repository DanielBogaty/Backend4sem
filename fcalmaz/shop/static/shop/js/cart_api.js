(function (window) {
    'use strict';

    var API_BASE = (window.FC_ALMAZ_API_BASE || '').replace(/\/$/, '');

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getAccessToken() {
        // 1. Всегда берём свежий JWT токен текущего залогиненного пользователя из meta-тега
        var meta = document.querySelector('meta[name="jwt-access"]');
        if (meta && meta.content) {
            localStorage.setItem('access_token', meta.content);
            return meta.content;
        }
        // 2. Иначе берём из localStorage (если вход был напрямую через /api/auth/login)
        return localStorage.getItem('access_token');
    }

    function setTokens(access, refresh) {
        if (access) localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    }

    function clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    function isAuthenticated() {
        var meta = document.querySelector('meta[name="jwt-access"]');
        return Boolean((meta && meta.content) || localStorage.getItem('access_token'));
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

        var csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        return fetch(API_BASE + endpoint, {
            method: options.method || 'GET',
            headers: headers,
            credentials: 'same-origin',
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

    document.addEventListener('DOMContentLoaded', function () {
        if (isAuthenticated()) {
            getCart().then(updateHeaderBadge).catch(function () {});
        }
    });

    window.CartAPI = {
        API_BASE: API_BASE,
        getAccessToken: getAccessToken,
        isAuthenticated: isAuthenticated,
        setTokens: setTokens,
        clearTokens: clearTokens,
        getCart: getCart,
        addToCart: addToCart,
        updateCartItem: updateCartItem,
        removeCartItem: removeCartItem,
        applyPromoCode: applyPromoCode,
        updateHeaderBadge: updateHeaderBadge
    };
})(window);