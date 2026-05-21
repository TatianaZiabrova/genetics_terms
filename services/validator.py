import re


class ValidationError(Exception):
    pass


BANNED_KEYWORDS = {
    # Единицы измерения
    "гектар", "литр", "метр", "час", "минута", "секунда", "тонна", "грамм",
    "километр", "сантиметр", "миллиметр", "градус", "процент",
    # Абстракции
    "свобода", "мысль", "душа", "музыка", "любовь", "власть", "счастье",
    "память", "сила", "истина", "вера", "надежда", "красота",
    # Сезоны и явления
    "зима", "лето", "осень", "весна",
    "дождь", "снег", "ветер", "гроза", "туман", "иней", "роса",
    # Собирательные
    "народ", "толпа", "стая", "армия", "общество", "семья", "класс", "коллектив",
    # Категории/классы
    "мебель", "транспорт", "одежда", "посуда", "техника", "обувь", "инвентарь",
    # Действия и состояния
    "пляска", "бег", "прыжок", "тишина", "темнота", "тепло", "холод", "звук",
    # Редкие/книжные/абстрактные
    "зиккурат", "амфора", "ятаган", "скарабей", "веретено", "кадуцей", "фолиант",
    "генезис", "номенклатура",
}


def validate(text: str, term: str) -> dict:
    """
    Проверяет ответ Claude и возвращает разобранный dict.
    Формат ожидается:
        📖 ЧАСТЬ1 (слово1) + ЧАСТЬ2 (слово2)
        🎨 Абсурдная сцена в одном предложении.

    Raises ValidationError если формат нарушен или слова запрещены.
    Returns dict: {part1, word1, part2, word2, image}
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    if len(lines) < 2:
        raise ValidationError(f"Ожидается 2 строки, получено {len(lines)}")

    line1, line2 = lines[0], lines[1]

    if not line1.startswith("📖"):
        raise ValidationError(f"Первая строка должна начинаться с 📖, получено: {line1[:30]}")

    if not line2.startswith("🎨"):
        raise ValidationError(f"Вторая строка должна начинаться с 🎨, получено: {line2[:30]}")

    # Парсим "📖 ЧАСТЬ1 (слово1) + ЧАСТЬ2 (слово2)"
    matches = re.findall(r'([А-ЯЁA-Z0-9\-]+)\s*\(([а-яёa-zA-Z]+)\)', line1)

    if len(matches) < 2:
        raise ValidationError(f"Не удалось разобрать слова-крючки: {line1}")

    if len(matches) > 2:
        raise ValidationError(f"Слишком много частей ({len(matches)}), нужно ровно 2")

    part1, word1 = matches[0]
    part2, word2 = matches[1]

    for word in [word1.lower(), word2.lower()]:
        if word in BANNED_KEYWORDS:
            raise ValidationError(f"Запрещённое слово-крючок: «{word}»")

    image = line2[len("🎨"):].strip()
    if not image:
        raise ValidationError("Пустой образ в строке 🎨")

    return {
        "part1": part1,
        "word1": word1,
        "part2": part2,
        "word2": word2,
        "image": image,
    }
