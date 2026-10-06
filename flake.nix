{
  description = "PierPressure development shell";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      lib = nixpkgs.lib;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      # "3.14" or "3.14.7" in .python-version both select python314.
      pythonVersionString = lib.trim (builtins.readFile ./.python-version);
      pythonVersion = lib.splitString "." pythonVersionString;
      pythonAttr = "python${lib.elemAt pythonVersion 0}${lib.elemAt pythonVersion 1}";
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.${pythonAttr}
            pkgs.uv
            pkgs.just
          ];

          # Make uv build the project venv on the Nix Python instead of
          # downloading its own interpreter. Prebuilt wheels (numpy, astropy)
          # link against libstdc++ and zlib, which the Nix Python cannot find
          # on its own.
          env = {
            UV_PYTHON = "${pkgs.${pythonAttr}}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
            # The image's Python version, which compose.yaml needs (#45).
            PYTHON_VERSION = pythonVersionString;
            LD_LIBRARY_PATH = lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
            ];
          };
        };
      });
    };
}
