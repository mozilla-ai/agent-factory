# Testing Guide

We have a variety of tests implemented as a support to Agent Factory development.
This guide describes them in detail and explains how to run them locally.
The following sections are:

- **Directory Structure**, explaining what is available and where.
- **Running Tests**, describing how to run each different type of test.
- **Tests in CI**, showing how tests are run on GitHub CI.

## Directory Structure

The `tests` folder is organized in the following sub-directories:

- **`unit`**: unit tests for core functionality including e.g. a2a client/server,
agent generation and validation, io and storage.
- **`tools`**: tests for MCP server discovery and our built-in MCP tools.
- **`generation`**: tests for end-to-end single-turn agent generation using real prompts. We have a few use cases detailed in the `use_cases.yaml` file, and the purpose of these tests is to verify that the process of building these agents completes with no errors.
- **`generated_artifacts`**: these tests validate the agents generated in the previous step, making sure they are consistent with their input prompts and that they work as expected. The tests both verify the generated agents and their generation traces statically, and dynamically execute the agents while mocking some external APIs and paid services.
- **`generated_agent_evaluation`**: our generated agents can also come with LLM-as-judge evaluation. The purpose of these tests is to validate the evaluation tool itself.
- **`artifacts`**: these are not tests, but the actual agent artifacts generated as a part of the `generation` tests, which are then tested in `generated_artifacts`.
- **`utils`** - Shared testing utilities and helpers. At the present time, the package contains just a single `run_until_success_threshold_async` function, which allows us to run a test multiple times and consider it successful only if it completes at least n runs out of m attempts.

While you can run the above directly with `pytest`, different tests might require different setups so we have added some shortcuts in our `Makefile` to run them in a single command.

> NOTE: there is another set of tests pertaining the MCP servers we are curating in the `docs/mcp-servers.json` file: these do not validate our own code, but the MCP servers themselves. You can find the code in `docs/scripts/test_mcp_servers.py` and you can run the tests with `make test-mcps`.


## Running Tests

### Unit Tests

These tests are the simplest ones, and you can run them with:

```bash
make test-unit
```

The `test-unit` target runs the following:

```
uv run --group tests pytest -v tests/unit/
uv run --group tests pytest -v tests/tools/
```

which will first make sure all the libraries in the `tests` dependency group are present in the environment, the run `pytest` on the two directories `unit/` and `tools/`.

### Generation Tests

These tests replicate the full agent generation workflow with specific prompts. To do this, they need the A2A server to be up and running.

The `pytest` command that is run by the `test-single-turn-generation` Makefile target is:

```
uv run --group tests pytest -xvs tests/generation/test_single_turn_generation.py --prompt-id=$(PROMPT_ID) $(UPDATE_ARTIFACTS)
```

This accepts two input parameters:
- `$(PROMPT_ID)` which is one of the use-case names found in `generation/use_cases.yaml` (currently `summarize-url-content`, `url-to-podcast`, and `scoring-blueprints-submission`).
- `$(UPDATE_ARTIFACTS)` which is just a flag (`--update-artifacts`), to be added if you want the artifacts generated during this test to replace the ones which are already stored in the `artifacts/` directory.

Note that this target assumes you are already running the A2A server and will break if you are not! The following two targets are more suitable as they first check whether the server is running and will not even start the tests otherwise:

```bash
make test-single-turn-generation-local PROMPT_ID=<prompt-id>
make test-single-turn-generation-e2e PROMPT_ID=<prompt-id>
```

The first target just verifies the server is up, and is most convenient in the local setting where you usually alreay have the server running in background. The second target is mostly used in CI and will always start and stop a server for you.

#### Structure of the `uses_cases.yaml` file

The `generation/uses_cases.yaml` file holds relevant information on how to run the generation / generated agents tests. Each use case has the following parameters:

