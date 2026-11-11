
"""Nova Software entry point.

Copyright (c) 2026 Nova Software. All rights reserved.
"""

import hashlib
import json
import os
import winreg
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pywintypes
import win32cred

LICENSE_CREDENTIAL_TARGET = "NovaSoftware:KeygenLicense"
DEFAULT_KEYGEN_ACCOUNT_ID = "6d08df46-47ac-4078-9460-67d68a495d3f"


@dataclass(frozen=True)
class LicenseValidation:
    valid: bool
    license_id: str | None = None
    code: str | None = None
    expiry: datetime | None = None
    expiry_known: bool = False


def load_saved_license_key() -> str | None:
    try:
        credential = win32cred.CredRead(
            LICENSE_CREDENTIAL_TARGET,
            win32cred.CRED_TYPE_GENERIC,
            0,
        )
    except pywintypes.error as error:
        if error.winerror == 1168:
            return None
        raise RuntimeError(
            "Could not read the saved license from Windows Credential Manager."
        ) from error

    license_blob = credential.get("CredentialBlob")
    if isinstance(license_blob, bytes):
        try:
            license_key = license_blob.decode("utf-16-le").rstrip("\x00")
        except UnicodeDecodeError as error:
            raise RuntimeError(
                "The saved license in Windows Credential Manager is invalid."
            ) from error
    elif isinstance(license_blob, str):
        license_key = license_blob
    else:
        license_key = ""
    if not license_key:
        raise RuntimeError(
            "The saved license in Windows Credential Manager is invalid."
        )
    return license_key


def save_license_key(license_key: str) -> None:
    try:
        win32cred.CredWrite(
            {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": LICENSE_CREDENTIAL_TARGET,
                "CredentialBlob": license_key,
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
                "UserName": "Nova Software",
            },
            0,
        )
    except pywintypes.error as error:
        raise RuntimeError(
            "Could not save the license in Windows Credential Manager."
        ) from error


def get_machine_fingerprint(account_id: str) -> str:
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        ) as key:
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        if not isinstance(machine_guid, str) or not machine_guid:
            raise RuntimeError("The computer's machine ID is unavailable.")
    except OSError as error:
        raise RuntimeError("Could not read this computer's machine ID.") from error

    fingerprint_source = f"Nova Software:{account_id}:{machine_guid}"
    return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()


