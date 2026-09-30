import { Plugin } from "@opencode/plugin";
import {
  createBoundedReceiptSink,
  createBoundedResponseReceiptSink,
  createNoProviderHttpHook,
  createSyntheticRequestObserver,
  createSyntheticResponseObserver,
} from "./observer.mjs";
import { createCapturePlugin } from "./plugin_setup.mjs";

const enabled = process.env.WRENCH_SYNTHETIC_CAPTURE === "1";

const WrenchSubRouteSyntheticCapture = Plugin.define(createCapturePlugin({
  enabled,
  arm: process.env.WRENCH_CAPTURE_ARM,
  createObserver: createSyntheticRequestObserver,
  createResponseObserver: createSyntheticResponseObserver,
  createNoProviderHttpHook,
  createReceiptSink: createBoundedReceiptSink,
  createResponseReceiptSink: createBoundedResponseReceiptSink,
}));

export { WrenchSubRouteSyntheticCapture };
export default WrenchSubRouteSyntheticCapture;
