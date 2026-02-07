"""Phase 1 & 2 algorithm implementations for license optimization.

This module exports all 25 implemented algorithms.
"""

# Cost Optimization Algorithms (1.x, 2.x)
from .algorithm_1_1_role_composition_analyzer import *  # noqa: F403, F401
from .algorithm_1_2_user_segment_analyzer import *  # noqa: F403, F401
from .algorithm_1_3_role_splitting_recommender import *  # noqa: F403, F401
from .algorithm_1_4_component_removal import *  # noqa: F403, F401
from .algorithm_2_1_permission_usage_analyzer import *  # noqa: F403, F401
from .algorithm_2_2_readonly_detector import *  # noqa: F403, F401
from .algorithm_2_3_role_usage_segmentation import *  # noqa: F403, F401
from .algorithm_2_4_multi_role_optimizer import *  # noqa: F403, F401
from .algorithm_2_5_license_minority_detector import *  # noqa: F403, F401
from .algorithm_2_6_cross_role_optimizer import *  # noqa: F403, F401

# Security & Compliance Algorithms (3.x)
from .algorithm_3_1_sod_violation_detector import *  # noqa: F403, F401
from .algorithm_3_2_anomalous_role_change_detector import *  # noqa: F403, F401
from .algorithm_3_3_privilege_creep_detector import *  # noqa: F403, F401
from .algorithm_3_4_toxic_combination_detector import *  # noqa: F403, F401
from .algorithm_3_5_orphaned_account_detector import *  # noqa: F403, F401
from .algorithm_3_6_emergency_account_monitor import *  # noqa: F403, F401
from .algorithm_3_7_service_account_analyzer import *  # noqa: F403, F401
from .algorithm_3_8_access_review_automation import *  # noqa: F403, F401
from .algorithm_3_9_entra_d365_sync_validator import *  # noqa: F403, F401

# Role Management & Analytics Algorithms (4.x, 5.x)
from .algorithm_4_1_device_license_detector import *  # noqa: F403, F401
from .algorithm_4_3_cross_app_analyzer import *  # noqa: F403, F401
from .algorithm_4_7_new_user_license_recommender import *  # noqa: F403, F401
from .algorithm_5_1_license_trend_analyzer import *  # noqa: F403, F401
from .algorithm_5_2_security_risk_scorer import *  # noqa: F403, F401
from .algorithm_5_4_contractor_access_tracker import *  # noqa: F403, F401
