{
  inputs = {
    flake-utils.url = github:numtide/flake-utils/master;
    nixpkgs.url = github:NixOS/nixpkgs/nixos-20.09;
    mach-nix = {
      url = github:DavHau/mach-nix/3.2.0;
      inputs = {
        nixpkgs.follows     = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
    tinybeachthor = {
      url = github:tinybeachthor/nur-packages/master;
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, flake-utils, nixpkgs, mach-nix, tinybeachthor }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = (import nixpkgs {
          inherit system;
          overlays = [ tinybeachthor.overlay ];
        });
      in {
        devShell = import ./shell.nix {
          inherit pkgs;
          inherit (mach-nix.lib.${system}) mkPython;
        };
      });
}
