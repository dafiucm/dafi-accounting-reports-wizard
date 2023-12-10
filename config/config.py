import locale
import logging

from src.logging.CustomFormatter import CustomFormatter
from src.valueobjects.BudgetPosition import BudgetPosition
from src.valueobjects.TransactionDocumentType import TransactionDocumentType

locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")

# Logging
logger = logging.getLogger("Wizard")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)

# Files
g_tmp_path = ".tmp/"

# E.g.: "Orden: E0390122A400 DELEGACION ALUMNOS"
g_request_regex = r"Orden: (?P<request_id>\w+) (?P<request_name>.+)"

# E.g.: "2    de    6"
g_number_of_pages_regex = r"\d\s+de\s+(?P<number_of_pages>\d+)"

# E.g.: "A DIA: 07 de Diciembre 2023"
g_date_regex = r"A DIA: (?P<day>\d{2}) de (?P<month>\w+) (?P<year>\d{4})"

g_months = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12
}

# E.g.: "11.384.852,92"
g_amount_regex = r"\d{1,3}(?:\.\d{3})*,\d{2}"

# E.g.: "Importe total de la orden E0390122A400:            11.384.852,92"
g_total_report_amount_regex = r"Importe total de la orden (?P<request_id>\w+):\s+(?P<total_report_amount>" + g_amount_regex + ")"

g_ignored_strings = [
    "UNIVERSIDAD COMPLUTENSE DE MADRID",
    "INFORME DE GASTOS ACUMULADO",
    g_request_regex,
    g_number_of_pages_regex,
    g_date_regex,
    g_total_report_amount_regex,
    "Tipo\ doc\.\ Nº\.Documento\ /\ Pos\ \+/\-\ Fecha\ doc\.\ Pos\.Pre\.\ Descripción\ Importe",
    "Referencia\ NIF\ acreedor\ Nombre",
    r"_{5,}\s*_{5,}",  # E.g.: "_______________________ _______________________"
    "\(\*\):\ No\ interviene\ en\ el\ calculo\ del\ importe\ total"
]

# E.g.: "G/2050000/2000"
g_budget_position_code_regex = r"G\/\d{7}\/2000"

# E.g.: "Posición Presupuestaria: G/2050000/2000 Mobiliario y Enseres"
g_budget_position_header_regex = r"Posición Presupuestaria: (?P<code>" + g_budget_position_code_regex + ") (?P<name>.+)"

# E.g.: "Importe total de la partida G/2050000/2000:               855,71"
g_budget_position_total_amount_regex = r"Importe total de la partida (?P<position_code>" + g_budget_position_code_regex + "):\s+(?P<total_amount>" + g_amount_regex + ")"

# First line of a transaction
# Has these fields:
# - Transaction document type (OY, RY, FM, RJ, KJ)
# - Transaction document number (4000240529, 1001523601, 4000253812, 2320053719, 2320060419)
# - Transaction document position (001, 002, 009), optional
# - Transaction document date (18.04.2023, 09.11.2023, 05.12.2023, 20.11.2023, 05.12.2023)
# - Transaction budget position (G/2050000/2000, G/2200300/2000, G/2261100/2000, G/2230100/2000, G/2261100/2000)
# - An optional description ("Tren Pedro Martínez Ritsi Valencia 8-12 noviembre", "Dietas Ritsi Valencia")
# - An amount ("855,71", "0,91", "99,01", "118,15", "45,50")
# - An optional asterisk ("*")
# E.g.: "OY 4000240529   / 001 18.04.2023 G/2050000/2000               855,71"
# E.g.: "RY 1001523601   / 002 09.11.2023 G/2200300/2000                 0,91"
# E.g.: "FM 4000253812   / 009 05.12.2023 G/2200300/2000                99,01"
# E.g.: "KJ 2320053719   / 20.11.2023 G/2230100/2000 Tren Pedro Martínez Ritsi Valencia 8-12 noviembre               118,15 *"
# E.g.: "KJ 2320060419   / 05.12.2023 G/2261100/2000 Dietas Ritsi Valencia                45,50 *"
g_transaction_first_line_regex = r"(?P<document_type>\w{2}) (?P<document_number>\d+)\s+/( (?P<document_position>\d{3}))? (?P<document_date>\d{2}\.\d{2}\.\d{4}) (?P<budget_position_code>" + g_budget_position_code_regex + ")( (?P<description>.+?))?\s+(?P<amount>" + g_amount_regex + ")\s*(?P<asterisk>\*)?"

