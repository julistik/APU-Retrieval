import re
import json


LEMMA = re.compile(r"(?:\b[А-ЯЁA-Z]{2,}\b.*){2,}")
LEMMA_RE = re.compile(
    r"^([А-ЯЁA-Z0-9\s\/,\.;:\(\)\-]+?)\s+(\d+)\s*[—-]\s*(.*)$"
)

def is_lemma_start(line: str) -> bool:
    """
    Возвращает True, если в строке явно присутствует заголовочная капс-часть:
    минимум два слова, состоящих исключительно из заглавных букв (А-ЯЁA-Z).
    Функция ориентирована на начало строки (чтобы не ловить капс-слова внутри примеров).
    """
    if not line:
        return False
    # Проверяем первые ~100 символов — заголовки обычно короткие; это снижает ложные срабатывания
    prefix = line[:200]
    return bool(LEMMA.search(prefix))

def is_synonyms(line):
    line = line.strip().lstrip("(")
    line = line.strip().lstrip("‘")
    return "синонимы" in line.lower()

def is_antonyms(line):
    line = line.strip().lstrip("(")
    return "антонимы" in line.lower()

def normalize_syn_ant(line):
    stripped = line.strip().lstrip("(").strip()

    # Ищем слово "синонимы" или "антонимы" + любой разделитель (: ; , .) + текст
    syn_match = re.search(r"синонимы\s*[:;,.]?\s*", stripped, re.IGNORECASE)
    ant_match = re.search(r"антонимы\s*[:;,.]?\s*", stripped, re.IGNORECASE)

    if syn_match:
        rest = stripped[syn_match.end():].strip()
        return "Синонимы: " + rest
    elif ant_match:
        rest = stripped[ant_match.end():].strip()
        return "Антонимы: " + rest
    else:
        # Если вообще не нашли просто возвращаем как есть
        return stripped

def split_meaning_and_grammar(text: str):
    if text is None:
        return "", ""
    text = text.strip()
    if not text:
        return "", ""

    # допустимые открывающие/закрывающие кавычки
    OPEN = "«‹<"+'"'+"'„‚‘“‘"
    CLOSE = "»›>"+'"'+"'”’‟"

    # поиск первой открывающей кавычки (в правой части после тире)
    first_open_idx = None
    for q in OPEN:
        idx = text.find(q)
        if idx != -1 and (first_open_idx is None or idx < first_open_idx):
            first_open_idx = idx

    # если есть открывающая кавычка, начинаем сбор цитат-значений
    if first_open_idx is not None:
        # найти первую закрывающую кавычку справа от неё
        def find_close(from_idx):
            for j in range(from_idx + 1, len(text)):
                if text[j] in CLOSE:
                    return j
            return None

        close_idx = find_close(first_open_idx)
        if close_idx is not None:
            parts = []

            # попытка взять номер перед первой кавычкой
            leading_segment = text[:first_open_idx]
            mnum = re.search(r'(\d+)\s*$', leading_segment)
            num = mnum.group(1) if mnum else None
            first_content = text[first_open_idx+1:close_idx].strip()
            parts.append(f"{num} {first_content}".strip() if num else first_content)

            pos = close_idx + 1

            # цикл: пытаться найти последующие кавычные блоки, если между ними только
            # допустимые разделители (пробелы, запятые, точки с запятой, цифры, тире)
            while True:
                # найти следующую открывающую кавычку
                next_open = None
                next_open_rel = None
                for q in OPEN:
                    idx = text.find(q, pos)
                    if idx != -1 and (next_open is None or idx < next_open):
                        next_open = idx
                if next_open is None:
                    break

                # проверяем промежуток text[pos:next_open] — он должен содержать
                # только разрешённые символы: пробелы, запятые, точки с запятой, цифры, тире, скобки
                between = text[pos:next_open]
                if not re.fullmatch(r'[\s\d,;:\-–—()«»‹›<>\"\'„“‟’‘]*', between):
                    break

                # нашли следующую закрывающую кавычку
                next_close = find_close(next_open)
                if next_close is None:
                    break

                # номер перед этой кавычкой (в промежутке между pos и next_open)
                num_match = re.search(r'(\d+)\s*$', text[pos:next_open])
                num2 = num_match.group(1) if num_match else None
                content2 = text[next_open+1:next_close].strip()
                parts.append(f"{num2} {content2}".strip() if num2 else content2)

                pos = next_close + 1
                # loop continue

            # всё, что осталось справа от pos — это грамматика (если есть)
            grammar = text[pos:].strip()
            meaning = "; ".join(parts)  # соединяем части через ; чтобы ясно отделять подзначения
            return meaning, grammar

    # Если кавычек нет / не удалось собрать — ищем маркеры грамматики
    grammar_pattern = re.compile(
        r'\b(?:Номин\.?|Неизм\.?|Призн\.?|Сказ\.?|Разг\.?|Прост\.?|'
        r'Кач[\.-]?обст\.?|Обст\.?|Опред\.?|Шутл\.?|Неодобр\.?|Устар\.?|Экспрес\.?)',
        flags=re.IGNORECASE
    )
    m = grammar_pattern.search(text)
    if m:
        meaning = text[:m.start()].strip(" ,;:\"'«»‹›<>").strip()
        if '—' in meaning:
            meaning = meaning.split('—', 1)[1].strip()
        elif '-' in meaning:
            meaning = meaning.split('-', 1)[1].strip()
        elif '–' in meaning:
            meaning = meaning.split('–', 1)[1].strip()
        grammar = text[m.start():].strip()
        return meaning, grammar

    # fallback — всё считается значением
    meaning = text.strip(" ,;:\"'«»‹›<>").strip()
    return meaning, ""

