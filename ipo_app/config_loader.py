# ipo_app/config_loader.py
from decouple import config
from cryptography.fernet import Fernet

FERNET_KEY = config("FERNET_KEY")
fernet = Fernet(FERNET_KEY.encode())

def decrypt(value):
    return fernet.decrypt(value.encode()).decode()

def load_accounts():
    accounts = []
    i = 1
    while True:
        try:
            name = config(f"ACC{i}_NAME")
            dp_id = config(f"ACC{i}_DP_ID")
            boid = config(f"ACC{i}_BOID")
            username = config(f"ACC{i}_USERNAME")
            password = decrypt(config(f"ACC{i}_PASSWORD"))
            crn = decrypt(config(f"ACC{i}_CRN"))
            pin = decrypt(config(f"ACC{i}_PIN"))
            lot_size = config(f"ACC{i}_LOT", cast=int)

            accounts.append({
                "name": name,
                "dp_id": dp_id,
                "boid": boid,
                "username": username,
                "password": password,
                "crn": crn,
                "pin": pin,
                "lot_size": lot_size,
            })
            i += 1
        except Exception:
            break
    return accounts
