# skills

My agent skills, published through GitHub and [skills.sh](https://skills.sh).
One repo, one `skills/` directory, one version line per skill.

## Skills

### photocraft-automation

Agent skill for [PhotoCraft](https://github.com/storytold/photocraft) — drive
the image editor end-to-end, and develop it: triage bugs, verify fixes, file
upstream issues. Includes the call-logging corpus, the wedge diagnostic
doctrine, the visual loop, a cross-project sqlite issue tracker, and a
machine-local runtime home shared by every install.

```sh
npx skills add ahmedhosnypro/skills --skill photocraft-automation
```

### mermaid-diagrams

Agent skill for authoring and validating Mermaid diagrams — every supported
diagram type, from flowcharts to the full C4 architecture family, with a
bundled offline structural validator (runs under [Bun](https://bun.sh);
falls back to `mmdc` or the [Mermaid Live Editor](https://mermaid.live) when
Bun is unavailable).

```sh
npx skills add ahmedhosnypro/skills --skill mermaid-diagrams
```

## Install

Install one skill by name with the
[skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ahmedhosnypro/skills --skill <skill-name>
```

Preview what a skill contains without installing:

```sh
npx skills add ahmedhosnypro/skills --list
```

The skills provide instructions and helper scripts only; they do not install
PhotoCraft, Bun, or any renderer, and they never manage tokens.

## Layout

```text
skills/
  photocraft-automation/   SKILL.md, config.example.json, assets/,
                           scripts/issues_db.py, utils/
  mermaid-diagrams/        SKILL.md, scripts/ (validator + tests),
                           assets/, references/
```

Maintained by [@ahmedhosnypro](https://github.com/ahmedhosnypro).
MIT licensed — see [LICENSE](LICENSE).
