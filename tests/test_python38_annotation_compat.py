import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_PATHS = [
    REPO_ROOT / "main.py",
    REPO_ROOT / "config.py",
    REPO_ROOT / "analyzer",
    REPO_ROOT / "reporter",
    REPO_ROOT / "scrapers",
    REPO_ROOT / "notifier",
]
BUILTIN_GENERIC_NAMES = {"list", "dict", "tuple", "set"}


def _iter_python_files():
    for path in PRODUCTION_PATHS:
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from path.rglob("*.py")


def _has_future_annotations(tree):
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            return any(alias.name == "annotations" for alias in node.names)
        return False
    return False


def _uses_modern_runtime_annotation(node):
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id in BUILTIN_GENERIC_NAMES
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return True
    return any(_uses_modern_runtime_annotation(child) for child in ast.iter_child_nodes(node))


def _annotation_nodes(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                yield node.returns
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                if arg.annotation is not None:
                    yield arg.annotation
            if node.args.vararg and node.args.vararg.annotation is not None:
                yield node.args.vararg.annotation
            if node.args.kwarg and node.args.kwarg.annotation is not None:
                yield node.args.kwarg.annotation
        elif isinstance(node, ast.AnnAssign):
            yield node.annotation


def test_python38_runtime_annotation_compatibility():
    offenders = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _has_future_annotations(tree):
            continue
        if any(_uses_modern_runtime_annotation(node) for node in _annotation_nodes(tree)):
            offenders.append(str(path.relative_to(REPO_ROOT)).replace("\\", "/"))

    assert offenders == []
