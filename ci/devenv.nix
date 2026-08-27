{ pkgs, ... }:

# Minimal shell for CI.
#
# The deployment pipeline needs exactly one tool: tofu. The root devenv.nix is
# the *development* environment (Python, bun, uv, database TUIs, process
# manager...), and evaluating all of it in CI meant any unrelated dev
# dependency could block a deploy — which is exactly what happened when a CVE
# patch deep in the toolchain stopped resolving on a cold Nix store.
#
# Keeping this separate preserves the reason we used devenv in CI in the first
# place (same nixpkgs pin as local, so same tofu version) while shrinking the
# blast radius to the one package the pipeline actually runs.
#
# Used from the repo root as:
#   devenv shell --from path:./ci -- tofu -chdir=infra/envs/dev plan
{
  packages = [ pkgs.opentofu ];
}
