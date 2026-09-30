export const PLUGIN_ID = "wrench-subroute-synthetic-capture-v2-0-12";

/**
 * Build the public OpenCode plugin definition separately from the SDK adapter.
 * This keeps registration, disposal, and the fail-closed request callback
 * directly testable without loading an OpenCode process or provider.
 */
export function createCapturePlugin({
  enabled,
  arm,
  createObserver,
  createResponseObserver,
  createNoProviderHttpHook,
  createReceiptSink,
  createResponseReceiptSink,
}) {
  if (typeof enabled !== "boolean") throw new TypeError("enabled_must_be_boolean");
  if (enabled) {
    for (const [name, value] of Object.entries({
      createObserver,
      createResponseObserver,
      createNoProviderHttpHook,
      createReceiptSink,
      createResponseReceiptSink,
    })) {
      if (typeof value !== "function") throw new TypeError(`${name}_required`);
    }
  }

  return {
    id: PLUGIN_ID,
    async setup(context) {
      if (!enabled) return;
      if (typeof context?.session?.hook !== "function") {
        throw new TypeError("session_http_hook_unavailable");
      }

      const sink = createReceiptSink(arm);
      if (typeof sink?.emit !== "function") throw new TypeError("receipt_sink_invalid");
      const responseSink = createResponseReceiptSink(arm);
      if (typeof responseSink?.emit !== "function") throw new TypeError("response_receipt_sink_invalid");
      const captureState = { sessionID: null };
      const observer = createObserver({
        enabled: true,
        arm,
        state: captureState,
        emit: (receipt) => sink.emit(receipt),
      });
      const callback = createNoProviderHttpHook(observer);
      const responseObserver = createResponseObserver({
        enabled: true,
        arm,
        state: captureState,
        emit: (receipt) => responseSink.emit(receipt),
      });
      const registrations = [];
      try {
        const requestRegistration = await context.session.hook("http.request", callback);
        if (typeof requestRegistration?.dispose !== "function") {
          throw new TypeError("http_request_hook_registration_invalid");
        }
        registrations.push(requestRegistration);
        const responseRegistration = await context.session.hook("http.response", responseObserver);
        if (typeof responseRegistration?.dispose !== "function") {
          throw new TypeError("http_response_hook_registration_invalid");
        }
        registrations.push(responseRegistration);
      } catch (error) {
        await Promise.allSettled(registrations.map((registration) => registration.dispose()));
        throw error;
      }

      if (registrations.length !== 2) {
        throw new TypeError("http_hook_registration_invalid");
      }

      let disposed = false;
      return async () => {
        if (disposed) return;
        disposed = true;
        await Promise.all(registrations.map((registration) => registration.dispose()));
      };
    },
  };
}
