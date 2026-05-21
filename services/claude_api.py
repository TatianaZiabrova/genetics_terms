import anthropic
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Ты создаёшь мнемоники для терминов ЕГЭ по биологии методом ключевых слов.

ПРАВИЛА:
1. Разбей термин ровно на 2 примерно равные части — даже если термин длинный (10+ букв). Никогда не делай 3 части.
2. Каждой части — одно простое русское слово, обозначающее конкретный предмет.
3. ГЛАВНОЕ: слово-крючок должно ЗВУЧАТЬ ПОХОЖЕ на свою часть термина. Первые 2–3 буквы должны совпадать или быть фонетически близки.
   Примеры допустимой фонетической близости:
   — ГЕТЕРО → гетры (ГЕТ = ГЕТ ✓), гетман (ГЕТ = ГЕТ ✓)
   — ЗИГОТА → зебра (ЗИ ≈ ЗЕ ✓), зонт (ЗО ≈ ЗИ — хуже, но допустимо)
   — КРОСС → кроссовок (КРОСС = КРОСС ✓)
   — ГОМО → гора (ГО = ГО ✓), гном (ГН ≈ ГО — допустимо)
   НЕЛЬЗЯ: ГЕТЕРО → ведро (ВЕ ≠ ГЕ — совсем не похоже ✗)
4. Используй только слова из повседневного лексикона российского подростка 2020-х годов. Ориентир: слово знает любой школьник 16 лет.
   Хорошие примеры: кот, носок, шапка, гель, банан, гном, торт, мяч, лампа, молоток, кружка, ключ, гетры, зонт, нож, бочка, жук, краб, гриб, лук, мед, бант, гол, газ, бег, зал.
5. НЕ используй слова, которые подросток может не знать: гетман, зиккурат, амфора, ятаган, скарабей, веретено, кадуцей, фолиант, берет, кивер, бармица, сюртук, камзол.
6. Слово = предмет, который можно нарисовать за 5 секунд. Никаких абстракций, процессов, эмоций, групп людей, явлений.
7. Из этих 2 слов составь одну короткую абсурдную сцену (1 предложение).
8. Действие в сцене должно отражать смысл определения.
9. Порядок слов совпадает с порядком частей термина.

ФОРМАТ ОТВЕТА — ровно 2 строки, без пояснений и преамбулы:
📖 ЧАСТЬ1 (слово1) + ЧАСТЬ2 (слово2)
🎨 [абсурдная сцена в 1 предложение]

ХОРОШИЙ ПРИМЕР
Вход: ГЕНОМ — вся наследственная информация организма
📖 ГЕ (гель) + НОМ (гном)
🎨 Гном залез в банку геля, и в каждой капле плавает его маленькая копия — полная инструкция, как его собрать.

ПЛОХОЙ ПРИМЕР (так делать НЕЛЬЗЯ)
Вход: ГЕНОМ
📖 ГЕ (генезис) + НОМ (номенклатура)
Почему плохо: «генезис» и «номенклатура» — абстрактные книжные слова, их нельзя нарисовать. Нужны конкретные предметы."""


async def generate_mnemonic(term: str, definition: str, previous: list[str] | None = None, max_retries: int = 3) -> dict:
    """Генерирует мнемонику с автоматическим повтором при провале валидации."""
    from services.validator import validate, ValidationError

    prev_block = ""
    if previous:
        prev_block = "\n\nУЖЕ ПОКАЗАННЫЕ ОБРАЗЫ — придумай полностью другой, с другими словами-крючками:\n" + "\n".join(f"— {p}" for p in previous)

    last_error = None
    for _ in range(max_retries):
        response = await asyncio.to_thread(
            _client.messages.create,
            model="claude-sonnet-4-6",
            max_tokens=180,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Термин: {term}\nОпределение: {definition}{prev_block}"
            }]
        )
        text = response.content[0].text
        try:
            return validate(text, term)
        except ValidationError as e:
            last_error = e
            continue

    raise RuntimeError(f"Не вышло сгенерировать мнемонику для '{term}' за {max_retries} попытки: {last_error}")


async def get_definition(term: str) -> str:
    """Получает краткое определение термина по генетике/биологии ЕГЭ"""
    message = await asyncio.to_thread(
        _client.messages.create,
        model="claude-haiku-4-5",
        max_tokens=80,
        messages=[{
            "role": "user",
            "content": f"Дай краткое определение термина по биологии (генетике) для ЕГЭ: {term}\nОдно предложение, максимум 15 слов."
        }]
    )
    return message.content[0].text.strip()


async def find_term_by_meaning(user_input: str, terms_list: list) -> str:
    """Находит термин по смыслу/опечаткам. Первая буква должна совпадать."""
    if not user_input or not user_input.strip():
        return None

    # Фильтр по первой букве — обязательное условие
    first_letter = user_input.strip()[0].lower()
    filtered = [t for t in terms_list if t and t[0].lower() == first_letter]

    if not filtered:
        # Термина с такой буквой нет в базе — возвращаем ввод как есть
        return user_input.strip().lower()

    terms_str = "\n".join(filtered)
    message = await asyncio.to_thread(
        _client.messages.create,
        model="claude-haiku-4-5",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""Список терминов:
{terms_str}

Пользователь написал: "{user_input}"

Найди подходящий термин из списка (учитывай опечатки).
Если ничего не подходит — ответь: НЕТ

Ответь ТОЛЬКО одним словом — термином из списка или НЕТ."""
        }]
    )

    result = message.content[0].text.strip().lower()
    if result == "нет":
        return user_input.strip().lower()
    return result