- `prompt`: the prompt used to generate the agent.
- `expected_num_turns`: the expected maximum number of turns agent-factory will take to generate the agent. If generation takes more, [this test](https://github.com/mozilla-ai/agent-factory/blob/faa7ee4edcd0ac6791df6bcf451f2b78010fb108/tests/generation/test_single_turn_generation.py#L88) will fail.
- `expected_execution_time`: the expected maximum execution time agent-factory will take to generate the agent. If generation takes more, [this test](https://github.com/mozilla-ai/agent-factory/blob/faa7ee4edcd0ac6791df6bcf451f2b78010fb108/tests/generation/test_single_turn_generation.py#L74) will fail.
- `min_successes`, `max_attempts`: these two parameters are used together. As generation results are non-deterministic, we allow tests to fail sometimes so we expect at least a minimum number of generation to be successful out of a maximum number of runs. This is built to end as early as possible: as soon as we reach `min_successes` runs, the test succeeds; if, before that, we get a number of failures greater than `max_attempts`-`min_successes`, the test fails.
- `requires_mcpd`: if this is `true`, it means that the generated agent is expected to use MCP tools. This information is used so we can run [mcpd](https://github.com/mozilla-ai/mcpd/) first before running integration tests.

### Artifact Tests

These tests statically validate the generated agent artifacts. They can be run as follows:

```bash
make test-generated-artifacts PROMPT_ID=<prompt-id>
```

with `prompt-id` as defined before (see "Generation Tests"). As there are no dependencies on external tools or services, the only command that is run by this Makefile target is:

```
uv run --group tests pytest tests/generated_artifacts/ -m artifact_validation --prompt-id=$(PROMPT_ID) -v
```

Note the `-m artifact_validation` parameter: this is a *marker* that is used to group tests under the same namespace so you can follow them more easily in CI. Our namespaces are defined in `/pytest.ini`.

### Artifact Tests (integration)

These tests run the agents that have been created by *single-turn-generation* and verify they behave as expected.
Some of the MCP tools are mocked so we don't depend on external applications or paid APIs for our tests.
As most MCP tools are managed by `mcpd`, its deamon needs to be started beforehand and passed the generated
`.mcpd.toml` and `secrets.prod.toml` files.

If you already have an mcpd server running (or if the agent you want to test does not need mcpd) you can
run the following:

```bash
make test-generated-artifacts-integration PROMPT_ID=<prompt-id>
```

with `prompt-id` as defined before (see "Generation Tests"). The command that is run by this Makefile target is:

```
uv run --group tests pytest tests/generated_artifacts/ -m artifact_integration --prompt-id=$(PROMPT_ID) -vs
```

In the more likely scenario where you need mcpd, you can run:

```bash
make test-generated-artifacts-integration-e2e PROMPT_ID=<prompt-id>
```

#### Q: What should I do if I add a new / change an existing agent artifact?

Artifact tests -and in particular those with mocks as they run their actual code- are tightly dependent on
the artifacts that you have built and the code they run. This means that you will need to update the test
not only when you create new use cases, but also when you regenerate the existing agents.

> **Why regenerate an existing agent?** We want our test agent artifacts to be consistent with the code
that generated them. If you change anything in agent-factory that might impact the downstream agents,
then you should recreate and test them. Examples of changes include agent-factory instructions, agent
template new or different tools called, and so on.

Here is what you should check when you create a new agent or update an existing one:

- *Are mocks running properly?* Mocks are 1:1 substitutes for existing python functions. The mappings
are defined [here](https://github.com/mozilla-ai/agent-factory/blob/main/tests/generated_artifacts/tool_mappings.py)
and their corresponding mocks
[here](https://github.com/mozilla-ai/agent-factory/blob/main/tests/generated_artifacts/tool_mocks.py).
When you create a new agent, you should make sure that if there's any tool you want to mock then there
also are a corresponding mock and an explicit mapping defined. When you update an agent, you should
verify that the MCP tools you are calling are still the same or they won't be mocked anymore.

- *Are we testing for the right outputs?* When we create an agent artifact, we generate code and
configuration files that we expect to satisfy some criteria. These criteria are verified in different
files and should be integrated with new use-cases or checked for consistency if an agent is rebuilt. For
instance, `test_generated_agents` checks that some specific [tools / environment variables](https://github.com/mozilla-ai/agent-factory/blob/main/tests/generated_artifacts/test_generated_agents.py#L8) are used;
`test_generated_traces` makes sure that some specific [tools](https://github.com/mozilla-ai/agent-factory/blob/main/tests/generated_artifacts/test_generated_traces.py#L40) are searched while generating the agents;
`test_with_mocks` verifies that the generated agents complete successfully with some specific
[outputs](https://github.com/mozilla-ai/agent-factory/blob/main/tests/generated_artifacts/test_with_mocks.py#L97).
While some of these rarely change (e.g. if we make available just one slack MCP tool we will likely
always check for the very same name), others (e.g. schemas for model outputs) have way more
variability and you'll have to make sure your tests are consistent with the generated code.

- *Are environments set properly?* Whenever we test an agent actually running (with or without mocks),
we need to make sure we set up its environment accordingly. Environment variables for tests are set
in the [Makefile](https://github.com/mozilla-ai/agent-factory/blob/main/Makefile#L150) and they
should be kept up-to-date with the (mock) tokens or configuration parameteres the agents need to run.

## Tests in CI

Almost all of our tests also run in CI. The CI pipeline (`.github/workflows/tests.yaml`) runs the following:

- **Always Run**
    - **Unit Tests** (`run-unit-tests`): fast unit tests on every push/PR
    - **Generated Artifacts Tests** (`run-generated-artifacts-tests`) - static artifact validation tests

- **Main Branch & Manual Only**
    - **Generation Tests** (`run-generation-tests`): end-to-end generation tests
    - **Agent Evaluation Tests** (`run-agent-evaluation-tests`): tests of generated agent evaluations

- **Manual Trigger Only**
    - **Integration Tests** (`run-generated-artifacts-integration-tests`): end-to-end integration tests with MCP servers
