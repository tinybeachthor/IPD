{ pkgs ? import <nixpkgs> { } }:

with pkgs;

mkShell {
  buildInputs = [
    git

    netlogo
  ];
  shellHook = ''
  '';
}
