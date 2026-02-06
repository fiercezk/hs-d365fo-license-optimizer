"""Algorithm implementations for license optimization.

Exported algorithms:
  - Algorithm 2.2: Read-Only User Detector
  - Algorithm 2.5: License Minority Detection
  - Algorithm 3.3: Privilege Creep Detector
  - Algorithm 3.4: Toxic Combination Detector
  - Algorithm 3.6: Emergency Account Monitor
  - Algorithm 4.7: New User License Recommender
"""

from .algorithm_2_2_readonly_detector import detect_readonly_users
from .algorithm_2_5_license_minority_detector import detect_license_minority_users
from .algorithm_3_3_privilege_creep_detector import detect_privilege_creep
from .algorithm_3_4_toxic_combination_detector import (
    detect_toxic_combinations,
    detect_toxic_combinations_batch,
)
from .algorithm_3_6_emergency_account_monitor import (
    EmergencyAccountAlert,
    EmergencyAccountAnalysis,
    EmergencyAccountConfig,
    monitor_emergency_accounts,
)
from .algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommender,
    LicenseRecommendationOption,
    suggest_license_for_new_user,
)

__all__ = [
    "detect_readonly_users",
    "detect_license_minority_users",
    "detect_privilege_creep",
    "detect_toxic_combinations",
    "detect_toxic_combinations_batch",
    "EmergencyAccountAlert",
    "EmergencyAccountAnalysis",
    "EmergencyAccountConfig",
    "monitor_emergency_accounts",
    "NewUserLicenseRecommender",
    "LicenseRecommendationOption",
    "suggest_license_for_new_user",
]
