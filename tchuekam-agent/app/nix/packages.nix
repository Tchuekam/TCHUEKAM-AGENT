# nix/packages.nix — TchuEkaM Agent package built with uv2nix
{ inputs, ... }:
{
  perSystem =
    { pkgs, inputs', ... }:
    let
      tchuekamAgent = pkgs.callPackage ./tchuekam-agent.nix {
        inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
        npm-lockfile-fix = inputs'.npm-lockfile-fix.packages.default;
        # Only embed clean revs — dirtyRev doesn't represent any upstream
        # commit, so comparing it would always claim "update available".
        rev = inputs.self.rev or null;
      };
    in
    {
      packages = {
        default = tchuekamAgent;
        tui = tchuekamAgent.tchuekamTui;
        web = tchuekamAgent.tchuekamWeb;

        fix-lockfiles = tchuekamAgent.tchuekamNpmLib.mkFixLockfiles {
          packages = [ tchuekamAgent.tchuekamTui tchuekamAgent.tchuekamWeb ];
        };
      };
    };
}
