/**
 * Miryn visual system.
 *
 * The one import surface for Miryn's background-plane drawing language:
 * warm black ground, moss ink, hand-drawn contour lines, fragmented
 * conversation marks, a through-line and an ink grain.
 *
 *   import { ThoughtWall } from "@/components/visuals";
 *
 * Prefer a composition preset (`ThoughtWall preset="memory"`) over placing
 * individual assets. Reach for the atoms directly only when a section needs its
 * own one-off asymmetry that no preset covers.
 */

export {
  ContourLines,
  ConversationMarks,
  InkGrain,
  MirynMark,
  ThreadLine,
  type ContourVariant,
  type MarksVariant,
  type MarkState,
  type ThreadVariant,
} from "./svg";

export { ThoughtWall, ThoughtWallPanel, type SurfaceName } from "./composition";

export { FOREGROUND, GROUND, INK, PRESENCE, type Presence, type VisualTone } from "./tokens";
