{
  description = "Sphinx Extension for performing SPARQL queries";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.pyproject-nix.url = "github:nix-community/pyproject.nix";
  inputs.pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, flake-utils, pyproject-nix, ... }:
    flake-utils.lib.eachSystem [ "aarch64-linux" "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };
        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };
        python = pkgs.python3;
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
    ) // {
      overlays.default = final: prev: {
        python3 = prev.python3.override {
          packageOverrides = final: prev: {
            sphinx-sparql = prev.pythonPackages.callPackage ./default.nix { };
          };
        };
      };
    };
}
