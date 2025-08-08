from typing import Optional, Union


def format_plant_reply(
    plant_name: str,
    scientific_name: Optional[str],
    family: Optional[str],
    description: str,
    care_tips: Optional[str],
    fun_facts: Optional[str],
    is_toxic: Optional[bool] = None,
    difficulty: Optional[str] = None,
) -> str:
    """Форматирует ответ с информацией о растении"""
    
    # Заголовок с названием растения
    lines = [f"🌿 **{plant_name}**"]
    
    if scientific_name:
        lines.append(f"🔬 _{scientific_name}_")
    
    if family:
        lines.append(f"👨‍👩‍👧‍👦 Семейство: {family}")
    
    lines.append("")  # Пустая строка
    
    # Описание
    lines.append(f"📝 **Описание:**")
    lines.append(description)
    lines.append("")
    
    # Уход (если есть)
    if care_tips:
        lines.append(f"🌱 **Уход:**")
        lines.append(care_tips)
        lines.append("")
    
    # Интересные факты (если есть)
    if fun_facts:
        lines.append(f"💡 **Интересные факты:**")
        lines.append(fun_facts)
        lines.append("")
    
    # Сложность ухода (если указана)
    if difficulty:
        difficulty_emoji = {
            "easy": "🟢 Легкий",
            "medium": "🟡 Средний", 
            "hard": "🔴 Сложный"
        }
        lines.append(f"📊 **Сложность ухода:** {difficulty_emoji.get(difficulty.lower(), difficulty)}")
        lines.append("")
    
    # Токсичность (если указана)
    if is_toxic is not None:
        if is_toxic:
            lines.append("⚠️ **Внимание:** Растение может быть токсичным для людей или животных")
        else:
            lines.append("✅ **Безопасность:** Растение не токсично")
        lines.append("")
    
    return "\n".join(lines)


def format_error_message(message: str = "Не удалось распознать растение") -> str:
    """Форматирует сообщение об ошибке"""
    return f"🤔 {message}\n\nПопробуйте:\n• Сделать фото при лучшем освещении\n• Показать растение целиком\n• Добавить текстовое описание" 