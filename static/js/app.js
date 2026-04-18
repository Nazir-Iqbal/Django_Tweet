// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);

    fetch('/accounts/toggle-theme/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRF(),
            'Content-Type': 'application/json',
        },
    });
}

function getCSRF() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    if (cookie) return cookie.split('=')[1];
    const meta = document.querySelector('[name=csrfmiddlewaretoken]');
    if (meta) return meta.value;
    const area = document.querySelector('[data-csrf]');
    if (area) return area.dataset.csrf;
    return '';
}

// User search
const searchInput = document.getElementById('userSearch');
const searchResults = document.getElementById('searchResults');

if (searchInput) {
    let debounce;
    searchInput.addEventListener('input', function () {
        clearTimeout(debounce);
        const q = this.value.trim();
        if (q.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        debounce = setTimeout(() => {
            fetch(`/accounts/search/?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.users.length === 0) {
                        searchResults.style.display = 'none';
                        return;
                    }
                    searchResults.innerHTML = data.users.map(u => `
                        <form method="post" action="/conversation/start/" class="search-result-item">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRF()}">
                            <input type="hidden" name="user_id" value="${u.id}">
                            <div class="avatar avatar-sm" style="background:${u.color}">${u.initials}</div>
                            <span>${u.username}</span>
                            <button type="submit" class="btn btn-sm btn-ghost" style="margin-left:auto">Chat</button>
                        </form>
                    `).join('');
                    searchResults.style.display = 'block';
                });
        }, 300);
    });

    document.addEventListener('click', (e) => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });
}
