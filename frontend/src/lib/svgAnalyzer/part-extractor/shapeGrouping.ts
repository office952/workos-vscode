import type { ConfidenceLevel } from '../analyzer/types'
import type { SvgPartWarning } from './partTypes'
import { partSplitWarning } from './partSplittingWarnings'
import { isInnerContourHoleOfOuter } from './shapeBounds'
import type { ExtractedSubPath } from './subPathExtractor'

export interface GroupedShape {
  id: string
  layerId: string | null
  layerName: string | null
  colors: string[]
  subPaths: ExtractedSubPath[]
  outerSubPaths: ExtractedSubPath[]
  innerSubPaths: ExtractedSubPath[]
  fragmentSubPaths: ExtractedSubPath[]
  geometryFragmentSubPaths: ExtractedSubPath[]
  boundsMm: { x: number; y: number; width: number; height: number } | null
  perimeterMm: number | null
  outerPerimeterMm: number | null
  totalContourPerimeterMm: number | null
  splitConfidence: ConfidenceLevel
  groupingReason: 'bbox-containment' | 'single-subpath' | 'fallback-layer' | 'unknown'
}

interface FragmentLink {
  parentId: string
  includeInGeometry: boolean
  reason: string
}

interface SubPathAssignment {
  subPathIndex: number
  layerName: string | null
  closed: boolean
  bboxMm: { x: number; y: number; width: number; height: number } | null
  assignedGroupId: string | null
  classification: 'outer' | 'inner' | 'fragment' | 'ambiguous'
  reason: string
}

interface GroupingResult {
  groups: GroupedShape[]
  warnings: SvgPartWarning[]
  confidence: ConfidenceLevel
  assignments: SubPathAssignment[]
}

function bboxArea(bbox: { width: number; height: number } | null): number {
  if (!bbox) return 0
  return bbox.width * bbox.height
}

function contains(outer: ExtractedSubPath, inner: ExtractedSubPath, toleranceMm: number): boolean {
  if (!outer.bboxMm || !inner.bboxMm) {
    return false
  }

  return (
    inner.bboxMm.x >= outer.bboxMm.x - toleranceMm &&
    inner.bboxMm.y >= outer.bboxMm.y - toleranceMm &&
    inner.bboxMm.x + inner.bboxMm.width <= outer.bboxMm.x + outer.bboxMm.width + toleranceMm &&
    inner.bboxMm.y + inner.bboxMm.height <= outer.bboxMm.y + outer.bboxMm.height + toleranceMm
  )
}

function isCentroidInsidePathFill(
  outer: ExtractedSubPath,
  inner: ExtractedSubPath,
  mmPerVbu: number | null,
): boolean {
  if (!inner.closed || !outer.closed || !inner.bboxMm) {
    return false
  }
  return isInnerContourHoleOfOuter(outer.d, inner.d, inner.bboxMm, mmPerVbu)
}

function isSubPathHoleOfOuter(
  outer: ExtractedSubPath,
  inner: ExtractedSubPath,
  mmPerVbu: number | null,
  bboxToleranceMm = 28,
): boolean {
  if (!inner.closed || !outer.closed || !inner.bboxMm || !outer.bboxMm) {
    return false
  }
  if (!shouldBeInnerContour(outer, inner)) {
    return false
  }

  const bboxPrefilter =
    contains(outer, inner, 0.5) ||
    contains(outer, inner, bboxToleranceMm) ||
    bboxIntersectsExpanded(outer.bboxMm, inner.bboxMm, bboxToleranceMm)

  if (!bboxPrefilter) {
    return false
  }

  return isInnerContourHoleOfOuter(outer.d, inner.d, inner.bboxMm, mmPerVbu)
}

function bboxIntersectsExpanded(
  outer: { x: number; y: number; width: number; height: number },
  inner: { x: number; y: number; width: number; height: number },
  toleranceMm: number,
): boolean {
  const outerRight = outer.x + outer.width + toleranceMm
  const outerBottom = outer.y + outer.height + toleranceMm
  const innerRight = inner.x + inner.width
  const innerBottom = inner.y + inner.height
  return !(
    inner.x > outerRight ||
    innerRight < outer.x - toleranceMm ||
    inner.y > outerBottom ||
    innerBottom < outer.y - toleranceMm
  )
}

