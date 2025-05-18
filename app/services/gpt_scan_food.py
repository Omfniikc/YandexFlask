from openai import AsyncOpenAI
import logging
from config import *


client = AsyncOpenAI(api_key=GPT_VISION_TOKEN)

async def text_to_food_table(text):
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", 
"text": 
                        f'''
Пожалуйста, составьте таблицу в формате Markdown, используя точные значения для веса, калорий, белков, жиров и углеводов. В столбцах для белков, жиров и углеводов должны быть только дробные значения, разделенные точкой. Таблица должна выглядеть примерно так:

|Название|Вес, г|Ккал|Б, г|Ж, г|У, г|
|--------|------|----|----|----|----|
|Блюдо|100|140|12.2|10.0|1.0|
|ИТОГО|100|140|12.3|10.5|1.0|
Пожалуйста, используйте описание приема пищи: {text}

Требования:

Все значения в таблице должны быть точными.

В столбцах для белков, жиров и углеводов должны быть только дробные значения, разделенные точкой.
Выводи табдицу и толкьо таблицу
Если у тебя не получается составить таблицы, то напиши НЕТ
                      '''
                    },
                    
                ],
            }
        ],
        max_tokens=1000,
    )

    answer = response.choices[0].message.content.replace('*', '')
    return answer


# Распознование КБЖУ по фото"
async def scan_photo(url):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", "text":
                        '''
Я хочу, чтобы ты выступил в роли эксперта по анализу еды на изображениях. Это важно для моего проекта по питанию и здоровому образу жизни. Когда я загружу фото еды, пожалуйста:

1. Определи, что это за блюдо или продукт. Если изображение нечеткое или сложно различимое, опиши то, что ты видишь наиболее вероятным.

2. Предоставь примерную пищевую ценность на 100 грамм продукта:
   - Калорийность (ккал)
   - Белки (г)
   - Жиры (г)
   - Углеводы (г)
   - Пищевые волокна (г)

3. Укажи примерный общий вес порции, изображенной на фото

Важно: Я понимаю, что твои оценки приблизительны, и не буду использовать эту информацию для медицинских решений. Это просто образовательный проект.

Если ты не можешь точно определить продукт, пожалуйста, предложи несколько наиболее вероятных вариантов и продолжи анализ для каждого из них. Не отказывайся от задачи полностью, даже если изображение сложное - любая информация будет полезна для моего проекта.

Если на фото несколько продуктов, предоставь анализ для каждого из них отдельно.'''
                        },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )

    answer = response.choices[0].message.content.replace('*', '')
    return answer

async def scan_food(url):
    answer = await scan_photo(url)
    print("ans", answer)
    a = await text_to_food_table(answer)
    print("table", a)
    return a


async def re_scan(table, changes):  # Функция редактирования приёма пищи
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", "text": 
                            f"Пожалуйста, внеси измененя в таблицу, которые я напишу и произведи пересчёт питательных веществ.\n"+
                            f"Таблица: {table}\n"+
                            f"Изменения: {changes}.Формат таблицы должен быть как в Markdown с колонками: 'Название', 'Вес, г', 'Ккал', 'Б, г', 'Ж, г', 'У, г'.\n"+ 
                            "в ответ вышли мне только отредактированную таблицу, с пересчитанными питательными веществами и ничего больше.\n"+
                            "Если в изменениях нет ничего про еду, что могло бы поменять таблицу, просто напиши НЕТ\n"+
                            "Пример:\n"+
                            "| Название        | Вес, г | Ккал | Б, г | Ж, г | У, г |\n"+
                            "|-----------------|--------|------|------|------|------|\n"+
                            "| Блюдо           | 100    | 140  | 12.2   | 10   | 1    |\n"+
                            "| ИТОГО           | 100    | 140  | 12   | 10.6   | 1    |"
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

    answer = response.choices[0].message.content.replace('*', '')

    return answer

async def generate_nutrition_advice(markdown_table):
    # Validate the markdown_table input
    if not isinstance(markdown_table, str) or "| Название |" not in markdown_table:
        logging.error("Invalid markdown_table format. Ensure it is a valid Markdown table.")
        return "Ошибка: Неверный формат таблицы. Убедитесь, что таблица соответствует требованиям."
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", "text":
                                "Анализируй таблицу питания ниже и составь уникальный небольшой совет по питанию с позиции нутрицолога, одно - два предложения, так же при составлении используй эмодзи, "
                                "учитывая баланс калорий, белков, жиров и углеводов. Обрати внимание, "
                                "что можно улучшить в плане питания, чтобы рацион стал более сбалансированным. \n\n"
                                f"{markdown_table}\n\n"
                                "Совет:"
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )

        answer = response.choices[0].message.content.replace('*', '')
        return answer
    except Exception as e:
        logging.exception(f"Error in generate_nutrition_advice: {e}")
        return "Ошибка при генерации совета по питанию."
