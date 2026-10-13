# Fonts for PhotoCraft

Font installation is the user's action, never the agent's. When the
artwork needs a family that `type.fonts` does not report, ask the user
to install it (system package manager, or placing TTF/OTF files in
`~/.local/share/fonts/`), then restart PhotoCraft and verify — the
agent never runs package-manager, superuser, or download commands.

## How PhotoCraft finds fonts (the facts that matter)

- **No fontconfig.** The text engine does its own recursive directory
  scan: `/usr/share/fonts`, `/usr/local/share/fonts`, `/run/host/fonts`,
  `/run/host/user-fonts`, `$XDG_DATA_HOME/fonts`, `~/.local/share/fonts`,
  `~/.fonts` — extensions `ttf|otf|ttc|otc`, depth 8.
- **One scan, at startup.** Enumeration happens once when the engine is
  created; there is no rescan command, preference, or timer. **A running
  app instance never sees newly installed fonts — restart required.**
  Fontconfig cache refreshes (e.g. `fc-cache -f`) affect other apps
  only; PhotoCraft ignores them.
- **Family names for `type.create`/`type.setStyle`:** stored verbatim;
  lookup is case-insensitive but spacing must be exact ("NotoSansCJK"
  does not match "Noto Sans CJK JP"). Always verify the exact reported
  family via `type.fonts` before using it. Gotchas seen in the field:
  variable fonts may report with a trailing asterisk (`Jost*`), and a
  family's marketed name may differ from its file name (`Playfair`, not
  "Playfair Display").
- Unknown family names do NOT error at set time; text silently falls
  back at layout (Inter + stack). Catch mistakes with
  `type.resolveMissingFonts` / `type.fonts`, never by eye.
- `CRAFT_FONTS_DIR` build input only embeds the app's bundled Japanese
  fonts into the binary; unrelated to system-font discovery.

## Verified family set (families as PhotoCraft reports them)

- Modern sans: Inter, Inter Display, Inter Variable, Montserrat,
  Open Sans, Jost* (variable), Mona Sans, Fira Sans, IBM Plex, Overpass,
  Ubuntu, Nunito
- Classic serif: Cormorant / Cormorant Garamond / Cormorant SC /
  Cormorant Infant / Cormorant Unicase / Cormorant Upright, Crimson Pro,
  Gentium Plus, Libertinus Serif (+ Sans/Mono/Keyboard/Math/Display/
  Initials), Merriweather, Playfair (variable)
- Brush / script: Dancing Script, Pacifico, Caveat, Great Vibes,
  Homemade Apple
- Decorative / display: Bebas Neue, Oswald, Abril Fatface, Cinzel,
  Italiana

## Pairing guidance (book/reading-themed artwork)

Elegant serif display for titles (Cormorant, Playfair, Cinzel), clean
geometric sans for support text (Jost, Montserrat, Inter), one brush/
script accent max (Caveat for casual, Great Vibes for elegant calligraphy).
Poster-caps display (Bebas Neue, Oswald) for badges and labels.
