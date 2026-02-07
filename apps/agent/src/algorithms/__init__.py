"""Phase 1 & 2 algorithm implementations for license optimization.

Exported algorithms:
  Phase 1:
  - Algorithm 2.2: Read-Only User Detector
  - Algorithm 2.5: License Minority Detection
  - Algorithm 3.3: Privilege Creep Detector
  - Algorithm 3.4: Toxic Combination Detector
  - Algorithm 4.7: New User License Recommender

  Phase 2:
  - Algorithm 3.5: Orphaned Account Detector
"""

from .algorithm_2_2_readonly_detector import detect_readonly_users
from .algorithm_2_5_license_minority_detector import detect_license_minority_users
from .algorithm_3_3_privilege_creep_detector import detect_privilege_creep
from .algorithm_3_4_toxic_combination_detector import (
    detect_toxic_combinations,
    detect_toxic_combinations_batch,
)
from .algorithm_3_5_orphaned_account_detector import (
    detect_orphaned_accounts,
    OrphanedAccountResult,
    OrphanType,
    UserDirectoryRecord,
)
from .algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommender,
    LicenseRecommendationOption,
    suggest_license_for_new_user,
)

__all__ = [
    # Phase 2
    "detect_orphaned_accounts",
    "OrphanedAccountResult",
    "OrphanType",
    "UserDirectoryRecord",
    # Phase 1
    "detect_readonly_users",
    "detect_license_minority_users",
    "detect_privilege_creep",
    "detect_toxic_combinations",
    "detect_toxic_combinations_batch",
    "NewUserLicenseRecommender",
    "LicenseRecommendationOption",
    "suggest_license_for_new_user",
]
