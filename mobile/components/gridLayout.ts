/**
 * Rule of the app (session 7): choice buttons always go in a tidy grid of two equal columns.
 * A button marked `wide` takes the whole row (for example "Cualquiera" above the four seasons),
 * and when an odd number is left over, the last one takes the whole row too.
 * Pure function, tested with Node.
 */
export function wideFlags(options: { wide?: boolean }[]): boolean[] {
  const narrow = options.filter((o) => !o.wide).length;
  const lastNarrow = options.map((o) => !o.wide).lastIndexOf(true);
  return options.map((o, i) => !!o.wide || (narrow % 2 === 1 && i === lastNarrow));
}
