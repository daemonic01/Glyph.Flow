import json, os, time, shutil
from pathlib import Path
from core.controllers.command_result import CommandResult
from core.controllers.command_factory import summon

class InternalTestError(Exception):
    pass


def test_handler(ctx, *, target: str = "all") -> CommandResult:
    """
    Usage: test <config|cfg | files|integrity | cmd|commands | all|overall>

    - files/integrity: tests/files.txt alapján fájlintegritás
    - config/cfg: config.json létezik + kötelező kulcsok megvannak
    - cmd/commands: parancsok tesztelése két külső JSON listából
      * with data:   paths.cmd_test_data  (minden elem: {"cmd": "...", "expect": "success"})
      * without:     paths.cmd_test_no_data
    - all/overall: mindhárom szekció egymás után
    """
    base_dir = Path(getattr(ctx, "base_dir", Path.cwd()))
    start_all = time.perf_counter()
    sections = _normalize_target(target)

    ctx.config.edit("assume_yes", True)
    ctx.config.edit("test_mode", True)

    report = []
    stats = {}
    overall_ok = True
    try:
        if "files" in sections:
            ok, sec, lines = _run_files(ctx, base_dir)
            report += ["=== FILES ===", *lines]
            stats["files_sec"] = sec
            overall_ok &= ok

        if "config" in sections:
            ok, sec, lines = _run_config(ctx, base_dir)
            report += ["\n=== CONFIG ===", *lines]
            stats["config_sec"] = sec
            overall_ok &= ok

        if "cmd" in sections:
            ok, sec, lines = _run_commands(ctx)
            report += ["\n=== COMMANDS ===", *lines]
            stats["commands_sec"] = sec
            overall_ok &= ok

        total = time.perf_counter() - start_all
        report += [
            "\n=== SUMMARY ===",
            f"sections: {', '.join(sections)}",
            f"time: files={stats.get('files_sec', 0):.4f}s "
            f"config={stats.get('config_sec', 0):.4f}s "
            f"commands={stats.get('commands_sec', 0):.4f}s "
            f"total={total:.4f}s"
        ]

        
        code = "success" if overall_ok else "partial"
        return CommandResult(code=code, params={"report": "\n".join(report)}, outcome=overall_ok)
    except Exception as e:
        return CommandResult(code=code, params={"error": e}, outcome=overall_ok)
    finally:
        # Reset config
        ctx.config.edit("assume_yes", False)
        ctx.config.edit("test_mode", False)
        ctx.config.save()
        # Delete test exports if they exist
        if os.path.exists(ctx.base_dir / "tests/exports"):
            shutil.rmtree(ctx.base_dir / "tests/exports")





# -------------------------
# SECTIONS
# -------------------------

