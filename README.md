# Snowflake for Flow Steward

Flow Steward extension `flowsteward.data-connector-mcp-toolbox-snowflake`, version **1.3.7**.

Bring Snowflake data into Flow Steward through saved, parameterized Dataset queries. The connector tests connections, discovers typed schemas, validates selected tables and columns, previews results, executes saved SQL and infers output schemas. Reads use the read-only query path and return at most 100 rows and 480 KiB of inline output. Use these results to supply a workflow with the warehouse records needed for a decision or follow-up action.

Workflow writes are exposed separately through execute_write, which accepts one INSERT, UPDATE or DELETE with named parameters, a values object and an optional parameter schema. For example, query a review queue, route a record for approval, then update its status or insert an audit outcome. Parameter values stay separate from the SQL text, allowing the same step to process different records.

Connections explicitly select the Snowflake account, database, schema, warehouse, user and role, with the password stored as a secret. Choose a role with the permissions your reads and writes require. Dataset queries stay read-only; this extension does not expose triggers, warehouse administration, schema-changing statements or multi-statement scripts. Use saved queries and explicit write steps together to turn warehouse findings into review tasks, notifications and recorded outcomes.

Create a project connection with account identifier, user, database, schema, warehouse and role, and store the user password in connection secrets. Warehouse and role are required explicitly; select a role with suitable privileges for the intended queries and workflow writes.

## Set up a Snowflake connection

Create a project connection using these settings:

| Setting | Meaning |
| --- | --- |
| `account` | Snowflake account identifier. Required. |
| `user` | Snowflake user. Required. |
| `database` | Snowflake database. Required. |
| `schema` | Snowflake schema (required by the pinned source). Required. |
| `warehouse` | Explicit Snowflake compute warehouse. Required. |
| `role` | Explicit least-privilege Snowflake role. Required. |

Store the Snowflake user password in the connection secrets. The pinned source requires a nonempty password; datasets may alternatively use their password environment secret. Resolved dataset secret environment values are forwarded to the native process; direct environment overrides retain their established precedence. Dataset advanced environment exposes only the named SNOWFLAKE_ source variables; password overrides remain in secrets. Writer connections use the explicit settings above.

Preserve the account identifier, schema, warehouse and role required by your deployment. Both warehouse and role must be supplied explicitly: native prebuilt interpolation resolves these variables before source-level defaults, so this extension does not rely on hidden defaults. Choose a least-privilege role. This pinned interface uses user/password authentication rather than a generic cloud project, region or instance form.

## Read datasets and write from workflows

Datasets support connection testing, typed schema introspection, saved SQL, visual-query resource scope validation, bounded previews and execution. Read queries use the native read-only path and are capped at 100 rows and 480 KiB inline output. No trigger surface is exposed.

`execute_write` runs one INSERT, UPDATE or DELETE on the selected Snowflake project connection. Provide `connection_ref`, SQL with named `:parameters`, a `params` object and optional JSON `param_schema`. Values stay separate from SQL and use native driver binding. The server must support the supplied SQL syntax.

The host resolves matching project configuration and secrets, account/project scope, execution context and a durable external-effect claim. Test mode suppresses writes before a driver starts. Writes execute once; uncertain dispatched failures return `retryable: false` and require checking the database before a manual retry. Workflow writes do not make dataset queries writable.

The bounded SQL subset refuses raw dollar characters and backslashes in read SQL; write SQL also refuses raw dollar characters. Put those values in bound parameters. A top-level read LIMIT accepts one integer literal with an optional integer OFFSET. The existing SQL safety guards and database-specific settings validation remain in force.

## Upgrade compatibility

The visible name is Snowflake. The legacy extension ID `flowsteward.data-connector-mcp-toolbox-snowflake`, project connection type `toolbox_sql_writer`, dataset connector IDs and action IDs remain unchanged so existing installations and workflows can upgrade. These are internal compatibility identifiers, not a second database selector.

## Technical implementation and packaging

Google MCP Toolbox is implementation tooling, pinned to tag `v1.16.0`, commit `06ea49d9a487a72c22419b5a8d5c22c11f0d7485`. Its fixed native build registers only this repository's Snowflake interfaces. Installation and runtime download no drivers. The local security module patch pins `github.com/snowflakedb/gosnowflake/v2` to `v2.4.0`, fixing diagnostic credential leakage (CVE-2026-86597). The original driver-bound SQL patch remains applied. Actual linked Go module versions are recorded in `toolbox-provenance.json`.

To package the existing verified binaries:

```sh
python3 scripts/package_extension.py --runtime-target linux-amd64
python3 scripts/package_extension.py --runtime-target linux-arm64
```

`scripts/build_toolbox.sh` is the optional pinned implementation rebuild (Docker, Python 3 and host Go for static build-info inspection are required); it cannot select another database. `toolbox-provenance.json`, `THIRD_PARTY.yml` and root `SHA256SUMS` describe the native payloads. Each installer ZIP contains exactly one executable for its target and target/native metadata. The byte-exact Apache-2.0 license is in `LICENSE`; implementation notices are in `NOTICE`.

## Verification limits

Manifest isolation checks cover friendly names, database-specific fields, credential separation and the exact shipped SQL profiles. Contract tests cover scope/ref checks, parameter separation, test-mode suppression, output bounds and unknown write outcomes. No live Snowflake credentials were supplied; compile and contract evidence does not establish a successful authenticated database connection.

Native payloads are rebuilt with pinned Go 1.27.4 and the reviewed module security baseline. Per-target toolchain, linked modules, size and SHA-256 are recorded in `toolbox-provenance.json`; static packaged checks reject stale native dependencies.

The native build freezes the previously approved prebuilt YAML from Toolbox v1.3.0
using `0003-approved-prebuilt-profiles.patch`; the implementation source and recorded
version remain Toolbox v1.16.0. Unused source, tool, prompt and resource registrations
are removed. Managed stdio launches use `--disable-version-check`.

The Snowflake DSN explicitly retains OCSP revocation checking in its prior
fail-open mode; the existing `SF_DISABLE_OCSP_CHECKS=true` environment opt-out
retains its upstream behavior. This prevents the newer driver default from
silently disabling checking for ordinary connection settings.

The pinned Go 1.27.3 image supplies only the bootstrap operating environment.
Before any Go command, the build installs the checksum-verified official Go
1.27.4 SDK recorded in `scripts/go-toolchain-sources.json`; provenance records
the installer, selected SDK, and actual compiler embedded in each payload.

## Automated releases

CI runs on pull requests and pushes to `main`. Official releases run through the
pinned shared GitHub Actions workflow using `.github/release-config.json` to test,
package both Linux runtime targets, and publish the release assets automatically.
Manual ZIP uploads are not part of the release process.

After merging the version **1.3.7** update into `main`, create and push its tag:

```sh
git switch main
git pull --ff-only
git tag -a v1.3.7 -m "Release v1.3.7"
git push origin v1.3.7
```

To rerun the workflow for an existing tag without moving it:

```sh
gh workflow run release.yml --ref main -f tag=v1.3.7
```

The manifest remains the source for release identity and catalog descriptions.
The shared workflow installs the verified first-party SDK wheel before test
dependencies. Where native payloads are absent from source, the recipe restores
only the listed missing files from checksum-pinned published archives; the source
packager still verifies their provenance before packaging.
