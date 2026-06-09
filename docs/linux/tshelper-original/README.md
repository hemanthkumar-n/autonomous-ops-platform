# tshelper Original Materials

This directory preserves the original Linux troubleshooting materials created
by Hemanth Kumar before their integration into Autonomous Ops Platform.

## Ownership and Provenance

- Author and operational subject-matter owner: Hemanth Kumar
- Original project: `tshelper`
- Original man-page version: `1.0.0`
- Archive date: June 10, 2026
- Purpose: preserve the author's Linux administration knowledge, command
  selection, troubleshooting order, configuration ideas, and documentation
  before AOP-specific development begins

These files were generated and refined from the author's Linux administration
experience. They are historical source material for AOP's Linux operational
intelligence domain.

## Preservation Rule

Do not modify the archived files in this directory.

Future implementations, corrections, and extensions belong in AOP source code
and the adjacent Linux design documents. When a new historical source is
discovered, add it as a new file and record its provenance rather than
replacing an existing artifact.

## Archived Files

| File | Original location | Purpose |
|---|---|---|
| `tshelper.sh` | `~/Downloads/tshelper.sh` | Original executable Bash implementation |
| `tshelper.conf` | `~/Downloads/tshelper.conf` | Original configuration design |
| `tshelper.1` | `~/Downloads/tshelper.1` | Original manual page |
| `pasted-text.txt` | Saved mobile/ChatGPT text attachment | Separately preserved script copy |

The two script copies are intentionally retained. They are not byte-identical,
so neither has been treated as disposable duplication.

## SHA-256 Manifest

```text
6fc681caa411ae727f466a2270952575ef18bdc0ac67e518a4799c4de12161be  tshelper.sh
fec768c82d903f8d7bf3c819ecd7e28e24e14ef4041fed2dba66fe5ac4cf9016  tshelper.conf
a89189e6780793724019128d8fe7aa472777b7d2906308406fe8a392e9e794ec  tshelper.1
9ed9b4d5fcaf209881c75c9e77976e042414c5cb1ef122379ef2282536d55d46  pasted-text.txt
```

Verify the archive from this directory with:

```bash
shasum -a 256 tshelper.sh tshelper.conf tshelper.1 pasted-text.txt
```

## Important Historical Observation

The configuration file and manual describe a more advanced intended product
than the archived Bash implementation currently provides. Examples include
configuration loading, connectivity and DNS tests, interface error analysis,
link speed, firewall inspection, configurable process output, and optional
service or log targeting.

This difference is valuable design history. AOP should preserve the intended
operational behavior rather than assuming the Bash implementation is the only
source of truth.
