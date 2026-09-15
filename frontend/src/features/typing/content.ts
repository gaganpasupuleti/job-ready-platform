export type Mode = 'text' | 'code' | 'custom'
export const languages = ['Python', 'SQL', 'JavaScript', 'Java', 'C++'] as const
export type Language = (typeof languages)[number]
export const difficulties = ['Foundation', 'Intermediate', 'Advanced'] as const
export type Difficulty = (typeof difficulties)[number]

// Original JobReady practice material. No third-party snippet corpus is bundled.
const words =
  'learn build create explore improve practice focus think solve plan write read clear simple steady better small steps daily work skill time flow idea start finish grow'.split(
    ' ',
  )
const passages = [
  'Good software starts with a clear problem. Break the work into small steps, test each change, and explain the result. Progress comes from careful practice and useful feedback.',
  'Before a data pipeline runs, validate its inputs. Check missing values, duplicate records, and unexpected types. A useful report explains what changed, why it matters, and what to do next.',
  'Reliable systems make failure visible. Record the event, preserve its context, and retry only when the operation is safe. Clear ownership and small interfaces help a team maintain software over time.',
]
const snippets: Record<Language, string[]> = {
  Python: [
    // Foundation: variables, simple functions, basic loops — short lines, light punctuation
    'def score_total(values):\n    total = 0\n    for value in values:\n        total = total + value\n    return total\n\nprint(score_total([2, 4, 6]))',
    // Intermediate: comprehensions, dict processing, exceptions, file handling
    'def load_active(path):\n    try:\n        with open(path, "r", encoding="utf-8") as handle:\n            rows = handle.read().splitlines()\n    except OSError as error:\n        raise RuntimeError("Unable to read file") from error\n    return {\n        name: int(score)\n        for name, score in (row.split(",") for row in rows)\n        if int(score) >= 70\n    }',
    // Advanced: classes, decorators, generators, async, typed pipelines — nested, denser punctuation
    'import asyncio\nfrom typing import AsyncIterator, Callable\n\ndef trace(fn: Callable[[str], str]) -> Callable[[str], str]:\n    def wrapped(value: str) -> str:\n        return f"{fn.__name__}:{fn(value)}"\n    return wrapped\n\nclass Pipeline:\n    def __init__(self, limit: int) -> None:\n        self.limit = limit\n\n    @trace\n    def label(self, item: str) -> str:\n        return item.upper()\n\n    async def stream(self, items: list[str]) -> AsyncIterator[str]:\n        for index, item in enumerate(items):\n            if index >= self.limit:\n                break\n            yield self.label(item)\n            await asyncio.sleep(0)',
  ],
  SQL: [
    'SELECT name, score\nFROM students\nWHERE score >= 70\nORDER BY score DESC;',
    'SELECT department, COUNT(*) AS total\nFROM employees\nWHERE is_active = TRUE\nGROUP BY department\nHAVING COUNT(*) > 5;',
    'WITH ranked AS (\n    SELECT customer_id, order_date,\n        ROW_NUMBER() OVER (\n            PARTITION BY customer_id\n            ORDER BY order_date DESC\n        ) AS row_num\n    FROM orders\n)\nSELECT customer_id, order_date\nFROM ranked\nWHERE row_num = 1;',
  ],
  JavaScript: [
    'function greet(name) {\n    const message = "Hello, " + name;\n    return message;\n}\n\nconsole.log(greet("learner"));',
    'const activeNames = students\n    .filter((student) => student.active)\n    .map((student) => student.name);\n\nconsole.log(activeNames);',
    'async function loadItems(url) {\n    const response = await fetch(url);\n    if (!response.ok) {\n        throw new Error("Request failed");\n    }\n    return response.json();\n}',
  ],
  Java: [
    'class Greeting {\n    public static void main(String[] args) {\n        String name = "learner";\n        System.out.println("Hello, " + name);\n    }\n}',
    'static int total(int[] values) {\n    int result = 0;\n    for (int value : values) {\n        result += value;\n    }\n    return result;\n}',
    'static Map<String, Integer> count(List<String> names) {\n    Map<String, Integer> counts = new HashMap<>();\n    for (String name : names) {\n        counts.merge(name, 1, Integer::sum);\n    }\n    return counts;\n}',
  ],
  'C++': [
    '#include <iostream>\n\nint main() {\n    std::cout << "Hello, learner" << std::endl;\n    return 0;\n}',
    'int total(const std::vector<int>& values) {\n    int result = 0;\n    for (int value : values) {\n        result += value;\n    }\n    return result;\n}',
    'std::unordered_map<std::string, int> count(\n    const std::vector<std::string>& names\n) {\n    std::unordered_map<std::string, int> counts;\n    for (const auto& name : names) {\n        ++counts[name];\n    }\n    return counts;\n}',
  ],
}
export function practiceContent(
  mode: Mode,
  language: Language,
  difficulty: Difficulty,
  round: number,
  timed: boolean,
) {
  const level = difficulties.indexOf(difficulty)
  if (mode === 'code') return snippets[language][level]
  if (level === 0)
    return Array.from(
      { length: timed ? 500 : 35 },
      (_, i) => words[(i * 7 + round * 11) % words.length],
    ).join(' ')
  const text = passages[(round + level - 1) % passages.length]
  return timed ? Array(18).fill(text).join(' ') : text
}
