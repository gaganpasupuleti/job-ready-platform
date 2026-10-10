"""Build the reviewed CRT and DSA sprint batch. Does not publish a database."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = ROOT.parents[2] / "app" / "seed"

# lesson_key, title, existing_published
# Existing keys are named in explanations only. They are not copied into this batch.
PUBLISHED = {
    "crt-quant-percentages": "Percentages for placement aptitude",
    "crt-logical-patterns": "Number patterns in logical reasoning",
    "crt-verbal-meaning": "Reading for meaning in verbal ability",
    "crt-di-tables": "Reading a simple data table",
    "dsa-complexity": "Time complexity with big-O",
    "dsa-arrays-strings": "Arrays and strings",
}


def _load(name: str, var: str) -> list:
    mod = ast.parse((SEED / name).read_text(encoding="utf-8"))
    for node in mod.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == var:
            return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, "id", None) == var:
                    return ast.literal_eval(node.value)
    raise SystemExit(f"missing {var}")


def _take(rows: list, topic: str, count: int) -> list:
    found = [row for row in rows if row[2] == topic][:count]
    if len(found) != count:
        raise SystemExit(f"{topic} has {len(found)} not {count}")
    return found


def _note(concept, formula, worked, lesson, related, steps, why, *, algorithm=None):
    return {
        "concept": concept,
        "formula": formula,
        "worked": worked,
        "lesson": lesson,
        "related": related,
        "steps": steps,
        "why": why,
        "algorithm": algorithm,
    }


NOTES = [
    _note(
        "A percentage is a fraction of a whole, written per hundred. One discount is applied once.",
        "Discount = list price × percent / 100. Sale price = list price − discount.",
        "15% of 40,000 is 6,000. 40,000 − 6,000 = 34,000.",
        "crt-quant-percentages",
        "Practice other percentage questions in the placement aptitude catalog. The published syllabus check is syl-crt-q01.",
        ["Write 15% as 15/100.", "15/100 × 40,000 = 6,000.", "Subtract that discount once: 40,000 − 6,000 = 34,000."],
        {
            "₹36,000": "36,000 removes only 4,000, which is 10% of 40,000, not 15%.",
            "₹32,000": "32,000 removes 8,000, which is 20% off, not 15%.",
            "₹35,000": "35,000 removes 5,000, which is 12.5% off, not 15%.",
        },
    ),
    _note(
        "“Percent of a group” means that fraction of the group, not a separate group.",
        "Part = percent / 100 × whole.",
        "40/100 × 250 = 100.",
        "crt-quant-percentages",
        "Use the percentages lesson, then the other percentage questions in this reviewed set.",
        ["40% is 0.40.", "0.40 × 250 = 100.", "100 of the 250 applicants cleared the screen."],
        {
            "80": "80 would be 32% of 250, not 40%.",
            "120": "120 would be 48% of 250, not 40%.",
            "150": "150 would be 60% of 250, not 40%.",
        },
    ),
    _note(
        "Percentage increase compares the change with the original value, not with the new value.",
        "Percentage increase = (new − original) / original × 100.",
        "(75 − 60) / 60 × 100 = 25.",
        "crt-quant-percentages",
        "The percentages lesson works the same one-change pattern. Related practice is the other percentage items in the catalog.",
        ["The increase is 75 − 60 = 15.", "The base is the original score, 60.", "15/60 × 100 = 25%."],
        {
            "15%": "15 is the point increase, not the percentage. 15/60 is 25%, not 15%.",
            "20%": "20% of 60 is 12, which would land on 72, not 75.",
            "30%": "30% of 60 is 18, which would land on 78, not 75.",
        },
    ),
    _note(
        "12.5% is one eighth of a whole because 12.5 × 8 = 100.",
        "12.5% of a number = number / 8.",
        "640 / 8 = 80.",
        "crt-quant-percentages",
        "Check this against the published percentages lesson, then the other items in this set.",
        ["12.5/100 = 1/8.", "640 × 1/8 = 80."],
        {
            "64": "64 is 10% of 640, not 12.5%.",
            "100": "100 is 640/6.4, not one eighth of 640.",
            "72": "72 is 11.25% of 640, not 12.5%.",
        },
    ),
    _note(
        "Profit percentage uses cost price as the base. Selling price is not the base.",
        "Profit % = (selling price − cost price) / cost price × 100.",
        "920 − 800 = 120. 120/800 × 100 = 15.",
        "crt-sprint-profit-loss",
        "Lesson: Profit and loss on cost price. Practice the other two profit questions in this lesson.",
        ["Profit is 920 − 800 = 120.", "Divide by the cost, 800.", "120/800 × 100 = 15%."],
        {
            "12%": "12% of 800 is 96, so the selling price would be 896, not 920.",
            "20%": "20% of 800 is 160, so the selling price would be 960, not 920.",
            "10%": "10% of 800 is 80, so the selling price would be 880, not 920.",
        },
    ),
    _note(
        "Loss percentage also uses cost price as the base.",
        "Loss % = loss / cost price × 100.",
        "45/450 × 100 = 10.",
        "crt-sprint-profit-loss",
        "Same profit-and-loss lesson. Compare this with the zero-profit case in the same lesson.",
        ["The loss is given as 45 on a cost of 450.", "45/450 = 0.10.", "0.10 × 100 = 10%."],
        {
            "5%": "5% of 450 is 22.50, not a loss of 45.",
            "15%": "15% of 450 is 67.50, not a loss of 45.",
            "12%": "12% of 450 is 54, not a loss of 45.",
        },
    ),
    _note(
        "Profit and loss are measured from the gap between cost and selling price. Equal prices leave no gap.",
        "If cost price = selling price, profit = 0 and loss = 0.",
        "A pen bought and sold at ₹20 has profit 0 and loss 0.",
        "crt-sprint-profit-loss",
        "Stay on the profit-and-loss lesson. GST is a tax question and is not stated here.",
        ["Profit = selling price − cost price.", "The two prices are equal, so the difference is 0.", "Zero is neither a profit nor a loss."],
        {
            "10% profit": "A 10% profit would require the selling price to be higher than the cost price.",
            "5% loss": "A loss would require the selling price to be lower than the cost price.",
            "Depends on GST": "The question gives no tax. GST does not create profit when the two prices are equal.",
        },
    ),
    _note(
        "Work rate is the fraction of the job finished in one day.",
        "If one person finishes in D days, one day of work is 1/D.",
        "10 days for the whole job means 1/10 of the job per day.",
        "crt-sprint-time-work",
        "Lesson: Time and work rates. The next question in this lesson uses the same rate on a 15-day job.",
        ["The whole job is 1.", "A finishes it in 10 days.", "Each day is 1/10 of the job."],
        {
            "1/5": "1/5 would be the daily rate of a 5-day worker, not a 10-day worker.",
            "10": "10 is the number of days, not the fraction of work done in one day.",
            "1/12": "1/12 would belong to a 12-day worker.",
        },
    ),
    _note(
        "Work done is rate multiplied by time, when the rate stays constant.",
        "Work = days worked × (1 / days needed alone).",
        "5 × 1/15 = 5/15 = 1/3.",
        "crt-sprint-time-work",
        "Use the time-and-work lesson, then the one-day rate question beside this one.",
        ["B's daily rate is 1/15.", "Five days contribute 5/15.", "5/15 simplifies to 1/3."],
        {
            "1/5": "1/5 would be correct only if B finished the whole job in 5 days.",
            "1/2": "Half the job would take 7.5 days at this rate, not 5.",
            "2/5": "2/5 is 6/15, which would be 6 days of work, not 5.",
        },
    ),
    _note(
        "A fair coin has two equally likely outcomes. Probability is favorable outcomes over total outcomes.",
        "P(heads) = 1/2.",
        "Outcomes {heads, tails}. One of the two is heads.",
        "crt-sprint-probability",
        "Lesson: Equally likely outcomes. This is the only probability item in the sprint lesson.",
        ["The sample space has 2 outcomes.", "Exactly one is heads.", "1/2 is the probability."],
        {
            "1/3": "A coin does not have three equally likely outcomes.",
            "1": "1 would mean heads is certain. Tails is also possible.",
            "1/4": "1/4 would be one face of a four-outcome experiment, not one coin toss.",
        },
    ),
    _note(
        "A multiplicative pattern must fit every step, not only the first gap.",
        "Each term is the previous term × 2.",
        "16 × 2 = 32.",
        "crt-logical-patterns",
        "Published lesson: Number patterns. The published check syl-crt-q02 uses the different rule ×2+1.",
        ["2×2=4, 4×2=8, and 8×2=16.", "The same rule gives 16×2=32.", "24, 30, and 18 do not continue the doubling."],
        {
            "24": "24 would add 8, but every earlier step multiplied by 2.",
            "30": "30 is 16+14. The earlier gaps are not +14.",
            "18": "18 is 16+2. The series is not increasing by 2.",
        },
    ),
    _note(
        "An arithmetic progression adds the same difference at every step.",
        "Missing term = previous term + common difference.",
        "15 + 5 = 20, and 20 + 5 = 25.",
        "crt-logical-patterns",
        "Check the rule on the published number-patterns lesson, then the square-number item in this set.",
        ["The known gaps are 10−5=5 and 15−10=5.", "The next term is 15+5=20.", "20+5=25, so the given last term agrees."],
        {
            "18": "18 leaves a gap of 3, then a gap of 7 before 25. The gaps are not constant.",
            "22": "22 leaves a gap of 7, then only 3 before 25.",
            "21": "21 leaves gaps of 6 and 4. The series uses a gap of 5.",
        },
    ),
    _note(
        "Square numbers are 1², 2², 3², and so on. The next square uses the next integer.",
        "n² for n = 1, 2, 3, 4, 5.",
        "5² = 25.",
        "crt-logical-patterns",
        "The number-patterns lesson asks you to test one rule on every term. These are the first five squares.",
        ["1, 4, 9, and 16 are 1², 2², 3², and 4².", "The next integer is 5.", "5² = 25."],
        {
            "20": "20 is not a perfect square, and it is not 4²+4.",
            "24": "24 continues neither the squares nor a constant gap.",
            "36": "36 is 6², which skips 5².",
        },
    ),
    _note(
        "An odd-one-out item is the term that breaks the rule the others share.",
        "A doubling chain is previous × 2.",
        "3, 6, 12, 24, 48 doubles each time. 36 does not.",
        "crt-logical-patterns",
        "Use the published pattern lesson. Reject a term that only looks close.",
        ["3×2=6, 6×2=12, 12×2=24, and 24×2=48.", "36 is not produced by that rule.", "36 is the term that does not belong."],
        {
            "48": "48 is 24×2, so it belongs to the doubling chain.",
            "12": "12 is 6×2, so it belongs.",
            "6": "6 is 3×2, so it belongs.",
        },
    ),
    _note(
        "When the differences themselves double, the next difference follows that doubling.",
        "Next term = last term + next doubled difference.",
        "Differences 3, 6, 12. Next difference 24. 28+24=52.",
        "crt-logical-patterns",
        "This is the same difference-doubling idea as the published 2, 5, 11, 23 example, with different numbers.",
        ["10−7=3, 16−10=6, and 28−16=12.", "Those differences double, so the next difference is 24.", "28+24=52."],
        {
            "40": "40 adds 12 again. The differences are doubling, not staying at 12.",
            "46": "46 adds 18. 18 is not the next doubled difference.",
            "48": "48 adds 20. 20 is not 24.",
        },
    ),
    _note(
        "A conclusion is forced only when every arrangement of the statements includes it.",
        "All A are B and some B are C does not force some A are C.",
        "Cats can sit entirely outside the pet circle while every cat is still a mammal.",
        "crt-sprint-syllogisms",
        "Lesson: Syllogisms. Practice the other four items on that lesson.",
        ["The first statement puts every cat inside mammals.", "The second statement only says that some mammals are pets.", "Those pets need not be cats, so “some cats are pets” is not forced."],
        {
            "All cats are mammals": "This repeats the first statement, so it is given, not an extra conclusion.",
            "Some mammals are pets": "This repeats the second statement.",
            "Cats belong to the mammal class": "This restates the first statement.",
        },
    ),
    _note(
        "A universal affirmative transfers to a named member of the first group.",
        "All engineers are graduates. Ravi is an engineer. Therefore Ravi is a graduate.",
        "If every engineer is a graduate and Ravi is an engineer, Ravi is a graduate.",
        "crt-sprint-syllogisms",
        "Syllogisms lesson. Do not reverse the statement into “all graduates are engineers”.",
        ["Ravi is inside the engineer group.", "The engineer group is inside the graduate group.", "Ravi is therefore a graduate."],
        {
            "Ravi is not a graduate": "That contradicts “all engineers are graduates”.",
            "Some graduates are not engineers": "The statements do not say whether every graduate is an engineer.",
            "No graduate is an engineer": "That contradicts the premise that engineers are graduates.",
        },
    ),
    _note(
        "“No A is B” plus “all B are C” forces some C (the B's) to lie outside A, when the B group exists.",
        "Some gadgets are not phones.",
        "Every laptop is a gadget and no laptop is a phone, so those gadgets are not phones.",
        "crt-sprint-syllogisms",
        "Stay on the syllogisms lesson. Do not widen “some” into “no” or “all”.",
        ["All laptops are gadgets.", "No phone is a laptop, so those laptops are not phones.", "Therefore some gadgets are not phones."],
        {
            "No gadget is a phone": "Phones could still be gadgets that are not laptops.",
            "All gadgets are laptops": "The statements never say that every gadget is a laptop.",
            "All phones are laptops": "That contradicts “no phone is a laptop”.",
        },
    ),
    _note(
        "“Some” means at least one. It does not mean all.",
        "Some books are novels, and all novels are fiction, so those books are fiction.",
        "A book that is a novel must be fiction. At least one book is a novel.",
        "crt-sprint-syllogisms",
        "Syllogisms lesson. Compare this with the cat item, where the overlap is not forced.",
        ["At least one book is a novel.", "Every novel is fiction.", "That book is fiction, so some books are fiction."],
        {
            "All books are fiction": "Only some books were said to be novels. Other books may not be fiction.",
            "No book is fiction": "This contradicts the books that are novels.",
            "All fiction is novels": "Fiction could be wider than novels.",
        },
    ),
    _note(
        "A statement that contradicts a premise is definitely false. A possible overlap is not definitely false.",
        "All A are B means it is false that no B is A, taking the groups as non-empty in the usual placement reading.",
        "If every A is a B, then those members are both A and B. “No B is A” cannot stand.",
        "crt-sprint-syllogisms",
        "Syllogisms lesson. Placement items treat these groups as having members.",
        ["All A are B puts every A inside B.", "Those members are B's that are also A's.", "“No B is A” denies that, so it is false."],
        {
            "Some A may be C": "This is possible. “Some B are C” can include A's. It is not definitely false.",
            "All A are B": "This is the first premise, so it is not false.",
            "Some B are C": "This is the second premise, so it is not false.",
        },
    ),
    _note(
        "When a group acts as one unit, placement tests use a singular verb.",
        "The team is ready.",
        "One team, one unit: “is”.",
        "crt-sprint-grammar",
        "Lesson: Error spotting. British English sometimes uses “are” for team members. This item follows the unit reading the sentence asks for.",
        ["The subject is “the team” as one unit.", "A singular unit takes “is”.", "“The team is ready for the demo.” is the grammatical sentence."],
        {
            "The team are ready for the demo.": "“Are” treats the members separately. The sentence gives no member-by-member reading.",
            "The team were ready for the demo yesterday morning only if plural.": "That string is not a finished grammatical sentence.",
            "The team be ready for the demo.": "“Be” is not the finite verb this sentence needs.",
        },
    ),
    _note(
        "Two independent clauses joined by “and” take a comma before the conjunction.",
        "Clause, and clause.",
        "“I finished the report” and “I sent it to my manager” are both independent.",
        "crt-sprint-grammar",
        "Error-spotting lesson. The comma belongs before “and”, not after it and not inside a phrase.",
        ["Find the two clauses.", "Join them with a comma and “and”.", "The correct sentence is “I finished the report, and I sent it to my manager.”"],
        {
            "I finished the report and, I sent it to my manager.": "The comma is after “and”, which splits the conjunction from the clause it joins.",
            "I finished, the report and I sent it to my manager.": "The comma splits “finished” from its object.",
            "I finished the report and I, sent it to my manager.": "The comma splits the subject “I” from its verb.",
        },
    ),
    _note(
        "A finished past action uses the simple past form, not the base, the past participle, or the -ing form alone.",
        "go → went.",
        "She went to the interview yesterday.",
        "crt-sprint-grammar",
        "Error-spotting lesson. “Yesterday” marks a completed past action.",
        ["The time word is “yesterday”.", "The simple past of “go” is “went”.", "“She went to the interview yesterday.”"],
        {
            "She go to the interview yesterday.": "“Go” is present. It does not match “yesterday”.",
            "She gone to the interview yesterday.": "“Gone” needs an auxiliary such as “has”. Alone it is not a finite past.",
            "She going to the interview yesterday.": "“Going” needs an auxiliary. It is not simple past.",
        },
    ),
    _note(
        "Choose “a” or “an” from the sound, not from the spelling. “Hour” starts with a vowel sound.",
        "an + vowel sound. a + consonant sound.",
        "“Hour” sounds like “our”, so “an hour”.",
        "crt-sprint-grammar",
        "Error-spotting lesson. Silent h does not make a consonant sound.",
        ["Say the word “hour”.", "The first sound is a vowel.", "Use “an”: “She waited for an hour.”"],
        {
            "She waited for a hour.": "“A” is for a consonant sound. “Hour” does not start with one.",
            "She waited for the hour indefinite.": "That is not a grammatical article pattern.",
            "She waited for hour.": "A singular countable noun needs an article here.",
        },
    ),
    _note(
        "With “neither…nor”, the verb agrees with the subject closer to it.",
        "Neither X nor Y + verb agreeing with Y.",
        "The nearer subject is “managers”, which is plural, so “are”.",
        "crt-sprint-grammar",
        "Error-spotting lesson. Do not agree the verb with “intern” when “managers” is nearer.",
        ["Find the two subjects: intern and managers.", "The nearer subject is managers.", "Plural “managers” takes “are”."],
        {
            "Neither the intern nor the managers is available.": "“Is” agrees with “intern”, which is not the nearer subject.",
            "Neither the intern nor the managers am available.": "“Am” agrees with “I”, and there is no “I” here.",
            "Neither the intern nor the managers be available.": "“Be” is not the finite present verb.",
        },
    ),
    _note(
        "A synonym is a word with nearly the same meaning in the given use.",
        "brief ≈ short or concise.",
        "A brief answer is a short answer.",
        "crt-sprint-vocabulary",
        "Vocabulary lesson in this batch. The published verbal lesson is about sentence meaning, not this synonym pair.",
        ["Read “brief” as duration or length of speech.", "The close meaning is short.", "Lengthy is the opposite direction."],
        {
            "Lengthy": "Lengthy means long, which is the opposite of brief.",
            "Complex": "Complex means made of many parts, not short.",
            "Loud": "Loud is about sound, not length.",
        },
    ),
    _note(
        "An antonym is a word of opposite meaning.",
        "scarce ↔ abundant.",
        "Scarce water is the opposite of abundant water.",
        "crt-sprint-vocabulary",
        "Vocabulary lesson. Rare is a near synonym of scarce, so it cannot be the antonym.",
        ["Scarce means there is not enough.", "The opposite is plentiful.", "Abundant means plentiful."],
        {
            "Rare": "Rare is close to scarce, not opposite to it.",
            "Tiny": "Tiny is about size. Scarce is about supply.",
            "Hidden": "Hidden is about visibility, not supply.",
        },
    ),
    _note(
        "Use the meaning that fits the sentence. Here candid describes the answer.",
        "candid = frank or honest.",
        "A candid answer says what the person actually thinks.",
        "crt-sprint-vocabulary",
        "Vocabulary lesson. Do not import a different sense that the sentence does not support.",
        ["The word modifies “answer”.", "A candid answer is an honest one.", "Angry, confused, and delayed describe other states."],
        {
            "Angry": "Angry describes temper. Candid does not.",
            "Confused": "Confused describes uncertainty. Candid does not.",
            "Delayed": "Delayed describes timing. Candid does not.",
        },
    ),
    _note(
        "A synonym can be a plain verb. Purchase and buy name the same action.",
        "purchase = buy.",
        "To purchase a book is to buy a book.",
        "crt-sprint-vocabulary",
        "Vocabulary lesson. Sell, borrow, and repair are different transactions.",
        ["Identify the action: obtaining something by paying.", "Buy names that action.", "The other verbs do not."],
        {
            "Sell": "Sell is the other side of the transaction.",
            "Borrow": "Borrow is temporary and is not the same as purchase.",
            "Repair": "Repair changes an object's condition. It is not a purchase.",
        },
    ),
    _note(
        "In a risk sentence, mitigate means to make the harm smaller, not to ignore it.",
        "mitigate = reduce the severity.",
        "A team mitigates a risk by lowering its impact or chance.",
        "crt-sprint-vocabulary",
        "Vocabulary lesson. Documenting a risk is not the same as reducing it.",
        ["The context is risk.", "Mitigate means lessen.", "The closest choice is “Reduce the severity”."],
        {
            "Ignore completely": "Ignoring a risk leaves the severity unchanged.",
            "Celebrate": "Celebrate does not reduce a risk.",
            "Document only": "A document records the risk. It does not by itself reduce the severity.",
        },
    ),
    _note(
        "A table cell is read from its row and column. Do not add cells the question did not ask for.",
        "February sales are the Feb cell.",
        "Feb = 150.",
        "crt-di-tables",
        "Published lesson: Reading a simple data table. Related practice is syl-crt-q04 and the other table items here.",
        ["Find the February column or row.", "Read 150.", "120 and 130 are other months. 400 is the three-month total, which was not asked."],
        {
            "120": "120 is January.",
            "130": "130 is March.",
            "400": "400 is 120+150+130. The question asks for February only.",
        },
    ),
    _note(
        "A total is the sum of every group in the table, once.",
        "Total = 40 + 35 + 25.",
        "40 + 35 = 75, and 75 + 25 = 100.",
        "crt-di-tables",
        "Use the published table lesson. Do not stop after two classes.",
        ["Add class A and class B: 75.", "Add class C: 100.", "Every class is included once."],
        {
            "90": "90 drops 10 students. 40+35+25 is 100.",
            "110": "110 adds 10 students who are not in the table.",
            "75": "75 is only class A plus class B. Class C is missing.",
        },
    ),
    _note(
        "The average is the sum divided by the number of values.",
        "Average = (80 + 70 + 90) / 3.",
        "240 / 3 = 80.",
        "crt-di-tables",
        "Table lesson. 80 is both the Math cell and the average. The average is the result of the division, not a guess that the middle subject is the answer.",
        ["Add 80 + 70 + 90 = 240.", "There are 3 subjects.", "240 / 3 = 80."],
        {
            "70": "70 is the Science mark, not the average.",
            "90": "90 is the English mark, not the average.",
            "85": "85 is (80+90)/2 and leaves Science out.",
        },
    ),
    _note(
        "The maximum is the largest cell, not the first cell.",
        "Compare 12, 18, and 10.",
        "18 is larger than 12 and 10, so Blue.",
        "crt-di-tables",
        "Table lesson. “All equal” would need the three cells to match.",
        ["Read Red 12, Blue 18, Green 10.", "18 is the largest.", "The color is Blue."],
        {
            "Red": "12 is less than 18.",
            "Green": "10 is less than 18.",
            "All equal": "12, 18, and 10 are not equal.",
        },
    ),
    _note(
        "A range in a table is the highest cell minus the lowest cell.",
        "Difference = maximum − minimum.",
        "70 − 35 = 35.",
        "crt-di-tables",
        "Table lesson. Name the cities only to find the cells. The question asks for the difference.",
        ["The cells are 40, 55, 35, and 70.", "The highest is 70 and the lowest is 35.", "70 − 35 = 35 mm."],
        {
            "30 mm": "30 is 70−40, which uses P instead of the lowest city R.",
            "40 mm": "40 is city P's rainfall, not the range.",
            "15 mm": "15 is 55−40, which ignores both the highest and the lowest.",
        },
    ),
    _note(
        "A bar difference is the taller bar minus the shorter bar.",
        "Android − iOS = 500 − 300.",
        "500 − 300 = 200.",
        "crt-sprint-charts",
        "Charts lesson. Adding the bars answers a different question.",
        ["Read Android 500 and iOS 300.", "Subtract.", "The difference is 200."],
        {
            "800": "800 is the sum 500+300. The question asks how many more, which is a difference.",
            "300": "300 is the iOS bar, not the gap.",
            "100": "100 is not 500−300.",
        },
    ),
    _note(
        "The largest pie slice is the greatest share. The shares must be compared, not assumed equal.",
        "Compare 25%, 40%, and 35%.",
        "40% is larger than 35% and 25%, so Rent.",
        "crt-sprint-charts",
        "Charts lesson. 25+40+35=100, so the pie is complete and the slices are not equal.",
        ["List the shares.", "40 is the largest number.", "That share is Rent."],
        {
            "Food": "Food is 25%, which is smaller than Rent.",
            "Other": "Other is 35%, which is smaller than Rent.",
            "All equal": "25, 40, and 35 are not equal.",
        },
    ),
    _note(
        "The highest bar is the greatest value, regardless of its position.",
        "Compare 40, 50, 45, and 65.",
        "65 is the largest, and it is Q4.",
        "crt-sprint-charts",
        "Charts lesson. Q2 is second. It is not the highest.",
        ["Read Q1 40, Q2 50, Q3 45, Q4 65.", "65 is the maximum.", "Q4 is the quarter."],
        {
            "Q2": "Q2 is 50, which is less than 65.",
            "Q1": "Q1 is 40, the smallest bar.",
            "Q3": "Q3 is 45, which is less than 65.",
        },
    ),
    _note(
        "A pie angle is the group's fraction of the circle, and a full circle is 360°.",
        "Angle = people / total people × 360.",
        "45/180 × 360 = 90.",
        "crt-sprint-charts",
        "Charts lesson. Do not treat the headcount as a degree measure.",
        ["The team is 45 out of 180.", "45/180 = 1/4.", "1/4 of 360° is 90°."],
        {
            "45°": "45 is the number of people, not the angle.",
            "180°": "180° would be half the company, 90 people, not 45.",
            "60°": "60° would be 1/6 of the circle, which is 30 people, not 45.",
        },
    ),
    _note(
        "A bar's percentage is that bar divided by the sum of the bars.",
        "Percent = part / total × 100.",
        "12+8+16+4=40. 16/40 × 100 = 40%.",
        "crt-sprint-charts",
        "Charts lesson. 16% copies the defect count and skips the total.",
        ["Add 12+8+16+4 = 40 defects.", "Module C has 16 of them.", "16/40 = 0.40 = 40%."],
        {
            "16%": "16 is the count. The percentage is 16 out of 40, which is 40%.",
            "50%": "50% of 40 would be 20 defects. C has 16.",
            "30%": "30% of 40 would be 12 defects, which is module A.",
        },
    ),
]


ARRAY_NOTES = [
    _note(
        "A 0-indexed array of length n uses the integers 0, 1, …, n−1. Index n is past the last slot.",
        "Valid indices: 0 ≤ i ≤ n−1.",
        "Length 4 uses indices 0, 1, 2, and 3.",
        "dsa-arrays-strings",
        "Published arrays lesson, then the array questions in the practice catalog. Coding practice: max-element.",
        ["The first slot is index 0.", "The last slot is one less than the length.", "The valid range is 0 to n−1."],
        {
            "1 to n": "That skips index 0 and then uses index n, which is outside the array.",
            "0 to n": "Index n is one past the last element.",
            "-1 to n": "Both −1 and n are outside a 0-indexed array of length n.",
        },
        algorithm="Read the length. The last legal index is length − 1. Dry run: [a,b,c,d] has indices 0,1,2,3. Time O(1) to compute the bounds. Space O(1). Edge case: n = 0 has no valid index.",
    ),
    _note(
        "Inserting at the front of a contiguous array moves every current element one slot to the right.",
        "Front insert on a dynamic array is O(n) element moves.",
        "Inserting x at the front of [a,b,c] writes [x,a,b,c] after shifting three items.",
        "dsa-arrays-strings",
        "Arrays lesson. A linked list can insert at the head in O(1). This question is about a plain array.",
        ["The new item needs index 0.", "Every old item moves one index higher.", "That shift touches n items, so the cost is O(n)."],
        {
            "O(1)": "O(1) would be true for a structure with a free head pointer, not for shifting a contiguous array.",
            "O(log n)": "Nothing is being halved. The work is a shift of n items.",
            "O(n²) always": "One front insert shifts n items once. It is not a nested n×n shift.",
        },
        algorithm="Shift from the last index down to 0, then write the new value at 0. Dry run: [a,b,c] → [a,b,c,_] → [a,b,c,c] → [a,b,b,c] → [a,a,b,c] → [x,a,b,c]. Time O(n). Extra space O(1). Edge case: an empty array inserts in O(1).",
    ),
    _note(
        "An unsorted array has no order you can use to skip elements. The maximum can be anywhere.",
        "Worst-case comparisons to find the maximum: Θ(n).",
        "In [3,1,4], the scan sees 3, then 1, then 4, and keeps 4.",
        "dsa-arrays-strings",
        "Arrays lesson. Coding practice in the DSA list: max-element.",
        ["Start with the first value as the candidate.", "Compare every remaining value.", "n elements require a linear number of comparisons."],
        {
            "Θ(1)": "A constant check cannot look at a later, larger value.",
            "Θ(log n)": "Halving needs a sorted order. The array is unsorted.",
            "Θ(n²) minimum always": "One comparison per extra element is enough. Quadratic work is not required.",
        },
        algorithm="candidate ← A[1]; for each later value, replace candidate if the value is larger. Dry run [3,1,4]: 3, then 3, then 4. Time Θ(n). Space O(1). Edge case: one element returns that element with no extra comparison.",
    ),
    _note(
        "Adding two equal-length arrays element by element visits each index once.",
        "One loop from 0 to n−1 is O(n).",
        "[1,2] + [3,4] = [4,6] after two additions.",
        "dsa-arrays-strings",
        "Arrays lesson. Do not square the cost because there are two arrays.",
        ["Each index does one addition.", "There are n indices.", "The loop is O(n)."],
        {
            "O(1)": "The work grows when n grows. It is not constant.",
            "O(n²)": "There is no nested loop over the pairs of indices.",
            "O(2ⁿ)": "Nothing branches into two recursive calls per element.",
        },
        algorithm="For i from 0 to n−1, C[i] ← A[i] + B[i]. Dry run n=2: index 0 writes 4, index 1 writes 6. Time O(n). Output space O(n). Extra working space O(1). Edge case: n = 0 writes an empty result.",
    ),
    _note(
        "Kadane's scan keeps the best sum that ends at the current index and the best sum seen anywhere.",
        "Classic non-empty maximum subarray: O(n) time and O(1) extra space.",
        "On [−2,1,−3,4,−1,2,1], the best ending sums reach 4, 3, 5, 6. The answer is 6, from [4,−1,2,1].",
        "dsa-arrays-strings",
        "Arrays lesson. The quadratic double loop also works, but it is not required.",
        ["At each index, extend the previous ending sum or start over.", "Also keep the best sum so far.", "Each index is visited once."],
        {
            "O(n²) required always": "A linear scan exists, so quadratic time is not required.",
            "O(log n)": "The algorithm does not discard half of an unsorted array.",
            "O(n!)": "There is no permutation of the array.",
        },
        algorithm="ending ← A[0]; best ← A[0]; for each next x: ending ← max(x, ending+x); best ← max(best, ending). Dry run [1,−2,3]: ending 1, then 1, then 3; best 3. Time O(n). Space O(1). Edge case: all negative values return the largest single value for the non-empty version.",
    ),
    _note(
        "A hash map stores a value's index so the complement can be checked in expected constant time.",
        "One pass two-sum: average O(n) time and O(n) extra space.",
        "Target 9 on [2,7,11]: see 2, store it; see 7, find 9−7=2. The pair is the stored index and the current index.",
        "dsa-arrays-strings",
        "Arrays lesson. Coding practice: two-sum. The average bound assumes a good hash and no pathological collisions.",
        ["For each value, look up target − value.", "If it is missing, store the current value.", "Each of the n steps does expected O(1) work."],
        {
            "O(n²) unavoidable": "The nested-pair scan is O(n²). The hash scan avoids that on average.",
            "O(1) time always": "Every element may need to be read. The time is not constant.",
            "O(n log n) space minimum": "The map stores up to n entries. It does not need n log n space.",
        },
        algorithm="map starts empty. For i, x in the array: if target−x is in the map, return both indices; else map[x] ← i. Dry run [2,7] target 9: store 2, then find it from 7. Time O(n) average. Space O(n). Edge case: no pair returns an empty result. Duplicate values need the index, not just a set of values.",
    ),
    _note(
        "In-place reverse swaps the ends and walks inward. The extra memory does not grow with n.",
        "Auxiliary space O(1). Time O(n).",
        "[a,b,c,d] swaps to [d,b,c,a], then [d,c,b,a].",
        "dsa-arrays-strings",
        "The published arrays lesson traces this swap. Coding practice: reverse-string uses the same two-end idea on characters.",
        ["Set left at the first index and right at the last.", "Swap, then move inward.", "Only a few index variables are extra."],
        {
            "O(n) auxiliary required": "A second array would use O(n). The in-place swap does not.",
            "O(n²) auxiliary": "The swaps do not allocate a quadratic table.",
            "O(log n) auxiliary required": "The iterative swap does not build a recursion stack of depth log n.",
        },
        algorithm="while left < right: swap A[left], A[right]; left ← left+1; right ← right−1. Dry run [a,b,c,d] → [d,b,c,a] → [d,c,b,a]. Time O(n). Space O(1). Edge cases: empty and one-element arrays do nothing.",
    ),
    _note(
        "A write index can copy the non-zero values forward, then fill the tail with zeros.",
        "O(n) time and O(1) extra space, preserving the order of non-zeros.",
        "[0,1,0,3] becomes [1,3,0,0].",
        "dsa-arrays-strings",
        "Arrays lesson. The stable order is the order the non-zero values already had.",
        ["Walk once and write each non-zero to the next output slot.", "Fill the remaining slots with zero.", "The walk is linear and uses only the write index as extra memory."],
        {
            "Only O(n²) time": "One pass is enough. Nested shifting is not required.",
            "Only with O(n) extra always": "Writing into the same array avoids a second array.",
            "O(log n) time": "Every element may be a zero that still has to be seen.",
        },
        algorithm="write ← 0. For each x: if x ≠ 0, A[write] ← x and write ← write+1. Then fill from write to the end with 0. Dry run [0,1,0,3] → [1,1,0,3] → [1,3,0,3] → [1,3,0,0]. Time O(n). Space O(1). Edge case: all zeros stays all zeros.",
    ),
    _note(
        "A prefix sum stores the sum of the array from the start through each index.",
        "Build in O(n). A range sum is then O(1).",
        "A = [2,4,6]. Prefix = [2,6,12]. Sum from index 1 through 2 is 12−2 = 10.",
        "dsa-arrays-strings",
        "Arrays lesson. The preprocess cost is paid once, then each query is a subtraction.",
        ["P[0] = A[0].", "P[i] = P[i−1] + A[i].", "Sum from L to R is P[R] − P[L−1], using 0 when L is 0."],
        {
            "O(n) per query always with no benefit": "That is the cost without a prefix array. With one, the query is a subtraction.",
            "O(n²) preprocess mandatory": "Each prefix cell adds one value. The build is linear.",
            "O(log n) preprocess only": "Every element must be added once. The build is not logarithmic.",
        },
        algorithm="Build P, then answer sum(L,R) by one subtraction. Dry run [2,4,6], query 1..2: 12−2=10. Build time O(n). Query time O(1). Extra space O(n). Edge case: L = 0 uses P[R] with no subtraction.",
    ),
    _note(
        "The Dutch national flag partition groups 0, then 1, then 2 with three pointers in one pass.",
        "O(n) time and O(1) extra space.",
        "[2,0,1] becomes [0,1,2].",
        "dsa-arrays-strings",
        "Arrays lesson. Sorting would also group them, but the three-way partition does not need O(n log n).",
        ["low marks the end of the 0s. mid scans. high marks the start of the 2s.", "Swap 0s toward low and 2s toward high.", "Each element is moved a constant number of times."],
        {
            "O(n log n) time required": "Comparison sorting is enough but not required for three known keys.",
            "O(n²) time": "The pointers only move inward. They do not nest.",
            "O(n) space required": "The swaps happen inside the same array.",
        },
        algorithm="low ← 0; mid ← 0; high ← n−1. While mid ≤ high: 0 swaps with low and both advance; 1 advances mid; 2 swaps with high and high retreats. Dry run [2,0,1] → [1,0,2] → [0,1,2]. Time O(n). Space O(1). Edge case: an array of only one value never needs a nested pass.",
    ),
]


def _q(key, skill, difficulty, stem, correct, wrongs, explanation, why, domain, category, topic):
    options = [{"key": "A", "text": correct, "correct": True, "why": "This matches the checked result."}]
    for letter, text in zip("BCD", wrongs, strict=True):
        options.append({"key": letter, "text": text, "correct": False, "why": why[text]})
    return {
        "key": key,
        "stem": stem,
        "skill": skill,
        "difficulty": difficulty,
        "mode": "single",
        "version": 1,
        "domain_slug": domain,
        "category_slug": category,
        "topic_slug": topic,
        "marks": 1,
        "negative_marks": 0.25,
        "estimated_time_seconds": 90,
        "options": options,
        "explanation": explanation,
    }


def _explain(difficulty, correct, note, domain, category, topic):
    why_lines = "\n".join(f"- {label}: {reason}" for label, reason in note["why"].items())
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(note["steps"], start=1))
    if note["lesson"] in PUBLISHED:
        lesson_title = PUBLISHED[note["lesson"]]
    else:
        lesson_title = LESSON_TITLES[note["lesson"]]
    algorithm = ""
    if note["algorithm"]:
        algorithm = (
            "\n\nWorked algorithm\n"
            + note["algorithm"]
            + "\n\nDry run, time complexity, space complexity, and edge cases are in that algorithm trace."
        )
    return (
        f"Difficulty: {difficulty}\n"
        f"Correct answer: {correct}\n\n"
        f"Step-by-step\n{steps}\n\n"
        f"Why other options are wrong\n{why_lines}\n\n"
        f"Learn the concept\n{note['concept']}\n\n"
        f"Formula or key principle\n{note['formula']}\n\n"
        f"Worked example\n{note['worked']}"
        f"{algorithm}\n\n"
        f"Related lesson\n{note['lesson']} — {lesson_title}. {note['related']}\n\n"
        f"Topic metadata\ndomain={domain}; category={category}; topic={topic}; difficulty={difficulty}; type=single-choice"
    )


LESSON_TITLES = {
    "crt-sprint-profit-loss": "Profit and loss on cost price",
    "crt-sprint-time-work": "Time and work rates",
    "crt-sprint-probability": "Equally likely outcomes",
    "crt-sprint-syllogisms": "What a syllogism forces",
    "crt-sprint-grammar": "Error spotting in short sentences",
    "crt-sprint-vocabulary": "Synonyms and antonyms in context",
    "crt-sprint-charts": "Bar charts and pie shares",
    "dsa-sprint-strings": "Scanning a string",
    "dsa-sprint-searching": "Linear and binary search",
    "dsa-sprint-complexity": "Checking a big-O claim",
}


def _selected_questions() -> list[dict]:
    aptitude = _load("phase11_aptitude_mcq.py", "APTITUDE_MCQS")
    technical = _load("phase11_technical_mcq.py", "TECHNICAL_MCQS")
    groups = (
        [("quantitative", "percentages", row) for row in _take(aptitude, "percentages", 4)]
        + [("quantitative", "profit-and-loss", row) for row in _take(aptitude, "profit-and-loss", 3)]
        + [("quantitative", "time-and-work", row) for row in _take(aptitude, "time-and-work", 2)]
        + [("quantitative", "probability", row) for row in _take(aptitude, "probability", 1)]
        + [("logical-reasoning", "series", row) for row in _take(aptitude, "series", 5)]
        + [("logical-reasoning", "syllogisms", row) for row in _take(aptitude, "syllogisms", 5)]
        + [("verbal", "grammar", row) for row in _take(aptitude, "grammar", 5)]
        + [("verbal", "vocabulary", row) for row in _take(aptitude, "vocabulary", 5)]
        + [("data-interpretation", "tables", row) for row in _take(aptitude, "tables", 5)]
        + [("data-interpretation", "charts", row) for row in _take(aptitude, "charts", 5)]
    )
    if len(groups) != len(NOTES):
        raise SystemExit(f"notes {len(NOTES)} groups {len(groups)}")
    questions = []
    prefixes = {
        "percentages": "pct",
        "profit-and-loss": "pl",
        "time-and-work": "tw",
        "probability": "pr",
        "series": "ser",
        "syllogisms": "syl",
        "grammar": "gr",
        "vocabulary": "voc",
        "tables": "tab",
        "charts": "ch",
    }
    seen: dict[str, int] = {}
    for (skill, topic, row), note in zip(groups, NOTES, strict=True):
        seen[topic] = seen.get(topic, 0) + 1
        domain, category, topic_slug, difficulty, stem, _seed, correct, w1, w2, w3 = row
        if set(note["why"]) != {w1, w2, w3}:
            raise SystemExit(f"why keys do not match options for {stem}")
        questions.append(
            _q(
                f"sprint1-{prefixes[topic]}-{seen[topic]:02d}",
                skill,
                difficulty,
                stem,
                correct,
                [w1, w2, w3],
                _explain(difficulty, correct, note, domain, category, topic_slug),
                note["why"],
                domain,
                category,
                topic_slug,
            )
        )
    for index, (row, note) in enumerate(zip(_take(technical, "arrays", 10), ARRAY_NOTES, strict=True), start=1):
        domain, category, topic_slug, difficulty, stem, _seed, correct, w1, w2, w3 = row
        if set(note["why"]) != {w1, w2, w3}:
            raise SystemExit(f"array why mismatch {stem}")
        questions.append(
            _q(
                f"sprint1-arr-{index:02d}",
                "arrays",
                difficulty,
                stem,
                correct,
                [w1, w2, w3],
                _explain(difficulty, correct, note, domain, category, topic_slug),
                note["why"],
                domain,
                category,
                topic_slug,
            )
        )
    return questions


def _original(key, skill, difficulty, stem, correct, wrongs, why, steps, concept, formula, worked, lesson, related, domain, category, topic, algorithm):
    note = _note(concept, formula, worked, lesson, related, steps, why, algorithm=algorithm)
    if set(why) != set(wrongs):
        raise SystemExit(key)
    return _q(
        key,
        skill,
        difficulty,
        stem,
        correct,
        wrongs,
        _explain(difficulty, correct, note, domain, category, topic),
        why,
        domain,
        category,
        topic,
    )


def _original_questions() -> list[dict]:
    strings = [
        _original(
            "sprint1-str-01", "strings", "easy",
            "What is the reverse of the string \"ab\"?",
            "ba", ["ab", "a", "b"],
            {"ab": "ab is the original string. Reverse exchanges the ends.", "a": "a drops the second character.", "b": "b drops the first character."},
            ["The characters are index 0 = a and index 1 = b.", "Swap the two ends.", "The result is ba."],
            "Reversing a string rewrites its characters from the last index back to the first.",
            "Result[i] = source[n−1−i].",
            "\"ab\" → \"ba\".",
            "dsa-sprint-strings",
            "String-scan lesson. Coding practice in the DSA list: reverse-string.",
            "technical", "dsa", "strings",
            "Two pointers at the ends swap until they meet. Dry run \"ab\": swap once to \"ba\". Time O(n). A new string uses O(n) space; an in-place character buffer uses O(1) extra space. Edge cases: empty stays empty, and one character stays unchanged.",
        ),
        _original(
            "sprint1-str-02", "strings", "easy",
            "What is the reverse of an empty string?",
            "The empty string", ["A single space", "null as the word \"null\"", "The letter e"],
            {
                "A single space": "A space is a character. The input has no characters.",
                "null as the word \"null\"": "Empty is a string of length 0. It is not the four letters n-u-l-l.",
                "The letter e": "The letter e is not in the input.",
            },
            ["Count the characters: 0.", "There is no end character to move.", "The reverse is still empty."],
            "The empty string is a real string with length 0.",
            "Reverse of length 0 is length 0.",
            "\"\" reversed is \"\".",
            "dsa-sprint-strings",
            "String-scan lesson. This is the empty edge case of reverse-string.",
            "technical", "dsa", "strings",
            "If left starts at 0 and right starts at −1, the loop does not run. Dry run of \"\": no swap. Time O(1). Space O(1). Do not invent a space or a null word.",
        ),
        _original(
            "sprint1-str-03", "strings", "easy",
            "How many vowels are in \"team\"? Count a, e, i, o, and u only.",
            "2", ["1", "3", "4"],
            {"1": "That count keeps only e or only a, not both.", "3": "There are only four letters, and t and m are not vowels.", "4": "4 would count every letter, including t and m."},
            ["Letters: t, e, a, m.", "e and a are vowels.", "The count is 2."],
            "A vowel count is a single scan that adds one when the character is in the vowel set.",
            "Count = number of characters in {a, e, i, o, u}. This item does not treat y as a vowel.",
            "\"team\" → e and a → 2.",
            "dsa-sprint-strings",
            "String-scan lesson. Coding practice: count-vowels.",
            "technical", "dsa", "strings",
            "total ← 0; for each character, add 1 if it is a vowel. Dry run \"team\": t no, e yes, a yes, m no. Time O(n). Space O(1). Edge case: an empty string counts 0. Case must be decided; this item is lowercase.",
        ),
        _original(
            "sprint1-str-04", "strings", "easy",
            "Is \"level\" a palindrome?",
            "Yes, it reads the same forwards and backwards", ["No, because it has five letters", "No, because it starts with l", "Only if the middle letter is removed"],
            {
                "No, because it has five letters": "An odd length can still be a palindrome. The middle letter matches itself.",
                "No, because it starts with l": "The test is whether the ends match, and both ends are l.",
                "Only if the middle letter is removed": "Removing v would make \"leel\", but the original already matches.",
            },
            ["Compare index 0 with index 4: l and l.", "Compare index 1 with index 3: e and e.", "The middle v stands alone. The string is a palindrome."],
            "A palindrome matches at every pair of positions equally far from the two ends.",
            "S[i] = S[n−1−i] for every i.",
            "level ↔ level.",
            "dsa-sprint-strings",
            "String-scan lesson. The same two pointers used for reverse can stop at the first mismatch.",
            "technical", "dsa", "strings",
            "left ← 0; right ← 4. Both pairs match, so accept. Time O(n). Space O(1). Edge cases: empty and one-character strings are palindromes. This check is case-sensitive; \"Level\" would fail if L and l differ.",
        ),
        _original(
            "sprint1-str-05", "strings", "medium",
            "What is the first character that occurs once in \"aabbc\"?",
            "c", ["a", "b", "There is no such character"],
            {
                "a": "a occurs at the first two positions, so it is not unique.",
                "b": "b occurs twice, after the a's.",
                "There is no such character": "c occurs once, at the end.",
            },
            ["Count a:2, b:2, c:1.", "Walk again in original order.", "The first count of 1 is c."],
            "First unique character means the earliest character whose total frequency is one.",
            "Two scans: count frequencies, then return the first character with count 1.",
            "\"aabbc\" → c.",
            "dsa-sprint-strings",
            "String-scan lesson. A frequency map is the same idea as the vowel counter, with one bucket per character.",
            "technical", "dsa", "strings",
            "Count, then scan. Dry run: a is skipped because its count is 2, b is skipped, c is returned. Time O(n). Space O(1) for a fixed alphabet, otherwise O(k) for k distinct characters. Edge case: \"aabb\" has no unique character.",
        ),
        _original(
            "sprint1-str-06", "strings", "medium",
            "Are \"listen\" and \"silent\" anagrams?",
            "Yes, they use the same letters the same number of times", ["No, because the first letters differ", "No, because one is a reverse of the other", "Only if both are sorted in the output"],
            {
                "No, because the first letters differ": "Anagrams do not need the same first letter.",
                "No, because one is a reverse of the other": "silent is not listen reversed. listen reversed is netsil.",
                "Only if both are sorted in the output": "Sorting is a method you may use. The words are anagrams before you print them.",
            },
            ["Both have length 6.", "Sorted, both become eilnst.", "The letter counts match, so they are anagrams."],
            "Anagrams are equal frequency maps. Order does not matter.",
            "Sort both and compare, or compare two count maps.",
            "listen and silent both sort to eilnst.",
            "dsa-sprint-strings",
            "String-scan lesson. Sorting is O(n log n). Counting is O(n) for a fixed alphabet.",
            "technical", "dsa", "strings",
            "Count each letter in the first word and decrement with the second. Dry run: l,i,s,t,e,n then s,i,l,e,n,t all return to zero. Time O(n). Space O(1) for a fixed alphabet. Edge case: different lengths cannot be anagrams. Spaces and case are not present in this pair.",
        ),
        _original(
            "sprint1-str-07", "strings", "easy",
            "In the 0-indexed string \"code\", which character is at index 0?",
            "c", ["o", "d", "e"],
            {"o": "o is index 1.", "d": "d is index 2.", "e": "e is index 3."},
            ["Indexing starts at 0.", "The first character is c.", "c is the character at index 0."],
            "A string index picks one character. Index 0 is the first character.",
            "S[0] is the first character in a 0-indexed string.",
            "\"code\"[0] = c.",
            "dsa-sprint-strings",
            "String-scan lesson and the published arrays-and-strings lesson both use the start of the sequence.",
            "technical", "dsa", "strings",
            "Read S[0]. Dry run \"code\": positions 0:c, 1:o, 2:d, 3:e. Time O(1). Space O(1). Edge case: the empty string has no index 0.",
        ),
        _original(
            "sprint1-str-08", "strings", "easy",
            "What is the length of \"ab\" concatenated with \"c\"?",
            "3", ["2", "1", "5"],
            {"2": "2 is only the length of \"ab\".", "1": "1 is only the length of \"c\".", "5": "5 is not 2+1."},
            ["Length of \"ab\" is 2.", "Length of \"c\" is 1.", "2+1=3, and the string is \"abc\"."],
            "Concatenation copies both strings in order. The length is the sum of the lengths.",
            "length(X+Y) = length(X) + length(Y).",
            "\"ab\" + \"c\" = \"abc\", length 3.",
            "dsa-sprint-strings",
            "String-scan lesson. Building a new string costs time proportional to the characters copied.",
            "technical", "dsa", "strings",
            "Copy ab, then copy c. Dry run writes a, b, c. Time O(n+m). Space O(n+m) for the new string. Edge case: concatenating an empty string does not change the other length.",
        ),
        _original(
            "sprint1-str-09", "strings", "medium",
            "A two-pointer palindrome check that stops at the first mismatch uses how much extra memory?",
            "O(1) extra memory", ["O(n) extra memory required", "O(n²) extra memory", "O(2ⁿ) extra memory"],
            {
                "O(n) extra memory required": "A reversed copy would use O(n). The two pointers do not build that copy.",
                "O(n²) extra memory": "The check does not allocate a table of pairs.",
                "O(2ⁿ) extra memory": "The check does not branch on every character.",
            },
            ["Store two indices.", "Move them toward the center.", "The extra memory stays constant."],
            "Indices are scalar variables. They do not grow with the string.",
            "Extra space O(1). Time O(n) in the worst case, when the string is a palindrome.",
            "\"abba\" checks a/a, then b/b, and accepts.",
            "dsa-sprint-strings",
            "String-scan lesson. Compare this with building a reversed copy, which uses linear extra memory.",
            "technical", "dsa", "strings",
            "left and right move inward. Dry run \"abba\": both pairs match. Time O(n). Space O(1). Edge case: a mismatch returns false without reading the rest, so the best case can be O(1) time.",
        ),
        _original(
            "sprint1-str-10", "strings", "medium",
            "If strings cannot be edited in place, how much extra memory does building the reverse of an n-character string take?",
            "O(n) extra memory", ["O(1) extra memory", "O(log n) extra memory", "O(n²) extra memory"],
            {
                "O(1) extra memory": "O(1) fits an in-place buffer. A new string must hold n characters.",
                "O(log n) extra memory": "The new string is not a balanced tree of log n cells in this model.",
                "O(n²) extra memory": "Each character is stored once in the result, not n times.",
            },
            ["The result needs one slot per input character.", "Those n slots are new.", "The extra memory is O(n)."],
            "An immutable string operation allocates the result. The reverse result has n characters.",
            "Extra space Θ(n) for the new string. Time Θ(n) to copy.",
            "Reversing \"code\" allocates a new 4-character string \"edoc\".",
            "dsa-sprint-strings",
            "String-scan lesson. The coding problem reverse-string prints a new line; the extra output is proportional to n.",
            "technical", "dsa", "strings",
            "Allocate n cells and fill them from the end of the source. Dry run \"ab\" allocates \"ba\". Time O(n). Space O(n). Edge case: n = 0 allocates an empty result.",
        ),
    ]
    complexity = [
        _original(
            "sprint1-cx-01", "complexity", "easy",
            "Two nested loops each run from 1 to n, and the inner body is constant work. What is the time complexity?",
            "O(n²)", ["O(n)", "O(log n)", "O(1)"],
            {
                "O(n)": "One loop over n is linear. The inner loop multiplies that by another n.",
                "O(log n)": "Neither loop halves n.",
                "O(1)": "The number of body runs grows with n.",
            },
            ["The outer loop runs n times.", "For each outer step the inner loop runs n times.", "n × n = n²."],
            "Nested full loops multiply. Big-O keeps the dominant term.",
            "n × n constant steps is O(n²).",
            "n = 3 runs the body 9 times.",
            "dsa-sprint-complexity",
            "This lesson checks the count. The published lesson dsa-complexity traces the pair-counting loop, which is also quadratic.",
            "technical", "dsa", "basics",
            "for i in 1..n: for j in 1..n: do constant work. Dry run n=3: 9 body runs. Time O(n²). Extra space O(1) if the body allocates nothing. Edge case: n = 0 runs the body 0 times, which is still inside O(n²).",
        ),
        _original(
            "sprint1-cx-02", "complexity", "easy",
            "A loop sets x = n and repeatedly replaces x with floor(x/2) until x is 0. How many iterations grow with n?",
            "O(log n)", ["O(n)", "O(n²)", "O(1) for every n > 1"],
            {
                "O(n)": "The loop does not subtract 1. It discards half of x each time.",
                "O(n²)": "There is only one loop, and it shrinks x.",
                "O(1) for every n > 1": "Larger n needs more halvings. n = 8 takes more steps than n = 2.",
            },
            ["Each iteration halves x.", "The number of halvings until 1 is about log2(n).", "That growth is O(log n)."],
            "Halving reaches a constant after a logarithmic number of steps.",
            "Iterations are floor(log2 n) + 1 while x stays positive.",
            "n = 8: 8, 4, 2, 1, then the next step reaches 0. Four halvings from 8.",
            "dsa-sprint-complexity",
            "Complexity lesson. Binary search uses this same halving count.",
            "technical", "dsa", "basics",
            "while x > 0: x ← floor(x/2). Dry run 8 → 4 → 2 → 1 → 0. Time O(log n). Space O(1). Edge case: n = 1 finishes in one halving to 0.",
        ),
        _original(
            "sprint1-cx-03", "complexity", "medium",
            "Which big-O class matches 3n² + 2n + 7?",
            "O(n²)", ["O(n)", "O(n³)", "O(1)"],
            {
                "O(n)": "The n² term grows faster than the linear term, so the whole expression is not linear.",
                "O(n³)": "There is no n³ term. A looser cubic bound is not the tight class asked here.",
                "O(1)": "The cost grows with n.",
            },
            ["3n² dominates 2n and 7 as n grows.", "Drop the lower terms and the constant 3.", "The class is O(n²)."],
            "Big-O of a polynomial is the highest power, with its coefficient dropped.",
            "3n² + 2n + 7 is O(n²).",
            "At n = 10, 3×100 = 300, while 2×10+7 = 27. The square term already dominates.",
            "dsa-sprint-complexity",
            "Complexity lesson and the published dsa-complexity recap both say to drop lower-order terms.",
            "technical", "dsa", "basics",
            "Identify the highest power. Dry run of term sizes at n=10: 300, 20, and 7. Time class O(n²). This is a classification, so extra space is not introduced. Edge case: the classification is about growth, not the value at one small n.",
        ),
        _original(
            "sprint1-cx-04", "complexity", "medium",
            "A function does 20 steps of setup and then one loop of n additions. What is the time complexity?",
            "O(n)", ["O(1)", "O(n + 20) as a different class from O(n)", "O(20ⁿ)"],
            {
                "O(1)": "The loop still grows with n. The 20 setup steps do not cancel it.",
                "O(n + 20) as a different class from O(n)": "O(n + 20) is the same class as O(n). Adding a constant does not create a new class.",
                "O(20ⁿ)": "20ⁿ would be exponential. The 20 here is a fixed setup, not the base of an exponent.",
            },
            ["Setup is constant.", "The loop is linear.", "Constant plus linear is linear."],
            "O(1) + O(n) = O(n).",
            "20 + n steps.",
            "n = 5 does 25 additions-and-setup steps. n = 50 does 70. The growth follows n.",
            "dsa-sprint-complexity",
            "Complexity lesson. Constants are dropped in the class even though they matter on a real machine.",
            "technical", "dsa", "basics",
            "Count setup, then count the loop. Dry run n=4: 20 setup steps plus 4 loop steps. Time O(n). Space O(1) if each addition reuses one variable. Edge case: n = 0 leaves only the setup, which is allowed inside O(n).",
        ),
        _original(
            "sprint1-cx-05", "complexity", "hard",
            "You need the sum 1 + 2 + … + n. Which statement is accurate?",
            "The formula n(n+1)/2 is O(1); adding the integers one by one is O(n)", ["Both methods are O(1)", "Both methods are O(n²)", "The formula is O(n!)"],
            {
                "Both methods are O(1)": "Walking from 1 to n does work that grows with n.",
                "Both methods are O(n²)": "The loop adds once per integer. It is not a nested pair of loops. The formula is constant.",
                "The formula is O(n!)": "The formula uses a fixed number of arithmetic operations, not a factorial.",
            },
            ["The closed form multiplies n by n+1 and divides by 2.", "That is a fixed amount of arithmetic.", "The loop performs n additions."],
            "The same result can have two algorithms with different costs.",
            "Sum = n(n+1)/2.",
            "n = 4. Formula: 4×5/2 = 10. Loop: 1+2+3+4 = 10.",
            "dsa-sprint-complexity",
            "Complexity lesson. Choose the method the question names before you name the class.",
            "technical", "dsa", "basics",
            "Formula: three arithmetic operations. Loop: for i from 1 to n, add i. Dry run n=4 gives 10 either way. Formula time O(1), loop time O(n). Space O(1) for both if you store only the total. Edge case: n = 0 sums to 0.",
        ),
    ]
    searching = [
        _original(
            "sprint1-sea-01", "searching", "easy",
            "Linear search looks for 9 in [4, 1, 9, 7]. How many comparisons does it make until it finds 9?",
            "3", ["1", "2", "4"],
            {
                "1": "The first cell is 4, not 9.",
                "2": "The second cell is 1, not 9. The search has not found it yet.",
                "4": "4 would continue after the match. It can stop when 9 is found.",
            },
            ["Compare 4: no.", "Compare 1: no.", "Compare 9: yes. That is the third comparison."],
            "Linear search checks elements in order until it hits the target or finishes the array.",
            "Worst case, when the target is missing or last, is n comparisons. Here the target is third.",
            "[4, 1, 9, 7] finds 9 on comparison 3.",
            "dsa-sprint-searching",
            "Searching lesson. Coding practice: linear-search.",
            "technical", "dsa", "searching",
            "for each index, compare. Dry run: 4 no, 1 no, 9 yes, return index 2. Time O(k) until the match, O(n) worst case. Space O(1). Edge case: a missing target scans all n cells and reports not found.",
        ),
        _original(
            "sprint1-sea-02", "searching", "medium",
            "Binary search looks for 6 in the sorted array [2, 4, 6, 8, 10]. Which index does it return?",
            "2", ["0", "1", "4"],
            {
                "0": "Index 0 holds 2. The first middle is not the answer.",
                "1": "Index 1 holds 4. The search moves right after seeing 4 only if the middle is 4; in this array the first middle is 6.",
                "4": "Index 4 holds 10, which is past the target.",
            },
            ["low = 0 and high = 4. mid = 2.", "The value at mid is 6, which is the target.", "Return index 2."],
            "Binary search is valid on a sorted array. It compares the middle and discards half.",
            "mid = low + floor((high−low)/2), using a form that stays inside the index range.",
            "[2,4,6,8,10], target 6, first mid index 2, value 6.",
            "dsa-sprint-searching",
            "Searching lesson. Coding practice: binary-search. The published complexity lesson explains the log n count, not this index trace.",
            "technical", "dsa", "searching",
            "low 0, high 4, mid 2, A[2]=6, return 2. Dry run stops after one comparison. Time O(log n) worst case, O(1) in this lucky first hit. Space O(1) for the iterative form. Edge case: an even length uses the chosen mid formula consistently.",
        ),
        _original(
            "sprint1-sea-03", "searching", "medium",
            "What is the worst-case time of linear search when the target is absent?",
            "Θ(n)", ["Θ(1)", "Θ(log n)", "Θ(n²)"],
            {
                "Θ(1)": "A constant check cannot prove that a later cell is also a miss.",
                "Θ(log n)": "Linear search does not discard half of the array.",
                "Θ(n²)": "Each element is compared once, not once per pair.",
            },
            ["Every cell might have held the target.", "The search reads all n cells.", "The worst-case cost is linear."],
            "Absence is a worst case for linear search because no early match occurs.",
            "Worst-case comparisons = n.",
            "Searching for 5 in [1,2,3,4] compares all four cells.",
            "dsa-sprint-searching",
            "Searching lesson. Best case is still Θ(1) when the first cell matches. Do not call the best case the big-O worst case.",
            "technical", "dsa", "searching",
            "Scan every index and then report absent. Dry run [1,2,3] target 9: three misses. Time Θ(n). Space O(1). Edge case: an empty array returns absent in Θ(1), which is inside the linear bound for n = 0.",
        ),
        _original(
            "sprint1-sea-04", "searching", "medium",
            "Binary search is run on the unsorted array [5, 1, 4]. Which statement is right?",
            "The halving rule can discard the half that actually holds the target", ["It is reliable because every array supports halving", "It always returns index 0", "It sorts the array before the first comparison"],
            {
                "It is reliable because every array supports halving": "Halving is reliable only when every value on the left is ≤ the middle and every value on the right is ≥ it.",
                "It always returns index 0": "The return depends on the comparisons. It is not fixed at index 0.",
                "It sorts the array before the first comparison": "Standard binary search does not sort. Sorting would be a separate O(n log n) step.",
            },
            ["Binary search assumes sorted order.", "[5,1,4] is not sorted.", "A decision to discard the left or the right can throw away the target."],
            "Sorted order is a precondition, not a result, of binary search.",
            "If A[mid] is not the target, search only the side where a sorted array would still hold it.",
            "Looking for 1 with mid index 1 finds 1 by luck. Looking for 5 can move right if a comparison treats 1 as too small, and then 5 is never seen.",
            "dsa-sprint-searching",
            "Searching lesson. Sort first only if the question allows that extra cost.",
            "technical", "dsa", "searching",
            "Do not call binary search on unsorted data. Dry run target 5, low 0, high 2, mid 1, value 1. Moving right because 1 < 5 leaves [4] and loses 5. Time of the unsafe search is still O(log n), but the answer can be wrong. Edge case: a one-element array does not need order beyond that single cell.",
        ),
        _original(
            "sprint1-sea-05", "searching", "hard",
            "Binary search looks for 7 in the sorted array [1, 3, 5, 7, 9, 11]. Which sequence of middle values does the usual lower-mid formula produce before it returns?",
            "5, then 9, then 7", ["7 on the first comparison", "1, then 3, then 7", "11, then 9, then 7"],
            {
                "7 on the first comparison": "The first middle of six items is index 2, whose value is 5, not 7.",
                "1, then 3, then 7": "The search does not start at the left end.",
                "11, then 9, then 7": "The search does not start at the right end.",
            },
            ["low 0, high 5, mid 2, value 5. 7 is larger, so low becomes 3.", "low 3, high 5, mid 4, value 9. 7 is smaller, so high becomes 3.", "low 3, high 3, mid 3, value 7. Return index 3."],
            "Use one mid formula and follow it. This trace uses mid = low + floor((high−low)/2).",
            "Each step discards the side that cannot hold the target in a sorted array.",
            "Middles: index 2 → 5, index 4 → 9, index 3 → 7.",
            "dsa-sprint-searching",
            "Searching lesson. Coding practice: binary-search. Count the comparisons instead of assuming the target is the first middle.",
            "technical", "dsa", "searching",
            "Iterative binary search. Dry run middles 5, 9, 7. Time O(log n). Space O(1). Edge case: if the loop uses mid = (low+high)//2 on huge indexes, the sum can overflow in fixed-width integers; the low + (high−low)//2 form avoids that sum. An absent target ends when low passes high.",
        ),
    ]
    return strings + complexity + searching


def _check_math() -> None:
    assert 40000 - 40000 * 15 / 100 == 34000
    assert 0.4 * 250 == 100
    assert (75 - 60) / 60 * 100 == 25
    assert 640 / 8 == 80
    assert (920 - 800) / 800 * 100 == 15
    assert 45 / 450 * 100 == 10
    assert 5 * (1 / 15) == 1 / 3
    assert 16 * 2 == 32
    assert 15 + 5 == 20
    assert 5 ** 2 == 25
    assert 28 + 24 == 52
    assert 40 + 35 + 25 == 100
    assert (80 + 70 + 90) / 3 == 80
    assert 70 - 35 == 35
    assert 500 - 300 == 200
    assert 45 / 180 * 360 == 90
    assert 12 + 8 + 16 + 4 == 40 and 16 / 40 == 0.4
    assert 4 * 5 / 2 == 10
    assert (0 + (4 - 0) // 2) == 2
    # six-item binary search middles
    low, high = 0, 5
    mids = []
    target_index = 3
    while low <= high:
        mid = low + (high - low) // 2
        mids.append(mid)
        if mid == target_index:
            break
        if mid < target_index:
            low = mid + 1
        else:
            high = mid - 1
    assert mids == [2, 4, 3]


ARTICLES = {
    "articles/crt-sprint-profit-loss.md": """# Profit and loss on cost price

