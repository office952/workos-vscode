import type { ReactNode } from "react";
import type {
  PreviewLayerSpec,
  VolumetricLetterPreviewConfig,
} from "@/lib/volumetricLetterPreview/volumetricLetterPreviewTypes";
import {
  PREVIEW_COLORS,
  buildLedModulePlacements,
  buildSpacerPlacements,
  computeExpandedViewBox,
  explodedLayerOffset,
  getIsometricDepthVector,
  getLayerBoundsWithOffset,
  getLetterBounds,
  resolveGeometrySource,
  usesEstimatedLedPlacement,
} from "@/lib/volumetricLetterPreview/volumetricLetterPreviewGeometry";
import { VolumetricLetterIsometricPreview } from "./VolumetricLetterIsometricPreview";

type LetterShapeProps = {
  config: VolumetricLetterPreviewConfig;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  vinylHatchId?: string;
};

function LetterShape({
  config,
  fill,
  stroke,
  strokeWidth = 1.5,
  opacity = 1,
  vinylHatchId,
}: LetterShapeProps) {
  const source = resolveGeometrySource(config);
  const bounds = getLetterBounds();
  const path = config.artwork.svgPath?.trim();
  const text = config.artwork.text?.trim();
  const resolvedFill = vinylHatchId ? `url(#${vinylHatchId})` : fill;

  if (source === "real" && path) {
    return (
      <path
        d={path}
        fill={resolvedFill ?? "none"}
        stroke={stroke}
        strokeWidth={strokeWidth}
        opacity={opacity}
        fillRule="evenodd"
        data-geometry-source="real"
      />
    );
  }

  if (source === "estimated" && text) {
    return (
      <text
        x={bounds.x + bounds.width / 2}
        y={bounds.y + bounds.height * 0.78}
        textAnchor="middle"
        fontSize={56}
        fontWeight={700}
        fill={resolvedFill ?? PREVIEW_COLORS.faceFill}
        stroke={stroke}
        strokeWidth={strokeWidth * 0.5}
        opacity={opacity}
        data-geometry-source="estimated"
      >
        {text.slice(0, 1)}
      </text>
    );
  }

  return (
    <rect
      x={bounds.x}
      y={bounds.y}
      width={bounds.width}
      height={bounds.height}
      rx={8}
      fill={resolvedFill ?? PREVIEW_COLORS.placeholderFill}
      stroke={stroke ?? PREVIEW_COLORS.placeholderStroke}
      strokeWidth={strokeWidth}
      strokeDasharray="6 4"
      opacity={opacity}
      data-geometry-source="placeholder"
    />
  );
}

function EstimatedBoundsGuide({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!usesEstimatedLedPlacement(config)) return null;

  const bounds = getLetterBounds();
  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-testid="estimated-led-bounds">
      <rect
        x={bounds.x}
        y={bounds.y}
        width={bounds.width}
        height={bounds.height}
        rx={6}
        fill="none"
        stroke="#64748B"
        strokeWidth={1}
        strokeDasharray="5 3"
        opacity={0.55}
      />
    </g>
  );
}

function IsometricReturnShell({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!config.returnSide.material && !config.returnSide.depthMm) return null;

  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const bx = bounds.x + offsetX;
  const by = bounds.y + offsetY;
  const bw = bounds.width;
  const bh = bounds.height;
  const { dx, dy } = iso;

  const rightSide = `${bx + bw},${by} ${bx + bw + dx},${by + dy} ${bx + bw + dx},${by + bh + dy} ${bx + bw},${by + bh}`;
  const bottom = `${bx},${by + bh} ${bx + bw},${by + bh} ${bx + bw + dx},${by + bh + dy} ${bx + dx * 0.22},${by + bh + dy * 0.92}`;

  return (
    <g data-layer="return" data-isometric-shell="true">
      <polygon
        points={bottom}
        fill={PREVIEW_COLORS.returnBottomFill}
        stroke={PREVIEW_COLORS.returnStroke}
        strokeWidth={1}
        opacity={0.88}
      />
      <polygon
        points={rightSide}
        fill={PREVIEW_COLORS.returnFill}
        stroke={PREVIEW_COLORS.returnStroke}
        strokeWidth={1}
        opacity={0.96}
      />
    </g>
  );
}

function IsometricBackingShape({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!config.backing.material && !config.backing.thicknessMm) return null;

  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const inset = 5;
  const bx = bounds.x - inset + offsetX;
  const by = bounds.y - inset + offsetY;
  const bw = bounds.width + inset * 2;
  const bh = bounds.height + inset * 2;
  const backDx = iso.dx * 1.12;
  const backDy = iso.dy * 1.12;

  return (
    <g data-layer="backing">
      <polygon
        points={`${bx + backDx},${by + backDy} ${bx + bw + backDx},${by + backDy} ${bx + bw + backDx},${by + bh + backDy} ${bx + backDx},${by + bh + backDy}`}
        fill={PREVIEW_COLORS.backingFill}
        stroke={PREVIEW_COLORS.backingStroke}
        strokeWidth={1}
        opacity={0.92}
      />
    </g>
  );
}

