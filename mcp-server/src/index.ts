import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type CallToolResult,
} from "@modelcontextprotocol/sdk/types.js";

const SERVER_INFO = {
  name: "context-schema-mcp",
  version: "1.0.0",
} as const;

const API_BASE_URL =
  process.env.CONTEXT_SCHEMA_API_URL ?? "http://localhost:8000/api/v1";
const API_TOKEN = process.env.CONTEXT_SCHEMA_API_TOKEN ?? process.env.API_TOKEN;
const DEFAULT_WINDOW_NAME =
  process.env.CONTEXT_SCHEMA_WINDOW_NAME ?? "Context Window";
const DEFAULT_WINDOW_PROVIDER =
  process.env.CONTEXT_SCHEMA_WINDOW_PROVIDER ?? "openai";
const DEFAULT_WINDOW_MODEL =
  process.env.CONTEXT_SCHEMA_WINDOW_MODEL ?? "gpt-4.1";
const DEFAULT_WINDOW_TOKEN_LIMIT = parsePositiveInteger(
  process.env.CONTEXT_SCHEMA_DEFAULT_MAX_TOKENS,
  4096,
);
const CONTEXT_ROLES = ["system", "user", "assistant", "tool"] as const;

type JsonObject = Record<string, unknown>;
type ToolHandler = (args: JsonObject) => Promise<CallToolResult>;

// Template types
interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  content: string;
  variables: string[];
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface TemplateCategory {
  id: string;
  name: string;
  description: string;
  template_count: number;
}

// In-memory template storage
const templateStorage = new Map<string, PromptTemplate>();
const templateCategories: TemplateCategory[] = [
  { id: "general", name: "General", description: "汎用テンプレート", template_count: 0 },
  { id: "coding", name: "Coding", description: "コーディング関連", template_count: 0 },
  { id: "writing", name: "Writing", description: "文書作成", template_count: 0 },
  { id: "analysis", name: "Analysis", description: "分析・評価", template_count: 0 },
  { id: "creative", name: "Creative", description: "クリエイティブ", template_count: 0 },
];

type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: JsonObject;
  handler: ToolHandler;
};

class ToolInputError extends Error {}

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly responseBody: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function parsePositiveInteger(
  value: string | undefined,
  fallback: number,
): number {
  if (value === undefined) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function jsonResult(payload: JsonObject): CallToolResult {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
    structuredContent: payload,
  };
}

function errorResult(error: unknown): CallToolResult {
  const message =
    error instanceof Error ? error.message : "An unknown error occurred.";

  return {
    isError: true,
    content: [
      {
        type: "text",
        text: message,
      },
    ],
  };
}

function isRecord(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getRequiredString(args: JsonObject, key: string): string {
  const value = args[key];
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new ToolInputError(`The "${key}" argument must be a non-empty string.`);
  }

  return value.trim();
}

function getOptionalString(args: JsonObject, key: string): string | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (typeof value !== "string") {
    throw new ToolInputError(`The "${key}" argument must be a string.`);
  }

  return value;
}

function getOptionalNonNegativeInteger(
  args: JsonObject,
  key: string,
): number | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new ToolInputError(
      `The "${key}" argument must be a non-negative integer.`,
    );
  }

  return value;
}

function getOptionalPositiveInteger(
  args: JsonObject,
  key: string,
): number | undefined {
  const value = getOptionalNonNegativeInteger(args, key);
  if (value === undefined) {
    return undefined;
  }

  if (value < 1) {
    throw new ToolInputError(`The "${key}" argument must be a positive integer.`);
  }

  return value;
}

function getOptionalNumber(args: JsonObject, key: string): number | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ToolInputError(`The "${key}" argument must be a finite number.`);
  }

  return value;
}

