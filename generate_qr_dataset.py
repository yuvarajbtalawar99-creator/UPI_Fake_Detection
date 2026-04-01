# -*- coding: utf-8 -*-
"""
KAVACH – QR Code Dataset Generator
Generates safe and fake QR code images for testing the fraud detection system.

Usage:
    pip install qrcode[pil]
    python generate_qr_dataset.py
"""

import os
import random
import sys

try:
    import qrcode
except ImportError:
    print("ERROR: Install qrcode library first: pip install qrcode[pil]")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------
SAFE_DIR = os.path.join("datasets", "qr", "safe")
FAKE_DIR = os.path.join("datasets", "qr", "fake")

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------
TRUSTED_HANDLES = [
    "@okicici", "@oksbi", "@okaxis", "@okhdfcbank",
    "@paytm", "@ybl", "@ibl", "@upi", "@phonepe", "@gpay",
    "@sbi", "@hdfcbank", "@kotak", "@pnb",
]

MERCHANT_NAMES = [
    "RamKirana", "ShivamMedicals", "PatelGrocery", "JaiHindRestaurant",
    "SunilTextiles", "AgarwalSweets", "NehaBeautyParlour", "VijayElectronics",
    "GuruNanakDhaba", "DurgaProvisions", "SaiPetrolPump", "LaxmiSupermarket",
    "GaneshBakers", "MaaBharati", "RadhaKrishnaStores", "BharatGas",
    "KisanFertilizers", "AnnapurnaHotel", "RajeshPharmacy", "DeepakHardware",
    "SureshMobiles", "PoojaCollections", "ArunStationery", "MaheshFruits",
    "SandeepTailors", "RaviOpticals", "PriyaDairy", "DineshPaint",
    "KumarTyres", "SharmaClinics", "HariomJewellers", "BalajiBhavan",
    "ChandraBookStore", "VinodFlowers", "AmitSports", "LataMusicCenter",
    "RajaBarberShop", "SantoshIceCream", "IndiraHandlooms", "NehruChemist",
]

SAFE_USERNAMES = [
    "shop", "merchant", "store", "biz", "retail", "pay",
    "sales", "vendor", "mart", "outlet", "kirana", "dukan",
]

SUSPICIOUS_HANDLES = [
    "@okbizaxis", "@okbiz", "@bizaxis", "@fastpay", "@quickupi",
    "@securepay", "@instantpay", "@safepay", "@xyzbank", "@freecharge99",
    "@moneymaker", "@easywin", "@lottopay",
]

SUSPICIOUS_NAMES = [
    "LotteryPrize", "FreeCashReward", "LuckyWinner2024", "ClaimYourPrize",
    "EasyMoneyOffers", "BettingKing", "CasinoOnline", "HackAndEarn",
    "QuickLoanApproval", "FreeOfferZone", "KYCUpdateNow", "RefundCenter",
    "BonusCashback", "IncomeDouble", "MoneyTreePlan",
]


def _build_upi_uri(pa, pn="", am="", tn="", mc=""):
    """Construct a UPI URI string."""
    parts = [f"upi://pay?pa={pa}"]
    if pn:
        parts.append(f"pn={pn}")
    if am:
        parts.append(f"am={am}")
    if tn:
        parts.append(f"tn={tn}")
    if mc:
        parts.append(f"mc={mc}")
    parts.append("cu=INR")
    return "&".join(parts)


