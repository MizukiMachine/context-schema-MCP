import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

type ToolArguments = Record<string, unknown>;

type TextContent = {
  type: "text";
  text: string;
};

type ToolResult = {
  content: TextContent[];
  isError?: boolean;
};

type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties?: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
  handler: (args: ToolArguments) => Promise<ToolResult>;
};

const SERVER_INFO = {
  name: "context-schema-mcp",
  version: "1.0.0",
} as const;

const tools: ToolDefinition[] = [
  {
    name: "ping",
    description: "疎通確認用のツールです。MCPサーバーが応答可能かを確認します。",
    inputSchema: {
      type: "object",
      additionalProperties: false,
    },
    handler: async () => ({
      content: [{ type: "text", text: "pong" }],
    }),
  },
  {
    name: "echo",
    description: "受け取ったメッセージをそのまま返します。入力と出力の確認に使えます。",
    inputSchema: {
      type: "object",
      properties: {
        message: {
          type: "string",
          description: "そのまま返却したい文字列",
        },
      },
      required: ["message"],
      additionalProperties: false,
    },
    handler: async (args) => {
      const message = args.message;

      if (typeof message !== "string" || message.length === 0) {
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: 'The "message" argument must be a non-empty string.',
            },
          ],
        };
      }

      return {
        content: [{ type: "text", text: message }],
      };
    },
  },
  {
    name: "server_info",
    description: "サーバー名、バージョン、登録済みツールの一覧を返します。",
    inputSchema: {
      type: "object",
      additionalProperties: false,
    },
    handler: async () => ({
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              server: SERVER_INFO,
              tools: tools.map(({ name, description }) => ({
                name,
                description,
              })),
            },
            null,
            2,
          ),
        },
      ],
    }),
  },
];

const toolRegistry = new Map(tools.map((tool) => [tool.name, tool]));

const server = new Server(
  {
    name: SERVER_INFO.name,
    version: SERVER_INFO.version,
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: tools.map(({ name, description, inputSchema }) => ({
    name,
    description,
    inputSchema,
  })),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = toolRegistry.get(request.params.name);

  if (!tool) {
    return {
      isError: true,
      content: [
        {
          type: "text",
          text: `Unknown tool: ${request.params.name}`,
        },
      ],
    };
  }

  return tool.handler(request.params.arguments ?? {});
});

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`${SERVER_INFO.name} server running on stdio`);
}

main().catch((error: unknown) => {
  console.error("Failed to start MCP server:", error);
  process.exit(1);
});
