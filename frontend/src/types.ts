export interface ServerEntry {
  name: string;
  host: string;
  os: string; // "windows" | "linux"
  user: string;
  port: string;
  key: string;
  ssh_client: string;
  note: string;
  op_item: string;
  op_vault: string;
  tags: string; // カンマ区切り
  has_credential: boolean;
  auth_mode: string; // "" | "dpapi" | "always"
  auth_has_op_item: boolean;
}

export interface ServerGroup {
  name: string;
  servers: ServerEntry[];
}

export interface AppConfig {
  ssh_default_client: string;
  ssh_teraterm_path: string;
  ssh_default_user: string;
  ssh_default_key: string;
  ssh_default_port: string;
  rdp_width: string;
  rdp_height: string;
  rdp_multimon: boolean;
  gui_title: string;
  gui_width: number;
  gui_height: number;
  gui_font_size: number;
  op_mode: string;
  op_sa_token_enc: string;
  op_connect_host: string;
  op_connect_token_enc: string;
}

export interface Bootstrap {
  version: string;
  config: AppConfig;
  groups: ServerGroup[];
}

export interface ApiResult {
  ok: boolean;
  error?: string;
  notice?: string;
}

export interface CredentialResult extends ApiResult {
  username?: string;
  password?: string;
}
