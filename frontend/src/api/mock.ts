// pywebview が存在しない開発環境（ブラウザで npm run dev を直接開いた場合）用のモック。
// Nocturneデザインハンドオフのサンプルデータに合わせている。
import type { ApiResult, Bootstrap, CredentialResult, ServerEntry } from "../types";

function mkServer(partial: Partial<ServerEntry>): ServerEntry {
  return {
    name: "", host: "", os: "linux", user: "", port: "", key: "",
    ssh_client: "", note: "", op_item: "", op_vault: "", tags: "",
    has_credential: false, auth_mode: "", auth_has_op_item: false,
    ...partial,
  };
}

const mockData: Bootstrap = {
  version: "3.0.0-dev",
  config: {
    ssh_default_client: "windowsterminal",
    ssh_teraterm_path: "C:\\Program Files\\teraterm\\ttermpro.exe",
    ssh_default_user: "",
    ssh_default_key: "",
    rdp_width: "", rdp_height: "", rdp_multimon: false,
    ssh_default_port: "22",
    gui_title: "EazyConnecter",
    gui_width: 1240, gui_height: 720, gui_font_size: 10,
    op_mode: "op", op_sa_token_enc: "", op_connect_host: "http://localhost:8080", op_connect_token_enc: "",
  },
  groups: [
    {
      name: "管理系",
      servers: [
        mkServer({ name: "踏み台サーバー", host: "192.168.1.10", os: "linux", port: "22", user: "opsadmin", tags: "踏み台,本番,鍵認証", note: "本番環境への踏み台", has_credential: true, auth_mode: "dpapi" }),
        mkServer({ name: "Zabbix監視サーバー", host: "192.168.1.20", os: "linux", port: "22", user: "zbxops", tags: "監視,本番", note: "Zabbix 7.4", has_credential: true, auth_mode: "dpapi" }),
      ],
    },
    {
      name: "Windows",
      servers: [
        mkServer({ name: "ファイルサーバー", host: "192.168.1.30", os: "windows", port: "3389", user: "DVMN\\svc-rdp", tags: "本番,ファイル共有", note: "DVMN-FS-01", has_credential: true, auth_mode: "dpapi" }),
        mkServer({ name: "バックアップサーバー (Veeam)", host: "192.168.1.31", os: "windows", port: "3389", user: "DVMN\\svc-rdp", tags: "本番,バックアップ", note: "DVMN-BK-01", has_credential: true, auth_mode: "dpapi" }),
      ],
    },
    {
      name: "Linux",
      servers: [
        mkServer({ name: "Webサーバー", host: "192.168.1.40", os: "linux", port: "2222", user: "deploy", tags: "本番,Web,鍵認証", note: "Apache / 冗長1号機", has_credential: true, auth_mode: "dpapi" }),
        mkServer({ name: "Webサーバー", host: "192.168.1.41", os: "linux", port: "22", user: "deploy", tags: "検証,Web", note: "TeraTerm指定" }),
        mkServer({ name: "DBサーバー", host: "192.168.1.50", os: "linux", port: "22", user: "dbadmin", tags: "本番,DB,鍵認証", note: "鍵認証専用", has_credential: true, auth_mode: "dpapi" }),
      ],
    },
  ],
};

export async function getBootstrap(): Promise<Bootstrap> {
  return JSON.parse(JSON.stringify(mockData));
}

export async function connect(host: string): Promise<ApiResult> {
  console.info(`[mock] connect(${host})`);
  return { ok: true };
}

export async function saveCredential(): Promise<ApiResult> {
  return { ok: true };
}

export async function deleteCredential(): Promise<ApiResult> {
  return { ok: true };
}

export async function getCredential(): Promise<CredentialResult> {
  return { ok: false };
}

export async function fetchFrom1Password(): Promise<CredentialResult> {
  return { ok: false, error: "開発モードでは1Password連携は利用できません（モックです）。" };
}

export async function openConfigFolder(): Promise<ApiResult> {
  return { ok: true };
}
