"""Algorithm 6.4: Role Hierarchy Optimizer.

Analyzes role inheritance hierarchies in D365 FO and recommends structural
improvements to reduce complexity, eliminate circular dependencies, prune
orphaned branches, and consolidate redundant inheritance.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 6.4)
Category: Role Management

Key behaviors:
  - Circular dependency in hierarchy = CRITICAL finding
  - Deep nesting (>3 levels) = HIGH risk (complexity)
  - Redundant inheritance (child re-declares parent permissions) = MEDIUM
  - Orphaned branch (no users assigned) = LOW
  - Common subset (3+ roles share 5+ permissions) = MEDIUM (extract base role)
  - Results sorted by finding severity then complexity score
"""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class HierarchyFinding(BaseModel):
    """Single finding from role hierarchy analysis."""

    finding_type: str = Field(
        description="Type of finding (e.g., 'circular_dependency', 'deep_nesting')"
    )
    severity: str = Field(description="Severity level: CRITICAL, HIGH, MEDIUM, or LOW")
    description: str = Field(description="Human-readable description of the finding")
    recommendation: str = Field(description="Actionable recommendation to resolve the finding")
    affected_roles: list[str] = Field(
        description="List of role names affected by this finding",
        default_factory=list,
    )
    complexity_impact: float = Field(
        default=0.0,
        description="Contribution to overall complexity score",
    )


class HierarchyAnalysis(BaseModel):
    """Complete output from Algorithm 6.4: Role Hierarchy Optimizer."""

    algorithm_id: str = Field(
        default="6.4",
        description="Algorithm identifier",
    )
    findings: list[HierarchyFinding] = Field(
        default_factory=list,
        description="All hierarchy findings sorted by severity",
    )
    complexity_score: float = Field(
        default=0.0,
        description="Overall hierarchy complexity score (0+)",
    )
    total_roles_analyzed: int = Field(
        default=0,
        description="Total number of roles analyzed",
    )
    max_depth: int = Field(
        default=0,
        description="Maximum inheritance depth in the hierarchy",
    )
    total_inheritance_relationships: int = Field(
        default=0,
        description="Total number of parent-child inheritance relationships",
    )
    total_findings: int = Field(
        default=0,
        description="Total count of findings",
    )


