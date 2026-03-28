"""Indian number-to-words (Crore/Lakh system)"""


def number_to_words(num: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def below_hundred(n: int) -> str:
        if n == 0: return ""
        if n < 10: return ones[n]
        if n < 20: return teens[n - 10]
        return tens[n // 10] + ("" if n % 10 == 0 else " " + ones[n % 10])

    def below_thousand(n: int) -> str:
        if n == 0: return ""
        if n < 100: return below_hundred(n)
        return ones[n // 100] + " Hundred" + (" " + below_hundred(n % 100) if n % 100 else "")

    if num == 0: return "Zero"
    if num < 0: return "Minus " + number_to_words(-num)

    parts = []
    if num >= 10_000_000:
        parts.append(below_thousand(num // 10_000_000) + " Crore")
        num %= 10_000_000
    if num >= 100_000:
        parts.append(below_thousand(num // 100_000) + " Lakh")
        num %= 100_000
    if num >= 1_000:
        parts.append(below_thousand(num // 1_000) + " Thousand")
        num %= 1_000
    if num > 0:
        parts.append(below_thousand(num))

    return " ".join(parts) + " Only"
