# SMMplanner, отложенный постинг в VK, Facebook, Telegram

Источником информации является [Google таблица](https://docs.google.com/spreadsheets/d/17r4QRW_m0clut772bRnUL-U1-JiazImiZMm43SkgS9Q/edit#gid=0)

Скрипт анализирует Google таблицу и публикует пост в нужное время в нужном месте.


### Как установить

Для использования скрипта необходимо:

1. Создать группу [ВКонтакте](https://vk.com/).
2. Создать приложение  [ВКонтакте](https://vk.com/). Создать приложение можно в разделе [Мои приложения](https://vk.com/apps?act=manage). В качестве типа приложения следует указать `standalone` — это подходящий тип для приложений, которые просто запускаются на компьютере.
3. Получить `client_id` созданного приложения. Чтобы работать со своим приложением, надо знать его `client_id`. Иначе сервер не поймёт, от имени какого приложения вы хотите работать. Если нажать на кнопку "Редактировать" для нового приложения, в адресной строке вы увидите его `client_id`.
4. Получить личный ключ - `access token`. Он нужен для того, чтобы ваше приложение имело доступ к вашему аккаунту и могло публиковать сообщения в группах.  Вам потребуются следующие права: `scope=photos,groups,wall,offline`. Вы получите `access_token` — строку наподобие `533bacf01e1165b57531ad114461ae8736d6506a3`. Она появится в адресной строке, подписанная как `access_token`. При получении ключа вы увидите [такую страницу](https://dvmn.org/media/filer_public/0b/cd/0bcd3fe4-8eb9-404c-9684-e34ec03662d7/test.png). Список разрешений должен быть как на скриншоте. Так как вы используете `standalone` приложение, для получения ключа пользователя стоит использовать `Implicit Flow`. Параметр redirect_uri у запроса на ключ лучше убрать.
5. Зарегистрируйте бота в Telegram. Для этого напишите [Отцу ботов](https://telegram.me/BotFather). Используйте команды: `/start` и `/newbot`.
6. Получите свой `id` номер Telegram аккаунта, напишите в Telegram специальному боту: `@userinfobot`.
7. Для публикации в группе Facebook нужен API ключ доступа (маркер доступа пользователя). Получите ключ с правом `publish_to_groups` - [инструкция](https://developers.facebook.com/docs/graph-api/explorer/). Продлите [ключ доступа с 2-х часов до 2-х месяцев](https://developers.facebook.com/tools/debug/accesstoken/).
8. При работе с Google Sheets библиотека использует специальный файл `credentials.json` с ключами и правами доступа. Как сгенерировать файл описано в [Google Sheets Quickstart](https://developers.google.com/sheets/api/quickstart/python). Файл `credentials.json` кладите рядом с `manage.py`.
9. Для работы с API Google Drive используется библиотека PyDrive. При работе PyDrive необходим специальный файл `client_secrets.json` с ключами и правами доступа. Как сгенерировать файл описано в [Авторизация с PyDrive](https://gsuitedevs.github.io/PyDrive/docs/build/html/quickstart.html#authentication). Файл с ключами кладите рядом с `manage.py`. Без него библиотека PyDrive не работает. Не забудьте переименовать файл с ключами на название: `client_secrets.json`
10. Открыть полный доступ к Вашей Google таблице.

Скрипт берет часть данных из переменных окружения. Чтобы их определить создайте файл `.env` рядом с `manage.py` и запишите туда данные в таком формате: `ПЕРЕМЕННАЯ=значение`.

Доступны следующие переменные:
- `VK_LOGIN` - логин [ВКонтакте](https://vk.com/)
- `VK_PASSWORD` - пароль от аккаунта [ВКонтакте](https://vk.com/)
- `VK_ACCESS_TOKEN` - ключ доступа [ВКонтакте](https://vk.com/)
- `VK_GROUP_ID` - ID группы [ВКонтакте](https://vk.com/). Узнать можно [здесь](https://regvk.com/id/).
- `VK_ALBUM_ID` - ID альбома [ВКонтакте](https://vk.com/)
- `TELEGRAM_BOT_TOKEN` - API ключ Telegram бота;
- `TELEGRAM_CHAT_ID` - ID номер Вашего Telegram аккаунта;
- `FACEBOOK_USER_ID` - ID аккаунта пользователя [Facebook](https://www.facebook.com/)
- `FACEBOOK_APPLICATION_ID` - ID приложения [Facebook](https://www.facebook.com/)
- `FACEBOOK_GROUP_ID` - ID группы [Facebook](https://www.facebook.com/)
- `FACEBOOK_ACCESS_TOKEN` - ключ доступа [Facebook](https://www.facebook.com/)
- `SPREADSHEET_ID` - ID Google таблицы, например `1oAvZbb-CTcB1l7OG_3zUs73oNPz6YJgaWy7i3n2YRrM`. Можно посмотреть в адресной строке браузера.
- `RANGE_NAME` - диапазон ячеек таблицы (данные для работы скрипта), например `Лист1!A3:H` означает столбцы с A до H, начиная с 3-й строки.
- `ROW_START_NUMBER` - номер строки таблицы, с которой начинаются данные (первая строка после наименования столбцов).

Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, если есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```

### Как запустить скрипт

Команда запуска: `python manage.py`

Скрипт работает в бесконечном цикле. Когда настанет время, то пост опубликуется. Поле в колонке "Опубликовано?" сменится с "нет" на "да".

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).