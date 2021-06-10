// Возвращает значение указанной куки.
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Устанавливает обработчик клика по ссылке.
// isAuth - аутентифицирован ли пользователь
// itemCssClass - CSS-класс всех тегов, для которых
//                устанавливается обработчик
// getUrl - функция, возвращающая URL, по которому
//          посылается POST-запрос при клике
// onResponse - функция, полчающая результат POST-запроса
//              в JSON-виде
function setClickHandlers(isAuth, itemCssClass, getUrl, onResponse) {
  const csrftoken = getCookie('csrftoken');

  for (link of document.getElementsByClassName(itemCssClass)) {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      if (!isAuth)
        return;

      fetch(getUrl(this), {
            method: "POST",
            credentials: "same-origin",
            headers:{
              'Accept': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'X-CSRFToken': csrftoken,
            }})
        .then(response => {
          if (!response.ok)
            throw Error(response);

          return response.json();
        })
        .then(data => onResponse(this, data))
        .catch(error => { console.log(error);/* do nothing on error */ });
    }, true);
  }
}

// Обработка кликов для выбора "верного" ответа.
function setSolutionHandler(urlSet, urlClear, isAuth) {
  setClickHandlers(
    isAuth,
    "solution-mark",
    item => {
      const answerId = item.getAttribute("data-answer-id");
      const wasSolution = item.getAttribute("data-answer-solution") === "1";

      return (wasSolution ? urlClear : urlSet)
        .replace(/\/0\//, "/" + answerId + "/");
    },
    (item, json) => {
      const wasSolution = item.getAttribute("data-answer-solution") === "1";

      for (link of document.getElementsByClassName("solution-mark")) {
        const image = link.firstElementChild;

        if (!wasSolution && link === item) {
          link.setAttribute("data-answer-solution", "1");
          image.classList.remove("bi-star");
          image.classList.add("bi-star-fill");
        } else {
          link.setAttribute("data-answer-solution", "0");
          image.classList.add("bi-star");
          image.classList.remove("bi-star-fill");
        }
      }
    }
  );
}

// Обработка кликов для голосования за вопрос.
function setQuestionVotesHandler(urlVoteUp, urlVoteDown, isAuth) {
  setClickHandlers(
    isAuth,
    "question-vote",
    item => {
      const isVoteUp = item.getAttribute("data-is-vote-up") === "1";
      return isVoteUp ? urlVoteUp : urlVoteDown;
    },
    (item, json) => {
      document.getElementById("votes-num").textContent = json.votes;
    }
  );
}

// Обработка кликов для голосования за ответы.
function setAnswersVotesHandler(urlVoteUp, urlVoteDown, isAuth) {
  setClickHandlers(
    isAuth,
    "answer-vote",
    item => {
      const answerId = item.getAttribute("data-answer-id");
      const isVoteUp = item.getAttribute("data-is-vote-up") === "1";

      return (isVoteUp ? urlVoteUp : urlVoteDown)
        .replace(/\/0\//, "/" + answerId + "/");
    },
    (item, json) => {
      item.parentElement
        .getElementsByClassName("votes-num")[0]
        .textContent = json.votes;
    }
  );
}
