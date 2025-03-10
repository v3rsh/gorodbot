(function() {
    // Убедимся, что функция spinWheel доступна
    if (typeof spinWheel === 'function') {
        // Создаем массив с индексами, исключая 2 и 8
        const availableIndices = [...Array(18).keys()].filter(index => index !== 2 && index !== 8);

        // Выбираем случайный индекс из оставшихся доступных
        const targetIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];

        // Записываем выбранный индекс в переменную bubble_fn_indexarea
        bubble_fn_indexarea(targetIndex);

        // Запускаем колесо на выбранный сектор
        spinWheel(targetIndex);
    } else {
        console.error("Ошибка: функция spinWheel не найдена.");
    }
})();
