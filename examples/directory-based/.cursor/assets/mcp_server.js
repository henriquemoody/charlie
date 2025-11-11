#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Create a simple MCP server with just the basics
const server = new Server(
  {
    name: "local-tools",
    version: "1.0.0",
  },
  {
    capabilities: {}, // no special features yet
  }
);

// Set up standard input/output transport (default for MCP)
const transport = new StdioServerTransport();

// Start the server
server.connect(transport);

console.log("✅ Simple MCP server started (stdio mode)");
