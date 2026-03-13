const MOJIBAKE_PATTERN = /(?:Ã.|Ø.|Ù.|ðŸ|â€|â€™|â€œ|â€\u009d|Â|[\u201a-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20AC\u2122\u0152\u0153\u0160\u0161\u0178\u017D\u017E])/;

const CP1252_REVERSE_MAP: Record<number, number> = {
  0x20ac: 0x80, // €
  0x201a: 0x82, // ‚
  0x0192: 0x83, // ƒ
  0x201e: 0x84, // „
  0x2026: 0x85, // …
  0x2020: 0x86, // †
  0x2021: 0x87, // ‡
  0x02c6: 0x88, // ˆ
  0x2030: 0x89, // ‰
  0x0160: 0x8a, // Š
  0x2039: 0x8b, // ‹
  0x0152: 0x8c, // Œ
  0x017d: 0x8e, // Ž
  0x2018: 0x91, // ‘
  0x2019: 0x92, // ’
  0x201c: 0x93, // “
  0x201d: 0x94, // ”
  0x2022: 0x95, // •
  0x2013: 0x96, // –
  0x2014: 0x97, // —
  0x02dc: 0x98, // ˜
  0x2122: 0x99, // ™
  0x0161: 0x9a, // š
  0x203a: 0x9b, // ›
  0x0153: 0x9c, // œ
  0x017e: 0x9e, // ž
  0x0178: 0x9f, // Ÿ
};

function decodeLatin1AsUtf8(value: string): string {
  const bytes = new Uint8Array(
    [...value].map((char) => {
      const code = char.codePointAt(0) ?? 0;
      if (code <= 0xff) return code;
      return CP1252_REVERSE_MAP[code] ?? 0x3f; // '?'
    })
  );
  return new TextDecoder('utf-8', { fatal: false }).decode(bytes);
}

export function repairMojibake(value: string): string {
  if (!value) return value;
  if (!MOJIBAKE_PATTERN.test(value)) return value;

  let repaired = value;
  for (let i = 0; i < 2; i += 1) {
    if (!MOJIBAKE_PATTERN.test(repaired)) break;
    const decoded = decodeLatin1AsUtf8(repaired);
    if (!decoded || decoded === repaired) break;
    repaired = decoded;
  }

  return repaired.replace(/\uFFFD/g, '');
}

export function bilingualLabel(english: string, arabic: string, language: 'en' | 'ar'): string {
  const en = repairMojibake(english || '');
  const ar = repairMojibake(arabic || '');

  if (!en) return ar;
  if (!ar) return en;

  return language === 'ar' ? `${ar} / ${en}` : `${en} / ${ar}`;
}
