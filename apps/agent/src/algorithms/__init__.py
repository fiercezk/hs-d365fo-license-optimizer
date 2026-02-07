"""Algorithm implementations for license optimization.

Exported algorithms:
  Phase 1:
  - Algorithm 2.2: Read-Only User Detector
  - Algorithm 2.5: License Minority Detection
  - Algorithm 3.3: Privilege Creep Detector
  - Algorithm 3.4: Toxic Combination Detector
  - Algorithm 4.2: License Attach Optimizer
  - Algorithm 4.7: New User License Recommender
  - Algorithm 5.3: Time-Based Access Analyzer
"""

from .algorithm_1_2_user_segment_analyzer import (
    UserSegmentAnalysis,
    UserSegmentDetail,
    analyze_user_segments,
from .algorithm_1_1_role_composition_analyzer import (
    LicenseCompositionEntry,
    RoleComposition,
    analyze_role_composition,
    analyze_roles_batch,
from .algorithm_1_4_component_removal import (
    ComponentRemovalCandidate,
    ComponentRemovalResult,
    recommend_component_removal,
)
from .algorithm_2_2_readonly_detector import detect_readonly_users
from .algorithm_2_5_license_minority_detector import detect_license_minority_users
from .algorithm_3_3_privilege_creep_detector import detect_privilege_creep
from .algorithm_3_4_toxic_combination_detector import (
    detect_toxic_combinations,
    detect_toxic_combinations_batch,
)
from .algorithm_4_2_license_attach_optimizer import (
    AttachOptimization,
    AttachOptimizationResult,
    optimize_license_attach,
)
from .algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommender,
    LicenseRecommendationOption,
    suggest_license_for_new_user,
)
from .algorithm_5_3_time_based_access_analyzer import (
    TimeBasedAccessAlert,
    TimeBasedAccessAnalysis,
    analyze_time_based_access,
)

__all__ = [
    "UserSegmentAnalysis",
    "UserSegmentDetail",
    "analyze_user_segments",
    # Phase 2
    "detect_orphaned_accounts",
    "OrphanedAccountResult",
    "OrphanType",
    "UserDirectoryRecord",
    "analyze_permission_usage",
    "LicenseCompositionEntry",
    "RoleComposition",
    "analyze_role_composition",
    "analyze_roles_batch",
    # Phase 2
    "ComponentRemovalCandidate",
    "ComponentRemovalResult",
    "recommend_component_removal",
    # Phase 1
    "detect_readonly_users",
    "detect_license_minority_users",
    "detect_privilege_creep",
    "detect_toxic_combinations",
    "detect_toxic_combinations_batch",
    "AttachOptimization",
    "AttachOptimizationResult",
    "optimize_license_attach",
    "NewUserLicenseRecommender",
    "LicenseRecommendationOption",
    "suggest_license_for_new_user",
    "TimeBasedAccessAlert",
    "TimeBasedAccessAnalysis",
    "analyze_time_based_access",
]
