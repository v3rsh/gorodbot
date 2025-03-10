(function() {
    // Динамически создаем тег <script> для подключения библиотеки Telegram Web Apps API
    var script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-web-app.js";
  
    // Ждем загрузки библиотеки и выполняем код
    script.onload = function() {
      // Убедимся, что WebApp готов к использованию
      Telegram.WebApp.ready();
  
      // Получаем все данные, доступные из WebView
      const userDataUnsafe = Telegram.WebApp.initDataUnsafe;
  
      // Выводим все полученные данные в консоль для диагностики
      console.log("Полные данные initDataUnsafe:", userDataUnsafe);
  
      if (userDataUnsafe && userDataUnsafe.user) {
        // Проверяем наличие user_id
        if (!userDataUnsafe.user.id) {
          console.error("Ошибка: user_id не найден.");
        } else {
          // Сохраняем данные пользователя в JSON формате
          const userdata = {
            value: userDataUnsafe.user.username,
            output1: userDataUnsafe.user.id,
            output2: userDataUnsafe.user.first_name,
            output3: userDataUnsafe.user.last_name
   };
  
          // Выводим результат в консоль для проверки
          console.log("Данные пользователя:", JSON.stringify(userdata));
  
          // Передаем объект userdata в Bubble функцию
          bubble_fn_userData(userdata);
        }
      } else {
        console.error("Ошибка: Данные о пользователе не получены.");
      }
    };
  
    // Добавляем тег script в head документа
    document.head.appendChild(script);
  })();
  