function isSubPathContainedInOuter(
  outer: ExtractedSubPath,
  inner: ExtractedSubPath,
  _mmPerVbu: number | null,
  toleranceMm: number,
): boolean {
  return contains(outer, inner, toleranceMm)
}

function resolveOuterRootId(
  subPathId: string,
  parentById: Map<string, string | null>,
  assignmentById: Map<string, SubPathAssignment>,
): string {
  let current = subPathId
  for (let guard = 0; guard < 32; guard += 1) {
    const parentId = parentById.get(current)
    if (!parentId) {
      return current
    }
    const parentAssignment = assignmentById.get(parentId)
    if (!parentAssignment || parentAssignment.classification === 'outer') {
      return parentId
    }
    current = parentId
  }
  return subPathId
}

function overlapRatioY(a: ExtractedSubPath, b: ExtractedSubPath): number {
  if (!a.bboxMm || !b.bboxMm) return 0
  const top = Math.max(a.bboxMm.y, b.bboxMm.y)
  const bottom = Math.min(a.bboxMm.y + a.bboxMm.height, b.bboxMm.y + b.bboxMm.height)
  const overlap = Math.max(0, bottom - top)
  const minHeight = Math.max(1e-6, Math.min(a.bboxMm.height, b.bboxMm.height))
  return overlap / minHeight
}

function horizontalGap(a: ExtractedSubPath, b: ExtractedSubPath): number {
  if (!a.bboxMm || !b.bboxMm) return Number.POSITIVE_INFINITY
  const aLeft = a.bboxMm.x
  const aRight = a.bboxMm.x + a.bboxMm.width
  const bLeft = b.bboxMm.x
  const bRight = b.bboxMm.x + b.bboxMm.width
  if (aRight < bLeft) return bLeft - aRight
  if (bRight < aLeft) return aLeft - bRight
  return 0
}

function verticalGap(a: ExtractedSubPath, b: ExtractedSubPath): number {
  if (!a.bboxMm || !b.bboxMm) return Number.POSITIVE_INFINITY
  const aTop = a.bboxMm.y
  const aBottom = a.bboxMm.y + a.bboxMm.height
  const bTop = b.bboxMm.y
  const bBottom = b.bboxMm.y + b.bboxMm.height
  if (aBottom < bTop) return bTop - aBottom
  if (bBottom < aTop) return aTop - bBottom
  return 0
}

function mergeBounds(subPaths: ExtractedSubPath[]): { x: number; y: number; width: number; height: number } | null {
  const valid = subPaths.map((s) => s.bboxMm).filter((v): v is { x: number; y: number; width: number; height: number } => !!v)
  if (!valid.length) {
    return null
  }

  const minX = Math.min(...valid.map((v) => v.x))
  const minY = Math.min(...valid.map((v) => v.y))
  const maxX = Math.max(...valid.map((v) => v.x + v.width))
  const maxY = Math.max(...valid.map((v) => v.y + v.height))

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  }
}

function shouldBeInnerContour(outer: ExtractedSubPath, inner: ExtractedSubPath): boolean {
  if (!outer.bboxMm || !inner.bboxMm) {
    return false
  }

  const areaRatio = bboxArea(inner.bboxMm) / Math.max(1e-6, bboxArea(outer.bboxMm))
  const widthRatio = inner.bboxMm.width / Math.max(1e-6, outer.bboxMm.width)
  const heightRatio = inner.bboxMm.height / Math.max(1e-6, outer.bboxMm.height)

  // Letter holes are visually small relative to the parent outer contour.
  if (areaRatio > 0.35) {
    return false
  }

  if (widthRatio > 0.55 && heightRatio > 0.55) {
    return false
  }

  return true
}