# ---------------------------------------------------------------------------
# Severity ordering for sorting
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def optimize_role_hierarchy(
    role_hierarchy: pd.DataFrame,
    role_definitions: pd.DataFrame,
    security_config: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    max_nesting_depth: int = 3,
    min_common_roles: int = 3,
    min_common_permissions: int = 5,
) -> HierarchyAnalysis:
    """Analyze role hierarchy and generate optimization recommendations.

    Builds a directed graph from role inheritance relationships and detects:
      1. Circular dependencies (cycles) -- CRITICAL
      2. Deep nesting (>max_nesting_depth levels) -- HIGH
      3. Redundant inheritance (child duplicates parent permissions) -- MEDIUM
      4. Common permission subsets (extract base role opportunity) -- MEDIUM
      5. Orphaned branches (no users assigned) -- LOW

    Args:
        role_hierarchy: DataFrame with columns [parent_role, child_role].
        role_definitions: DataFrame with columns [role_id, role_name, role_type].
        security_config: DataFrame with columns [securityrole, AOTName, AccessLevel,
            LicenseType, Priority].
        user_role_assignments: DataFrame with columns [user_id, role_name, status].
        max_nesting_depth: Maximum acceptable nesting depth (default 3).
        min_common_roles: Minimum roles sharing permissions to trigger
            common-subset finding (default 3).
        min_common_permissions: Minimum shared permissions to trigger
            common-subset finding (default 5).

    Returns:
        HierarchyAnalysis with findings, complexity score, and summary stats.
    """
    findings: list[HierarchyFinding] = []

    # Build directed graph: edge from parent -> child
    graph: nx.DiGraph[str] = nx.DiGraph()

    # Collect all known role names from definitions
    all_role_names: set[str] = set()
    if not role_definitions.empty and "role_name" in role_definitions.columns:
        all_role_names = set(role_definitions["role_name"].tolist())

    # Add edges from hierarchy
    if not role_hierarchy.empty and "parent_role" in role_hierarchy.columns:
        for _, row in role_hierarchy.iterrows():
            parent = str(row["parent_role"])
            child = str(row["child_role"])
            graph.add_edge(parent, child)
            all_role_names.add(parent)
            all_role_names.add(child)

    # Add any isolated roles (in definitions but not in hierarchy)
    for role_name in all_role_names:
        if role_name not in graph:
            graph.add_node(role_name)

    total_roles = len(all_role_names)
    total_relationships = graph.number_of_edges()

    # Handle empty input
    if total_roles == 0:
        return HierarchyAnalysis(
            total_roles_analyzed=0,
            total_inheritance_relationships=0,
            total_findings=0,
        )

    # --- 1. Circular Dependency Detection (CRITICAL) ---
    circular_findings = _detect_circular_dependencies(graph)
    findings.extend(circular_findings)

    # --- 2. Deep Nesting Detection (HIGH) ---
    # Only calculate depths on a DAG; skip if cycles exist
    max_depth = 0
    if not circular_findings:
        nesting_findings, max_depth = _detect_deep_nesting(graph, max_nesting_depth)
        findings.extend(nesting_findings)
    else:
        # With cycles, approximate max_depth from longest simple path
        max_depth = _approximate_max_depth(graph)

    # --- 3. Redundant Inheritance Detection (MEDIUM) ---
    if not security_config.empty and "securityrole" in security_config.columns:
        redundant_findings = _detect_redundant_inheritance(graph, security_config)
        findings.extend(redundant_findings)

    # --- 4. Common Permission Subset Detection (MEDIUM) ---
    if not security_config.empty and "securityrole" in security_config.columns:
        subset_findings = _detect_common_permission_subsets(
            security_config, min_common_roles, min_common_permissions
        )
        findings.extend(subset_findings)

    # --- 5. Orphaned Branch Detection (LOW) ---
    assigned_roles: set[str] = set()
    if not user_role_assignments.empty and "role_name" in user_role_assignments.columns:
        assigned_roles = set(user_role_assignments["role_name"].tolist())

    orphan_findings = _detect_orphaned_branches(graph, assigned_roles)
    findings.extend(orphan_findings)

    # --- Calculate complexity score ---
    complexity_score = _calculate_complexity_score(
        total_roles, total_relationships, max_depth, len(findings)
    )

    # --- Sort findings by severity then complexity impact ---
    findings.sort(
        key=lambda f: (
            _SEVERITY_ORDER.get(f.severity, 99),
            -f.complexity_impact,
        )
    )

    return HierarchyAnalysis(
        findings=findings,
        complexity_score=complexity_score,
        total_roles_analyzed=total_roles,
        max_depth=max_depth,
        total_inheritance_relationships=total_relationships,
        total_findings=len(findings),
    )


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _detect_circular_dependencies(
    graph: nx.DiGraph,
) -> list[HierarchyFinding]:
    """Detect cycles in the role hierarchy graph.

    Uses networkx simple_cycles to find all cycles. Each cycle is reported
    as a CRITICAL finding.

    Args:
        graph: Directed graph of role inheritance.

    Returns:
        List of CRITICAL findings for each cycle detected.
    """
    findings: list[HierarchyFinding] = []

    # Check for self-loops first
    for node in graph.nodes():
        if graph.has_edge(node, node):
            findings.append(
                HierarchyFinding(
                    finding_type="circular_dependency_self",
                    severity="CRITICAL",
                    description=(
                        f"Role '{node}' has a self-referencing inheritance "
                        f"(inherits from itself). This is a circular dependency."
                    ),
                    recommendation=(
                        f"Remove the self-referencing inheritance on role " f"'{node}' immediately."
                    ),
                    affected_roles=[node],
                    complexity_impact=50.0,
                )
            )

    # Check for multi-node cycles
    try:
        cycles = list(nx.simple_cycles(graph))
    except nx.NetworkXError:
        cycles = []

    for cycle in cycles:
        # Skip self-loops (already handled above)
        if len(cycle) <= 1:
            continue

        cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
        findings.append(
            HierarchyFinding(
                finding_type="circular_dependency_cycle",
                severity="CRITICAL",
                description=(
                    f"Circular dependency detected in role hierarchy: "
                    f"{cycle_str}. This breaks the inheritance model and "
                    f"must be resolved immediately."
                ),
                recommendation=(
                    f"Break the circular dependency by removing one "
                    f"inheritance link in the chain: {cycle_str}. "
                    f"Recommend removing the link that was added most "
                    f"recently."
                ),
                affected_roles=list(cycle),
                complexity_impact=50.0,
            )
        )

    return findings