Profit and loss compare the selling price with the cost price. The cost price is the base.

## Learning objectives

- Compute profit or loss as selling price minus cost price.
- Turn that gap into a percentage of the cost price.
- Recognize that equal prices mean neither profit nor loss.

## Formula

Profit = selling price − cost price. If the result is negative, the loss is its absolute value.

Profit % = profit / cost price × 100.

Loss % = loss / cost price × 100.

## Worked example

Cost 800 and selling price 920.

Profit = 120. Percentage = 120/800 × 100 = 15%.

A 12% profit on the same cost would sell at 896, not 920. That is why 12% is a different question.

## Common mistakes

- Dividing the gap by the selling price.
- Treating the rupee profit as if it were already a percentage.
- Adding GST when the question never mentions tax.

## Recap

Subtract the prices, then divide by the cost. The three practice questions on this lesson use only that rule.
""",
    "articles/crt-sprint-time-work.md": """# Time and work rates

If one person finishes a job in D days, and the rate stays constant, one day of work is 1/D of the job.

## Learning objectives

- Write a daily rate as a fraction of the whole job.
- Multiply that rate by the number of days worked.
- Keep the answer as a fraction of the job when the question asks for work, not days.

## Formula

Work = days worked × (1 / days needed alone).

## Worked example

B finishes a job in 15 days. In 5 days the work done is 5 × 1/15 = 1/3.