function LedModules({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!config.lighting.enabled) return null;

  const modules = buildLedModulePlacements(config);
  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="led">
      {modules.map((m, i) => (
        <rect
          key={i}
          x={m.x}
          y={m.y}
          width={m.w}
          height={m.h}
          rx={1.5}
          fill={PREVIEW_COLORS.ledFill}
          stroke={PREVIEW_COLORS.ledStroke}
          strokeWidth={0.75}
        />
      ))}
    </g>
  );
}

function WiringLines({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!config.lighting.enabled) return null;

  const modules = buildLedModulePlacements(config);
  if (modules.length < 2) return null;

  const points = modules.map((m) => ({ x: m.x + m.w / 2, y: m.y + m.h / 2 }));
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="wiring">
      <path
        d={d}
        fill="none"
        stroke={PREVIEW_COLORS.wiringStroke}
        strokeWidth={1}
        strokeDasharray="3 2"
        opacity={0.8}
      />
    </g>
  );
}

function SpacerMarkers({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  const spacers = buildSpacerPlacements(config);
  if (spacers.length === 0) return null;

  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="mounting">
      {spacers.map((s, i) => (
        <circle
          key={i}
          cx={s.cx}
          cy={s.cy}
          r={s.r}
          fill="none"
          stroke={PREVIEW_COLORS.spacerStroke}
          strokeWidth={1.5}
        />
      ))}
    </g>
  );
}

function SupportPanel({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  if (!config.mounting.supportPanel) return null;

  const bounds = getLetterBounds();
  const pad = 12;
  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="support">
      <rect
        x={bounds.x - pad}
        y={bounds.y - pad}
        width={bounds.width + pad * 2}
        height={bounds.height + pad * 2}
        rx={10}
        fill={PREVIEW_COLORS.supportFill}
        stroke={PREVIEW_COLORS.supportStroke}
        strokeWidth={1}
        strokeDasharray="4 3"
        opacity={0.75}
      />
    </g>
  );
}

function VinylOverlay({
  config,
  offsetX = 0,
  offsetY = 0,
  vinylHatchId,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
  vinylHatchId?: string;
}) {
  if (!config.face.hasVinyl) return null;

  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="vinyl" opacity={0.85}>
      <LetterShape
        config={config}
        fill={PREVIEW_COLORS.vinylFill}
        stroke={PREVIEW_COLORS.vinylStroke}
        strokeWidth={1.25}
        vinylHatchId={vinylHatchId}
      />
    </g>
  );
}

function FaceLayer({
  config,
  offsetX = 0,
  offsetY = 0,
}: {
  config: VolumetricLetterPreviewConfig;
  offsetX?: number;
  offsetY?: number;
}) {
  return (
    <g transform={`translate(${offsetX} ${offsetY})`} data-layer="face">
      <LetterShape
        config={config}
        fill={PREVIEW_COLORS.faceFill}
        stroke={PREVIEW_COLORS.faceStroke}
        strokeWidth={2}
      />
    </g>
  );
}

function LayerSlotFrame({
  offsetX,
  offsetY,
  layerId,
}: {
  offsetX: number;
  offsetY: number;
  layerId: string;
}) {
  const box = getLayerBoundsWithOffset(offsetX, offsetY);
  return (
    <rect
      x={box.x - 6}
      y={box.y - 6}
      width={box.width + 6}
      height={box.height + 6}
      rx={8}
      fill="none"
      stroke="#334155"
      strokeWidth={0.75}
      strokeDasharray="4 3"
      opacity={0.65}
      data-layer-frame={layerId}
    />
  );
}

function renderLayerContent(
  layerId: PreviewLayerSpec["id"],
  config: VolumetricLetterPreviewConfig,
  dx: number,
  dy: number,
  vinylHatchId?: string
): ReactNode {
  switch (layerId) {
    case "face":
      return <FaceLayer key={layerId} config={config} offsetX={dx} offsetY={dy} />;
    case "vinyl":
      return (
        <VinylOverlay
          key={layerId}
          config={config}
          offsetX={dx}
          offsetY={dy}
          vinylHatchId={vinylHatchId}
        />
      );
    case "return":
      return (
        <IsometricReturnShell key={layerId} config={config} offsetX={dx} offsetY={dy} />
      );
    case "backing":
      return (
        <IsometricBackingShape key={layerId} config={config} offsetX={dx} offsetY={dy} />
      );
    case "led":
      return (
        <>
          <EstimatedBoundsGuide key={`${layerId}-guide`} config={config} offsetX={dx} offsetY={dy} />
          <LedModules key={layerId} config={config} offsetX={dx} offsetY={dy} />
        </>
      );
    case "wiring":
      return <WiringLines key={layerId} config={config} offsetX={dx} offsetY={dy} />;
    case "mounting":
      return <SpacerMarkers key={layerId} config={config} offsetX={dx} offsetY={dy} />;
    case "support":
      return <SupportPanel key={layerId} config={config} offsetX={dx} offsetY={dy} />;
    default:
      return null;
  }
}

