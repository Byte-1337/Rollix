
let profitChart;
function updateChart(profitValues) {
    const ctx = document.getElementById('profit-chart').getContext('2d');
    if (profitChart) profitChart.destroy();
    profitChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: profitValues.map((_, i) => i + 1),
            datasets: [{
                label: 'Profit per Move',
                data: profitValues,
                borderColor: 'lime',
                backgroundColor: 'rgba(0,255,0,0.2)',
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}