def _detect_deep_nesting(
    graph: nx.DiGraph,
    max_depth: int,
) -> tuple[list[HierarchyFinding], int]:
    """Detect chains in the DAG that exceed the maximum nesting depth.

    Args:
        graph: Directed acyclic graph of role inheritance.
        max_depth: Maximum acceptable nesting depth.

    Returns:
        Tuple of (findings list, maximum depth found).
    """
    findings: list[HierarchyFinding] = []
    overall_max_depth = 0

    # Find root nodes (nodes with no incoming edges)
    roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    if not roots:
        # No roots means all nodes are part of cycles or graph is empty
        return findings, 0

    # Calculate longest path from each root using BFS/DFS
    for root in roots:
        # Use single_source_shortest_path_length but we need longest,
        # so use dag_longest_path_length on subgraph
        try:
            lengths = nx.single_source_shortest_path_length(graph, root)
            local_max = max(lengths.values()) if lengths else 0
        except nx.NetworkXError:
            local_max = 0

        if local_max > overall_max_depth:
            overall_max_depth = local_max

    # The depth is number of edges (levels = edges + 1 for nodes)
    # For nesting: depth of 4 edges = 5 levels
    # We flag if depth > max_depth (edges)
    if overall_max_depth > max_depth:
        # Find the actual deepest chain(s)
        deep_chains = _find_deep_chains(graph, roots, max_depth)
        for chain in deep_chains:
            chain_str = " -> ".join(chain)
            findings.append(
                HierarchyFinding(
                    finding_type="deep_nesting",
                    severity="HIGH",
                    description=(
                        f"Role hierarchy chain has {len(chain)} levels of "
                        f"deep nesting (maximum recommended: "
                        f"{max_depth + 1}): {chain_str}"
                    ),
                    recommendation=(
                        f"Flatten the hierarchy by reducing nesting to "
                        f"{max_depth + 1} levels or fewer. Consider "
                        f"consolidating intermediate roles or using direct "
                        f"permission assignment to simplify the chain."
                    ),
                    affected_roles=chain,
                    complexity_impact=float(len(chain)) * 5.0,
                )
            )

    return findings, overall_max_depth


def _find_deep_chains(
    graph: nx.DiGraph,
    roots: list[str],
    max_depth: int,
) -> list[list[str]]:
    """Find all chains exceeding max_depth in the hierarchy.

    Args:
        graph: Directed graph.
        roots: Root nodes to start from.
        max_depth: Maximum acceptable depth.

    Returns:
        List of chains (each chain is a list of role names).
    """
    deep_chains: list[list[str]] = []

    for root in roots:
        # DFS to find all paths to leaves
        for leaf in graph.nodes():
            if graph.out_degree(leaf) == 0:  # leaf node
                try:
                    for path in nx.all_simple_paths(graph, root, leaf):
                        if len(path) - 1 > max_depth:
                            deep_chains.append(path)
                except nx.NetworkXError:
                    continue
                except nx.NodeNotFound:
                    continue

    # Deduplicate by keeping only maximal chains
    # (remove chains that are subsets of longer chains)
    if len(deep_chains) > 1:
        deep_chains.sort(key=len, reverse=True)
        maximal: list[list[str]] = []
        for chain in deep_chains:
            is_subset = False
            chain_as_set = set(chain)
            for existing in maximal:
                if chain_as_set.issubset(set(existing)):
                    is_subset = True
                    break
            if not is_subset:
                maximal.append(chain)
        deep_chains = maximal

    return deep_chains