def is_grammar_line(line):
    grammar_pattern = re.compile(
        r'\b(?:Номин\.|Неизм\.|Призн\.|Сказ\.|Разг\.|Прост\.|'
        r'Кач[\.-]?обст\.|Обст\.|Опред\.|Шутл\.|Неодобр\.|Устар\.|Экспрес\.)\b'
    )
    return bool(grammar_pattern.search(line))

def glue_lines(lines):
    return " ".join(x.strip() for x in lines if x.strip())

def parse_dictionary(file):
    with open(file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    result = []
    current = None  
    block = None  # examples / synonyms / antonyms

    i = 0
    while i < len(raw_lines):
        stripped = raw_lines[i].strip()

        if not stripped:
            i += 1
            continue
        
        m = None
        lemma_lines = [stripped]  # склеиваем строки леммы

        # если это строка в капсе, но LEMMA_RE не сработал
        if is_lemma_start(stripped) and not LEMMA_RE.match(stripped):
            # собираем следующие строки, пока не найдём номер+тире
            j = i + 1
            while j < len(raw_lines):
                next_line = raw_lines[j].strip()
                lemma_lines.append(next_line)
                combined = " ".join(lemma_lines)
                if LEMMA_RE.match(combined):
                    m = LEMMA_RE.match(combined)
                    i = j  # перескакиваем на последнюю строку леммы
                    break
                j += 1
        elif LEMMA_RE.match(stripped):
            m = LEMMA_RE.match(stripped)

        if m:
            if current:
                print('1', current['lemma'])
                result.append(current)

            lemma, num, rest = m.groups()

            full_rest = rest
            i += 1
            while i < len(raw_lines) and is_grammar_line(raw_lines[i]):
                full_rest += " " + raw_lines[i].strip()
                i += 1  # ← строки грамматики съедены и больше не появятся

            meaning, grammar = split_meaning_and_grammar(full_rest)

            current = {
                "lemma": lemma.strip(),
                "entries": [{
                    "sense_number": int(num),
                    "meaning": meaning.strip(),
                    "grammar": grammar.strip(),
                    "examples": [],
                    "synonyms": [],
                    "antonyms": []
                }]
            }
            print(current['lemma'])
            block = "examples"  # ← с этого момента начинаются примеры
            continue
        

        if is_synonyms(stripped):
            block = "synonyms"

            # Приводим строку к правильному формату: Синонимы:
            normalized = normalize_syn_ant(stripped)
            text_only = normalized.replace("Синонимы:", "").strip()

            # Пытаемся склеить сумму строк, пока не будет:
            # — пустой строки
            # — слова Антонимы
            # — новой леммы
            # — новой головной статьи
            j = i + 1
            while j < len(raw_lines):
                nxt = raw_lines[j].strip()

                # стоп-условия
                if not nxt:
                    break
                if is_antonyms(nxt):
                    break
                if is_lemma_start(nxt):
                    break

                # если строка продолжает синонимы — добавляем
                text_only += " " + nxt
                j += 1

            # сохраняем итоговую строку
            current["entries"][-1]["synonyms"].append(text_only)

            # перескакиваем на последнюю обработанную строку
            i = j
            continue

        if is_antonyms(stripped):
            block = "antonyms"

            normalized = normalize_syn_ant(stripped)
            text_only = normalized.replace("Антонимы:", "").strip()

            # Склеивание многострочных антонимов
            j = i + 1
            while j < len(raw_lines):
                nxt = raw_lines[j].strip()

                # Стоп условия
                if not nxt:
                    break
                if is_synonyms(nxt):
                    break
                if is_lemma_start(nxt):
                    break

                # Добавляем строку
                text_only += " " + nxt
                j += 1

            current["entries"][-1]["antonyms"].append(text_only)

            i = j
            continue


        if block == "examples":
            current["entries"][-1]["examples"].append(stripped)
        elif block == "synonyms":
            current["entries"][-1]["synonyms"].append(stripped)
        elif block == "antonyms":
            current["entries"][-1]["antonyms"].append(stripped)
        
        i += 1
      
    if current:
        result.append(current)
        
    for item in result:
        for entry in item["entries"]:
            entry["examples"] = glue_lines(entry["examples"])
            entry["synonyms"] = glue_lines(entry["synonyms"])
            entry["antonyms"] = glue_lines(entry["antonyms"])

    return result

def process_to_json(input_file, output_file):
    data = parse_dictionary(input_file)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- запуск ---
process_to_json("result_abs.txt", "result_glue.json")