function centroidDistanceMm(
  a: ExtractedSubPath,
  b: ExtractedSubPath,
): number {
  if (!a.bboxMm || !b.bboxMm) {
    return Number.POSITIVE_INFINITY
  }
  const ax = a.bboxMm.x + a.bboxMm.width / 2
  const ay = a.bboxMm.y + a.bboxMm.height / 2
  const bx = b.bboxMm.x + b.bboxMm.width / 2
  const by = b.bboxMm.y + b.bboxMm.height / 2
  return Math.hypot(ax - bx, ay - by)
}

function pickFallbackHoleLetterParent(
  fragment: ExtractedSubPath,
  outerRoots: ExtractedSubPath[],
  innerCountByOuterId: Map<string, number>,
): ExtractedSubPath | null {
  if (!fragment.bboxMm) {
    return null
  }

  const candidates = outerRoots
    .filter((root) => root.id !== fragment.id)
    .filter((root) => shouldBeInnerContour(root, fragment))
    .filter((root) => (innerCountByOuterId.get(root.id) ?? 0) < 2)
    .map((root) => ({
      root,
      distance: centroidDistanceMm(fragment, root),
      innerCount: innerCountByOuterId.get(root.id) ?? 0,
    }))
    .sort((a, b) => a.innerCount - b.innerCount || a.distance - b.distance)

  return candidates[0]?.root ?? null
}

function pickHoleLetterParent(
  fragment: ExtractedSubPath,
  outerRoots: ExtractedSubPath[],
  mmPerVbu: number | null,
): ExtractedSubPath | null {
  if (!fragment.bboxMm) {
    return null
  }

  return (
    outerRoots
      .filter((root) => root.id !== fragment.id)
      .filter((root) => isSubPathHoleOfOuter(root, fragment, mmPerVbu))
      .sort((a, b) => bboxArea(a.bboxMm) - bboxArea(b.bboxMm))[0] ?? null
  )
}

function pickFragmentParent(fragment: ExtractedSubPath, roots: ExtractedSubPath[]): FragmentLink | null {
  if (!fragment.bboxMm || roots.length === 0) {
    return null
  }

  const sortedRootAreas = roots.map((root) => bboxArea(root.bboxMm)).sort((a, b) => a - b)
  const medianArea = sortedRootAreas[Math.floor(sortedRootAreas.length / 2)] ?? 0
  const fragmentArea = bboxArea(fragment.bboxMm)

  // Small detached contours are likely letter details and should attach to a nearby large outer contour.
  if (fragmentArea > medianArea * 0.35) {
    return null
  }

  const candidates = roots
    .map((root) => {
      const yOverlap = overlapRatioY(fragment, root)
      const xGap = horizontalGap(fragment, root)
      const yGap = verticalGap(fragment, root)
      const maxGap = Math.max(20, (root.bboxMm?.width ?? 0) * 0.45)
      const score = xGap + Math.max(0, 1 - yOverlap) * 100
      const xContained =
        !!fragment.bboxMm &&
        !!root.bboxMm &&
        fragment.bboxMm.x >= root.bboxMm.x &&
        fragment.bboxMm.x + fragment.bboxMm.width <= root.bboxMm.x + root.bboxMm.width
      return { root, yOverlap, xGap, yGap, maxGap, score, xContained }
    })
    .filter(
      (entry) =>
        (entry.yOverlap >= 0.45 && entry.xGap <= entry.maxGap) ||
        (entry.xContained && entry.xGap === 0 && entry.yGap <= Math.max(25, (entry.root.bboxMm?.height ?? 0) * 0.25)),
    )
    .sort((a, b) => a.score - b.score)

  const selected = candidates[0]
  if (!selected) {
    return null
  }

  const includeInGeometry = selected.yOverlap >= 0.35 && selected.xGap <= Math.max(10, (selected.root.bboxMm?.width ?? 0) * 0.08)

  return {
    parentId: selected.root.id,
    includeInGeometry,
    reason: includeInGeometry
      ? 'Fragment overlaps parent geometry and contributes to outer bounds.'
      : 'Fragment attached as semantic detail; excluded from geometry bounds.',
  }
}