type PreviewSvgProps = {
  config: VolumetricLetterPreviewConfig;
  mode: "compact" | "expanded";
  showLabels: boolean;
  layers: PreviewLayerSpec[];
  testId: string;
};

export function VolumetricLetterPreviewSvg({
  config,
  mode,
  showLabels,
  layers,
  testId,
}: PreviewSvgProps) {
  const hatchId = `${testId}-vinyl-hatch`;

  if (mode === "compact") {
    return (
      <VolumetricLetterIsometricPreview
        config={config}
        showLabels={showLabels}
        testId={testId}
        vinylHatchId={hatchId}
      />
    );
  }

  const expandedBox = computeExpandedViewBox(layers.length);
  const vbW = expandedBox.width;
  const vbH = expandedBox.height;
  const contentOffsetX = 12;
  const contentOffsetY = 12;

  function renderExpandedStack(): ReactNode {
    const offsets = layers.map((_, idx) => explodedLayerOffset(idx));
    const anchors = offsets.map(({ dx, dy }) => getLayerBoundsWithOffset(dx, dy));

    return (
      <>
        {layers.map((layer, idx) => {
          const { dx, dy } = offsets[idx];
          return (
            <LayerSlotFrame
              key={`frame-${layer.id}`}
              offsetX={dx}
              offsetY={dy}
              layerId={layer.id}
            />
          );
        })}

        {offsets.slice(0, -1).map((from, idx) => {
          const to = offsets[idx + 1];
          const a = getLayerBoundsWithOffset(from.dx, from.dy);
          const b = getLayerBoundsWithOffset(to.dx, to.dy);
          return (
            <line
              key={`connector-${layers[idx].id}-${layers[idx + 1].id}`}
              x1={a.cx}
              y1={a.cy}
              x2={b.cx}
              y2={b.cy}
              stroke="#64748B"
              strokeWidth={0.85}
              strokeDasharray="3 2"
              opacity={0.75}
              data-testid={`${testId}-connector-${layers[idx].id}-${layers[idx + 1].id}`}
            />
          );
        })}

        {layers.map((layer, idx) => {
          const { dx, dy } = offsets[idx];
          return (
            <g key={`content-${layer.id}`}>
              {renderLayerContent(layer.id, config, dx, dy, hatchId)}
            </g>
          );
        })}

        {showLabels &&
          layers.map((layer, idx) => {
            const box = anchors[idx];
            const labelX = box.x + box.width + 14;
            const labelY = box.cy + 3;
            return (
              <g key={`callout-${layer.id}`} data-testid={`${testId}-layer-label-${layer.id}`}>
                <line
                  x1={box.x + box.width + 2}
                  y1={box.cy}
                  x2={labelX - 4}
                  y2={labelY - 2}
                  stroke="#64748B"
                  strokeWidth={0.75}
                />
                <text x={labelX} y={labelY} fontSize={9} fill="#CBD5E1" fontWeight={600}>
                  {layer.label}
                </text>
                {layer.detail && (
                  <text x={labelX} y={labelY + 10} fontSize={7.5} fill="#64748B">
                    {layer.detail.length > 28 ? `${layer.detail.slice(0, 28)}…` : layer.detail}
                  </text>
                )}
              </g>
            );
          })}
      </>
    );
  }

  return (
    <svg
      viewBox={`0 0 ${vbW} ${vbH}`}
      className="w-full h-auto min-h-[200px] max-h-[380px]"
      role="img"
      aria-label="Previzualizare construcție literă volumetrică"
      data-testid={`${testId}-svg`}
      data-preview-mode="expanded"
    >
      <defs>
        <pattern
          id={hatchId}
          patternUnits="userSpaceOnUse"
          width="5"
          height="5"
          patternTransform="rotate(45)"
        >
          <line x1="0" y1="0" x2="0" y2="5" stroke="#22D3EE" strokeWidth="1.5" opacity={0.55} />
        </pattern>
      </defs>

      <g transform={`translate(${contentOffsetX} ${contentOffsetY})`}>{renderExpandedStack()}</g>
    </svg>
  );
}