Someone who finishes in 10 days does 1/10 of the job in a single day. 1/5 would describe a 5-day worker instead.

## Common mistakes

- Adding the day counts instead of adding rates.
- Reporting the number of days when the question asks for a fraction of work.
- Using a different worker's time in the denominator.

## Recap

Name the rate first. Then multiply by the time in the question.
""",
    "articles/crt-sprint-probability.md": """# Equally likely outcomes

Probability is the number of favorable outcomes divided by the number of equally likely outcomes.

## Learning objectives

- List the sample space before choosing a number.
- Count only the outcomes the question names.
- Refuse a probability greater than 1 for a single event that can fail.

## Formula

P(event) = favorable / total, when every outcome is equally likely.

## Worked example

A fair coin has the sample space {heads, tails}. P(heads) = 1/2.

1/3 would require three equally likely outcomes. 1 would mean tails cannot happen.

## Common mistakes

- Using the number of faces from a different object, such as a die.
- Treating “possible” as “certain”.

## Recap

Write the outcomes, count the match, and divide. This lesson's practice question is one coin toss.
""",
    "articles/crt-sprint-syllogisms.md": """# What a syllogism forces

A conclusion is forced only when it is true in every reading of the statements. Placement items in this lesson treat the named groups as non-empty.

## Learning objectives

