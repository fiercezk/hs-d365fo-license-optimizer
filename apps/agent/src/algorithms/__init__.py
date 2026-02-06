"""Phase 1 algorithm implementations for license optimization.

Exported algorithms:
  - Algorithm 2.2: Read-Only User Detector
  - Algorithm 2.5: License Minority Detection
  - Algorithm 3.3: Privilege Creep Detector
  - Algorithm 4.7: New User License Recommender
"""

from .algorithm_2_2_readonly_detector import detect_readonly_users
from .algorithm_2_5_license_minority_detector import detect_license_minority_users
from .algorithm_3_3_privilege_creep_detector import detect_privilege_creep
from .algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommender,
    LicenseRecommendationOption,
    suggest_license_for_new_user,
)

__all__ = [
    "detect_readonly_users",
    "detect_license_minority_users",
    "detect_privilege_creep",
    "NewUserLicenseRecommender",
    "LicenseRecommendationOption",
    "suggest_license_for_new_user",
]