def get_keygen_error_message(error: HTTPError) -> str:
    try:
        result = json.loads(error.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ""

    if not isinstance(result, dict):
        return ""
    errors = result.get("errors")
    if not isinstance(errors, list):
        return ""

    messages = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        detail = item.get("detail") or item.get("title")
        if not isinstance(detail, str) or not detail:
            continue
        source = item.get("source")
        pointer = source.get("pointer") if isinstance(source, dict) else None
        messages.append(f"{pointer}: {detail}" if pointer else detail)
    return "; ".join(messages)


def activate_machine(
    license_key: str, account_id: str, fingerprint: str, license_id: str
) -> bool:
    endpoint = f"https://api.keygen.sh/v1/accounts/{account_id}/machines"
    request = Request(
        endpoint,
        data=json.dumps(
            {
                "data": {
                    "type": "machines",
                    "attributes": {
                        "fingerprint": fingerprint,
                        "name": "Nova Software",
                        "platform": "Windows",
                    },
                    "relationships": {
                        "license": {
                            "data": {"type": "licenses", "id": license_id}
                        }
                    },
                }
            }
        ).encode("utf-8"),
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"License {license_key.strip()}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10):
            return True
    except HTTPError as error:
        message = get_keygen_error_message(error)
        if message:
            print(f"Keygen nu a putut activa acest dispozitiv: {message}")
        else:
            print(f"Keygen nu a putut activa acest dispozitiv (HTTP {error.code}).")
        return False
    except URLError as error:
        print(f"Could not contact the licensing service: {error.reason}")
        return False
    except TimeoutError:
        print("The licensing service request timed out.")
        return False


def validate_license_key(
    license_key: str, account_id: str, fingerprint: str | None = None
) -> LicenseValidation:
    endpoint = (
        f"https://api.keygen.sh/v1/accounts/{account_id}/licenses/actions/validate-key"
    )
    scope = {"fingerprint": fingerprint} if fingerprint else None
    meta = {"key": license_key.strip()}
    if scope is not None:
        meta["scope"] = scope
    request = Request(
        endpoint,
        data=json.dumps({"meta": meta}).encode("utf-8"),
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        message = get_keygen_error_message(error)
        if message:
            print(f"Licensing service returned HTTP {error.code}: {message}")
        else:
            print(f"Licensing service returned HTTP {error.code}.")
        return LicenseValidation(False)
    except URLError as error:
        print(f"Could not contact the licensing service: {error.reason}")
        return LicenseValidation(False)
    except TimeoutError:
        print("The licensing service request timed out.")
        return LicenseValidation(False)
    except (UnicodeDecodeError, json.JSONDecodeError):
        print("The licensing service returned an invalid response.")
        return LicenseValidation(False)

    if not isinstance(result, dict):
        print("The licensing service returned an invalid response.")
        return LicenseValidation(False)

    meta = result.get("meta")
    if not isinstance(meta, dict):
        print("The licensing service returned an invalid response.")
        return LicenseValidation(False)

    license_data = result.get("data")
    license_id = None
    if (
        isinstance(license_data, dict)
        and license_data.get("type") == "licenses"
        and isinstance(license_data.get("id"), str)
        and license_data["id"]
    ):
        license_id = license_data["id"]

    expiry_known = False
    expiry = None
    if isinstance(license_data, dict) and isinstance(
        license_data.get("attributes"), dict
    ):
        attributes = license_data["attributes"]
        if "expiry" in attributes:
            expiry_known = True
            expiry_value = attributes["expiry"]
            if expiry_value is not None:
                if not isinstance(expiry_value, str):
                    print("The licensing service returned an invalid expiry date.")
                    return LicenseValidation(False, license_id)
                try:
                    expiry = datetime.fromisoformat(
                        expiry_value.replace("Z", "+00:00")
                    )
                    if expiry.tzinfo is None:
                        expiry = expiry.replace(tzinfo=timezone.utc)
                except ValueError:
                    print("The licensing service returned an invalid expiry date.")
                    return LicenseValidation(False, license_id)

    if not isinstance(meta.get("valid"), bool):
        code = meta.get("code")
        detail = meta.get("detail")
        if code or detail:
            print(
                "Keygen nu a putut confirma licenta: "
                f"{code or 'unknown'} {detail or ''}".strip()
            )
            return LicenseValidation(
                False,
                license_id,
                code if isinstance(code, str) else None,
                expiry,
                expiry_known,
            )
        print("The licensing service returned an invalid response.")
        return LicenseValidation(
            False,
            license_id,
            expiry=expiry,
            expiry_known=expiry_known,
        )

    if not meta["valid"]:
        code = meta.get("code")
        detail = meta.get("detail")
        expected_scope_codes = {
            "FINGERPRINT_SCOPE_REQUIRED",
            "NO_MACHINES",
        }
        if code not in expected_scope_codes and (code or detail):
            print(
                "Keygen a respins licenta: "
                f"{code or 'INVALID'} {detail or ''}".strip()
            )
        elif code not in expected_scope_codes:
            print("Keygen a respins licenta fara sa ofere un motiv.")
        return LicenseValidation(
            False,
            license_id,
            code if isinstance(code, str) else None,
            expiry,
            expiry_known,
        )

    return LicenseValidation(True, license_id, "VALID", expiry, expiry_known)


def print_license_expiry(validation: LicenseValidation) -> None:
    if not validation.expiry_known:
        print("Keygen nu a returnat data expirarii licentei.")
        return
    if validation.expiry is None:
        print("Licenta nu are data de expirare (nelimitata).")
        return

    remaining_seconds = int(
        (
            validation.expiry.astimezone(timezone.utc)
            - datetime.now(timezone.utc)
        ).total_seconds()
    )
    if remaining_seconds <= 0:
        print("Licenta expira acum sau a expirat.")
        return

    days, remaining_seconds = divmod(remaining_seconds, 24 * 60 * 60)
    hours, remaining_seconds = divmod(remaining_seconds, 60 * 60)
    minutes, seconds = divmod(remaining_seconds, 60)
    parts = []
    if days:
        parts.append(f"{days} {'zi' if days == 1 else 'zile'}")
    if hours:
        parts.append(f"{hours} {'ora' if hours == 1 else 'ore'}")
    if minutes:
        parts.append(f"{minutes} {'minut' if minutes == 1 else 'minute'}")
    if not parts:
        parts.append(f"{seconds} secunde")
    print(f"Licenta valida. Timp ramas: {', '.join(parts)}.")


if __name__ == "__main__":
    account_id = os.environ.get(
        "NOVA_KEYGEN_ACCOUNT_ID", DEFAULT_KEYGEN_ACCOUNT_ID
    ).strip()
    if not account_id:
        print("License check is not configured.")
        print(
            "Set the NOVA_KEYGEN_ACCOUNT_ID environment variable "
            "to your public Keygen account ID."
        )
        raise SystemExit(1)

    try:
        saved_license_key = load_saved_license_key()
    except RuntimeError as error:
        print(f"Nu am putut accesa cheia salvata: {error}")
        saved_license_key = None

    if saved_license_key:
        entered_key = input(
            "Apasa Enter pentru licenta salvata sau lipeste cheia noua: "
        ).strip()
        if entered_key.casefold() == "schimba":
            license_key = input("Introdu sau lipeste noua cheie de licenta: ").strip()
        elif entered_key:
            license_key = entered_key
        else:
            license_key = saved_license_key
    else:
        license_key = input("Introdu sau lipeste cheia de licenta: ").strip()

    if not license_key and saved_license_key:
        license_key = saved_license_key
    if not license_key:
        print("Nu a fost introdusa nicio cheie de licenta.")
        raise SystemExit(1)

    validation = validate_license_key(license_key, account_id)
    if not validation.valid and validation.code in (
        "FINGERPRINT_SCOPE_REQUIRED",
        "NO_MACHINES",
    ):
        try:
            fingerprint = get_machine_fingerprint(account_id)
        except RuntimeError as error:
            print(f"License check could not identify this computer: {error}")
            raise SystemExit(1) from error

        validation = validate_license_key(license_key, account_id, fingerprint)
        if (
            not validation.valid
            and validation.code == "NO_MACHINES"
            and validation.license_id
        ):
            if not activate_machine(
                license_key,
                account_id,
                fingerprint,
                validation.license_id,
            ):
                raise SystemExit(1)
            validation = validate_license_key(
                license_key, account_id, fingerprint
            )

    if not validation.valid:
        print("Cheie de licenta invalida.")
        raise SystemExit(1)

    print_license_expiry(validation)
    if license_key != saved_license_key:
        try:
            save_license_key(license_key)
            print("Cheia de licenta a fost salvata in Windows Credential Manager.")
        except RuntimeError as error:
            print(f"Nu am putut salva cheia de licenta: {error}")

    from nova_software import NovaSoftware

    nova_software = NovaSoftware()
    nova_software.run()