- Separate a restated premise from a new conclusion.
- Keep “some” from turning into “all” or “none”.
- Mark a statement false when it contradicts a premise.

## Key principle

All A are B puts every A inside B. Some A are B guarantees at least one shared member. No A is B keeps the groups apart.

## Worked example

All engineers are graduates. Ravi is an engineer. Ravi is a graduate.

“Some graduates are not engineers” might be true and might be false. It is not forced. “No graduate is an engineer” contradicts the premise.

## Common mistakes

- Reversing “all A are B” into “all B are A”.
- Treating a possible overlap as a required overlap.
- Choosing a sentence just because it repeats a premise, when the question asks for something that is not forced.

## Recap

Draw the groups, keep the wording tight, and reject any option the statements do not require. The five practice questions on this lesson are the related practice.
""",
    "articles/crt-sprint-grammar.md": """# Error spotting in short sentences

An error-spotting item has one sentence that follows the rule and others that break it. Decide the rule before you compare the options.

## Learning objectives

- Match a singular unit with a singular verb when the sentence treats the group as one unit.
- Put a comma before “and” when it joins two independent clauses.
- Use the simple past for a finished action, and choose “a” or “an” from the sound.

## Key principle

Neither…nor: the verb agrees with the nearer subject. “Hour” starts with a vowel sound, so it takes “an”.

