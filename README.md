# Как запустить
1. Настройка переменных окружения
```bash
cp .env.example .env
```
2. Запуск всех сервисов
```bash
docker-compose up -d --build
```
3. Миграции
```bash
docker-compose exec backend alembic upgrade head
```
4. Загрузка тестовых данных
```bash
docker-compose exec backend python -m app.seed
```
