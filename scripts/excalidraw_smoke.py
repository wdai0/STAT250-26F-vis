#!/usr/bin/env python3
"""Check the official hosted MCP; optionally create a disposable teaching diagram."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


ENDPOINT = "https://mcp.excalidraw.com/mcp"
ROOT = Path(__file__).resolve().parents[1]


class MCPClient:
    """Small synchronous JSON-RPC client supporting JSON and SSE responses."""

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self.sequence = 0

    def request(self, method: str, params: dict, *, notification=False):
        self.sequence += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification:
            payload["id"] = self.sequence
        request = urllib.request.Request(
            ENDPOINT, data=json.dumps(payload).encode(), headers=self.headers
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.headers["Mcp-Session-Id"] = session
            if notification:
                response.read()
                return None
            if "text/event-stream" in response.headers.get("Content-Type", ""):
                message, data = None, []
                for raw in response:
                    line = raw.decode().rstrip("\r\n")
                    if line.startswith("data:"):
                        data.append(line[5:].lstrip())
                    elif not line and data:
                        candidate = json.loads("\n".join(data))
                        data = []
                        if candidate.get("id") == self.sequence:
                            message = candidate
                            break
                if message is None:
                    raise RuntimeError("MCP stream ended without the requested response")
            else:
                message = json.load(response)
        if message.get("id") != self.sequence or "error" in message:
            raise RuntimeError(f"Invalid MCP response: {message}")
        result = message["result"]
        if result.get("isError"):
            raise RuntimeError(f"MCP tool failed: {result}")
        return result

    def call(self, name: str, arguments: dict):
        return self.request("tools/call", {"name": name, "arguments": arguments})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draw", action="store_true", help="Send the sample to create_view")
    parser.add_argument("--output", type=Path, default=ROOT / "build/excalidraw-smoke")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    client = MCPClient()
    initialized = client.request("initialize", {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "stat250-excalidraw-smoke", "version": "1.0"},
    })
    client.headers["MCP-Protocol-Version"] = initialized["protocolVersion"]
    client.request("notifications/initialized", {}, notification=True)
    tools = client.request("tools/list", {})["tools"]
    names = {tool["name"] for tool in tools}
    if not {"read_me", "create_view"} <= names:
        raise RuntimeError(f"Expected drawing tools missing: {sorted(names)}")
    reference = client.call("read_me", {})
    if not any(c.get("text") for c in reference.get("content", [])):
        raise RuntimeError("Empty element-format reference")
    resource_uri = next(t for t in tools if t["name"] == "create_view")["_meta"]["ui"]["resourceUri"]
    resource = client.request("resources/read", {"uri": resource_uri})
    html = next(c["text"] for c in resource["contents"] if c.get("text"))
    if "<html" not in html.lower():
        raise RuntimeError("UI resource is not HTML")
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT, "server": initialized["serverInfo"],
        "protocol_version": initialized["protocolVersion"], "tools": sorted(names),
        "read_me": "passed", "ui_resource": resource_uri,
        "ui_sha256": hashlib.sha256(html.encode()).hexdigest(),
        "ui_rendering": "not tested by this protocol check",
    }
    if args.draw:
        source = ROOT / "diagrams/excalidraw/sampling-workflow.elements.json"
        elements = json.loads(source.read_text())
        result = client.call("create_view", {"elements": json.dumps(elements)})
        (args.output / "create-view-result.json").write_text(json.dumps(result, indent=2) + "\n")
        checkpoint = result["structuredContent"]["checkpointId"]
        restored = client.call("read_checkpoint", {"id": checkpoint})
        original = json.loads(restored["content"][0]["text"])["elements"]
        if original != elements:
            raise RuntimeError("Created checkpoint differs from submitted elements")
        replacement = next(e.copy() for e in elements if e.get("id") == "subtitle")
        replacement.update(id="subtitle-edited", text="STAT 250 · Repeated random sampling")
        delta = [
            {"type": "restoreCheckpoint", "id": checkpoint},
            {"type": "delete", "ids": "subtitle"}, replacement,
        ]
        edited = client.call("create_view", {"elements": json.dumps(delta)})
        edited_id = edited["structuredContent"]["checkpointId"]
        restored = client.call("read_checkpoint", {"id": edited_id})
        actual = json.loads(restored["content"][0]["text"])["elements"]
        expected = [e for e in elements if e.get("id") != "subtitle"] + [replacement]
        if actual != expected:
            raise RuntimeError("Checkpoint edit did not preserve the expected scene")
        (args.output / "edited.elements.json").write_text(json.dumps(actual, indent=2) + "\n")
        report.update(create_view="passed", checkpoint_roundtrip="passed",
                      checkpoint_edit="passed", checkpoint_id=edited_id)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