function groupLayerSubPaths(
  layerSubPaths: ExtractedSubPath[],
  warnings: SvgPartWarning[],
  layerIndex: number,
  mmPerVbu: number | null,
): { groups: GroupedShape[]; assignments: SubPathAssignment[] } {
  const sorted = [...layerSubPaths].sort((a, b) => bboxArea(b.bboxMm) - bboxArea(a.bboxMm))
  const parentById = new Map<string, string | null>()
  const assignmentById = new Map<string, SubPathAssignment>()
  const fragmentLinks = new Map<string, FragmentLink>()

  for (let i = 0; i < sorted.length; i += 1) {
    const current = sorted[i]
    let parentCandidates: ExtractedSubPath[] = []

    for (let j = 0; j < i; j += 1) {
      const candidate = sorted[j]
      if (isSubPathContainedInOuter(candidate, current, mmPerVbu, 0.5)) {
        parentCandidates.push(candidate)
      }
    }

    if (parentCandidates.length === 0 && current.bboxMm) {
      for (let j = 0; j < i; j += 1) {
        const candidate = sorted[j]
        if (parentById.get(candidate.id) != null) {
          continue
        }
        if (isSubPathHoleOfOuter(candidate, current, mmPerVbu)) {
          parentCandidates.push(candidate)
        }
      }
    }

    if (parentCandidates.length === 0) {
      parentById.set(current.id, null)
      assignmentById.set(current.id, {
        subPathIndex: current.subPathIndex,
        layerName: current.layerName,
        closed: current.closed,
        bboxMm: current.bboxMm,
        assignedGroupId: null,
        classification: 'outer',
        reason: 'No containing subpath candidate.',
      })
      continue
    }

    parentCandidates = parentCandidates.sort((a, b) => bboxArea(a.bboxMm) - bboxArea(b.bboxMm))
    const selected = parentCandidates[0]
    const isInner = shouldBeInnerContour(selected, current)

    if (isInner) {
      parentById.set(current.id, selected.id)
      assignmentById.set(current.id, {
        subPathIndex: current.subPathIndex,
        layerName: current.layerName,
        closed: current.closed,
        bboxMm: current.bboxMm,
        assignedGroupId: selected.id,
        classification: 'inner',
        reason: contains(selected, current, 0.5)
          ? 'Contained with low area ratio relative to parent.'
          : 'Centroid inside parent fill with low area ratio (letter hole).',
      })
      warnings.push(partSplitWarning('SUBPATH_AS_INNER_CONTOUR', 'info', 'Subpath assigned as inner contour by containment.', current.id))
    } else {
      parentById.set(current.id, null)
      assignmentById.set(current.id, {
        subPathIndex: current.subPathIndex,
        layerName: current.layerName,
        closed: current.closed,
        bboxMm: current.bboxMm,
        assignedGroupId: null,
        classification: 'ambiguous',
        reason: 'Contained but contour ratios indicate non-hole geometry.',
      })
      warnings.push(
        partSplitWarning('SUBPATH_CONTAINMENT_AMBIGUOUS', 'warning', 'Contained subpath kept as separate outer contour due geometric ambiguity.', current.id),
      )
    }

    if (parentCandidates.length > 1) {
      warnings.push(
        partSplitWarning('SUBPATH_CONTAINMENT_AMBIGUOUS', 'warning', 'Subpath containment is ambiguous; nearest container chosen.', current.id, {
          candidateCount: parentCandidates.length,
        }),
      )
    }
  }

  const roots = sorted.filter((item) => parentById.get(item.id) == null)
  const rootSet = new Set(roots.map((root) => root.id))

  // Attach tiny detached roots as fragments to nearby large roots.
  for (const root of roots) {
    const currentAssignment = assignmentById.get(root.id)
    if (!currentAssignment || currentAssignment.classification === 'inner') {
      continue
    }

    const letterOuters = sorted.filter((item) => assignmentById.get(item.id)?.classification === 'outer')
    const holeLetterParent = pickHoleLetterParent(root, letterOuters, mmPerVbu)
    if (holeLetterParent) {
      parentById.set(root.id, holeLetterParent.id)
      rootSet.delete(root.id)
      assignmentById.set(root.id, {
        subPathIndex: root.subPathIndex,
        layerName: root.layerName,
        closed: root.closed,
        bboxMm: root.bboxMm,
        assignedGroupId: holeLetterParent.id,
        classification: 'inner',
        reason: 'Detached contour samples inside parent letter fill (hole).',
      })
      warnings.push(
        partSplitWarning('SUBPATH_AS_INNER_CONTOUR', 'info', 'Detached subpath promoted to inner hole by letter fill.', root.id),
      )
      continue
    }

    const eligibleParents = roots.filter((candidate) => candidate.id !== root.id)
    const holeParent = eligibleParents
      .filter(
        (candidate) =>
          assignmentById.get(candidate.id)?.classification === 'outer' &&
          root.bboxMm &&
          isSubPathHoleOfOuter(candidate, root, mmPerVbu),
      )
      .sort((a, b) => bboxArea(a.bboxMm) - bboxArea(b.bboxMm))[0]
    if (holeParent) {
      parentById.set(root.id, holeParent.id)
      rootSet.delete(root.id)
      assignmentById.set(root.id, {
        subPathIndex: root.subPathIndex,
        layerName: root.layerName,
        closed: root.closed,
        bboxMm: root.bboxMm,
        assignedGroupId: holeParent.id,
        classification: 'inner',
        reason: 'Detached contour centroid inside parent letter fill (hole).',
      })
      warnings.push(
        partSplitWarning('SUBPATH_AS_INNER_CONTOUR', 'info', 'Detached subpath promoted to inner hole by fill containment.', root.id),
      )
      continue
    }

    const link = pickFragmentParent(root, eligibleParents)
    if (!link) {
      continue
    }

    parentById.set(root.id, link.parentId)
    rootSet.delete(root.id)
    fragmentLinks.set(root.id, link)
    assignmentById.set(root.id, {
      ...currentAssignment,
      assignedGroupId: link.parentId,
      classification: 'fragment',
      reason: link.reason,
    })
  }

  const childrenById = new Map<string, ExtractedSubPath[]>()
  for (const subPath of sorted) {
    const parentId = parentById.get(subPath.id)
    if (!parentId) {
      continue
    }
    const outerRootId = resolveOuterRootId(subPath.id, parentById, assignmentById)
    const children = childrenById.get(outerRootId) ?? []
    children.push(subPath)
    childrenById.set(outerRootId, children)
  }

  const finalRoots = sorted.filter((item) => rootSet.has(item.id))
  const groups: GroupedShape[] = []

  for (let rootIndex = 0; rootIndex < finalRoots.length; rootIndex += 1) {
    const root = finalRoots[rootIndex]
    const children = childrenById.get(root.id) ?? []
    const innerChildren = children.filter((child) => assignmentById.get(child.id)?.classification === 'inner')
    const fragmentChildren = children.filter((child) => assignmentById.get(child.id)?.classification === 'fragment')
    const holeFragments = fragmentChildren.filter((child) => isSubPathHoleOfOuter(root, child, mmPerVbu))
    for (const holeFragment of holeFragments) {
      const assigned = assignmentById.get(holeFragment.id)
      if (assigned) {
        assignmentById.set(holeFragment.id, {
          ...assigned,
          classification: 'inner',
          reason: 'Fragment contour samples inside parent letter fill (hole).',
        })
      }
    }
    const promotedInnerChildren = [
      ...innerChildren,
      ...holeFragments.filter((child) => assignmentById.get(child.id)?.classification === 'inner'),
    ]
    const remainingFragments = fragmentChildren.filter(
      (child) => !holeFragments.some((hole) => hole.id === child.id),
    )
    const geometryFragmentChildren = remainingFragments.filter((child) => fragmentLinks.get(child.id)?.includeInGeometry === true)
    const groupSubPaths = [root, ...children]
    const geometrySubPaths = [root, ...geometryFragmentChildren]

    const outerPerimeterMm = geometrySubPaths.reduce<number | null>((acc, sub) => {
      if (sub.perimeterMm == null) return acc
      return (acc ?? 0) + sub.perimeterMm
    }, null)
    const totalContourPerimeterMm = groupSubPaths.reduce<number | null>((acc, sub) => {
      if (sub.perimeterMm == null) return acc
      return (acc ?? 0) + sub.perimeterMm
    }, null)

    const confidences = groupSubPaths.map((sub) => sub.confidence)
    const splitConfidence: ConfidenceLevel = confidences.some((value) => value === 'low')
      ? 'low'
      : confidences.some((value) => value === 'medium')
        ? 'medium'
        : 'high'

    const groupId = `split_${root.layerName?.toLowerCase().replace(/[^a-z0-9]+/g, '_') || 'layer'}_${layerIndex + 1}_${rootIndex + 1}`

    assignmentById.set(root.id, {
      ...(assignmentById.get(root.id) ?? {
        subPathIndex: root.subPathIndex,
        layerName: root.layerName,
        closed: root.closed,
        bboxMm: root.bboxMm,
        assignedGroupId: null,
        classification: 'outer' as const,
        reason: 'Root contour for group.',
      }),
      assignedGroupId: groupId,
      classification: 'outer',
      reason: fragmentChildren.length > 0 ? 'Outer contour with attached fragments.' : 'Outer contour root.',
    })

    for (const child of children) {
      const assigned = assignmentById.get(child.id)
      if (assigned) {
        assignmentById.set(child.id, {
          ...assigned,
          assignedGroupId: groupId,
        })
      }
    }

    groups.push({
      id: groupId,
      layerId: root.layerId,
      layerName: root.layerName,
      colors: [...new Set(groupSubPaths.flatMap((sub) => sub.colors))],
      subPaths: groupSubPaths,
      outerSubPaths: [root],
      innerSubPaths: promotedInnerChildren,
      fragmentSubPaths: remainingFragments,
      geometryFragmentSubPaths: geometryFragmentChildren,
      boundsMm: mergeBounds(geometrySubPaths),
      perimeterMm: outerPerimeterMm,
      outerPerimeterMm,
      totalContourPerimeterMm,
      splitConfidence,
      groupingReason: children.length > 0 ? 'bbox-containment' : 'single-subpath',
    })
  }

  return {
    groups,
    assignments: sorted
      .map((subPath) => assignmentById.get(subPath.id))
      .filter((value): value is SubPathAssignment => !!value)
      .sort((a, b) => a.subPathIndex - b.subPathIndex),
  }
}

