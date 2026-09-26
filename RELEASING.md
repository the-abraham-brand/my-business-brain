# Releasing My Business Brain

1. **Update the version** in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, and add a section to `CHANGELOG.md`.
2. **Run the checks locally** from the plugin root:
   ```
   claude plugin validate .
   python3 -m unittest discover -s tests -v
   claude plugin eval . --scaffold --allow-tools Write Edit Bash --runs 1 --ablation none   # quick smoke test
   ```
   The eval suite calls the model and uses your plan or API credit. For a release, run it at the default 3 runs with the no-plugin baseline, and keep every case at 0.8 or above.
3. **Commit and push.** GitHub Actions validates the plugin and runs the unit tests on Linux, macOS and Windows.
4. **Tag the release** as `my-business-brain--v<version>` (for example `my-business-brain--v1.2.0`) and publish a GitHub release with the changelog section and the packaged `.plugin` file. Plugin dependencies resolve versions from tags in this format. Pushing the tag also runs the eval suite in CI if the `ANTHROPIC_API_KEY` repository secret is set.
5. **Package** for the Claude app: zip the plugin folder (without `evals/results/`, `tests/` caches or `.git`) as `my-business-brain.plugin`.

## Evals in CI

Evals run only when started by hand (Actions > CI > Run workflow) or when a release tag is pushed, because they are billed. Add your key as the repository secret `ANTHROPIC_API_KEY`. The workflow pins the agent and judge models and caps spend at USD 25 per run.
