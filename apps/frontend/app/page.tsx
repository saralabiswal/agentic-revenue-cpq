/**
 * Next.js client workbench for the opportunity-to-quote command center.
 *
 * @author Sarala Biswal
 */
"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Account = {
  sf_account_id: string;
  name: string;
  industry: string;
  region: string;
  segment: string;
  opportunity_count: number;
  open_pipeline: number;
};

type Opportunity = {
  sf_opportunity_id: string;
  name: string;
  stage: string;
  currency: string;
  amount: number;
  term_months: number;
  use_case: string;
  sites: number;
  region: string;
  budget: number;
  target_close_date: string;
  compliance_need: string;
  incumbent_vendor: string;
  risk_level: string;
  requirements: string[];
  account: {
    sf_account_id: string;
    name: string;
    industry: string;
    region: string;
    segment: string;
  };
};

type Product = {
  sku: string;
  name: string;
  category?: string;
  quantity: number;
  term_months: number;
  selected: boolean;
  required: boolean;
  billing_model?: string;
  reason?: string;
  rule_id?: string;
};

type LineItem = {
  sku: string;
  name: string;
  category: string;
  quantity: number;
  term_months: number;
  billing_model: string;
  annual_unit_price: number;
  net_price: number;
};

type Pricing = {
  sf_opportunity_id: string;
  currency: string;
  line_items: LineItem[];
  subtotal: number;
  discount: number;
  discount_percent: number;
  discounts: Array<{
    code: string;
    label: string;
    percent: number;
    amount: number;
  }>;
  total: number;
};

type RunStep = {
  id: string;
  label: string;
  layer: string;
  status: string;
  detail: string;
};

type QuoteRecord = {
  oracle_quote_id: string;
  sf_opportunity_id: string;
  status: string;
  currency: string;
  subtotal: number;
  discount: number;
  discount_percent: number;
  total: number;
  selected_product_count: number;
  created_at?: string;
  accepted_at?: string;
  line_items?: LineItem[];
};

type OrderRecord = {
  oracle_order_id: string;
  oracle_quote_id: string;
  sf_opportunity_id: string;
  status: string;
  currency: string;
  total: number;
  placed_at?: string;
  line_items?: LineItem[];
};

type ActivityEvent = {
  activity_id: string;
  sf_account_id?: string;
  sf_opportunity_id?: string;
  oracle_quote_id?: string;
  oracle_order_id?: string;
  system: string;
  event_type: string;
  title: string;
  detail: string;
  created_at: string;
};

type RecommendationResponse = {
  status: string;
  message: string;
  opportunity: Opportunity;
  products: Product[];
  pricing: Pricing;
  retrieved_context: string[];
  run_steps: RunStep[];
};

type PricingResponse = {
  status: string;
  products: Product[];
  pricing: Pricing;
  run_steps: RunStep[];
};

type QuoteCreateResponse = {
  status: string;
  message: string;
  oracle_quote_id: string;
  quote: QuoteRecord;
  products: Product[];
  pricing: Pricing;
  run_steps: RunStep[];
};

type QuoteFinalizeResponse = {
  status: string;
  quote: QuoteRecord;
  order: OrderRecord;
};

type TraceStep = {
  label: string;
  layer: string;
  system: string;
  status: "completed" | "active" | "pending";
  detail: string;
  input: unknown;
  output: unknown;
};

type CommandIntent = "recommend" | "create_quote" | "create_order" | null;

type CommandSource = "auto" | "manual";

type ViewMode = "business" | "architecture" | "developer";

type RuntimeProfileSummary = {
  runtime_profile: string;
  agent_orchestration: string;
  llm: string;
  embeddings: string;
  vector_store: string;
  business_store: string;
  object_store: string;
  secrets: string;
  observability: string;
};

type RuntimeProfile = {
  platform_profile: string;
  display_name: string;
  agent_orchestrator: string;
  llm_provider: string;
  embedding_provider: string;
  vector_store_provider: string;
  business_store_provider: string;
  object_store_provider: string;
  secrets_provider: string;
  observability_provider: string;
  editable_in_ui: false;
  summary: RuntimeProfileSummary;
  profiles: Record<string, RuntimeProfileSummary>;
};

type SuggestedCommand = {
  text: string;
  intent: CommandIntent;
};

type AgentActionKind = "recommend" | "quote" | "order";

type ArchitectureActionKind = AgentActionKind | "ready";

type DeveloperFlowKey =
  | "recommend"
  | "rag"
  | "backend"
  | "langgraph"
  | "mcp"
  | "integrations"
  | "data"
  | "llm"
  | "providers";

type AgentActionState = {
  kind: AgentActionKind;
  title: string;
  summary: string;
  timestamp: string;
};

type SignalGroup = {
  label: string;
  summary: string;
  signals: string[];
};

type WorkbenchStep = {
  name: string;
  detail: string;
  status: "completed" | "active" | "pending";
};

type AgentWorkbenchKind = AgentActionKind | "ready";

type AgentWorkbenchModel = {
  kind: AgentWorkbenchKind;
  title: string;
  subtitle: string;
  summary: string;
  systems: string;
  systemDetail: string;
  output: string;
  outputDetail: string;
  contextTitle: string;
  steps: WorkbenchStep[];
};

const defaultCommand =
  "Recommend NetApp-aligned products for this telecom opportunity, prepare pricing, and explain the quote path.";

const COMMAND_OPTIONS: {
  intent: Exclude<CommandIntent, null>;
  text: string;
  label: string;
  description: string;
}[] = [
  {
    intent: "recommend",
    text: "Recommend Product",
    label: "Recommend Product",
    description: "Find products and pricing for the selected opportunity.",
  },
  {
    intent: "create_quote",
    text: "Create quote",
    label: "Create Quote",
    description: "Create an Oracle CPQ quote from selected products.",
  },
  {
    intent: "create_order",
    text: "Create order",
    label: "Create Order",
    description: "Finalize the accepted quote into an order.",
  },
];