function recomputeGroupMetrics(group: GroupedShape): void {
  const geometrySubPaths = [group.outerSubPaths[0], ...group.geometryFragmentSubPaths].filter(
    (value): value is ExtractedSubPath => !!value,
  )

  group.outerPerimeterMm = geometrySubPaths.reduce<number | null>((acc, sub) => {
    if (sub.perimeterMm == null) return acc
    return (acc ?? 0) + sub.perimeterMm
  }, null)
  group.totalContourPerimeterMm = group.subPaths.reduce<number | null>((acc, sub) => {
    if (sub.perimeterMm == null) return acc
    return (acc ?? 0) + sub.perimeterMm
  }, null)
  group.perimeterMm = group.outerPerimeterMm
  group.boundsMm = mergeBounds(geometrySubPaths)
}

function innerCountByOuter(groups: GroupedShape[]): Map<string, number> {
  const counts = new Map<string, number>()
  for (const group of groups) {
    for (const outer of group.outerSubPaths) {
      counts.set(outer.id, group.innerSubPaths.length)
    }
  }
  return counts
}

function applyFragmentHoleMove(
  fragment: ExtractedSubPath,
  fromGroup: GroupedShape,
  toGroup: GroupedShape,
  assignments: SubPathAssignment[],
  warnings: SvgPartWarning[],
  reason: string,
): void {
  fromGroup.fragmentSubPaths = fromGroup.fragmentSubPaths.filter((sp) => sp.id !== fragment.id)
  fromGroup.geometryFragmentSubPaths = fromGroup.geometryFragmentSubPaths.filter((sp) => sp.id !== fragment.id)
  fromGroup.subPaths = fromGroup.subPaths.filter((sp) => sp.id !== fragment.id)

  toGroup.innerSubPaths = [...toGroup.innerSubPaths, fragment]
  if (!toGroup.subPaths.some((sp) => sp.id === fragment.id)) {
    toGroup.subPaths = [...toGroup.subPaths, fragment]
  }

  recomputeGroupMetrics(fromGroup)
  recomputeGroupMetrics(toGroup)

  const assignment = assignments.find((row) => row.subPathIndex === fragment.subPathIndex)
  if (assignment) {
    assignment.classification = 'inner'
    assignment.assignedGroupId = toGroup.id
    assignment.reason = reason
  }

  warnings.push(
    partSplitWarning('SUBPATH_AS_INNER_CONTOUR', 'info', reason, fragment.id),
  )
}

