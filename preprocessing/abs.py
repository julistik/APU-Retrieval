import re
from tqdm import tqdm 

def is_page_number(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.isdigit():
        return True
    if re.fullmatch(r"\d+.*\d+", stripped):
        if not re.search(r"[А-Яа-яЁё]", stripped):
            return True
        if re.search(r"заказ|заявка|оттиск", stripped, flags=re.IGNORECASE):
            return True

    return False

def is_single_letter(line):
    return bool(re.fullmatch(r"[А-Яа-яЁё]", line.strip()))

def process(input_text, output_text):
    with open(input_text, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []
    i = 0
    n = len(lines)

    pbar = tqdm(total=n, desc="Обработка строк", unit="строка")

    while i < n:
        line = lines[i].rstrip("\n")
        stripped = line.strip()

        # Пропускаем номера страниц
        if is_page_number(stripped):
            i += 4
            pbar.update(4)
            continue

        # Пропускаем одиночные буквы
        if is_single_letter(stripped):
            i += 1
            pbar.update(1)
            continue

        # Если строка не заканчивается на "-"
        if not stripped or stripped[-1] != "-":
            cleaned_lines.append(stripped)
            i += 1
            pbar.update(1)
            continue

        # --- Обработка переноса ---
        merged = stripped[:-1]  # убираем дефис
        j = i + 1

        while j < n:
            next_line = lines[j].strip()

            # Пропускаем мусорные строки
            if not next_line or is_page_number(next_line) or is_single_letter(next_line) or re.fullmatch(r"[А-Яа-яЁё\s]+\d*", next_line):
                j += 1
                pbar.update(1)
                continue

            # Склеиваем следующую строку
            if next_line.endswith("-"):
                merged += next_line[:-1]  # убираем дефис
                j += 1
                pbar.update(1)
            else:
                merged += next_line
                j += 1
                pbar.update(1)
                break

        cleaned_lines.append(merged)
        i = j  # продолжаем после обработанных строк

    
    pbar.close()  # закрываем прогресс-бар

    # Сохраняем результат
    with open(output_text, "w", encoding="utf-8") as f:
        for line in cleaned_lines:
            f.write(line + "\n")

if __name__ == "__main__":
    process("result_pdf_to_txt.txt", "result_abs.txt")
