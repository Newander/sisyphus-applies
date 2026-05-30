# Local Job Search Tracker

Локальное single-user приложение для отслеживания поиска работы через Gmail и Google Calendar.

## MVP scope

- Ручное добавление вакансий и откликов.
- Импорт писем из Gmail.
- Извлечение базовых фактов из писем без AI: отправитель, тема, дата, ссылки, вложения, цепочка писем.
- Связывание писем с компаниями, вакансиями и откликами.
- Импорт событий из Google Calendar и привязка интервью к откликам.
- Дашборд по статусам, датам подачи, времени без ответа и ближайшим событиям.
- Локальное хранение данных на компьютере пользователя.

## Out of scope for now

- Авторизация внутри приложения.
- Многопользовательский режим.
- Облачное хранение.
- Автоматическая подача на вакансии через сайты рекрутинга.
- AI-извлечение информации из писем. Это long-lasting feature на будущие итерации.

## Documentation

- [Зафиксированный стек](docs/tech-stack.md)
- [Нужные навыки и зоны компетенций](docs/skills.md)
- [Roadmap разработки](docs/roadmap.md)

## Local run

1. Настроить PostgreSQL credentials в `.env` (см. `.env.example`).
2. При необходимости задать папку документов:

   - Linux/macOS: `JOB_TRACKER_STORAGE_DIR=/home/<user>/JobTracker`
   - Windows: `JOB_TRACKER_STORAGE_DIR=C:\Users\<user>\Documents\JobTracker`

3. Установить зависимости, применить миграции, запустить процессы.

### Linux / macOS

```bash
./scripts/install-backend.sh
./scripts/install-frontend.sh
./scripts/init-db.sh
./scripts/start-all.sh
```

`start-all.sh` поднимает backend, worker и frontend в фоне, логи пишет в `logs/`. Ctrl+C останавливает все три.

Заполнить локальную БД тестовыми данными:

```bash
./scripts/seed-data.sh
```

### Windows (PowerShell)

```powershell
.\scripts\install-backend.ps1
.\scripts\install-frontend.ps1
.\scripts\init-db.ps1
.\scripts\start-all.ps1
```

Тестовые данные:

```powershell
.\scripts\seed-data.ps1
```

Frontend будет доступен на `http://localhost:3000`, backend API на `http://127.0.0.1:8000`.

## Gmail

Gmail integration использует локальный OAuth Desktop App flow и scope `gmail.readonly`.

Локальные файлы:

- `credentials/client_secret.json` — OAuth client secret из Google Cloud Console.
- `credentials/gmail_token.json` — локальный token после подключения.

Подключить Gmail:

```bash
# Linux / macOS
./scripts/connect-gmail.sh
```

```powershell
# Windows
.\scripts\connect-gmail.ps1
```

Запустить ручную синхронизацию:

```bash
# Linux / macOS
./scripts/sync-gmail.sh
```

```powershell
# Windows
.\scripts\sync-gmail.ps1
```

Страница Gmail в интерфейсе:

```text
http://localhost:3000/gmail
```

## Codex bridge

Страница локального бриджа:

```text
http://localhost:3000/codex
```

Backend endpoint `POST /api/codex/ask` запускает локальный Codex CLI из корня проекта,
передает вопрос через stdin и возвращает stdout. Поддерживаются два режима:

- `text` — передать в Codex текстовый контекст напрямую.
- `url` — сначала снять видимый текст со страницы по ссылке, затем передать его в Codex.

Команда настраивается через `.env`:

```dotenv
CODEX_CLI_COMMAND=codex
CODEX_CLI_ARGS=exec -
CODEX_CLI_TIMEOUT_SECONDS=120
CODEX_BRIDGE_PROMPT_FILE=backend/prompts/codex_bridge.md
CODEX_JOB_EXTRACTION_PROMPT_FILE=backend/prompts/job_post_extraction.md
```

На Windows, если не разрешено запускать packaged `codex.exe` из `WindowsApps`,
укажи в `CODEX_CLI_COMMAND` путь к рабочему CLI или PowerShell wrapper.

Промпт для страницы `/codex` лежит в `backend/prompts/codex_bridge.md`, промпт для
извлечения данных вакансии из текста страницы — в `backend/prompts/job_post_extraction.md`.
