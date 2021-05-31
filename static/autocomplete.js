// Подключает "autocomplete" к полю ввода `inp`.
// Для "подсказок" используется список строк `arr`.
function autocomplete(inp, arr, getTextFunc, setTextFunc) {
  // На каком элементе списка находится фокус.
  var currentFocus;

  if (!getTextFunc)
    getTextFunc = function(ctrl) {
      return ctrl.value;
    };

  if (!setTextFunc)
    setTextFunc = function(ctrl, value) {
      ctrl.value = value;
    };

  // Обработчик клика где-либо в документе.
  document.addEventListener("click", function (e) {
    // Закрываем все открытые выпадающие меню.
    closeAllMenus(e.target);
  });

  // Обработчик ввода текста в поле.
  inp.addEventListener("input", function(e) {
    var text = getTextFunc(e.target);
    if (!text)
      return false;

    closeAllMenus();

    currentFocus = -1;

    var items = [];
    for (i = 0; i < arr.length; i++) {
      // Заполняем массив `items` элементами,
      // начало которых совпадает с введенным текстом.
      var prefix = arr[i].substr(0, text.length);
      if (prefix.toUpperCase() == text.toUpperCase()) {
        items.push(arr[i]);
      }
    }

    if (items.length == 0)
        return false;

    // Создаем выпадающее меню.
    menuList = document.createElement("ul");
    menuList.setAttribute("class", "dropdown-menu");
    menuList.setAttribute("id", this.id + "-dropdown-menu");

    this.parentNode.insertBefore(menuList, this.nextSibling);

    for (i = 0; i < items.length; i++) {
      // Заполняем выпадающее меню.
      var prefix = items[i].substr(0, text.length);

      menuItem = document.createElement("li");
      menuItem.setAttribute("class", "dropdown-item");
      menuItem.setAttribute("value", items[i]);

      menuItem.innerHTML = "<strong>" + prefix + "</strong>";
      menuItem.innerHTML += items[i].substr(text.length);

      menuItem.addEventListener("click", function(e) {
        // При клике по элементу, переносим его содержимое
        // в поле ввода и закрываем список.
        setTextFunc(inp, this.getAttribute("value"));
        closeAllMenus();
      });

      menuList.appendChild(menuItem);
    }

    menuList.style.display = "block";
  });

  // Обработчик нажатия кнопок в поле ввода.
  inp.addEventListener("keydown", function(e) {
      var menuList = document.getElementById(this.id + "-dropdown-menu");

      if (!menuList)
        return false;

      menuItems = menuList.getElementsByTagName("li");

      if (e.keyCode == 40) {
        // Курсор вниз. Блокируем передачу в форму,
        // чтобы курсор в поле ввода не менял положение.
        e.preventDefault();
        currentFocus++;
        setActive(menuItems);
      } else if (e.keyCode == 38) {
        // Курсор вверх. Блокируем передачу в форму,
        // чтобы курсор в поле ввода не менял положение.
        e.preventDefault();
        currentFocus--;
        setActive(menuItems);
      } else if (e.keyCode == 13) {
        // Нажатие Enter. Блокируем передачу Enter в форму,
        // чтобы она не закрылась.
        e.preventDefault();
        if (currentFocus > -1) {
          if (menuItems) {
            // Переносим его содержимое элемента
            // в поле ввода и закрываем список.
            setTextFunc(inp, menuItems[currentFocus].getAttribute("value"));
            closeAllMenus();
          }
        }
      } else if (e.keyCode == 9) {
        // Нажатие Tab. Закрываем список.
        closeAllMenus();
      }
  });

  // Активирует пункт списка с индексом currentFocus.
  function setActive(menuItems) {
    if (!menuItems)
      return;

    for (var i = 0; i < menuItems.length; i++) {
      menuItems[i].classList.remove("active");
    }

    if (currentFocus >= menuItems.length)
      currentFocus = 0;
    if (currentFocus < 0)
      currentFocus = (menuItems.length - 1);

    menuItems[currentFocus].classList.add("active");
  }

  function closeAllMenus() {
    // Находим в документе все блоки .dropdown-menu и удаляем их.
    var menus = document.getElementsByClassName("dropdown-menu");
    for (var i = 0; i < menus.length; i++) {
      menus[i].parentNode.removeChild(menus[i]);
    }
  }
}
