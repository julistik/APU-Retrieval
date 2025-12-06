import re
import json

# === РЕГУЛЯРКИ ===
LEMMA_RE = re.compile(r"^([А-ЯЁ\s\(\)\-]+?)\s+(\d+)\s*[—–-]\s*(.+)$")

# Строка состоит ТОЛЬКО из грамматических помет
GRAMMAR_LINE_RE = re.compile(
    r"^(?:\s*(?:Номин\.?|Неизм\.?|Призн\.?|Сказ\.?|Разг\.?|Прост\.?|Кач[\.-]?обст\.?|Обст\.?|Опред\.?|Шутл\.?|Неодобр\.?|Устар\.?|Экспрес\.?)\s*[:;]?\s*)+$",
    re.IGNORECASE
)

def is_grammar_line(line: str) -> bool:
    return bool(GRAMMAR_LINE_RE.match(line.strip()))

def split_meaning_and_grammar(text: str):
    text = text.strip()
    # Сначала пытаемся поймать кавычки
    m = re.match(r'^[«‹"„](.+?)[»›"“]\s*(.*)$', text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    
    # Если нет — ищем начало грамматики
    m = re.search(r'\b(Номин|Неизм|Призн|Сказ|Разг|Прост|Кач|Обст|Опред|Шутл|Неодобр|Устар|Экспрес)', text)
    if m:
        return text[:m.start()].strip(), text[m.start():].strip()
    
    return text, ""

def glue_lines(lines_list):
    return " ".join(x.strip() for x in lines_list if x.strip())

# === ОСНОВНАЯ ФУНКЦИЯ ===
def parse_dictionary(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]

    result = []
    current = None
    i = 0

    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()

        # Пропуск мусора
        if not line or line.isdigit() or "заказ" in line.lower():
            i += 1
            continue

        # === НОВАЯ ЛЕММА ===
        m = LEMMA_RE.match(raw_line)
        if m:
            if current:
                result.append(current)

            lemma = m.group(1).strip()
            num = int(m.group(2))
            rest = m.group(3)

            # Собираем все строки, пока они — чистая грамматика
            full_text = raw_line
            i += 1
            while i < len(lines) and is_grammar_line(lines[i]):
                full_text += " " + lines[i].strip()
                i += 1

            meaning, grammar = split_meaning_and_grammar(full_text)

            current = {
                "lemma": lemma,
                "entries": [{
                    "sense_number": num,
                    "meaning": meaning,
                    "grammar": grammar,
                    "examples": [],
                    "synonyms": [],
                    "antonyms": []
                }]
            }
            continue  # ← важный continue! строки грамматики уже пропущены

        # === Синонимы ===
        if re.match(r"^\s*синонимы", line, re.IGNORECASE):
            syn_text = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line or re.match(r"^\s*антонимы", next_line, re.IGNORECASE) or LEMMA_RE.match(lines[i]):
                    break
                syn_text.append(next_line)
                i += 1
            current["entries"][-1]["synonyms"] = [glue_lines(syn_text)]
            continue

        # === Антонимы ===
        if re.match(r"^\s*антонимы", line, re.IGNORECASE):
            ant_text = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line or LEMMA_RE.match(lines[i]):
                    break
                ant_text.append(next_line)
                i += 1
            current["entries"][-1]["antonyms"] = [glue_lines(ant_text)]
            continue

        # === Всё остальное — примеры ===
        if current:
            current["entries"][-1]["examples"].append(raw_line)

        i += 1

    # Последняя запись
    if current:
        result.append(current)

    # Финальная склейка
    for item in result:
        for e in item["entries"]:
            e["examples"] = glue_lines(e["examples"])
            e["synonyms"] = glue_lines(e["synonyms"])
            e["antonyms"] = glue_lines(e["antonyms"])
            for key in ["grammar", "synonyms", "antonyms"]:
                if e.get(key, "").strip() == "":
                    e.pop(key, None)

    return result


# === ЗАПУСК ===
if __name__ == "__main__":
    data = parse_dictionary("result_abs.txt")
    with open("dictionary_perfect.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("ГОТОВО! → dictionary_perfect.json")