def _save_qr(data: str, folder: str, filename: str):
    """Generate and save a QR code image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(folder, filename))


def generate_safe_samples(count=40):
    """Generate safe QR codes with valid UPI URIs."""
    os.makedirs(SAFE_DIR, exist_ok=True)
    generated = 0
    for i in range(count):
        handle = random.choice(TRUSTED_HANDLES)
        username = random.choice(SAFE_USERNAMES) + str(random.randint(1, 999))
        pa = f"{username}{handle}"
        pn = random.choice(MERCHANT_NAMES)
        am = str(random.choice([50, 100, 150, 200, 250, 300, 500, 750, 999, 1200, 1500, 2000]))
        tn = random.choice(["Payment", "Purchase", "Order", "Bill", ""])
        mc = random.choice(["5411", "5812", "5541", "5699", ""])  # real MCC codes

        uri = _build_upi_uri(pa, pn, am, tn, mc)
        _save_qr(uri, SAFE_DIR, f"safe_{i+1:03d}.png")
        generated += 1

    print(f"✓ Generated {generated} safe QR samples in {SAFE_DIR}/")


def generate_fake_samples(count=40):
    """Generate fake/suspicious QR codes with various fraud indicators."""
    os.makedirs(FAKE_DIR, exist_ok=True)
    generated = 0

    strategies = [
        "missing_at",          # Invalid UPI format
        "unknown_processor",   # Unknown bank handle
        "suspicious_handle",   # Known scam handle
        "missing_payee",       # No payee name
        "malformed_uri",       # Not a UPI URI
        "phishing_url",        # Web URL instead of UPI
        "high_amount",         # Unusually high amount
        "suspicious_name",     # Suspicious payee name
        "domain_handle",       # Domain-like handle
        "suspicious_prefix",   # test/fake/fraud prefix
    ]

    for i in range(count):
        strategy = strategies[i % len(strategies)]

        if strategy == "missing_at":
            pa = f"frauduser{random.randint(100,999)}icici"
            uri = _build_upi_uri(pa, "Some Shop", str(random.randint(100, 5000)))

        elif strategy == "unknown_processor":
            pa = f"user{random.randint(100,999)}@randombank{random.randint(1,50)}"
            uri = _build_upi_uri(pa, "Unknown Store", str(random.randint(100, 2000)))

        elif strategy == "suspicious_handle":
            handle = random.choice(SUSPICIOUS_HANDLES)
            pa = f"merchant{random.randint(100,999)}{handle}"
            uri = _build_upi_uri(pa, "Quick Pay Store", str(random.randint(100, 5000)))

        elif strategy == "missing_payee":
            handle = random.choice(TRUSTED_HANDLES)
            pa = f"unknown{random.randint(100,999)}{handle}"
            uri = _build_upi_uri(pa, "", str(random.randint(500, 3000)))

        elif strategy == "malformed_uri":
            uri = random.choice([
                f"upi:pay?pa=broken",
                f"upi//pay?={random.randint(1,999)}",
                f"not-a-upi-string-{random.randint(1000,9999)}",
                f"upi://pay?invalid_format",
                f"random_text_{random.randint(1,999)}",
            ])

        elif strategy == "phishing_url":
            uri = random.choice([
                f"https://fake-paytm-login.com/verify?id={random.randint(1000,9999)}",
                f"http://gpay-refund.xyz/claim/{random.randint(100,999)}",
                f"https://free-recharge-offer.in/win",
                f"http://upi-kyc-update.com/bank/{random.randint(1,99)}",
                f"https://lottery-winner-{random.randint(1,99)}.com/prize",
            ])

        elif strategy == "high_amount":
            handle = random.choice(TRUSTED_HANDLES)
            pa = f"seller{random.randint(100,999)}{handle}"
            am = str(random.choice([150000, 200000, 500000, 999999]))
            uri = _build_upi_uri(pa, "Large Payment", am)

        elif strategy == "suspicious_name":
            handle = random.choice(TRUSTED_HANDLES)
            pa = f"seller{random.randint(100,999)}{handle}"
            pn = random.choice(SUSPICIOUS_NAMES)
            uri = _build_upi_uri(pa, pn, str(random.randint(100, 5000)))

        elif strategy == "domain_handle":
            pa = f"user{random.randint(100,999)}@paypal.com"
            uri = _build_upi_uri(pa, "PayPal Refund", str(random.randint(500, 5000)))

        elif strategy == "suspicious_prefix":
            handle = random.choice(TRUSTED_HANDLES)
            prefix = random.choice(["test", "fake", "fraud", "000", "xxx"])
            pa = f"{prefix}{random.randint(100,999)}{handle}"
            uri = _build_upi_uri(pa, "Suspicious Store", str(random.randint(100, 5000)))

        else:
            uri = f"invalid-content-{i}"

        _save_qr(uri, FAKE_DIR, f"fake_{i+1:03d}.png")
        generated += 1

    print(f"✓ Generated {generated} fake QR samples in {FAKE_DIR}/")


if __name__ == "__main__":
    print("KAVACH – QR Code Dataset Generator\n")
    random.seed(42)  # Reproducible results
    generate_safe_samples(40)
    generate_fake_samples(40)
    print(f"\nDone! Total: 80 QR images generated.")
