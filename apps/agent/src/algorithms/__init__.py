"""D365 FO License & Security Optimization Agent - Algorithm Implementations."""

# Phase 1 Algorithms
from .algorithm_2_2_readonly_detector import (
    ReadOnlyAnalysis,
    analyze_readonly_users,
)
from .algorithm_2_5_license_minority_detector import (
    LicenseMinorityAnalysis,
    analyze_license_minority,
)
from .algorithm_3_1_sod_violation_detector import (
    SoDViolationAnalysis,
    detect_sod_violations,
)
from .algorithm_3_2_anomalous_role_change_detector import (
    AnomalousRoleChangeAnalysis,
    detect_anomalous_role_changes,
)
from .algorithm_3_3_privilege_creep_detector import (
    PrivilegeCreepAnalysis,
    detect_privilege_creep,
)
from .algorithm_3_4_toxic_combination_detector import (
    ToxicCombinationAnalysis,
    detect_toxic_combinations,
)
from .algorithm_4_1_device_license_detector import (
    DeviceLicenseAnalysis,
    analyze_device_license_opportunities,
)
from .algorithm_4_3_cross_app_analyzer import (
    CrossAppAnalysis,
    analyze_cross_app_licenses,
)
from .algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommendation,
    recommend_new_user_license,
)
from .algorithm_5_1_license_trend_analyzer import (
    LicenseTrendAnalysis,
    analyze_license_trends,
)
from .algorithm_5_2_security_risk_scorer import (
    SecurityRiskAnalysis,
    score_security_risks,
)

# Phase 2 Algorithms
# Algorithm 1.1
# Algorithm 1.2
from .algorithm_1_2_user_segment_analyzer import (
    UserSegmentAnalysis,
    analyze_user_segments,
)
# Algorithm 1.3
# Algorithm 2.1

__all__ = [
    # Phase 1
    "ReadOnlyAnalysis",
    "analyze_readonly_users",
    "LicenseMinorityAnalysis",
    "analyze_license_minority",
    "SoDViolationAnalysis",
    "detect_sod_violations",
    "AnomalousRoleChangeAnalysis",
    "detect_anomalous_role_changes",
    "PrivilegeCreepAnalysis",
    "detect_privilege_creep",
    "ToxicCombinationAnalysis",
    "detect_toxic_combinations",
    "DeviceLicenseAnalysis",
    "analyze_device_license_opportunities",
    "CrossAppAnalysis",
    "analyze_cross_app_licenses",
    "NewUserLicenseRecommendation",
    "recommend_new_user_license",
    "LicenseTrendAnalysis",
    "analyze_license_trends",
    "SecurityRiskAnalysis",
    "score_security_risks",
    # Phase 2 exports will be added dynamically
]
