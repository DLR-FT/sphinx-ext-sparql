{
  description = "Sphinx Extension for performing SPARQL queries";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.pyproject-nix.url = "github:nix-community/pyproject.nix";
  inputs.pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { nixpkgs, flake-utils, pyproject-nix, ... }:
    flake-utils.lib.eachSystem [ "aarch64-linux" "x86_64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

        python = pkgs.python3.override {
          packageOverrides = self: super: {
            pyoxigraph = import ./pyoxigraph.nix {
              inherit (super) buildPythonPackage;
              inherit (pkgs) rustPlatform pkg-config fetchFromGitHub;
            };
          };
        };
      in
      rec {
        packages.default =
          let
            attrs = project.renderers.buildPythonPackage { inherit python; };
          in
          python.pkgs.buildPythonPackage (attrs // {
            env.CUSTOM_ENVVAR = "hello";
          });
        devShells.default =
          let
            arg = project.renderers.withPackages { inherit python; };
            pythonEnv = python.withPackages arg;
          in
          pkgs.mkShell {
            packages = [
              pkgs.nodePackages.prettier
              pkgs.nixpkgs-fmt
              packages.default.passthru.optional-dependencies.test
              pythonEnv
              pkgs.ruff-lsp
              python.pkgs.pythonPackages.pylsp-rope
              python.pkgs.pythonPackages.python-lsp-ruff
              python.pkgs.pythonPackages.python-lsp-server
            ];
          };
      }
    );
}
