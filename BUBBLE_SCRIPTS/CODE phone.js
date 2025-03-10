// Генерация случайного 4-значного кода от 0000 до 9999
function generatePhoneCode() {
    let code = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    
    // Передаем сгенерированный код в Bubble функцию
    bubble_fn_phonecode(code);
  }
  
  // Запуск функции генерации кода
  generatePhoneCode();
  