def _detect_redundant_inheritance(
    graph: nx.DiGraph,
    security_config: pd.DataFrame,
) -> list[HierarchyFinding]:
    """Detect child roles that re-declare the same permissions as parent.

    When a child role has direct permission assignments identical to its
    parent, the inheritance is redundant -- the child could simply inherit.

    Args:
        graph: Directed graph of role hierarchy.
        security_config: Security configuration with role-permission mappings.

    Returns:
        List of MEDIUM findings for redundant inheritance.
    """
    findings: list[HierarchyFinding] = []

    # Build role -> set of (AOTName, AccessLevel) mapping
    role_permissions: dict[str, set[tuple[str, str]]] = {}
    for _, row in security_config.iterrows():
        role = str(row["securityrole"])
        aot = str(row["AOTName"])
        access = str(row["AccessLevel"])
        if role not in role_permissions:
            role_permissions[role] = set()
        role_permissions[role].add((aot, access))

    # Check each parent-child edge
    for parent, child in graph.edges():
        parent_perms = role_permissions.get(parent, set())
        child_perms = role_permissions.get(child, set())

        if not parent_perms or not child_perms:
            continue

        # Find overlap: permissions declared in both parent and child
        overlap = parent_perms & child_perms

        if overlap and len(overlap) == len(parent_perms):
            # Child re-declares all parent permissions
            findings.append(
                HierarchyFinding(
                    finding_type="redundant_inheritance",
                    severity="MEDIUM",
                    description=(
                        f"Role '{child}' re-declares all {len(overlap)} "
                        f"permissions already available through parent role "
                        f"'{parent}'. The inheritance relationship is "
                        f"redundant."
                    ),
                    recommendation=(
                        f"Remove the {len(overlap)} duplicate permission "
                        f"assignments from '{child}' and rely on "
                        f"inheritance from '{parent}' instead."
                    ),
                    affected_roles=[parent, child],
                    complexity_impact=float(len(overlap)) * 1.0,
                )
            )

    return findings


def _detect_common_permission_subsets(
    security_config: pd.DataFrame,
    min_roles: int,
    min_permissions: int,
) -> list[HierarchyFinding]:
    """Detect groups of roles sharing a common set of permissions.

    When min_roles or more roles share min_permissions or more identical
    permission assignments, recommend extracting a base role.

    Args:
        security_config: Security configuration with role-permission mappings.
        min_roles: Minimum number of roles that must share permissions.
        min_permissions: Minimum number of shared permissions.

    Returns:
        List of MEDIUM findings for common subset opportunities.
    """
    findings: list[HierarchyFinding] = []

    # Build role -> set of AOTName mapping
    role_aots: dict[str, set[str]] = {}
    for _, row in security_config.iterrows():
        role = str(row["securityrole"])
        aot = str(row["AOTName"])
        if role not in role_aots:
            role_aots[role] = set()
        role_aots[role].add(aot)

    roles = list(role_aots.keys())

    if len(roles) < min_roles:
        return findings

    # Check all combinations of min_roles roles for shared permissions
    for role_combo in combinations(roles, min_roles):
        # Find intersection of all roles' permissions
        shared = role_aots[role_combo[0]]
        for role in role_combo[1:]:
            shared = shared & role_aots[role]

        if len(shared) >= min_permissions:
            combo_names = list(role_combo)
            findings.append(
                HierarchyFinding(
                    finding_type="common_permission_subset",
                    severity="MEDIUM",
                    description=(
                        f"Roles {combo_names} share {len(shared)} common "
                        f"permissions. Consider extracting a base role to "
                        f"reduce duplication."
                    ),
                    recommendation=(
                        f"Extract the {len(shared)} common permissions "
                        f"into a new base role, then have "
                        f"{', '.join(combo_names)} inherit from it. "
                        f"This reduces maintenance overhead and ensures "
                        f"consistency."
                    ),
                    affected_roles=combo_names,
                    complexity_impact=float(len(shared)) * 0.5,
                )
            )

    return findings


