"""
Async stdio MCP client bridge for the /paper workflow.

This client starts the local MCP server process (default: `node build/index.js`),
performs MCP initialization, and provides typed helper wrappers for tools used by
paper/cdli_api.py.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
from pathlib import Path
from typing import Any


class MCPClientError(RuntimeError):
    """Raised when MCP transport/protocol operations fail."""


class MCPToolError(RuntimeError):
    """Raised when an MCP tool returns isError=true or malformed output."""


class MCPStdioClient:
    """Minimal async JSON-RPC client over newline-delimited stdio MCP transport."""

    def __init__(
        self,
        command: str,
        args: list[str],
        timeout_sec: float,
        cwd: str,
    ) -> None:
        self.command = command
        self.args = args
        self.timeout_sec = timeout_sec
        self.cwd = cwd

        self._proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._request_id = 0
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._write_lock = asyncio.Lock()
        self._initialized = False
        self._last_stderr_lines: list[str] = []

    async def start(self) -> None:
        if self._proc is not None:
            return

        try:
            self._proc = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
            )
        except FileNotFoundError as exc:
            raise MCPClientError(
                f"Failed to start MCP server: command not found '{self.command}'."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive branch
            raise MCPClientError(f"Failed to start MCP server: {exc}") from exc

        self._reader_task = asyncio.create_task(self._read_loop(), name="paper-mcp-read-loop")
        self._stderr_task = asyncio.create_task(self._stderr_loop(), name="paper-mcp-stderr-loop")

        try:
            await self._initialize()
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        # Stop reader tasks first
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                task.cancel()

        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

        self._reader_task = None
        self._stderr_task = None

        # Fail pending requests
        pending_error = MCPClientError("MCP connection closed.")
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(pending_error)
        self._pending.clear()

        # Terminate process
        if self._proc is not None:
            proc = self._proc
            self._proc = None

            if proc.stdin is not None:
                try:
                    proc.stdin.close()
                except Exception:
                    pass

            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()

        self._initialized = False

    async def list_tools(self) -> dict[str, Any]:
        return await self._request("tools/list", {})

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def _initialize(self) -> None:
        init_result = await self._request(
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {
                    "name": "cdli-paper-agent",
                    "version": "1.0.0",
                },
            },
        )

        protocol_version = init_result.get("protocolVersion")
        if not isinstance(protocol_version, str):
            raise MCPClientError("Invalid MCP initialize result: missing protocolVersion.")

        await self._notify("notifications/initialized", {})
        self._initialized = True

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        await self._send(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }
        )

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._proc is None:
            raise MCPClientError("MCP client is not started.")

        self._request_id += 1
        request_id = self._request_id
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future

        await self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )

        try:
            response = await asyncio.wait_for(future, timeout=self.timeout_sec)
        except asyncio.TimeoutError as exc:
            self._pending.pop(request_id, None)
            raise MCPClientError(f"MCP request timed out for method '{method}'.") from exc

        if "error" in response:
            err = response["error"]
            code = err.get("code") if isinstance(err, dict) else "unknown"
            message = err.get("message") if isinstance(err, dict) else str(err)
            raise MCPClientError(f"MCP error calling '{method}' (code {code}): {message}")

        result = response.get("result")
        if not isinstance(result, dict):
            raise MCPClientError(f"Invalid MCP response for '{method}': missing result object.")

        return result

    async def _send(self, message: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise MCPClientError("MCP process is not writable.")

        payload = (json.dumps(message, ensure_ascii=True) + "\n").encode("utf-8")

        async with self._write_lock:
            self._proc.stdin.write(payload)
            await self._proc.stdin.drain()

    async def _read_loop(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return

        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break

            try:
                message = json.loads(line.decode("utf-8").strip())
            except json.JSONDecodeError:
                continue

            req_id = message.get("id")
            if isinstance(req_id, int) and req_id in self._pending:
                fut = self._pending.pop(req_id)
                if not fut.done():
                    fut.set_result(message)

        # Process ended; fail all pending calls.
        proc_exit = self._proc.returncode if self._proc else None
        stderr_tail = "\n".join(self._last_stderr_lines[-5:]).strip()
        detail = f" (exit code {proc_exit})" if proc_exit is not None else ""
        if stderr_tail:
            detail += f"\nRecent stderr:\n{stderr_tail}"

        err = MCPClientError(f"MCP server process closed unexpectedly{detail}")
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(err)
        self._pending.clear()

    async def _stderr_loop(self) -> None:
        if self._proc is None or self._proc.stderr is None:
            return

        while True:
            line = await self._proc.stderr.readline()
            if not line:
                break

            txt = line.decode("utf-8", errors="replace").rstrip("\n")
            if txt:
                self._last_stderr_lines.append(txt)
                if len(self._last_stderr_lines) > 50:
                    self._last_stderr_lines = self._last_stderr_lines[-50:]


_client: MCPStdioClient | None = None


def _default_workdir() -> str:
    # paper/ is one level below repo root.
    return str(Path(__file__).resolve().parent.parent)


def _parse_args(raw_args: str) -> list[str]:
    return shlex.split(raw_args)


async def init_client() -> None:
    """Initialize global MCP client singleton (idempotent)."""
    global _client

    if _client is not None:
        return

    command = os.getenv("PAPER_MCP_COMMAND", "node")
    args = _parse_args(os.getenv("PAPER_MCP_ARGS", "build/index.js"))
    timeout_sec = float(os.getenv("PAPER_MCP_TIMEOUT_SEC", "8"))
    workdir = os.getenv("PAPER_MCP_WORKDIR", _default_workdir())

    client = MCPStdioClient(
        command=command,
        args=args,
        timeout_sec=timeout_sec,
        cwd=workdir,
    )
    await client.start()
    _client = client


async def close_client() -> None:
    """Close global MCP client singleton (idempotent)."""
    global _client

    if _client is None:
        return

    client = _client
    _client = None
    await client.close()


def require_client() -> MCPStdioClient:
    if _client is None:
        raise MCPClientError(
            "Paper MCP client is not initialized. "
            "Call init_client() before invoking CDLI access functions."
        )
    return _client


def tool_text(result: dict[str, Any]) -> str:
    """Extract concatenated text payload from MCP call-tool result."""
    content = result.get("content")
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            txt = item.get("text")
            if isinstance(txt, str):
                parts.append(txt)

    return "\n".join(parts).strip()


def ensure_tool_success(result: dict[str, Any], tool_name: str) -> str:
    text = tool_text(result)
    if result.get("isError") is True:
        msg = text or f"Tool '{tool_name}' returned an error without details."
        raise MCPToolError(msg)
    return text
