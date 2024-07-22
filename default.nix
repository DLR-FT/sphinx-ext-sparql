{
  buildPythonPackage,
  hatchling,
  sphinx,
  pyoxigraph,
}:
buildPythonPackage {
  pname = "sphinx-sparql";
  pyproject = true;
  version = "0.1";
  src = ./.;
  build-system = [ hatchling ];
  dependencies = [
    pyoxigraph
    sphinx
  ];
}
