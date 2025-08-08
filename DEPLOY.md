# 🚀 Деплой Plants Bot на Ubuntu сервер

Подробная инструкция по развертыванию бота для распознавания растений на Ubuntu сервере с Docker.

## 📋 Предварительные требования

- Ubuntu сервер с установленным Docker и Docker Compose
- Доступ к серверу по SSH
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- OpenAI API Key (получить на [OpenAI Platform](https://platform.openai.com/))

## 🔧 Способ 1: Автоматическая установка (рекомендуется)

### Быстрая установка одной командой:

```bash
curl -fsSL https://raw.githubusercontent.com/mmizmaylov/plants-bot/main/deploy/setup-ubuntu-docker.sh | bash -s -- \
  --repo-url https://github.com/mmizmaylov/plants-bot.git \
  --telegram-token "YOUR_TELEGRAM_BOT_TOKEN" \
  --openai-key "YOUR_OPENAI_API_KEY" \
  --model "gpt-4o-mini"
```

**Замените:**
- `YOUR_TELEGRAM_BOT_TOKEN` — на токен вашего Telegram бота
- `YOUR_OPENAI_API_KEY` — на ваш OpenAI API ключ

### Что делает скрипт:
1. Устанавливает Docker (если не установлен)
2. Клонирует репозиторий в `/opt/plants-bot`
3. Создает файл `.env` с вашими токенами
4. Запускает бота через Docker Compose

## 🔧 Способ 2: Ручная установка

### 1. Подключитесь к серверу:
```bash
ssh your-user@your-server-ip
```

### 2. Клонируйте репозиторий:
```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/mmizmaylov/plants-bot.git
cd plants-bot
```

### 3. Создайте файл конфигурации:
```bash
sudo tee .env > /dev/null <<EOF
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_VISION_MODEL=gpt-4o-mini
EOF
```

### 4. Запустите бота:
```bash
sudo docker compose up -d --build
```

## 📊 Управление ботом

### Просмотр логов:
```bash
# Логи в реальном времени
sudo docker compose -f /opt/plants-bot/docker-compose.yml logs -f

# Последние 100 строк логов
sudo docker logs plants-bot --tail 100

# Логи за последний час
sudo docker logs plants-bot --since 1h
```

### Перезапуск бота:
```bash
cd /opt/plants-bot
sudo docker compose restart
```

### Остановка бота:
```bash
cd /opt/plants-bot
sudo docker compose down
```

### Обновление бота:
```bash
cd /opt/plants-bot
sudo git pull
sudo docker compose up -d --build
```

### Проверка статуса:
```bash
# Статус контейнера
sudo docker ps --filter name=plants-bot

# Использование ресурсов
sudo docker stats plants-bot --no-stream
```

## 🔄 Запуск вместе с nutrition-bot

Если у вас уже запущен nutrition-bot, plants-bot можно запустить параллельно:

### 1. Убедитесь что nutrition-bot использует другой порт (если нужно):
```bash
# Проверьте какие порты заняты
sudo docker ps
```

### 2. Запустите plants-bot:
```bash
cd /opt/plants-bot
sudo docker compose up -d --build
```

### 3. Проверьте что оба бота работают:
```bash
sudo docker ps --filter name=bot
```

Должны увидеть:
```
CONTAINER ID   IMAGE                    NAMES
xxxxxxxxx      plants-bot_bot           plants-bot
yyyyyyyyy      nutrition-bot_bot        nutrition-bot
```

## 🛠 Настройка systemd сервиса (опционально)

Для автоматического запуска при перезагрузке сервера:

### 1. Скопируйте файл сервиса:
```bash
sudo cp /opt/plants-bot/deploy/plants-bot.service /etc/systemd/system/
```

### 2. Создайте файл окружения:
```bash
sudo tee /etc/plants-bot.env > /dev/null <<EOF
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_VISION_MODEL=gpt-4o-mini
EOF
```

### 3. Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable plants-bot
sudo systemctl start plants-bot
```

### 4. Проверьте статус:
```bash
sudo systemctl status plants-bot
```

## 🔍 Диагностика проблем

### Бот не запускается:
```bash
# Проверьте логи
sudo docker logs plants-bot

# Проверьте конфигурацию
sudo cat /opt/plants-bot/.env

# Проверьте что токены корректные
sudo docker run --rm --env-file /opt/plants-bot/.env plants-bot_bot python -c "import os; print('TELEGRAM_BOT_TOKEN:', 'OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING'); print('OPENAI_API_KEY:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')"
```

### Бот не отвечает:
```bash
# Проверьте что контейнер запущен
sudo docker ps --filter name=plants-bot

# Перезапустите бота
cd /opt/plants-bot
sudo docker compose restart

# Проверьте логи на ошибки
sudo docker logs plants-bot --tail 50
```

### Проблемы с памятью:
```bash
# Проверьте использование ресурсов
sudo docker stats plants-bot --no-stream

# Ограничьте память (добавьте в docker-compose.yml):
# deploy:
#   resources:
#     limits:
#       memory: 512M
```

## 🔐 Безопасность

### 1. Защитите файл с токенами:
```bash
sudo chmod 600 /opt/plants-bot/.env
sudo chown root:root /opt/plants-bot/.env
```

### 2. Настройте firewall (если нужно):
```bash
# Разрешите только SSH
sudo ufw allow ssh
sudo ufw enable
```

### 3. Регулярно обновляйте систему:
```bash
sudo apt update && sudo apt upgrade -y
```

## 📈 Мониторинг

### Простой мониторинг через cron:
```bash
# Добавьте в crontab для проверки каждые 5 минут
sudo crontab -e

# Добавьте строку:
*/5 * * * * docker ps --filter name=plants-bot --filter status=running -q | grep -q . || (cd /opt/plants-bot && docker compose up -d)
```

## ❓ Полезные команды

```bash
# Посмотреть размер логов
sudo du -sh /var/lib/docker/containers/*/

# Очистить старые Docker образы
sudo docker system prune -a

# Бэкап конфигурации
sudo tar -czf plants-bot-backup-$(date +%Y%m%d).tar.gz -C /opt plants-bot/.env

# Проверить версию Docker
sudo docker --version
sudo docker compose version
```

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo docker logs plants-bot`
2. Убедитесь что токены корректные
3. Проверьте доступ к интернету на сервере
4. Создайте issue в [репозитории](https://github.com/mmizmaylov/plants-bot/issues)

---

**Удачного деплоя!** 🌿🚀 