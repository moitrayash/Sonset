"""Location set for the daily G20 almanac.

The original five cities (solar.CITIES) plus the G20 seats plus operator
additions, 30 locations total. G20 membership read as 19 national capitals +
Brussels (EU seat) + Addis Ababa (AU seat, member since 2023), MINUS Paris and
Brussels: operator instruction, 23 Jul, Berlin stands for CET representation,
so France's capital and the EU seat are deliberately absent. PLUS seven
operator additions (23 Jul): Bangkok, Los Angeles, San Francisco, Marrakesh,
Kigali, Accra, Gaza. Two of those carry unusual clocks, verified against
tzdata: Morocco is permanent UTC+1 except a Ramadan reversion to UTC+0
(15 Feb - 22 Mar 2026), and Palestine observes DST (28 Mar - 24 Oct 2026).
Gaza's code GZA is Yasser Arafat Intl, closed since 2004; the code remains
assigned and the convention here is codes-as-shorthand anyway. New Delhi is
already covered by DEL; the existing city-centre coordinate (28.6139 N,
77.2090 E) is the published New Delhi coordinate.

Codes are the IATA code of each city's PRIMARY AIRPORT (operator instruction,
22 Jul). Recode from the earlier metro codes: NYC->JFK, ANK->ESB, BJS->PEK,
BUE->EZE, JKT->CGK, LON->LHR, MOW->SVO, PAR->CDG, ROM->FCO, SEL->ICN,
TYO->HND, WAS->IAD; the other 13 were already airport codes. Contested picks,
resolved as flagship international gateway: HND over NRT, ICN over GMP, SVO
over DME, PEK over PKX (PEK remains Beijing's primary international airport),
IAD over DCA, EZE over AEP. Pretoria keeps PRY (Wonderboom, the city's own
airport); its heavy traffic goes through JNB, which is Johannesburg's.

READ THIS TWICE: coordinates are CITY CENTRES, not aerodrome reference points,
exactly as README section 1 warns. JFK the label sits on Manhattan-ish
coordinates, not on the field at Jamaica Bay. The codes are shorthand.

`us` marks locations subject to the Sunshine Protection Act scenario (US
federal law). Ottawa is deliberately not flagged: Canadian clocks are
provincial law. Ontario's Time Amendment Act 2020 would move Ontario to
permanent DST only if Quebec and New York State both do, so the knock-on is
plausible but not law; it is excluded rather than guessed at.

`std` is the standard-time UTC offset in hours, DST ignored.
"""

from solar import CITIES as ORIGINAL_FIVE

# solar.py keys -> primary-airport IATA (solar.py itself stays untouched; its
# artifacts keep the historical metro codes)
RECODE = {"NYC": "JFK", "DEL": "DEL", "CCU": "CCU", "BOM": "BOM", "SEA": "SEA"}

_AIRPORT_FIVE = {
    "JFK": "John F. Kennedy Intl",
    "DEL": "Indira Gandhi Intl",
    "CCU": "Netaji Subhas Chandra Bose Intl",
    "BOM": "Chhatrapati Shivaji Maharaj Intl",
    "SEA": "Seattle-Tacoma Intl",
}

LOCATIONS = {}

# ---- the five analysed so far (order preserved) --------------------------
for _old, _c in ORIGINAL_FIVE.items():
    _new = RECODE[_old]
    LOCATIONS[_new] = dict(
        _c, us=(_old in ("NYC", "SEA")), group="analysed so far",
        airport=_AIRPORT_FIVE[_new],
        role={"NYC": "existing set", "SEA": "existing set",
              "DEL": "existing set; covers G20 New Delhi",
              "CCU": "existing set", "BOM": "existing set"}[_old])

# ---- G20 seats, alphabetical by code ------------------------------------
_G20 = [
    ("ADD", "Addis Ababa",   9.0192,   38.7525, "Africa/Addis_Ababa",            3.0, False, "African Union seat",              "Addis Ababa Bole Intl"),
    ("BER", "Berlin",       52.5200,   13.4050, "Europe/Berlin",                 1.0, False, "Germany",                          "Berlin Brandenburg"),
    ("BSB", "Brasilia",    -15.7939,  -47.8828, "America/Sao_Paulo",            -3.0, False, "Brazil",                           "Pres. Juscelino Kubitschek Intl"),
    ("CBR", "Canberra",    -35.2809,  149.1300, "Australia/Sydney",             10.0, False, "Australia",                        "Canberra Airport"),
    ("CGK", "Jakarta",      -6.2088,  106.8456, "Asia/Jakarta",                  7.0, False, "Indonesia",                        "Soekarno-Hatta Intl"),
    ("ESB", "Ankara",       39.9334,   32.8597, "Europe/Istanbul",               3.0, False, "Turkiye",                          "Esenboga Intl"),
    ("EZE", "Buenos Aires",-34.6037,  -58.3816, "America/Argentina/Buenos_Aires",-3.0, False, "Argentina",                       "Ministro Pistarini Intl (Ezeiza)"),
    ("FCO", "Rome",         41.9028,   12.4964, "Europe/Rome",                   1.0, False, "Italy",                            "Fiumicino, Leonardo da Vinci"),
    ("HND", "Tokyo",        35.6762,  139.6503, "Asia/Tokyo",                    9.0, False, "Japan",                            "Haneda"),
    ("ICN", "Seoul",        37.5665,  126.9780, "Asia/Seoul",                    9.0, False, "South Korea",                      "Incheon Intl"),
    ("LHR", "London",       51.5074,   -0.1278, "Europe/London",                 0.0, False, "United Kingdom",                   "Heathrow"),
    ("MEX", "Mexico City",  19.4326,  -99.1332, "America/Mexico_City",          -6.0, False, "Mexico",                           "Benito Juarez Intl"),
    ("PEK", "Beijing",      39.9042,  116.4074, "Asia/Shanghai",                 8.0, False, "China",                            "Beijing Capital Intl"),
    ("PRY", "Pretoria",    -25.7479,   28.2293, "Africa/Johannesburg",           2.0, False, "South Africa (executive capital)", "Wonderboom"),
    ("RUH", "Riyadh",       24.7136,   46.6753, "Asia/Riyadh",                   3.0, False, "Saudi Arabia",                     "King Khalid Intl"),
    ("SVO", "Moscow",       55.7558,   37.6173, "Europe/Moscow",                 3.0, False, "Russia",                           "Sheremetyevo Intl"),
    ("YUL", "Montreal",     45.5019,  -73.5674, "America/Toronto",              -5.0, False, "Canada (operator: replaces Ottawa)", "Montreal-Trudeau Intl"),
]

