showWheel()

(function waitForFunctions() {
    if (typeof spinWheel === 'function' && typeof bubble_fn_spinbutton_ready === 'function' && typeof bubble_fn_indexarea === 'function') {
        // Все необходимые функции доступны, устанавливаем bubble_fn_spinbutton_ready в true
        bubble_fn_spinbutton_ready(true);
    } else {
        // Функции еще не доступны, проверяем снова через 100 миллисекунд
        setTimeout(waitForFunctions, 100);
    }
})();