## Worked example

“She went to the interview yesterday.”

“Go” is not past. “Gone” needs an auxiliary. “Going” needs an auxiliary. “Went” is the simple past.

## Common mistakes

- Moving the comma to the inside of a phrase.
- Agreeing “neither…nor” with the first subject instead of the nearer one.
- Choosing “a” because h is a consonant letter, even when the h is silent.

## Recap

Name the broken rule in each wrong option. The five practice questions on this lesson are the related practice. The published verbal lesson is about meaning, not these grammar rules.
""",
    "articles/crt-sprint-vocabulary.md": """# Synonyms and antonyms in context

A synonym is a close meaning. An antonym is an opposite meaning. The sentence decides which sense of the word is in play.

## Learning objectives

- Match “brief” with short, not with a legal brief.
- Tell a near synonym from an antonym. Rare is not the opposite of scarce.
- Use the risk sense of “mitigate”: reduce the severity.

## Key principle

Replace the word in the sentence. If the sentence still says the same thing, the choice is a synonym.

## Worked example

“She gave a candid answer” still means the same thing as “She gave an honest answer.” Angry, confused, and delayed change the meaning.

## Common mistakes

- Picking the opposite when the question asks for a synonym.
- Picking a word from a nearby idea, such as size, when the word is about supply.

