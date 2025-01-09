## Запуск проекта

### Требования

- Python 3.8+
- Установленные зависимости из `requirements.txt` (FastAPI, Uvicorn)

### Установка

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/softskate/test_parser.git
    cd task-manager-api
    ```

2. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

3. Запустите сервер:
    ```bash
    uvicorn app:app --reload
    ```

4. После завершения всех задач сводка доступна по `/summary`.
    ```bash
    curl -X GET http://127.0.0.1:8000/summary
    ```