for _code, _name, _lat, _lon, _tz, _std, _us, _role, _ap in _G20:
    LOCATIONS[_code] = dict(name=_name, lat=_lat, lon=_lon, tz=_tz, std=_std,
                            us=_us, group="G20 seat", role=_role, airport=_ap)

# ---- operator additions, 23 Jul, alphabetical by code --------------------
_ADDED = [
    ("ACC", "Accra",         5.6037,   -0.1870, "Africa/Accra",       0.0, False, "operator addition",  "Kotoka Intl"),
    ("AUS", "Austin",       30.2672,  -97.7431, "America/Chicago",   -6.0, True,  "operator addition (US; replaces Washington with MIA)", "Austin-Bergstrom Intl"),
    ("BKK", "Bangkok",      13.7563,  100.5018, "Asia/Bangkok",       7.0, False, "operator addition",  "Suvarnabhumi"),
    ("GZA", "Gaza",         31.5017,   34.4668, "Asia/Gaza",          2.0, False, "operator addition",  "Yasser Arafat Intl (closed since 2004)"),
    ("KGL", "Kigali",       -1.9441,   30.0619, "Africa/Kigali",      2.0, False, "operator addition",  "Kigali Intl"),
    ("LAX", "Los Angeles",  34.0522, -118.2437, "America/Los_Angeles",-8.0, True, "operator addition",  "Los Angeles Intl"),
    ("MIA", "Miami",        25.7617,  -80.1918, "America/New_York",  -5.0, True,  "operator addition (US; replaces Washington with AUS)", "Miami Intl"),
    ("MNL", "Manila",       14.5995,  120.9842, "Asia/Manila",        8.0, False, "operator addition",  "Ninoy Aquino Intl"),
    ("NQZ", "Astana",       51.1694,   71.4491, "Asia/Almaty",        5.0, False, "operator addition; Kazakhstan unified on UTC+5 in Mar 2024", "Nursultan Nazarbayev Intl"),
    ("PER", "Perth",       -31.9523,  115.8613, "Australia/Perth",    8.0, False, "operator addition",  "Perth Airport"),
    ("RAK", "Marrakesh",    31.6295,   -7.9811, "Africa/Casablanca",  1.0, False, "operator addition",  "Marrakesh Menara"),
    ("SFO", "San Francisco",37.7749, -122.4194, "America/Los_Angeles",-8.0, True, "operator addition",  "San Francisco Intl"),
    ("SZX", "Shenzhen",     22.5431,  114.0579, "Asia/Shanghai",      8.0, False, "operator addition",  "Bao'an Intl"),
    ("TAS", "Tashkent",     41.2995,   69.2401, "Asia/Tashkent",      5.0, False, "operator addition",  "Islam Karimov Tashkent Intl"),
    ("URC", "Urumqi",       43.8256,   87.6168, "Asia/Shanghai",      8.0, False, "operator addition (Xinjiang); official Beijing time, unofficial Xinjiang Time runs UTC+6", "Urumqi Diwopu Intl"),
    ("VVO", "Vladivostok",  43.1332,  131.9113, "Asia/Vladivostok",  10.0, False, "operator addition",  "Vladivostok Intl"),
]

for _code, _name, _lat, _lon, _tz, _std, _us, _role, _ap in _ADDED:
    LOCATIONS[_code] = dict(name=_name, lat=_lat, lon=_lon, tz=_tz, std=_std,
                            us=_us, group="operator addition", role=_role,
                            airport=_ap)

ORDER = ([RECODE[c] for c in ORIGINAL_FIVE] + [c for c, *_ in _G20]
         + [c for c, *_ in _ADDED])

if __name__ == "__main__":
    for code in ORDER:
        c = LOCATIONS[code]
        print(f"{code}  {c['name']:<13} {c['lat']:>9.4f} {c['lon']:>10.4f}  "
              f"{c['tz']:<32} std {c['std']:+.1f}  "
              f"{'US-scenario ' if c['us'] else ''}{c['role']}  [{c['airport']}]")