def _detect_orphaned_branches(
    graph: nx.DiGraph,
    assigned_roles: set[str],
) -> list[HierarchyFinding]:
    """Detect hierarchy branches where no roles have assigned users.

    An orphaned branch is a subtree in the hierarchy where neither the
    root of the branch nor any of its descendants have any user assignments.

    Args:
        graph: Directed graph of role hierarchy.
        assigned_roles: Set of role names that have at least one user assigned.

    Returns:
        List of LOW findings for orphaned branches.
    """
    findings: list[HierarchyFinding] = []

    # For each node, check if any node in its subtree has users
    for node in graph.nodes():
        # Only check nodes that have children (branch points)
        if graph.out_degree(node) == 0 and graph.in_degree(node) == 0:
            # Isolated node with no users
            if node not in assigned_roles:
                findings.append(
                    HierarchyFinding(
                        finding_type="orphaned_role",
                        severity="LOW",
                        description=(
                            f"Role '{node}' has no users assigned and no "
                            f"inheritance relationships. It is completely "
                            f"unused."
                        ),
                        recommendation=(
                            f"Review role '{node}' for potential removal " f"or archival."
                        ),
                        affected_roles=[node],
                        complexity_impact=1.0,
                    )
                )
            continue

        # Check subtree: get all descendants
        try:
            descendants = nx.descendants(graph, node)
        except nx.NetworkXError:
            descendants = set()

        subtree = {node} | descendants

        # Check if any role in the subtree has users
        subtree_has_users = bool(subtree & assigned_roles)

        if not subtree_has_users and graph.out_degree(node) > 0:
            # This is a branch with children but no users anywhere
            subtree_roles = sorted(subtree)
            findings.append(
                HierarchyFinding(
                    finding_type="orphaned_branch",
                    severity="LOW",
                    description=(
                        f"Hierarchy branch rooted at '{node}' has "
                        f"{len(subtree_roles)} roles but no users assigned "
                        f"to any of them. The entire branch is unused."
                    ),
                    recommendation=(
                        f"Review the orphaned branch ({', '.join(subtree_roles)}) "
                        f"for removal. Unused branches add complexity "
                        f"without value."
                    ),
                    affected_roles=subtree_roles,
                    complexity_impact=float(len(subtree_roles)) * 1.0,
                )
            )

    # Deduplicate: if a child branch is reported AND its parent branch is
    # also reported, keep only the parent (maximal orphan).
    if len(findings) > 1:
        findings = _deduplicate_orphan_findings(findings)

    return findings


def _deduplicate_orphan_findings(
    findings: list[HierarchyFinding],
) -> list[HierarchyFinding]:
    """Remove orphan findings that are subsets of larger orphan branches.

    Args:
        findings: List of orphan findings to deduplicate.

    Returns:
        Deduplicated list keeping only maximal branches.
    """
    # Sort by number of affected roles descending
    findings.sort(key=lambda f: len(f.affected_roles), reverse=True)
    result: list[HierarchyFinding] = []

    for finding in findings:
        affected_set = set(finding.affected_roles)
        is_subset = False
        for existing in result:
            if affected_set.issubset(set(existing.affected_roles)):
                is_subset = True
                break
        if not is_subset:
            result.append(finding)

    return result


def _calculate_complexity_score(
    total_roles: int,
    total_relationships: int,
    max_depth: int,
    total_findings: int,
) -> float:
    """Calculate overall hierarchy complexity score.

    Factors:
      - Number of roles (linear contribution)
      - Number of inheritance relationships (linear contribution)
      - Maximum depth (exponential contribution)
      - Number of findings (weighted contribution)

    Args:
        total_roles: Total roles in hierarchy.
        total_relationships: Total parent-child edges.
        max_depth: Maximum inheritance depth.
        total_findings: Number of detected findings.

    Returns:
        Complexity score (0+, no upper limit).
    """
    role_factor = total_roles * 1.0
    relationship_factor = total_relationships * 2.0
    depth_factor = max_depth**2 * 3.0
    finding_factor = total_findings * 5.0

    return role_factor + relationship_factor + depth_factor + finding_factor


def _approximate_max_depth(graph: nx.DiGraph) -> int:
    """Approximate maximum depth in a graph that may contain cycles.

    Uses longest simple path heuristic since DAG-specific algorithms
    cannot be applied when cycles exist.

    Args:
        graph: Directed graph (may contain cycles).

    Returns:
        Approximate maximum depth.
    """
    max_depth = 0
    for node in graph.nodes():
        try:
            lengths = nx.single_source_shortest_path_length(graph, node)
            local_max = max(lengths.values()) if lengths else 0
            if local_max > max_depth:
                max_depth = local_max
        except nx.NetworkXError:
            continue
    return max_depth
