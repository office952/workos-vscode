import type { VolumetricLetterPreviewConfig } from "@/lib/volumetricLetterPreview/volumetricLetterPreviewTypes";
import {
  buildSpacerPlacements,
  getIsometricDepthVector,
  getLetterBounds,
  resolveGeometrySource,
  usesEstimatedLedPlacement,
} from "@/lib/volumetricLetterPreview/volumetricLetterPreviewGeometry";
import {
  ISOMETRIC_VISUAL,
  buildIsometricCallouts,
  computeIsometricCompactViewBox,
  getBackingIsometricQuad,
  getCompactSplitPlaneX,
  getIsometricShellPolygons,
  getLedModuleRenderData,
  resolveIsometricPalette,
  resolveLetterSilhouettePath,
  usesPlaceholderSilhouette,
} from "@/lib/volumetricLetterPreview/volumetricLetterIsometric";

type Props = {
  config: VolumetricLetterPreviewConfig;
  showLabels: boolean;
  testId: string;
  vinylHatchId: string;
};

function SilhouetteShape({
  config,
  fill,
  stroke,
  strokeWidth = 0,
  opacity = 1,
  fillRule,
  vinylHatchId,
  className,
}: {
  config: VolumetricLetterPreviewConfig;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  fillRule?: "evenodd" | "nonzero";
  vinylHatchId?: string;
  className?: string;
}) {
  const path = resolveLetterSilhouettePath(config);
  const bounds = getLetterBounds();
  const source = resolveGeometrySource(config);
  const resolvedFill = vinylHatchId ? `url(#${vinylHatchId})` : fill;

  if (path) {
    return (
      <path
        d={path}
        fill={resolvedFill ?? "none"}
        stroke={stroke}
        strokeWidth={strokeWidth}
        opacity={opacity}
        fillRule={fillRule ?? "evenodd"}
        data-geometry-source={source}
        className={className}
      />
    );
  }

  if (source === "estimated" && config.artwork.text?.trim()) {
    return (
      <text
        x={bounds.x + bounds.width / 2}
        y={bounds.y + bounds.height * 0.78}
        textAnchor="middle"
        fontSize={58}
        fontWeight={800}
        fill={resolvedFill ?? fill}
        stroke={stroke}
        strokeWidth={strokeWidth * 0.4}
        opacity={opacity}
        data-geometry-source="estimated"
        className={className}
      >
        {config.artwork.text.slice(0, 1)}
      </text>
    );
  }

  return (
    <rect
      x={bounds.x}
      y={bounds.y}
      width={bounds.width}
      height={bounds.height}
      rx={10}
      fill={resolvedFill ?? "#1E293B"}
      stroke={stroke ?? "#64748B"}
      strokeWidth={strokeWidth || 1.5}
      strokeDasharray="6 4"
      opacity={opacity}
      data-geometry-source="placeholder"
      className={className}
    />
  );
}

function IsometricCallouts({
  config,
  showLabels,
  testId,
  splitX,
}: {
  config: VolumetricLetterPreviewConfig;
  showLabels: boolean;
  testId: string;
  splitX: number;
}) {
  if (!showLabels) return null;

  const callouts = buildIsometricCallouts(config, splitX);

  return (
    <g data-testid={`${testId}-compact-callouts`} data-split-cutaway-labels="true">
      {callouts.map((c) => (
        <g key={c.id} data-testid={`${testId}-compact-callout-${c.id}`}>
          <line
            x1={c.anchorX}
            y1={c.anchorY}
            x2={c.labelX + (c.side === "exterior" ? 18 : 14)}
            y2={c.labelY + 4}
            stroke="#64748B"
            strokeWidth={0.75}
            opacity={0.85}
          />
          <circle cx={c.anchorX} cy={c.anchorY} r={2.2} fill="#475569" stroke="#94A3B8" strokeWidth={0.5} />
          <text
            x={c.labelX + (c.side === "exterior" ? 22 : 18)}
            y={c.labelY + 7}
            fontSize={7.5}
            fill="#334155"
            fontWeight={600}
          >
            {c.label}
          </text>
        </g>
      ))}
    </g>
  );
}

/**
 * Compact channel-letter preview — isometric 3D cutaway (interior left / exterior right).
 */
