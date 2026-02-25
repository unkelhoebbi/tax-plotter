import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_chf(x) -> float:
    if x is None:
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return np.nan
    s = s.replace("’", "").replace("'", "").replace(" ", "")
    s = s.replace(",", ".")
    return float(s)

federal_single = [
    ("0", "0.00", "0"),
    ("15’200", "0.77", "0"),
    ("33’200", "0.88", "139"),
    ("43’500", "2.64", "229"),
    ("58’000", "2.97", "612"),
    ("76’100", "5.94", "1’150"),
    ("82’000", "6.60", "1’500"),
    ("108’800", "8.80", "3’269"),
    ("141’500", "11.00", "6’146"),
    ("184’900", "13.20", "10’920"),
    ("793’300", "13.20", "91’229"),
    ("793’400", "11.50", "91’241")]
federal_married = [
    ("0", "0.00", "0"),
    ("29’700", "1.00", "0"),
    ("53’400", "2.00", "237"),
    ("61’300", "3.00", "395"),
    ("79’100", "4.00", "929"),
    ("94’900", "5.00", "1’561"),
    ("108’600", "6.00", "2’246"),
    ("120’500", "7.00", "2’960"),
    ("130’500", "8.00", "3’660"),
    ("138’300", "9.00", "4’284"),
    ("144’200", "10.00", "4’815"),
    ("148’200", "11.00", "5’215"),
    ("150’300", "12.00", "5’446"),
    ("152’300", "13.00", "5’686"),
    ("940’800", "13.00", "108’191"),
    ("940’900", "11.50", "108’204"),
]

cantonal_single = [
    ("6’900", "0.00"),
    ("4’900", "2.00"),
    ("4’800", "3.00"),
    ("7’900", "4.00"),
    ("9’600", "5.00"),
    ("11’000", "6.00"),
    ("12’900", "7.00"),
    ("17’400", "8.00"),
    ("33’600", "9.00"),
    ("33’200", "10.00"),
    ("52’700", "11.00"),
    ("68’400", "12.00"),
    ("99’999’999", "13.00")]
cantonal_married = [
    ("13’900", "0.00"),
    ("6’300", "2.00"),
    ("8’000", "3.00"),
    ("9’700", "4.00"),
    ("11’100", "5.00"),
    ("14’300", "6.00"),
    ("31’800", "7.00"),
    ("31’900", "8.00"),
    ("47’900", "9.00"),
    ("57’200", "10.00"),
    ("62’100", "11.00"),
    ("71’600", "12.00"),
    ("99’999’999", "13.00"),
]

def federal_tax(income: float, tax_category: list) -> float:
    t = pd.DataFrame(tax_category, columns=["For the next CHF", "Additional %", "Base amount CHF"])
    t["For the next CHF"] = t["For the next CHF"].apply(parse_chf)
    t["Additional %"] = t["Additional %"].apply(parse_chf)
    t["Base amount CHF"] = t["Base amount CHF"].apply(parse_chf)
    t = t.sort_values("For the next CHF")
    if income <= 0:
        return 0.0
    larger_row = t[t["For the next CHF"] > income]
    if larger_row.empty:
        row = t.iloc[-1]
    else:
        idx = larger_row.index[0]
        row = t.loc[idx - 1] if idx > 0 else t.iloc[0]
    threshold = float(row["For the next CHF"])
    rate = float(row["Additional %"]) / 100.0
    base = float(row.get("Base amount CHF", 0))
    return max(0.0, (income - threshold) * rate + base)

def cantonal_tax(income: float, tax_category: list) -> float:
    if income <= 0:
        return 0.0
    total_tax = 0.0
    remaining_income = income
    for amount_str, rate_str in tax_category:
        bracket_amount = parse_chf(amount_str)
        rate = parse_chf(rate_str) / 100.0
        if remaining_income <= 0:
            break
        taxable_in_bracket = min(remaining_income, bracket_amount)
        total_tax += taxable_in_bracket * rate
        remaining_income -= taxable_in_bracket
    return total_tax * 0.98

def calculate_percentage(tax_amount: float, income: float) -> float:
    if income == 0:
        return 0.0
    return (tax_amount / income) * 100

def municipal_tax(cantonal_tax_amount: float) -> float:
    return cantonal_tax_amount * 1.19

income_list = np.arange(0, 300000, 100)

percentage_federal = [
    calculate_percentage(federal_tax(income, federal_single), income)
    for income in income_list
]

percentage_cantonal = [
    calculate_percentage(cantonal_tax(income, cantonal_single), income)
    for income in income_list
]

percentage_municipal = [
    calculate_percentage(municipal_tax(cantonal_tax(income, cantonal_single)), income)
    for income in income_list
]

percentage_total = [
    federal + cantonal + municipal
    for federal, cantonal, municipal in zip(percentage_federal, percentage_cantonal, percentage_municipal)
]

fig, ax = plt.subplots(figsize=(12, 8))

# Plot the percentage lines
ax.plot(income_list, percentage_federal, label="Bund - Alleinstehend ohne Kinder")
ax.plot(income_list, percentage_cantonal, label="Kanton - Alleinstehend ohne Kinder")
ax.plot(income_list, percentage_municipal, label="Gemeinde - Alleinstehend ohne Kinder")
ax.plot(income_list, percentage_total, label="Total - Alleinstehend ohne Kinder", linestyle="--")

# Configure the primary y-axis
ax.set_ylabel("Steuertarif (%)")
ax.set_xlabel("Steuerbares Einkommen (CHF)")
ax.set_xticks(np.arange(0, 300001, 10000))
ax.set_xticklabels([f"{x:,.0f}".replace(",", "'") + " CHF" for x in range(0, 300001, 10000)], rotation=45)
ax.legend(loc="upper left")
ax.grid(True)

# Set the title and layout
plt.title("Steuertarif und Steuerbetrag: Bundessteuer, Kantonssteuer (Zürich), Gemeindesteuer & Total")
plt.tight_layout()

output_path = "plot.png"
plt.savefig(output_path)

if os.environ.get("CI", "").lower() != "true":
    plt.show()