/** Render the command center and coordinate account, opportunity, recommendation, quote, and order state. */
export default function Home() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selectedSfAccountId, setSelectedSfAccountId] = useState("");
  const [expandedSfAccountId, setExpandedSfAccountId] = useState("");
  const [selectedSfOpportunityId, setSelectedSfOpportunityId] = useState("");
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [command, setCommand] = useState(defaultCommand);
  const [commandSource, setCommandSource] = useState<CommandSource>("auto");
  const [commandNotice, setCommandNotice] = useState("");
  const [agentAction, setAgentAction] = useState<AgentActionState | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [pricing, setPricing] = useState<Pricing | null>(null);
  const [recommendationMessage, setRecommendationMessage] = useState("");
  const [retrievedContext, setRetrievedContext] = useState<string[]>([]);
  const [runSteps, setRunSteps] = useState<RunStep[]>([]);
  const [quotes, setQuotes] = useState<QuoteRecord[]>([]);
  const [latestQuote, setLatestQuote] = useState<QuoteRecord | null>(null);
  const [order, setOrder] = useState<OrderRecord | null>(null);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [runtimeProfile, setRuntimeProfile] = useState<RuntimeProfile | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("business");
  const [developerFlow, setDeveloperFlow] = useState<DeveloperFlowKey>("data");
  const [status, setStatus] = useState<
    "idle" | "loading" | "running" | "pricing" | "quoting" | "finalizing"
  >("idle");
  const [error, setError] = useState<string | null>(null);

  const isBusy = status !== "idle";
  const selectedProducts = useMemo(
    () => products.filter((product) => product.selected),
    [products],
  );
  const selectedAccount = useMemo(
    () => accounts.find((account) => account.sf_account_id === selectedSfAccountId) ?? null,
    [accounts, selectedSfAccountId],
  );
  const lineItemBySku = useMemo(() => {
    const entries = pricing?.line_items.map((item) => [item.sku, item] as const) ?? [];
    return new Map(entries);
  }, [pricing]);
  const finalizableQuote = useMemo(
    () =>
      (latestQuote && isFinalizableQuote(latestQuote) ? latestQuote : null) ??
      [...quotes].reverse().find(isFinalizableQuote) ??
      null,
    [latestQuote, quotes],
  );
  const nextBestAction = useMemo(
    () =>
      buildNextBestAction({
        finalizableQuote,
        opportunity,
        order,
        products,
        selectedProducts,
      }),
    [finalizableQuote, opportunity, order, products, selectedProducts],
  );
  const suggestedCommand = useMemo(
    () =>
      buildSuggestedCommand({
        finalizableQuote,
        opportunity,
        order,
        products,
        selectedProducts,
      }),
    [finalizableQuote, opportunity, order, products, selectedProducts],
  );
  const commandIntent = resolveCommandIntent(command);
  const effectiveCommandIntent =
    commandIntent ?? (commandSource === "auto" ? suggestedCommand.intent : null);
  const traceSteps = useMemo(
    () =>
      buildTraceSteps({
        activity,
        command,
        opportunity,
        order,
        pricing,
        products,
        quotes,
        retrievedContext,
        runSteps,
        selectedAccount,
        selectedProducts,
      }),
    [
      activity,
      command,
      opportunity,
      order,
      pricing,
      products,
      quotes,
      retrievedContext,
      runSteps,
      selectedAccount,
      selectedProducts,
    ],
  );
  const architectureAction = resolveActiveAgentAction({
    action: agentAction,
    latestQuote,
    order,
    products,
  });

  const headline = order
    ? "Order placed"
    : latestQuote
      ? "Quote version created"
      : products.length
        ? "Ready for quote review"
        : isBusy
          ? "Agent running"
          : "Ready";

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (commandSource !== "auto" || command === suggestedCommand.text) {
      return;
    }

    setCommand(suggestedCommand.text);
  }, [command, commandSource, suggestedCommand.text]);

  async function bootstrap() {
    setStatus("loading");
    setError(null);
    try {
      const [profileResponse, accountResponse] = await Promise.all([
        // Read provider metadata once for documentation panels. The UI never
        // mutates runtime provider selection.
        getJson<RuntimeProfile>("/runtime/profile"),
        getJson<{ accounts: Account[] }>("/accounts"),
      ]);
      setRuntimeProfile(profileResponse);
      setAccounts(accountResponse.accounts);
      const firstAccount = accountResponse.accounts[0];
      if (firstAccount) {
        await selectAccount(firstAccount.sf_account_id, false);
      }
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setStatus("idle");
    }
  }

  async function selectAccount(sfAccountId: string, clearCurrent = true) {
    setSelectedSfAccountId(sfAccountId);
    setExpandedSfAccountId(sfAccountId);
    if (clearCurrent) {
      clearRecommendationState();
    }

    const opportunityResponse = await getJson<{ opportunities: Opportunity[] }>(
      `/accounts/${encodeURIComponent(sfAccountId)}/opportunities`,
    );
    setOpportunities(opportunityResponse.opportunities);
    const firstOpportunity = opportunityResponse.opportunities[0];
    if (firstOpportunity) {
      await selectOpportunity(firstOpportunity.sf_opportunity_id, clearCurrent);
    }
  }

  async function toggleAccount(sfAccountId: string) {
    if (sfAccountId === selectedSfAccountId && sfAccountId === expandedSfAccountId) {
      setExpandedSfAccountId("");
      return;
    }

    await selectAccount(sfAccountId);
  }

  async function selectOpportunity(sfOpportunityId: string, clearCurrent = true) {
    setSelectedSfOpportunityId(sfOpportunityId);
    if (clearCurrent) {
      clearRecommendationState();
    }

    const detail = await getJson<Opportunity>(
      `/opportunities/${encodeURIComponent(sfOpportunityId)}`,
    );
    setOpportunity(detail);
    await refreshOracleAndActivity(sfOpportunityId);
  }

  async function refreshOracleAndActivity(sfOpportunityId = selectedSfOpportunityId) {
    if (!sfOpportunityId) {
      return;
    }

    const [quoteResponse, activityResponse] = await Promise.all([
      getJson<{ quotes: QuoteRecord[] }>(
        `/opportunities/${encodeURIComponent(sfOpportunityId)}/quotes`,
      ),
      getJson<{ activity: ActivityEvent[] }>(
        `/opportunities/${encodeURIComponent(sfOpportunityId)}/activity`,
      ),
    ]);
    setQuotes(quoteResponse.quotes);
    setActivity(activityResponse.activity);
  }

  function clearRecommendationState() {
    setProducts([]);
    setPricing(null);
    setRecommendationMessage("");
    setRetrievedContext([]);
    setRunSteps([]);
    setLatestQuote(null);
    setOrder(null);
    setCommandNotice("");
    setAgentAction(null);
    setCommandSource("auto");
  }

  async function runCommand() {
    if (effectiveCommandIntent === "recommend") {
      const completed = await runRecommendation();
      if (completed) {
        setCommandNotice("Recommendation is ready. Follow the next best action for this opportunity.");
      }
      return;
    }

    if (effectiveCommandIntent === "create_quote") {
      const quote = await createQuote();
      if (quote) {
        setCommandNotice(`Created ${displayRecordId(quote.oracle_quote_id)}. Next best action is Create order.`);
      }
      return;
    }

    if (effectiveCommandIntent === "create_order") {
      if (!finalizableQuote) {
        setCommandNotice("Create a draft quote first, then type Create order or use Finalize / Place Order.");
        return;
      }

      const placedOrder = await finalizeQuote(finalizableQuote.oracle_quote_id);
      if (placedOrder) {
        setCommandNotice(
          `Order ${displayRecordId(placedOrder.oracle_order_id)} placed from ${displayRecordId(placedOrder.oracle_quote_id)}.`,
        );
      }
      return;
    }

    setCommandNotice(
      "Choose Recommend Product, Create Quote, or Create Order before running the command.",
    );
  }

  async function executeCommand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runCommand();
  }

  async function runRecommendation(): Promise<boolean> {
    if (!selectedSfOpportunityId) {
      setCommandNotice("Select a Salesforce opportunity first.");
      return false;
    }

    setStatus("running");
    setError(null);
    setLatestQuote(null);
    setOrder(null);
    try {
      const response = await postJson<RecommendationResponse>(
        "/quote/recommendations",
        {
          sf_opportunity_id: selectedSfOpportunityId,
          message: buildRecommendationRequestMessage(command.trim(), opportunity),
        },
      );
      setOpportunity(response.opportunity);
      setProducts(response.products);
      setPricing(response.pricing);
      setRecommendationMessage(response.message);
      setRetrievedContext(response.retrieved_context);
      setRunSteps(response.run_steps);
      setCommandSource("auto");
      setAgentAction(
        createAgentAction(
          "recommend",
          "Recommend Product",
          `${response.products.length} recommendations grounded by ${response.retrieved_context.length} RAG snippets and priced at ${formatCurrency(response.pricing.total, response.pricing.currency)}.`,
        ),
      );
      await refreshOracleAndActivity(response.opportunity.sf_opportunity_id);
      return true;
    } catch (caught) {
      setError(errorMessage(caught));
      return false;
    } finally {
      setStatus("idle");
    }
  }

  async function updateProducts(nextProducts: Product[]) {
    setProducts(nextProducts);
    setLatestQuote(null);
    setOrder(null);
    if (!opportunity) {
      return;
    }

    setStatus("pricing");
    setError(null);
    try {
      const response = await postJson<PricingResponse>("/quote/pricing", {
        sf_opportunity_id: opportunity.sf_opportunity_id,
        currency: opportunity.currency,
        products: nextProducts,
      });
      setPricing(response.pricing);
      setRunSteps((current) => mergeRunSteps(current, response.run_steps));
      setCommandSource("auto");
      setAgentAction(
        createAgentAction(
          "recommend",
          "Recommend Product",
          `Selection updated; CPQ repriced ${response.pricing.line_items.length} selected products at ${formatCurrency(response.pricing.total, response.pricing.currency)}.`,
        ),
      );
      await refreshOracleAndActivity(opportunity.sf_opportunity_id);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setStatus("idle");
    }
  }

  async function createQuote(): Promise<QuoteRecord | null> {
    if (!opportunity || selectedProducts.length === 0) {
      setCommandNotice("Run recommendation and keep at least one product selected before creating a quote.");
      return null;
    }

    setStatus("quoting");
    setError(null);
    try {
      const response = await postJson<QuoteCreateResponse>("/quote/create", {
        sf_opportunity_id: opportunity.sf_opportunity_id,
        currency: opportunity.currency,
        products,
      });
      setLatestQuote(response.quote);
      setPricing(response.pricing);
      setRunSteps((current) => mergeRunSteps(current, response.run_steps));
      setCommandSource("auto");
      setAgentAction(
        createAgentAction(
          "quote",
          "Create Quote",
          `Created ${displayRecordId(response.quote.oracle_quote_id)} with ${response.quote.selected_product_count} selected products for ${formatCurrency(response.quote.total, response.quote.currency)}.`,
        ),
      );
      await refreshOracleAndActivity(opportunity.sf_opportunity_id);
      return response.quote;
    } catch (caught) {
      setError(errorMessage(caught));
      return null;
    } finally {
      setStatus("idle");
    }
  }

  async function finalizeQuote(oracleQuoteId: string): Promise<OrderRecord | null> {
    setStatus("finalizing");
    setError(null);
    try {
      const response = await postJson<QuoteFinalizeResponse>("/quote/finalize", {
        oracle_quote_id: oracleQuoteId,
      });
      setLatestQuote(response.quote);
      setOrder(response.order);
      setCommandSource("auto");
      setAgentAction(
        createAgentAction(
          "order",
          "Create Order",
          `Placed ${displayRecordId(response.order.oracle_order_id)} from accepted quote ${displayRecordId(response.order.oracle_quote_id)} for ${formatCurrency(response.order.total, response.order.currency)}.`,
        ),
      );
      await refreshOracleAndActivity(response.quote.sf_opportunity_id);
      return response.order;
    } catch (caught) {
      setError(errorMessage(caught));
      return null;
    } finally {
      setStatus("idle");
    }
  }

  function patchProduct(index: number, patch: Partial<Product>) {
    const nextProducts = products.map((product, productIndex) =>
      productIndex === index ? { ...product, ...patch } : product,
    );
    void updateProducts(nextProducts);
  }

  return (
    <div className="shell live-shell">
      <main className="main live-main">
        <header className="topbar">
          <div className="topbar-content">
            <div className="topbar-meta">
              <p className="eyebrow">Enterprise AI Agent Platform</p>
              <span>Author: Sarala Biswal</span>
            </div>
            <h1>Enterprise AI Agentic Workflow</h1>
            <p className="product-punchline">
              Revenue-flow platform showing how an AI agent reads Salesforce, orchestrates decisions,
              and writes governed quote/order outcomes to Oracle CPQ.
            </p>
            <div className="capability-strip" aria-label="Platform capabilities">
              <span>LangGraph</span>
              <span>MCP tools</span>
              <span>RAG evidence</span>
              <span>LLMClient</span>
              <span>CRM to CPQ</span>
            </div>
          </div>
          <div className="topbar-insight" aria-label="Architecture at a glance">
            <div className="topbar-insight-head">
              <strong>Agentic Revenue Flow</strong>
              <span className={`status-pill ${error ? "status-error" : ""}`}>{headline}</span>
            </div>
            <div className="flow-ribbon" aria-label="System flow">
              <span>
                <em>Read</em>
                Salesforce
              </span>
              <b>
                <em>Orchestrate</em>
                Agent + MCP
              </b>
              <span>
                <em>Write</em>
                Oracle CPQ
              </span>
            </div>
            <div className="topbar-metrics">
              <div>
                <span>Context</span>
                <strong>{opportunity ? displayRecordId(opportunity.sf_opportunity_id) : "Select deal"}</strong>
              </div>
              <div>
                <span>Evidence</span>
                <strong>{retrievedContext.length ? `${retrievedContext.length} RAG` : "Pending"}</strong>
              </div>
              <div>
                <span>Output</span>
                <strong>
                  {order
                    ? displayRecordId(order.oracle_order_id)
                    : finalizableQuote
                      ? displayRecordId(finalizableQuote.oracle_quote_id)
                      : products.length
                        ? `${products.length} products`
                        : "Ready"}
                </strong>
              </div>
            </div>
            {viewMode !== "business" ? <RuntimeProfileBadge profile={runtimeProfile} /> : null}
          </div>
        </header>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="view-switch" aria-label="Workspace view">
          <button
            aria-pressed={viewMode === "business"}
            className={viewMode === "business" ? "active" : ""}
            onClick={() => setViewMode("business")}
            type="button"
          >
            Business View
          </button>
          <button
            aria-pressed={viewMode === "architecture"}
            className={viewMode === "architecture" ? "active" : ""}
            onClick={() => setViewMode("architecture")}
            type="button"
          >
            Architecture View
          </button>
          <button
            aria-pressed={viewMode === "developer"}
            className={viewMode === "developer" ? "active" : ""}
            onClick={() => setViewMode("developer")}
            type="button"
          >
            Developer View
          </button>
        </div>

        {viewMode === "business" ? (
          <section className="business-workspace">
            <section className="business-source-layer">
              <div className="source-command-row">
                <div className="source-command-title">
                  <p className="eyebrow">Source System</p>
                  <h2>Salesforce CRM Cloud</h2>
                  <span className="source-badge sf">Read</span>
                </div>
                <div className="source-select-row" aria-label="Salesforce source selectors">
                  <label>
                    <span>Account</span>
                    <select
                      disabled={isBusy}
                      onChange={(event) => void selectAccount(event.target.value)}
                      value={selectedSfAccountId}
                    >
                      {accounts.map((account) => (
                        <option key={account.sf_account_id} value={account.sf_account_id}>
                          {displayRecordId(account.sf_account_id)} - {account.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Opportunity</span>
                    <select
                      disabled={isBusy || opportunities.length === 0}
                      onChange={(event) => void selectOpportunity(event.target.value)}
                      value={selectedSfOpportunityId}
                    >
                      {opportunities.map((item) => (
                        <option key={item.sf_opportunity_id} value={item.sf_opportunity_id}>
                          {displayRecordId(item.sf_opportunity_id)} - {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
              <SelectedContextBand
                account={selectedAccount}
                order={order}
                opportunity={opportunity}
                opportunityCount={opportunities.length}
                pricing={pricing}
                quoteCount={quotes.length}
                selectedProductCount={selectedProducts.length}
              />
            </section>

            <section className="business-execution-grid">
              <section className="cloud-lane agent-lane">
                <LaneHeader
                  badge="Decide + Orchestrate"
                  badgeClass="agent"
                  kicker="Middle Layer"
                  title="Agentic Orchestration App"
                />
                <form className="command-panel" onSubmit={executeCommand}>
                  <div className="command-panel-head">
                    <div>
                      <span>Command Assistant</span>
                      <strong>Choose one command, then run it for the selected opportunity.</strong>
                    </div>
                    <em>{effectiveCommandIntent ? "Command ready" : "Waiting for command"}</em>
                  </div>
                  <div className="command-composer">
                    <label className="command-select-field">
                      <span>Command to run</span>
                      <select
                        disabled={isBusy}
                        onChange={(event) => {
                          const selected = COMMAND_OPTIONS.find((option) => option.intent === event.target.value);
                          if (selected) {
                            setCommandSource("manual");
                            setCommand(selected.text);
                          }
                        }}
                        value={effectiveCommandIntent ?? ""}
                      >
                        <option value="">Choose a command</option>
                        {COMMAND_OPTIONS.map((option) => (
                          <option key={option.intent} value={option.intent}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="command-field">
                      <span>Command details</span>
                      <textarea
                        disabled={isBusy}
                        onKeyDown={(event) => {
                          if (event.key !== "Enter" || event.shiftKey) {
                            return;
                          }

                          event.preventDefault();
                          event.currentTarget.form?.requestSubmit();
                        }}
                        onChange={(event) => {
                          setCommandSource("manual");
                          setCommand(event.target.value);
                        }}
                        rows={2}
                        value={command}
                      />
                    </label>
                  </div>
                  <div className="command-action-row">
                    <div className="assistant-guidance">
                      <span>Next best action</span>
                      <strong>{nextBestAction}</strong>
                      {commandNotice ? <p>{commandNotice}</p> : null}
                    </div>
                    <button
                      className="command-primary"
                      disabled={isBusy || !selectedSfOpportunityId || !effectiveCommandIntent}
                      type="submit"
                    >
                      {commandButtonLabel(status, effectiveCommandIntent)}
                    </button>
                  </div>
                </form>

                {order ? (
                  <OrderDocument order={order} />
                ) : latestQuote && agentAction?.kind === "quote" ? (
                  <QuoteDocument
                    isBusy={isBusy}
                    onFinalize={() => void finalizeQuote(latestQuote.oracle_quote_id)}
                    quote={latestQuote}
                    status={status}
                  />
                ) : (
                  <RecommendedProductsPanel
                    isBusy={isBusy}
                    lineItemBySku={lineItemBySku}
                    onCreateQuote={createQuote}
                    onPatchProduct={patchProduct}
                    pricing={pricing}
                    products={products}
                    selectedProducts={selectedProducts}
                    status={status}
                  />
                )}

                {pricing ? (
                  <section className="price-band-live" aria-label="Pricing summary">
                    <SummaryItem label="Subtotal" value={formatCurrency(pricing.subtotal, pricing.currency)} />
                    <SummaryItem label="Discount" value={formatCurrency(pricing.discount, pricing.currency)} />
                    <SummaryItem label="Total" value={formatCurrency(pricing.total, pricing.currency)} />
                  </section>
                ) : null}

                <AgentWorkbench
                  action={agentAction}
                  activity={activity}
                  finalizableQuote={finalizableQuote}
                  latestQuote={latestQuote}
                  order={order}
                  opportunity={opportunity}
                  pricing={pricing}
                  products={products}
                  quotes={quotes}
                  retrievedContext={retrievedContext}
                  runSteps={runSteps}
                  selectedProducts={selectedProducts}
                />
              </section>

              <aside className="cloud-lane target-lane">
                <LaneHeader
                  badge="Write"
                  badgeClass="cpq"
                  kicker="Target System"
                  title="Oracle CPQ Cloud"
                />
                <section className="lane-section">
                  <h2>Quote Versions</h2>
                  {quotes.length === 0 ? (
                    <div className="empty-state">
                      No quote versions exist for this opportunity yet.
                    </div>
                  ) : (
                    <div className="quote-stack">
                      {quotes.map((quote) => (
                        <article className={`quote-card ${quote.status.toLowerCase()}`} key={quote.oracle_quote_id}>
                          <div>
                            <strong>{displayRecordId(quote.oracle_quote_id)}</strong>
                            <span>{formatStatusLabel(quote.status)}</span>
                          </div>
                          <p>
                            {quote.selected_product_count} products -{" "}
                            {formatCurrency(quote.total, quote.currency)}
                          </p>
                          <button
                            disabled={
                              isBusy ||
                              quote.status === "SUPERSEDED" ||
                              quote.status === "ACCEPTED"
                            }
                            onClick={() => void finalizeQuote(quote.oracle_quote_id)}
                            type="button"
                          >
                            {status === "finalizing" ? "Placing..." : "Finalize / Place Order"}
                          </button>
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                {order ? (
                  <section className="lane-section order-panel-live">
                    <p className="eyebrow">Placed Order</p>
                    <h2>{displayRecordId(order.oracle_order_id)}</h2>
                    <p>
                      Created from {displayRecordId(order.oracle_quote_id)} for{" "}
                      {formatCurrency(order.total, order.currency)}.
                    </p>
                  </section>
                ) : null}

                <details className="lane-section activity-panel">
                  <summary className="section-title-row activity-summary">
                    <div>
                      <h2>Activity Timeline</h2>
                      <p>{activity.length ? `Latest ${formatDateTime(activity[0]?.created_at)}` : "No activity yet"}</p>
                    </div>
                    <div className="workbench-summary-actions">
                      <span className="source-badge cpq">{activity.length} Events</span>
                      <span className="workbench-toggle" aria-hidden="true" />
                    </div>
                  </summary>
                  <div className="activity-stack">
                    {activity.length === 0 ? (
                      <p className="muted">No activity yet.</p>
                    ) : (
                      activity.slice(0, 8).map((event) => (
                        <article className="activity-event" key={event.activity_id}>
                          <time dateTime={event.created_at}>
                            <span>{formatDatePart(event.created_at)}</span>
                            <strong>{formatTimePart(event.created_at)}</strong>
                          </time>
                          <div>
                            <span>{event.system}</span>
                            <strong>{event.title}</strong>
                            <p>{displayRecordIdsInText(event.detail)}</p>
                          </div>
                        </article>
                      ))
                    )}
                  </div>
                </details>
              </aside>
            </section>
          </section>
        ) : viewMode === "architecture" ? (
          <ArchitectureView
            actionKind={architectureAction?.kind ?? "ready"}
            activity={activity}
            pricing={pricing}
            runtimeProfile={runtimeProfile}
            quotes={quotes}
            retrievedContext={retrievedContext}
            runSteps={runSteps}
            steps={traceSteps}
          />
        ) : (
          <DeveloperView
            activeFlow={developerFlow}
            onSelectFlow={setDeveloperFlow}
            runtimeProfile={runtimeProfile}
          />
        )}
      </main>
    </div>
  );
}

/** Render a compact read-only runtime provider badge outside the sales workflow. */
function RuntimeProfileBadge({ profile }: { profile: RuntimeProfile | null }) {
  const summary = profile?.summary;
  return (
    <section className="runtime-profile-badge" aria-label="Runtime provider profile">
      <div>
        <span>Runtime profile</span>
        <strong>{summary?.runtime_profile ?? "Loading"}</strong>
      </div>
      <div>
        <span>LLM</span>
        <strong>{summary?.llm ?? "-"}</strong>
      </div>
      <div>
        <span>Vector</span>
        <strong>{summary?.vector_store ?? "-"}</strong>
      </div>
      <div>
        <span>Store</span>
        <strong>{summary?.business_store ?? "-"}</strong>
      </div>
    </section>
  );
}

/** Render one system ownership tile in the architecture map. */
function SystemCard({
  accent,
  code,
  detail,
  title,
}: {
  accent: string;
  code: string;
  detail: string;
  title: string;
}) {
  return (
    <article className={`system-card-app ${accent}`}>
      <div>{code}</div>
      <section>
        <strong>{title}</strong>
        <span>{detail}</span>
      </section>
    </article>
  );
}

/** Render a lane title with its short operational summary. */
function LaneHeader({
  badge,
  badgeClass,
  kicker,
  title,
}: {
  badge: string;
  badgeClass: string;
  kicker: string;
  title: string;
}) {
  return (
    <header className="lane-header">
      <div>
        <p className="eyebrow">{kicker}</p>
        <h2>{title}</h2>
      </div>
      <span className={`source-badge ${badgeClass}`}>{badge}</span>
    </header>
  );
}

/** Render the currently selected account and opportunity context. */
function SelectedContextBand({
  account,
  order,
  opportunity,
  opportunityCount,
  pricing,
  quoteCount,
  selectedProductCount,
}: {
  account: Account | null;
  order: OrderRecord | null;
  opportunity: Opportunity | null;
  opportunityCount: number;
  pricing: Pricing | null;
  quoteCount: number;
  selectedProductCount: number;
}) {
  return (
    <section className="selected-context slim-context" aria-label="Selected Salesforce context">
      <article className="slim-context-group">
        <span className="record-id">{account ? displayRecordId(account.sf_account_id) : "SF-A"}</span>
        <strong>{account?.name ?? "Select an account"}</strong>
        <div className="compact-fields">
          <em>{account?.segment ?? "Segment"}</em>
          <em>{account ? formatCurrency(account.open_pipeline, "USD") : "Pipeline"}</em>
          <em>{opportunityCount} opps</em>
        </div>
      </article>

      <article className="slim-context-group wide">
        <span className="record-id">{opportunity ? displayRecordId(opportunity.sf_opportunity_id) : "SF-O"}</span>
        <strong>{opportunity?.name ?? "Select an opportunity"}</strong>
        <div className="compact-fields">
          <em>{opportunity?.stage ?? "Stage"}</em>
          <em>{opportunity ? formatCurrency(opportunity.amount, opportunity.currency) : "Amount"}</em>
          <em>{opportunity?.target_close_date ?? "Close date"}</em>
          <em>{opportunity?.risk_level ?? "Risk"}</em>
        </div>
      </article>

      <article className="slim-context-status">
        <div>
          <span>Products</span>
          <strong>{selectedProductCount}</strong>
        </div>
        <div>
          <span>Total</span>
          <strong>{pricing ? formatCurrency(pricing.total, pricing.currency) : "Pending"}</strong>
        </div>
        <div>
          <span>Quotes</span>
          <strong>{quoteCount}</strong>
        </div>
        <div>
          <span>Order</span>
          <strong>{order ? displayRecordId(order.oracle_order_id) : "Not placed"}</strong>
        </div>
      </article>
    </section>
  );
}

/** Render the central agent workbench status, steps, and current output. */
function AgentWorkbench({
  action,
  activity,
  finalizableQuote,
  latestQuote,
  order,
  opportunity,
  pricing,
  products,
  quotes,
  retrievedContext,
  runSteps,
  selectedProducts,
}: {
  action: AgentActionState | null;
  activity: ActivityEvent[];
  finalizableQuote: QuoteRecord | null;
  latestQuote: QuoteRecord | null;
  order: OrderRecord | null;
  opportunity: Opportunity | null;
  pricing: Pricing | null;
  products: Product[];
  quotes: QuoteRecord[];
  retrievedContext: string[];
  runSteps: RunStep[];
  selectedProducts: Product[];
}) {
  const signalGroups = groupOpportunitySignals(opportunity?.requirements ?? []);
  const activeAction = resolveActiveAgentAction({
    action,
    latestQuote,
    order,
    products,
  });
  const model = buildAgentWorkbenchModel({
    action: activeAction,
    activity,
    finalizableQuote,
    latestQuote,
    order,
    opportunity,
    pricing,
    products,
    quotes,
    retrievedContext,
    runSteps,
    selectedProducts,
    signalGroups,
  });
  const completedSteps = model.steps.filter((step) => step.status === "completed").length;

  return (
    <details className="lane-section agent-workbench">
      <summary className="section-title-row workbench-title">
        <div>
          <h2>Agent Workbench</h2>
          <p>{model.subtitle}</p>
        </div>
        <div className="workbench-summary-actions">
          <span className="source-badge agent">{completedSteps}/{model.steps.length} Steps</span>
          <span className="workbench-toggle" aria-hidden="true" />
        </div>
      </summary>

      <div className="agent-status-strip">
        <article>
          <span>Current Agent Run</span>
          <strong>{model.title}</strong>
          <p>{model.summary}</p>
        </article>
        <article>
          <span>Systems Touched</span>
          <strong>{model.systems}</strong>
          <p>{model.systemDetail}</p>
        </article>
        <article>
          <span>Business Output</span>
          <strong>{model.output}</strong>
          <p>{model.outputDetail}</p>
        </article>
      </div>

      <div className="capability-rail action-step-rail" aria-label="Agent action execution steps">
        {model.steps.map((step, index) => (
          <article className={step.status} key={step.name} title={step.detail}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{step.name}</strong>
            <p>{step.detail}</p>
          </article>
        ))}
      </div>

      <div className="context-results-panel">
        <div className="context-results-heading">
          <span>Context Results</span>
          <strong>{model.contextTitle}</strong>
        </div>
        {renderWorkbenchContext({
          action: model.kind,
          activity,
          finalizableQuote,
          latestQuote,
          order,
          opportunity,
          pricing,
          products,
          quotes,
          retrievedContext,
          selectedProducts,
          signalGroups,
        })}
      </div>
    </details>
  );
}

/** Render editable product recommendations and pricing controls. */
function RecommendedProductsPanel({
  isBusy,
  lineItemBySku,
  onCreateQuote,
  onPatchProduct,
  pricing,
  products,
  selectedProducts,
  status,
}: {
  isBusy: boolean;
  lineItemBySku: Map<string, LineItem>;
  onCreateQuote: () => Promise<QuoteRecord | null>;
  onPatchProduct: (index: number, patch: Partial<Product>) => void;
  pricing: Pricing | null;
  products: Product[];
  selectedProducts: Product[];
  status: string;
}) {
  return (
    <section className="lane-section">
      <div className="section-title-row">
        <h2>Recommended Products</h2>
        <button
          disabled={isBusy || selectedProducts.length === 0}
          onClick={onCreateQuote}
          type="button"
        >
          {status === "quoting" ? "Creating..." : "Create Quote Version"}
        </button>
      </div>

      {products.length === 0 ? (
        <div className="empty-state">
          Run the command to generate CPQ-backed recommendations.
        </div>
      ) : (
        <div className="product-stack">
          {products.map((product, index) => {
            const lineItem = lineItemBySku.get(product.sku);
            return (
              <article
                className={`product-card ${product.selected ? "selected" : ""}`}
                key={product.sku}
              >
                <div className="product-card-main">
                  <label className="include-toggle">
                    <input
                      checked={product.selected}
                      disabled={isBusy}
                      onChange={(event) =>
                        onPatchProduct(index, { selected: event.target.checked })
                      }
                      type="checkbox"
                    />
                    <span>{product.selected ? "Included" : "Excluded"}</span>
                  </label>
                  <div>
                    <strong>{product.name}</strong>
                    <span>{product.sku}</span>
                    <p>{product.reason}</p>
                  </div>
                </div>
                <div className="product-controls">
                  <label>
                    <span>Qty</span>
                    <input
                      disabled={isBusy || !product.selected}
                      min={1}
                      onChange={(event) =>
                        onPatchProduct(index, {
                          quantity: Number(event.target.value),
                        })
                      }
                      type="number"
                      value={product.quantity}
                    />
                  </label>
                  <label>
                    <span>Term</span>
                    <input
                      disabled={isBusy || !product.selected}
                      min={1}
                      onChange={(event) =>
                        onPatchProduct(index, {
                          term_months: Number(event.target.value),
                        })
                      }
                      type="number"
                      value={product.term_months}
                    />
                  </label>
                  <div className="line-total">
                    <span>Net</span>
                    <strong>
                      {lineItem
                        ? formatCurrency(lineItem.net_price, pricing?.currency ?? "USD")
                        : "-"}
                    </strong>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

/** Render the latest quote as a compact CPQ document view. */
function QuoteDocument({
  isBusy,
  onFinalize,
  quote,
  status,
}: {
  isBusy: boolean;
  onFinalize: () => void;
  quote: QuoteRecord;
  status: string;
}) {
  return (
    <section className="lane-section document-panel quote-document">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Oracle CPQ Quote</p>
          <h2>{displayRecordId(quote.oracle_quote_id)}</h2>
        </div>
        <button
          disabled={isBusy || quote.status === "SUPERSEDED" || quote.status === "ACCEPTED"}
          onClick={onFinalize}
          type="button"
        >
          {status === "finalizing" ? "Placing..." : "Finalize / Place Order"}
        </button>
      </div>

      <DocumentHeader
        items={[
          ["Quote ID", displayRecordId(quote.oracle_quote_id)],
          ["Source Opportunity", displayRecordId(quote.sf_opportunity_id)],
          ["Status", formatStatusLabel(quote.status)],
          ["Total", formatCurrency(quote.total, quote.currency)],
          ["Discount", formatCurrency(quote.discount, quote.currency)],
          ["Created", formatDateTime(quote.created_at)],
        ]}
      />
      <DocumentLineTable currency={quote.currency} lines={quote.line_items ?? []} />
    </section>
  );
}

/** Render the placed order summary document. */
function OrderDocument({ order }: { order: OrderRecord }) {
  return (
    <section className="lane-section document-panel order-document">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Oracle CPQ Order</p>
          <h2>{displayRecordId(order.oracle_order_id)}</h2>
        </div>
        <span className="source-badge cpq">{formatStatusLabel(order.status)}</span>
      </div>

      <DocumentHeader
        items={[
          ["Order ID", displayRecordId(order.oracle_order_id)],
          ["Accepted Quote", displayRecordId(order.oracle_quote_id)],
          ["Source Opportunity", displayRecordId(order.sf_opportunity_id)],
          ["Status", formatStatusLabel(order.status)],
          ["Total", formatCurrency(order.total, order.currency)],
          ["Placed", formatDateTime(order.placed_at)],
        ]}
      />
      <DocumentLineTable currency={order.currency} lines={order.line_items ?? []} />
    </section>
  );
}

/** Render key-value metadata above quote and order documents. */
function DocumentHeader({ items }: { items: Array<[string, string]> }) {
  return (
    <div className="document-header-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

/** Render priced line items for quote and order documents. */
function DocumentLineTable({
  currency,
  lines,
}: {
  currency: string;
  lines: LineItem[];
}) {
  if (lines.length === 0) {
    return <div className="empty-state">No line items found for this record.</div>;
  }

  return (
    <div className="document-lines" aria-label="Line items">
      <div className="document-line header">
        <span>SKU</span>
        <span>Product</span>
        <span>Qty</span>
        <span>Term</span>
        <span>Billing</span>
        <span>Net</span>
      </div>
      {lines.map((line) => (
        <div className="document-line" key={line.sku}>
          <span>{line.sku}</span>
          <strong>{line.name}</strong>
          <span>{line.quantity}</span>
          <span>{line.term_months} mo</span>
          <span>{line.billing_model}</span>
          <strong>{formatCurrency(line.net_price, currency)}</strong>
        </div>
      ))}
    </div>
  );
}

/** Render one label-value item in a summary strip. */
function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

/** Render one recommendation decision statement. */
function Decision({ label, value }: { label: string; value: string }) {
  return (
    <article className="decision-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

/** Render a compact grid of business context details. */
function DetailGrid({ items }: { items: Array<[string, string]> }) {
  return (
    <dl className="detail-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Render the trace, payloads, and governance contracts for the current flow. */
function ArchitectureView({
  actionKind,
  activity,
  pricing,
  runtimeProfile,
  quotes,
  retrievedContext,
  runSteps,
  steps,
}: {
  actionKind: ArchitectureActionKind;
  activity: ActivityEvent[];
  pricing: Pricing | null;
  runtimeProfile: RuntimeProfile | null;
  quotes: QuoteRecord[];
  retrievedContext: string[];
  runSteps: RunStep[];
  steps: TraceStep[];
}) {
  const completed = steps.filter((step) => step.status === "completed").length;
  return (
    <section className="architecture-workspace live-architecture">
      <div className="architecture-main">
        <div className="section-header">
          <div>
            <h2>Architecture Trace</h2>
            <p>
              {completed}/{steps.length} steps complete across Salesforce, Agent/MCP/RAG, and Oracle CPQ.
            </p>
          </div>
          <span className="trace-count">{retrievedContext.length} RAG snippets</span>
        </div>
        <div className="trace-list">
          {steps.map((step, index) => (
            <details className={`trace-detail ${step.status}`} key={`${step.label}-${index}`}>
              <summary>
                <span className="trace-index">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <strong>{step.label}</strong>
                  <span>{step.system} - {step.layer}</span>
                </div>
                <em>{formatStatusLabel(step.status)}</em>
              </summary>
              <div className="trace-payloads">
                <PayloadPanel title="Input" payload={step.input} />
                <PayloadPanel title="Output" payload={step.output} />
              </div>
            </details>
          ))}
        </div>
        <ArchitectureCodeFlow actionKind={actionKind} />
        <ArchitectureRagFlow actionKind={actionKind} retrievedContext={retrievedContext} />
      </div>

      <aside className="architecture-aside">
        <DeploymentProfilePanel profile={runtimeProfile} />
        <section>
          <h2>Layer Contracts</h2>
          <div className="contract-list">
            <ContractItem label="Salesforce CRM" value="Owns sf_account_id and sf_opportunity_id records." />
            <ContractItem label="Agent" value="Orchestrates the workflow through LangGraph state." />
            <ContractItem label="MCP" value="Only execution boundary for Salesforce, RAG, and CPQ tools." />
            <ContractItem label="RAG" value="Returns knowledge only through MCP.search_knowledge." />
            <ContractItem label="Oracle CPQ" value="Owns oracle_quote_id and oracle_order_id records." />
          </div>
        </section>
        <section>
          <h2>Run Evidence</h2>
          <div className="decision-list">
            <Decision label="Run Steps" value={`${runSteps.length} agent steps recorded`} />
            <Decision label="Quote Versions" value={`${quotes.length} Oracle CPQ versions`} />
            <Decision
              label="Pricing"
              value={pricing ? formatCurrency(pricing.total, pricing.currency) : "Not calculated"}
            />
            <Decision label="Activity" value={`${activity.length} timeline events`} />
          </div>
        </section>
      </aside>
    </section>
  );
}

/** Render read-only backend deployment provider metadata in Architecture View. */
function DeploymentProfilePanel({ profile }: { profile: RuntimeProfile | null }) {
  const summary = profile?.summary;
  return (
    <section className="deployment-profile-panel">
      <h2>Deployment Profile</h2>
      <p>
        Provider selection is controlled by backend deployment configuration. This UI is read-only.
      </p>
      <div className="deployment-profile-grid">
        <ContractItem label="Active runtime profile" value={summary?.runtime_profile ?? "Loading"} />
        <ContractItem label="Agent orchestration" value={summary?.agent_orchestration ?? "-"} />
        <ContractItem label="MCP execution boundary" value="MCPExecutionEngine and registered tool names" />
        <ContractItem label="LLM provider" value={summary?.llm ?? "-"} />
        <ContractItem label="Embedding provider" value={summary?.embeddings ?? "-"} />
        <ContractItem label="RAG / vector store" value={summary?.vector_store ?? "-"} />
        <ContractItem label="Business store" value={summary?.business_store ?? "-"} />
        <ContractItem label="Object store" value={summary?.object_store ?? "-"} />
        <ContractItem label="Secrets provider" value={summary?.secrets ?? "-"} />
        <ContractItem label="Observability provider" value={summary?.observability ?? "-"} />
      </div>
    </section>
  );
}

const RECOMMEND_PRODUCT_CODE_FLOW = [
  {
    layer: "Frontend UI",
    title: "User Command",
    detail: "User submits the command form with intent recommend.",
    code: "page.tsx:436\nexecuteCommand()",
  },
  {
    layer: "Frontend UI",
    title: "Run UI Handler",
    detail: "The UI checks selected opportunity, clears stale quote/order state, and starts loading.",
    code: "page.tsx:474\nrunRecommendation()",
  },
  {
    layer: "Frontend UI",
    title: "POST API Request",
    detail: "The frontend sends the selected Salesforce opportunity and recommendation prompt.",
    code: 'page.tsx:485\npostJson("/quote/recommendations")',
  },
  {
    layer: "FastAPI",
    title: "FastAPI Boundary",
    detail: "FastAPI validates the request and creates initial LangGraph state.",
    code: "main.py:236\nrecommend_quote()",
  },
  {
    layer: "LangGraph",
    title: "Build Graph",
    detail: "The backend invokes the recommendation-only graph before quote creation.",
    code: "main.py:256\nbuild_recommendation_graph()\n  .invoke(state)",
  },
  {
    layer: "LangGraph",
    title: "LangGraph Nodes",
    detail: "The graph runs intent analysis, RAG, opportunity lookup, recommendation, pricing, and response.",
    code: "graph.py:68\nanalyze -> retrieve_context\n-> get_opportunity -> recommend_products\n-> get_pricing -> respond",
  },
  {
    layer: "MCP",
    title: "MCP Recommendation Tool",
    detail: "The agent calls MCP by tool name, and MCP looks up the registered handler.",
    code: 'graph.py:242\nengine.execute(\n  "recommend_products",\n  {"opportunity": state["opportunity"]}\n)',
  },
  {
    layer: "CPQ",
    title: "CPQ Rules",
    detail: "The handler validates payload, calls CPQ recommendation logic, and records activity.",
    code: "opportunity_quote.py:52\nrecommend_products_tool()\nrecommend_products(opportunity)",
  },
  {
    layer: "MCP",
    title: "MCP Pricing Tool",
    detail: "The graph prices the recommended bundle through the same MCP execution boundary.",
    code: 'graph.py:258\nengine.execute(\n  "get_pricing",\n  {"recommendation": state["recommendation"]}\n)',
  },
  {
    layer: "UI State",
    title: "UI Updates",
    detail: "The response populates products, pricing, RAG context, run steps, and architecture trace.",
    code: "page.tsx:492\nsetProducts()\nsetPricing()\nsetRetrievedContext()\nsetRunSteps()",
  },
] as const;

const RAG_CODE_FLOW = [
  {
    layer: "Setup",
    title: "Ingest Knowledge",
    detail: "Product, pricing, and playbook documents are embedded and stored before runtime.",
    code: "services/rag/ingest.py\nSAMPLE_DOCUMENTS",
  },
  {
    layer: "LangGraph",
    title: "Keyword Gate",
    detail: "The user command is checked for domain terms like sales playbook, pricing rules, and telecom.",
    code: "graph.py:683\n_should_retrieve_context()",
  },
  {
    layer: "MCP",
    title: "Search Tool",
    detail: "The agent crosses the MCP boundary instead of calling the retriever directly.",
    code: 'graph.py:200\nengine.execute("search_knowledge")',
  },
  {
    layer: "Retriever",
    title: "Embed And Query",
    detail: "The query is embedded with Ollama and matched against ChromaDB vectors.",
    code: "retriever.py:28\nVectorStore.query(k=3)",
  },
  {
    layer: "Response",
    title: "Prompt Context",
    detail: "Returned snippets become retrieved_context for the assistant prompt and UI trace.",
    code: "graph.py:476\nCONTEXT:\\n...",
  },
] as const;

const DEVELOPER_FLOWS: Record<
  DeveloperFlowKey,
  {
    title: string;
    subtitle: string;
    steps: readonly {
      layer: string;
      title: string;
      detail: string;
      code: string;
    }[];
  }
> = {
  recommend: {
    title: "Recommend Product Flow",
    subtitle: "UI command to recommendation graph, MCP tools, CPQ rules, pricing, and UI state.",
    steps: RECOMMEND_PRODUCT_CODE_FLOW,
  },
  rag: {
    title: "RAG Retrieval Flow",
    subtitle: "Knowledge ingestion and runtime search through MCP.search_knowledge.",
    steps: RAG_CODE_FLOW,
  },
  backend: {
    title: "Backend API Boundary",
    subtitle: "FastAPI validates payloads and chooses graph or direct MCP execution.",
    steps: [
      {
        layer: "Frontend",
        title: "Business Action",
        detail: "A UI button or command chooses the endpoint for recommendation, quote, or order.",
        code: "page.tsx\nrunRecommendation()\ncreateQuote()\ncreateOrder()",
      },
      {
        layer: "Frontend",
        title: "POST Request",
        detail: "The client sends a compact JSON payload with selected Salesforce and workflow context.",
        code: 'postJson("/quote/recommendations", payload)',
      },
      {
        layer: "Schema",
        title: "Validate Body",
        detail: "Pydantic validates request and response models.",
        code: "schemas/quote.py\nRecommendationRequest",
      },
      {
        layer: "FastAPI",
        title: "Route Handler",
        detail: "The route builds initial state and handles HTTP errors.",
        code: "apps/backend/main.py\nrecommend_quote()",
      },
      {
        layer: "LangGraph",
        title: "Dispatch Agentic Work",
        detail: "Recommendation requests invoke the compiled graph with the validated state.",
        code: "build_recommendation_graph().invoke(state)",
      },
      {
        layer: "MCP",
        title: "Dispatch Tool Work",
        detail: "Quote and order routes can call MCP tools directly after the boundary check.",
        code: 'engine.execute("create_quote", payload)',
      },
      {
        layer: "Response",
        title: "Return Contract",
        detail: "The backend returns dictionaries that the UI can render without knowing integration internals.",
        code: "return RecommendationResponse(...)",
      },
    ],
  },
  langgraph: {
    title: "LangGraph Orchestration",
    subtitle: "StateGraph nodes pass AgentState through a deterministic workflow.",
    steps: [
      {
        layer: "State",
        title: "AgentState",
        detail: "Shared typed dictionary carries user input and tool outputs.",
        code: "services/agent/state.py\nclass AgentState",
      },
      {
        layer: "Factory",
        title: "Build Workflow",
        detail: "The graph builder creates a StateGraph around the shared AgentState contract.",
        code: "graph.py\nStateGraph(AgentState)",
      },
      {
        layer: "Graph",
        title: "Add Nodes",
        detail: "Each node is one unit of workflow behavior.",
        code: 'graph.add_node("analyze", _analyze_intent)',
      },
      {
        layer: "Graph",
        title: "Add Edges",
        detail: "Edges define execution order between nodes.",
        code: 'graph.add_edge("get_opportunity", "recommend_products")',
      },
      {
        layer: "Node",
        title: "Run Python Function",
        detail: "Every node receives state, adds its output, and returns the changed state.",
        code: "def _get_pricing(state):\n  return {**state, \"pricing\": pricing}",
      },
      {
        layer: "Runtime",
        title: "Invoke",
        detail: "FastAPI invokes the compiled graph with initial state.",
        code: "graph.compile().invoke(state)",
      },
      {
        layer: "Response",
        title: "Read Final State",
        detail: "The route reads recommendation, pricing, retrieved context, and run steps from graph output.",
        code: "result[\"recommendation\"]\nresult[\"pricing\"]",
      },
    ],
  },
  mcp: {
    title: "MCP Tool Boundary",
    subtitle: "Named tools protect execution against direct integration calls.",
    steps: [
      {
        layer: "Setup",
        title: "Load Tool Module",
        detail: "The MCP factory imports the module that exposes opportunity and quote tool definitions.",
        code: "services/mcp/factory.py\nfrom services.tools import opportunity_quote",
      },
      {
        layer: "Registry",
        title: "Register Tool",
        detail: "Tool names map to Python handlers.",
        code: 'ToolDefinition(name="get_pricing", handler=get_pricing_tool)',
      },
      {
        layer: "Engine",
        title: "Execute",
        detail: "The engine validates dict payloads and result shape.",
        code: 'engine.execute("get_pricing", {"recommendation": data})',
      },
      {
        layer: "Handler",
        title: "Validate Payload",
        detail: "Tool handler checks required keys before integration code runs.",
        code: '_required(payload, "recommendation")',
      },
      {
        layer: "Integration",
        title: "Delegate",
        detail: "Handler calls Salesforce, CPQ, RAG, or data-layer code.",
        code: "return get_pricing(recommendation)",
      },
      {
        layer: "Response",
        title: "Return Dict",
        detail: "The handler returns a clean dictionary for graph state, API response, and UI rendering.",
        code: "return {\"pricing\": pricing}",
      },
    ],
  },
  integrations: {
    title: "Mock Enterprise Integrations",
    subtitle: "Local Salesforce and Oracle CPQ behavior behind MCP handlers.",
    steps: [
      {
        layer: "Salesforce",
        title: "CRM Read",
        detail: "Opportunity context comes from the Salesforce mock.",
        code: "integrations/salesforce/mock.py\nget_opportunity()",
      },
      {
        layer: "Repository",
        title: "Runtime Data",
        detail: "Mock integrations read seeded account, opportunity, product, and quote records.",
        code: "services/data/repositories.py\nget_opportunity_by_sf_id()",
      },
      {
        layer: "CPQ Catalog",
        title: "Product Metadata",
        detail: "Catalog owns SKU, category, billing model, and unit price.",
        code: "integrations/cpq/catalog.py\nget_catalog_item()",
      },
      {
        layer: "CPQ Rules",
        title: "Recommend",
        detail: "Requirements map to product SKUs and rule IDs.",
        code: "integrations/cpq/recommendation.py\nrecommend_products()",
      },
      {
        layer: "CPQ Pricing",
        title: "Calculate Price",
        detail: "Pricing applies quantity, term, discounts, and totals before quote creation.",
        code: "integrations/cpq/pricing.py\ncalculate_pricing()",
      },
      {
        layer: "CPQ Lifecycle",
        title: "Quote/Order",
        detail: "Quote creation and finalization produce Oracle-owned records.",
        code: "integrations/cpq/quote.py\ncreate_quote()",
      },
    ],
  },
  data: {
    title: "Data Layer And Runtime State",
    subtitle: "SQLite stores business state, activity, and agent run history.",
    steps: [
      {
        layer: "Database",
        title: "Connect",
        detail: "Runtime data lives in app_data/business.sqlite3.",
        code: "services/data/database.py\nconnect()",
      },
      {
        layer: "Seed",
        title: "Initialize",
        detail: "Demo accounts, opportunities, products, quotes, and orders seed once.",
        code: "services/data/seed.py\nseed_if_empty()",
      },
      {
        layer: "Repository",
        title: "Read Business State",
        detail: "The API reads account, opportunity, activity, quote, and order state through repositories.",
        code: "repositories.py\nlist_accounts()\nlist_opportunities()",
      },
      {
        layer: "Repository",
        title: "Persist Quote",
        detail: "Quote headers, line items, and activity are written together.",
        code: "repositories.py\ncreate_quote_record()",
      },
      {
        layer: "Audit",
        title: "Agent Runs",
        detail: "Run history and step records power trace/audit views.",
        code: "repositories.py\nrecord_agent_run()",
      },
      {
        layer: "Frontend",
        title: "Refresh UI State",
        detail: "The business view reloads source data after recommendation, quote, and order actions.",
        code: "page.tsx\nloadSources()\nsetQuotes()\nsetActivity()",
      },
    ],
  },
  llm: {
    title: "LLM Abstraction",
    subtitle: "The agent depends on LLMClient, not a provider-specific SDK.",
    steps: [
      {
        layer: "Interface",
        title: "LLMClient",
        detail: "Provider-neutral chat interface.",
        code: "services/llm/client.py\nchat(messages)",
      },
      {
        layer: "Factory",
        title: "Select Provider",
        detail: "Fallback returns None; Ollama returns OllamaClient.",
        code: "create_llm_client()\nLLM_PROVIDER=ollama",
      },
      {
        layer: "Graph",
        title: "Optional Client",
        detail: "Graph code can run deterministic fallback logic when no live model is configured.",
        code: "llm = create_llm_client()\nif llm is None: fallback",
      },
      {
        layer: "Prompt",
        title: "Curated Context",
        detail: "Graph builds prompts from tool outputs and RAG snippets.",
        code: "graph.py\n_build_recommendation_prompt()",
      },
      {
        layer: "Provider",
        title: "Ollama",
        detail: "Live mode posts non-streaming chat messages to Ollama.",
        code: "ollama.py\nPOST /api/chat",
      },
      {
        layer: "Response",
        title: "Normalize Text",
        detail: "Provider output is reduced to plain assistant text before entering graph state.",
        code: "LLMResponse(content=...)",
      },
    ],
  },
  providers: {
    title: "Provider Profiles",
    subtitle: "Read-only deployment profile mappings for Local, OCI, GCP, and Kubernetes.",
    steps: [
      {
        layer: "Config",
        title: "Select Profile",
        detail: "Backend environment variables choose provider names at deployment time.",
        code: "PLATFORM_PROFILE=local\nLLM_PROVIDER=ollama",
      },
      {
        layer: "API",
        title: "Expose Read-Only Metadata",
        detail: "The UI reads sanitized profile display labels without credentials or connection strings.",
        code: "GET /runtime/profile\neditable_in_ui=false",
      },
      {
        layer: "Boundary",
        title: "Keep Runtime Immutable",
        detail: "Provider selection is not changed by frontend controls.",
        code: "services/platform/config.py\nget_runtime_profile_payload()",
      },
    ],
  },
};

const DEVELOPER_FLOW_GROUPS: {
  title: string;
  description: string;
  flows: DeveloperFlowKey[];
}[] = [
  {
    title: "Setup",
    description: "The pieces that exist before a user clicks a workflow button.",
    flows: ["data", "integrations", "llm", "rag", "providers"],
  },
  {
    title: "Runtime",
    description: "The request path after a user starts work in the UI.",
    flows: ["backend", "langgraph", "mcp", "recommend"],
  },
];

/** Render the implementation code path for the active architecture action. */
function ArchitectureCodeFlow({ actionKind }: { actionKind: ArchitectureActionKind }) {
  if (actionKind !== "recommend") {
    return null;
  }

  return (
    <section className="code-flow-panel" aria-label="Recommend product code flow">
      <div className="section-header compact">
        <div>
          <h2>Recommend Product Code Flow</h2>
          <p>How the UI action crosses FastAPI, LangGraph, MCP, and CPQ code boundaries.</p>
        </div>
      </div>
      <div className="code-flow-strip">
        {RECOMMEND_PRODUCT_CODE_FLOW.map((step, index) => (
          <article className="code-flow-node" key={step.title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <em>{step.layer}</em>
            <strong>{step.title}</strong>
            <p>{step.detail}</p>
            <code>{step.code}</code>
          </article>
        ))}
      </div>
    </section>
  );
}

/** Render a tabbed developer-oriented code flow workbench. */
function DeveloperView({
  activeFlow,
  onSelectFlow,
  runtimeProfile,
}: {
  activeFlow: DeveloperFlowKey;
  onSelectFlow: (flow: DeveloperFlowKey) => void;
  runtimeProfile: RuntimeProfile | null;
}) {
  const selected = DEVELOPER_FLOWS[activeFlow];
  const activeGroup = DEVELOPER_FLOW_GROUPS.find((group) => group.flows.includes(activeFlow));

  return (
    <section className="developer-workspace">
      <aside className="developer-tabs" aria-label="Developer flow tabs">
        {DEVELOPER_FLOW_GROUPS.map((group) => (
          <div className="developer-tab-group" key={group.title}>
            <div className="developer-tab-heading">
              <strong>{group.title}</strong>
              <span>{group.description}</span>
            </div>
            {group.flows.map((flowKey) => (
              <button
                aria-pressed={activeFlow === flowKey}
                className={activeFlow === flowKey ? "active" : ""}
                key={flowKey}
                onClick={() => onSelectFlow(flowKey)}
                type="button"
              >
                {DEVELOPER_FLOWS[flowKey].title}
              </button>
            ))}
          </div>
        ))}
      </aside>

      <section className="developer-panel">
        <div className="section-header">
          <div>
            <span className="developer-stage">{activeGroup?.title ?? "Flow"}</span>
            <h2>{selected.title}</h2>
            <p>{selected.subtitle}</p>
          </div>
          <span className="trace-count">{selected.steps.length} steps</span>
        </div>
        {activeFlow === "providers" ? (
          // Provider Profiles is a Setup topic, not a persistent footer across
          // every Developer View flow.
          <ProviderProfilesMatrix runtimeProfile={runtimeProfile} />
        ) : (
          <CodeFlowStrip steps={selected.steps} />
        )}
      </section>
    </section>
  );
}

/** Render provider profile comparison documentation for Developer View. */
function ProviderProfilesMatrix({
  runtimeProfile,
}: {
  runtimeProfile: RuntimeProfile | null;
}) {
  const profiles = runtimeProfile?.profiles ?? {};
  const profileKeys = ["local", "oci", "gcp", "generic-kubernetes"];
  // The matrix is documentation sourced from /runtime/profile. It deliberately
  // shows display labels only, never raw deployment variables with secrets.
  const rows: Array<[string, keyof RuntimeProfileSummary]> = [
    ["Agent orchestration", "agent_orchestration"],
    ["LLM", "llm"],
    ["Embeddings", "embeddings"],
    ["Vector store", "vector_store"],
    ["Business store", "business_store"],
    ["Object store", "object_store"],
    ["Secrets", "secrets"],
    ["Observability", "observability"],
  ];

  return (
    <section className="provider-profiles-section">
      <div className="section-header compact">
        <div>
          <h2>Provider Profiles</h2>
          <p>Read-only comparison of deployment profile mappings.</p>
        </div>
        <span className="trace-count">
          Active: {runtimeProfile?.display_name ?? "Loading"}
        </span>
      </div>
      <div className="provider-profile-table" role="table" aria-label="Provider profile comparison">
        <div className="provider-profile-row header" role="row">
          <strong role="columnheader">Capability</strong>
          {profileKeys.map((profileKey) => (
            <strong role="columnheader" key={profileKey}>
              {profiles[profileKey]?.runtime_profile ?? formatProfileKey(profileKey)}
            </strong>
          ))}
        </div>
        {rows.map(([label, key]) => (
          <div className="provider-profile-row" role="row" key={key}>
            <span role="cell">{label}</span>
            {profileKeys.map((profileKey) => (
              <p role="cell" key={`${profileKey}-${key}`}>
                {profiles[profileKey]?.[key] ?? "-"}
              </p>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

/** Render one horizontal code-flow diagram. */
function CodeFlowStrip({
  steps,
}: {
  steps: readonly {
    layer: string;
    title: string;
    detail: string;
    code: string;
  }[];
}) {
  return (
    <div className="code-flow-strip developer-flow-strip">
      {steps.map((step, index) => (
        <article
          className={`code-flow-node developer-flow-node ${getFlowLayerClass(step.layer)}`}
          key={`${step.layer}-${step.title}`}
        >
          <span>{String(index + 1).padStart(2, "0")}</span>
          <em>{step.layer}</em>
          <strong>{step.title}</strong>
          <p>{step.detail}</p>
          <code>{step.code}</code>
        </article>
      ))}
    </div>
  );
}

function getFlowLayerClass(layer: string) {
  const normalized = layer.toLowerCase();

  if (normalized.includes("frontend") || normalized.includes("ui")) {
    return "flow-layer-ui";
  }
  if (normalized.includes("api") || normalized.includes("schema") || normalized.includes("response")) {
    return "flow-layer-api";
  }
  if (normalized.includes("graph") || normalized.includes("node") || normalized.includes("runtime")) {
    return "flow-layer-agent";
  }
  if (normalized.includes("mcp") || normalized.includes("registry") || normalized.includes("handler")) {
    return "flow-layer-mcp";
  }
  if (normalized.includes("cpq") || normalized.includes("salesforce") || normalized.includes("integration")) {
    return "flow-layer-cpq";
  }
  if (
    normalized.includes("data") ||
    normalized.includes("database") ||
    normalized.includes("repository") ||
    normalized.includes("audit") ||
    normalized.includes("seed") ||
    normalized.includes("retriever")
  ) {
    return "flow-layer-data";
  }
  if (
    normalized.includes("llm") ||
    normalized.includes("factory") ||
    normalized.includes("prompt") ||
    normalized.includes("provider") ||
    normalized.includes("interface")
  ) {
    return "flow-layer-llm";
  }
  return "flow-layer-default";
}

/** Render the RAG retrieval code path for recommendation runs. */
function ArchitectureRagFlow({
  actionKind,
  retrievedContext,
}: {
  actionKind: ArchitectureActionKind;
  retrievedContext: string[];
}) {
  if (actionKind !== "recommend") {
    return null;
  }

  return (
    <section className="code-flow-panel" aria-label="RAG retrieval code flow">
      <div className="section-header compact">
        <div>
          <h2>RAG Retrieval Code Flow</h2>
          <p>
            How product, pricing, and playbook knowledge is retrieved through MCP.search_knowledge.
          </p>
        </div>
        <span className="trace-count">{retrievedContext.length} snippets</span>
      </div>
      <div className="code-flow-strip rag-flow-strip">
        {RAG_CODE_FLOW.map((step, index) => (
          <article className="code-flow-node rag-flow-node" key={step.title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <em>{step.layer}</em>
            <strong>{step.title}</strong>
            <p>{step.detail}</p>
            <code>{step.code}</code>
          </article>
        ))}
      </div>
    </section>
  );
}

/** Render a formatted JSON payload block. */
function PayloadPanel({ title, payload }: { title: string; payload: unknown }) {
  return (
    <div className="payload-panel">
      <span>{title}</span>
      <pre>{formatPayload(payload)}</pre>
    </div>
  );
}

/** Render one platform contract or governance rule. */
function ContractItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <strong>{label}</strong>
      <span>{value}</span>
    </div>
  );
}

/** Fetch JSON from the backend API and surface HTTP failures as errors. */
async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/** Post JSON to the backend API and parse the JSON response. */
async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/** Build architecture trace steps from the selected state and agent outputs. */
function buildTraceSteps({
  activity,
  command,
  opportunity,
  order,
  pricing,
  products,
  quotes,
  retrievedContext,
  runSteps,
  selectedAccount,
  selectedProducts,
}: {
  activity: ActivityEvent[];
  command: string;
  opportunity: Opportunity | null;
  order: OrderRecord | null;
  pricing: Pricing | null;
  products: Product[];
  quotes: QuoteRecord[];
  retrievedContext: string[];
  runSteps: RunStep[];
  selectedAccount: Account | null;
  selectedProducts: Product[];
}): TraceStep[] {
  return [
    {
      label: "Select Salesforce Account",
      layer: "Frontend",
      system: "Salesforce CRM Cloud",
      status: selectedAccount ? "completed" : "pending",
      detail: "The app reads account portfolio context from Salesforce.",
      input: {},
      output: selectedAccount ?? {},
    },
    {
      label: "Select Salesforce Opportunity",
      layer: "Frontend",
      system: "Salesforce CRM Cloud",
      status: opportunity ? "completed" : "pending",
      detail: "The app reads the selected opportunity and requirements.",
      input: { sf_account_id: selectedAccount?.sf_account_id },
      output: opportunity ?? {},
    },
    {
      label: "Analyze Command",
      layer: "Agent",
      system: "Agentic Orchestration App",
      status: runSteps.length ? "completed" : "pending",
      detail: "LangGraph prepares an opportunity-to-quote workflow.",
      input: { command },
      output: runSteps.find((step) => step.id === "analyze") ?? {},
    },
    {
      label: "Retrieve Knowledge",
      layer: "MCP + RAG",
      system: "Agentic Orchestration App",
      status: retrievedContext.length ? "completed" : products.length ? "active" : "pending",
      detail: "MCP.search_knowledge retrieves product, pricing, and playbook context.",
      input: { query: command, k: 3 },
      output: { retrieved_context: retrievedContext },
    },
    {
      label: "Recommend Products",
      layer: "MCP + Oracle CPQ Tool",
      system: "Oracle CPQ Cloud",
      status: products.length ? "completed" : "pending",
      detail: "CPQ rules map opportunity requirements to catalog products.",
      input: { requirements: opportunity?.requirements ?? [] },
      output: products.map((product) => ({
        sku: product.sku,
        rule_id: product.rule_id,
        selected: product.selected,
      })),
    },
    {
      label: "Calculate Pricing",
      layer: "MCP + Oracle CPQ Tool",
      system: "Oracle CPQ Cloud",
      status: pricing ? "completed" : products.length ? "active" : "pending",
      detail: "CPQ prices the selected product configuration and discounts.",
      input: { selected_products: selectedProducts.map((product) => product.sku) },
      output: pricing ?? {},
    },
    {
      label: "Create Quote Version",
      layer: "MCP + Oracle CPQ Tool",
      system: "Oracle CPQ Cloud",
      status: quotes.length ? "completed" : products.length ? "active" : "pending",
      detail: "Oracle CPQ owns quote versions through oracle_quote_id.",
      input: { sf_opportunity_id: opportunity?.sf_opportunity_id },
      output: { quotes: quotes.map((quote) => quote.oracle_quote_id) },
    },
    {
      label: "Customer Finalizes Quote",
      layer: "Human Approval",
      system: "Customer + Sales Rep",
      status: order ? "completed" : quotes.length ? "active" : "pending",
      detail: "A customer-selected quote version moves forward.",
      input: { available_quotes: quotes.map((quote) => quote.oracle_quote_id) },
      output: order ? { accepted_quote: order.oracle_quote_id } : {},
    },
    {
      label: "Place Order",
      layer: "MCP + Oracle CPQ Tool",
      system: "Oracle CPQ Cloud",
      status: order ? "completed" : quotes.length ? "active" : "pending",
      detail: "Oracle CPQ places the order with oracle_order_id.",
      input: order ? { oracle_quote_id: order.oracle_quote_id } : {},
      output: order ?? {},
    },
    {
      label: "Persist Activity",
      layer: "SQLite Repository",
      system: "Agentic Orchestration App",
      status: activity.length ? "completed" : "pending",
      detail: "Business events are persisted for the live timeline.",
      input: { sf_opportunity_id: opportunity?.sf_opportunity_id },
      output: { activity_count: activity.length },
    },
  ];
}

/** Merge current and incoming run steps without duplicating step ids. */
function mergeRunSteps(current: RunStep[], next: RunStep[]) {
  const byId = new Map(current.map((step) => [step.id, step]));
  for (const step of next) {
    byId.set(step.id, step);
  }
  return Array.from(byId.values());
}

/** Create a timestamped summary of the most recent agent action. */
function createAgentAction(
  kind: AgentActionKind,
  title: string,
  summary: string,
): AgentActionState {
  return {
    kind,
    title,
    summary,
    timestamp: new Date().toISOString(),
  };
}

/** Choose the agent action that should drive the current workbench state. */
function resolveActiveAgentAction({
  action,
  latestQuote,
  order,
  products,
}: {
  action: AgentActionState | null;
  latestQuote: QuoteRecord | null;
  order: OrderRecord | null;
  products: Product[];
}): AgentActionState | null {
  if (action) {
    return action;
  }
  if (order) {
    return {
      kind: "order",
      title: "Create Order",
      summary: `Order ${displayRecordId(order.oracle_order_id)} is the latest Oracle CPQ output.`,
      timestamp: "",
    };
  }
  if (latestQuote) {
    return {
      kind: "quote",
      title: "Create Quote",
      summary: `Quote ${displayRecordId(latestQuote.oracle_quote_id)} is the latest Oracle CPQ output.`,
      timestamp: "",
    };
  }
  if (products.length > 0) {
    return {
      kind: "recommend",
      title: "Recommend Product",
      summary: `${products.length} recommended products are ready for sales review.`,
      timestamp: "",
    };
  }

  return null;
}

/** Build the view model for the central agent workbench. */
function buildAgentWorkbenchModel({
  action,
  activity,
  finalizableQuote,
  latestQuote,
  order,
  opportunity,
  pricing,
  products,
  quotes,
  retrievedContext,
  runSteps,
  selectedProducts,
  signalGroups,
}: {
  action: AgentActionState | null;
  activity: ActivityEvent[];
  finalizableQuote: QuoteRecord | null;
  latestQuote: QuoteRecord | null;
  order: OrderRecord | null;
  opportunity: Opportunity | null;
  pricing: Pricing | null;
  products: Product[];
  quotes: QuoteRecord[];
  retrievedContext: string[];
  runSteps: RunStep[];
  selectedProducts: Product[];
  signalGroups: SignalGroup[];
}): AgentWorkbenchModel {
  const runStepIds = new Set(runSteps.map((step) => step.id));
  const quote = getActiveQuote({ finalizableQuote, latestQuote, order, quotes });
  const quoteCreated = Boolean(
    quote && findActivityEvent(activity, "quote_created", quote.oracle_quote_id),
  );
  const orderPlaced = Boolean(
    order && findActivityEvent(activity, "order_placed", order.oracle_order_id),
  );
  const supersededCount = quotes.filter((item) => item.status === "SUPERSEDED").length;

  if (action?.kind === "recommend") {
    return {
      kind: "recommend",
      title: action.title,
      subtitle: "Latest run: interpret Salesforce opportunity context, retrieve knowledge through MCP, and execute CPQ recommendation and pricing.",
      summary: action.summary,
      systems: "Salesforce + MCP/RAG + Oracle CPQ",
      systemDetail: opportunity
        ? `${displayRecordId(opportunity.sf_opportunity_id)} drove ${signalGroups.length} signal groups.`
        : "Waiting for Salesforce opportunity context.",
      output: products.length ? `${products.length} products` : "No products yet",
      outputDetail: pricing
        ? `${pricing.discounts.length} discount rule(s), ${formatCurrency(pricing.total, pricing.currency)} total`
        : "Recommendation has not been priced yet.",
      contextTitle: "Signals, RAG evidence, CPQ rules, and price",
      steps: [
        {
          name: "Salesforce.get_opportunity",
          detail: opportunity
            ? `Loaded ${displayRecordId(opportunity.sf_opportunity_id)} and customer requirements.`
            : "Select an opportunity to load Salesforce context.",
          status: opportunity ? "completed" : "pending",
        },
        {
          name: "MCP.search_knowledge",
          detail: retrievedContext.length
            ? `${retrievedContext.length} product, pricing, or playbook snippets returned.`
            : "Runs only when the command needs domain knowledge.",
          status: retrievedContext.length ? "completed" : products.length ? "active" : "pending",
        },
        {
          name: "OracleCPQ.recommend_products",
          detail: products.length
            ? `${products.length} products matched from CPQ rules.`
            : "Maps grouped signals to product rules.",
          status: products.length ? "completed" : "pending",
        },
        {
          name: "OracleCPQ.get_pricing",
          detail: pricing
            ? `Priced ${pricing.line_items.length} selected line items.`
            : "Prices the selected recommendation bundle.",
          status: pricing ? "completed" : products.length ? "active" : "pending",
        },
        {
          name: "LLMClient.generate_response",
          detail: runStepIds.has("get_pricing")
            ? "Generated the grounded recommendation summary."
            : "Explains after MCP tool outputs are available.",
          status: runStepIds.has("get_pricing") || pricing ? "completed" : "pending",
        },
      ],
    };
  }

  if (action?.kind === "quote") {
    return {
      kind: "quote",
      title: action.title,
      subtitle: "Latest run: validate sales selections, reprice the bundle, and create an Oracle CPQ quote version.",
      summary: action.summary,
      systems: "Agent + MCP + Oracle CPQ",
      systemDetail: "The middle layer passes selected products to CPQ without owning the quote record.",
      output: quote ? displayRecordId(quote.oracle_quote_id) : "No quote yet",
      outputDetail: quote
        ? `${formatStatusLabel(quote.status)} - ${formatCurrency(quote.total, quote.currency)}`
        : "Create a quote after at least one product is selected.",
      contextTitle: "Selected lines, quote record, pricing, and persistence evidence",
      steps: [
        {
          name: "Validate selected products",
          detail: `${selectedProducts.length} selected product(s) from the recommendation layer.`,
          status: selectedProducts.length ? "completed" : products.length ? "active" : "pending",
        },
        {
          name: "OracleCPQ.get_pricing",
          detail: pricing
            ? `Confirmed ${formatCurrency(pricing.total, pricing.currency)} quote-ready total.`
            : "Reprices the selected products before quote creation.",
          status: pricing ? "completed" : selectedProducts.length ? "active" : "pending",
        },
        {
          name: "OracleCPQ.create_quote",
          detail: quote
            ? `Created ${displayRecordId(quote.oracle_quote_id)}.`
            : "Creates the Oracle-owned draft quote version.",
          status: quote ? "completed" : pricing ? "active" : "pending",
        },
        {
          name: "Persist oracle_quote_id",
          detail: quote
            ? `${displayRecordId(quote.oracle_quote_id)} is linked to ${displayRecordId(quote.sf_opportunity_id)}.`
            : "Stores the source-owned quote key.",
          status: quote ? "completed" : "pending",
        },
        {
          name: "Refresh activity timeline",
          detail: quoteCreated
            ? "Quote creation event is visible in the live timeline."
            : "Timeline updates after CPQ persists the quote.",
          status: quoteCreated ? "completed" : quote ? "active" : "pending",
        },
      ],
    };
  }

  if (action?.kind === "order") {
    return {
      kind: "order",
      title: action.title,
      subtitle: "Latest run: accept the chosen Oracle CPQ quote, supersede open drafts, and place the order.",
      summary: action.summary,
      systems: "Agent + MCP + Oracle CPQ",
      systemDetail: "The app orchestrates the request; Oracle CPQ owns quote acceptance and order creation.",
      output: order ? displayRecordId(order.oracle_order_id) : "No order yet",
      outputDetail: order
        ? `${formatStatusLabel(order.status)} - ${formatCurrency(order.total, order.currency)}`
        : "Finalize a customer-ready quote to create an order.",
      contextTitle: "Accepted quote, order record, ordered lines, and timeline evidence",
      steps: [
        {
          name: "Select finalizable quote",
          detail: quote
            ? `${displayRecordId(quote.oracle_quote_id)} selected for customer acceptance.`
            : "A draft quote is required before order creation.",
          status: quote ? "completed" : "pending",
        },
        {
          name: "OracleCPQ.finalize_quote",
          detail: order
            ? `Finalized ${displayRecordId(order.oracle_quote_id)}.`
            : "MCP calls the CPQ finalization tool.",
          status: order ? "completed" : quote ? "active" : "pending",
        },
        {
          name: "Accept selected quote",
          detail: order
            ? `${displayRecordId(order.oracle_quote_id)} moved to Accepted.`
            : "Customer-selected quote becomes the accepted version.",
          status: order ? "completed" : quote ? "active" : "pending",
        },
        {
          name: "Supersede other drafts",
          detail: order
            ? `${supersededCount} competing draft quote(s) superseded.`
            : "Other draft versions stay untouched until order placement.",
          status: order ? "completed" : quote ? "active" : "pending",
        },
        {
          name: "Create oracle_order_id",
          detail: order
            ? `${displayRecordId(order.oracle_order_id)} created and linked to ${displayRecordId(order.sf_opportunity_id)}.`
            : "Creates the Oracle-owned order key.",
          status: orderPlaced ? "completed" : order ? "active" : "pending",
        },
      ],
    };
  }

  return {
    kind: "ready",
    title: "Ready for command",
    subtitle: "Select Salesforce context, then use the command assistant or manual actions to drive the agent flow.",
    summary: opportunity
      ? `${displayRecordId(opportunity.sf_opportunity_id)} is loaded. The next run will update this panel with action-specific evidence.`
      : "No opportunity selected yet.",
    systems: opportunity ? "Salesforce loaded" : "Waiting",
    systemDetail: opportunity
      ? `${opportunity.account.name} - ${opportunity.use_case}`
      : "Choose an account and opportunity to begin.",
    output: "No agent run",
    outputDetail: "Run Recommend Product, Create quote, or Create order.",
    contextTitle: "Selected context and next action",
    steps: [
      {
        name: "Salesforce context",
        detail: opportunity
          ? `${displayRecordId(opportunity.sf_opportunity_id)} selected.`
          : "Select an opportunity from the account list.",
        status: opportunity ? "completed" : "pending",
      },
      {
        name: "Command assistant",
        detail: opportunity
          ? "Ready to parse the next business command."
          : "Waiting for opportunity context.",
        status: opportunity ? "active" : "pending",
      },
      {
        name: "MCP execution",
        detail: "Tool calls appear here after the agent acts.",
        status: "pending",
      },
    ],
  };
}

/** Render contextual workbench content for recommendation, quote, order, or ready states. */
function renderWorkbenchContext({
  action,
  activity,
  finalizableQuote,
  latestQuote,
  order,
  opportunity,
  pricing,
  products,
  quotes,
  retrievedContext,
  selectedProducts,
  signalGroups,
}: {
  action: AgentWorkbenchKind;
  activity: ActivityEvent[];
  finalizableQuote: QuoteRecord | null;
  latestQuote: QuoteRecord | null;
  order: OrderRecord | null;
  opportunity: Opportunity | null;
  pricing: Pricing | null;
  products: Product[];
  quotes: QuoteRecord[];
  retrievedContext: string[];
  selectedProducts: Product[];
  signalGroups: SignalGroup[];
}) {
  const selectedLines = getSelectedLineItems(pricing, selectedProducts);
  const quote = getActiveQuote({ finalizableQuote, latestQuote, order, quotes });
  const quoteEvent = quote
    ? findActivityEvent(activity, "quote_created", quote.oracle_quote_id)
    : undefined;
  const orderEvent = order
    ? findActivityEvent(activity, "order_placed", order.oracle_order_id)
    : undefined;
  const orderLines = order?.line_items ?? quote?.line_items ?? [];

  if (action === "recommend") {
    return (
      <div className="agent-context-grid">
        <article className="action-result-card">
          <header>
            <span>Salesforce Signals</span>
            <strong>{buildAgentInterpretation(signalGroups, products)}</strong>
          </header>
          <div className="compact-pill-list">
            {signalGroups.map((group) => (
              <em key={group.label}>
                {group.label.replace(" Signals", "")}: {group.signals.length}
              </em>
            ))}
          </div>
        </article>

        <article className="action-result-card">
          <header>
            <span>MCP RAG Evidence</span>
            <strong>{retrievedContext.length ? `${retrievedContext.length} snippets returned` : "No snippets yet"}</strong>
          </header>
          {retrievedContext.length ? (
            <div className="context-snippet-list">
              {retrievedContext.slice(0, 3).map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          ) : (
            <p className="muted">Run recommendation to show search_knowledge results.</p>
          )}
        </article>

        <article className="action-result-card">
          <header>
            <span>CPQ Rule Matches</span>
            <strong>{buildRecommendationStrategy(products, pricing)}</strong>
          </header>
          {products.length ? (
            <div className="context-result-list">
              {products.slice(0, 4).map((product) => (
                <p key={product.sku}>
                  <span>{product.rule_id ?? "CPQ-RULE"}</span>
                  <strong>{product.name}</strong>
                </p>
              ))}
            </div>
          ) : (
            <p className="muted">No product rules have run yet.</p>
          )}
        </article>

        <article className="action-result-card">
          <header>
            <span>Pricing Result</span>
            <strong>{pricing ? formatCurrency(pricing.total, pricing.currency) : "Pending"}</strong>
          </header>
          {pricing ? (
            <div className="mini-metric-grid">
              <div>
                <span>Subtotal</span>
                <strong>{formatCurrency(pricing.subtotal, pricing.currency)}</strong>
              </div>
              <div>
                <span>Discount</span>
                <strong>{formatCurrency(pricing.discount, pricing.currency)}</strong>
              </div>
              <div>
                <span>Lines</span>
                <strong>{String(pricing.line_items.length)}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">CPQ pricing appears after product recommendation.</p>
          )}
        </article>
      </div>
    );
  }

  if (action === "quote") {
    return (
      <div className="agent-context-grid">
        <article className="action-result-card">
          <header>
            <span>Selected Lines</span>
            <strong>{selectedLines.length ? `${selectedLines.length} quote line items` : "No selected lines"}</strong>
          </header>
          {selectedLines.length ? (
            <div className="context-result-list">
              {selectedLines.slice(0, 4).map((line) => (
                <p key={line.sku}>
                  <span>{line.sku}</span>
                  <strong>
                    {line.name} - Qty {line.quantity} - {formatCurrency(line.net_price, pricing?.currency ?? "USD")}
                  </strong>
                </p>
              ))}
            </div>
          ) : (
            <p className="muted">Select products before creating a quote.</p>
          )}
        </article>

        <article className="action-result-card">
          <header>
            <span>Oracle Quote Record</span>
            <strong>{quote ? displayRecordId(quote.oracle_quote_id) : "Not created"}</strong>
          </header>
          <div className="mini-metric-grid">
            <div>
              <span>Status</span>
              <strong>{formatStatusLabel(quote?.status)}</strong>
            </div>
            <div>
              <span>Total</span>
              <strong>{quote ? formatCurrency(quote.total, quote.currency) : "-"}</strong>
            </div>
            <div>
              <span>Source Link</span>
              <strong>{displayRecordId(quote?.sf_opportunity_id ?? opportunity?.sf_opportunity_id ?? "-")}</strong>
            </div>
          </div>
        </article>

        <article className="action-result-card">
          <header>
            <span>Pricing Snapshot</span>
            <strong>{pricing ? `${pricing.discount_percent}% discount` : "Pending"}</strong>
          </header>
          {pricing ? (
            <div className="context-result-list">
              {pricing.discounts.length ? (
                pricing.discounts.map((discount) => (
                  <p key={discount.code}>
                    <span>{discount.code}</span>
                    <strong>{discount.label}</strong>
                  </p>
                ))
              ) : (
                <p>
                  <span>CPQ</span>
                  <strong>No discount rule applied.</strong>
                </p>
              )}
            </div>
          ) : (
            <p className="muted">Pricing is required before quote creation.</p>
          )}
        </article>

        <article className="action-result-card">
          <header>
            <span>Persistence Evidence</span>
            <strong>{quoteEvent?.title ?? "Awaiting timeline event"}</strong>
          </header>
          <p className="muted">
            {quoteEvent?.detail
              ? displayRecordIdsInText(quoteEvent.detail)
              : "Oracle CPQ quote creation events appear here after the quote is persisted."}
          </p>
        </article>
      </div>
    );
  }

  if (action === "order") {
    return (
      <div className="agent-context-grid">
        <article className="action-result-card">
          <header>
            <span>Accepted Quote</span>
            <strong>
              {order?.oracle_quote_id ?? quote?.oracle_quote_id
                ? displayRecordId(order?.oracle_quote_id ?? quote?.oracle_quote_id)
                : "No accepted quote"}
            </strong>
          </header>
          <div className="mini-metric-grid">
            <div>
              <span>Status</span>
              <strong>{formatStatusLabel(quote?.status ?? (order ? "ACCEPTED" : undefined))}</strong>
            </div>
            <div>
              <span>Quote Total</span>
              <strong>{quote ? formatCurrency(quote.total, quote.currency) : "-"}</strong>
            </div>
            <div>
              <span>Superseded</span>
              <strong>{String(quotes.filter((item) => item.status === "SUPERSEDED").length)}</strong>
            </div>
          </div>
        </article>

        <article className="action-result-card">
          <header>
            <span>Oracle Order Record</span>
            <strong>{order ? displayRecordId(order.oracle_order_id) : "Not placed"}</strong>
          </header>
          <div className="mini-metric-grid">
            <div>
              <span>Status</span>
              <strong>{formatStatusLabel(order?.status)}</strong>
            </div>
            <div>
              <span>Total</span>
              <strong>{order ? formatCurrency(order.total, order.currency) : "-"}</strong>
            </div>
            <div>
              <span>Source Link</span>
              <strong>{displayRecordId(order?.sf_opportunity_id ?? opportunity?.sf_opportunity_id ?? "-")}</strong>
            </div>
          </div>
        </article>

        <article className="action-result-card">
          <header>
            <span>Ordered Lines</span>
            <strong>{orderLines.length ? `${orderLines.length} items` : "No order lines"}</strong>
          </header>
          {orderLines.length ? (
            <div className="context-result-list">
              {orderLines.slice(0, 4).map((line) => (
                <p key={line.sku}>
                  <span>{line.sku}</span>
                  <strong>
                    {line.name} - Qty {line.quantity} - {formatCurrency(line.net_price, order?.currency ?? quote?.currency ?? "USD")}
                  </strong>
                </p>
              ))}
            </div>
          ) : (
            <p className="muted">Order lines appear after CPQ places the order.</p>
          )}
        </article>

        <article className="action-result-card">
          <header>
            <span>Timeline Evidence</span>
            <strong>{orderEvent?.title ?? "Awaiting order event"}</strong>
          </header>
          <p className="muted">
            {orderEvent?.detail
              ? displayRecordIdsInText(orderEvent.detail)
              : "Oracle CPQ order placement events appear here after finalization."}
          </p>
        </article>
      </div>
    );
  }

  return (
    <div className="agent-context-grid">
      <article className="action-result-card">
        <header>
          <span>Salesforce Context</span>
          <strong>{opportunity ? displayRecordId(opportunity.sf_opportunity_id) : "No opportunity selected"}</strong>
        </header>
        <p className="muted">
          {opportunity
            ? `${opportunity.name} - ${opportunity.account.name}`
            : "Choose an account and opportunity to load business context."}
        </p>
      </article>
      <article className="action-result-card">
        <header>
          <span>Next Command</span>
          <strong>{products.length ? "Create quote" : "Recommend Product"}</strong>
        </header>
        <p className="muted">
          {products.length
            ? "The agent will use selected products and CPQ pricing to create the quote."
            : "The agent will retrieve knowledge, call CPQ recommendation rules, and price the bundle."}
        </p>
      </article>
    </div>
  );
}

/** Choose the quote that is currently actionable in the UI. */
function getActiveQuote({
  finalizableQuote,
  latestQuote,
  order,
  quotes,
}: {
  finalizableQuote: QuoteRecord | null;
  latestQuote: QuoteRecord | null;
  order: OrderRecord | null;
  quotes: QuoteRecord[];
}) {
  if (order) {
    return (
      quotes.find((quote) => quote.oracle_quote_id === order.oracle_quote_id) ??
      (latestQuote?.oracle_quote_id === order.oracle_quote_id ? latestQuote : null)
    );
  }

  return latestQuote ?? finalizableQuote ?? [...quotes].reverse().find(isFinalizableQuote) ?? null;
}

/** Find the latest activity event matching the requested type and object id. */
function findActivityEvent(
  activity: ActivityEvent[],
  eventType: string,
  sourceId?: string,
) {
  return activity.find((event) => {
    if (event.event_type !== eventType) {
      return false;
    }
    if (!sourceId) {
      return true;
    }

    return (
      event.oracle_quote_id === sourceId ||
      event.oracle_order_id === sourceId ||
      event.sf_opportunity_id === sourceId
    );
  });
}

/** Return priced line items that correspond to selected products. */
function getSelectedLineItems(pricing: Pricing | null, selectedProducts: Product[]) {
  if (!pricing) {
    return [];
  }

  const selectedSkus = new Set(selectedProducts.map((product) => product.sku));
  if (selectedSkus.size === 0) {
    return pricing.line_items;
  }

  return pricing.line_items.filter((line) => selectedSkus.has(line.sku));
}

/** Group opportunity requirements into readable signal categories. */
function groupOpportunitySignals(requirements: string[]): SignalGroup[] {
  const definitions = [
    {
      label: "Resilience + Cloud Signals",
      summary: "Used to add hybrid cloud and disaster recovery coverage.",
      keywords: ["hybrid cloud", "disaster recovery", "dr", "cloud", "recovery", "resilience"],
    },
    {
      label: "Workload Signals",
      summary: "Used to choose core storage platforms.",
      keywords: [
        "billing",
        "subscriber",
        "database",
        "block",
        "san",
        "vmware",
        "low latency",
        "5g edge",
        "edge",
      ],
    },
    {
      label: "Data + Analytics Signals",
      summary: "Used to identify object, archive, and analytics needs.",
      keywords: ["telemetry", "logs", "cdr", "archive", "data lake", "object", "analytics", "ai"],
    },
    {
      label: "Delivery + Operations Signals",
      summary: "Used to add services, support, and operating model coverage.",
      keywords: ["professional services", "migration", "deployment", "support", "premium", "management", "operations"],
    },
  ];
  const groups = definitions.map(({ label, summary }) => ({
    label,
    summary,
    signals: [] as string[],
  }));
  const unmatched: string[] = [];

  for (const requirement of requirements) {
    const normalized = requirement.toLowerCase();
    const scoredDefinitions = definitions
      .map((definition, index) => ({
        index,
        score: definition.keywords.filter((keyword) => normalized.includes(keyword)).length,
      }))
      .filter((item) => item.score > 0)
      .sort((first, second) => second.score - first.score);
    if (scoredDefinitions.length > 0) {
      groups[scoredDefinitions[0].index].signals.push(requirement);
    } else {
      unmatched.push(requirement);
    }
  }

  const visibleGroups = groups.filter((group) => group.signals.length > 0);
  if (unmatched.length > 0) {
    visibleGroups.push({
      label: "Other Customer Signals",
      summary: "Kept available for agent review and explanation.",
      signals: unmatched,
    });
  }

  if (visibleGroups.length === 0) {
    return [
      {
        label: "Customer Signals",
        summary: "Select an opportunity to load recommendation evidence.",
        signals: ["No opportunity selected yet."],
      },
    ];
  }

  return visibleGroups;
}

/** Summarize opportunity signals and recommended products for the workbench. */
function buildAgentInterpretation(signalGroups: SignalGroup[], products: Product[]) {
  if (products.length > 0) {
    const ruleCount = new Set(products.map((product) => product.rule_id).filter(Boolean)).size;
    return `${signalGroups.length} groups -> ${products.length} products -> ${ruleCount} CPQ rules`;
  }

  return `${signalGroups.length} signal groups ready for recommendation`;
}

/** Summarize the pricing and product strategy behind a recommendation. */
function buildRecommendationStrategy(products: Product[], pricing: Pricing | null) {
  if (pricing) {
    return `${pricing.discounts.length} discount rule(s), quote-ready total ${formatCurrency(pricing.total, pricing.currency)}`;
  }
  if (products.length > 0) {
    return "Products selected; pricing responds to quantity, term, and selection changes";
  }

  return "Awaiting recommendation run";
}

/** Infer the command intent from the sales rep command text. */
function resolveCommandIntent(command: string): CommandIntent {
  const normalized = command.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  if (
    normalized.includes("create order") ||
    normalized.includes("place order") ||
    normalized.includes("finalize") ||
    normalized.includes("accept quote")
  ) {
    return "create_order";
  }
  if (normalized.includes("create quote") || normalized.includes("draft quote")) {
    return "create_quote";
  }
  if (
    normalized.includes("recommend") ||
    normalized.includes("recomend") ||
    normalized.includes("product") ||
    normalized.includes("price") ||
    normalized.includes("pricing")
  ) {
    return "recommend";
  }

  return null;
}

/** Return the primary command button label for the current status and intent. */
function commandButtonLabel(status: string, intent: CommandIntent) {
  if (status === "running") {
    return "Recommending...";
  }
  if (status === "quoting") {
    return "Creating quote...";
  }
  if (status === "finalizing") {
    return "Creating order...";
  }
  if (intent) {
    return "Run Command";
  }

  return "Execute";
}

/** Return whether a quote can still be accepted into an order. */
function isFinalizableQuote(quote: QuoteRecord) {
  return quote.status !== "SUPERSEDED" && quote.status !== "ACCEPTED";
}

/** Choose the next guided action for the selected deal state. */
function buildNextBestAction({
  finalizableQuote,
  opportunity,
  order,
  products,
  selectedProducts,
}: {
  finalizableQuote: QuoteRecord | null;
  opportunity: Opportunity | null;
  order: OrderRecord | null;
  products: Product[];
  selectedProducts: Product[];
}) {
  if (!opportunity) {
    return "Select a Salesforce account, then choose one of its opportunities.";
  }
  if (order) {
    return `Order ${displayRecordId(order.oracle_order_id)} is placed. Review Architecture View for the full trace.`;
  }
  if (finalizableQuote) {
    return `Run Create Order to finalize quote ${displayRecordId(finalizableQuote.oracle_quote_id)}.`;
  }
  if (products.length === 0) {
    return `Run Recommend Product for ${displayRecordId(opportunity.sf_opportunity_id)}.`;
  }
  if (selectedProducts.length === 0) {
    return "Select at least one recommended product before creating a quote.";
  }

  return `Review ${selectedProducts.length} selected products, then run Create Quote.`;
}

/** Build the command text and intent for the next guided action. */
function buildSuggestedCommand({
  finalizableQuote,
  opportunity,
  order,
  products,
  selectedProducts,
}: {
  finalizableQuote: QuoteRecord | null;
  opportunity: Opportunity | null;
  order: OrderRecord | null;
  products: Product[];
  selectedProducts: Product[];
}): SuggestedCommand {
  if (!opportunity) {
    return {
      text: "Select a Salesforce opportunity",
      intent: null,
    };
  }
  if (order) {
    return {
      text: "Review Architecture View",
      intent: null,
    };
  }
  if (finalizableQuote) {
    return {
      text: "Create order",
      intent: "create_order",
    };
  }
  if (products.length === 0) {
    return {
      text: "Recommend Product",
      intent: "recommend",
    };
  }
  if (selectedProducts.length === 0) {
    return {
      text: "Select at least one product",
      intent: null,
    };
  }

  return {
    text: "Create quote",
    intent: "create_quote",
  };
}

/** Build the backend recommendation prompt from the command and selected opportunity. */
function buildRecommendationRequestMessage(command: string, opportunity: Opportunity | null) {
  const baseCommand = command || defaultCommand;
  if (!opportunity) {
    return baseCommand;
  }

  return [
    baseCommand,
    `Recommend NetApp-aligned products for telecom/network infrastructure opportunity ${opportunity.sf_opportunity_id}.`,
    `Opportunity: ${opportunity.name}.`,
    `Use case: ${opportunity.use_case}.`,
    `Account industry: ${opportunity.account.industry}.`,
    `Requirements: ${opportunity.requirements.join("; ")}.`,
    "Use product catalog, pricing rules, sales playbook, and Oracle CPQ handoff context.",
  ].join(" ");
}

/** Shorten enterprise record ids for dense UI surfaces. */
function displayRecordId(value?: string | null) {
  if (!value || value === "-") {
    return value ?? "-";
  }

  return value
    .replace(/^ORA-QUOTE-SF-OPP-(\d+)-(\d+)$/, "ORA-Q-$1-$2")
    .replace(/^ORA-ORDER-SF-OPP-(\d+)-(\d+)$/, "ORA-O-$1-$2")
    .replace(/^ORA-QUOTE-(.+)$/, "ORA-Q-$1")
    .replace(/^ORA-ORDER-(.+)$/, "ORA-O-$1")
    .replace(/^SF-ACC-(\d+)$/, "SF-A-$1")
    .replace(/^SF-OPP-(\d+)$/, "SF-O-$1");
}

/** Shorten all known record ids inside a free-form message. */
function displayRecordIdsInText(value: string) {
  return value
    .replace(/\bORA-QUOTE-SF-OPP-(\d+)-(\d+)\b/g, "ORA-Q-$1-$2")
    .replace(/\bORA-ORDER-SF-OPP-(\d+)-(\d+)\b/g, "ORA-O-$1-$2")
    .replace(/\bORA-QUOTE-([A-Z0-9-]+)\b/g, "ORA-Q-$1")
    .replace(/\bORA-ORDER-([A-Z0-9-]+)\b/g, "ORA-O-$1")
    .replace(/\bSF-ACC-(\d+)\b/g, "SF-A-$1")
    .replace(/\bSF-OPP-(\d+)\b/g, "SF-O-$1");
}

/** Format enum-like status values for user-facing UI labels. */
function formatStatusLabel(value?: string) {
  if (!value) {
    return "-";
  }

  return value
    .toLowerCase()
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Format provider profile keys for loading or fallback display. */
function formatProfileKey(profileKey: string) {
  if (profileKey === "generic-kubernetes") {
    return "Generic Kubernetes";
  }
  if (profileKey === "gcp" || profileKey === "oci") {
    return profileKey.toUpperCase();
  }

  return profileKey.charAt(0).toUpperCase() + profileKey.slice(1);
}

/** Normalize unknown caught values into a displayable error message. */
function errorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "Unable to complete request.";
}

/** Format money values using the selected currency. */
function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    currency,
    maximumFractionDigits: 0,
    style: "currency",
  }).format(amount);
}

/** Format ISO timestamps for the sales workbench. */
function formatDateTime(value?: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

/** Format just the calendar date for compact timeline rows. */
function formatDatePart(value?: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "short",
  }).format(date);
}

/** Format just the clock time for compact timeline rows. */
function formatTimePart(value?: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/** Trim assistant responses for compact workbench display. */
function compactAssistantMessage(message: string) {
  const cleaned = message.replace(/\*\*/g, "").replace(/\s+/g, " ").trim();
  if (cleaned.length <= 180) {
    return cleaned;
  }

  return `${cleaned.slice(0, 177).trim()}...`;
}

/** Serialize payload data for the architecture trace panels. */
function formatPayload(payload: unknown) {
  if (payload === null || payload === undefined) {
    return "-";
  }
  if (typeof payload === "string") {
    return payload || "-";
  }
  if (Array.isArray(payload) && payload.length === 0) {
    return "[]";
  }
  if (typeof payload === "object" && Object.keys(payload).length === 0) {
    return "{}";
  }

  return JSON.stringify(payload, null, 2);
}
