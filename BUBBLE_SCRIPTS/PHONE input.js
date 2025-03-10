(function() {
    // Получаем номер телефона, введенный пользователем, из входного параметра
    let phoneNumber = properties.param1;
  
    // Удаляем все символы, кроме цифр и плюса
    phoneNumber = phoneNumber.replace(/[^\d+]/g, '');
  
    // Инициализируем переменную для хранения результата
    let result = 'error';
  
    // Проверка на соответствие формату и преобразование
    if (phoneNumber.length === 11 && phoneNumber.startsWith('7') && phoneNumber[1] === '9') {
      // Если длина 11 символов, начинается с 7 и за ней идет 9, номер корректный
      result = phoneNumber;
    } else if (phoneNumber.length === 10 && phoneNumber.startsWith('9')) {
      // Если длина 10 символов и начинается с 9, добавляем 7 в начало
      result = '7' + phoneNumber;
    } else if (phoneNumber.length === 11 && phoneNumber.startsWith('+7') && phoneNumber[2] === '9') {
      // Если длина 11 символов и начинается с +79, убираем +
      result = phoneNumber.slice(1);
    } else if (phoneNumber.length === 11 && phoneNumber.startsWith('8') && phoneNumber[1] === '9') {
      // Если длина 11 символов и начинается с 89, заменяем на 79
      result = '7' + phoneNumber.slice(1);
    }
  
    // Возвращаем результат в Bubble
    bubble_fn_phoneinput(result);
  })();
  