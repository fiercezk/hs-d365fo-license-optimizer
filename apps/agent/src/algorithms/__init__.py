"""Phase 1 & 2 algorithm implementations for license optimization.

This module exports all 34 implemented algorithms.
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

# Role Management & Analytics Algorithms (4.x, 5.x, 6.x, 7.x)
from .algorithm_4_1_device_license_detector import *  # noqa: F403, F401
from .algorithm_4_2_license_attach_optimizer import *  # noqa: F403, F401
from .algorithm_4_3_cross_app_analyzer import *  # noqa: F403, F401
from .algorithm_4_7_new_user_license_recommender import *  # noqa: F403, F401
from .algorithm_5_1_license_trend_analyzer import *  # noqa: F403, F401
from .algorithm_5_2_security_risk_scorer import *  # noqa: F403, F401
from .algorithm_5_3_time_based_access_analyzer import *  # noqa: F403, F401
from .algorithm_5_4_contractor_access_tracker import *  # noqa: F403, F401
from .algorithm_6_1_stale_role_detector import *  # noqa: F403, F401
from .algorithm_6_2_permission_explosion_detector import *  # noqa: F403, F401
from .algorithm_6_3_duplicate_role_consolidator import *  # noqa: F403, F401
from .algorithm_6_4_role_hierarchy_optimizer import *  # noqa: F403, F401
from .algorithm_7_1_license_utilization_trend import *  # noqa: F403, F401
from .algorithm_7_2_cost_allocation_engine import *  # noqa: F403, F401
from .algorithm_7_4_roi_calculator import *  # noqa: F403, F401
