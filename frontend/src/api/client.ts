// window.pywebview.api (Promiseベース) の薄いラッパー。
// pywebview が存在しない場合（ブラウザ単体でのフロントエンド開発時）は mock にフォールバックする。
import type { ApiResult, Bootstrap, CredentialResult } from "../types";
import * as mock from "./mock";

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_bootstrap(): Promise<Bootstrap>;
        reload(): Promise<Bootstrap>;
        connect(host: string): Promise<ApiResult>;
        get_credential(host: string): Promise<CredentialResult>;
        save_credential(
          host: string, username: string, password: string,
          opItem: string, opVault: string, opMode: string
        ): Promise<ApiResult>;
        delete_credential(host: string): Promise<ApiResult>;
        fetch_from_1password(item: string, vault: string): Promise<CredentialResult>;
        open_config_folder(): Promise<ApiResult>;
      };
    };
  }
}

function hasPywebview(): boolean {
  return typeof window !== "undefined" && !!window.pywebview?.api;
}

/** pywebview の初期化完了 (pywebviewready イベント) を待つ。開発モードでは即解決する。 */
export function waitForPywebviewReady(): Promise<void> {
  if (hasPywebview()) return Promise.resolve();
  return new Promise((resolve) => {
    const onReady = () => resolve();
    window.addEventListener("pywebviewready", onReady, { once: true });
    // pywebview不在（ブラウザ単体デバッグ）でも進行できるようフォールバック
    setTimeout(resolve, 300);
  });
}

export async function getBootstrap(): Promise<Bootstrap> {
  return hasPywebview() ? window.pywebview!.api.get_bootstrap() : mock.getBootstrap();
}

export async function reload(): Promise<Bootstrap> {
  return hasPywebview() ? window.pywebview!.api.reload() : mock.getBootstrap();
}

export async function connect(host: string): Promise<ApiResult> {
  return hasPywebview() ? window.pywebview!.api.connect(host) : mock.connect(host);
}

export async function getCredential(host: string): Promise<CredentialResult> {
  return hasPywebview() ? window.pywebview!.api.get_credential(host) : mock.getCredential();
}

export async function saveCredential(
  host: string, username: string, password: string,
  opItem: string, opVault: string, opMode: string
): Promise<ApiResult> {
  return hasPywebview()
    ? window.pywebview!.api.save_credential(host, username, password, opItem, opVault, opMode)
    : mock.saveCredential();
}

export async function deleteCredential(host: string): Promise<ApiResult> {
  return hasPywebview() ? window.pywebview!.api.delete_credential(host) : mock.deleteCredential();
}

export async function fetchFrom1Password(item: string, vault: string): Promise<CredentialResult> {
  return hasPywebview()
    ? window.pywebview!.api.fetch_from_1password(item, vault)
    : mock.fetchFrom1Password();
}

export async function openConfigFolder(): Promise<ApiResult> {
  return hasPywebview() ? window.pywebview!.api.open_config_folder() : mock.openConfigFolder();
}