def _run_files(ctx, base_dir: Path):
    """File integrity checks according to tests/files.txt (paths.file_tests)."""
    t0 = time.perf_counter()
    lines = []
    ok_count = 0

    list_rel = ctx.config.get("paths.file_tests")
    if not list_rel:
        raise InternalTestError("paths.file_tests doesn't exists.")
    fpath = Path(list_rel)
    if not fpath.is_absolute():
        fpath = base_dir / fpath

    try:
        entries = [ln.strip() for ln in fpath.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception as e:
        raise InternalTestError(f"files.txt read error: {e}")

    for fp in entries:
        p = Path(fp)
        if not p.is_absolute():
            p = base_dir / p
        exists = p.exists()
        tag = "SUCCESS" if exists else "FAILED"
        if exists:
            ok_count += 1
        lines.append(f"[{tag}] {fp}")

    sec = time.perf_counter() - t0
    lines.append(f"-> total {len(entries)} | ok {ok_count} | time {sec:.4f}s")
    return ok_count == len(entries), sec, lines


def _run_config(ctx, base_dir: Path):
    """
    Config check:
      1) config path exists (paths.config)
      2) neccessary keys are exist:
         - origin: paths.config_keys (txt)
      Key format: dot-path (pl. 'paths.config', 'paths.file_tests', ...)
    """
    t0 = time.perf_counter()
    lines = []
    ok = True

    # config file
    cfg_path_val = ctx.base_dir / "config.json"
    if not cfg_path_val:
        lines.append("[FAILED] paths.config doesn't exists.")
        return False, time.perf_counter() - t0, lines

    cfg_path = Path(cfg_path_val)
    if not cfg_path.is_absolute():
        cfg_path = base_dir / cfg_path
    if cfg_path.exists():
        lines.append(f"[SUCCESS] config file exists: {cfg_path}")
    else:
        lines.append(f"[FAILED] config file missing: {cfg_path}")
        ok = False

    # list of neccessary keys
    keys_file = ctx.config.get("paths.config_keys_test")
    if keys_file:
        kpath = Path(keys_file)
        if not kpath.is_absolute():
            kpath = base_dir / kpath
        try:
            required = [ln.strip() for ln in kpath.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except Exception as e:
            lines.append(f"[FAILED] config_keys file read error: {e}")
            ok = False
            required = []
    else:
        lines.append("No validation.config_keys / paths.config_keys")

    # check keys
    missing = []
    for key in required:
        try:
            val = ctx.config.get(key)
        except Exception:
            val = None
        if val is None:
            missing.append(key)

    if missing:
        ok = False
        for m in missing:
            lines.append(f"[FAILED] missing config key: {m}")
    else:
        lines.append("[SUCCESS] all required config keys present")

    sec = time.perf_counter() - t0
    lines.append(f"-> time {sec:.4f}s")
    return ok, sec, lines


def _run_commands(ctx):
    """
    CMD test:
      - with data:   paths.cmd_test_data  -> before: sample
      - without:     paths.cmd_test_no_data -> before: clearall
      JSON formátum: [ {"cmd":"...", "expect":"success"}, ... ]
    """
    t0 = time.perf_counter()
    lines = []
    ok = True
    total_ok = 0
    total = 0

    # with data
    lines.append("")
    data_path = ctx.config.get("paths.cmd_test_data")
    if data_path:
        cases = _load_cmd_cases(ctx, data_path)
        if cases:
            _run_cmd_and_log(ctx, "sample", lines)
            for case in cases:
                dt, passed = _exec_case(ctx, case, lines)
                total += 1
                total_ok += 1 if passed else 0
                ok &= passed
    
    # without data
    no_data_path = ctx.config.get("paths.cmd_test_no_data")
    if no_data_path:
        cases = _load_cmd_cases(ctx, no_data_path)
        if cases:
            _run_cmd_and_log(ctx, "clearall", lines)
            for case in cases:
                dt, passed = _exec_case(ctx, case, lines)
                total += 1
                total_ok += 1 if passed else 0
                ok &= passed
    
    sec = time.perf_counter() - t0
    lines.append(f"-> commands {total_ok}/{total} ok | time {sec:.4f}s")
    return ok, sec, lines


# -------------------------
# HELPERS
# -------------------------

def _load_cmd_cases(ctx, path_val: str):
    """JSON: [ { 'cmd': '...', 'expect': 'success' }, ... ]"""
    base_dir = Path(getattr(ctx, "base_dir", Path.cwd()))
    p = Path(path_val)
    if not p.is_absolute():
        p = base_dir / p
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise InternalTestError(f"cmd cases load failed ({p}): {e}")

    if not isinstance(data, list):
        raise InternalTestError(f"cmd cases must be a JSON array in {p}")

    norm = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "cmd" not in item:
            raise InternalTestError(f"invalid case at index {i} in {p}: must be dict with 'cmd'")
        norm.append({"cmd": str(item["cmd"]), "expect": str(item.get("expect", "success"))})
    return norm


def _exec_case(ctx, case, lines):
    raw = case["cmd"]
    expect = case.get("expect", "success")
    t0 = time.perf_counter()
    cmd = summon(raw, ctx)
    res = cmd.execute()
    dt = time.perf_counter() - t0
    got = getattr(res, "code", None)
    passed = (got == expect)
    tag = "SUCCESS" if passed else "FAILED"
    if passed:
        lines.append(f"[green][{tag}] {raw} -> code={got} expect={expect} ({dt:.4f}s)")
    else:
        lines.append(f"[red][{tag}] {raw} -> code={got} expect={expect} ({dt:.4f}s)")
    return dt, passed


def _normalize_target(target: str):
    key = (target or "all").strip().lower()
    if key in ("files", "integrity"):
        return ["files"]
    if key in ("config", "cfg"):
        return ["config"]
    if key in ("cmd", "commands"):
        return ["cmd"]
    if key in ("all", "overall"):
        return ["files", "config", "cmd"]
    # default: overall
    return ["files", "config", "cmd"]

def _run_cmd(ctx, summon, raw):
    t0 = time.perf_counter()
    cmd = summon(raw, ctx)
    res = cmd.execute()
    dt = time.perf_counter() - t0
    return dt, res

def _log(ctx, msg, *, level="info"):
    try:
        log = getattr(ctx, "log", None)
        if log is None:
            return
        if level == "error" and hasattr(log, "error"):
            log.error(msg)
        elif level == "warning" and hasattr(log, "warning"):
            log.warning(msg)
        elif hasattr(log, "info"):
            log.info(msg)
    except Exception:
        pass

def _run_cmd_and_log(ctx, raw, report_lines):
    dt, res = _run_cmd(ctx, summon, raw)
    line = f"[RUN] {raw} -> code={getattr(res, 'code', None)} ({dt:.4f}s)"
    report_lines.append(line)
    return res