## Recap

Substitute, then check the direction: same meaning or opposite meaning. The five vocabulary questions on this lesson are the related practice.
""",
    "articles/crt-sprint-charts.md": """# Bar charts and pie shares

A bar chart compares values by length. A pie chart compares shares of one whole. Read the question before you add or subtract.

## Learning objectives

- Subtract two bars when the question says “how many more”.
- Pick the largest share by comparing the numbers.
- Turn a headcount into a pie angle with a full circle of 360°.
- Turn one bar into a percentage of the sum of the bars.

## Formula

Angle = group / total × 360.

Percent = part / total × 100.

## Worked example

45 employees out of 180.

45/180 = 1/4. 1/4 × 360° = 90°.

45° copies the headcount and forgets the circle. 180° would be half of the employees, which is 90 people.

## Common mistakes

- Adding bars when the question asks for a difference.
- Treating a defect count as if it were already a percentage.
- Assuming pie slices are equal when the labels show different shares.

## Recap

Write the operation the question names, then use every bar or slice that operation needs. The five chart questions on this lesson are the related practice. Table reading stays on the published table lesson.
""",
    "articles/dsa-sprint-strings.md": """# Scanning a string

A string is a sequence of characters with indexes. In this lesson the first character is index 0.

## Learning objectives

- Reverse by swapping the ends or by writing a new string from the end.
- Count vowels with one pass.
- Test a palindrome and an anagram from character counts or two pointers.

