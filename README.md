# Авиахакатон. Решение команды Collapse на трек МТС

В данном репозитории находится решение команды Collabse. Никакие наработки до хакатона не использовались, продукт был создан только за время хакатона

## Содержание

- [Авиахакатон. Решение команды Collapse на трек МТС](#авиахакатон-решение-команды-collapse-на-трек-мтс)
  - [Содержание](#содержание)
  - [Описание решения](#описание-решения)
  - [Инструкция по запуску](#инструкция-по-запуску)
    - [Локальный запуск](#локальный-запуск)
  - [Архитектура](#архитектура)
  - [Паттерны и Референсная Архитектура](#паттерны-и-референсная-архитектура)
    - [Референсная Архитектура](#референсная-архитектура)
    - [Паттерны](#паттерны)
  - [Описание модели машинного обучения](#описание-модели-машинного-обучения)
    - [Статистическая обработка](#статистическая-обработка)
    - [Рекуррентная Нейронная Сеть](#рекуррентная-нейронная-сеть)
  - [Результаты тестов модели](#результаты-тестов-модели)
  - [Контакты](#контакты)

## Описание решения

Нашим решением является веб портал с наиболее актуальной информацией. На нем можно осуществить следующие действия:

- Запуск модели со своими данными и генерация графиков
- Возможность создания новых графиков на основе старого с измененными параметрами
- Анализ качества общей утилизации складов

[Видео о продукте](https://www.renderforest.com/ru/watch-67051383?queue_id=64976292&quality=720)

## Инструкция по запуску

Фронтенд публично нашегоо сервиса доступен по ссылкам соответственно:

  4.231.226.222:8080

  4.231.226.222:8090

Однако, есть возможность развернуть локально.

### Локальный запуск

Перед тем, как развернуть у себя сервис необходим [Docker](https://docs.docker.com/get-docker/) и [Docker Commpose](https://docs.docker.com/compose/install).

Если требование выполнено, то выполните 3 простых действия:

1. Склонируйте этот репозиторий
2. Зайдите в корневую директорию проекта и запустите следующую команду:

    docker-compose up -d
3. Используйте развернутые приложения
   - **frontend:8080** - адрес фронтенда
   - **server:8090** - адрес сервиса отправки в RabbitMQ
   - **database:27017-27019** - адрес базы данных
   - **broker:15672** - адрес RabbitMQ

## Архитектура

На диаграмме ниже можно посмотреть на верхнеуровневую архитектуру нашего сервиса. Давайте пройдем по шагам в соответствии с нумерацией диаграммы:

![Архитектура](readme-assets/Архитектура.png)

- **Шаг 1**. Пользователь (предположительно аналитик или внешний стейнхолдер) обращается в наше веб приложение, которое было развернуто на виртуальной машине с ипользованием **Docker Commpose**. Пользователь взаимодействует с веб интерфейсом на HTML/CSS/JS с применением Bootstrap.
- **Шаг 2**. Если пользователь хочет запустить модель со своими данными, то сервис **создает новый объект со статусом "initiated" (инициализирован) в базе данных(MongoDB) через REST запрос** к этой базе и **записывает его название в локальный кеш** (он будет нужен в шаге 6). Данные пользователя не отправляются.
- **Шаг 3**. После отправления данных этот же сервис **передает полученные данные в RabbitMQ**.
- **Шаг 4**. Обработчик событий (worker) уведомляется о новом запросе в RabbitMQ и **вызывает модель статистического анализа**, которая в свою очередь передает полученные результаты на вход к **рекуррентной нейронной сети (RNN)**. Более того, этот же worker отправляет **REST запрос в базу данных об изменении статуса** объекта на **"in progress"** (в процессе создания)
- **Шаг 5**. Как только модель вернула данные для графиков, worker **отправляет эти данные в MongoDB через REST запрос**. Помимо этого, статус объекта меняется на **"done"** (закончен).
- **Шаг 6**. В фоновом режиме веб сервис опрашивает базу данных через REST запрос о статусе элементов, которые были созданы, но не закончены. Если элемент из локального кеша получил статус "done", то тогда он **удаляется из кеша**.

## Паттерны и Референсная Архитектура

В рамках работы над прототипом были учтены лучшие практики построения подобных решений. В качестве главного архитектурного принципа были выбрана несколько:

- **Обеспечить минимальное время ожидания для пользователя**
- **Необходимость отделить бизнес логику веб сервиса от ресурсоемких задач Машинного Обучения**

В этой связи мы опираемся на референсные архитектуры ведущих ИТ компаний, а также используем общеприщнанные паттерны, проверенные временем.

### Референсная Архитектура

В качестве референсных архитектур мы взяли подход IBM в построении решений [AI for IT Operations (AIOps)](https://www.ibm.com/cloud/architecture/architectures/sm-aiops/reference-architecture), из которого мы поняли, что шаги 1-7 и разбиение процесса на этапы (Collect, Organize, Analyze, Infuse) соответствуют нашим потребноостям.

### Паттерны

Что касается паттернов, то мы используем два довольно популярных паттерна:

- [Микросервисная архитектура](https://microservices.io/patterns/microservices.html). Каждый сервис может быть развернут отдельно, а большинство коммуникаций - через REST API запросы.
- [Database per service](https://microservices.io/patterns/data/database-per-service.html). Поскольку база данных используется в нескокльких местах, мы приняли решение выделить отдельный микросервис для обспечения Create, Read, Update, Delete (CRUD) запросов
  
## Описание модели машинного обучения

Наша модель отвечает за два этапы Organize и Analyze из [референсной архитектуры](#референсная-архитектура). Работа над данными проходит в 3 этапа. В начале определяется начальная дата отсчета для анализа обьемов скаладского помещения в зависимости от планов постройки базовых станций. С помощью additive regression model на базе Prohet(Facebook), мы проводим анализ временных рядов для общей загрузки складов и обьема под обработку. Далее для начальной даты отсчета мы определяем с помощью модели изначальную загрузку склада. Далее мы [статистически организовываем данные](#статистическая-обработка), получая прогноз на фактические даты постройки базовых станций для каждого региона. А далее производим анализ с помощью [Рекурретной нейронной сети (RNN)](#рекуррентна-нейронная-сеть) и получаем дальнейший прогноз по предполагаемой загрузке региона в зависимости от изначального плана постройки БС.
Также мы с помощью Prohet и RNN провели анализ текущих данных по загрузке склада, и представили общие прогнозы для загрузки и места под обработку на 1, 3, 9 месяцев от 30 сентября 2022 года.

### Статистическая обработка

В качестве входных параметров используются **данные о базовых станциях**, которые мы обрабатываем данные о **расходных операциях и отгрузках со склада** и генерируем **оптимальную отгрузку/загрузку по складу соответственно проценту средней отгрузки/загрузки по дням**. Также начальная загрузка склада берется из additive regression model. Итого, этот процесс выглядит следующим образом:

1. Берем общую отгрузку с конкретного склада за месяц.
2. Смотрим плановое кол-во постройки Базовых станция за этот месяц.
3. Из п. 1 и 2 получаем для каждого склада для каждого месяца среднее значение обьема для одной базовой станции.
4. Усредняем и получаем среднее значение объёма одной базовой станции для каждого склада.
5. Смотрим в какие дни недели на склад активнее доставляли, в какие отправляли, и далее распределяем эту общую отгрузку/загрузку по складу соответственно проценту средней отгрузки/загрузки по дням (ну и раньше даты постройки объекта , конечно же).

### Рекуррентная Нейронная Сеть

В качестве подготовки данных для Нейронной Сети мы размножили текущие временные ряды на множество подсемплов с меньшей длинной. На их основании мы обучили несколько нейронных сетей разных архитектур и протестировали их. На основе тестов наибольшую эффективность показала рекуррентная нейронная сеть на архитектуре LSTM.

![Рекуррентная Нейронная Сеть](readme-assets/model_selection.png)

Далее мы обучили (на основе архитектуры LSTM) модель для предсказания загрузки склада на следующий месяц (3, 6, 9, 12) будут чуть позже. В нее поступает временной ряд и она на его основе предоставляет следующие значения. График обучения ниже:

![Рекуррентная Нейронная Сеть](readme-assets/model_training.png)

Среднее отклонение по Rmse не превышает 800, что не провосходит заявленные критические 8% отклонения.

![Рекуррентная Нейронная Сеть](readme-assets/test.png)


## Результаты тестов модели

**Предсказания модели:**

**Предсказания общего обьема хранилища**

- Синий - выборка использовалась при обучении модели
- Желтый - выборка не использовалась при обучении модели
- Зеленый - результат предсказаний


![Результаты тестов модели](readme-assets/Hran.png)


**Предсказания общего обьема Обработки**

- Синий - выборка использовалась при обучении модели
- Желтый - выборка не использовалась при обучении модели
- Зеленый - результат предсказаний


![Результаты тестов модели](readme-assets/Obr.png)

## Контакты

В случае возникновения каких-либо ошибок или вопросов не стесняйтесь создавать Issue в репозитории. Также можете писать в личные сообщения@ilya_2108 (Telegram, VK) или на почту ilya210819993@gmail.com
