{ pkgs ? import <nixpkgs> { } }:

with pkgs;

mkShell {
  buildInputs = [
    git

    tinybeachthor.netlogo
  ];
  shellHook = ''
  '';
}
