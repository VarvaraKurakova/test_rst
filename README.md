# Асинхронный сервис конфигурирования оборудования

Этот проект реализует асинхронную службу конфигурирования оборудования, используя **FastAPI** и **RabbitMQ**.
---

## Структура проекта

- `main.py` — приложение FastAPI с двумя основными конечными точками и имитатором сервиса
- `worker.py` — фоновый рабочий, обрабатывающий сообщения от RabbitMQ
- `tests/test_api.py` - интеграционный тест
- `Dockerfile`, `docker-compose.yml` - настройка контейнеризации
- `.github/workflows/ci.yml` - конвейер действий GitHub
- `ansible/` - плейбук и инвентарь Ansible

---

## Запуск приложения с помощью Docker

```bash
docker-compose up --build
```

Сервис будет доступен по адресу `http://localhost:8000`.

---

## Запуск рабочего (вручную)

В отдельном терминале (с активным окружением):

```bash
python worker.py
```

Или внутри контейнера, если необходимо.

---

## Запуск интеграционных тестов

```bash
pytest tests/
```

---

## Обзор API

### POST `/api/v1/equipment/cpe/{device_id}`.

Запускает асинхронную задачу инициализации.

**Request JSON**:
```json
{
  "timeoutInSeconds": 60,
  "parameters": {
    "username": "admin",
    "password": "admin",
    "vlan": 100,
    "interfaces": [1, 2]
  }
}
```

**Response**:
```json
{
  "code": 200,
  "taskId": "..."
}
```

---

### GET `/api/v1/equipment/cpe/{device_id}/task/{taskId}`

Возвращает статус задачи:
- `200 OK` - выполнено
- `204` - еще выполняется
- `500` - не удалось
- `404` - не найдено

---

## Макет службы A

Монтируется под `/service-a`

**Endpoint**: `POST /service-a/mock/equipment/cpe/{device_id}`

Имитирует медленную операцию с 60-секундной задержкой. Может возвращать:
- `200 OK`
- `500`, если `device_id` начинается с `fail`
- `404`, если `device_id` начинается с `notfnd`.

---

## Развертывание Ansible

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

---

## CI/CD

GitHub Actions will:
- Запустить RabbitMQ
- Установить зависимости
- Запускать тесты при каждом push в `main`

---

## Примечания

- `TASKS` хранятся в памяти (могут быть перенесены в DB)
- HTTPS и логика повторных попыток могут быть добавлены
- Для производства требуется соответствующий менеджер процессов и обратный прокси (например, nginx)
