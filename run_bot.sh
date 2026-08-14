#!/usr/bin/env bash
set -Eeuo pipefail

# Interactive launcher for a VPS or local terminal.
# Secrets are kept only in this process environment and are never written to disk.
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIR="$ROOT_DIR/bots/telegram-bot"
VENV_DIR="$BOT_DIR/.venv"

if [[ -x "$VENV_DIR/bin/python" ]]; then
    PYTHON="$VENV_DIR/bin/python"
else
    PYTHON="$(command -v python3.11 || command -v python3 || true)"
    if [[ -z "$PYTHON" ]]; then
        echo "Ошибка: нужен Python 3.11 или новее." >&2
        exit 1
    fi
fi

python_version="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python_major="${python_version%%.*}"
python_minor="${python_version#*.}"
if (( python_major < 3 || (python_major == 3 && python_minor < 11) )); then
    echo "Ошибка: найден Python $python_version, нужен Python 3.11 или новее." >&2
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "Первый запуск: создаю виртуальное окружение..."
    if ! "$PYTHON" -m venv "$VENV_DIR"; then
        echo "Ошибка: не удалось создать venv. Установите пакет Python venv (например, python3.11-venv) и повторите." >&2
        exit 1
    fi
fi

PYTHON="$VENV_DIR/bin/python"
if ! "$PYTHON" -c "import aiogram, dotenv" >/dev/null 2>&1; then
    echo "Устанавливаю зависимости бота..."
    PIP_USER=0 "$PYTHON" -m pip install --disable-pip-version-check --upgrade pip
    PIP_USER=0 "$PYTHON" -m pip install --disable-pip-version-check --no-user -r "$BOT_DIR/requirements.txt"
fi

if [[ -z "${BOT_TOKEN:-}" ]]; then
    printf "Введите BOT_TOKEN от @BotFather (ввод скрыт): "
    read -r -s BOT_TOKEN
    printf "\n"
fi
if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    echo "Ошибка: BOT_TOKEN выглядит некорректно." >&2
    exit 1
fi

if [[ -z "${ADMIN_IDS:-}" ]]; then
    read -r -p "Telegram ID администраторов через запятую [7307275806,1038562411]: " ADMIN_IDS
    ADMIN_IDS="${ADMIN_IDS:-7307275806,1038562411}"
fi
if [[ ! "$ADMIN_IDS" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
    echo "Ошибка: ADMIN_IDS должен содержать числовые Telegram ID через запятую." >&2
    exit 1
fi

if [[ -z "${SHOP_NAME:-}" ]]; then
    read -r -p "Название магазина [veachelsell]: " SHOP_NAME
    SHOP_NAME="${SHOP_NAME:-veachelsell}"
fi

export BOT_TOKEN ADMIN_IDS SHOP_NAME
cd "$BOT_DIR"
exec "$PYTHON" main.py