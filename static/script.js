document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.card .data-value');
    cards.forEach(card => {
        const target = parseFloat(card.textContent.replace('R$', '').replace(/\./g, '').replace(',', '.')); // Remover 'R$', substituir ',' por '.', remover '.' milhares
        const increment = target / 100; // Incremento calculado em 100 passos
        let current = 0;
        card.classList.add('counting'); // Adiciona classe 'counting' para mudar a cor durante a contagem
        const timer = setInterval(function() {
            current += increment;
            card.textContent = 'R$ ' + current.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); // Formatar como moeda brasileira
            if (current >= target) {
                clearInterval(timer);
                card.textContent = 'R$ ' + target.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); // Formatar como moeda brasileira
                card.classList.remove('counting'); // Remove classe 'counting' após a contagem ser concluída
            }
        }, 60); // Intervalo de atualização em milissegundos
    });
});