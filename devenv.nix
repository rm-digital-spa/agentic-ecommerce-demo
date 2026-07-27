{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

# Secrets (API keys, account-specific ids) live in devenv.local.nix — gitignored.
# Copy the env.* entries you need there; see .env.example for the full list.
{
  env.LANGFUSE_BASE_URL = "http://localhost:3000";
  env.BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0";

  env.SII_MCP_PORT = 8001;
  env.SII_MCP_URL = "http://localhost:${builtins.toString config.env.SII_MCP_PORT}/mcp";
  env.SII_MCP_BASE_URL = "http://localhost:${builtins.toString config.env.SII_MCP_PORT}";
  env.SII_AGENT_PORT = 8002;
  env.SII_AGENT_URL = "http://localhost:${builtins.toString config.env.SII_AGENT_PORT}";
  env.ECOMMERCE_AGENT_PORT = 8080;
  env.ECOMMERCE_AGENT_URL = "http://localhost:${builtins.toString config.env.ECOMMERCE_AGENT_PORT}";
  env.API_PORT = 8000;
  env.API_URL = "http://localhost:${builtins.toString config.env.API_PORT}";

  scripts.login-aws.exec = "aws sso login --profile ${config.env.AWS_PROFILE}";
  scripts.start-ui.exec = ''
    cd $DEVENV_ROOT/web
    bun run dev
  '';

  languages = {
    # clojure.enable = true;

    python = {
      enable = true;
      uv.enable = true;
      # uv.sync.enable = true;
    };

    javascript = {
      enable = true;
      bun.enable = true;
    };

    opentofu.enable = true;
  };
  packages = [
    pkgs.lazysql
    pkgs.gobang
  ];

  process.manager.implementation = "process-compose";
  processes = {
    api = {
      exec = "uv run fastapi dev --port ${builtins.toString config.env.API_PORT}";
      cwd = "./api";
      after = [ "devenv:processes:sii-agent" ];
      ready = {
        http.get = {
            host = "localhost";
            port = config.env.API_PORT;
            path = "/ping";
        };
        initial_delay = 1;
      };
    };

    sii-mcp = {
      exec = "uv run fastmcp run main.py:mcp --transport http --port ${builtins.toString config.env.SII_MCP_PORT}";
      cwd = "./sii-mcp";
      ready = {
        http.get = {
            host = "localhost";
            port = config.env.SII_MCP_PORT;
            path = "/health";
        };
        initial_delay = 1;
      };
    };

    sii-agent = {
      exec = "uv run main.py";
      cwd = "./sii-agent";
      ready = {
        http.get = {
            host = "localhost";
            port = config.env.SII_AGENT_PORT;
            path = "/health";
        };
        initial_delay = 1;
      };
      after = [ "devenv:processes:sii-mcp" ];
    };

    ecommerce-agent = {
      exec = "uv run main.py";
      cwd = "./ecommerce-agent";
      ready = {
        http.get = {
            host = "localhost";
            port = config.env.ECOMMERCE_AGENT_PORT;
            path = "/ping";
        };
        initial_delay = 1;
      };
      after = [ "devenv:processes:sii-agent" ];
    };

    langfuse = {
      exec = "docker compose up";
      cwd = "./langfuse";
      ready = {
        http.get = {
            host = "localhost";
            port = 3000;
            path = "/";
        };
        initial_delay = 1;
      };
    };
  };
}
