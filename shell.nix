{ pkgs ? import <nixpkgs> { } }:

with pkgs;

mkShell {
  buildInputs = [
    git

    texlive.combined.scheme-full

    tinybeachthor.netlogo
  ];
  shellHook = ''
  '';
}