## Worked algorithm: reverse

Set left at the first character and right at the last. Swap, then move inward, until left meets or passes right.

Dry run of \"ab\": one swap produces \"ba\".

Time: O(n). Extra space: O(1) in an editable buffer, and O(n) if the language must allocate a new string.

Edge cases: the empty string stays empty. One character stays unchanged. Do not add a space.

## Worked algorithm: vowel count

Walk once. Add 1 when the character is a, e, i, o, or u. This lesson does not treat y as a vowel.

Dry run of \"team\": e and a, so the count is 2.

Time O(n). Space O(1). An empty string counts 0.

## Worked algorithm: anagram

Count the letters in the first word and decrement with the second. Both words are anagrams if every count returns to zero and the lengths match.

Dry run: listen and silent both contain one of each of e, i, l, n, s, t.

Time O(n) for a fixed alphabet. Space O(1) for that alphabet. Different lengths fail immediately.

## Related practice

The ten string questions on this lesson. In the DSA practice list, the coding problems are named reverse-string and count-vowels. Those names are the related coding practice. This article does not start a code runner.
""",
    "articles/dsa-sprint-searching.md": """# Linear and binary search

Linear search checks indexes in order. Binary search discards half of a sorted array after each comparison.

## Learning objectives

- Count the comparisons linear search makes before a hit.
- State the worst case when the target is missing: every cell is checked.
- Trace binary search with one mid formula on a sorted array.
- Refuse binary search on unsorted data.

