{ pkgs ? import <nixpkgs> { }
, mkPython
}:

let
  pyEnv = mkPython {
    requirements = builtins.readFile ./requirements.txt;
  };
in

with pkgs;

mkShell {
  buildInputs = [
    git
    pre-commit

    texlive.combined.scheme-full

    pyEnv
    tinybeachthor.netlogo

    nodejs
    yarn
    chromium
  ];
  PUPPETEER_EXECUTABLE_PATH = "${chromium}/bin/chromium";
}
