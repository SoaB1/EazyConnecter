"""YAML 簡易パーサー（config.yaml / servers.yaml、標準ライブラリのみ）"""
import os
import re


def parse_yaml_config(path):
    defaults = {
        "ssh_default_client":     "windowsterminal",
        "ssh_teraterm_path":      r"C:\Program Files\teraterm\ttermpro.exe",
        "ssh_default_user":       "",
        "ssh_default_key":        "",
        "ssh_default_port":       "22",
        "rdp_width":              "",
        "rdp_height":             "",
        "rdp_multimon":           False,
        "gui_title":              "EazyConnecter",
        "gui_width":              760,
        "gui_height":             560,
        "gui_font_size":          10,
        # 1Password 連携設定
        "op_mode":                "op",            # op / service_account / connect
        "op_sa_token_enc":        "",              # Service Account トークン（DPAPI暗号化済み）
        "op_connect_host":        "http://localhost:8080",
        "op_connect_token_enc":   "",              # Connect トークン（DPAPI暗号化済み）
    }
    if not os.path.exists(path):
        return defaults
    section = ""
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = re.sub(r'\s*#.*$', '', raw)
            stripped = line.strip()
            if not stripped: continue
            indent = len(line) - len(line.lstrip())
            if indent == 0 and re.match(r'^(\w+):\s*$', stripped):
                section = re.match(r'^(\w+):', stripped).group(1); continue
            m = re.match(r'^([\w_]+):\s*"?([^"#]*)"?\s*$', stripped)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                key = f"{section}_{k}"
                if   key == "ssh_default_client": defaults["ssh_default_client"] = v
                elif key == "ssh_teraterm_path":  defaults["ssh_teraterm_path"]  = v
                elif key == "ssh_default_user":   defaults["ssh_default_user"]   = v
                elif key == "ssh_default_key":    defaults["ssh_default_key"]    = v
                elif key == "ssh_default_port":   defaults["ssh_default_port"]   = v
                elif key == "rdp_width":          defaults["rdp_width"]          = v
                elif key == "rdp_height":         defaults["rdp_height"]         = v
                elif key == "rdp_multimon":       defaults["rdp_multimon"]       = (v == "true")
                elif key == "gui_title":          defaults["gui_title"]          = v
                elif key == "gui_window_width":   defaults["gui_width"]          = int(v)
                elif key == "gui_window_height":  defaults["gui_height"]         = int(v)
                elif key == "gui_font_size":         defaults["gui_font_size"]          = int(v)
                elif key == "onepassword_mode":              defaults["op_mode"]                = v
                elif key == "onepassword_sa_token_enc":      defaults["op_sa_token_enc"]        = v
                elif key == "onepassword_connect_host":      defaults["op_connect_host"]        = v
                elif key == "onepassword_connect_token_enc": defaults["op_connect_token_enc"]   = v
    return defaults


def parse_yaml_servers(path):
    groups = []
    cur_group = cur_server = None
    in_groups = in_servers = False

    def new_server():
        return {"name":"","host":"","os":"linux","user":"","port":"","key":"","ssh_client":"","note":"","op_item":"","op_vault":"","tags":""}

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = re.sub(r'\s*#.*$', '', raw)
            stripped = line.strip()
            if not stripped: continue
            indent = len(line) - len(line.lstrip())

            if indent == 0 and stripped == "groups:":
                in_groups = True; in_servers = False; continue
            if not in_groups: continue

            if indent == 2 and stripped == "-":
                if cur_server and cur_group is not None:
                    cur_group["servers"].append(cur_server); cur_server = None
                if cur_group is not None: groups.append(cur_group)
                cur_group = {"name":"","servers":[]}; in_servers = False; continue

            m = re.match(r'^-\s+name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 2 and m:
                if cur_server and cur_group is not None:
                    cur_group["servers"].append(cur_server); cur_server = None
                if cur_group is not None: groups.append(cur_group)
                cur_group = {"name": m.group(1).strip(), "servers":[]}; in_servers = False; continue

            m = re.match(r'^name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 4 and m and cur_group is not None and not in_servers:
                cur_group["name"] = m.group(1).strip(); continue

            if indent == 4 and stripped == "servers:":
                in_servers = True; continue
            if not in_servers: continue

            m = re.match(r'^-\s+name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 6 and m:
                if cur_server: cur_group["servers"].append(cur_server)
                cur_server = new_server(); cur_server["name"] = m.group(1).strip(); continue

            if indent == 6 and stripped == "-":
                if cur_server: cur_group["servers"].append(cur_server)
                cur_server = new_server(); continue

            m = re.match(r'^([\w_]+):\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 8 and m and cur_server is not None:
                k, v = m.group(1).strip(), m.group(2).strip()
                if k in cur_server: cur_server[k] = v
                continue
            # op_item / op_vault（YAMLのkeyがアンダースコア区切り）
            m2 = re.match(r"^(op_item|op_vault):\s*\"?([^\"#]*)\"?\s*$", stripped)
            if indent == 8 and m2 and cur_server is not None:
                cur_server[m2.group(1)] = m2.group(2).strip()
                continue

    if cur_server and cur_group is not None: cur_group["servers"].append(cur_server)
    if cur_group is not None: groups.append(cur_group)
    return groups
