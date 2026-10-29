/**
 * unicode-text-styles — the fancy-text styles behind https://fontvibe.ai/tools/fancy-font-generator
 * Code: MIT. Style data: CC BY 4.0 — attribution required, see README.
 */

/** One step of a style's pipeline. Exact semantics: SCHEMA.md in the repository. */
export type Step =
  | { op: 'lower' }
  | { op: 'upper' }
  | { op: 'reverse' }
  | { op: 'wrap'; prefix: string; suffix: string }
  | { op: 'join'; separator: string }
  | { op: 'append'; marks: string; only: 'all' | 'ascii_letters' }
  | { op: 'case'; mode: 'title' | 'camel' | 'snake' | 'kebab' | 'constant' | 'alternating' | 'inverse' }
  | { op: 'roman'; case: 'upper' | 'lower' }
  | {
      op: 'map';
      table: Record<string, string>;
      lookup?: 'exact' | 'lower' | 'exact_then_lower';
      join?: string;
      digraphs?: Record<string, string>;
    }
  | { op: 'number_runs'; table: Record<string, string>; whole: Record<string, string> }
  | { op: 'zalgo'; up: number; mid: number; down: number; pools: { up: string[]; mid: string[]; down: string[] } };

export type Locale = 'en' | 'es' | 'pt' | 'de' | 'ja' | 'zh';

export interface Style {
  key: string;
  label: string;
  category: string;
  category_labels: Record<Locale, string>;
  /** FontVibe's editorial rating, not a measurement. "low" = tagged "may not show on all devices" on fontvibe.ai. */
  fontvibe_compat: 'high' | 'medium' | 'low';
  /** Present on chained styles: the base styles applied, in order. */
  chain?: string[];
  steps: Step[];
  /** The step ops used, joined with "+", ignoring lower/upper. */
  kind: string;
  /** Unicode version that added the newest code point this style can emit. */
  unicode_age: string;
}

export interface StyledText {
  key: string;
  label: string;
  category: string;
  text: string;
}

/**
 * Style `text` with one style. `key` may chain styles with "+", e.g. "math_bold+strikethrough".
 * Characters the style has no glyph for pass through unchanged. Throws on an unknown key.
 */
export function transform(text: string, key: string): string;

/** Every style applied to `text`, in the order fontvibe.ai shows them. */
export function transformAll(text: string, opts?: { category?: string }): StyledText[];

/**
 * Best-effort reverse: styled characters → plain ASCII; the combining marks these styles add
 * are removed. Does not undo reversed order or wraps, and also folds real letters of other
 * scripts that a style borrows (Greek α → a).
 */
export function defancify(text: string): string;

export function getStyle(key: string): Style | null;

export const styles: Style[];
export const keys: string[];
export const categories: string[];
export const unicodeVersion: string;
/** https://fontvibe.ai/tools/fancy-font-generator */
export const homepage: string;

declare const _default: {
  transform: typeof transform;
  transformAll: typeof transformAll;
  defancify: typeof defancify;
  getStyle: typeof getStyle;
  styles: Style[];
  keys: string[];
  categories: string[];
  unicodeVersion: string;
  homepage: string;
};
export default _default;
