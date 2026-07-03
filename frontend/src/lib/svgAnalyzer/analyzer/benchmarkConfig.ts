import type { AnalyzeOptions } from './analyzeSvg'

const BENCHMARKS: Record<string, AnalyzeOptions> = {
  'pbl.svg': {
    referencePerimeterMm: 13656.08,
    referenceSource: 'CorelDRAW Curve Properties',
    passThresholdPercent: 1,
  },
}

export function getBenchmarkOptionsForFile(fileName: string): AnalyzeOptions | undefined {
  const key = fileName.trim().toLowerCase()
  return BENCHMARKS[key]
}
