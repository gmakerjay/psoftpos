# -*- coding: utf-8 -*-
"""
Test script for verifying 30-Day Trial System behavior.
Validates:
1. Feature set is 100% identical to full version.
2. Trial start date persists in Windows Registry even if files/DB are deleted.
3. Re-download / file deletion cannot bypass trial expiration on the same machine.
4. License editing / transfer is locked for trial mode.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import utils.license_system_trial_30days as license_system_trial_30days
from utils.license_system_trial_30days import LicenseManager, HardwareID

def test_30day_trial_system():
    print("==========================================================")
    print("      Testing 30-Day Trial System Verification            ")
    print("==========================================================")

    hwid = HardwareID.generate_hwid()
    print(f"Current HWID: {hwid}")
    assert hwid and len(hwid.split('-')) == 4, "HWID format is valid"
    print("  [PASS] HWID generated successfully.")

    # 1. Test check_activation on trial system
    is_ok, msg, data = LicenseManager.check_activation()
    print(f"Activation check result: is_ok={is_ok}, msg={msg}")
    assert data is not None, "License data should be returned"
    assert data.get("is_trial") is True or is_ok is True, "Trial flag or activation status set"

    # Verify features are 100% identical to full version
    features = data.get("features", {})
    required_features = ["pos", "inventory", "reports", "multi_user", "customer_display", "thermal_printer", "barcode_scanner", "tax_invoice", "delivery_note"]
    for feat in required_features:
        assert features.get(feat) is True, f"Feature '{feat}' must be enabled in 30-day trial"
    print("  [PASS] All 9 full-version features are 100% enabled in 30-day trial.")

    # 2. Test Registry persistence (Delete local file & test if Registry holds start date)
    reg_date = LicenseManager._read_registry_trial_date()
    print(f"Windows Registry Trial Date: {reg_date}")
    assert reg_date is not None, "Windows Registry must store trial date on first run"
    print("  [PASS] Windows Registry trial date recorded correctly.")

    # Simulate deleting local trial file
    if LicenseManager.TRIAL_FILE.exists():
        LicenseManager.TRIAL_FILE.unlink()
        print("  - Unlinked local .trial_30days file")

    # Re-check activation: registry date must be used as min(all_dates)
    is_ok2, msg2, data2 = LicenseManager.check_activation()
    assert LicenseManager.TRIAL_FILE.exists(), "Trial file should be re-created from Registry date"
    recreated_date = LicenseManager._read_trial_file()
    assert abs((recreated_date - reg_date).total_seconds()) < 2, "Recreated trial date must match Windows Registry date"
    print("  [PASS] File deletion persistence test passed! App restored start date from Windows Registry.")

    # 3. Test Transfer lock
    ok_trans, msg_trans, _ = LicenseManager.transfer_license()
    assert ok_trans is False, "License transfer should be blocked in trial mode"
    print("  [PASS] License transfer is properly locked in 30-day trial mode.")

    # 4. Test Expiry logic simulation
    past_date = datetime.now() - timedelta(days=35)
    LicenseManager._write_trial_file(past_date)
    LicenseManager._write_trial_db_date(past_date)
    LicenseManager._write_registry_trial_date(past_date)

    is_exp_ok, exp_msg, exp_data = LicenseManager.check_activation()
    assert is_exp_ok is False, "Activation should fail when trial date is 35 days in the past"
    assert "หมดอายุ" in exp_msg, "Expiration message should indicate trial expired"
    print("  [PASS] 30-Day trial expiration lock verified successfully.")

    # Restore current start date for dev safety
    now = datetime.now()
    LicenseManager._write_trial_file(now)
    LicenseManager._write_trial_db_date(now)
    LicenseManager._write_registry_trial_date(now)

    print("==========================================================")
    print("      ALL 30-DAY TRIAL TESTS PASSED SUCCESSFULLY!         ")
    print("==========================================================")

if __name__ == "__main__":
    test_30day_trial_system()
