from thefuzz import fuzz, process

def find_term(user_input: str, term_list: list) -> tuple:
    # Приводим к нижнему регистру
    user_input = user_input.lower().strip()
    
    # Ищем наиболее похожий термин в базе
    result = process.extractOne(
        user_input,
        term_list,
        scorer=fuzz.WRatio
    )
    
    # Возвращаем термин и процент совпадения
    if result:
        return result[0], result[1]
    
    return None, 0