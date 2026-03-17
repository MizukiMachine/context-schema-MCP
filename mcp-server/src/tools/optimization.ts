import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

type JsonObject = Record<string, unknown>;
type ToolHandler = (args: JsonObject) => Promise<CallToolResult>;

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: JsonObject;
  handler: ToolHandler;
}

const OPTIMIZATION_STRATEGIES = [
  "token_reduction",
  "clarity_improvement",
  "redundancy_removal",
  "structure_optimization",
] as const;

type OptimizationStrategy = (typeof OPTIMIZATION_STRATEGIES)[number];
type OptimizationTaskState = "pending" | "in_progress" | "completed" | "failed";

export interface OptimizationOptions {
  strategy?: OptimizationStrategy;
  targetLength?: number;
  aggressive?: boolean;
  preserveKeywords?: string[];
}

export interface OptimizationResult {
  taskId: string;
  status: "completed";
  strategyUsed: OptimizationStrategy;
  originalText: string;
  optimizedText: string;
  originalTokenCount: number;
  optimizedTokenCount: number;
  tokenSavings: number;
  tokenReductionRatio: number;
  suggestions: string[];
}

export interface OptimizationStatus {
  taskId: string;
  status: OptimizationTaskState;
  progress: number;
  currentStep: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  strategyUsed?: OptimizationStrategy;
  result?: OptimizationResult;
  errorMessage?: string;
}

type OptimizationTaskRecord = OptimizationStatus;

interface TextAnalysis {
  segments: string[];
  uniqueSegments: string[];
  estimatedTokens: number;
  duplicateRatio: number;
  averageSegmentLength: number;
  lineCount: number;
}

const optimizationTasks = new Map<string, OptimizationTaskRecord>();

function jsonResult(payload: object): CallToolResult {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
    structuredContent: payload as Record<string, unknown>,
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

class ToolInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ToolInputError";
  }
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

function getOptionalBoolean(args: JsonObject, key: string): boolean | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (typeof value !== "boolean") {
    throw new ToolInputError(`The "${key}" argument must be a boolean.`);
  }

  return value;
}

function getOptionalPositiveInteger(
  args: JsonObject,
  key: string,
): number | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (typeof value !== "number" || !Number.isInteger(value) || value < 1) {
    throw new ToolInputError(`The "${key}" argument must be a positive integer.`);
  }

  return value;
}

function getOptionalStringArray(args: JsonObject, key: string): string[] | undefined {
  const value = args[key];
  if (value === undefined) {
    return undefined;
  }

  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new ToolInputError(`The "${key}" argument must be an array of strings.`);
  }

  return value
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function parseStrategy(value: unknown, key: string): OptimizationStrategy | undefined {
  if (value === undefined) {
    return undefined;
  }

  if (
    typeof value !== "string" ||
    !OPTIMIZATION_STRATEGIES.includes(value as OptimizationStrategy)
  ) {
    throw new ToolInputError(
      `The "${key}" argument must be one of: ${OPTIMIZATION_STRATEGIES.join(", ")}.`,
    );
  }

  return value as OptimizationStrategy;
}

function parseOptimizationOptions(args: JsonObject): OptimizationOptions | undefined {
  const rawOptions = args.options;
  if (rawOptions === undefined) {
    return undefined;
  }

  if (!isRecord(rawOptions)) {
    throw new ToolInputError('The "options" argument must be an object.');
  }

  const allowedKeys = new Set([
    "strategy",
    "targetLength",
    "aggressive",
    "preserveKeywords",
  ]);

  for (const key of Object.keys(rawOptions)) {
    if (!allowedKeys.has(key)) {
      throw new ToolInputError(`Unknown optimization option: ${key}`);
    }
  }

  return {
    strategy: parseStrategy(rawOptions.strategy, "options.strategy"),
    targetLength: getOptionalPositiveInteger(rawOptions, "targetLength"),
    aggressive: getOptionalBoolean(rawOptions, "aggressive"),
    preserveKeywords: getOptionalStringArray(rawOptions, "preserveKeywords"),
  };
}

