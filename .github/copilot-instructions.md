# Hercules - AI Coding Agent Instructions

Hercules is a **fast Git repository analysis engine** written in Go with Python visualization tools. It processes commit history through a **pipeline architecture** to extract metrics like code burndown, developer activity, churn, and code sentiment.

## Architecture Overview

### Core Design: Pipeline-Based Analysis (Pipeline DAG)
- **Entry point**: `cmd/hercules/root.go` - CLI that orchestrates the entire flow
- **Core pipeline**: `internal/core/pipeline.go` - Executes a Directed Acyclic Graph (DAG) of analysis tasks
- **Items processed sequentially** by `Consume(deps)` method for each commit
- **Results merged** across Git branches via `Fork()` and `Merge()` methods

**Key interfaces** (all in `internal/core/`):
- `PipelineItem` - Basic unit; implements: `Name()`, `Provides()`, `Requires()`, `Consume()`, `Fork()`, `Merge()`
- `LeafPipelineItem` - End-stage analyses that produce results; adds `Finalize()`, `Serialize()`
- `ResultMergeablePipelineItem` - Optional for combining analysis results across runs

### Component Layers

1. **Plumbing Layer** (`internal/plumbing/`): Low-level Git analysis
   - `diff.go` - Line-level diffs using go-git
   - `languages.go` - Language detection (via `src-d/enry`)
   - `identity/`, `uast/`, `imports/` - Advanced language features via BBLang UAST

2. **Leaves** (`leaves/`): High-level analyses producing final metrics
   - `burndown.go` - Line burndown with time-series granularity (main analysis)
   - `couples.go` - Co-changed file pairs
   - `devs.go` - Developer activity per file
   - `commits.go` - Commit statistics
   - `comment_sentiment.go` - Sentiment analysis via BiDiSentiment

3. **Registry & Configuration** (`internal/core/registry.go`):
   - Reflection-based auto-registration of `PipelineItem`s
   - Dynamic CLI flag mapping via `LeafPipelineItem.Flag()`
   - Dependency resolution via `Provides()` and `Requires()` metadata

## Build, Test & Run

### Build
```bash
make all
# Produces: hercules (or hercules.exe on Windows)
# Also generates: internal/pb/pb.pb.go, python/labours/pb_pb2.py, cmd/hercules/plugin_template_source.go
```

### Test
```bash
make test
# Runs: go test gopkg.in/src-d/hercules.v10
```

### Run
```bash
hercules --burndown --devs https://github.com/user/repo | labours -f pb -m burndown-project
# Output: YAML or Protocol Buffers format
```

## Critical Patterns & Conventions

### 1. Data Flow Between Pipeline Items
- Each item receives `deps map[string]interface{}` containing outputs from dependent items
- Return `map[string]interface{}` with keys matching `Provides()`
- Example: `Burndown` requires `"file"` key from `FileHistory`, returns `"burndown"` key
- All items receive `"commit"` and `"index"` automatically

### 2. Fork/Merge for Branching
- `Fork(n)` clones item state for parallel branches; returns n fresh clones
- `Merge(branches)` combines branches back; **must update ALL branch states** not just self
- Critical for correctness: GC branches must sync with default branch metrics

### 3. Protocol Buffers Serialization
- Results serialize to `.pb` (binary) or `.yaml` (text) via `Serialize()`
- Proto messages defined in `internal/pb/pb.proto`
- Python read via auto-generated `python/labours/pb_pb2.py`
- See: `leaves/burndown.go:Serialize()` for pattern

### 4. Configuration Options Pattern
```go
// In Configure() method:
facts[hercules.ConfigTickSize] = 24 * time.Hour  // Override tick granularity
facts[hercules.ConfigLogger] = customLogger       // Custom logging
```
- List available via `ListConfigurationOptions()` → CLI auto-generates `--flag-name`

### 5. Plumbing Item Composition
- Items like `Burndown` depend on `FileHistory` + `LineStats` from plumbing layer
- Plumbing items are **non-leaf** analysis helpers; they don't finalize
- Always call parent `Consume()` when extending plumbing items

## Development Workflows

### Adding a New Analysis
1. Create `leaves/my_analysis.go` implementing `LeafPipelineItem`
2. Define proto in `internal/pb/pb.proto`
3. Implement lifecycle: `Configure()` → `Initialize()` → `Consume()` → `Finalize()` → `Serialize()`
4. Register via `init()` in leaves package:
   ```go
   func init() {
       hercules.Registry.Register(&MyAnalysis{})
   }
   ```
5. CLI automatically gets `--my-analysis` flag

### Custom Plugins
- Use `hercules generate-plugin -n MyPlugin -o ./my_plugin`
- Generates: `.go` source, `.proto` definition, `Makefile`
- Compile to `.so`/`.dll` and load via `--plugin my_plugin.so`
- See: `contrib/_plugin_example/` for reference

### Testing
- Each analysis has `*_test.go` file
- Use `dummies.go` for mock commits/trees
- Pattern: `repository := &test.Repository{...}; item.Initialize(repo); item.Consume(deps)`

## Integration Points & Dependencies

- **go-git** (`gopkg.in/src-d/go-git.v4`): Repository access, tree/blob walking
- **BBLang** (`gopkg.in/bblfsh/client-go.v3`): UAST syntax trees (optional via `--feature=uast`)
- **Protocol Buffers** (`gogo/protobuf`): Serialization format
- **Cobra/pflag**: CLI framework for dynamic flag binding
- **Python labours** (`python/setup.py`): Visualization tool; reads `.pb` files

## Key Files to Reference

| Purpose | File |
|---------|------|
| Public API exports | [../Hercules/core.go](../Hercules/core.go) |
| Pipeline execution | [../Hercules/internal/core/pipeline.go](../Hercules/internal/core/pipeline.go) |
| Registry & dependency resolution | [../Hercules/internal/core/registry.go](../Hercules/internal/core/registry.go) |
| Proto message schema | [../Hercules/internal/pb/pb.proto](../Hercules/internal/pb/pb.proto) |
| Main CLI entry | [../Hercules/cmd/hercules/root.go](../Hercules/cmd/hercules/root.go) |
| Burndown example (most complex) | [../Hercules/leaves/burndown.go](../Hercules/leaves/burndown.go) |
| Plumbing example | [../Hercules/internal/plumbing/diff.go](../Hercules/internal/plumbing/diff.go) |
| Plugin system | [../Hercules/cmd/hercules/generate_plugin.go](../Hercules/cmd/hercules/generate_plugin.go) |

## Project Conventions

- **Naming**: Snake case for files (`my_analysis.go`), CamelCase for types (`MyAnalysis`)
- **Flag convention**: `--kebab-case` CLI flags derived from type names via camelcase split
- **Memory management**: Use hibernatable RBTree for large-scale data (`internal/rbtree/`)
- **Git branching**: Code handles detached heads, octopus merges, and full DAG topology
- **Determinism**: Set random seeds explicitly for reproducible plugin generation