function promoteGlobalFragmentHoles(
  groups: GroupedShape[],
  assignments: SubPathAssignment[],
  mmPerVbu: number | null,
  warnings: SvgPartWarning[],
): void {
  const outerRoots: { group: GroupedShape; outer: ExtractedSubPath }[] = []
  for (const group of groups) {
    for (const outer of group.outerSubPaths) {
      outerRoots.push({ group, outer })
    }
  }

  for (const group of groups) {
    for (const fragment of [...group.fragmentSubPaths]) {
      const innerCounts = innerCountByOuter(groups)
      const parentEntry = outerRoots
        .filter(({ outer }) => isSubPathHoleOfOuter(outer, fragment, mmPerVbu))
        .filter(({ outer }) => (innerCounts.get(outer.id) ?? 0) < 2)
        .sort((a, b) => bboxArea(a.outer.bboxMm) - bboxArea(b.outer.bboxMm))[0]

      if (parentEntry && parentEntry.group.id !== group.id) {
        applyFragmentHoleMove(
          fragment,
          group,
          parentEntry.group,
          assignments,
          warnings,
          'Cross-layer hole promoted by compound-path even-odd containment.',
        )
        continue
      }

      const fallbackOuter = pickFallbackHoleLetterParent(
        fragment,
        outerRoots.map((entry) => entry.outer),
        innerCounts,
      )
      if (!fallbackOuter) {
        continue
      }

      const targetGroup = outerRoots.find((entry) => entry.outer.id === fallbackOuter.id)?.group
      if (!targetGroup || targetGroup.id === group.id) {
        continue
      }

      applyFragmentHoleMove(
        fragment,
        group,
        targetGroup,
        assignments,
        warnings,
        'Detached contour assigned as letter hole by nearest-parent fallback.',
      )
    }
  }
}

