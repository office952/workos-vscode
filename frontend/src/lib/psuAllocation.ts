const PSU_WATTS = [60, 100, 160, 200] as const;

export interface PsuAllocationResult {
  configuration: number[];
  totalCapacityWatts: number;
  status: "ok" | "impossible";
}

export function computeRequiredPsuWatts(
  totalLedWatts: number,
  reserveRatio: number,
): number {
  if (!Number.isFinite(totalLedWatts) || totalLedWatts <= 0) return 0;
  const safeReserve = Number.isFinite(reserveRatio) && reserveRatio > 0 ? reserveRatio : 0;
  return Math.round(totalLedWatts * (1 + safeReserve) * 100) / 100;
}

export function allocatePSUCombination(
  requiredWatts: number,
): PsuAllocationResult | null {
  if (!Number.isFinite(requiredWatts) || requiredWatts <= 0) {
    return {
      configuration: [],
      totalCapacityWatts: 0,
      status: "ok",
    };
  }

  const maxUnits = Math.max(1, Math.ceil(requiredWatts / PSU_WATTS[0]) + 1);
  let best: PsuAllocationResult | null = null;

  const search = (startIndex: number, remainingUnits: number, current: number[]) => {
    const total = current.reduce((sum, watts) => sum + watts, 0);
    if (total >= requiredWatts) {
      const candidate: PsuAllocationResult = {
        configuration: [...current].sort((left, right) => right - left),
        totalCapacityWatts: total,
        status: "ok",
      };
      if (
        !best ||
        candidate.totalCapacityWatts < best.totalCapacityWatts ||
        (candidate.totalCapacityWatts === best.totalCapacityWatts &&
          candidate.configuration.length < best.configuration.length)
      ) {
        best = candidate;
      }
      return;
    }

    if (remainingUnits <= 0) return;

    for (let index = startIndex; index < PSU_WATTS.length; index += 1) {
      current.push(PSU_WATTS[index]);
      search(index, remainingUnits - 1, current);
      current.pop();
    }
  };

  search(0, maxUnits, []);
  return best;
}