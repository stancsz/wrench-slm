# OpenCode setup for the existing SubRoute

This example points OpenCode v2.0.12 at the existing local SubRoute service.
It targets `http://127.0.0.1:4000/v1` and sends the gateway alias `openrouter`,
which the current force route maps to `openrouter/minimax/minimax-m3`.

Copy the `provider` object from
[`opencode.subroute.example.json`](opencode.subroute.example.json) into the
project's existing `opencode.json`. Keep its other settings. The selectable
model reference becomes `wrench-subroute/openrouter`; the example does not set
it as OpenCode's default model. Configure `WRENCH_SUBROUTE_API_KEY` in the
OpenCode process environment if the local gateway requires authentication.
Do not put a key in this repository.

The example uses OpenCode v2.0.12's documented custom-provider fields:
`provider`, `npm`, `options.baseURL`, `options.apiKey`, and `models`. Its
32,768 context and 8,192 output limits are conservative client-side settings,
not a hard token or spend cap. The Wrench gateway's durable campaign ledger is
not wired into arbitrary OpenCode requests.

The observer plugin in this directory remains opt-in. With
`WRENCH_SYNTHETIC_CAPTURE=1`, it only accepts the pinned synthetic request,
writes a bounded content-free receipt, then fails before HTTP transport. Leave
that variable unset for ordinary OpenCode behavior. Ordinary requests to this
route can incur provider charges. Do not use them for the Wrench comparison
until the campaign-wide caller, numeric cap, and billing receipts gate them.

The latest read-only metadata advertises tool-call support, but no completion
or tool round trip has verified it. Do not infer agent compatibility from the
model-info flag. The current experiment still needs a no-provider OpenCode
runtime preflight, then an explicitly capped end-to-end request before any
effectiveness or cost conclusion.

Sources: [OpenCode v2.0.12 provider configuration](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/web/src/content/docs/providers.mdx#custom-provider), [SubRoute iteration 039](../../docs/evals/wrench-gateway-model-research/iteration-039-subroute-opencode-setup-20260927.md).