export function VolumetricLetterIsometricPreview({
  config,
  showLabels,
  testId,
  vinylHatchId,
}: Props) {
  const palette = resolveIsometricPalette(config);
  const viewBox = computeIsometricCompactViewBox(config);
  const splitX = getCompactSplitPlaneX();
  const shell = getIsometricShellPolygons(config);
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const bounds = getLetterBounds();
  const backingQuad = getBackingIsometricQuad(config);
  const ledModules = getLedModuleRenderData(config);
  const spacers = buildSpacerPlacements(config);
  const hasReturn = Boolean(config.returnSide.material || config.returnSide.depthMm);
  const hasBacking = Boolean(config.backing.material || config.backing.thicknessMm);
  const hasFace = Boolean(
    config.face.material || config.artwork.text || config.artwork.svgPath
  );
  const placeholder = usesPlaceholderSilhouette(config);

  const interiorClipId = `${testId}-iso-clip-interior`;
  const exteriorClipId = `${testId}-iso-clip-exterior`;
  const faceGradId = `${testId}-iso-face-grad`;
  const returnGradId = `${testId}-iso-return-grad`;
  const backingGradId = `${testId}-iso-backing-grad`;
  const canvasGradId = `${testId}-iso-canvas-grad`;

  const shadowCx = bounds.x + bounds.width / 2 + iso.dx * 0.35;
  const shadowCy = bounds.y + bounds.height + iso.dy + 4;

  return (
    <svg
      viewBox={`0 0 ${viewBox.width} ${viewBox.height}`}
      className="w-full h-auto max-h-[280px]"
      role="img"
      aria-label="Previzualizare 3D literă volumetrică"
      data-testid={`${testId}-svg`}
      data-preview-mode="compact"
      data-isometric-preview="true"
    >
      <defs>
        <linearGradient id={canvasGradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={palette.canvasTop} />
          <stop offset="100%" stopColor={palette.canvasBottom} />
        </linearGradient>
        <linearGradient id={faceGradId} x1="0" y1="0" x2="0.2" y2="1">
          <stop offset="0%" stopColor={palette.faceTop} />
          <stop offset="100%" stopColor={palette.faceBottom} />
        </linearGradient>
        <linearGradient id={returnGradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={palette.returnExterior} />
          <stop offset="100%" stopColor={palette.returnExteriorDark} />
        </linearGradient>
        <linearGradient id={backingGradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={palette.backingTop} />
          <stop offset="100%" stopColor={palette.backingBottom} />
        </linearGradient>
        <pattern
          id={vinylHatchId}
          patternUnits="userSpaceOnUse"
          width="5"
          height="5"
          patternTransform="rotate(45)"
        >
          <line x1="0" y1="0" x2="0" y2="5" stroke="#FDBA74" strokeWidth="1.2" opacity={0.45} />
        </pattern>
        <clipPath id={interiorClipId}>
          <rect x={0} y={0} width={splitX + 3} height={viewBox.height} />
        </clipPath>
        <clipPath id={exteriorClipId}>
          <rect x={splitX - 2} y={0} width={viewBox.width - splitX + 4} height={viewBox.height} />
        </clipPath>
        <filter id={`${testId}-iso-shadow`} x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor={palette.shadow} />
        </filter>
      </defs>

      <rect x={0} y={0} width={viewBox.width} height={viewBox.height} fill={`url(#${canvasGradId})`} />

      <g data-split-cutaway="true" filter={`url(#${testId}-iso-shadow)`}>
        {/* Ground shadow */}
        <ellipse
          cx={shadowCx}
          cy={shadowCy}
          rx={bounds.width * 0.42}
          ry={7}
          fill={palette.shadow}
          opacity={0.55}
        />

        {/* Interior cutaway — left half */}
        <g clipPath={`url(#${interiorClipId})`} data-split-region="interior">
          {hasReturn && (
            <polygon
              points={`${splitX},${shell.bounds.by} ${splitX},${shell.bounds.by + shell.bounds.bh} ${splitX - ISOMETRIC_VISUAL.returnWallThickness},${shell.bounds.by + shell.bounds.bh} ${splitX - ISOMETRIC_VISUAL.returnWallThickness},${shell.bounds.by}`}
              fill={palette.returnInterior}
              stroke={palette.returnExteriorDark}
              strokeWidth={0.6}
              data-layer="return-cutaway"
            />
          )}

          <SilhouetteShape
            config={config}
            fill={palette.cavity}
            opacity={0.92}
            fillRule="evenodd"
          />

          {hasBacking && (
            <g data-layer="backing">
              <polygon
                points={backingQuad}
                fill={`url(#${backingGradId})`}
                stroke="#94A3B8"
                strokeWidth={0.85}
              />
            </g>
          )}

          {config.lighting.enabled &&
            ledModules.map((m, i) => (
              <g key={i} data-layer="led">
                <rect
                  x={m.x}
                  y={m.y}
                  width={m.w}
                  height={m.h}
                  rx={1.5}
                  fill={palette.ledBody}
                  stroke="#CBD5E1"
                  strokeWidth={0.6}
                />
                {m.dots.map((d, j) => (
                  <circle key={j} cx={d.cx} cy={d.cy} r={1.1} fill={palette.ledDot} />
                ))}
              </g>
            ))}

          {config.lighting.enabled && (
            <>
              <circle
                cx={bounds.x + bounds.width * 0.2}
                cy={bounds.y + bounds.height * 0.76}
                r={2.8}
                fill="#E2E8F0"
                stroke="#64748B"
                strokeWidth={0.75}
                data-schematic="wiring-hole"
              />
              <circle
                cx={bounds.x + bounds.width * 0.12}
                cy={bounds.y + bounds.height + iso.dy * 0.15}
                r={1.8}
                fill="none"
                stroke="#64748B"
                strokeWidth={0.65}
                data-schematic="drain-hole"
              />
              {ledModules.length >= 2 && (
                <path
                  d={ledModules
                    .map((m, i) => `${i === 0 ? "M" : "L"} ${m.x + m.w / 2} ${m.y + m.h / 2}`)
                    .join(" ")}
                  fill="none"
                  stroke={palette.wiring}
                  strokeWidth={0.85}
                  strokeDasharray="2 1.5"
                  opacity={0.9}
                  data-layer="wiring"
                />
              )}
            </>
          )}

          {usesEstimatedLedPlacement(config) && (
            <rect
              x={bounds.x}
              y={bounds.y}
              width={bounds.width}
              height={bounds.height}
              rx={6}
              fill="none"
              stroke="#64748B"
              strokeWidth={0.75}
              strokeDasharray="4 3"
              opacity={0.4}
              data-testid="estimated-led-bounds"
            />
          )}
        </g>

        {/* Exterior finish — right half */}
        <g clipPath={`url(#${exteriorClipId})`} data-split-region="exterior">
          {hasReturn && (
            <g data-layer="return" data-isometric-shell="true">
              <polygon
                points={shell.bottom}
                fill={palette.returnBottom}
                stroke={palette.returnExteriorDark}
                strokeWidth={0.85}
              />
              <polygon
                points={shell.rightSide}
                fill={`url(#${returnGradId})`}
                stroke={palette.returnExteriorDark}
                strokeWidth={0.85}
              />
            </g>
          )}

          {config.mounting.supportPanel && (
            <rect
              x={bounds.x - 12}
              y={bounds.y - 12}
              width={bounds.width + 24}
              height={bounds.height + 24}
              rx={10}
              fill="#1E293B"
              stroke="#0F172A"
              strokeWidth={0.75}
              strokeDasharray="4 3"
              opacity={0.35}
              data-layer="support"
            />
          )}

          {spacers.map((s, i) => (
            <circle
              key={i}
              cx={s.cx}
              cy={s.cy}
              r={s.r}
              fill="none"
              stroke="#15803D"
              strokeWidth={1.2}
              data-layer="mounting"
            />
          ))}

          {hasFace && config.face.hasVinyl && (
            <SilhouetteShape
              config={config}
              fill="rgba(251, 146, 60, 0.35)"
              vinylHatchId={vinylHatchId}
              fillRule="evenodd"
            />
          )}

          {hasFace && (
            <g data-layer="face">
              <SilhouetteShape
                config={config}
                fill={`url(#${faceGradId})`}
                stroke={palette.trim}
                strokeWidth={ISOMETRIC_VISUAL.trimWidth}
                fillRule="evenodd"
              />
              {!placeholder && (
                <SilhouetteShape
                  config={config}
                  fill="none"
                  stroke="rgba(255,255,255,0.22)"
                  strokeWidth={0.75}
                  fillRule="evenodd"
                />
              )}
            </g>
          )}
        </g>

        {/* Split plane */}
        <line
          x1={splitX}
          y1={bounds.y - 4}
          x2={splitX}
          y2={bounds.y + bounds.height + iso.dy + 8}
          stroke="#94A3B8"
          strokeWidth={0.9}
          strokeDasharray="5 3"
          opacity={0.7}
          data-split-plane="true"
        />
      </g>

      <IsometricCallouts
        config={config}
        showLabels={showLabels}
        testId={testId}
        splitX={splitX}
      />
    </svg>
  );
}