# Second line of a transaction
# Has these fields:
# - Reference (20230401, 0839264, ABR016023, NOV015723, SN 07.02.2023, 00554/23, 0863A00880/23, AUCM_2023-031, S/N A. CUENCA)
# - An optional vendor id (B82560947, B78949799, B01767086, CF0012200, G83299487, 12345678A)
# - A vendor name (OFIPAPEL CENTER. S.L., FRAMENET 3, S.L., "GARCIA SANZ, JOSE LUIS -F. VENECIA", FTAD. DE INFORMÁTICA, AVORIS RETAIL DIVISION SL, ASOCIACION RITSI E. T. S. I.I., "DIGITAL LA PAZ, S.L.U.", "FERNÁNDEZ MARTÍNEZ, MARÍA")
# E.g.: "20230401 B82352691 CONSTAN"
# E.g.: "0842773 B82560947 OFIPAPEL CENTER. S.L."
# E.g.: "SN 07.02.2023 00827691J GARCIA SANZ, JOSE LUIS -F. VENECIA"
# E.g.: "CF0012200 FTAD. DE INFORMÁTICA"
# E.g.: "EMIT-106 B88047196 FLUGE AUDIOVISUAL, S.L."
g_reference_common_regex = r"[\w\/_\-]+"
g_reference_sn_date_regex = r"SN \d{2}\.\d{2}\.\d{4}"
g_reference_ssn_name_regex = r"S\/N \w\. \w+"
g_reference_regex = "|".join([g_reference_common_regex, g_reference_sn_date_regex, g_reference_ssn_name_regex])
g_transaction_second_line_regex = r"^((?P<reference>" + g_reference_regex + ")\s)?(?P<vendor_id>\w+)\s(?P<vendor_name>.+)$"

g_budget_positions = {
    "G/2050000/2000": BudgetPosition("G/2050000/2000", "Mobiliario y Enseres", 2),
    "G/2200000/2000": BudgetPosition("G/2200000/2000", "Fungible de Oficina", 2),
    "G/2200300/2000": BudgetPosition("G/2200300/2000", "Fungibles de Informática", 2),
    "G/2210700/2000": BudgetPosition("G/2210700/2000", "Fungibles de Laboratorio", 2),
    "G/2219900/2000": BudgetPosition("G/2219900/2000", "Otros Suministros", 2),
    "G/2230100/2000": BudgetPosition("G/2230100/2000", "Otros Transportes", 2),
    "G/2260200/2000": BudgetPosition("G/2260200/2000", "Publicidad y Propaganda", 2),
    "G/2260500/2000": BudgetPosition("G/2260500/2000", "Cuotas de Inscripciones", 2),
    "G/2261100/2000": BudgetPosition("G/2261100/2000", "Ayudas de Viajes", 2),
    "G/2270800/2000": BudgetPosition("G/2270800/2000", "Trabajos de Imprenta", 2),
    "G/2279900/2000": BudgetPosition("G/2279900/2000", "Otros Trabajos", 2),
    "G/6200127/2000": BudgetPosition("G/6200127/2000", "Utillaje", 6),
    "G/6200129/2000": BudgetPosition("G/6200129/2000", "Equipos Informáticos", 6),
}

d_transaction_document_types = {
    "OY": TransactionDocumentType("OY"),
    "RY": TransactionDocumentType("RY"),
    "FM": TransactionDocumentType("FM"),
    "RJ": TransactionDocumentType("RJ"),
    "KJ": TransactionDocumentType("KJ"),
}