export function groupSubPathsByShape(subPaths: ExtractedSubPath[], mmPerVbu: number | null = null): GroupingResult {
  const warnings: SvgPartWarning[] = []
  const groups: GroupedShape[] = []
  const assignments: SubPathAssignment[] = []
  const byLayer = new Map<string, ExtractedSubPath[]>()

  for (const subPath of subPaths) {
    const key = subPath.layerId ?? `layer:${subPath.layerName ?? 'unassigned'}`
    const current = byLayer.get(key) ?? []
    current.push(subPath)
    byLayer.set(key, current)
  }

  const layerEntries = [...byLayer.entries()]
  for (let i = 0; i < layerEntries.length; i += 1) {
    const [, layerSubPaths] = layerEntries[i]
    const groupedLayer = groupLayerSubPaths(layerSubPaths, warnings, i, mmPerVbu)
    groups.push(...groupedLayer.groups)
    assignments.push(...groupedLayer.assignments)
  }

  const confidence: ConfidenceLevel = groups.length === 0
    ? 'low'
    : groups.some((group) => group.splitConfidence === 'low')
      ? 'low'
      : groups.some((group) => group.splitConfidence === 'medium')
        ? 'medium'
        : 'high'

  promoteGlobalFragmentHoles(groups, assignments, mmPerVbu, warnings)

  return {
    groups,
    warnings,
    confidence,
    assignments,
  }
}