function getRequiredRole(
  args: JsonObject,
  key: string,
): (typeof CONTEXT_ROLES)[number] {
  const value = getRequiredString(args, key);
  if (!CONTEXT_ROLES.includes(value as (typeof CONTEXT_ROLES)[number])) {
    throw new ToolInputError(
      `The "${key}" argument must be one of: ${CONTEXT_ROLES.join(", ")}.`,
    );
  }

  return value as (typeof CONTEXT_ROLES)[number];
}

function getOptionalArray(args: JsonObject, key: string): unknown[] | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (!Array.isArray(value)) {
    throw new ToolInputError(`The "${key}" argument must be an array.`);
  }

  return value;
}

function getOptionalStringArray(args: JsonObject, key: string): string[] | undefined {
  const value = getOptionalArray(args, key);
  if (value === undefined) {
    return undefined;
  }

  return value.filter((item): item is string => typeof item === "string");
}

function generateId(): string {
  return `tmpl_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function extractVariables(content: string): string[] {
  const regex = /\{\{(\w+)\}\}/g;
  const variables: string[] = [];
  let match;
  while ((match = regex.exec(content)) !== null) {
    if (!variables.includes(match[1])) {
      variables.push(match[1]);
    }
  }
  return variables;
}

function renderTemplateContent(template: string, variables: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    return variables[key] ?? `{{${key}}}`;
  });
}

function buildApiUrl(path: string): URL {
  return new URL(path.replace(/^\//, ""), `${API_BASE_URL.replace(/\/$/, "")}/`);
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function buildApiErrorMessage(
  status: number,
  statusText: string,
  payload: unknown,
): string {
  if (isRecord(payload) && typeof payload.detail === "string") {
    return `Backend API request failed (${status} ${statusText}): ${payload.detail}`;
  }

  if (typeof payload === "string" && payload.trim().length > 0) {
    return `Backend API request failed (${status} ${statusText}): ${payload}`;
  }

  return `Backend API request failed (${status} ${statusText}).`;
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (API_TOKEN) {
    headers.set("Authorization", `Bearer ${API_TOKEN}`);
  }

  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers,
  });
  const rawBody = await response.text();
  const payload = rawBody.length > 0 ? safeJsonParse(rawBody) : undefined;

  if (!response.ok) {
    throw new ApiError(
      buildApiErrorMessage(response.status, response.statusText, payload),
      response.status,
      payload,
    );
  }

  return payload as T;
}

function toNonNegativeInteger(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? Math.trunc(value)
    : 0;
}

function countBy(values: Iterable<string>): Record<string, number> {
  const counts: Record<string, number> = {};

  for (const value of values) {
    counts[value] = (counts[value] ?? 0) + 1;
  }

  return counts;
}

async function buildSessionStatsFallback(sessionId: string): Promise<JsonObject> {
  const [sessions, windows, elements] = await Promise.all([
    apiRequest<Array<JsonObject>>("/sessions"),
    apiRequest<Array<JsonObject>>(
      `/windows?session_id=${encodeURIComponent(sessionId)}`,
    ),
    apiRequest<Array<JsonObject>>("/elements"),
  ]);

  const session = sessions.find(
    (candidate) => typeof candidate.id === "string" && candidate.id === sessionId,
  );

  if (!session) {
    throw new ToolInputError(`Session not found: ${sessionId}`);
  }

  const windowIds = new Set(
    windows
      .map((window) => window.id)
      .filter((windowId): windowId is string => typeof windowId === "string"),
  );
  const sessionElements = elements.filter(
    (element) =>
      typeof element.window_id === "string" && windowIds.has(element.window_id),
  );

  return {
    session_id: sessionId,
    session_name: typeof session.name === "string" ? session.name : null,
    session_status: typeof session.status === "string" ? session.status : null,
    window_count: windows.length,
    element_count: sessionElements.length,
    total_token_count: sessionElements.reduce(
      (sum, element) => sum + toNonNegativeInteger(element.token_count),
      0,
    ),
    elements_by_role: countBy(
      sessionElements
        .map((element) => element.role)
        .filter((role): role is string => typeof role === "string"),
    ),
  };
}

async function buildGlobalStats(): Promise<JsonObject> {
  const [sessions, windows, elements] = await Promise.all([
    apiRequest<Array<JsonObject>>("/sessions"),
    apiRequest<Array<JsonObject>>("/windows"),
    apiRequest<Array<JsonObject>>("/elements"),
  ]);

  return {
    session_count: sessions.length,
    active_session_count: sessions.filter(
      (session) => session.status === "active",
    ).length,
    archived_session_count: sessions.filter(
      (session) => session.status === "archived",
    ).length,
    window_count: windows.length,
    element_count: elements.length,
    total_token_count: elements.reduce(
      (sum, element) => sum + toNonNegativeInteger(element.token_count),
      0,
    ),
    windows_by_session: countBy(
      windows
        .map((window) => window.session_id)
        .filter((sessionId): sessionId is string => typeof sessionId === "string"),
    ),
    elements_by_role: countBy(
      elements
        .map((element) => element.role)
        .filter((role): role is string => typeof role === "string"),
    ),
  };
}

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
      try {
        return {
          content: [{ type: "text", text: getRequiredString(args, "message") }],
        };
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "server_info",
    description: "サーバー名、バージョン、登録済みツールの一覧を返します。",
    inputSchema: {
      type: "object",
      additionalProperties: false,
    },
    handler: async () =>
      jsonResult({
        server: SERVER_INFO,
        tools: tools.map(({ name, description }) => ({
          name,
          description,
        })),
      }),
  },
  {
    name: "create_context_session",
    description: "新しいコンテキストセッションを作成します。",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "セッション名",
          minLength: 1,
        },
        description: {
          type: "string",
          description: "セッションの説明",
        },
      },
      required: ["name"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const session = await apiRequest<{ id: string }>("/sessions", {
          method: "POST",
          body: JSON.stringify({
            name: getRequiredString(args, "name"),
            description: getOptionalString(args, "description"),
          }),
        });

        return jsonResult({ session_id: session.id });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "create_context_window",
    description: "コンテキストウィンドウを作成します。",
    inputSchema: {
      type: "object",
      properties: {
        session_id: {
          type: "string",
          description: "紐づけ先のセッションID",
          minLength: 1,
        },
        max_tokens: {
          type: "integer",
          description: "ウィンドウの最大トークン数",
          minimum: 1,
        },
        reserved_tokens: {
          type: "integer",
          description: "応答用に予約しておくトークン数",
          minimum: 0,
        },
      },
      required: ["session_id"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const sessionId = getRequiredString(args, "session_id");
        const maxTokens = getOptionalPositiveInteger(args, "max_tokens");
        const reservedTokens = getOptionalNonNegativeInteger(
          args,
          "reserved_tokens",
        );

        if (
          maxTokens !== undefined &&
          reservedTokens !== undefined &&
          reservedTokens > maxTokens
        ) {
          throw new ToolInputError(
            'The "reserved_tokens" argument must be less than or equal to "max_tokens".',
          );
        }

        const window = await apiRequest<{ id: string }>("/windows", {
          method: "POST",
          body: JSON.stringify({
            session_id: sessionId,
            name: DEFAULT_WINDOW_NAME,
            provider: DEFAULT_WINDOW_PROVIDER,
            model: DEFAULT_WINDOW_MODEL,
            token_limit: maxTokens ?? DEFAULT_WINDOW_TOKEN_LIMIT,
            max_tokens: maxTokens,
            reserved_tokens: reservedTokens,
          }),
        });

        return jsonResult({ window_id: window.id });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "add_context_element",
    description: "コンテキストウィンドウに要素を追加します。",
    inputSchema: {
      type: "object",
      properties: {
        window_id: {
          type: "string",
          description: "追加先のウィンドウID",
          minLength: 1,
        },
        role: {
          type: "string",
          description: "要素のロール",
          enum: [...CONTEXT_ROLES],
        },
        content: {
          type: "string",
          description: "要素の本文",
          minLength: 1,
        },
        priority: {
          type: "number",
          description: "任意の優先度",
        },
      },
      required: ["window_id", "role", "content"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const priority = getOptionalNumber(args, "priority");
        const metadata = priority === undefined ? {} : { priority };
        const element = await apiRequest<{ id: string }>("/elements", {
          method: "POST",
          body: JSON.stringify({
            window_id: getRequiredString(args, "window_id"),
            role: getRequiredRole(args, "role"),
            content: getRequiredString(args, "content"),
            token_count: 0,
            metadata,
          }),
        });

        return jsonResult({ element_id: element.id });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "get_context_window",
    description: "コンテキストウィンドウとその要素一覧を取得します。",
    inputSchema: {
      type: "object",
      properties: {
        window_id: {
          type: "string",
          description: "取得対象のウィンドウID",
          minLength: 1,
        },
      },
      required: ["window_id"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const windowId = getRequiredString(args, "window_id");
        const [window, elements] = await Promise.all([
          apiRequest<JsonObject>(`/windows/${encodeURIComponent(windowId)}`),
          apiRequest<Array<JsonObject>>(
            `/elements?window_id=${encodeURIComponent(windowId)}`,
          ),
        ]);

        return jsonResult({ window, elements });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "analyze_context",
    description: "コンテキストウィンドウを解析し、分析結果を返します。",
    inputSchema: {
      type: "object",
      properties: {
        window_id: {
          type: "string",
          description: "解析対象のウィンドウID",
          minLength: 1,
        },
      },
      required: ["window_id"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const windowId = getRequiredString(args, "window_id");
        const analysis = await apiRequest<JsonObject>(
          `/windows/${encodeURIComponent(windowId)}/analyze`,
          {
            method: "POST",
          },
        );

        return jsonResult({ analysis });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "get_context_stats",
    description: "コンテキスト統計情報を取得します。",
    inputSchema: {
      type: "object",
      properties: {
        session_id: {
          type: "string",
          description: "対象セッションID。未指定時は全体統計を返します。",
          minLength: 1,
        },
      },
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const sessionId = getOptionalString(args, "session_id")?.trim();

        if (sessionId) {
          try {
            const stats = await apiRequest<JsonObject>(
              `/sessions/${encodeURIComponent(sessionId)}/stats`,
            );
            return jsonResult({ stats });
          } catch (error) {
            if (!(error instanceof ApiError) || error.status !== 404) {
              throw error;
            }

            const stats = await buildSessionStatsFallback(sessionId);
            return jsonResult({ stats });
          }
        }

        return jsonResult({ stats: await buildGlobalStats() });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  // Template Tools (MCP-04)
  {
    name: "create_prompt_template",
    description: "新しいプロンプトテンプレートを作成します。変数は {{variable_name}} 形式で記述してください。",
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "テンプレート名",
          minLength: 1,
        },
        description: {
          type: "string",
          description: "テンプレートの説明",
        },
        content: {
          type: "string",
          description: "テンプレートの内容。{{variable}} 形式で変数を定義",
          minLength: 1,
        },
        category: {
          type: "string",
          description: "カテゴリID (general, coding, writing, analysis, creative)",
        },
        tags: {
          type: "array",
          items: { type: "string" },
          description: "タグ一覧",
        },
      },
      required: ["name", "content"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const now = new Date().toISOString();
        const content = getRequiredString(args, "content");
        const variables = extractVariables(content);

        const template: PromptTemplate = {
          id: generateId(),
          name: getRequiredString(args, "name"),
          description: getOptionalString(args, "description") ?? "",
          content,
          variables,
          category: getOptionalString(args, "category") ?? "general",
          tags: getOptionalStringArray(args, "tags") ?? [],
          created_at: now,
          updated_at: now,
        };

        templateStorage.set(template.id, template);

        return jsonResult({
          template_id: template.id,
          name: template.name,
          variables: template.variables,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "generate_prompt_template",
    description: "AIを使用してプロンプトテンプレートを生成します。目的と要件を説明してください。",
    inputSchema: {
      type: "object",
      properties: {
        purpose: {
          type: "string",
          description: "テンプレートの目的（例: コードレビュー、要約、翻訳）",
          minLength: 1,
        },
        requirements: {
          type: "string",
          description: "追加要件の説明",
        },
        category: {
          type: "string",
          description: "カテゴリID",
        },
      },
      required: ["purpose"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const purpose = getRequiredString(args, "purpose");
        const requirements = getOptionalString(args, "requirements");
        const category = getOptionalString(args, "category") ?? "general";

        // Generate template content based on purpose
        let templateContent = "";
        const variables: string[] = [];

        if (purpose.toLowerCase().includes("review") || purpose.toLowerCase().includes("レビュー")) {
          templateContent = `以下のコードをレビューしてください:\n\n\`\`\`{{language}}\n{{code}}\n\`\`\`\n\nレビュー観点: {{focus_areas}}`;
          variables.push("language", "code", "focus_areas");
        } else if (purpose.toLowerCase().includes("summar") || purpose.toLowerCase().includes("要約")) {
          templateContent = `以下の文章を要約してください:\n\n{{text}}\n\n要約の長さ: {{length}}\n重点を置く観点: {{focus}}`;
          variables.push("text", "length", "focus");
        } else if (purpose.toLowerCase().includes("translat") || purpose.toLowerCase().includes("翻訳")) {
          templateContent = `以下のテキストを{{target_language}}に翻訳してください:\n\n{{text}}\n\n翻訳スタイル: {{style}}`;
          variables.push("target_language", "text", "style");
        } else {
          templateContent = `{{instruction}}\n\n入力:\n{{input}}\n\n出力形式: {{output_format}}`;
          variables.push("instruction", "input", "output_format");
        }

        if (requirements) {
          templateContent += `\n\n追加要件: ${requirements}`;
        }

        const now = new Date().toISOString();
        const template: PromptTemplate = {
          id: generateId(),
          name: `${purpose} テンプレート`,
          description: `${purpose}のためのテンプレート${requirements ? ` (${requirements})` : ""}`,
          content: templateContent,
          variables,
          category,
          tags: [purpose.toLowerCase().replace(/\s+/g, "-")],
          created_at: now,
          updated_at: now,
        };

        templateStorage.set(template.id, template);

        return jsonResult({
          template_id: template.id,
          name: template.name,
          content: templateContent,
          variables,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "list_prompt_templates",
    description: "プロンプトテンプレートの一覧を取得します。カテゴリやタグでフィルタリング可能です。",
    inputSchema: {
      type: "object",
      properties: {
        category: {
          type: "string",
          description: "カテゴリでフィルタ",
        },
        tags: {
          type: "array",
          items: { type: "string" },
          description: "タグでフィルタ（OR条件）",
        },
        limit: {
          type: "integer",
          description: "取得件数の上限",
          minimum: 1,
          maximum: 100,
        },
      },
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const categoryFilter = getOptionalString(args, "category");
        const tagFilters = getOptionalStringArray(args, "tags");
        const limit = getOptionalPositiveInteger(args, "limit") ?? 50;

        let templates = Array.from(templateStorage.values());

        if (categoryFilter) {
          templates = templates.filter((t) => t.category === categoryFilter);
        }

        if (tagFilters && tagFilters.length > 0) {
          templates = templates.filter((t) =>
            tagFilters.some((tag) => t.tags.includes(tag)),
          );
        }

        templates = templates.slice(0, limit);

        return jsonResult({
          templates: templates.map((t) => ({
            id: t.id,
            name: t.name,
            description: t.description,
            category: t.category,
            variables: t.variables,
            tags: t.tags,
          })),
          total: templates.length,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "render_template",
    description: "テンプレートに変数を埋め込んでレンダリングします。",
    inputSchema: {
      type: "object",
      properties: {
        template_id: {
          type: "string",
          description: "テンプレートID",
          minLength: 1,
        },
        variables: {
          type: "object",
          description: "埋め込む変数のキーと値",
          additionalProperties: { type: "string" },
        },
      },
      required: ["template_id"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const templateId = getRequiredString(args, "template_id");
        const template = templateStorage.get(templateId);

        if (!template) {
          throw new ToolInputError(`Template not found: ${templateId}`);
        }

        const variables = args.variables as Record<string, string> | undefined;
        const rendered = renderTemplateContent(
          template.content,
          variables ?? {},
        );

        const missingVariables = template.variables.filter(
          (v) => !variables || !variables[v],
        );

        return jsonResult({
          rendered,
          template_name: template.name,
          missing_variables: missingVariables.length > 0 ? missingVariables : undefined,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "get_template_recommendations",
    description: "ユーザーの目的に基づいて最適なテンプレートを推奨します。",
    inputSchema: {
      type: "object",
      properties: {
        context: {
          type: "string",
          description: "現在のコンテキストや目的の説明",
          minLength: 1,
        },
        max_results: {
          type: "integer",
          description: "推奨数の上限",
          minimum: 1,
          maximum: 10,
        },
      },
      required: ["context"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const context = getRequiredString(args, "context").toLowerCase();
        const maxResults = getOptionalPositiveInteger(args, "max_results") ?? 5;

        const allTemplates = Array.from(templateStorage.values());

        // Score templates based on context match
        const scoredTemplates = allTemplates.map((t) => {
          let score = 0;
          const searchText = `${t.name} ${t.description} ${t.tags.join(" ")}`.toLowerCase();

          // Check keyword matches
          const keywords = context.split(/\s+/);
          for (const keyword of keywords) {
            if (searchText.includes(keyword)) score += 1;
            if (t.category.toLowerCase().includes(keyword)) score += 2;
            if (t.tags.some((tag) => tag.includes(keyword))) score += 2;
          }

          return { template: t, score };
        });

        // Sort by score and return top results
        const recommendations = scoredTemplates
          .filter((item) => item.score > 0)
          .sort((a, b) => b.score - a.score)
          .slice(0, maxResults)
          .map((item) => ({
            id: item.template.id,
            name: item.template.name,
            description: item.template.description,
            category: item.template.category,
            relevance_score: item.score,
          }));

        return jsonResult({
          recommendations,
          context_analyzed: context,
          total_templates_available: allTemplates.length,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "browse_template_categories",
    description: "テンプレートカテゴリ一覧を参照します。",
    inputSchema: {
      type: "object",
      properties: {
        include_templates: {
          type: "boolean",
          description: "各カテゴリのテンプレート一覧も含める",
        },
      },
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const includeTemplates = args.include_templates === true;

        const categoriesWithCount = templateCategories.map((cat) => {
          const templates = Array.from(templateStorage.values()).filter(
            (t) => t.category === cat.id,
          );

          return {
            ...cat,
            template_count: templates.length,
            templates: includeTemplates
              ? templates.map((t) => ({
                  id: t.id,
                  name: t.name,
                  description: t.description,
                  variables: t.variables,
                }))
              : undefined,
          };
        });

        return jsonResult({
          categories: categoriesWithCount,
          total_templates: templateStorage.size,
        });
      } catch (error) {
        return errorResult(error);
      }
    },
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
    return errorResult(new ToolInputError(`Unknown tool: ${request.params.name}`));
  }

  return tool.handler((request.params.arguments ?? {}) as JsonObject);
});

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`${SERVER_INFO.name} server running on stdio`);
}

main().catch((error) => {
  console.error("Failed to start MCP server:", error);
  process.exit(1);
});
