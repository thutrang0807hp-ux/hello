"""Windows bundle entry point; child backend uses the same executable."""
import os
import runpy
import sys


def main():
    for name in ('stdout', 'stderr'):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, 'w', encoding='utf-8'))
    if sys.argv[1:] == ['--server']:
        runpy.run_module('server', run_name='__main__')
        return 0
    if sys.argv[1:] == ['--stop-server']:
        from desktop_background import stop
        stop()
        return 0
    if sys.argv[1:] == ['--diagnose']:
        from desktop_diagnostics import report
        report()
        return 0
    from desktop_app import main as desktop_main
    return desktop_main()


if __name__ == '__main__':
    raise SystemExit(main())
