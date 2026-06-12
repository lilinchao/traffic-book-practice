// Use the mature release line while the newer 314 series propagates to CDNs.
const PYODIDE_VERSION = '0.29.4';
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
let pyodidePromise = null;

async function getPyodide() {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      self.postMessage({type: 'status', text: '正在下载浏览器 Python（首次约需数秒）...'});
      self.importScripts(`${PYODIDE_BASE}pyodide.js`);
      const pyodide = await self.loadPyodide({indexURL: PYODIDE_BASE});
      self.postMessage({type: 'status', text: '正在加载 NumPy...'});
      await pyodide.loadPackage('numpy');
      return pyodide;
    })();
  }
  return pyodidePromise;
}

self.addEventListener('message', async (event) => {
  if (event.data.type !== 'run') return;
  const started = Date.now();
  try {
    const pyodide = await getPyodide();
    self.postMessage({type: 'status', text: '正在运行 Python...'});
    pyodide.globals.set('__student_code__', event.data.code);
    const payload = await pyodide.runPythonAsync(`
import contextlib
import io
import json
import traceback

_stdout = io.StringIO()
_namespace = {"__name__": "__main__"}
try:
    with contextlib.redirect_stdout(_stdout):
        exec(compile(__student_code__, "<online-lab>", "exec"), _namespace)
    if "result" not in _namespace:
        raise ValueError("代码需要创建名为 result 的字典，用于绘制结果。")
    _payload = {"ok": True, "stdout": _stdout.getvalue(), "result": _namespace["result"]}
except Exception:
    _payload = {"ok": False, "stdout": _stdout.getvalue(), "error": traceback.format_exc()}
json.dumps(_payload, ensure_ascii=False)
    `);
    const parsed = JSON.parse(payload);
    if (!parsed.ok) {
      self.postMessage({type: 'error', error: `${parsed.stdout || ''}${parsed.error}`});
      return;
    }
    self.postMessage({
      type: 'result',
      stdout: parsed.stdout,
      result: parsed.result,
      elapsed: ((Date.now() - started) / 1000).toFixed(1)
    });
  } catch (error) {
    self.postMessage({type: 'error', error: error.stack || String(error)});
  }
});