## Worked algorithm: linear search

Start at the first cell. Compare. Stop on a match. If the loop ends, the target is absent.

Dry run of 9 in [4, 1, 9, 7]: compare 4, compare 1, compare 9, return the third cell's index.

Time: O(1) best case when the first cell matches, Θ(n) worst case when it is missing or last. Space O(1).

Edge case: an empty array is absent without a comparison.

## Worked algorithm: binary search

The array must be sorted. low starts at the first index. high starts at the last. mid = low + floor((high−low)/2).

If the middle equals the target, return it. If the target is greater, set low = mid + 1. If it is smaller, set high = mid − 1. Stop when low passes high.

Dry run of 6 in [2, 4, 6, 8, 10]: mid index 2 holds 6, so the search returns 2.

Dry run of 7 in [1, 3, 5, 7, 9, 11]: middle values 5, then 9, then 7. Return the index of 7.

Time O(log n). Iterative extra space O(1). A recursive form uses O(log n) stack space.

Edge cases: empty input is absent. An unsorted array can discard the half that holds the target, so the result is not reliable. The low + (high−low)//2 form avoids adding two huge indexes in fixed-width arithmetic.

## Related practice

The five searching questions on this lesson. In the DSA practice list, the coding problems are named linear-search and binary-search. The published complexity lesson explains why halving is logarithmic. It does not replace this trace.
""",
    "articles/dsa-sprint-complexity.md": """# Checking a big-O claim

Big-O names how the number of steps grows with n. Count the dominant steps, then drop constants and lower-order terms.

## Learning objectives

- Multiply nested loops that each run n times.
- Count halvings as logarithmic.
- Keep a fixed setup from changing a linear loop into another class.
- Separate a closed formula from a loop that computes the same value.

## Worked algorithm

```text
for i ← 1 to n:
  for j ← 1 to n:
    constant work
```

Dry run n = 3: the body runs 9 times. The growth is O(n²). Extra space is O(1) when the body only updates a counter.

A loop that replaces x with floor(x/2) until x is 0 is O(log n). Dry run x = 8: 8, 4, 2, 1, 0.

## Formula and loop

The sum 1 + 2 + … + n equals n(n+1)/2.

The formula does a fixed amount of arithmetic, so it is O(1). Adding the integers in a loop is O(n). Both give 10 when n = 4. The costs are different.

## Common mistakes

- Calling every nested loop linear.
- Treating O(n + 20) as a different class from O(n).
- Using the best case of a search as the worst-case class.

## Related practice

The five complexity questions on this lesson. Read the published lesson “Time complexity with big-O” (dsa-complexity) for the pair-counting trace. This article is the checklist for the sprint questions.
""",
}


def _materials() -> list[dict]:
    specs = [
        ("crt-sprint-profit-loss", "Profit and loss on cost price", "quantitative", 8, ["Compute profit from cost and selling price", "Use cost price as the percentage base"]),
        ("crt-sprint-time-work", "Time and work rates", "quantitative", 8, ["Write a one-day work rate", "Multiply the rate by days worked"]),
        ("crt-sprint-probability", "Equally likely outcomes", "quantitative", 6, ["List a sample space", "Divide favorable outcomes by total outcomes"]),
        ("crt-sprint-syllogisms", "What a syllogism forces", "logical-reasoning", 10, ["Separate forced conclusions from possible ones", "Keep some, all, and none distinct"]),
        ("crt-sprint-grammar", "Error spotting in short sentences", "verbal", 8, ["Check verb form, comma placement, and articles", "Agree neither-nor with the nearer subject"]),
        ("crt-sprint-vocabulary", "Synonyms and antonyms in context", "verbal", 8, ["Match a word to the sentence", "Separate synonyms from antonyms"]),
        ("crt-sprint-charts", "Bar charts and pie shares", "data-interpretation", 8, ["Choose difference, maximum, angle, or percentage", "Use 360 degrees for a full pie"]),
        ("dsa-sprint-strings", "Scanning a string", "strings", 12, ["Reverse and scan with explicit edge cases", "State time and extra memory"]),
        ("dsa-sprint-searching", "Linear and binary search", "searching", 12, ["Trace linear and binary search", "Require sorted order before binary search"]),
        ("dsa-sprint-complexity", "Checking a big-O claim", "complexity", 10, ["Multiply nested loops", "Drop constants and lower-order terms"]),
    ]
    materials = []
    for key, title, skill, minutes, objectives in specs:
        materials.append(
            {
                "key": key,
                "title": title,
                "kind": "article",
                "level": "beginner",
                "audience": "Fresher",
                "minutes": minutes,
                "families": ["business-analyst"],
                "skills": [skill, "crt" if skill in {"quantitative", "logical-reasoning", "verbal", "data-interpretation"} else "dsa"],
                "objectives": objectives,
                "prerequisites": [],
                "examples": ["See the worked example in the article."],
                "exercises": ["Answer the practice questions linked from this lesson after reading the article."],
                "summary": title + ". The practice questions on the lesson use this article.",
                "sources": [],
                "body_file": f"articles/{key}.md",
                "version": 1,
            }
        )
    return materials


def _syllabus(questions: list[dict]) -> list[dict]:
    def keys(prefix: str) -> list[str]:
        return [row["key"] for row in questions if row["key"].startswith(prefix)]

    def entry(key, track, title, unit, unit_title, unit_position, position, material, question_keys, prerequisites, minutes, version, status="published"):
        return {
            "key": key,
            "track": track,
            "track_title": "CRT / Aptitude" if track == "crt" else "DSA Foundations",
            "unit": unit,
            "unit_title": unit_title,
            "unit_position": unit_position,
            "title": title,
            "position": position,
            "status": status,
            "material_key": material,
            "question_keys": question_keys,
            "prerequisites": prerequisites,
            "minutes": minutes,
            "video": None,
            "version": version,
        }

    return [
        entry("syl-sprint-profit", "crt", "Profit and loss on cost price", "quantitative", "Quantitative Aptitude", 1, 3, "crt-sprint-profit-loss", keys("sprint1-pl-"), ["syl-crt-quant-percentages"], 8, 1),
        entry("syl-sprint-time-work", "crt", "Time and work rates", "quantitative", "Quantitative Aptitude", 1, 4, "crt-sprint-time-work", keys("sprint1-tw-"), ["syl-sprint-profit"], 8, 1),
        entry("syl-sprint-probability", "crt", "Equally likely outcomes", "quantitative", "Quantitative Aptitude", 1, 5, "crt-sprint-probability", keys("sprint1-pr-"), ["syl-sprint-time-work"], 6, 1),
        entry("syl-crt-logical-syllogisms", "crt", "Syllogisms", "logical", "Logical Reasoning", 2, 2, "crt-sprint-syllogisms", keys("sprint1-syl-"), ["syl-crt-logical-patterns"], 10, 2),
        entry("syl-crt-verbal-grammar", "crt", "Error spotting", "verbal", "Verbal Ability", 3, 2, "crt-sprint-grammar", keys("sprint1-gr-"), ["syl-crt-verbal-meaning"], 8, 2),
        entry("syl-sprint-vocabulary", "crt", "Synonyms and antonyms in context", "verbal", "Verbal Ability", 3, 3, "crt-sprint-vocabulary", keys("sprint1-voc-"), ["syl-crt-verbal-grammar"], 8, 1),
        entry("syl-crt-di-charts", "crt", "Bar charts and pie shares", "data-interpretation", "Data Interpretation", 4, 2, "crt-sprint-charts", keys("sprint1-ch-"), ["syl-crt-di-tables"], 8, 2),
        entry("syl-sprint-complexity", "dsa", "Checking a big-O claim", "complexity", "Complexity", 1, 2, "dsa-sprint-complexity", keys("sprint1-cx-"), ["syl-dsa-complexity"], 10, 1),
        entry("syl-sprint-strings", "dsa", "Scanning a string", "arrays-strings", "Arrays and Strings", 2, 2, "dsa-sprint-strings", keys("sprint1-str-"), ["syl-dsa-arrays-strings"], 12, 1),
        entry("syl-sprint-searching", "dsa", "Linear and binary search", "searching-sorting", "Searching and Sorting", 3, 2, "dsa-sprint-searching", keys("sprint1-sea-"), ["syl-dsa-arrays-strings"], 12, 1),
    ]


def _write(path: Path, payload: object) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def _write_text(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def main() -> None:
    _check_math()
    questions = _selected_questions() + _original_questions()
    if len(questions) != 70:
        raise SystemExit(len(questions))
    if len({row["key"] for row in questions}) != 70:
        raise SystemExit("duplicate keys")
    articles = ROOT / "articles"
    articles.mkdir(exist_ok=True)
    for name, body in ARTICLES.items():
        _write_text(ROOT / name, body)
    _write(ROOT / "questions.json", {"version": 1, "questions": questions})
    _write(ROOT / "materials.json", {"version": 1, "materials": _materials()})
    _write(ROOT / "syllabus.json", {"version": 1, "entries": _syllabus(questions)})
    _write(
        ROOT / "packs.json",
        {
            "version": 1,
            "packs": [
                {
                    "key": "sprint1-crt-dsa",
                    "title": "CRT and DSA sprint 1",
                    "kind": "practice",
                    "version": 1,
                    "families": ["business-analyst"],
                    "instructions": "Practice mode shows the explanation after you submit. A timed exam keeps the explanation hidden until the exam is complete. These items do not reveal the correct option before that.",
                    "question_keys": [row["key"] for row in questions],
                }
            ],
        },
    )
    files = [
        "materials.json",
        "questions.json",
        "syllabus.json",
        "packs.json",
        *sorted(ARTICLES),
    ]
    items = []
    for rel in files:
        digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        items.append({"path": rel, "sha256": digest})
    manifest = {
        "batch_id": "2026-10-10-crt-dsa-sprint-001",
        "title": "CRT and DSA content sprint 1",
        "items": items,
    }
    _write(ROOT / "manifest.json", manifest)
    print(f"wrote {len(questions)} questions")


if __name__ == "__main__":
    main()
