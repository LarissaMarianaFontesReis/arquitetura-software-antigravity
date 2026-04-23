const moneyFormat = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

async function initDashboard() {
    const loader = document.getElementById('global-stats');
    loader.textContent = "Buscando Ofertas...";

    try {
        const variantsRes = await fetch('/api/variants');
        const variants = await variantsRes.json();
        
        loader.innerHTML = `Monitorando <span style="color:var(--accent-secondary)">${variants.length}</span> Peças na Cesta`;
        
        const grid = document.getElementById('dashboard-grid');
        grid.innerHTML = '';
        
        for (const variant of variants) {
            fetchStats(variant, grid);
        }

    } catch (err) {
        loader.textContent = "Erro grave de conexão.";
        console.error(err);
    }
}

async function fetchStats(variant, gridContainer) {
    try {
        const res = await fetch(`/api/history?variant=${encodeURIComponent(variant)}`);
        const stats = await res.json();
        
        if (stats.error) return;
        renderCard(stats, gridContainer);
        
    } catch(err) {
        console.error("Falha", variant, err);
    }
}

function renderCard(stats, container) {
    const card = document.createElement('div');
    card.className = 'card';
    
    let trendClass = 'trend-neutral';
    let trendIcon = '➖';
    let trendText = 'Pesquisando...';
    
    // Logica de Evolucao
    const prices = stats.timeline.map(t => parseFloat(t.price));
    if (prices.length >= 2) {
        const diff = prices[prices.length -1] - prices[prices.length -2];
        if (diff < 0) {
            trendClass = 'trend-down';
            trendIcon = '⏬';
            trendText = "Queda " + moneyFormat.format(Math.abs(diff));
        } else if (diff > 0) {
            trendClass = 'trend-up';
            trendIcon = '⏫';
            trendText = "Sobe " + moneyFormat.format(diff);
        } else {
            trendText = 'Estacionado';
        }
    }

    card.innerHTML = `
        <div class="card-header">
            <div class="header-wrapper">
                ${stats.latest_image_url ? `<img src="${stats.latest_image_url}" class="product-image" loading="lazy" alt="Foto">` : `<div class="product-image" style="display:flex;align-items:center;justify-content:center;font-size:24px;">📦</div>`}
                <h3 class="variant-title" style="margin-bottom:0;">${stats.variant.toUpperCase()}</h3>
            </div>
            <div class="price-row">
                <span class="current-price">${moneyFormat.format(stats.current_price)}</span>
                <span class="trend-badge ${trendClass}">${trendIcon} ${trendText}</span>
            </div>
        </div>
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-label">Menor Valor Histórico</div>
                <div class="metric-value" style="color: #22c55e">${moneyFormat.format(stats.lowest_historical_price)}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Pico (Max Oferta)</div>
                <div class="metric-value" style="color: #ef4444">${moneyFormat.format(stats.highest_historical_price)}</div>
            </div>
        </div>
        <div class="chart-container">
            <canvas id="chart-${stats.variant.replace(/\W/g, '')}"></canvas>
        </div>
        
        <!-- Botao de Compra -->
        <a href="${stats.latest_url || '#'}" target="_blank" class="buy-button">Ir à Loja</a>
    `;
    container.appendChild(card);
    
    renderChart(stats, `chart-${stats.variant.replace(/\W/g, '')}`);
}

function renderChart(stats, canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const labels = stats.timeline.map(t => {
        const date = new Date(t.timestamp);
        return `${date.getDate()}/${date.getMonth()+1}`;
    });
    const data = stats.timeline.map(t => parseFloat(t.price));
    
    // Gradiente Roxo Estilo Corporativo/Zoom
    let gradient = ctx.createLinearGradient(0, 0, 0, 150);
    gradient.addColorStop(0, 'rgba(87, 45, 145, 0.25)');
    gradient.addColorStop(1, 'rgba(87, 45, 145, 0.01)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: '#572d91', // Zoom Purple
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: (data.length > 1) ? 2 : 5, 
                pointBackgroundColor: '#ff5722', // Zoom orange points
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: {
                callbacks: { label: (ctx) => moneyFormat.format(ctx.raw) }
            }},
            scales: {
                x: { display: false },
                y: { display: false } 
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();
        const cards = document.querySelectorAll('.card');

        cards.forEach(card => {
            const titleElement = card.querySelector('.variant-title');
            if (titleElement) {
                const title = titleElement.textContent.toLowerCase();
                if (title.includes(term)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    setupSearch();
});
