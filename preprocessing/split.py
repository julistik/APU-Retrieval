import json
import re

INPUT_FILE = "result_glue.json"
OUTPUT_FILE = "result_split.json"


def split_grammar(grammar_str):
    if not isinstance(grammar_str, str):
        return grammar_str
    if not grammar_str:
        return []
    s = grammar_str.split('.')
    for i in range(len(s)):
        s[i] = s[i].strip()
        if s[i] == '':
            continue
        else:
            s[i] += '.'
        if s[i][0] != '-':
            s[i] = s[i][0].upper() + s[i][1:]
    restored = [s[0]]
    for i in range(1, len(s)):
        if s[i] == '':
            continue
        if s[i].startswith('-'):
            restored[-1] += s[i]
        else:
            restored.append(s[i])
    return restored

import re

def split_examples(text):
    # Автор = инициалы + фамилия, возможно несколько через запятую
    author_pattern = re.compile(
        r'(?:[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?)'
        r'(?:,\s*(?:[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?))*'
    )

    results = []
    last_end = 0
    if author_pattern.search(text):
        for m in author_pattern.finditer(text):
            author_block = m.group()
            authors = [a.strip() for a in author_block.split(',')]
            
            example_text = text[last_end:m.start()].strip()
            example_text = example_text.strip(" \n\t—")  # убираем лишние символы

            if example_text:
                if example_text.startswith('.'):
                    example_text = example_text[1:].strip()
                if len(authors) == 1:
                    results.append([example_text, authors[0]])
                else:
                    results.append([example_text, authors])
            
            last_end = m.end()


    if not author_pattern.search(text):
        source_pattern = re.compile(
            r'([А-ЯЁ][А-ЯЁа-яё\s\-«»/.]+?)'   # название источника
            r'(?:,\s*№\s*\d+)?'               # опциональный номер
            r'(?:,\s*(?:\d{2}\.\d{2}\.\d{2}|\d{2}\.\d{2}|\d{4}))?'  # дата или год
            r'\.'                              # точка в конце источника
        )

        results = []
        last_end = 0

        for m in source_pattern.finditer(text):
            source = m.group().strip()
            example = text[last_end:m.start()].strip(" \n\t—")
            if example:
                results.append([example, source])
            last_end = m.end()

        # остаток текста после последнего источника
        remainder = text[last_end:].strip()
        if remainder:
            results.append([remainder, ""])

    return results


def transform_dictionary(data):
    for item in data:
        if "entries" not in item:
            continue

        for entry in item["entries"]:
            if "grammar" in entry and isinstance(entry["grammar"], str):
                entry["grammar"] = split_grammar(entry["grammar"])
            if "examples" in entry and isinstance(entry["examples"], str):
                entry["examples"] = split_examples(entry["examples"])

        

    return data


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    transformed_data = transform_dictionary(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