function createTaskId(): string {
  return `opt_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function createTaskRecord(): OptimizationTaskRecord {
  const now = new Date().toISOString();
  return {
    taskId: createTaskId(),
    status: "pending",
    progress: 0,
    currentStep: "queued",
    createdAt: now,
  };
}

function updateTask(
  taskId: string,
  patch: Partial<OptimizationTaskRecord>,
): OptimizationTaskRecord {
  const current = optimizationTasks.get(taskId);
  if (!current) {
    throw new ToolInputError(`Optimization task not found: ${taskId}`);
  }

  const next = { ...current, ...patch };
  optimizationTasks.set(taskId, next);
  return next;
}

function estimateTokenCount(text: string): number {
  const normalized = text.trim();
  if (normalized.length === 0) {
    return 0;
  }

  return Math.max(1, Math.ceil(normalized.length / 4));
}

function normalizeWhitespace(text: string): string {
  return text.replace(/\r\n/g, "\n").replace(/[ \t]+/g, " ").trim();
}

function normalizeSentence(sentence: string): string {
  return normalizeWhitespace(sentence)
    .replace(/\s+([,.;!?])/g, "$1")
    .replace(/\(\s+/g, "(")
    .replace(/\s+\)/g, ")");
}

function splitSegments(text: string): string[] {
  const normalized = text.replace(/\r\n/g, "\n").trim();
  if (normalized.length === 0) {
    return [];
  }

  const lineSegments = normalized
    .split(/\n+/)
    .map((segment) => normalizeSentence(segment))
    .filter((segment) => segment.length > 0);

  if (lineSegments.length > 1) {
    return lineSegments;
  }

  return (normalized.match(/[^.!?。！？\n]+[.!?。！？]?/g) ?? [normalized])
    .map((segment) => normalizeSentence(segment))
    .filter((segment) => segment.length > 0);
}

function normalizeComparisonKey(text: string): string {
  return text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
}

function dedupeSegments(segments: string[]): string[] {
  const seen = new Set<string>();
  const unique: string[] = [];

  for (const segment of segments) {
    const key = normalizeComparisonKey(segment);
    if (!key || seen.has(key)) {
      continue;
    }
    seen.add(key);
    unique.push(segment);
  }

  return unique;
}

function analyzeText(input: string): TextAnalysis {
  const segments = splitSegments(input);
  const uniqueSegments = dedupeSegments(segments);
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0);

  return {
    segments,
    uniqueSegments,
    estimatedTokens: estimateTokenCount(input),
    duplicateRatio:
      segments.length === 0 ? 0 : (segments.length - uniqueSegments.length) / segments.length,
    averageSegmentLength:
      segments.length === 0 ? 0 : totalLength / segments.length,
    lineCount: input.split(/\n/).length,
  };
}

function removeFillerPhrases(text: string, aggressive: boolean): string {
  const fillerPatterns = [
    /\b(?:really|very|basically|actually|simply|just)\b/gi,
    /\b(?:kind of|sort of)\b/gi,
    /\b(?:please note that|it is important to note that)\b/gi,
  ];

  let next = text;
  for (const pattern of fillerPatterns) {
    next = next.replace(pattern, "");
  }

  if (aggressive) {
    next = next.replace(/\([^)]*\)/g, "");
  }

  return normalizeSentence(next).replace(/\s{2,}/g, " ").trim();
}

function prioritizeSegments(
  segments: string[],
  preserveKeywords: string[],
): string[] {
  if (preserveKeywords.length === 0) {
    return segments;
  }

  const loweredKeywords = preserveKeywords.map((keyword) => keyword.toLowerCase());
  const scored = segments.map((segment, index) => {
    const loweredSegment = segment.toLowerCase();
    const score = loweredKeywords.reduce(
      (sum, keyword) => sum + (loweredSegment.includes(keyword) ? 1 : 0),
      0,
    );

    return { index, segment, score };
  });

  return scored
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .map((entry) => entry.segment);
}

function enforceTargetLength(
  text: string,
  targetLength: number | undefined,
  preserveKeywords: string[],
): string {
  if (targetLength === undefined || estimateTokenCount(text) <= targetLength) {
    return text;
  }

  const prioritized = prioritizeSegments(splitSegments(text), preserveKeywords);
  const selected: string[] = [];

  for (const segment of prioritized) {
    const candidate = [...selected, segment].join(" ");
    if (selected.length > 0 && estimateTokenCount(candidate) > targetLength) {
      continue;
    }
    selected.push(segment);
    if (estimateTokenCount(selected.join(" ")) >= targetLength) {
      break;
    }
  }

  const compact = normalizeSentence(selected.join(" "));
  if (compact.length > 0) {
    return compact;
  }

  const roughCharacterLimit = targetLength * 4;
  return normalizeSentence(text.slice(0, roughCharacterLimit)).trim();
}

function applyTokenReduction(input: string, options: OptimizationOptions): string {
  const aggressive = options.aggressive === true;
  const cleaned = splitSegments(input).map((segment) =>
    removeFillerPhrases(segment, aggressive),
  );
  const uniqueSegments = aggressive ? dedupeSegments(cleaned) : cleaned;
  const maxSegments = aggressive ? 3 : 5;
  const reduced = uniqueSegments.slice(0, maxSegments).join(" ");

  return enforceTargetLength(
    normalizeSentence(reduced),
    options.targetLength,
    options.preserveKeywords ?? [],
  );
}

function applyRedundancyRemoval(input: string, options: OptimizationOptions): string {
  const cleaned = splitSegments(input).map((segment) =>
    removeFillerPhrases(segment, options.aggressive === true),
  );
  const uniqueSegments = dedupeSegments(cleaned);
  const joined =
    input.includes("\n") || uniqueSegments.length > 1
      ? uniqueSegments.join("\n")
      : (uniqueSegments[0] ?? "");

  return enforceTargetLength(
    normalizeSentence(joined),
    options.targetLength,
    options.preserveKeywords ?? [],
  );
}

function applyClarityImprovement(input: string, options: OptimizationOptions): string {
  const cleaned = dedupeSegments(
    splitSegments(input).map((segment) =>
      removeFillerPhrases(segment, options.aggressive === true),
    ),
  );

  if (cleaned.length <= 1) {
    return enforceTargetLength(
      cleaned[0] ?? "",
      options.targetLength,
      options.preserveKeywords ?? [],
    );
  }

  const bullets = cleaned.map((segment) => `- ${segment}`);
  return enforceTargetLength(
    bullets.join("\n"),
    options.targetLength,
    options.preserveKeywords ?? [],
  );
}

function applyStructureOptimization(input: string, options: OptimizationOptions): string {
  const cleaned = dedupeSegments(
    splitSegments(input).map((segment) =>
      removeFillerPhrases(segment, options.aggressive === true),
    ),
  );

  if (cleaned.length === 0) {
    return "";
  }

  const [headline, ...rest] = cleaned;
  const detailLimit = options.aggressive === true ? 4 : 6;
  const details = rest.slice(0, detailLimit).map((segment) => `- ${segment}`);
  const structured = details.length === 0
    ? `Summary: ${headline}`
    : [`Summary: ${headline}`, "Details:", ...details].join("\n");

  return enforceTargetLength(
    structured,
    options.targetLength,
    options.preserveKeywords ?? [],
  );
}

function chooseAutomaticStrategy(analysis: TextAnalysis): OptimizationStrategy {
  if (analysis.duplicateRatio >= 0.25) {
    return "redundancy_removal";
  }

  if (analysis.estimatedTokens >= 180) {
    return "token_reduction";
  }

  if (analysis.lineCount >= 4 || analysis.segments.length >= 5) {
    return "structure_optimization";
  }

  if (analysis.averageSegmentLength >= 120) {
    return "clarity_improvement";
  }

  return "clarity_improvement";
}

function optimizeText(
  input: string,
  strategy: OptimizationStrategy,
  options: OptimizationOptions,
): string {
  switch (strategy) {
    case "token_reduction":
      return applyTokenReduction(input, options);
    case "clarity_improvement":
      return applyClarityImprovement(input, options);
    case "redundancy_removal":
      return applyRedundancyRemoval(input, options);
    case "structure_optimization":
      return applyStructureOptimization(input, options);
  }
}

function buildSuggestions(
  strategy: OptimizationStrategy,
  analysis: TextAnalysis,
  result: OptimizationResult,
): string[] {
  const suggestions: string[] = [];

  if (strategy === "token_reduction") {
    suggestions.push("不要な修飾語を削減し、先頭の重要文を優先して保持しました。");
  }

  if (strategy === "redundancy_removal" && analysis.duplicateRatio > 0) {
    suggestions.push("重複表現を除去し、同義の繰り返しを抑えました。");
  }

  if (strategy === "clarity_improvement") {
    suggestions.push("長文を分割し、読みやすい箇条書きへ再構成しました。");
  }

  if (strategy === "structure_optimization") {
    suggestions.push("要約と詳細に分離し、参照しやすい構造へ整理しました。");
  }

  if (result.tokenSavings > 0) {
    suggestions.push(
      `推定 ${result.tokenSavings} トークンを削減しました。`,
    );
  }

  if (suggestions.length === 0) {
    suggestions.push("表現を整形し、利用しやすい形に調整しました。");
  }

  return suggestions;
}

function buildOptimizationResult(
  taskId: string,
  input: string,
  optimizedText: string,
  strategy: OptimizationStrategy,
  analysis: TextAnalysis,
): OptimizationResult {
  const originalTokenCount = analysis.estimatedTokens;
  const optimizedTokenCount = estimateTokenCount(optimizedText);
  const tokenSavings = Math.max(0, originalTokenCount - optimizedTokenCount);
  const tokenReductionRatio =
    originalTokenCount === 0 ? 0 : tokenSavings / originalTokenCount;

  const result: OptimizationResult = {
    taskId,
    status: "completed",
    strategyUsed: strategy,
    originalText: input,
    optimizedText,
    originalTokenCount,
    optimizedTokenCount,
    tokenSavings,
    tokenReductionRatio: Number(tokenReductionRatio.toFixed(3)),
    suggestions: [],
  };

  result.suggestions = buildSuggestions(strategy, analysis, result);
  return result;
}

async function executeOptimization(
  input: string,
  options: OptimizationOptions | undefined,
  mode: "manual" | "auto",
): Promise<OptimizationResult> {
  const task = createTaskRecord();
  optimizationTasks.set(task.taskId, task);

  try {
    updateTask(task.taskId, {
      status: "in_progress",
      progress: 0.2,
      currentStep: "analyzing_input",
      startedAt: new Date().toISOString(),
    });

    const normalizedInput = normalizeWhitespace(input);
    const analysis = analyzeText(normalizedInput);
    const strategy =
      mode === "auto"
        ? chooseAutomaticStrategy(analysis)
        : options?.strategy ?? "token_reduction";

    updateTask(task.taskId, {
      status: "in_progress",
      progress: 0.55,
      currentStep: "optimizing_context",
      strategyUsed: strategy,
    });

    const optimizedText = optimizeText(normalizedInput, strategy, options ?? {});
    const result = buildOptimizationResult(
      task.taskId,
      normalizedInput,
      optimizedText.length > 0 ? optimizedText : normalizedInput,
      strategy,
      analysis,
    );

    updateTask(task.taskId, {
      status: "completed",
      progress: 1,
      currentStep: "completed",
      completedAt: new Date().toISOString(),
      strategyUsed: strategy,
      result,
    });

    return result;
  } catch (error) {
    updateTask(task.taskId, {
      status: "failed",
      progress: 1,
      currentStep: "failed",
      completedAt: new Date().toISOString(),
      errorMessage:
        error instanceof Error ? error.message : "Optimization failed unexpectedly.",
    });
    throw error;
  }
}

export const optimizationTools: ToolDefinition[] = [
  {
    name: "optimize_context",
    description:
      "コンテキスト文字列を指定した戦略で手動最適化します。戦略・目標長・キーワード保持を指定できます。",
    inputSchema: {
      type: "object",
      properties: {
        input: {
          type: "string",
          description: "最適化対象のコンテキスト文字列",
          minLength: 1,
        },
        options: {
          type: "object",
          description: "手動最適化オプション",
          properties: {
            strategy: {
              type: "string",
              enum: [...OPTIMIZATION_STRATEGIES],
              description: "適用する最適化戦略",
            },
            targetLength: {
              type: "integer",
              minimum: 1,
              description: "目標とする推定トークン数",
            },
            aggressive: {
              type: "boolean",
              description: "より強めの圧縮を行うかどうか",
            },
            preserveKeywords: {
              type: "array",
              items: { type: "string" },
              description: "優先的に保持したいキーワード一覧",
            },
          },
          additionalProperties: false,
        },
      },
      required: ["input"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const input = getRequiredString(args, "input");
        const options = parseOptimizationOptions(args);
        return jsonResult(await executeOptimization(input, options, "manual"));
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "auto_optimize_context",
    description:
      "入力コンテキストを解析し、最も適切な戦略を自動選択して最適化します。",
    inputSchema: {
      type: "object",
      properties: {
        input: {
          type: "string",
          description: "自動最適化対象のコンテキスト文字列",
          minLength: 1,
        },
      },
      required: ["input"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const input = getRequiredString(args, "input");
        return jsonResult(await executeOptimization(input, undefined, "auto"));
      } catch (error) {
        return errorResult(error);
      }
    },
  },
  {
    name: "get_optimization_status",
    description: "最適化タスクの進行状況と結果を taskId から取得します。",
    inputSchema: {
      type: "object",
      properties: {
        taskId: {
          type: "string",
          description: "確認対象の最適化タスクID",
          minLength: 1,
        },
      },
      required: ["taskId"],
      additionalProperties: false,
    },
    handler: async (args) => {
      try {
        const taskId = getRequiredString(args, "taskId");
        const task = optimizationTasks.get(taskId);
        if (!task) {
          throw new ToolInputError(`Optimization task not found: ${taskId}`);
        }
        return jsonResult(task);
      } catch (error) {
        return errorResult(error);
      }
    },
  },
];
