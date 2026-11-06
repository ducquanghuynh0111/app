"""Menu rows transcribed from the two CUKCUK screenshots supplied by the owner.

Confirmed saleable items are imported from the owner's lists and later clarifications.
Units from the original screenshots are kept where applicable.
"""

# CUKCUK code, display name, inventory group, displayed unit.
CODE_ALIASES = {
    "DIGI": "DG", "DAPH": "DAUPHONG", "CC": "COCA",
    "BIAHUDACHAI": "HUCH", "HL": "BH",
}


def canonical_code(code):
    normalized = str(code or "").strip().upper()
    return CODE_ALIASES.get(normalized, normalized)


READY = [
    ("CL", "CARLSBERG LON", "beer", "Chai"),
    ("BIAHENIKENCHAI", "BIA HENIKEN CHAI", "beer", "Chai"),
    ("HUCH", "HUDA CHAI", "beer", "Chai"),
    ("BL1", "BLANC LON 1664", "beer", "Chai"),
    ("CORONA", "Corona", "beer", "Chai"),
    ("BITICH", "BIA TIGER CHAI", "beer", "Chai"),
    ("TUBORG", "Tuborg", "beer", "Chai"),
    ("HI", "HUDA ICE", "beer", "Chai"),
    ("DG", "Điện giải", "soft_drink", "Chai"),
    ("TTC", "Trà Trái cây", "soft_drink", "Chai"),
    ("NB", "Nutri boost", "soft_drink", "Chai"),
    ("NS", "Nước suối", "water", "Chai"),
    ("NK", "Nước khoáng", "water", "Chai"),
    ("STINGG", "Sting vàng", "soft_drink", "Lon"),
    ("BT", "BIA TIGER", "beer", "Lon"),
    ("COCA", "Coca", "soft_drink", "Lon"),
    ("B3", "BIA 333", "beer", "Lon"),
    ("TILU", "Tiger lùn", "beer", "Lon"),
    ("BIHELU", "BIA HENIKEN LÙN", "beer", "Lon"),
    ("BOHU", "Bò húc", "soft_drink", "Lon"),
    ("TICA", "tiger cao", "beer", "Lon"),
    ("BU", "Bia Ultra", "beer", "Lon"),
    ("BH", "BIA HUDA", "beer", "Lon"),
    ("PEPSI", "Pepsi", "soft_drink", "Lon"),
    ("BL", "BIA LARUE", "beer", "Lon"),
    ("BIHE", "BIA HENIKEN LON", "beer", "Lon"),
    ("BULO", "Budweiser Lon", "beer", "Lon"),
    ("SD", "Sting dâu", "soft_drink", "Lon"),
    ("7 UP", "7up", "soft_drink", "Lon"),
    ("FANTA", "Fanta", "soft_drink", "Lon"),
]

READY += [
    ("RTM", "rượu táo mèo", "liquor", "Chai"),
    ("RCH", "rượu chuối hột", "liquor", "Chai"),
    ("RBK", "rượu ba kích", "liquor", "Chai"),
    ("RMN", "rượu mơ nhật", "liquor", "Chai"),
    ("RMR", "rượu mơ rừng", "liquor", "Chai"),
    ("BATR", "Bánh tráng", "rice_paper", "Gói"),
    ("DAUPHONG", "Đậu phộng", "peanuts", "Gói"),
    ("TNn", "Thuốc con ngựa", "tobacco", "Gói"),
    ("TM", "Thuốc con mèo", "tobacco", "Gói"),
]
# The owner confirmed these are kitchen dishes; the source image lists "Chai" in error.
PENDING_FOOD = [
    ("CLNLCD", "cá lăng nấu lẩu chanh dây", "Chai"),
    ("DHNTB", "diềm heo nướng tây bắc", "Chai"),
    ("BORAMUKICH", "bò rang muối kim châm", "Chai"),
]
